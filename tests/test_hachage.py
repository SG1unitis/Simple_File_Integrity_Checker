import hashlib

from sific.hachage import calculate_hash, verify_hash


def test_calculate_sha256(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    expected = hashlib.sha256(b"test").hexdigest()

    assert calculate_hash(str(fichier), "sha256") == expected


def test_calculate_sha512(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    expected = hashlib.sha512(b"test").hexdigest()

    assert calculate_hash(str(fichier), "sha512") == expected


def test_calculate_md5(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    expected = hashlib.md5(b"test").hexdigest()

    assert calculate_hash(str(fichier), "md5") == expected


def test_verify_hash_match(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    expected = hashlib.sha256(b"test").hexdigest()

    ok, actual, received = verify_hash(str(fichier), expected, "sha256")

    assert ok is True
    assert actual == expected
    assert received == expected


def test_verify_hash_mismatch(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    wrong_hash = "0" * 64

    ok, actual, received = verify_hash(str(fichier), wrong_hash, "sha256")

    assert ok is False
    assert actual != wrong_hash
    assert received == wrong_hash