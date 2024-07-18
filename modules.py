from enum import Enum
import constants


class ValidationModule(Enum):
    ECDSA = 1
    MULTICHAIN_VALIDATION_MODULE = 2
    BATCHED_SESSION_ROUTER_MODULE = 3
    ABI_SESSION_VALIDATION_MODULE = 4
    SESSION_KEY_MANAGER_V1 = 5

    def get_module_address(self) -> str:
        if self == ValidationModule.ECDSA:
            return constants.ECDSA_OWNERSHIP_MODULE
        elif self == ValidationModule.MULTICHAIN_VALIDATION_MODULE:
            return constants.MULTICHAIN_VALIDATION_MODULE
        elif self == ValidationModule.BATCHED_SESSION_ROUTER_MODULE:
            return constants.BATCHED_SESSION_ROUTER_MODULE
        elif self == ValidationModule.ABI_SESSION_VALIDATION_MODULE:
            return constants.ABI_SESSION_VALIDATION_MODULE
        elif self == ValidationModule.SESSION_KEY_MANAGER_V1:
            return constants.SESSION_KEY_MANAGER_V1
        else:
            raise ValueError(f"Unknown validation module: {self}")
