"""
Unit tests for the ContractId class.
"""

import pytest

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import basic_types_pb2

pytestmark = pytest.mark.unit


def test_default_initialization():
    """Test ContractId initialization with default values."""
    contract_id = ContractId()

    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0
    assert contract_id.evm_address is None


def test_custom_initialization():
    """Test ContractId initialization with custom values."""
    contract_id = ContractId(shard=1, realm=2, contract=3)

    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address is None


def test_str_representation():
    """Test string representation of ContractId."""
    contract_id = ContractId(shard=1, realm=2, contract=3)

    assert str(contract_id) == "1.2.3"
    assert contract_id.evm_address is None


def test_str_representation_default():
    """Test string representation of ContractId with default values."""
    contract_id = ContractId()

    assert str(contract_id) == "0.0.0"
    assert contract_id.evm_address is None


def test_from_string_valid():
    """Test creating ContractId from valid string format."""
    contract_id = ContractId.from_string("1.2.3")

    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address is None


def test_from_string_with_spaces():
    """Test creating ContractId from string with leading/trailing spaces."""
    contract_id = ContractId.from_string("  1.2.3  ")

    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address is None


def test_from_string_zeros():
    """Test creating ContractId from string with zero values."""
    contract_id = ContractId.from_string("0.0.0")

    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0
    assert contract_id.evm_address is None


def test_from_string_invalid_format_too_few_parts():
    """Test creating ContractId from invalid string format with too few parts."""
    with pytest.raises(
        ValueError, match="Invalid ContractId format. Expected 'shard.realm.contract'"
    ):
        ContractId.from_string("1.2")


def test_from_string_invalid_format_too_many_parts():
    """Test creating ContractId from invalid string format with too many parts."""
    with pytest.raises(
        ValueError, match="Invalid ContractId format. Expected 'shard.realm.contract'"
    ):
        ContractId.from_string("1.2.3.4")


def test_from_string_invalid_format_non_numeric():
    """Test creating ContractId from invalid string format with non-numeric parts."""
    with pytest.raises(ValueError):
        ContractId.from_string("a.b.c")


def test_from_string_invalid_format_empty():
    """Test creating ContractId from empty string."""
    with pytest.raises(
        ValueError, match="Invalid ContractId format. Expected 'shard.realm.contract'"
    ):
        ContractId.from_string("")


def test_from_string_invalid_format_partial_numeric():
    """Test creating ContractId from string with some non-numeric parts."""
    with pytest.raises(ValueError):
        ContractId.from_string("1.a.3")


def test_to_proto():
    """Test converting ContractId to protobuf format."""
    contract_id = ContractId(shard=1, realm=2, contract=3)
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 3


def test_to_proto_default_values():
    """Test converting ContractId with default values to protobuf format."""
    contract_id = ContractId()
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.contractNum == 0


def test_from_proto():
    """Test creating ContractId from protobuf format."""
    proto = basic_types_pb2.ContractID(shardNum=1, realmNum=2, contractNum=3)

    contract_id = ContractId._from_proto(proto)

    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3


def test_from_proto_zero_values():
    """Test creating ContractId from protobuf format with zero values."""
    proto = basic_types_pb2.ContractID(shardNum=0, realmNum=0, contractNum=0)

    contract_id = ContractId._from_proto(proto)

    assert contract_id.shard == 0
    assert contract_id.realm == 0
    assert contract_id.contract == 0


def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    original = ContractId(shard=5, realm=10, contract=15)
    proto = original._to_proto()
    reconstructed = ContractId._from_proto(proto)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.contract == reconstructed.contract


def test_roundtrip_string_conversion():
    """Test that converting to string and back preserves values."""
    original = ContractId(shard=7, realm=14, contract=21)
    string_repr = str(original)
    reconstructed = ContractId.from_string(string_repr)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.contract == reconstructed.contract


def test_equality():
    """Test ContractId equality comparison."""
    contract_id1 = ContractId(shard=1, realm=2, contract=3)
    contract_id2 = ContractId(shard=1, realm=2, contract=3)
    contract_id3 = ContractId(shard=1, realm=2, contract=4)

    assert contract_id1 == contract_id2
    assert contract_id1 != contract_id3


def test_evm_address_initialization():
    """Test ContractId initialization with EVM address."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address)

    assert contract_id.shard == 1
    assert contract_id.realm == 2
    assert contract_id.contract == 3
    assert contract_id.evm_address == evm_address


def test_evm_address_to_proto():
    """Test converting ContractId with EVM address to protobuf format."""
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address)
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 0
    assert proto.evm_address == evm_address


def test_evm_address_to_proto_none():
    """Test converting ContractId with None EVM address to protobuf format."""
    contract_id = ContractId(shard=1, realm=2, contract=3, evm_address=None)
    proto = contract_id._to_proto()

    assert isinstance(proto, basic_types_pb2.ContractID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.contractNum == 3
    assert proto.evm_address == b""


def test_evm_address_equality():
    """Test ContractId equality with EVM addresses."""
    evm_address1 = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    evm_address2 = bytes.fromhex("1234567890abcdef1234567890abcdef12345678")

    contract_id1 = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id2 = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id3 = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address2)
    contract_id4 = ContractId(shard=1, realm=2, contract=3, evm_address=None)

    # Same EVM address should be equal
    assert contract_id1 == contract_id2

    # Different EVM addresses should not be equal
    assert contract_id1 != contract_id3

    # None EVM address should not be equal to one with EVM address
    assert contract_id1 != contract_id4


def test_evm_address_hash():
    """Test ContractId hash with EVM addresses."""
    evm_address1 = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    evm_address2 = bytes.fromhex("1234567890abcdef1234567890abcdef12345678")

    contract_id1 = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id2 = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address1)
    contract_id3 = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address2)

    # Same EVM address should have same hash
    assert hash(contract_id1) == hash(contract_id2)

    # Different EVM addresses should have different hashes
    assert hash(contract_id1) != hash(contract_id3)

def test_to_evm_address():
    """Test ContractId.to_evm_address() for both explicit and computed EVM addresses."""
    # Explicit EVM address
    evm_address = bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
    contract_id = ContractId(shard=1, realm=2, contract=3, evm_address=evm_address)
    assert contract_id.to_evm_address() == evm_address.hex()

    # Computed EVM address (no explicit evm_address)
    contract_id = ContractId(shard=1, realm=2, contract=3)
    # [4 bytes shard][8 bytes realm][8 bytes contract], all big-endian
    expected_bytes = (
        (0).to_bytes(4, "big") +
        (0).to_bytes(8, "big") +
        (3).to_bytes(8, "big")
    )
    assert contract_id.to_evm_address() == expected_bytes.hex()

    # Default values
    contract_id = ContractId()
    expected_bytes = (
        (0).to_bytes(4, "big") +
        (0).to_bytes(8, "big") +
        (0).to_bytes(8, "big")
    )
    assert contract_id.to_evm_address() == expected_bytes.hex()
