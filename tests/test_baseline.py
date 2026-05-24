import json

import pytest

from sific.baseline import (
    InvalidBaselineError,
    InvalidDirectoryError,
    check_baseline,
    create_baseline,
    load_baseline,
    save_baseline,
    scan_directory,
    validate_directory_path,
)


def test_validate_directory_path_accepts_existing_directory(tmp_path):
    assert validate_directory_path(str(tmp_path)) == tmp_path


def test_validate_directory_path_rejects_missing_directory(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        validate_directory_path(str(missing))


def test_validate_directory_path_rejects_file(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test", encoding="utf-8")

    with pytest.raises(InvalidDirectoryError):
        validate_directory_path(str(file_path))


def test_scan_directory_hashes_files_recursively(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()

    file_a = tmp_path / "a.txt"
    file_b = nested / "b.txt"

    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    result = scan_directory(str(tmp_path), "sha256")

    assert sorted(result.keys()) == ["a.txt", "nested/b.txt"]
    assert len(result["a.txt"]) == 64
    assert len(result["nested/b.txt"]) == 64


def test_create_baseline_contains_expected_schema(tmp_path):
    file_path = tmp_path / "app.conf"
    file_path.write_text("clean", encoding="utf-8")

    baseline = create_baseline(str(tmp_path), "sha256")

    assert baseline["version"] == 1
    assert baseline["algorithm"] == "sha256"
    assert "created_at" in baseline
    assert "root" in baseline
    assert "files" in baseline
    assert "app.conf" in baseline["files"]


def test_save_and_load_baseline(tmp_path):
    file_path = tmp_path / "app.conf"
    file_path.write_text("clean", encoding="utf-8")

    baseline = create_baseline(str(tmp_path), "sha256")
    output = tmp_path / "baseline.json"

    save_baseline(baseline, str(output))
    loaded = load_baseline(str(output))

    assert loaded == baseline


def test_load_baseline_rejects_invalid_json(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(InvalidBaselineError):
        load_baseline(str(baseline_path))


def test_load_baseline_rejects_missing_keys(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"version": 1}), encoding="utf-8")

    with pytest.raises(InvalidBaselineError):
        load_baseline(str(baseline_path))


def test_check_baseline_unchanged(tmp_path):
    file_path = tmp_path / "app.conf"
    file_path.write_text("clean", encoding="utf-8")

    baseline = create_baseline(str(tmp_path), "sha256")
    baseline_path = tmp_path / "baseline.json"
    save_baseline(baseline, str(baseline_path))

    result = check_baseline(str(tmp_path), str(baseline_path))

    assert result["modified"] == []
    assert result["added"] == []
    assert result["deleted"] == []
    assert result["unchanged"] == ["app.conf"]


def test_check_baseline_detects_modified_added_and_deleted_files(tmp_path):
    app_file = tmp_path / "app.conf"
    users_file = tmp_path / "users.conf"

    app_file.write_text("clean", encoding="utf-8")
    users_file.write_text("admin=true", encoding="utf-8")

    baseline = create_baseline(str(tmp_path), "sha256")
    baseline_path = tmp_path / "baseline.json"
    save_baseline(baseline, str(baseline_path))

    app_file.write_text("modified", encoding="utf-8")
    users_file.unlink()

    suspicious_file = tmp_path / "suspicious.conf"
    suspicious_file.write_text("new", encoding="utf-8")

    result = check_baseline(str(tmp_path), str(baseline_path))

    assert result["modified"] == ["app.conf"]
    assert result["added"] == ["suspicious.conf"]
    assert result["deleted"] == ["users.conf"]