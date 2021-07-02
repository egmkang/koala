package storage

import (
	"context"
	"fmt"
	"github.com/cespare/xxhash"
	"github.com/go-redis/redis/v8"
	"github.com/pingcap/log"
	"go.uber.org/zap"
	"pd/server/util"
	"strings"
)

const EngineRedis = "redis"

type redisStorageImpl struct {
	clients []*redis.Client
}

func (this *redisStorageImpl) Close() {
	if this.clients == nil {
		return
	}
	for _, client := range this.clients {
		if client != nil {
			_ = client.Close()
		}
	}
}

func (this *redisStorageImpl) Name() string {
	return EngineRedis
}

func (this *redisStorageImpl) getDb(uniqueId string) (*redis.Client, uint64) {
	hash := xxhash.Sum64String(uniqueId)
	index := hash % uint64(len(this.clients))
	return this.clients[index], index
}

func uniqueId(actorType string, actorID string) string {
	return fmt.Sprintf("%s_%s", actorType, actorID)
}

func (this *redisStorageImpl) GetRecord(args *PlacementArgs) (*PlacementInfo, error) {
	ctx := context.Background()
	id := uniqueId(args.ActorType, args.ActorID)
	rdb, _ := this.getDb(id)
	val, err := rdb.Get(ctx, id).Result()
	if err == redis.Nil {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	result := &PlacementInfo{}
	err = util.ReadJSONFromData([]byte(val), result)
	if err != nil {
		return nil, err
	}
	return result, nil
}

func (this *redisStorageImpl) PutRecord(info *PlacementInfo) error {
	ctx := context.Background()
	id := uniqueId(info.ActorType, info.ActorID)
	rdb, index := this.getDb(id)
	result, err := util.JSON(info)
	if err != nil {
		return err
	}
	log.Info("RedisStorage PutRecord",
		zap.String("ActorID", fmt.Sprintf("%s_%s", info.ActorType, info.ActorID)),
		zap.Uint64("RedisPoolIndex", index))
	_, err = rdb.Set(ctx, id, result, 0).Result()
	if err != nil {
		return err
	}
	return nil
}

func (this *redisStorageImpl) DeleteRecord(args *PlacementArgs) error {
	ctx := context.Background()
	id := uniqueId(args.ActorType, args.ActorID)
	rdb, _ := this.getDb(id)
	_, err := rdb.Del(ctx, id).Result()
	if err != nil {
		return err
	}
	return nil
}

func NewRedisStorageImpl(config string) *redisStorageImpl {
	array := strings.Split(config, ",")
	var clients []*redis.Client
	for _, v := range array {
		opt, err := redis.ParseURL(v)
		if err != nil {
			log.Error("NewRedisStorageImpl fail", zap.Error(err), zap.String("redis-urls", config))
			return nil
		}
		client := redis.NewClient(opt)
		clients = append(clients, client)
	}

	impl := &redisStorageImpl{
		clients: clients,
	}
	return impl
}
