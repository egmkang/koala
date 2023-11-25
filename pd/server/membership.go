package server

import (
	"fmt"
	"pd/server/util"
	"sort"

	lru "github.com/hashicorp/golang-lru"
	"github.com/pingcap/log"
	"go.uber.org/zap"
)

const RecentHostNodeIDLRUSize = 1024 * 8
const PDServerHeartBeatTime int64 = 1 * 1000
const HostEventLifeTime = 60 * 1000

// 路径: /node/{server_id}
// 内容是HostInfo的JSON字符串
const HostNodePrefix = "/node"

func GenerateServerKey(serverID int64) string {
	return fmt.Sprintf("%s/%d", HostNodePrefix, serverID)
}

type HostNodeInfo struct {
	ServerID  int64             `json:"server_id"`  //服务器ID
	Load      int64             `json:"load"`       //负载
	StartTime int64             `json:"start_time"` //服务器注册的时间(单位毫秒)
	TTL       int64             `json:"ttl"`        //存活时间(心跳时间*3)
	Address   string            `json:"address"`    //服务器地址
	Services  map[string]string `json:"services"`   //可以提供服务的类型(接口 => 实现)
	Desc      string            `json:"desc"`       //Host的描述信息
	Labels    map[string]string `json:"labels"`     //额外的属性, GatewayAddress等放在这里面
}

type HostNodeIndex struct {
	ids   map[int64]*HostNodeInfo            //ServerID => HostNodeInfo
	types map[string]map[int64]*HostNodeInfo //ActorType => Set<HostNodeInfo>
}

type Membership struct {
	lastUpdateIndexTime int64
	index               *HostNodeIndex
	events              map[int64]*HostNodeAddRemoveEvent //milliSeconds => events
	eventsSnapshot      []*HostNodeAddRemoveEvent         //event snapshot
	registeredID        *lru.Cache                        //recent registered server id
}

type HostNodeAddRemoveEvent struct {
	Time   int64   `json:"time"`
	Add    []int64 `json:"add"`
	Remove []int64 `json:"remove"`
}

type HostNodeEventSlice []*HostNodeAddRemoveEvent

func (s HostNodeEventSlice) Len() int {
	return len(s)
}

func (s HostNodeEventSlice) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}

func (s HostNodeEventSlice) Less(i, j int) bool {
	return s[i].Time < s[j].Time
}

func NewMembershipManager() *Membership {
	index := buildIndexFromArray(nil)
	serverIdLru, _ := lru.New(RecentHostNodeIDLRUSize)
	return &Membership{
		lastUpdateIndexTime: util.GetMilliSeconds(),
		index:               index,
		events:              map[int64]*HostNodeAddRemoveEvent{},
		registeredID:        serverIdLru,
	}
}

func (this *Membership) compare2Index(newIndex *HostNodeIndex) ([]int64, []int64) {
	add := make([]int64, 0)
	remove := make([]int64, 0)
	for k, v := range newIndex.ids {
		if _, ok := this.index.ids[k]; !ok {
			add = append(add, v.ServerID)
		}
	}
	for k, v := range this.index.ids {
		if _, ok := newIndex.ids[k]; !ok {
			remove = append(remove, v.ServerID)
		}
	}
	return add, remove
}

func (this *Membership) updateEvents(add []int64, remove []int64) {
	if len(add) > 0 || len(remove) > 0 {
		event := &HostNodeAddRemoveEvent{
			Time:   this.lastUpdateIndexTime,
			Add:    add,
			Remove: remove,
		}
		this.events[this.lastUpdateIndexTime] = event
	}

	needRemove := make([]int64, 0)
	snapshot := make([]*HostNodeAddRemoveEvent, 0)
	currentTime := util.GetMilliSeconds()
	for k, v := range this.events {
		if currentTime-k >= HostEventLifeTime {
			needRemove = append(needRemove, k)
		} else {
			snapshot = append(snapshot, v)
		}
	}

	sort.Sort(HostNodeEventSlice(snapshot))
	this.eventsSnapshot = snapshot

	for _, v := range needRemove {
		delete(this.events, v)
	}
}

func (this *Membership) GetReadonlyIndex() *HostNodeIndex {
	return this.index
}

func (this *Membership) GetReadonlyRecentEvents() []*HostNodeAddRemoveEvent {
	return this.eventsSnapshot
}

func (this *Membership) AddHostNodeID(serverID int64) {
	this.registeredID.Add(serverID, serverID)
}

func (this *Membership) GetHostNodeID(serverID int64) interface{} {
	v, _ := this.registeredID.Get(serverID)
	return v
}

func (this *Membership) GetHostNodeInfoByID(serverID int64) *HostNodeInfo {
	index := this.GetReadonlyIndex()
	info, _ := index.ids[serverID]
	return info
}

func (this *Membership) GetHostNodesInfo() map[int64]*HostNodeInfo {
	result := map[int64]*HostNodeInfo{}
	index := this.GetReadonlyIndex()

	for k, v := range index.ids {
		result[k] = v
	}

	return result
}

func (this *Membership) GetHostNodesByType(actorType string) map[int64]*HostNodeInfo {
	typesName := actorType
	index := this.GetReadonlyIndex()

	result, ok := index.types[typesName]
	if ok {
		return map[int64]*HostNodeInfo{}
	}
	return result
}

func (this *Membership) UpdateIndex(startTime int64, newIndex *HostNodeIndex) ([]int64, []int64) {
	if startTime > this.lastUpdateIndexTime {
		this.lastUpdateIndexTime = startTime

		add, remove := this.compare2Index(newIndex)
		this.index = newIndex
		this.updateEvents(add, remove)
		return add, remove
	}
	log.Warn("UpdateIndex", zap.Int64("LastUpdateTime", this.lastUpdateIndexTime), zap.Int64("StartTime", startTime))
	return nil, nil
}

func tryParseHostNodeInfo(data []byte) *HostNodeInfo {
	info := &HostNodeInfo{}
	err := util.ReadJSONFromData(data, info)
	if err != nil {
		log.Error("tryParseHostNodeInfo fail", zap.Error(err))
		return nil
	}
	return info
}

func buildIndexFromArray(list []*HostNodeInfo) *HostNodeIndex {
	index := &HostNodeIndex{ids: map[int64]*HostNodeInfo{}, types: map[string]map[int64]*HostNodeInfo{}}
	if list == nil || len(list) == 0 {
		return index
	}
	for _, v := range list {
		//id的索引
		index.ids[v.ServerID] = v
		//注册类型的索引
		for interfaceName, implName := range v.Services {
			if len(implName) == 0 {
				continue
			}
			if _, ok := index.types[interfaceName]; !ok {
				index.types[interfaceName] = map[int64]*HostNodeInfo{}
			}
			s := index.types[interfaceName]
			s[v.ServerID] = v
		}
	}
	return index
}
