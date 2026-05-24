from pathlib import Path

SUPPORTED_ALGORITHMS = ("sha256", "sha512", "md5")

HASH_LENGTHS = {
    "md5": 32,
    "sha256": 64,
    "sha512": 128,
}


class InvalidHashError(ValueError):
    """Raised when the expected hash has an invalid format."""


class InvalidFilePathError(ValueError):
    """Raised when the provided path is invalid for file hashing."""


def validate_file_path(file_path: str) -> Path:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    if not path.is_file():
        raise InvalidFilePathError(f"Le chemin existe mais n'est pas un fichier : {path}")

    return path


def validate_expected_hash(expected_hash: str, algo: str) -> str:
    algo = algo.lower().strip()
    expected = expected_hash.strip().lower()

    expected_length = HASH_LENGTHS[algo]

    if len(expected) != expected_length:
        raise InvalidHashError(
            f"Hash invalide pour {algo.upper()} : "
            f"longueur attendue {expected_length}, reçue {len(expected)}."
        )

    if not all(char in "0123456789abcdef" for char in expected):
        raise InvalidHashError(
            "Hash invalide : seuls les caractères hexadécimaux sont autorisés (0-9, a-f)."
        )

    return expected