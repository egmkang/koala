package server

import (
	lru "github.com/hashicorp/golang-lru"
	"github.com/pingcap/log"
	"github.com/pkg/errors"
	"go.etcd.io/etcd/clientv3"
	"go.etcd.io/etcd/clientv3/concurrency"
	"go.etcd.io/etcd/embed"
	"go.etcd.io/etcd/etcdserver/etcdserverpb"
	"go.uber.org/zap"
	"net/http"
	"net/http/httputil"
	"net/url"
	"pd/server/config"
	"pd/server/storage"
	"pd/server/util"
	"reflect"
	"sync/atomic"
	"time"
)

const PlacementLRUSize = 1024 * 1024

type APIServer struct {
	config     *config.Config
	etcdConfig *embed.Config
	etcd       *embed.Etcd
	etcdClient *clientv3.Client

	terminal int32

	handler http.Handler

	etcdMembers []*etcdserverpb.Member
	membership  *Membership

	//leader选举以及状态重置
	proxies       map[string]*httputil.ReverseProxy
	proxy         *httputil.ReverseProxy //指向当前leader的proxy
	election      *concurrency.Election
	leaderName    string     //选举出来leader的名字
	positionCache *lru.Cache //actor position lru
	database      storage.PlacementStorage
}

func (this *APIServer) InitStorage() error {
	this.database = this.newStorage()
	if this.database == nil || reflect.ValueOf(this.database).IsNil() {
		return errors.Errorf("init storage fail")
	}
	return nil
}

func (this *APIServer) LeaderName() string {
	return this.leaderName
}

func (this *APIServer) GetProxy() *httputil.ReverseProxy {
	return this.proxy
}

func (this *APIServer) createProxy(address string) *httputil.ReverseProxy {
	l, err := url.Parse(address)
	if err == nil {
		director := func(req *http.Request) {
			req.URL.Scheme = l.Scheme
			req.URL.Host = l.Host
		}
		return &httputil.ReverseProxy{
			Director: director,
		}
	}
	return nil
}

func (this *APIServer) tryCreateProxy(url string) *httputil.ReverseProxy {
	if proxy, ok := this.proxies[url]; ok {
		return proxy
	}
	l := this.createProxy(url)
	this.proxies[url] = l
	return l
}

func (this *APIServer) InitEtcd(path string, apiRegister func(*APIServer) http.Handler) error {
	var err error
	this.etcdConfig, err = this.config.GenEmbedEtcdConfig()
	if err != nil {
		return err
	}

	if path[len(path)-1] != '/' {
		path = path + "/"
	}
	this.etcdConfig.UserHandlers = map[string]http.Handler{path: apiRegister(this)}

	etcd, err := embed.StartEtcd(this.etcdConfig)
	if err != nil {
		log.Error("StartEtcd failed", zap.Error(err))
		return errors.WithStack(err)
	}

	select {
	case <-etcd.Server.ReadyNotify():
		log.Info("etcd inited")
	}

	endpoints := []string{this.etcdConfig.ACUrls[0].String()}
	log.Info("create etcd v3 client", zap.Strings("endpoints", endpoints))

	client, err := clientv3.New(clientv3.Config{
		Endpoints:   endpoints,
		DialTimeout: 3 * time.Second,
	})

	if err != nil {
		return errors.WithStack(err)
	}

	this.etcd = etcd
	this.etcdClient = client
	go this.updateHostNodeListLoop()

	//测试代码
	//go this.TestEtcdMutex("/tttttt", 1)
	//go this.FindPosition(&storage.PlacementArgs{
	//	ActorID:   "1",
	//	ActorType: "1",
	//	TTL:       0,
	//})
	go this.Campaign()
	go this.Monitor()
	return nil
}

func (this *APIServer) Shutdown() {
	atomic.StoreInt32(&this.terminal, 1)
	this.etcd.Close()
}

func (this *APIServer) IsRunning() bool {
	return atomic.LoadInt32(&this.terminal) == 0
}

func (this *APIServer) TestEtcdMutex(prefix string, x int) {
	mutex, err := util.NewMutex(this.etcdClient, prefix)
	if err != nil {
		log.Error("Etcd Mutex error", zap.Error(err))
		return
	}

	err = mutex.Lock()
	if err != nil {
		log.Error("etcd mutex lock error", zap.Error(err))
		return
	}

	defer mutex.AsyncClose()
	time.Sleep(time.Second * time.Duration(x))
	log.Info("print", zap.Int("index", x))
}

func (this *APIServer) GetEtcdClient() *clientv3.Client {
	return this.etcdClient
}

func NewAPIServer(config *config.Config) *APIServer {
	positionLru, _ := lru.New(PlacementLRUSize)
	s := &APIServer{
		config:        config,
		terminal:      0,
		positionCache: positionLru,
		proxies:       make(map[string]*httputil.ReverseProxy),
	}
	membership := NewMembershipManager()
	s.membership = membership
	return s
}
