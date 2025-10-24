from __future__ import annotations

import threading
from queue import Queue
from typing import Any

from .workers import (
    make_discovery_worker,
    make_validation_worker,
    make_verify_worker,
)


def current_validator(node: Any) -> bytes:
    """Return the current validator identifier. Override downstream."""
    raise NotImplementedError("current_validator must be implemented by the host node")


def consensus_setup(node: Any) -> None:
    # Shared state
    node.validation_lock = getattr(node, "validation_lock", threading.RLock())

    # Public maps per your spec
    # - chains: Dict[root, Chain]
    # - forks:  Dict[head, Fork]
    node.chains = getattr(node, "chains", {})
    node.forks = getattr(node, "forks", {})

    # Pending transactions queue (hash-only entries)
    node._validation_transaction_queue = getattr(
        node, "_validation_transaction_queue", Queue()
    )
    # Single work queue of grouped items: (latest_block_hash, set(peer_ids))
    node._validation_verify_queue = getattr(
        node, "_validation_verify_queue", Queue()
    )
    node._validation_stop_event = getattr(
        node, "_validation_stop_event", threading.Event()
    )

    def enqueue_transaction_hash(tx_hash: bytes) -> None:
        """Schedule a transaction hash for validation processing."""
        if not isinstance(tx_hash, (bytes, bytearray)):
            raise TypeError("transaction hash must be bytes-like")
        node._validation_transaction_queue.put(bytes(tx_hash))

    node.enqueue_transaction_hash = enqueue_transaction_hash

    verify_worker = make_verify_worker(node)
    validation_worker = make_validation_worker(
        node, current_validator=current_validator
    )

    # Start workers as daemons
    discovery_worker = make_discovery_worker(node)
    node.consensus_discovery_thread = threading.Thread(
        target=discovery_worker, daemon=True, name="consensus-discovery"
    )
    node.consensus_verify_thread = threading.Thread(
        target=verify_worker, daemon=True, name="consensus-verify"
    )
    node.consensus_validation_thread = threading.Thread(
        target=validation_worker, daemon=True, name="consensus-validation"
    )
    node.consensus_discovery_thread.start()
    node.consensus_verify_thread.start()
    if getattr(node, "validation_secret_key", None):
        node.consensus_validation_thread.start()
