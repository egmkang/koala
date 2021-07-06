package server

import (
	"github.com/pingcap/log"
	"go.etcd.io/etcd/clientv3"
	"go.uber.org/zap"
	"pd/server/util"
	"time"
)

func (this *APIServer) tryUpdateEtcdMembers() {
	resp, err := util.EtcdListMembers(this.etcdClient)
	if err != nil {
		log.Error("tryUpdateEtcdMembers", zap.Error(err))
		log.Error("etcd server exit")

		this.Shutdown()
		return
	}
	this.etcdMembers = resp.Members
}

//思考一下, 感觉跟etcd断链, 也不需要退出, 等啥时候连上了再重新pull
//从etcd pull所有的服务器信息
//构造map, 然后替换hosts
//需要注意分配程序, 可能新的服务器会丢失一次: Add了Host, 然后pull的时候还没进etcd
func (this *APIServer) tryUpdateHostNodesListOnce() {
	startTime := util.GetMilliSeconds()
	prefix := HostNodePrefix
	resp, err := util.EtcdKVGet(this.etcdClient, prefix, clientv3.WithPrefix())
	if err != nil {
		log.Error("tryUpdateHostNodesListOnce", zap.Error(err))
		return
	}

	var list []*HostNodeInfo
	for _, data := range resp.Kvs {
		item := tryParseHostNodeInfo(data.Value)
		if item != nil {
			list = append(list, item)
		}
	}

	index := buildIndexFromArray(list)
	add, remove := this.membership.UpdateIndex(startTime, index)
	if add != nil && len(add) > 0 {
		log.Info("TryUpdateActorHostList", zap.Reflect("AddServer", add))
	}
	if remove != nil && len(remove) > 0 {
		log.Info("TryUpdateActorHostList", zap.Reflect("RemoveServer", remove))
	}
}

func (this *APIServer) GetMembershipRecentEvent() []*HostNodeAddRemoveEvent {
	return this.membership.GetReadonlyRecentEvents()
}

func (this *APIServer) SaveHostNodeInfo(serverInfo *HostNodeInfo, leaseID int64) error {
	json, err := util.JSON(serverInfo)
	if err != nil {
		return err
	}

	key := GenerateServerKey(serverInfo.ServerID)
	_, err = util.EtcdKVPut(this.etcdClient, key, json, clientv3.WithLease(clientv3.LeaseID(leaseID)))
	if err != nil {
		return err
	}
	return nil
}

func (this *APIServer) DeleteHost(serverID int64, address string) error {
	host := this.GetHostInfoByServerID(serverID)
	if host != nil && host.Address == address {
		index := this.membership.GetReadonlyIndex()
		delete(index.ids, serverID)
		for k, _ := range host.Services {
			delete(index.types[k], serverID)
		}
		log.Info("DeleteHost", zap.Int64("ServerID", serverID), zap.String("Address", address))
	}
	key := GenerateServerKey(serverID)
	_, err := util.EtcdKVDelete(this.etcdClient, key)
	if err != nil {
		return err
	}
	return nil
}

func (this *APIServer) GetHostInfoByServerID(serverID int64) *HostNodeInfo {
	index := this.membership.GetReadonlyIndex()
	info, ok := index.ids[serverID]
	if ok {
		return info
	}

	key := GenerateServerKey(serverID)
	data, err := util.EtcdGetKVValue(this.etcdClient, key)
	if err != nil || data == nil {
		return nil
	}
	info = tryParseHostNodeInfo(data)
	return info
}

func (this *APIServer) GetHostNodes() map[int64]*HostNodeInfo {
	return this.membership.GetHostNodesInfo()
}

func (this *APIServer) GetHostNodesByType(actorType string) map[int64]*HostNodeInfo {
	return this.membership.GetHostNodesByType(actorType)
}

func (this *APIServer) AddHostNodeID(serverID int64) {
	this.membership.AddHostNodeID(serverID)
}

func (this *APIServer) GetRegisteredActorHostID(serverID int64) interface{} {
	v := this.membership.GetHostNodeID(serverID)
	return v
}

func (this *APIServer) updateHostNodeListLoop() {
	beginTime := util.GetMilliSeconds()
	for i := int64(0); this.IsRunning(); i++ {
		go this.tryUpdateHostNodesListOnce()
		go this.tryUpdateEtcdMembers()
		currentTime := util.GetMilliSeconds()
		sleepTime := beginTime + (i+1)*PDServerHeartBeatTime - currentTime
		time.Sleep(time.Millisecond * time.Duration(sleepTime))
	}
}

func (this *APIServer) GetMembership() *Membership {
	return this.membership
}
