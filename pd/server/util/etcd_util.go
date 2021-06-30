package util

import (
	"context"
	"github.com/pingcap/log"
	"github.com/pkg/errors"
	"go.etcd.io/etcd/clientv3"
	"go.etcd.io/etcd/clientv3/concurrency"
	"go.uber.org/zap"
	"time"
)

const DefaultRequestTimeout = time.Second * 5
const DefaultSlowRequest = time.Second * 1

func EtcdLeaseGrant(client *clientv3.Client, ttl int64) (*clientv3.LeaseGrantResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()

	start := time.Now()
	resp, err := clientv3.NewLease(client).Grant(ctx, ttl)
	if err != nil {
		log.Error("EtcdLeaseGrant", zap.Error(err))
	}
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdLeaseGrant get too slow", zap.Duration("cost", cost), zap.Error(err))
	}
	return resp, errors.WithStack(err)
}

func EtcdLeaseKeepAliveOnce(client *clientv3.Client, leaseID int64) (*clientv3.LeaseKeepAliveResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()

	start := time.Now()
	resp, err := clientv3.NewLease(client).KeepAliveOnce(ctx, clientv3.LeaseID(leaseID))
	if err != nil {
		log.Error("EtcdLeaseKeepAliveOnce", zap.Error(err))
	}
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdLeaseKeepAliveOnce get too slow", zap.Duration("cost", cost), zap.Error(err))
	}
	return resp, errors.WithStack(err)
}

func EtcdLeaseRevoke(client *clientv3.Client, leaseID int64) (*clientv3.LeaseRevokeResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()

	start := time.Now()
	resp, err := clientv3.NewLease(client).Revoke(ctx, clientv3.LeaseID(leaseID))
	if err != nil {
		log.Error("EtcdLeaseRevoke", zap.Error(err))
	}
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdLeaseRevoke get too slow", zap.Duration("cost", cost), zap.Error(err))
	}
	return resp, errors.WithStack(err)
}

func EtcdKVDelete(client *clientv3.Client, key string, opts ...clientv3.OpOption) (*clientv3.DeleteResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()

	start := time.Now()
	resp, err := clientv3.NewKV(client).Delete(ctx, key, opts...)
	if err != nil {
		log.Error("EtcdKVDelete error", zap.Error(err))
	}
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdKVDelete get too slow", zap.String("key", key), zap.Duration("cost", cost), zap.Error(err))
	}
	return resp, errors.WithStack(err)
}

func EtcdKVPut(client *clientv3.Client, key string, value string, opts ...clientv3.OpOption) (*clientv3.PutResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()

	start := time.Now()
	resp, err := clientv3.NewKV(client).Put(ctx, key, value, opts...)
	if err != nil {
		log.Error("EtcdKVPut error", zap.Error(err))
	}
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdKVPut get too slow", zap.String("key", key), zap.Duration("cost", cost), zap.Error(err))
	}
	return resp, errors.WithStack(err)
}

func EtcdKVGet(client *clientv3.Client, key string, opts ...clientv3.OpOption) (*clientv3.GetResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()

	start := time.Now()
	resp, err := clientv3.NewKV(client).Get(ctx, key, opts...)
	if err != nil {
		log.Error("EtcdKVGet error", zap.Error(err))
	}
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdKVGet get too slow", zap.String("key", key), zap.Duration("cost", cost), zap.Error(err))
	}
	return resp, errors.WithStack(err)
}

func getKV(client *clientv3.Client, key string, opts ...clientv3.OpOption) (*clientv3.GetResponse, error) {
	resp, err := EtcdKVGet(client, key, opts...)
	if err != nil {
		return nil, err
	}
	if n := len(resp.Kvs); n == 0 {
		return nil, nil
	} else if n > 1 {
		return nil, errors.Errorf("invalid get value resp %v", resp.Kvs)
	}
	return resp, nil
}

func EtcdGetKVValue(client *clientv3.Client, key string, opts ...clientv3.OpOption) ([]byte, error) {
	resp, err := getKV(client, key, opts...)
	if err != nil {
		return nil, err
	}
	if resp == nil {
		return nil, nil
	}
	return resp.Kvs[0].Value, nil
}

func EtcdListMembers(client *clientv3.Client) (*clientv3.MemberListResponse, error) {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	defer cancel()
	listResp, err := client.MemberList(ctx)
	return listResp, errors.WithStack(err)
}

type slowLogTxn struct {
	clientv3.Txn
	cancel context.CancelFunc
}

func Txn(client *clientv3.Client) clientv3.Txn {
	ctx, cancel := context.WithTimeout(client.Ctx(), DefaultRequestTimeout)
	return &slowLogTxn{
		Txn:    client.Txn(ctx),
		cancel: cancel,
	}
}

func (this *slowLogTxn) If(cs ...clientv3.Cmp) clientv3.Txn {
	return &slowLogTxn{
		Txn:    this.Txn.If(cs...),
		cancel: this.cancel,
	}
}

func (this *slowLogTxn) Then(op ...clientv3.Op) clientv3.Txn {
	return &slowLogTxn{
		Txn:    this.Txn.Then(op...),
		cancel: this.cancel,
	}
}

func (this *slowLogTxn) Commit() (*clientv3.TxnResponse, error) {
	start := time.Now()
	defer this.cancel()
	resp, err := this.Txn.Commit()

	cost := time.Since(start)
	if cost > DefaultSlowRequest {
		log.Warn("txn too slow", zap.Error(err), zap.Reflect("resp", resp), zap.Duration("cost", cost))
	}

	//TODO: metrics

	return resp, errors.WithStack(err)
}

type EtcdMutex struct {
	session *concurrency.Session
	name    string
	mutex   *concurrency.Mutex
}

var defaultEtcdMutexTimeout = concurrency.WithTTL(10)

func NewMutex(client *clientv3.Client, name string, opts ...concurrency.SessionOption) (*EtcdMutex, error) {
	var optstemp = make([]concurrency.SessionOption, 0)
	optstemp = append(optstemp, defaultEtcdMutexTimeout)
	optstemp = append(optstemp, opts...)
	session, err := concurrency.NewSession(client, optstemp...)

	if err != nil {
		return nil, errors.WithStack(err)
	}
	mutex := concurrency.NewMutex(session, name)
	return &EtcdMutex{session: session, name: name, mutex: mutex}, nil
}

func (this *EtcdMutex) Lock() error {
	start := time.Now()
	err := this.mutex.Lock(context.TODO())
	if cost := time.Since(start); cost > DefaultSlowRequest {
		log.Warn("EtcdMutex get too slow", zap.Duration("cost", cost), zap.Error(err))
	}
	return err
}

func (this *EtcdMutex) Unlock() {
	this.mutex.Unlock(context.TODO())
}

func (this *EtcdMutex) Close() {
	this.session.Close()
}

func (this *EtcdMutex) AsyncClose() {
	go this.session.Close()
}
