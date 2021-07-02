package api

import (
	"github.com/gorilla/mux"
	"github.com/unrolled/render"
	"net/http"
	"pd/server"
	"pd/server/util"
	"strconv"
	"sync"
)

const SequencePathPrefix = "/global/sequence/"
const ServerIDPathPrefix = "/global/server_id"

var serverIdGenerator = util.NewIdGenerator(ServerIDPathPrefix, 1)

var sequenceMapMutex = sync.Mutex{}
var sequenceGenerator = map[string]*util.IdGenerator{}

func getIdGenerator(sequencePath string, step int64) *util.IdGenerator {
	sequenceMapMutex.Lock()
	defer sequenceMapMutex.Unlock()
	v, ok := sequenceGenerator[sequencePath]
	if ok {
		return v
	}
	path := SequencePathPrefix + sequencePath
	newGenerator := util.NewIdGenerator(path, step)
	sequenceGenerator[sequencePath] = newGenerator
	return newGenerator
}

type idHandler struct {
	server *server.APIServer
	render *render.Render
}

func newIdHandler(server *server.APIServer, render *render.Render) *idHandler {
	return &idHandler{server: server, render: render}
}

type NewIDResp struct {
	ID int64 `json:"id"`
}

func (this *idHandler) NewServerID(w http.ResponseWriter, r *http.Request) {
	newId, err := serverIdGenerator.GetNewID(this.server.GetEtcdClient())
	if err != nil {
		this.render.JSON(w, http.StatusInternalServerError, err.Error())
		return
	}
	info := NewIDResp{ID: newId}
	this.render.JSON(w, http.StatusOK, info)
}

func (this *idHandler) NewSequenceID(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	key := vars["sequence_key"]
	stepStr := vars["step"]

	if len(key) == 0 {
		this.render.JSON(w, http.StatusBadRequest, "sequence_key is null")
		return
	}
	step, err := strconv.ParseInt(stepStr, 10, 64)
	if err != nil {
		this.render.JSON(w, http.StatusBadRequest, err.Error())
		return
	}

	if step < 100 {
		step = 100
	}

	generator := getIdGenerator(key, step)
	newId, err := generator.GetNewID(this.server.GetEtcdClient())
	if err != nil {
		this.render.JSON(w, http.StatusInternalServerError, err.Error())
		return
	}

	resp := &NewIDResp{ID: newId}
	this.render.JSON(w, http.StatusOK, resp)
}
