// Copyright 2016 TiKV Project Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// See the License for the specific language governing permissions and
// limitations under the License.

package config

import (
	"flag"
	"fmt"
	"github.com/BurntSushi/toml"
	"github.com/coreos/go-semver/semver"
	"github.com/pingcap/errors"
	"github.com/pingcap/log"
	"go.etcd.io/etcd/embed"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"net/url"
	"os"
	"path/filepath"
	"pd/server/errs"
	"strings"
	"time"
)

type Config struct {
	flagSet *flag.FlagSet

	Version bool `json:"-"`

	ConfigCheck bool `json:"-"`

	ClientUrls          string `toml:"client-urls" json:"client-urls"`
	PeerUrls            string `toml:"peer-urls" json:"peer-urls"`
	AdvertiseClientUrls string `toml:"advertise-client-urls" json:"advertise-client-urls"`
	AdvertisePeerUrls   string `toml:"advertise-peer-urls" json:"advertise-peer-urls"`

	Name            string `toml:"name" json:"name"`
	DataDir         string `toml:"data-dir" json:"data-dir"`
	ForceNewCluster bool   `json:"force-new-cluster"`

	InitialCluster      string `toml:"initial-cluster" json:"initial-cluster"`
	InitialClusterState string `toml:"initial-cluster-state" json:"initial-cluster-state"`
	InitialClusterToken string `toml:"initial-cluster-token" json:"initial-cluster-token"`

	RedisUrls string `toml:"redis-urls" json:"redis-urls"`

	// Join to an existing pd cluster, a string of endpoints.
	Join string `toml:"join" json:"join"`

	// LeaderLease time, if leader doesn't update its TTL
	// in etcd after lease time, etcd will expire the leader key
	// and other servers can campaign the leader again.
	// Etcd only supports seconds TTL, so here is second too.
	LeaderLease int64 `toml:"lease" json:"lease"`

	// Log related config.
	Log log.Config `toml:"log" json:"log"`

	// Backward compatibility.
	LogFileDeprecated  string `toml:"log-file" json:"log-file,omitempty"`
	LogLevelDeprecated string `toml:"log-level" json:"log-level,omitempty"`

	// TsoSaveInterval is the interval to save timestamp.
	TsoSaveInterval time.Duration `toml:"tso-save-interval" json:"tso-save-interval"`

	ClusterVersion semver.Version `toml:"cluster-version" json:"cluster-version"`

	// QuotaBackendBytes Raise alarms when backend size exceeds the given quota. 0 means use the default quota.
	// the default size is 2GB, the maximum is 8GB.
	QuotaBackendBytes uint64 `toml:"quota-backend-bytes" json:"quota-backend-bytes"`
	// AutoCompactionMode is either 'periodic' or 'revision'. The default value is 'periodic'.
	AutoCompactionMode string `toml:"auto-compaction-mode" json:"auto-compaction-mode"`
	// AutoCompactionRetention is either duration string with time unit
	// (e.g. '5m' for 5-minute), or revision unit (e.g. '5000').
	// If no time unit is provided and compaction mode is 'periodic',
	// the unit defaults to hour. For example, '5' translates into 5-hour.
	// The default retention is 1 hour.
	// Before etcd v3.3.x, the type of retention is int. We add 'v2' suffix to make it backward compatible.
	AutoCompactionRetention string `toml:"auto-compaction-retention" json:"auto-compaction-retention-v2"`

	// TickInterval is the interval for etcd Raft tick.
	TickInterval time.Duration `toml:"tick-interval"`
	// ElectionInterval is the interval for etcd Raft election.
	ElectionInterval time.Duration `toml:"election-interval"`
	// Prevote is true to enable Raft Pre-Vote.
	// If enabled, Raft runs an additional election phase
	// to check whether it would get enough votes to win
	// an election, thus minimizing disruptions.
	PreVote bool `toml:"enable-prevote"`

	configFile string

	// For all warnings during parsing.
	WarningMsgs []string

	// Only test can change them.
	nextRetryDelay             time.Duration
	DisableStrictReconfigCheck bool

	HeartbeatStreamBindInterval time.Duration

	LeaderPriorityCheckInterval time.Duration

	logger   *zap.Logger
	logProps *log.ZapProperties
}

func (c *Config) adjustLog(meta *configMetaData) {
	if !meta.IsDefined("disable-error-verbose") {
		c.Log.DisableErrorVerbose = defaultDisableErrorVerbose
	}
}

func adjustString(v *string, defValue string) {
	if len(*v) == 0 {
		*v = defValue
	}
}

func adjustUint64(v *uint64, defValue uint64) {
	if *v == 0 {
		*v = defValue
	}
}

func adjustInt64(v *int64, defValue int64) {
	if *v == 0 {
		*v = defValue
	}
}

func adjustFloat64(v *float64, defValue float64) {
	if *v == 0 {
		*v = defValue
	}
}

func adjustDuration(v *time.Duration, defValue time.Duration) {
	if *v == 0 {
		*v = defValue
	}
}

func adjustPath(p *string) {
	absPath, err := filepath.Abs(*p)
	if err == nil {
		*p = absPath
	}
}

// NewConfig creates a new config.
func NewConfig() *Config {
	cfg := &Config{}
	cfg.flagSet = flag.NewFlagSet("pd", flag.ContinueOnError)
	fs := cfg.flagSet

	fs.BoolVar(&cfg.Version, "V", false, "print version information and exit")
	fs.BoolVar(&cfg.Version, "version", false, "print version information and exit")
	fs.StringVar(&cfg.configFile, "config", "", "config file")
	fs.BoolVar(&cfg.ConfigCheck, "config-check", false, "check config file validity and exit")

	fs.StringVar(&cfg.Name, "name", "", "human-readable name for this pd member")

	fs.StringVar(&cfg.DataDir, "data-dir", "", "path to the data directory (default 'default.${name}')")
	fs.StringVar(&cfg.ClientUrls, "client-urls", defaultClientUrls, "url for client traffic")
	fs.StringVar(&cfg.AdvertiseClientUrls, "advertise-client-urls", "", "advertise url for client traffic (default '${client-urls}')")
	fs.StringVar(&cfg.PeerUrls, "peer-urls", defaultPeerUrls, "url for peer traffic")
	fs.StringVar(&cfg.AdvertisePeerUrls, "advertise-peer-urls", "", "advertise url for peer traffic (default '${peer-urls}')")
	fs.StringVar(&cfg.InitialCluster, "initial-cluster", "", "initial cluster configuration for bootstrapping, e,g. pd=http://127.0.0.1:2380")
	fs.StringVar(&cfg.Join, "join", "", "join to an existing cluster (usage: cluster's '${advertise-client-urls}'")

	fs.StringVar(&cfg.RedisUrls, "redis-urls", "", "set redis pool urls, e.g. redis://:password@localhost:6379/1,redis://:password@localhost:6379/2")
	fs.BoolVar(&cfg.ForceNewCluster, "force-new-cluster", false, "force to create a new one-member cluster")

	return cfg
}

// configFromFile loads config from file.
func (c *Config) configFromFile(path string) (*toml.MetaData, error) {
	meta, err := toml.DecodeFile(path, c)
	return &meta, errors.WithStack(err)
}

// Parse parses flag definitions from the argument list.
func (c *Config) Parse(arguments []string) error {
	// Parse first to get config file.
	err := c.flagSet.Parse(arguments)
	if err != nil {
		return errors.WithStack(err)
	}

	// Load config file if specified.
	var meta *toml.MetaData
	if c.configFile != "" {
		meta, err = c.configFromFile(c.configFile)
		if err != nil {
			return err
		}

		// Backward compatibility for toml config
		if c.LogFileDeprecated != "" {
			msg := fmt.Sprintf("log-file in %s is deprecated, use [log.file] instead", c.configFile)
			c.WarningMsgs = append(c.WarningMsgs, msg)
			if c.Log.File.Filename == "" {
				c.Log.File.Filename = c.LogFileDeprecated
			}
		}
		if c.LogLevelDeprecated != "" {
			msg := fmt.Sprintf("log-level in %s is deprecated, use [log] instead", c.configFile)
			c.WarningMsgs = append(c.WarningMsgs, msg)
			if c.Log.Level == "" {
				c.Log.Level = c.LogLevelDeprecated
			}
		}
		if meta.IsDefined("schedule", "disable-raft-learner") {
			msg := fmt.Sprintf("disable-raft-learner in %s is deprecated", c.configFile)
			c.WarningMsgs = append(c.WarningMsgs, msg)
		}
		if meta.IsDefined("dashboard", "disable-telemetry") {
			msg := fmt.Sprintf("disable-telemetry in %s is deprecated, use enable-telemetry instead", c.configFile)
			c.WarningMsgs = append(c.WarningMsgs, msg)
		}
	}

	// Parse again to replace with command line options.
	err = c.flagSet.Parse(arguments)
	if err != nil {
		return errors.WithStack(err)
	}

	if len(c.flagSet.Args()) != 0 {
		return errors.Errorf("'%s' is an invalid flag", c.flagSet.Arg(0))
	}

	err = c.Adjust(meta)

	return err
}

func (c *Config) SetupLogger() error {
	lg, p, err := log.InitLogger(&c.Log, zap.AddStacktrace(zapcore.FatalLevel))
	if err != nil {
		return errs.ErrInitLogger.Wrap(err).FastGenWithCause()
	}
	c.logger = lg
	c.logProps = p
	return nil
}

// GetZapLogger gets the created zap logger.
func (c *Config) GetZapLogger() *zap.Logger {
	return c.logger
}

// GetZapLogProperties gets properties of the zap logger.
func (c *Config) GetZapLogProperties() *log.ZapProperties {
	return c.logProps
}

// Utility to test if a configuration is defined.
type configMetaData struct {
	meta *toml.MetaData
	path []string
}

func newConfigMetadata(meta *toml.MetaData) *configMetaData {
	return &configMetaData{meta: meta}
}

func (m *configMetaData) IsDefined(key string) bool {
	if m.meta == nil {
		return false
	}
	keys := append([]string(nil), m.path...)
	keys = append(keys, key)
	return m.meta.IsDefined(keys...)
}

func (m *configMetaData) Child(path ...string) *configMetaData {
	newPath := append([]string(nil), m.path...)
	newPath = append(newPath, path...)
	return &configMetaData{
		meta: m.meta,
		path: newPath,
	}
}

func (m *configMetaData) CheckUndecoded() error {
	if m.meta == nil {
		return nil
	}
	undecoded := m.meta.Undecoded()
	if len(undecoded) == 0 {
		return nil
	}
	errInfo := "Config contains undefined item: "
	for _, key := range undecoded {
		errInfo += key.String() + ", "
	}
	return errors.New(errInfo[:len(errInfo)-2])
}

// Validate is used to validate if some configurations are right.
func (c *Config) Validate() error {
	if c.Join != "" && c.InitialCluster != "" {
		return errors.New("-initial-cluster and -join can not be provided at the same time")
	}
	dataDir, err := filepath.Abs(c.DataDir)
	if err != nil {
		return errors.WithStack(err)
	}
	logFile, err := filepath.Abs(c.Log.File.Filename)
	if err != nil {
		return errors.WithStack(err)
	}
	rel, err := filepath.Rel(dataDir, filepath.Dir(logFile))
	if err != nil {
		return errors.WithStack(err)
	}
	if !strings.HasPrefix(rel, "..") {
		return errors.New("log directory shouldn't be the subdirectory of data directory")
	}

	return nil
}

// Adjust is used to adjust the PD configurations.
func (c *Config) Adjust(meta *toml.MetaData) error {
	configMetaData := newConfigMetadata(meta)
	if err := configMetaData.CheckUndecoded(); err != nil {
		c.WarningMsgs = append(c.WarningMsgs, err.Error())
	}

	if c.Name == "" {
		hostname, err := os.Hostname()
		if err != nil {
			return err
		}
		adjustString(&c.Name, fmt.Sprintf("%s-%s", defaultName, hostname))
	}
	adjustString(&c.DataDir, fmt.Sprintf("default.%s", c.Name))
	adjustPath(&c.DataDir)

	if err := c.Validate(); err != nil {
		return err
	}

	adjustString(&c.ClientUrls, defaultClientUrls)
	adjustString(&c.AdvertiseClientUrls, c.ClientUrls)
	adjustString(&c.PeerUrls, defaultPeerUrls)
	adjustString(&c.AdvertisePeerUrls, c.PeerUrls)

	if len(c.InitialCluster) == 0 {
		// The advertise peer urls may be http://127.0.0.1:2380,http://127.0.0.1:2381
		// so the initial cluster is pd=http://127.0.0.1:2380,pd=http://127.0.0.1:2381
		items := strings.Split(c.AdvertisePeerUrls, ",")

		sep := ""
		for _, item := range items {
			c.InitialCluster += fmt.Sprintf("%s%s=%s", sep, c.Name, item)
			sep = ","
		}
	}

	adjustString(&c.InitialClusterState, defaultInitialClusterState)
	adjustString(&c.InitialClusterToken, defaultInitialClusterToken)

	if len(c.Join) > 0 {
		if _, err := url.Parse(c.Join); err != nil {
			return errors.Errorf("failed to parse join addr:%s, err:%v", c.Join, err)
		}
	}

	adjustInt64(&c.LeaderLease, defaultLeaderLease)

	adjustDuration(&c.TsoSaveInterval, time.Duration(defaultLeaderLease)*time.Second)

	if c.nextRetryDelay == 0 {
		c.nextRetryDelay = defaultNextRetryDelay
	}

	adjustString(&c.AutoCompactionMode, defaultCompactionMode)
	adjustString(&c.AutoCompactionRetention, defaultAutoCompactionRetention)
	if !configMetaData.IsDefined("quota-backend-bytes") {
		c.QuotaBackendBytes = defaultQuotaBackendBytes
	}
	adjustDuration(&c.TickInterval, defaultTickInterval)
	adjustDuration(&c.ElectionInterval, defaultElectionInterval)

	c.adjustLog(configMetaData.Child("log"))
	adjustDuration(&c.HeartbeatStreamBindInterval, defaultHeartbeatStreamRebindInterval)

	adjustDuration(&c.LeaderPriorityCheckInterval, defaultLeaderPriorityCheckInterval)

	if !configMetaData.IsDefined("enable-prevote") {
		c.PreVote = true
	}

	return nil
}

const (
	defaultLeaderLease             = int64(3)
	defaultNextRetryDelay          = time.Second
	defaultCompactionMode          = "periodic"
	defaultAutoCompactionRetention = "1h"
	defaultQuotaBackendBytes       = uint64(648 * 1024 * 1024 * 1024) // 8GB

	defaultName                = "pd"
	defaultClientUrls          = "http://127.0.0.1:2379"
	defaultPeerUrls            = "http://127.0.0.1:2380"
	defaultInitialClusterState = embed.ClusterStateFlagNew
	defaultInitialClusterToken = "pd-cluster"

	//TiDB需要跨机房, 所以心跳超时是500ms, 选举超时是3000ms
	//游戏的PD因为不需要跨机房, 所以可以把心跳超时和选举超时改成默认配置
	// etcd use 100ms for heartbeat and 1s for election timeout.
	// We can enlarge both a little to reduce the network aggression.
	// now embed etcd use TickMs for heartbeat, we will update
	// after embed etcd decouples tick and heartbeat.
	defaultTickInterval = 100 * time.Millisecond
	// embed etcd has a check that `5 * tick > election`
	defaultElectionInterval = 1000 * time.Millisecond

	defaultHeartbeatStreamRebindInterval = time.Minute

	defaultLeaderPriorityCheckInterval = time.Minute

	defaultDisableErrorVerbose = true
)

// ParseUrls parse a string into multiple urls.
// Export for api.
func ParseUrls(s string) ([]url.URL, error) {
	items := strings.Split(s, ",")
	urls := make([]url.URL, 0, len(items))
	for _, item := range items {
		u, err := url.Parse(item)
		if err != nil {
			return nil, errs.ErrURLParse.Wrap(err).GenWithStackByCause()
		}

		urls = append(urls, *u)
	}

	return urls, nil
}

// GenEmbedEtcdConfig generates a configuration for embedded etcd.
func (c *Config) GenEmbedEtcdConfig() (*embed.Config, error) {
	cfg := embed.NewConfig()
	cfg.Name = c.Name
	cfg.Dir = c.DataDir
	cfg.WalDir = ""
	cfg.InitialCluster = c.InitialCluster
	cfg.ClusterState = c.InitialClusterState
	cfg.InitialClusterToken = c.InitialClusterToken
	cfg.EnablePprof = true
	cfg.PreVote = c.PreVote
	cfg.StrictReconfigCheck = !c.DisableStrictReconfigCheck
	cfg.TickMs = uint(c.TickInterval / time.Millisecond)
	cfg.ElectionMs = uint(c.ElectionInterval / time.Millisecond)
	cfg.AutoCompactionMode = c.AutoCompactionMode
	cfg.AutoCompactionRetention = c.AutoCompactionRetention
	cfg.QuotaBackendBytes = int64(c.QuotaBackendBytes)

	cfg.ForceNewCluster = c.ForceNewCluster
	cfg.ZapLoggerBuilder = embed.NewZapCoreLoggerBuilder(c.logger, c.logger.Core(), c.logProps.Syncer)
	cfg.EnableV2 = true
	cfg.Logger = "zap"
	var err error

	cfg.LPUrls, err = ParseUrls(c.PeerUrls)
	if err != nil {
		return nil, err
	}

	cfg.APUrls, err = ParseUrls(c.AdvertisePeerUrls)
	if err != nil {
		return nil, err
	}

	cfg.LCUrls, err = ParseUrls(c.ClientUrls)
	if err != nil {
		return nil, err
	}

	cfg.ACUrls, err = ParseUrls(c.AdvertiseClientUrls)
	if err != nil {
		return nil, err
	}

	return cfg, nil
}
