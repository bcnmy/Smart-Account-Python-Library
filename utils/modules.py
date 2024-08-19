from enum import Enum
from eth_abi import encode
import utils.constants as constants
from web3 import Web3
from web3.contract.contract import Contract

class ValidationModule(Enum):
    """
    Enum representing the different validation modules available.

    Attributes:
        ECDSA (int): Represents the ECDSA validation module.
        SESSION_KEY_MANAGER_V1 (int): Represents the Session Key Manager V1 validation module.
    """

    ECDSA = 1
    SESSION_KEY_MANAGER_V1 = 2

    def get_address(self) -> str:
        """
        Retrieves the contract address associated with the validation module.

        Returns:
            str: The contract address corresponding to the selected validation module.

        Raises:
            ValueError: If the validation module is not recognized.
        """
        if self == ValidationModule.ECDSA:
            return constants.ECDSA_OWNERSHIP_MODULE
        elif self == ValidationModule.SESSION_KEY_MANAGER_V1:
            return constants.SESSION_KEY_MANAGER_V1
        else:
            raise ValueError(f"Unknown validation module: {self}")


class SessionValidationModule(Enum):
    """
    Enum representing the different session validation modules available.

    Attributes:
        ABI (int): Represents the ABI session validation module.
        ERC20 (int): Represents the ERC20 session validation module.
    """

    ABI = 1
    ERC20 = 2

    def create_session_key_data(self, **kwargs) -> bytes:
        """
        Creates session key data based on the selected session validation module.

        For the ABI module, the following parameters are required:
            - session_key: The session key address.
            - permitted_contract: The address of the permitted contract.
            - permitted_selector: The function selector (4 bytes) allowed.
            - permitted_value_limit: The maximum value limit (uint128).
            - rules_list: A list of rules where each rule is a dictionary with 'offset', 'condition', and 'value'.

        For the ERC20 module, the following parameters are required:
            - session_key: The session key address.
            - token: The address of the ERC20 token.
            - recipient: The address of the recipient.
            - max_amount: The maximum amount allowed for the session.

        Args:
            **kwargs: The parameters required for the session key data based on the selected module.

        Returns:
            bytes: The encoded session key data.

        Raises:
            ValueError: If any required parameter is missing or if the session validation module is not recognized.
        """
        if self == SessionValidationModule.ABI:
            required_keys = [
                "session_key",
                "permitted_contract",
                "permitted_selector",
                "permitted_value_limit",
                "rules_list",
            ]
            for key in required_keys:
                if key not in kwargs:
                    raise ValueError(f"Missing required parameter: {key}")

            rules_list = kwargs["rules_list"]
            # Encode the base structure without the rules list
            session_key_data = encode(
                ["address", "address", "bytes4", "uint128", "uint16"],
                [
                    kwargs["session_key"],
                    kwargs["permitted_contract"],
                    kwargs["permitted_selector"],
                    kwargs["permitted_value_limit"],
                    len(rules_list),
                ],
            )

            # Encode the rules
            for rule in rules_list:
                rule_offset = rule["offset"]
                rule_condition = rule["condition"]
                rule_value = rule["value"]

                session_key_data += encode(
                    ["uint16", "uint8", "bytes32"],
                    [rule_offset, rule_condition, rule_value],
                )

            return session_key_data

        elif self == SessionValidationModule.ERC20:
            required_keys = ["session_key", "token", "recipient", "max_amount"]
            for key in required_keys:
                if key not in kwargs:
                    raise ValueError(f"Missing required parameter: {key}")

            session_key_data = encode(
                ["address", "address", "address", "uint256"],
                [
                    kwargs["session_key"],
                    kwargs["token"],
                    kwargs["recipient"],
                    kwargs["max_amount"],
                ],
            )
            return session_key_data

        else:
            raise ValueError(f"Unknown validation module: {self}")

    def get_address(self) -> str:
        """
        Retrieves the contract address associated with the session validation module.

        Returns:
            str: The contract address corresponding to the selected session validation module.

        Raises:
            ValueError: If the session validation module is not recognized.
        """
        if self == SessionValidationModule.ABI:
            return constants.ABI_SESSION_VALIDATION_MODULE
        elif self == SessionValidationModule.ERC20:
            return constants.ERC20_SESSION_VALIDATION_MODULE
        else:
            raise ValueError(f"Unknown validation module: {self}")
        
    def get_contract(self, provider: Web3) -> type[Contract]:
        """
        Retrieves the web3py contract instance associated with the session validation module.

        Returns:
            str: The contract address corresponding to the selected session validation module.

        Raises:
            ValueError: If the session validation module is not recognized.
        """
        if self == SessionValidationModule.ABI:
            abi = constants.read_abi("./contract_abis/abi_session_validation_module.json")
            return provider.eth.contract(address=constants.ABI_SESSION_VALIDATION_MODULE, abi=abi)
        elif self == SessionValidationModule.ERC20:
            abi = constants.read_abi("./contract_abis/erc20_session_validation_module.json")
            return provider.eth.contract(address=constants.ERC20_SESSION_VALIDATION_MODULE, abi=abi)
        else:
            raise ValueError(f"Unknown validation module: {self}")
