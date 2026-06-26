"""Hashing helpers for the file integrity checker."""

from __future__ import annotations

import hashlib
from pathlib import Path


ALGORITHMS = {
    "md5": "MD5",
    "sha1": "SHA-1",
    "sha256": "SHA-256",
    "sha512": "SHA-512",
}

CHUNK_SIZE = 1024 * 1024


class HashingError(Exception):
    """Raised when a file cannot be hashed safely."""


def calculate_hashes(file_path: Path, algorithms: list[str] | None = None) -> dict[str, str]:
    """Calculate selected hashes for a file using Python's hashlib library."""
    selected_algorithms = algorithms or list(ALGORITHMS.keys())
    invalid_algorithms = [
        algorithm for algorithm in selected_algorithms if algorithm not in ALGORITHMS
    ]

    if invalid_algorithms:
        raise HashingError("Unsupported hash algorithm requested.")

    try:
        hashers = {
            algorithm: hashlib.new(algorithm)
            for algorithm in selected_algorithms
        }

        with file_path.open("rb") as file_object:
            while True:
                chunk = file_object.read(CHUNK_SIZE)
                if not chunk:
                    break

                for hasher in hashers.values():
                    hasher.update(chunk)

        return {
            algorithm: hasher.hexdigest()
            for algorithm, hasher in hashers.items()
        }
    except OSError as error:
        raise HashingError("The uploaded file could not be read.") from error
    except ValueError as error:
        raise HashingError("Unsupported hash algorithm requested.") from error


def compare_hash(generated_hash: str, expected_hash: str) -> bool:
    """Compare two hashes while ignoring letter casing and extra whitespace."""
    return generated_hash.strip().lower() == expected_hash.strip().lower()


def format_file_size(size_bytes: int) -> str:
    """Convert a byte count into a readable file size."""
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size_bytes} B"
