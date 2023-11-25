package api

import (
	"net/http"
	"pd/server"

	"github.com/unrolled/render"
)

type infoHandler struct {
	server *server.APIServer
	render *render.Render
}

func newInfoHandler(server *server.APIServer, render *render.Render) *infoHandler {
	return &infoHandler{server: server, render: render}
}

type PDServerInfo struct {
	Version string `json:"version"`
}

func (this *infoHandler) Version(w http.ResponseWriter, r *http.Request) {
	info := PDServerInfo{
		Version: "0.1",
	}
	this.render.JSON(w, http.StatusOK, info)
}
