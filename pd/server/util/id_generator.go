package util

import (
	"github.com/pingcap/errors"
	"github.com/pingcap/log"
	"go.etcd.io/etcd/clientv3"
	"go.uber.org/zap"
	"sync"
)

const MaxRetryCount = 5

type IdGenerator struct {
	mutex   sync.Mutex
	path    string
	current int64
	end     int64
	step    int64
}

func NewIdGenerator(path string, step int64) *IdGenerator {
	return &IdGenerator{
		mutex:   sync.Mutex{},
		path:    path,
		current: 0,
		end:     0,
		step:    step,
	}
}

func (this *IdGenerator) GetNewID(client *clientv3.Client) (int64, error) {
	this.mutex.Lock()
	defer this.mutex.Unlock()

	if this.current == this.end {
		//尝试多次
		i := 0
		for ; i < MaxRetryCount; i++ {
			newEnd, err := this.tryGenerateNewID(client)
			if err != nil {
				return 0, err
			}

			if newEnd == -1 {
				continue
			}

			this.current = newEnd - this.step
			this.end = newEnd
			break
		}
		if i >= MaxRetryCount {
			return 0, errors.Errorf("need retry")
		}
	}
	this.current++
	return this.current, nil
}

//-1: need retry
func (this *IdGenerator) tryGenerateNewID(client *clientv3.Client) (int64, error) {
	value, err := EtcdGetKVValue(client, this.path)
	if err != nil {
		return 0, err
	}
	var cmp clientv3.Cmp

	if value == nil {
		cmp = clientv3.Compare(clientv3.CreateRevision(this.path), "=", 0)
	} else {
		cmp = clientv3.Compare(clientv3.Value(this.path), "=", string(value))
	}
	number, _ := BytesToInt64(value)
	number += this.step
	newValue := Int64ToBytes(number)

	resp, err := Txn(client).If(cmp).Then(clientv3.OpPut(this.path, string(newValue))).Commit()

	if err != nil {
		return 0, err
	}

	if !resp.Succeeded {
		return -1, nil
	}

	//TODO: metrics
	log.Info("IdGenerator allocates new id", zap.String("path", this.path), zap.Int64("value", number))
	return number, nil
}
