from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import blake3
from ..format import encode, decode

class MerkleNode:
    def __init__(
        self,
        left: Optional[bytes],
        right: Optional[bytes],
        value: Optional[bytes],
    ) -> None:
        self.left = left
        self.right = right
        self.value = value
        self._hash: Optional[bytes] = None

    def to_bytes(self) -> bytes:
        return encode([self.left, self.right, self.value])

    @classmethod
    def from_bytes(cls, blob: bytes) -> "MerkleNode":
        left, right, value = decode(blob)
        return cls(left, right, value)

    def _compute_hash(self) -> bytes:
        if self.value is not None:
            return blake3.blake3(self.value).digest()
        left = self.left or b""
        right = self.right or b""
        return blake3.blake3(left + right).digest()

    def hash(self) -> bytes:
        if self._hash is None:
            self._hash = self._compute_hash()
        return self._hash


class MerkleTree:
    def __init__(
        self,
        global_get_fn: Callable[[bytes], Optional[bytes]],
        root_hash: Optional[bytes] = None,
        height: Optional[int] = None,
    ) -> None:
        self._global_get_fn = global_get_fn
        self.nodes: Dict[bytes, MerkleNode] = {}
        self.root_hash = root_hash
        self._height: Optional[int] = height

    @classmethod
    def from_leaves(
        cls,
        leaves: List[bytes],
        global_get_fn: Callable[[bytes], Optional[bytes]] | None = None,
    ) -> "MerkleTree":
        if not leaves:
            raise ValueError("must supply at least one leaf")

        global_get_fn = global_get_fn or (lambda _h: None)
        tree = cls(global_get_fn=global_get_fn)

        # Step 1 – create leaf nodes list[bytes]
        level_hashes: List[bytes] = []
        for val in leaves:
            leaf = MerkleNode(None, None, val)
            h = leaf.hash()
            tree.nodes[h] = leaf
            level_hashes.append(h)

        height = 1  # current level (leaves)

        # Step 2 – build upper levels until single root remains
        while len(level_hashes) > 1:
            next_level: List[bytes] = []
            it = iter(level_hashes)
            for left_hash in it:
                try:
                    right_hash = next(it)
                except StopIteration:
                    right_hash = None
                parent = MerkleNode(left_hash, right_hash, None)
                ph = parent.hash()
                tree.nodes[ph] = parent
                next_level.append(ph)
            level_hashes = next_level
            height += 1

        tree.root_hash = level_hashes[0]
        tree._height = height
        return tree

    def _fetch(self, h: bytes | None) -> Optional[MerkleNode]:
        if h is None:
            return None
        node = self.nodes.get(h)
        if node is None:
            raw = self._global_get_fn(h)
            if raw is None:
                return None
            node = MerkleNode.from_bytes(raw)
            self.nodes[h] = node
        return node

    def _invalidate(self, node: MerkleNode) -> None:
        node._hash = None

    def _ensure_height(self) -> None:
        if self._height is None:
            h = 0
            nh = self.root_hash
            while nh is not None:
                node = self._fetch(nh)
                nh = node.left if node and node.value is None else None
                h += 1
            self._height = h or 1

    def _capacity(self) -> int:
        self._ensure_height()
        assert self._height is not None
        return 1 << (self._height - 1)

    def _path_bits(self, index: int) -> List[int]:
        self._ensure_height()
        assert self._height is not None
        bits = []
        for shift in range(self._height - 2, -1, -1):
            bits.append((index >> shift) & 1)
        return bits

    # ------------------------------------------------------------------
    # get / put
    # ------------------------------------------------------------------
    def get(self, index: int) -> Optional[bytes]:
        if index < 0 or self.root_hash is None or index >= self._capacity():
            return None

        node_hash = self.root_hash
        for bit in self._path_bits(index):
            node = self._fetch(node_hash)
            if node is None:
                return None
            node_hash = node.right if bit else node.left
            if node_hash is None:
                return None
        leaf = self._fetch(node_hash)
        return leaf.value if leaf else None

    def put(self, index: int, value: bytes) -> None:
        # 1 . input validation
        if index < 0:
            raise IndexError("negative index")
        if self.root_hash is None:
            raise IndexError("tree is empty – build it first with from_leaves()")
        if index >= self._capacity():
            raise IndexError("index beyond tree capacity")

        # 2 . walk down to the target leaf
        node_hash = self.root_hash
        stack: List[Tuple[MerkleNode, bytes, bool]] = []
        for bit in self._path_bits(index):
            node = self._fetch(node_hash)
            if node is None:
                raise IndexError("missing node along path")
            went_right = bool(bit)
            child_hash = node.right if went_right else node.left
            if child_hash is None:
                raise IndexError("path leads into non-existent branch")
            stack.append((node, node.hash(), went_right))
            node_hash = child_hash

        # 3 . update the leaf
        leaf = self._fetch(node_hash)
        if leaf is None or leaf.value is None:
            raise IndexError("target leaf missing")

        old_hash = leaf.hash()
        leaf.value = value
        self._invalidate(leaf)
        new_hash = leaf.hash()
        
        if new_hash != old_hash:
            self.nodes.pop(old_hash, None)
        self.nodes[new_hash] = leaf
        
        # 4 . bubble the change up
        for parent, old_hash, went_right in reversed(stack):
            if went_right:
                parent.right = new_hash
            else:
                parent.left = new_hash

            self._invalidate(parent)
            new_hash = parent.hash()

            if new_hash != old_hash:
                self.nodes.pop(old_hash, None)
            self.nodes[new_hash] = parent
            
        # 5 . finalise the new root
        self.root_hash = new_hash


