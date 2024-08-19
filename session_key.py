from web3 import Web3
from utils import constants
from utils.modules import SessionValidationModule
from eth_abi import encode, is_encodable
from eth_account import Account
from utils.persistent_merkle_tree import PersistentMerkleTree
import os
from appdirs import user_data_dir
import tempfile

class SessionKeyManager:
    def __init__(
        self,
        smart_account_address: str,
        session_key_storage_path: str = "",
    ):
        # Set a default session key storage path if not provided
        if not session_key_storage_path:
            session_key_storage_path = user_data_dir(constants.APP_NAME, constants.APP_AUTHOR)
        
        self.smart_account_address = smart_account_address
        self.session_key_storage_path = session_key_storage_path
        
        # Ensure the directory exists
        os.makedirs(self.session_key_storage_path, exist_ok=True)
        
        # Initialize the PersistentMerkleTree
        self.merkle_tree = PersistentMerkleTree(self.session_key_storage_path, self.session_address)
        
        # Check read/write permissions
        self._check_rw_permissions(self.session_key_storage_path)
    
    def create_session(
        self,
        valid_until: int,
        valid_after: int,
        session_validation_module: SessionValidationModule = SessionValidationModule.ABI,
        **kwargs
    ) -> bool:
        try:
            session_validation_module_address = session_validation_module.get_address()
            session_key_data = session_validation_module.create_session_key_data(**kwargs)
            leaf = self._create_session_leaf(valid_until, valid_after, session_validation_module_address, session_key_data)
            self.merkle_tree.add_leaf(leaf)
            root = self.merkle_tree.root
            # Todo: update root on chain
            return True
        except Exception as e:
            raise Exception("Error Creating Session:", e)
    
    def _create_session_leaf(
        self,
        valid_until: int,
        valid_after: int,
        session_validation_module: str,
        sessionKeyData: bytes,
    ) -> bytes:
        try:
            return Web3.solidity_keccak(
                ["uint48", "uint48", "address", "bytes"],
                [valid_until, valid_after, session_validation_module, sessionKeyData],
            )
        except Exception as e:
            raise Exception("Error Creating Session Leaf:", e)


    def _check_rw_permissions(self, path: str):
        try:
            with tempfile.NamedTemporaryFile(dir=path, delete=True) as temp_file:
                temp_file.write(b"test")
                temp_file.flush()
                os.fsync(temp_file.fileno())
        except (IOError, OSError) as e:
            raise PermissionError(f"Read/write permission error on path: {path}. {str(e)}")