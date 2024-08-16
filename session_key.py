from web3 import Web3
from utils import constants
from utils.modules import SessionValidationModule
from eth_abi import encode, is_encodable
from pymerkle import InmemoryTree as MerkleTree, MerkleProof

class SessionKeyManager:
    def __init__(self, session_private_key: str, session_validation_module: SessionValidationModule = SessionValidationModule.ABI):
        self.session_private_key = session_private_key
        self.session_validation_module = session_validation_module
        self.merkle_tree: MerkleTree = MerkleTree(algorithm="keccak256")

    def _create_session_leaf(
        valid_until: int,
        valid_after: int,
        session_validation_module: str,
        sessionKeyData: bytes,
    ) -> bytes:
        return Web3.solidity_keccak(
            ["uint48", "uint48", "address", "bytes"],
            [valid_until, valid_after, session_validation_module, sessionKeyData],
        )
