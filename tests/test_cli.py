import hashlib
import json
import subprocess
import sys


def run_sific(*args):
    return subprocess.run(
        [sys.executable, "-m", "sific.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_hash_success(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    expected = hashlib.sha256(b"test").hexdigest()

    result = run_sific("hash", str(fichier))

    assert result.returncode == 0
    assert expected in result.stdout


def test_cli_verify_match(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    expected = hashlib.sha256(b"test").hexdigest()

    result = run_sific("verify", str(fichier), "--hash", expected)

    assert result.returncode == 0
    assert "MATCH" in result.stdout


def test_cli_verify_mismatch(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    wrong_hash = "0" * 64

    result = run_sific("verify", str(fichier), "--hash", wrong_hash)

    assert result.returncode == 1
    assert "MISMATCH" in result.stdout


def test_cli_invalid_hash(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    result = run_sific("verify", str(fichier), "--hash", "deadbeef")

    assert result.returncode == 3
    assert "Hash invalide" in result.stderr


def test_cli_missing_file(tmp_path):
    fichier = tmp_path / "missing.txt"

    result = run_sific("hash", str(fichier))

    assert result.returncode == 4
    assert "Fichier introuvable" in result.stderr


def test_cli_directory_instead_of_file(tmp_path):
    result = run_sific("hash", str(tmp_path))

    assert result.returncode == 4
    assert "n'est pas un fichier" in result.stderr

def test_cli_hash_json_success(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    result = run_sific("hash", str(fichier), "--json")

    data = json.loads(result.stdout)

    assert result.returncode == 0
    assert data["status"] == "success"
    assert data["algorithm"] == "sha256"
    assert data["file"] == str(fichier)
    assert len(data["hash"]) == 64


def test_cli_verify_json_match(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    hash_result = run_sific("hash", str(fichier))
    expected_hash = hash_result.stdout.strip()

    result = run_sific("verify", str(fichier), "--hash", expected_hash, "--json")
    data = json.loads(result.stdout)

    assert result.returncode == 0
    assert data["status"] == "match"
    assert data["calculated"] == expected_hash
    assert data["expected"] == expected_hash


def test_cli_verify_json_mismatch(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    wrong_hash = "0" * 64

    result = run_sific("verify", str(fichier), "--hash", wrong_hash, "--json")
    data = json.loads(result.stdout)

    assert result.returncode == 1
    assert data["status"] == "mismatch"
    assert data["expected"] == wrong_hash
    assert len(data["calculated"]) == 64


def test_cli_invalid_hash_json_error(tmp_path):
    fichier = tmp_path / "test.txt"
    fichier.write_text("test", encoding="utf-8")

    result = run_sific("verify", str(fichier), "--hash", "deadbeef", "--json")
    data = json.loads(result.stdout)

    assert result.returncode == 3
    assert data["status"] == "error"
    assert data["error_type"] == "invalid_hash"
    assert "Hash invalide" in data["message"]


def test_cli_baseline_check_json_unchanged(tmp_path):
    fichier = tmp_path / "app.conf"
    fichier.write_text("clean", encoding="utf-8")

    baseline_path = tmp_path / "baseline.json"

    create_result = run_sific(
        "baseline",
        "create",
        str(tmp_path),
        "--output",
        str(baseline_path),
        "--json",
    )
    create_data = json.loads(create_result.stdout)

    assert create_result.returncode == 0
    assert create_data["status"] == "success"
    assert create_data["files_indexed"] == 1

    check_result = run_sific(
        "baseline",
        "check",
        str(tmp_path),
        "--baseline",
        str(baseline_path),
        "--json",
    )
    check_data = json.loads(check_result.stdout)

    assert check_result.returncode == 0
    assert check_data["status"] == "unchanged"
    assert check_data["summary"]["unchanged"] == 1
    assert check_data["summary"]["modified"] == 0
    assert check_data["summary"]["added"] == 0
    assert check_data["summary"]["deleted"] == 0


def test_cli_baseline_check_json_detects_changes(tmp_path):
    app_file = tmp_path / "app.conf"
    users_file = tmp_path / "users.conf"

    app_file.write_text("clean", encoding="utf-8")
    users_file.write_text("admin=true", encoding="utf-8")

    baseline_path = tmp_path / "baseline.json"

    run_sific(
        "baseline",
        "create",
        str(tmp_path),
        "--output",
        str(baseline_path),
    )

    app_file.write_text("modified", encoding="utf-8")
    users_file.unlink()

    suspicious_file = tmp_path / "suspicious.conf"
    suspicious_file.write_text("new", encoding="utf-8")

    result = run_sific(
        "baseline",
        "check",
        str(tmp_path),
        "--baseline",
        str(baseline_path),
        "--json",
    )
    data = json.loads(result.stdout)

    assert result.returncode == 1
    assert data["status"] == "changed"
    assert data["summary"]["modified"] == 1
    assert data["summary"]["added"] == 1
    assert data["summary"]["deleted"] == 1
    assert data["modified"] == ["app.conf"]
    assert data["added"] == ["suspicious.conf"]
    assert data["deleted"] == ["users.conf"]