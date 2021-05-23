from koala.sequence_id import SequenceId


_session_id_sequence = SequenceId()


def new_session_id() -> int:
    return _session_id_sequence.new_id()


def session_id_seed(seed: int):
    _session_id_sequence.set_seed(seed)
