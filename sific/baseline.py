import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sific.hachage import calculate_hash
from sific.validation import SUPPORTED_ALGORITHMS


class InvalidDirectoryError(ValueError):
    """Raised when the provided path is not a valid directory."""


class InvalidBaselineError(ValueError):
    """Raised when the baseline file is invalid."""


def validate_directory_path(directory_path: str) -> Path:
    path = Path(directory_path)

    if not path.exists():
        raise FileNotFoundError(f"Dossier introuvable : {path}")

    if not path.is_dir():
        raise InvalidDirectoryError(f"Le chemin existe mais n'est pas un dossier : {path}")

    return path


def scan_directory(directory_path: str, algo: str = "sha256") -> dict[str, str]:
    root = validate_directory_path(directory_path)
    files: dict[str, str] = {}

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(root).as_posix()
        files[relative_path] = calculate_hash(str(path), algo)

    return files


def create_baseline(directory_path: str, algo: str = "sha256") -> dict[str, Any]:
    algo = algo.lower().strip()

    if algo not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Algorithme non supporté : {algo}")

    root = validate_directory_path(directory_path)

    return {
        "version": 1,
        "algorithm": algo,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root": str(root.resolve()),
        "files": scan_directory(str(root), algo),
    }


def save_baseline(baseline: dict[str, Any], output_path: str) -> None:
    path = Path(output_path)

    with path.open("w", encoding="utf-8") as file:
        json.dump(baseline, file, indent=2, sort_keys=True)


def load_baseline(baseline_path: str) -> dict[str, Any]:
    path = Path(baseline_path)

    if not path.exists():
        raise FileNotFoundError(f"Baseline introuvable : {path}")

    if not path.is_file():
        raise InvalidBaselineError(f"Le chemin de baseline n'est pas un fichier : {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            baseline = json.load(file)
    except json.JSONDecodeError as error:
        raise InvalidBaselineError(f"Baseline JSON invalide : {error}") from error

    validate_baseline_schema(baseline)

    return baseline


def validate_baseline_schema(baseline: dict[str, Any]) -> None:
    required_keys = {"version", "algorithm", "created_at", "root", "files"}

    if not isinstance(baseline, dict):
        raise InvalidBaselineError("Baseline invalide : le contenu doit être un objet JSON.")

    missing_keys = required_keys - baseline.keys()

    if missing_keys:
        raise InvalidBaselineError(
            f"Baseline invalide : clés manquantes : {', '.join(sorted(missing_keys))}."
        )

    if baseline["algorithm"] not in SUPPORTED_ALGORITHMS:
        raise InvalidBaselineError(
            f"Baseline invalide : algorithme non supporté : {baseline['algorithm']}."
        )

    if not isinstance(baseline["files"], dict):
        raise InvalidBaselineError("Baseline invalide : 'files' doit être un objet.")


def check_baseline(directory_path: str, baseline_path: str) -> dict[str, list[str]]:
    baseline = load_baseline(baseline_path)
    algo = baseline["algorithm"]

    root = validate_directory_path(directory_path)

    expected_files: dict[str, str] = baseline["files"]
    current_files = scan_directory(str(root), algo)

    baseline_file = Path(baseline_path).resolve()

    try:
        baseline_relative_path = baseline_file.relative_to(root.resolve()).as_posix()
        current_files.pop(baseline_relative_path, None)
    except ValueError:
        pass

    expected_paths = set(expected_files.keys())
    current_paths = set(current_files.keys())

    added = sorted(current_paths - expected_paths)
    deleted = sorted(expected_paths - current_paths)

    common_paths = expected_paths & current_paths

    modified = sorted(
        path
        for path in common_paths
        if current_files[path] != expected_files[path]
    )

    unchanged = sorted(
        path
        for path in common_paths
        if current_files[path] == expected_files[path]
    )

    return {
        "unchanged": unchanged,
        "modified": modified,
        "added": added,
        "deleted": deleted,
    }