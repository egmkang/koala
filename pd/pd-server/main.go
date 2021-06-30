package main

import (
	"github.com/pingcap/log"
	"os"
	"pd/server"
	"pd/server/api"
	"pd/server/config"
	"time"
)

func main() {
	cfg := config.NewConfig()
	err := cfg.Parse(os.Args[1:])

	if err != nil {
		os.Exit(0)
	}

	err = cfg.SetupLogger()

	if err != nil {
		log.Error(err.Error())
		return
	}

	s := server.NewAPIServer(cfg)
	err = s.InitStorage()
	if err != nil {
		log.Error(err.Error())
		return
	}

	err = s.InitEtcd(api.Prefix, api.NewHandle)
	if err != nil {
		log.Error(err.Error())
		return
	}

	for s.IsRunning() {
		time.Sleep(time.Second)
	}
	log.Info("exit")
}
