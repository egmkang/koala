from koala.sequence_id import SequenceId

_request_id = SequenceId()
_reentrant_id = SequenceId()


def set_request_id_seed(seed: int):
    _request_id.set_seed(seed)


def new_request_id() -> int:
    return _request_id.new_id()


def set_reentrant_id_seed(seed: int):
    _reentrant_id.set_seed(seed)


def new_reentrant_id() -> int:
    return _reentrant_id.new_id()
