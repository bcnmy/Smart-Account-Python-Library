from eth_abi import encode, is_encodable
from typing import List, Tuple, Union
from eth_utils import keccak


class UserOperation:
    """
    Represents a user operation containing all the necessary information for execution.

    Attributes:
        sender (str): Address of the sender.
        nonce (int): Nonce for the operation.
        init_code (bytes): Initialization code.
        call_data (bytes): Data for the call.
        call_gas_limit (int): Gas limit for the call.
        verification_gas_limit (int): Gas limit for verification.
        pre_verification_gas (int): Gas limit for pre-verification.
        max_fee_per_gas (int): Maximum fee per gas.
        max_priority_fee_per_gas (int): Maximum priority fee per gas.
        paymaster_and_data (bytes): Paymaster and data.
        signature (bytes): Signature of the user operation.
    """

    def __init__(
        self,
        sender: str,
        nonce: int,
        init_code: bytes,
        call_data: bytes,
        call_gas_limit: int,
        verification_gas_limit: int,
        pre_verification_gas: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        paymaster_and_data: bytes,
        signature: bytes,
    ):
        """
        Initializes a UserOperation instance.

        Args:
            sender (str): Address of the sender.
            nonce (int): Nonce for the operation.
            init_code (bytes): Initialization code.
            call_data (bytes): Data for the call.
            call_gas_limit (int): Gas limit for the call.
            verification_gas_limit (int): Gas limit for verification.
            pre_verification_gas (int): Gas limit for pre-verification.
            max_fee_per_gas (int): Maximum fee per gas.
            max_priority_fee_per_gas (int): Maximum priority fee per gas.
            paymaster_and_data (bytes): Paymaster and data.
            signature (bytes): Signature of the user operation.

        Raises:
            ValueError: If any attribute value is not encodable as the expected type.
        """
        # Check if all attributes are encodable
        attributes: List[Tuple[str, Union[str, int, bytes]]] = [
            ("address", sender),
            ("uint256", nonce),
            ("bytes", init_code),
            ("bytes", call_data),
            ("uint256", call_gas_limit),
            ("uint256", verification_gas_limit),
            ("uint256", pre_verification_gas),
            ("uint256", max_fee_per_gas),
            ("uint256", max_priority_fee_per_gas),
            ("bytes", paymaster_and_data),
            ("bytes", signature),
        ]

        encodable = UserOperationLib.check_encodability(attributes)
        if not encodable[0]:
            raise ValueError(
                f"Attribute value '{encodable[2]}' is not encodable as type '{encodable[1]}'"
            )

        self.sender: str = sender
        self.nonce: int = nonce
        self.init_code: bytes = init_code
        self.call_data: bytes = call_data
        self.call_gas_limit: int = call_gas_limit
        self.verification_gas_limit: int = verification_gas_limit
        self.pre_verification_gas: int = pre_verification_gas
        self.max_fee_per_gas: int = max_fee_per_gas
        self.max_priority_fee_per_gas: int = max_priority_fee_per_gas
        self.paymaster_and_data: bytes = paymaster_and_data
        self.signature: bytes = signature

    def __repr__(self) -> str:
        """
        Returns a string representation of the UserOperation instance.

        Returns:
            str: String representation of the UserOperation instance.
        """
        return (
            f"UserOperation(sender={self.sender}, nonce={self.nonce}, init_code={self.init_code}, "
            f"call_data={self.call_data}, call_gas_limit={self.call_gas_limit}, verification_gas_limit={self.verification_gas_limit}, "
            f"pre_verification_gas={self.pre_verification_gas}, max_fee_per_gas={self.max_fee_per_gas}, "
            f"max_priority_fee_per_gas={self.max_priority_fee_per_gas}, paymaster_and_data={self.paymaster_and_data}, "
            f"signature={self.signature})"
        )


class UserOperationLib:
    """
    Library for operations on UserOperation instances.
    """

    @staticmethod
    def get_sender(userop: UserOperation) -> str:
        """
        Returns the sender address of the given UserOperation.

        Args:
            userop (UserOperation): The UserOperation instance.

        Returns:
            str: The sender address.
        """
        return userop.sender

    @staticmethod
    def gas_price(userop: UserOperation, block_base_fee: int) -> int:
        """
        Calculates the gas price for the given UserOperation.

        Args:
            userop (UserOperation): The UserOperation instance.
            block_base_fee (int): The base fee of the current block.

        Returns:
            int: The gas price.
        """
        max_fee_per_gas = userop.max_fee_per_gas
        max_priority_fee_per_gas = userop.max_priority_fee_per_gas

        if max_fee_per_gas == max_priority_fee_per_gas:
            return max_fee_per_gas

        return min(max_fee_per_gas, max_priority_fee_per_gas + block_base_fee)

    @staticmethod
    def pack(userop: UserOperation) -> bytes:
        """
        Packs the UserOperation attributes into a byte array.

        Args:
            userop (UserOperation): The UserOperation instance.

        Returns:
            bytes: Packed byte array of the UserOperation attributes.
        """
        hash_init_code = keccak(userop.init_code)
        hash_call_data = keccak(userop.call_data)
        hash_paymaster_and_data = keccak(userop.paymaster_and_data)

        packed = encode(
            [
                "address",
                "uint256",
                "bytes32",
                "bytes32",
                "uint256",
                "uint256",
                "uint256",
                "uint256",
                "uint256",
                "bytes32",
            ],
            [
                userop.sender,
                userop.nonce,
                hash_init_code,
                hash_call_data,
                userop.call_gas_limit,
                userop.verification_gas_limit,
                userop.pre_verification_gas,
                userop.max_fee_per_gas,
                userop.max_priority_fee_per_gas,
                hash_paymaster_and_data,
            ],
        )

        return packed

    @staticmethod
    def hash(userop: UserOperation, entry_point_address: str, chain_id: int) -> bytes:
        """
        Hashes the UserOperation as specified by ERC4337.

        Args:
            userop (UserOperation): The UserOperation instance.
            entry_point_address (str): The entry point address.
            chain_id (int): The chain ID.

        Returns:
            bytes: Hash of the packed UserOperation attributes.
        """
        packed_userop = UserOperationLib.pack(userop)
        packed_userop_hash = keccak(packed_userop)
        encoded_hash = encode(
            ["bytes32", "address", "uint256"],
            [packed_userop_hash, entry_point_address, chain_id],
        )
        return keccak(encoded_hash)

    @staticmethod
    def min(a: int, b: int) -> int:
        """
        Returns the minimum of two integers.

        Args:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The minimum of the two integers.
        """
        return a if a < b else b

    @staticmethod
    def check_encodability(
        attributes: List[Tuple[str, Union[str, int, bytes]]],
    ) -> Tuple[bool, Union[str, None], Union[str, int, bytes, None]]:
        """
        Checks if the given attributes are encodable.

        Args:
            attributes (List[Tuple[str, Union[str, int, bytes]]]): The list of attributes to check.

        Returns:
            Tuple[bool, Union[str, None], Union[str, int, bytes, None]]:
                - bool: Whether all attributes are encodable.
                - str or None: The type of the first non-encodable attribute, or None if all are encodable.
                - str, int, bytes, or None: The value of the first non-encodable attribute, or None if all are encodable.
        """
        for typ, value in attributes:
            if not is_encodable(typ, value):
                return (False, typ, value)
        return (True, None, None)

    @staticmethod
    def marshal_partial_userop(userop: UserOperation) -> dict[str, str]:
        """
        Marshals a UserOperation into a dictionary, excluding certain attributes.

        Args:
            userop (UserOperation): The UserOperation instance.

        Returns:
            dict[str, str]: The marshaled UserOperation.
        """
        return {
            "sender": userop.sender,
            "nonce": hex(userop.nonce),
            "initCode": "0x" + userop.init_code.hex(),
            "callData": "0x" + userop.call_data.hex(),
            "paymasterAndData": "0x" + userop.paymaster_and_data.hex(),
            "signature": "0x" + userop.signature.hex(),
        }

    @staticmethod
    def marshal_userop(userop: UserOperation) -> dict[str, str]:
        """
        Marshals a UserOperation into a dictionary.

        Args:
            userop (UserOperation): The UserOperation instance.

        Returns:
            dict[str, str]: The marshaled UserOperation.
        """
        return {
            "sender": userop.sender,
            "nonce": hex(userop.nonce),
            "initCode": "0x" + userop.init_code.hex(),
            "callData": "0x" + userop.call_data.hex(),
            "callGasLimit": hex(userop.call_gas_limit),
            "verificationGasLimit": hex(userop.verification_gas_limit),
            "preVerificationGas": hex(userop.pre_verification_gas),
            "maxFeePerGas": hex(userop.max_fee_per_gas),
            "maxPriorityFeePerGas": hex(userop.max_priority_fee_per_gas),
            "paymasterAndData": "0x" + userop.paymaster_and_data.hex(),
            "signature": "0x" + userop.signature.hex(),
        }

    @staticmethod
    def unmarshal_userop(userop: dict) -> UserOperation:
        """
        Unmarshals a dictionary into a UserOperation instance.

        Args:
            userop (dict): The dictionary containing the UserOperation data.

        Returns:
            UserOperation: The unmarshaled UserOperation instance.
        """
        return UserOperation(
            sender=userop["sender"],
            nonce=int(userop["nonce"], 16),
            init_code=bytes.fromhex(userop["initCode"][2:]),
            call_data=bytes.fromhex(userop["callData"][2:]),
            call_gas_limit=int(userop["callGasLimit"], 16),
            verification_gas_limit=int(userop["verificationGasLimit"], 16),
            pre_verification_gas=int(userop["preVerificationGas"], 16),
            max_fee_per_gas=int(userop["maxFeePerGas"], 16),
            max_priority_fee_per_gas=int(userop["maxPriorityFeePerGas"], 16),
            paymaster_and_data=bytes.fromhex(userop["paymasterAndData"][2:]),
            signature=bytes.fromhex(userop["signature"][2:]),
        )
