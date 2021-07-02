package storage

type PlacementInfo struct {
	ActorID    string `json:"actor_id"`
	ActorType  string `json:"actor_type"`
	TTL        int64  `json:"ttl"`
	CreateTime int64  `json:"create_time"`
	ServerID   int64  `json:"server_id"`
}

type PlacementArgs struct {
	ActorID   string
	ActorType string
	TTL       int64
}

type PlacementStorage interface {
	Close()
	Name() string
	GetRecord(args *PlacementArgs) (*PlacementInfo, error)
	PutRecord(info *PlacementInfo) error
	DeleteRecord(args *PlacementArgs) error
}
