package server

import (
	"fmt"
	"github.com/pingcap/log"
	"github.com/pkg/errors"
	"go.uber.org/zap"
	"pd/server/storage"
	"pd/server/util"
)

var AliveServerTime int64 = 5 * 1000 //起码要存活超过一定时间, 才会被系统分配到Actor

func (this *APIServer) findPositionInLRU(uniqueActorID string, needAllocNewPosition bool) *storage.PlacementInfo {
	cache, ok := this.positionCache.Get(uniqueActorID)
	if !ok {
		return nil
	}
	position, _ := cache.(*storage.PlacementInfo)
	if needAllocNewPosition {
		if this.checkServerAlive(position.ServerID) {
			return position
		}
		return nil
	}
	return position
}

func (this *APIServer) checkServerAlive(serverID int64) bool {
	info := this.membership.GetHostNodeInfoByID(serverID)
	return info != nil
}

func (this *APIServer) savePositionToLRU(uniqueActorID string, position *storage.PlacementInfo) {
	this.positionCache.Add(uniqueActorID, position)
}

func (this *APIServer) findPositionFromRemote(args *storage.PlacementArgs, needAllocNewPosition bool) (*storage.PlacementInfo, error) {
	info, err := this.database.GetRecord(args)
	if err != nil {
		log.Error("findPositionFromRemote", zap.Error(err))
		return nil, err
	}

	if info == nil {
		return nil, nil
	}

	if needAllocNewPosition {
		if this.checkServerAlive(info.ServerID) {
			return info, nil
		}
		return nil, nil
	}
	return info, nil
}

func (this *APIServer) removePositionFromRemote(args *storage.PlacementArgs) error {
	err := this.database.DeleteRecord(args)
	return err
}

func (this *APIServer) savePositionToRemote(args *storage.PlacementArgs, position *storage.PlacementInfo) error {
	err := this.database.PutRecord(position)
	if err != nil {
		log.Error("savePositionToRemote", zap.Error(err))
	}
	return err
}

//-1服务器个数不够
//-2没有该类型的服务器
//-3分配算法错误
func (this *APIServer) chooseServerByRandom(actorType string) int64 {
	//返回-1表示服务器个数不够
	index := this.membership.GetReadonlyIndex()
	uniqueType := fmt.Sprintf("%s", actorType)
	set, ok := index.types[uniqueType]
	if !ok || len(set) == 0 {
		return -2
	}

	now := util.GetMilliSeconds()

	max := int64(10)
	loads := make([]int64, 0)
	servers := make([]*HostNodeInfo, 0)
	for _, v := range set {
		//需要加入到集群一段时间, 然后当前负载是正数
		if now-v.StartTime >= AliveServerTime && v.Load >= 0 {
			servers = append(servers, v)
			loads = append(loads, v.Load)
			if v.Load > max {
				max = v.Load
			}
		}
	}

	if len(servers) == 0 {
		return -1
	}

	max = max * 11 / 10
	for index, v := range loads {
		loads[index] = max - v
	}

	i := util.RandomInArray(loads)

	if i < 0 {
		log.Error("RandomInArray return -1", zap.Reflect("loads", loads))
		i = 0
	}

	return servers[i].ServerID
}

func (this *APIServer) findOrAllocNewPosition(args *storage.PlacementArgs) (*storage.PlacementInfo, error) {
	needAllocNewPosition := args.TTL == 0
	uniqueActorID := fmt.Sprintf("%s_%s", args.ActorID, args.ActorType)
	//1. 先到LRU里面去找, 找到检查server存在性, 存在就返回
	//2. 到remote里面找, 找到检查sever存在性, 存在, 写LUR返回
	//3. 上锁
	//4. 到LRU里面找, 到remote里面找, 检查存在性, 存在写LRU返回
	//5. 按照type分配一个server, 然后写remote, 写LRU, 返回
	position, err := this.findPositionFromRemote(args, needAllocNewPosition)
	if err != nil {
		return nil, err
	}
	if position != nil {
		return position, nil
	}
	mutex, err := util.NewMutex(this.GetEtcdClient(), uniqueActorID)
	if err != nil {
		return nil, errors.WithStack(err)
	}
	err = mutex.Lock()
	if err != nil {
		return nil, errors.WithStack(err)
	}
	defer mutex.AsyncClose()

	position = this.findPositionInLRU(uniqueActorID, needAllocNewPosition)
	if position != nil {
		return position, nil
	}
	position, err = this.findPositionFromRemote(args, needAllocNewPosition)
	if err != nil {
		return nil, err
	}
	if position != nil {
		this.savePositionToLRU(uniqueActorID, position)
		return position, nil
	}

	//log.Info("chooseServerByRandom", zap.Uint64("Term", this.etcd.Server.Term()))
	//随机生成一个server
	newServerID := this.chooseServerByRandom(args.ActorType)
	log.Info("chooseServerByRandom",
		zap.String("ActorID", fmt.Sprintf("%s_%s", args.ActorType, args.ActorID)),
		zap.Int64("ServerID", newServerID))
	if newServerID < 0 {
		if newServerID == -1 {
			return nil, errors.New("without enough server")
		}
		if newServerID == -2 {
			return nil, errors.New("not find actor type")
		}
		return nil, errors.New("unknown chooseSever error")
	}

	position = &storage.PlacementInfo{
		ActorID:    args.ActorID,
		ActorType:  args.ActorType,
		TTL:        args.TTL,
		CreateTime: util.GetMilliSeconds(),
		ServerID:   newServerID,
	}
	err = this.savePositionToRemote(args, position)
	if err != nil {
		return nil, err
	}
	this.savePositionToLRU(uniqueActorID, position)

	return position, nil
}

func (this *APIServer) FindPosition(args *storage.PlacementArgs) (*storage.PlacementInfo, error) {
	needAllocNewPosition := args.TTL == 0
	uniqueActorID := fmt.Sprintf("%s_%s", args.ActorID, args.ActorType)
	position := this.findPositionInLRU(uniqueActorID, needAllocNewPosition)
	if position != nil {
		return position, nil
	}
	return this.findOrAllocNewPosition(args)
}

func (this *APIServer) DeletePosition(args *storage.PlacementArgs) error {
	uniqueActorID := fmt.Sprintf("%s_%s", args.ActorID, args.ActorType)

	mutex, err := util.NewMutex(this.GetEtcdClient(), uniqueActorID)
	if err != nil {
		return err
	}
	mutex.Lock()
	go mutex.AsyncClose()
	this.positionCache.Remove(uniqueActorID)
	err = this.removePositionFromRemote(args)
	if err != nil {
		return err
	}
	return nil
}
