import pytest

from sific.validation import (
    InvalidFilePathError,
    InvalidHashError,
    validate_expected_hash,
    validate_file_path,
)


def test_validate_expected_hash_accepts_valid_sha256():
    valid_hash = "A" * 64

    result = validate_expected_hash(valid_hash, "sha256")

    assert result == "a" * 64


def test_validate_expected_hash_rejects_short_hash():
    with pytest.raises(InvalidHashError):
        validate_expected_hash("deadbeef", "sha256")


def test_validate_expected_hash_rejects_non_hexadecimal_hash():
    invalid_hash = "z" * 64

    with pytest.raises(InvalidHashError):
        validate_expected_hash(invalid_hash, "sha256")


def test_validate_file_path_accepts_existing_file(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    result = validate_file_path(str(fichier))

    assert result == fichier


def test_validate_file_path_rejects_missing_file(tmp_path):
    fichier = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        validate_file_path(str(fichier))


def test_validate_file_path_rejects_directory(tmp_path):
    with pytest.raises(InvalidFilePathError):
        validate_file_path(str(tmp_path))