package server

import (
	"context"
	"fmt"
	lru "github.com/hashicorp/golang-lru"
	"github.com/pingcap/log"
	"go.etcd.io/etcd/clientv3/concurrency"
	"go.uber.org/zap"
	"pd/server/storage"
	"reflect"
	"strings"
	"time"
)

const PDElectionPath = "/pd_election"

var nodeName = ""

func (this *APIServer) IsLeader() bool {
	return this.NodeNameInfo() == this.leaderName
}

func (this *APIServer) NodeNameInfo() string {
	if len(nodeName) == 0 {
		nodeName = fmt.Sprintf("%s,%s", this.config.Name, this.etcdConfig.LCUrls[0].String())
	}
	return nodeName
}

func (this *APIServer) Campaign() {
	for {
		session, err := concurrency.NewSession(this.etcdClient, concurrency.WithTTL(3))
		if err != nil {
			log.Error("PD Campaign fail", zap.Error(err))
			continue
		}

		this.election = concurrency.NewElection(session, PDElectionPath)
		ctx := context.TODO()
		if err := this.election.Campaign(ctx, this.NodeNameInfo()); err != nil {
			log.Error("PD Campaign fail", zap.Error(err))
			continue
		}

		log.Info("Campaign Success", zap.String("Leader", this.NodeNameInfo()), zap.String("Name", this.NodeNameInfo()))
		//这边标注自己是leader
		//this.ChangeLeader(this.NodeNameInfo())
		select {
		case <-session.Done():
			if this.IsLeader() {
				this.leaderName = ""
			}
			log.Info("Campaign leader exist")
		}
	}
}

func (this *APIServer) Monitor() {
	for {
		if this.election == nil {
			time.Sleep(time.Microsecond * 10)
			continue
		}
		ctx, cancel := context.WithCancel(context.TODO())
		channel := this.election.Observe(ctx)
		for {
			select {
			case resp := <-channel:
				if len(resp.Kvs) > 0 {
					leader := string(resp.Kvs[0].Value)
					this.ChangeLeader(leader)
				} else {
					cancel()
					time.Sleep(time.Second * 1)
					ctx, cancel = context.WithCancel(context.TODO())
					channel = this.election.Observe(ctx)
				}
			}
		}
	}
}

func (this *APIServer) ChangeLeader(newLeader string) {
	if this.leaderName == newLeader {
		return
	}
	log.Info("ChangeLeader", zap.String("NewLeader", newLeader), zap.String("OldLeader", this.leaderName), zap.String("Name", this.NodeNameInfo()))
	this.leaderName = newLeader
	url := strings.Split(this.leaderName, ",")[1]
	//leader切换, 把http请求重新路由一下
	this.proxy = this.tryCreateProxy(url)
	if this.proxy == nil {
		log.Error("ChangeLeader Proxy", zap.String("Url", url))
	}
	this.resetState()
}

func (this *APIServer) newStorage() storage.PlacementStorage {
	if len(this.config.RedisUrls) > 0 {
		return storage.NewRedisStorageImpl(this.config.RedisUrls)
	}
	log.Warn("using memory storage")
	return storage.NewMemoryStorage()
}

func (this *APIServer) resetState() {
	log.Info("Reset PD State")

	positionLru, _ := lru.New(PlacementLRUSize)
	db := this.newStorage()
	if this.database != nil && !reflect.ValueOf(this.database).IsNil() {
		this.database.Close()
	}
	this.database = db
	this.positionCache = positionLru
}
