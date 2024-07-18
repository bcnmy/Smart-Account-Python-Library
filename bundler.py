from userop import UserOperation, UserOperationLib
from utils.rpc import RPC
from typing import Union


class Bundler(RPC):
    """
    A class to interact with a bundler for sending and managing user operations on a blockchain.

    Attributes:
        bundler_url (str): The URL of the bundler's RPC endpoint.
    """

    def __init__(self, bundler_url: str):
        """
        Initializes the Bundler instance.

        Args:
            bundler_url (str): The URL of the bundler's RPC endpoint.
        """
        super().__init__(bundler_url)

    def get_chain_id(self) -> int:
        """
        Retrieves the chain ID from the bundler.

        Returns:
            int: The chain ID.
        """
        result = self._send_json_rpc_request("eth_chainId", [])
        return int(result, 16)

    def get_gas_fee_values(self) -> dict[str, int]:
        """
        Retrieves the current gas fee values from the bundler.

        Returns:
            dict[str, int]: A dictionary containing the max priority fee per gas and the max fee per gas.
        """
        result = self._send_json_rpc_request("biconomy_getGasFeeValues", [])
        result["maxPriorityFeePerGas"] = int(result["maxPriorityFeePerGas"])
        result["maxFeePerGas"] = int(result["maxFeePerGas"])
        return result

    def estimate_userop_gas(
        self, userop: UserOperation, ep_address: str
    ) -> dict[str, Union[str, int]]:
        """
        Estimates the gas required for a user operation.

        Args:
            userop (UserOperation): The user operation to estimate gas for.
            ep_address (str): The entry point address.

        Returns:
            dict[str, Union[str, int]]: A dictionary containing the gas estimates.
        """
        marshaled_userop = UserOperationLib.marshal_partial_userop(userop)
        result = self._send_json_rpc_request(
            "eth_estimateUserOperationGas", [marshaled_userop, ep_address]
        )
        result["maxPriorityFeePerGas"] = int(result["maxPriorityFeePerGas"])
        result["maxFeePerGas"] = int(result["maxFeePerGas"])
        return result

    def send_userop(
        self,
        userop: UserOperation,
        ep_address: str,
        simulation_type: str = "validation_and_execution",
    ) -> str:
        """
        Sends a user operation to the bundler for execution.

        Args:
            userop (UserOperation): The user operation to send.
            ep_address (str): The entry point address.
            simulation_type (str): The type of simulation to perform (default is "validation_and_execution").

        Returns:
            str: The result of the user operation submission.
        """
        marshaled_userop = UserOperationLib.marshal_userop(userop)
        result = self._send_json_rpc_request(
            "eth_sendUserOperation",
            [marshaled_userop, ep_address, {"simulation_type": simulation_type}],
        )
        return result

    def get_user_operation_receipt(self, userop_hash: str) -> Union[dict, None]:
        """
        Retrieves the receipt of a user operation by its hash.

        Args:
            userop_hash (str): The hash of the user operation.

        Returns:
            Union[dict, None]: The receipt of the user operation, or None if not found.
        """
        result = self._send_json_rpc_request(
            "eth_getUserOperationReceipt", [userop_hash]
        )
        return result

    def get_user_operation_by_hash(
        self, userop_hash: str
    ) -> Union[UserOperation, None]:
        """
        Retrieves a user operation by its hash.

        Args:
            userop_hash (str): The hash of the user operation.

        Returns:
            Union[UserOperation, None]: The user operation, or None if not found.
        """
        result = self._send_json_rpc_request(
            "eth_getUserOperationByHash", [userop_hash]
        )
        if result is None:
            return None
        else:
            result = UserOperationLib.unmarshal_userop(result)
            return result

    def get_user_operation_status(self, userop_hash: str) -> dict:
        """
        Retrieves the status of a user operation by its hash.

        Args:
            userop_hash (str): The hash of the user operation.

        Returns:
            dict: The status of the user operation.
        """
        result = self._send_json_rpc_request(
            "biconomy_getUserOperationStatus", [userop_hash]
        )
        return result
