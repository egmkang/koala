package api

import (
	"fmt"
	"github.com/pingcap/log"
	"github.com/unrolled/render"
	"go.uber.org/zap"
	"net/http"
	"pd/server"
	"pd/server/util"
	"strings"
)

//默认存活时间是15秒, 5秒一个心跳
const HostNodeDefaultTTL = 15

type membershipHandler struct {
	server *server.APIServer
	render *render.Render
}

func newMembershipHandler(server *server.APIServer, render *render.Render) *membershipHandler {
	return &membershipHandler{server: server, render: render}
}

type RegisterNewServerResp struct {
	LeaseID int64 `json:"lease_id"`
}

type KeepAliveServerRequest struct {
	ServerID int64 `json:"server_id"`
	LeaseID  int64 `json:"lease_id"`
	Load     int64 `json:"load"`
}

type KeepAliveServerResp struct {
	Hosts  map[int64]*server.HostNodeInfo   `json:"hosts"`
	Events []*server.HostNodeAddRemoveEvent `json:"events"`
}

type FetchAllServerResp struct {
	Hosts  map[int64]*server.HostNodeInfo   `json:"hosts"`
	Events []*server.HostNodeAddRemoveEvent `json:"events"`
}

func (this *membershipHandler) RegisterNewServer(w http.ResponseWriter, r *http.Request) {
	serverInfo := &server.HostNodeInfo{}
	if err := util.ReadJSONResponseError(this.render, w, r.Body, serverInfo); err != nil {
		return
	}

	//从etcd里面获取server信息, 如果存在就拒绝注册
	if info := this.server.GetHostInfoByServerID(serverInfo.ServerID); info != nil {
		this.render.JSON(w, http.StatusBadRequest, fmt.Sprintf("RegisterNewServer, ServerID:%d exist", serverInfo.ServerID))
		log.Info("RegisterNewServer server exist", zap.Int64("ServerID", info.ServerID))
		return
	}

	//从LRU里面查看
	if v := this.server.GetRegisteredActorHostID(serverInfo.ServerID); v != nil {
		this.render.JSON(w, http.StatusBadRequest, fmt.Sprintf("RegisterNewServer, ServerID:%d exist", serverInfo.ServerID))
		log.Info("RegisterNewServer server exist", zap.Reflect("ServerID", v))
		return
	}

	serverInfo.StartTime = util.GetMilliSeconds()
	if serverInfo.TTL == 0 {
		serverInfo.TTL = HostNodeDefaultTTL
	}

	lease, err := util.EtcdLeaseGrant(this.server.GetEtcdClient(), serverInfo.TTL)
	if err != nil {
		this.render.JSON(w, http.StatusInternalServerError, err.Error())
		return
	}
	err = this.server.SaveHostNodeInfo(serverInfo, int64(lease.ID))
	if err != nil {
		this.render.JSON(w, http.StatusInternalServerError, err.Error())
		return
	}

	this.server.AddHostNodeID(serverInfo.ServerID)

	var sb = strings.Builder{}
	for key, s := range serverInfo.Services {
		sb.WriteString(key)
		sb.WriteString(" => ")
		sb.WriteString(s)
		sb.WriteString(", ")
	}

	var services = sb.String()
	if len(services) > 2 {
		services = services[0 : len(services)-2]
	}

	log.Info("RegisterNewServer",
		zap.Int64("ServerID", serverInfo.ServerID),
		zap.Int64("LeaseID", int64(lease.ID)),
		zap.Int64("TTL", serverInfo.TTL),
		zap.Int64("StartTime", serverInfo.StartTime),
		zap.String("Address", serverInfo.Address),
		zap.String("Services", services))

	data := &RegisterNewServerResp{LeaseID: int64(lease.ID)}
	this.render.JSON(w, http.StatusOK, data)
}

func (this *membershipHandler) FetchAllServer(w http.ResponseWriter, r *http.Request) {
	result := &FetchAllServerResp{
		Hosts:  this.server.GetHostNodes(),
		Events: this.server.GetMembershipRecentEvent(),
	}
	this.render.JSON(w, http.StatusOK, result)
}

func (this *membershipHandler) KeepAliveServer(w http.ResponseWriter, r *http.Request) {
	serverInfo := &KeepAliveServerRequest{}
	if err := util.ReadJSONResponseError(this.render, w, r.Body, serverInfo); err != nil {
		return
	}

	if serverInfo.ServerID == 0 || serverInfo.LeaseID == 0 {
		this.render.JSON(w, http.StatusBadRequest, "ServerID/LeaseID must input")
		return
	}

	_, err := util.EtcdLeaseKeepAliveOnce(this.server.GetEtcdClient(), serverInfo.LeaseID)
	if err != nil {
		this.render.JSON(w, http.StatusBadRequest, err.Error())
		return
	}

	//更新缓存和etcd里面的数据
	info := this.server.GetHostInfoByServerID(serverInfo.ServerID)
	if info == nil {
		log.Error("KeepAliveServer server not found", zap.Int64("ServerID", serverInfo.ServerID))
		this.render.JSON(w, http.StatusBadRequest, "ServerID not found")
		return
	}

	info.Load = serverInfo.Load
	this.server.SaveHostNodeInfo(info, serverInfo.LeaseID)

	log.Debug("KeepAliveServer",
		zap.Int64("ServerID", info.ServerID),
		zap.Int64("LeaseID", serverInfo.LeaseID),
		zap.Int64("Load", info.Load))

	result := &KeepAliveServerResp{
		Hosts:  this.server.GetHostNodes(),
		Events: this.server.GetMembershipRecentEvent(),
	}
	this.render.JSON(w, http.StatusOK, result)
}
