import argparse
import json
import sys
from typing import Any

from sific.baseline import (
    InvalidBaselineError,
    InvalidDirectoryError,
    check_baseline,
    create_baseline,
    save_baseline,
)
from sific.hachage import calculate_hash, verify_hash
from sific.validation import SUPPORTED_ALGORITHMS, InvalidFilePathError, InvalidHashError

EXIT_SUCCESS = 0
EXIT_MISMATCH = 1
EXIT_INVALID_INPUT = 3
EXIT_FILE_ERROR = 4
EXIT_INTERNAL_ERROR = 5


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def warn_weak_algorithm(algo: str, json_output: bool = False) -> None:
    if algo.lower() == "md5" and not json_output:
        print(
            "AVERTISSEMENT: MD5 est cassé cryptographiquement. "
            "À utiliser seulement pour compatibilité legacy, pas pour une garantie de sécurité.",
            file=sys.stderr,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sific",
        description="SIFIC : Simple File Integrity Checker.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    hash_parser = subparsers.add_parser(
        "hash",
        help="Génère le hachage d'un fichier.",
    )
    hash_parser.add_argument("file_path", help="Chemin du fichier.")
    hash_parser.add_argument(
        "-a",
        "--algo",
        default="sha256",
        choices=SUPPORTED_ALGORITHMS,
        help="Algorithme de hachage.",
    )
    hash_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Affiche le résultat au format JSON.",
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="Vérifie un fichier contre un hachage attendu.",
    )
    verify_parser.add_argument("file_path", help="Chemin du fichier.")
    verify_parser.add_argument(
        "--hash",
        required=True,
        dest="expected_hash",
        help="Hachage attendu.",
    )
    verify_parser.add_argument(
        "-a",
        "--algo",
        default="sha256",
        choices=SUPPORTED_ALGORITHMS,
        help="Algorithme de hachage.",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Affiche le résultat au format JSON.",
    )

    baseline_parser = subparsers.add_parser(
        "baseline",
        help="Crée ou vérifie une baseline d'intégrité pour un dossier.",
    )

    baseline_subparsers = baseline_parser.add_subparsers(
        dest="baseline_command",
        required=True,
    )

    baseline_create_parser = baseline_subparsers.add_parser(
        "create",
        help="Crée une baseline d'intégrité pour un dossier.",
    )
    baseline_create_parser.add_argument(
        "directory_path",
        help="Chemin du dossier à analyser.",
    )
    baseline_create_parser.add_argument(
        "--output",
        required=True,
        help="Chemin du fichier baseline JSON à créer.",
    )
    baseline_create_parser.add_argument(
        "-a",
        "--algo",
        default="sha256",
        choices=SUPPORTED_ALGORITHMS,
        help="Algorithme de hachage.",
    )
    baseline_create_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Affiche le résultat au format JSON.",
    )

    baseline_check_parser = baseline_subparsers.add_parser(
        "check",
        help="Compare un dossier avec une baseline existante.",
    )
    baseline_check_parser.add_argument(
        "directory_path",
        help="Chemin du dossier à vérifier.",
    )
    baseline_check_parser.add_argument(
        "--baseline",
        required=True,
        help="Chemin du fichier baseline JSON.",
    )
    baseline_check_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Affiche le résultat au format JSON.",
    )

    return parser


def handle_hash_command(args: argparse.Namespace) -> int:
    warn_weak_algorithm(args.algo, args.json_output)

    digest = calculate_hash(args.file_path, args.algo)

    if args.json_output:
        print_json(
            {
                "file": args.file_path,
                "algorithm": args.algo,
                "hash": digest,
                "status": "success",
            }
        )
        return EXIT_SUCCESS

    print(digest)
    return EXIT_SUCCESS


def handle_verify_command(args: argparse.Namespace) -> int:
    warn_weak_algorithm(args.algo, args.json_output)

    ok, actual, expected = verify_hash(
        args.file_path,
        args.expected_hash,
        args.algo,
    )

    status = "match" if ok else "mismatch"

    if args.json_output:
        print_json(
            {
                "file": args.file_path,
                "algorithm": args.algo,
                "status": status,
                "calculated": actual,
                "expected": expected,
            }
        )
        return EXIT_SUCCESS if ok else EXIT_MISMATCH

    if ok:
        print("MATCH")
        print(f"Calculated: {actual}")
        return EXIT_SUCCESS

    print("MISMATCH")
    print(f"Calculated: {actual}")
    print(f"Expected:   {expected}")

    return EXIT_MISMATCH


def handle_baseline_create_command(args: argparse.Namespace) -> int:
    warn_weak_algorithm(args.algo, args.json_output)

    baseline = create_baseline(args.directory_path, args.algo)
    save_baseline(baseline, args.output)

    total_files = len(baseline["files"])

    if args.json_output:
        print_json(
            {
                "status": "success",
                "directory": args.directory_path,
                "baseline": args.output,
                "algorithm": baseline["algorithm"],
                "files_indexed": total_files,
            }
        )
        return EXIT_SUCCESS

    print(f"Baseline créée : {args.output}")
    print(f"Fichiers indexés : {total_files}")
    print(f"Algorithme : {baseline['algorithm']}")

    return EXIT_SUCCESS


def handle_baseline_check_command(args: argparse.Namespace) -> int:
    result = check_baseline(args.directory_path, args.baseline)

    has_changes = bool(result["modified"] or result["added"] or result["deleted"])
    status = "changed" if has_changes else "unchanged"

    if args.json_output:
        print_json(
            {
                "status": status,
                "directory": args.directory_path,
                "baseline": args.baseline,
                "summary": {
                    "unchanged": len(result["unchanged"]),
                    "modified": len(result["modified"]),
                    "added": len(result["added"]),
                    "deleted": len(result["deleted"]),
                },
                "unchanged": result["unchanged"],
                "modified": result["modified"],
                "added": result["added"],
                "deleted": result["deleted"],
            }
        )
        return EXIT_MISMATCH if has_changes else EXIT_SUCCESS

    print(f"UNCHANGED: {len(result['unchanged'])}")
    print(f"MODIFIED:  {len(result['modified'])}")
    print(f"ADDED:     {len(result['added'])}")
    print(f"DELETED:   {len(result['deleted'])}")

    if result["modified"]:
        print("\nModified files:")
        for path in result["modified"]:
            print(f"  - {path}")

    if result["added"]:
        print("\nAdded files:")
        for path in result["added"]:
            print(f"  - {path}")

    if result["deleted"]:
        print("\nDeleted files:")
        for path in result["deleted"]:
            print(f"  - {path}")

    return EXIT_MISMATCH if has_changes else EXIT_SUCCESS


def print_error(error_type: str, message: str, json_output: bool = False) -> None:
    if json_output:
        print_json(
            {
                "status": "error",
                "error_type": error_type,
                "message": message,
            }
        )
        return

    print(f"ERREUR: {message}", file=sys.stderr)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "hash":
            return handle_hash_command(args)

        if args.command == "verify":
            return handle_verify_command(args)

        if args.command == "baseline":
            if args.baseline_command == "create":
                return handle_baseline_create_command(args)

            if args.baseline_command == "check":
                return handle_baseline_check_command(args)

        return EXIT_INVALID_INPUT

    except InvalidHashError as error:
        print_error(
            "invalid_hash",
            str(error),
            getattr(args, "json_output", False),
        )
        return EXIT_INVALID_INPUT

    except (
        FileNotFoundError,
        InvalidFilePathError,
        InvalidDirectoryError,
        InvalidBaselineError,
        PermissionError,
    ) as error:
        print_error(
            "file_error",
            str(error),
            getattr(args, "json_output", False),
        )
        return EXIT_FILE_ERROR

    except Exception as error:
        print_error(
            "internal_error",
            str(error),
            getattr(args, "json_output", False),
        )
        return EXIT_INTERNAL_ERROR


if __name__ == "__main__":
    raise SystemExit(main())