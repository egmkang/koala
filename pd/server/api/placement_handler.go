package api

import (
	"github.com/unrolled/render"
	"net/http"
	"pd/server"
	"pd/server/storage"
	"pd/server/util"
)

const TokenPathPrefix = "/global/token"

var tokenID = util.NewIdGenerator(TokenPathPrefix, 1000)

type placementHandler struct {
	server *server.APIServer
	render *render.Render
}

func newPlacementHandler(server *server.APIServer, render *render.Render) *placementHandler {
	return &placementHandler{server: server, render: render}
}

type FindActorPositionRequest struct {
	ActorType string `json:"actor_type"`
	ActorID   string `json:"actor_id"`
	TTL       int64  `json:"ttl"`
}

type FindActorPositionResponse struct {
	ActorID       string `json:"actor_id"`
	ActorType     string `json:"actor_type"`
	TTL           int64  `json:"ttl"`
	CreateTime    int64  `json:"create_time"`
	ServerID      int64  `json:"server_id"`
	ServerAddress string `json:"server_address"`
}

func (this *placementHandler) FindPosition(w http.ResponseWriter, r *http.Request) {
	req := &FindActorPositionRequest{}
	if err := util.ReadJSONResponseError(this.render, w, r.Body, req); err != nil {
		return
	}

	if len(req.ActorType) == 0 || len(req.ActorID) == 0 {
		this.render.JSON(w, http.StatusBadRequest, "args error")
		return
	}
	args := &storage.PlacementArgs{
		ActorID:   req.ActorID,
		ActorType: req.ActorType,
		TTL:       req.TTL,
	}

	result, err := this.server.FindPosition(args)
	if err != nil {
		this.render.JSON(w, http.StatusBadRequest, err.Error())
		return
	}

	serverInfo := this.server.GetHostInfoByServerID(result.ServerID)
	if serverInfo == nil {
		this.render.JSON(w, http.StatusBadRequest, "server not found")
		return
	}
	resp := FindActorPositionResponse{
		ActorID:       result.ActorID,
		ActorType:     result.ActorType,
		TTL:           result.TTL,
		CreateTime:    result.CreateTime,
		ServerID:      result.ServerID,
		ServerAddress: serverInfo.Address,
	}

	this.render.JSON(w, http.StatusOK, resp)
}

func (this *placementHandler) NewToken(w http.ResponseWriter, r *http.Request) {
	newId, err := tokenID.GetNewID(this.server.GetEtcdClient())
	if err != nil {
		this.render.JSON(w, http.StatusInternalServerError, err.Error())
		return
	}
	info := NewIDResp{ID: newId}
	this.render.JSON(w, http.StatusOK, info)
}

type DeleteActorResponse struct {
	ActorID   string `json:"actor_id"`
	ActorType string `json:"actor_type"`
}

func (this *placementHandler) DeleteActor(w http.ResponseWriter, r *http.Request) {
	req := &FindActorPositionRequest{}
	if err := util.ReadJSONResponseError(this.render, w, r.Body, req); err != nil {
		return
	}

	if len(req.ActorType) == 0 || len(req.ActorID) == 0 {
		this.render.JSON(w, http.StatusBadRequest, "args error")
		return
	}
	args := &storage.PlacementArgs{
		ActorID:   req.ActorID,
		ActorType: req.ActorType,
	}
	err := this.server.DeletePosition(args)
	if err != nil {
		this.render.JSON(w, http.StatusBadRequest, err.Error())
		return
	}

	resp := &DeleteActorResponse{
		ActorID:   args.ActorID,
		ActorType: args.ActorType,
	}
	this.render.JSON(w, http.StatusOK, resp)
}
