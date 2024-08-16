from enum import Enum
from eth_abi import encode
import utils.constants as constants


class ValidationModule(Enum):
    ECDSA = 1
    SESSION_KEY_MANAGER_V1 = 2

    def get_module_address(self) -> str:
        if self == ValidationModule.ECDSA:
            return constants.ECDSA_OWNERSHIP_MODULE
        elif self == ValidationModule.SESSION_KEY_MANAGER_V1:
            return constants.SESSION_KEY_MANAGER_V1
        else:
            raise ValueError(f"Unknown validation module: {self}")
        
class SessionValidationModule(Enum):
    ABI = 1
    ERC20 = 2
    
    def create_session_key_data(self, **kwargs) -> bytes:
        if self == SessionValidationModule.ABI:
            required_keys = [
                'session_key',
                'permitted_contract',
                'permitted_selector',
                'permitted_value_limit',
                'rules_list'
            ]
            for key in required_keys:
                if key not in kwargs:
                    raise ValueError(f"Missing required parameter: {key}")

            session_key = kwargs['session_key']
            permitted_contract = kwargs['permitted_contract']
            permitted_selector = kwargs['permitted_selector']
            permitted_value_limit = kwargs['permitted_value_limit']
            rules_list = kwargs['rules_list']
            
            # Encode the base structure without the rules list
            session_key_data = encode(
                ['address', 'address', 'bytes4', 'uint128', 'uint16'],
                [session_key, permitted_contract, permitted_selector, permitted_value_limit, len(rules_list)]
            )
            
            # Encode the rules
            for rule in rules_list:
                rule_offset = rule['offset']
                rule_condition = rule['condition']
                rule_value = rule['value']
                
                session_key_data += encode(
                    ['uint16', 'uint8', 'bytes32'],
                    [rule_offset, rule_condition, rule_value]
                )
            
            return session_key_data
            
        elif self == SessionValidationModule.ERC20:
            required_keys = ['session_key', 'token', 'recipient', 'max_amount']
            for key in required_keys:
                if key not in kwargs:
                    raise ValueError(f"Missing required parameter: {key}")
            
            session_key_data = encode(
                ['address', 'address', 'address', 'uint256'],
                [kwargs['session_key'], kwargs['token'], kwargs['recipient'], kwargs['max_amount']]
            )
            return session_key_data
        
        else:
            raise ValueError(f"Unknown validation module: {self}")
    
    def get_module_address(self) -> str:
        if self == SessionValidationModule.ABI:
            return constants.ABI_SESSION_VALIDATION_MODULE
        elif self == SessionValidationModule.ERC20:
            return constants.ERC20_SESSION_VALIDATION_MODULE
        else:
            raise ValueError(f"Unknown validation module: {self}")