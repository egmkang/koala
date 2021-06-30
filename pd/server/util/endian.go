package util

import (
	"encoding/binary"
	"github.com/pkg/errors"
)

func BytesToInt64(b []byte) (int64, error) {
	if len(b) != 8 {
		return 0, errors.Errorf("must intput 8 byte, but %d", len(b))
	}
	return int64(binary.LittleEndian.Uint64(b)), nil
}

func Int64ToBytes(v int64) []byte {
	b := make([]byte, 8)
	binary.LittleEndian.PutUint64(b, uint64(v))
	return b
}
