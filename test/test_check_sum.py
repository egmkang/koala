from koala import utils


def test_check_sum():
    input = b'{"open_id":"1", "server_id":2, "timestamp":1212121, "check_sum":"2b3c2c4505f72edccbae6accbde6f1293e7c8a39f2508a032eab616402bbac3b"}'
    private_key = "1234567890"

    message, check_sum = utils.message_check_sum(input, private_key)
    assert check_sum
