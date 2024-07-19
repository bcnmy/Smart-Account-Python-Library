from web3 import Web3
from bundler import Bundler
from paymaster import Paymaster
from userop import UserOperation, UserOperationLib
from eth_abi import encode
from eth_utils import keccak, to_checksum_address
from eth_account import Account
from utils.modules import ValidationModule
from typing import Union
import json
import utils.constants as constants


class BiconomyV2SmartAccount:
    """
    Represents a Biconomy V2 Smart Account.

    Attributes:
        provider (Web3): The Web3 provider instance.
        bundler (Bundler): The bundler instance for managing user operations.
        validation_module (ValidationModule): The validation module to be used.
        private_key (str): The private key for signing transactions.
        eoa_address (str): The externally owned account (EOA) address.
        smart_account_address (str): The smart account address.
        paymaster_url (str): The paymaster ID.
        index (int): The index of the account.
    """

    def __init__(
        self,
        rpc_url: str,
        bundler_url: str,
        private_key: str,
        index: int = 0,
        paymaster_url: Union[str, None] = None,
        validation_module: ValidationModule = ValidationModule.ECDSA,
    ):
        """
        Initializes the BiconomyV2SmartAccount instance.

        Args:
            rpc_url (str): The URL of the RPC provider.
            bundler_url (str): The URL of the bundler.
            paymaster_url (str): The paymaster ID.
            private_key (str): The private key for signing transactions.
            index (int, optional): The index of the account. Defaults to 0.
            validation_module (ValidationModule, optional): The validation module to be used. Defaults to ValidationModule.ECDSA.
        """
        self.provider = Web3(Web3.HTTPProvider(rpc_url))
        self.bundler = Bundler(bundler_url)
        self._check_chain_ids()
        self.validation_module = validation_module
        self._set_contract_instances()
        self.index = index
        self._check_index()
        self.private_key = private_key
        self.eoa_address = self.get_eoa_address()
        self.smart_account_address = self.get_smart_account_address()
        if paymaster_url:
            self.paymaster = Paymaster(paymaster_url)
        else:
            self.paymaster = None

    def get_eoa_address(self) -> str:
        """
        Returns the externally owned account (EOA) address derived from the private key.

        Returns:
            str: The EOA address.
        """
        account = Account.from_key(self.private_key)
        return account.address

    def get_smart_account_address(self) -> str:
        """
        Computes the smart account address based on the provided configuration.

        Returns:
            str: The smart account address.
        """
        # Generate setup data for setting eoa as owner of sa in ecdsa module
        ownership_module_setup_data = self._get_module_setup_data()
        # Generate call data for initializing smart account
        sa_init_calldata = self.smart_account_implementation_v2.encode_abi(
            fn_name="init",
            args=[
                constants.DEFAULT_FALLBACK_HANDLER_ADDRESS,
                self.validation_module.get_module_address(),
                bytes.fromhex(ownership_module_setup_data[2:]),
            ],
        )

        salt = Web3.solidity_keccak(
            ["bytes32", "uint256"],
            [keccak(bytes.fromhex(sa_init_calldata[2:])), self.index],
        )

        create2_hash = Web3.solidity_keccak(
            ["bytes1", "address", "bytes32", "bytes32"],
            [
                b"\xff",
                constants.SMART_ACCOUNT_FACTORY_V2,
                salt,
                constants.PROXY_CREATION_CODE_HASH,
            ],
        )

        smart_account_address = to_checksum_address(create2_hash[-20:])
        return smart_account_address

    def get_smart_account_native_balance(self) -> int:
        """
        Returns the native balance of the smart account.

        Returns:
            int: The native balance of the smart account in wei.
        """
        balance = self.provider.eth.get_balance(self.smart_account_address)
        return balance

    def send_eth(self, recipient: str, amount_wei: int, nonce_key: int = 0) -> str:
        """
        Sends a specified amount of Ether to a recipient address using a user operation.

        Args:
            recipient (str): The Ethereum address of the recipient.
            amount_wei (int): The amount of Ether to send, in wei.
            nonce_key (int, optional): The key for the nonce value. Default is 0.

        Returns:
            str: The transaction hash of the user operation.

        Raises:
            ValueError: If the amount is not a positive integer, or if the recipient address is invalid,
                        or if the amount is greater than the account balance.
            Exception: If the smart account is not deployed.
        """
        if amount_wei <= 0 or not isinstance(amount_wei, int):
            raise ValueError("Amount must be a positive integer")

        if not Web3.is_address(recipient):
            raise ValueError("Recipient must be a valid ethereum address")

        if not self.is_deployed():
            raise Exception(
                f"Account at address {self.smart_account_address} isn't deployed"
            )

        sa_balance = self.provider.eth.get_balance(self.smart_account_address)
        if amount_wei > sa_balance:
            raise ValueError("Amount is greater than account balance")

        call_data = self.smart_account_implementation_v2.encode_abi(
            fn_name="execute",
            args=[
                recipient,
                amount_wei,
                b"",
            ],
        )
        userop = self.build_user_op(
            nonce=self.get_nonce(nonce_key), call_data=bytes.fromhex(call_data[2:])
        )
        userop = self.sign_userop(userop)
        return self.send_userop(userop)

    def get_nonce(self, key: int = 0) -> int:
        """
        Retrieves the nonce for the smart account.

        Args:
            key (int): The nonce key.

        Returns:
            int: The nonce value.

        Raises:
            ValueError: If the key is not a positive integer.
        """
        if key < 0 or not isinstance(key, int):
            raise ValueError("Key must be a positive integer")
        # Get nonce from EP
        nonce = self.entry_point.functions.getNonce(
            self.smart_account_address, key
        ).call()
        return nonce

    def fund_account(self, amount_wei: int, gas: int = 50000) -> str:
        """
        Funds the smart account with the specified amount of wei.

        Args:
            amount_wei (int): The amount of wei to fund the account with.
            gas (int): The amount of gas to send with the transaction.
        Returns:
            str: The userop hash of the funding transaction.

        Raises:
            ValueError: If the amount is greater than the account balance or is not a positive integer.
        """
        if amount_wei <= 0 or not isinstance(amount_wei, int):
            raise ValueError("Amount must be a positive integer")

        eoa_balance = self.provider.eth.get_balance(self.eoa_address)
        if amount_wei >= eoa_balance:
            raise ValueError("Amount is greater than account balance")

        latest_block = self.provider.eth.get_block("latest")
        base_fee_per_gas = latest_block["baseFeePerGas"]
        max_priority_fee_per_gas = Web3.to_wei(2, "gwei")
        max_fee_per_gas = base_fee_per_gas + max_priority_fee_per_gas

        transaction = {
            "from": self.eoa_address,
            "to": self.smart_account_address,
            "value": amount_wei,
            "nonce": self.provider.eth.get_transaction_count(self.eoa_address),
            "gas": gas,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.provider.eth.chain_id,
        }

        signed_txn = Account.sign_transaction(transaction, self.private_key)

        tx_hash = self.provider.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash.hex()

    def deploy_smart_account(self, nonce_key: int = 0) -> str:
        """
        Deploys the smart account if it is not already deployed.

        Args:
            nonce_key (int, optional): The nonce key to use. Defaults to 0.

        Returns:
            str: The userop hash of the deployment transaction.

        Raises:
            Exception: If the account is already deployed.
        """
        # Check if account is already deployed
        if self.is_deployed():
            raise Exception(f"Account at address {self.smart_account_address} exists")

        # Generate setup data for setting eoa as owner of sa in ecdsa module
        ownership_module_setup_data = self._get_module_setup_data()
        factory_address = constants.SMART_ACCOUNT_FACTORY_V2
        factory_data = self.smart_account_factory_v2.encode_abi(
            fn_name="deployCounterFactualAccount",
            args=[
                self.validation_module.get_module_address(),
                bytes.fromhex(ownership_module_setup_data[2:]),
                self.index,
            ],
        )
        init_code = bytes.fromhex(factory_address[2:] + factory_data[2:])
        nonce = self.get_nonce(nonce_key)

        # Build userop
        userop: UserOperation = self.build_user_op(
            nonce=nonce, init_code=init_code
        )
        userop = self.sign_userop(userop)
        return self.send_userop(userop)

    def build_user_op(
        self,
        # If nonce is null, they will be derived from this smart account instance
        nonce: Union[int, None] = None,
        init_code: bytes = b"",
        call_data: bytes = b"",
        paymaster_context: dict = constants.DEFAULT_PAYMASTER_CONTEXT,
    ) -> UserOperation:
        """
        Builds a user operation with the specified parameters.

        Args:
            sender (str): The sender address.
            nonce (int): The nonce value.
            init_code (bytes, optional): The initialization code. Defaults to b"".
            call_data (bytes, optional): The call data. Defaults to b"".
            paymaster_and_data (bytes, optional): The paymaster and data. Defaults to b"".
            max_fee_per_gas (int, optional): The maximum fee per gas. Defaults to 0.
            max_priority_fee_per_gas (int, optional): The maximum priority fee per gas. Defaults to 0.
            pre_verification_gas (int, optional): The pre-verification gas. Defaults to 0.
            verification_gas_limit (int, optional): The verification gas limit. Defaults to 0.
            call_gas_limit (int, optional): The call gas limit. Defaults to 0.

        Returns:
            UserOperation: The constructed user operation.
        """
        # Build the initial user operation object
        userop = UserOperation(
            self.smart_account_address,
            nonce if nonce is not None else self.get_nonce(),
            init_code,
            call_data,
            call_gas_limit=0,
            verification_gas_limit=0,
            pre_verification_gas=0,
            max_fee_per_gas=0,
            max_priority_fee_per_gas=0,
            paymaster_and_data=b"",
            signature=b"",
        )

        # Get dummy signature for gas estimation
        estimation_sig = encode(
            ["bytes", "address"],
            [
                self._sign_hash(constants.DUMMY_DATA_HASH),
                self.validation_module.get_module_address(),
            ],
        )
        userop.signature = estimation_sig
        # Get gas estimation from bundler
        gas_estimations = self.bundler.estimate_userop_gas(
            userop, self.entry_point.address
        )
        userop.max_fee_per_gas = gas_estimations["maxFeePerGas"]
        userop.max_priority_fee_per_gas = gas_estimations["maxPriorityFeePerGas"]
        if self.paymaster:
            # Get gas estimation from paymaster
            paymaster_and_data = self.paymaster.sponsor_user_operation(
                userop, paymaster_context
            )
            userop.paymaster_and_data = bytes.fromhex(
                paymaster_and_data["paymasterAndData"][2:]
            )
            userop.pre_verification_gas = int(paymaster_and_data["preVerificationGas"])
            userop.verification_gas_limit = int(
                paymaster_and_data["verificationGasLimit"]
            )
            userop.call_gas_limit = int(paymaster_and_data["callGasLimit"])
        else:
            # If no paymaster set, use bundler gas estimations
            userop.pre_verification_gas = gas_estimations["preVerificationGas"]
            userop.verification_gas_limit = gas_estimations["verificationGasLimit"]
            userop.call_gas_limit = gas_estimations["callGasLimit"]

        userop.signature = b""

        return userop

    def sign_userop(self, userop: UserOperation) -> UserOperation:
        """
        Signs the user operation.

        Args:
            userop (UserOperation): The user operation to sign.

        Returns:
            UserOperation: The signed user operation.
        """
        userop_hash = UserOperationLib.hash(
            userop, self.entry_point.address, self.provider.eth.chain_id
        )
        signed_userop_hash = self._sign_hash(userop_hash)
        complete_userop_signature = encode(
            ["bytes", "address"],
            [
                signed_userop_hash,
                self.validation_module.get_module_address(),
            ],
        )
        userop.signature = complete_userop_signature
        return userop

    def send_userop(self, userop: UserOperation) -> str:
        """
        Sends the user operation to the bundler.

        Args:
            userop (UserOperation): The user operation to send.

        Returns:
            str: The userop hash of the sent user operation.
        """
        return self.bundler.send_userop(userop, self.entry_point.address)

    def get_userop_status(self, userop_hash: str) -> str:
        """
        Retrieves the status of a user operation by its hash.

        Args:
            userop_hash (str): The hash of the user operation.

        Returns:
            str: The status of the user operation.
        """
        return self.bundler.get_user_operation_status(userop_hash)

    def get_userop_by_hash(self, userop_hash: str) -> Union[UserOperation, None]:
        """
        Retrieves a user operation by its hash.

        Args:
            userop_hash (str): The hash of the user operation.

        Returns:
            Union[UserOperation, None]: The user operation, or None if not found.
        """
        return self.bundler.get_user_operation_by_hash(userop_hash)

    def get_userop_receipt(self, userop_hash: str) -> Union[dict, None]:
        """
        Retrieves the receipt of a user operation by its hash.

        Args:
            userop_hash (str): The hash of the user operation.

        Returns:
            Union[dict, None]: The receipt of the user operation, or None if not found.
        """
        return self.bundler.get_user_operation_receipt(userop_hash)

    def is_deployed(self) -> bool:
        """
        Checks if the smart account is already deployed.

        Returns:
            bool: True if the smart account is deployed, False otherwise.
        """
        return True if self.provider.eth.get_code(self.smart_account_address) else False

    def _check_chain_ids(self) -> None:
        """
        Checks if the chain IDs of the RPC provider and bundler match.

        Raises:
            ValueError: If the chain IDs do not match.
        """
        # Fetch the chain ID from the RPC provider
        rpc_chain_id = self.provider.eth.chain_id

        bundler_chain_id = self.bundler.get_chain_id()

        # Compare the chain IDs
        if rpc_chain_id != bundler_chain_id:
            raise ValueError(
                f"Chain ID mismatch: RPC chain ID is {rpc_chain_id}, Bundler chain ID is {bundler_chain_id}"
            )

    def _set_contract_instances(self):
        """
        Sets the contract instances for the smart account, factory, and validation modules.
        """
        entry_point_address = constants.ENTRY_POINT_OTHER_CHAINS
        # if using chiliz mainnet or testnet, adjust entrypoint
        if self.provider.eth.chain_id == 88888 or self.provider.eth.chain_id == 88880:
            entry_point_address = constants.ENTRY_POINT_CHILIZ_MAINNET_TESTNET

        # Instantiate global entrypoint
        entry_point_abi = self.read_abi("./contract_abis/entry_point.json")
        self.entry_point = self.provider.eth.contract(
            address=entry_point_address,
            abi=entry_point_abi,
        )

        # Instantiate global SA factory
        smart_account_factory_v2_abi = self.read_abi(
            "./contract_abis/smart_account_factory_v2.json"
        )
        self.smart_account_factory_v2 = self.provider.eth.contract(
            address=constants.SMART_ACCOUNT_FACTORY_V2,
            abi=smart_account_factory_v2_abi,
        )

        # Instantiate global SA implementation
        smart_account_implementation_v2_abi = self.read_abi(
            "./contract_abis/smart_account_implementation_v2.json"
        )
        self.smart_account_implementation_v2 = self.provider.eth.contract(
            address=constants.SMART_ACCOUNT_IMPLEMENTATION_V2,
            abi=smart_account_implementation_v2_abi,
        )

        # Instantiate global ECDSA implementation
        ecdsa_ownership_module_abi = self.read_abi(
            "./contract_abis/ecdsa_ownership_module.json"
        )
        self.ecdsa_ownership_module = self.provider.eth.contract(
            address=self.validation_module.get_module_address(),
            abi=ecdsa_ownership_module_abi,
        )

    def _check_index(self):
        """
        Checks if the index is a positive integer.

        Raises:
            ValueError: If the index is not a positive integer.
        """
        if self.index < 0 or not isinstance(self.index, int):
            raise ValueError("Index must be a positive integer")

    def _sign_hash(self, hash) -> bytes:
        """
        Signs the given hash with the private key.

        Args:
            hash: The hash to sign.

        Returns:
            bytes: The signature of the hash.
        """
        signed_hash = Account.signHash(hash, self.private_key)
        return signed_hash.signature

    def _get_module_setup_data(self) -> str:
        """
        Returns the setup data for the validation module.

        Returns:
            str: The setup data.

        Raises:
            ValueError: If the validation module is not supported or unknown.
        """
        if self.validation_module == ValidationModule.ECDSA:
            return self.ecdsa_ownership_module.encode_abi(
                fn_name="initForSmartAccount", args=[self.eoa_address]
            )
        elif self.validation_module == ValidationModule.MULTICHAIN_VALIDATION_MODULE:
            raise ValueError(f"Module not yet supported: {self.validation_module}")
        elif self.validation_module == ValidationModule.BATCHED_SESSION_ROUTER_MODULE:
            raise ValueError(f"Module not yet supported: {self.validation_module}")
        elif self.validation_module == ValidationModule.ABI_SESSION_VALIDATION_MODULE:
            raise ValueError(f"Module not yet supported: {self.validation_module}")
        elif self.validation_module == ValidationModule.SESSION_KEY_MANAGER_V1:
            raise ValueError(f"Module not yet supported: {self.validation_module}")
        else:
            raise ValueError(f"Unknown validation module: {self.validation_module}")

    @staticmethod
    def read_abi(file_path: str) -> list:
        """
        Reads and returns the ABI from the specified file.

        Args:
            file_path (str): The path to the ABI file.

        Returns:
            list: The ABI read from the file.
        """
        with open(file_path, "r") as file:
            abi = json.load(file)
        return abi
