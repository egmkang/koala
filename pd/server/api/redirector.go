package api

import (
	"github.com/pingcap/log"
	"github.com/urfave/negroni"
	"go.uber.org/zap"
	"net/http"
	"pd/server"
)

type redirector struct {
	s *server.APIServer
}

func NewRedirector(s *server.APIServer) negroni.Handler {
	return &redirector{s: s}
}

const RedirectUrlFullPath = Prefix + FindPositionUrl

func (this *redirector) ServeHTTP(w http.ResponseWriter, r *http.Request, next http.HandlerFunc) {
	if r.RequestURI == RedirectUrlFullPath && !this.s.IsLeader() {
		log.Info("ServeHTTP using proxy", zap.String("Url", r.RequestURI))
		//这边不是leader, 而且还是find position, 那么需要把请求路由到leader上面去
		proxy := this.s.GetProxy()
		proxy.ServeHTTP(w, r)
		return
	}
	next(w, r)
}
