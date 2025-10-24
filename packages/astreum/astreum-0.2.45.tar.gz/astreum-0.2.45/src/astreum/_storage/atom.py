

from typing import List, Optional, Tuple

from .._lispeum.expression import Expr
from blake3 import blake3

ZERO32 = b"\x00"*32

def u64_le(n: int) -> bytes:
    return int(n).to_bytes(8, "little", signed=False)

def hash_bytes(b: bytes) -> bytes:
    return blake3(b).digest()

class Atom:
    data: bytes
    next: bytes
    size: int

    def __init__(self, data: bytes, next: bytes = ZERO32, size: Optional[int] = None):
        self.data = data
        self.next = next
        self.size = len(data) if size is None else size

    @staticmethod
    def from_data(data: bytes, next_hash: bytes = ZERO32) -> "Atom":
        return Atom(data=data, next=next_hash, size=len(data))

    @staticmethod
    def object_id_from_parts(data_hash: bytes, next_hash: bytes, size: int) -> bytes:
        return blake3(data_hash + next_hash + u64_le(size)).digest()

    def data_hash(self) -> bytes:
        return hash_bytes(self.data)

    def object_id(self) -> bytes:
        return self.object_id_from_parts(self.data_hash(), self.next, self.size)

    @staticmethod
    def verify_metadata(object_id: bytes, size: int, next_hash: bytes, data_hash: bytes) -> bool:
        return object_id == blake3(data_hash + next_hash + u64_le(size)).digest()

    def to_bytes(self) -> bytes:
        return self.next + self.data

    @staticmethod
    def from_bytes(buf: bytes) -> "Atom":
        if len(buf) < len(ZERO32):
            raise ValueError("buffer too short for Atom header")
        next_hash = buf[:len(ZERO32)]
        data = buf[len(ZERO32):]
        return Atom(data=data, next=next_hash, size=len(data))

def expr_to_atoms(e: Expr) -> Tuple[bytes, List[Atom]]:
    def symbol(value: str) -> Tuple[bytes, List[Atom]]:
        val = value.encode("utf-8")
        val_atom = Atom.from_data(data=val)
        typ_atom = Atom.from_data(b"symbol", val_atom.object_id())
        return typ_atom.object_id(), [val_atom, typ_atom]

    def bytes(data: bytes) -> Tuple[bytes, List[Atom]]:
        val_atom = Atom.from_data(data=data)
        typ_atom = Atom.from_data(b"byte", val_atom.object_id())
        return typ_atom.object_id(), [val_atom, typ_atom]

    def err(topic: str, origin: Optional[Expr]) -> Tuple[bytes, List[Atom]]:
        topic_bytes = topic.encode("utf-8")
        topic_atom = Atom.from_data(data=topic_bytes)
        typ_atom = Atom.from_data(data=b"error", next_hash=topic_atom.object_id())
        return typ_atom.object_id(), [topic_atom, typ_atom]

    def lst(items: List[Expr]) -> Tuple[bytes, List[Atom]]:
        acc: List[Atom] = []
        child_hashes: List[bytes] = []
        for it in items:
            h, atoms = expr_to_atoms(it)
            acc.extend(atoms)
            child_hashes.append(h)
        next_hash = ZERO32
        elem_atoms: List[Atom] = []
        for h in reversed(child_hashes):
            a = Atom.from_data(h, next_hash)
            next_hash = a.object_id()
            elem_atoms.append(a)
        elem_atoms.reverse()
        head = next_hash
        val_atom = Atom.from_data(data=u64_le(len(items)), next_hash=head)
        typ_atom = Atom.from_data(data=b"list", next_hash=val_atom.object_id())
        return typ_atom.object_id(), acc + elem_atoms + [val_atom, typ_atom]

    if isinstance(e, Expr.Symbol):
        return symbol(e.value)
    if isinstance(e, Expr.Bytes):
        return bytes(e.value)
    if isinstance(e, Expr.Error):
        return err(e.topic, e.origin)
    if isinstance(e, Expr.ListExpr):
        return lst(e.elements)
    raise TypeError("unknown Expr variant")


def bytes_list_to_atoms(values: List[bytes]) -> Tuple[bytes, List[Atom]]:
    """Build a forward-ordered linked list of atoms from byte payloads.

    Returns the head object's hash (ZERO32 if no values) and the atoms created.
    """
    next_hash = ZERO32
    atoms: List[Atom] = []

    for value in reversed(values):
        atom = Atom.from_data(data=bytes(value), next_hash=next_hash)
        atoms.append(atom)
        next_hash = atom.object_id()

    atoms.reverse()
    return (next_hash if values else ZERO32), atoms
