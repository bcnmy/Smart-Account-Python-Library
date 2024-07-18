from userop import UserOperation, UserOperationLib
from utils.rpc import RPC
import utils.constants as constants


class Paymaster(RPC):
    """
    A class to interact with a paymaster for managing user operations on a blockchain.

    Attributes:
        paymaster_url (str): The URL of the paymaster's RPC endpoint.
    """

    def __init__(self, paymaster_url: str):
        """
        Initializes the Paymaster instance.

        Args:
            paymaster_url (str): The URL of the paymaster's RPC endpoint.
        """
        super().__init__(paymaster_url)

    def get_paymaster_stub_data(
        self,
        userop: UserOperation,
        ep_address: str,
        chain_id: str,
        context: dict = constants.DEFAULT_PAYMASTER_CONTEXT,
    ) -> dict:
        """
        Retrieves the stub data for the paymaster-related fields of an unsigned user operation.

        Args:
            userop (UserOperation): The unsigned user operation.
            ep_address (str): The entry point address.
            chain_id (str): The chain ID.
            context (dict): The context object for the paymaster service.

        Returns:
            dict: The stub data for the paymaster-related fields.
        """
        params = [
            UserOperationLib.marshal_partial_userop(userop),
            ep_address,
            chain_id,
            context,
        ]
        return self._send_json_rpc_request("pm_getPaymasterStubData", params)[
            "paymasterAndData"
        ]

    def get_paymaster_data(
        self,
        userop: UserOperation,
        ep_address: str,
        chain_id: str,
        context: dict = constants.DEFAULT_PAYMASTER_CONTEXT,
    ) -> dict:
        """
        Retrieves the values for the paymaster-related fields of an unsigned user operation.

        Args:
            userop (UserOperation): The unsigned user operation.
            ep_address (str): The entry point address.
            chain_id (str): The chain ID.
            context (dict): The context object for the paymaster service.

        Returns:
            dict: The values for the paymaster-related fields.
        """
        params = [
            UserOperationLib.marshal_partial_userop(userop),
            ep_address,
            chain_id,
            context,
        ]
        return self._send_json_rpc_request("pm_getPaymasterData", params)[
            "paymasterAndData"
        ]

    def get_fee_quote_or_data(
        self, userop: UserOperation, context: dict = constants.DEFAULT_PAYMASTER_CONTEXT
    ) -> dict:
        """
        Retrieves the fee quote or data for a user operation.

        Args:
            userop (UserOperation): The unsigned user operation.
            context (dict): Additional information required for the request.

        Returns:
            dict: The fee quote or data for the user operation.
        """
        params = [UserOperationLib.marshal_partial_userop(userop), context]
        return self._send_json_rpc_request("pm_getFeeQuoteOrData", params)

    def sponsor_user_operation(
        self, userop: UserOperation, context: dict = constants.DEFAULT_PAYMASTER_CONTEXT
    ) -> dict:
        """
        Sponsors a user operation.

        Args:
            userop (UserOperation): The user operation to be sponsored.
            context (dict): Additional information required for the request.

        Returns:
            dict: The result of the sponsorship operation.
        """
        params = [UserOperationLib.marshal_partial_userop(userop), context]
        return self._send_json_rpc_request("pm_sponsorUserOperation", params)
