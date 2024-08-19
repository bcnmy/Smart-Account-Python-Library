import os
import pickle
from typing import List, Tuple, Optional
from eth_utils import keccak

class PersistentMerkleTree:
    def __init__(self, storage_dir: str, eth_address: str, leaves: Optional[List[bytes]] = None):
        """
        Initializes the PersistentMerkleTree.

        Args:
            storage_dir (str): Directory where Merkle tree data will be stored.
            eth_address (str): Ethereum address used as the unique identifier for the Merkle tree.
            leaves (Optional[List[bytes]], optional): Initial leaves to build the tree. Defaults to None.
        """
        self.storage_dir = storage_dir
        self.eth_address = eth_address
        self.tree_file = os.path.join(self.storage_dir, f"{self.eth_address}.pkl")

        if os.path.exists(self.tree_file):
            self.tree, self.leaves = self._load_tree()
        else:
            self.leaves = leaves if leaves is not None else []
            self.tree = self._build_merkle_tree(self.leaves)
            self._save_tree()

    def _save_tree(self):
        """Saves the Merkle tree and its leaves to a file."""
        with open(self.tree_file, 'wb') as f:
            pickle.dump((self.tree, self.leaves), f)

    def _load_tree(self) -> Tuple[List[bytes], List[bytes]]:
        """Loads the Merkle tree and its leaves from a file."""
        with open(self.tree_file, 'rb') as f:
            return pickle.load(f)

    def _build_merkle_tree(self, leaves: List[bytes]) -> List[bytes]:
        """Builds the Merkle tree from the list of leaves."""
        if not leaves:
            return []

        tree = leaves[:]
        while len(tree) > 1:
            if len(tree) % 2 == 1:
                tree.append(tree[-1])
            tree = [keccak(tree[i] + tree[i + 1]) for i in range(0, len(tree), 2)]
        return tree

    def add_leaf(self, leaf: bytes):
        """Adds a new leaf to the Merkle tree and updates the tree."""
        self.leaves.append(keccak(leaf))
        self.tree = self._build_merkle_tree(self.leaves)
        self._save_tree()

    @property
    def root(self) -> bytes:
        """Returns the Merkle tree root."""
        return self.tree[0] if self.tree else b''

    def get_proof(self, leaf: bytes) -> List[bytes]:
        """Generates a Merkle proof for a given leaf."""
        leaf_hash = keccak(leaf)
        proof = []
        index = self.leaves.index(leaf_hash)
        siblings = self.leaves[:]
        while len(siblings) > 1:
            if len(siblings) % 2 == 1:
                siblings.append(siblings[-1])
            new_siblings = []
            for i in range(0, len(siblings), 2):
                if i == index or i + 1 == index:
                    proof.append(siblings[i + 1] if i == index else siblings[i])
                new_siblings.append(keccak(siblings[i] + siblings[i + 1]))
            index = index // 2
            siblings = new_siblings
        return proof

    def verify_proof(self, leaf: bytes, proof: List[bytes]) -> bool:
        """Verifies a Merkle proof against the stored root."""
        computed_hash = keccak(leaf)
        for sibling in proof:
            if computed_hash < sibling:
                computed_hash = keccak(computed_hash + sibling)
            else:
                computed_hash = keccak(sibling + computed_hash)
        return computed_hash == self.root
