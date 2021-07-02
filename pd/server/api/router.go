package api

import (
	"github.com/gorilla/mux"
	"github.com/unrolled/render"
	"github.com/urfave/negroni"
	"net/http"
	"pd/server"
)

const Prefix = "/pd"

const FindPositionUrl = "/api/v1/placement/find_position"

func createRouter(prefix string, server *server.APIServer) *mux.Router {
	render := render.New(render.Options{IndentJSON: false})

	subRouter := mux.NewRouter().PathPrefix(prefix).Subrouter()

	infoHandler := newInfoHandler(server, render)
	subRouter.HandleFunc("/api/v1/version", infoHandler.Version).Methods("GET")

	idHandler := newIdHandler(server, render)
	subRouter.HandleFunc("/api/v1/id/new_server_id", idHandler.NewServerID).Methods("POST")
	subRouter.HandleFunc("/api/v1/id/new_sequence/{sequence_key}/{step}", idHandler.NewSequenceID).Methods("POST")

	membershipHandler := newMembershipHandler(server, render)
	subRouter.HandleFunc("/api/v1/membership/register", membershipHandler.RegisterNewServer).Methods("POST")
	subRouter.HandleFunc("/api/v1/membership/keep_alive", membershipHandler.KeepAliveServer).Methods("POST")
	subRouter.HandleFunc("/api/v1/membership/fetch_all", membershipHandler.FetchAllServer).Methods("POST")

	placementHandler := newPlacementHandler(server, render)
	subRouter.HandleFunc(FindPositionUrl, placementHandler.FindPosition).Methods("POST")
	subRouter.HandleFunc("/api/v1/placement/new_token", placementHandler.NewToken).Methods("POST")
	return subRouter
}

func NewHandle(server *server.APIServer) http.Handler {
	router := mux.NewRouter()
	r := createRouter(Prefix, server)
	router.PathPrefix(Prefix).Handler(negroni.New(
		NewRedirector(server),
		negroni.Wrap(r)))
	return router
}
