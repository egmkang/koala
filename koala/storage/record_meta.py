from abc import ABC, abstractmethod
from pydantic import BaseModel
from koala.typing import *
from koala import utils
from dataclasses import dataclass
from koala.storage.record import Record


RecordType = TypeVar("RecordType", bound=Record)


# 最多可以通过两列组成主键
@dataclass
class KeyInfo:
    key_name: str
    key_type: Type
    key_name_2: Optional[str]
    key_type_2: Optional[Type]


@dataclass
class RecordMetaData:
    table_name: str
    key_info: KeyInfo


__global_dict: Dict[Type, RecordMetaData] = dict()


def get_record_meta(record_type: Type[RecordType]) -> Optional[RecordMetaData]:
    if record_type in __global_dict:
        return __global_dict[record_type]
    return None


def record_meta(table_name: str,
                key_name: str, key_type: Type,
                key_name_2: Optional[str] = None, key_type_2: Optional[Type] = None):
    def f(clz: Type[RecordType]):
        global __global_dict
        meta_data = RecordMetaData(table_name=table_name, key_info=KeyInfo(key_name, key_type, key_name_2, key_type_2))
        __global_dict[clz] = meta_data
        return clz
    return f
