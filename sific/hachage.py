import hashlib
import hmac

from sific.validation import SUPPORTED_ALGORITHMS, validate_expected_hash, validate_file_path

CHUNK_SIZE = 64 * 1024


def get_hasher(algo: str):
    algo = algo.lower().strip()

    if algo not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Algorithme non supporté : {algo}")

    return hashlib.new(algo)


def calculate_hash(file_path: str, algo: str = "sha256") -> str:
    path = validate_file_path(file_path)
    hasher = get_hasher(algo)

    try:
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
                hasher.update(chunk)
    except PermissionError as error:
        raise PermissionError(f"Permission refusée : {path}") from error

    return hasher.hexdigest()


def verify_hash(file_path: str, expected_hash: str, algo: str = "sha256") -> tuple[bool, str, str]:
    expected = validate_expected_hash(expected_hash, algo)
    actual = calculate_hash(file_path, algo)
    ok = hmac.compare_digest(actual, expected)

    return ok, actual, expected