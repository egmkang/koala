package storage

import (
	"fmt"
	"sync"
)

const EngineMemory = "memory"

type memoryStorageImpl struct {
	mutex sync.Mutex
	dict  map[string]*PlacementInfo
}

func NewMemoryStorage() PlacementStorage {
	return &memoryStorageImpl{
		mutex: sync.Mutex{},
		dict:  make(map[string]*PlacementInfo),
	}
}

func (this *memoryStorageImpl) Close() {
	this.mutex.Lock()
	defer this.mutex.Unlock()
	this.dict = make(map[string]*PlacementInfo)
}

func placementKey(args *PlacementArgs) string {
	return fmt.Sprintf("%s/%s", args.ActorType, args.ActorID)
}

func (this *memoryStorageImpl) GetRecord(args *PlacementArgs) (*PlacementInfo, error) {
	this.mutex.Lock()
	defer this.mutex.Unlock()
	key := placementKey(args)
	v, ok := this.dict[key]
	if ok {
		return v, nil
	}
	return nil, nil
}

func (this *memoryStorageImpl) PutRecord(info *PlacementInfo) error {
	this.mutex.Lock()
	defer this.mutex.Unlock()
	key := placementKey(&PlacementArgs{
		ActorID:   info.ActorID,
		ActorType: info.ActorType,
	})
	this.dict[key] = info
	return nil
}

func (this *memoryStorageImpl) DeleteRecord(args *PlacementArgs) error {
	this.mutex.Lock()
	defer this.mutex.Unlock()
	key := placementKey(args)
	delete(this.dict, key)
	return nil
}

func (this *memoryStorageImpl) Name() string {
	return EngineMemory
}
