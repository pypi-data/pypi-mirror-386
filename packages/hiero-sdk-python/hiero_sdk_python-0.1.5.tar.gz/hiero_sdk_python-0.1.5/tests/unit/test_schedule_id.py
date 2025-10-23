import pytest

from hiero_sdk_python.hapi.services.basic_types_pb2 import ScheduleID
from hiero_sdk_python.schedule.schedule_id import ScheduleId

pytestmark = pytest.mark.unit


def test_default_initialization():
    """Test ScheduleId initialization with default values."""
    schedule_id = ScheduleId()

    assert schedule_id.shard == 0
    assert schedule_id.realm == 0
    assert schedule_id.schedule == 0


def test_custom_initialization():
    """Test ScheduleId initialization with custom values."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3


def test_str_representation():
    """Test string representation of ScheduleId."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    assert str(schedule_id) == "1.2.3"


def test_str_representation_default():
    """Test string representation of ScheduleId with default values."""
    schedule_id = ScheduleId()

    assert str(schedule_id) == "0.0.0"


def test_from_string_valid():
    """Test creating ScheduleId from valid string format."""
    schedule_id = ScheduleId.from_string("1.2.3")

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3


def test_from_string_with_spaces():
    """Test creating ScheduleId from string with leading/trailing spaces."""
    schedule_id = ScheduleId.from_string("  1.2.3  ")

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3


def test_from_string_invalid_formats():
    """Test creating ScheduleId from various invalid string formats."""
    invalid_formats = [
        "1.2",  # Too few parts
        "1.2.3.4",  # Too many parts
        "a.b.c",  # Non-numeric parts
        "",  # Empty string
        "1.a.3",  # Partial numeric
    ]

    for invalid_format in invalid_formats:
        with pytest.raises(ValueError):
            ScheduleId.from_string(invalid_format)


def test_to_proto():
    """Test converting ScheduleId to protobuf format."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)
    proto = schedule_id._to_proto()

    assert isinstance(proto, ScheduleID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.scheduleNum == 3


def test_from_proto():
    """Test creating ScheduleId from protobuf format."""
    proto = ScheduleID(shardNum=1, realmNum=2, scheduleNum=3)

    schedule_id = ScheduleId._from_proto(proto)

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3


def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    original = ScheduleId(shard=5, realm=10, schedule=15)
    proto = original._to_proto()
    reconstructed = ScheduleId._from_proto(proto)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.schedule == reconstructed.schedule


def test_roundtrip_string_conversion():
    """Test that converting to string and back preserves values."""
    original = ScheduleId(shard=7, realm=14, schedule=21)
    string_repr = str(original)
    reconstructed = ScheduleId.from_string(string_repr)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.schedule == reconstructed.schedule


def test_equality():
    """Test ScheduleId equality comparison."""
    schedule_id1 = ScheduleId(shard=1, realm=2, schedule=3)
    schedule_id2 = ScheduleId(shard=1, realm=2, schedule=3)
    schedule_id3 = ScheduleId(shard=1, realm=2, schedule=4)

    assert schedule_id1 == schedule_id2
    assert schedule_id1 != schedule_id3


def test_equality_different_type():
    """Test ScheduleId equality comparison with different type."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    # Should not raise an exception and should return False
    assert schedule_id != "1.2.3"
