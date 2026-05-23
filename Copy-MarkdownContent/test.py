#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

try:
    import argcomplete
except ImportError:
    argcomplete = None

SCRIPT_DIR = Path(__file__).parent
TESTING_DIR = SCRIPT_DIR / "testing"
TEMPLATES_DIR = TESTING_DIR / ".templates"
PARAMETERS_FILE = TESTING_DIR / "parameters.jsonl"
LOGS_FILE = TESTING_DIR / "process.jsonl"


def get_local_timestamp():
    """Get current timestamp in YYYY_MM_DD-HH_mm format (local timezone)."""
    return datetime.now().strftime("%Y_%m_%d-%H_%M")


def load_parameters():
    """Load all cases from parameters.jsonl."""
    if not PARAMETERS_FILE.exists():
        return {}

    cases = {}
    with open(PARAMETERS_FILE, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                cases[data["case_name"]] = data
    return cases


def save_parameters(cases):
    """Save all cases to parameters.jsonl (overwrite)."""
    PARAMETERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PARAMETERS_FILE, "w") as f:
        for case_name in sorted(cases.keys()):
            f.write(json.dumps(cases[case_name]) + "\n")


def case_completer(prefix, parsed_args, **kwargs):
    """Autocomplete case names from parameters.jsonl."""
    cases = load_parameters()
    return [name for name in cases.keys() if name.startswith(prefix)]


def log_process(action, status, case_name=None, details=None, error=None):
    """Log process activity to process.jsonl."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "status": status,
        "case_name": case_name,
        "details": details or {},
    }

    if error:
        log_entry["error"] = str(error)

    LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOGS_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def get_relative_file_paths(case_name, timestamp):
    """Generate relative file paths for a case and timestamp."""
    base = f"{case_name}/{timestamp}"
    files = [
        f"{base}/script-output-{case_name}-windows_explorer-file_single",
        f"{base}/script-output-{case_name}-windows_explorer-multi_file",
        f"{base}/script-output-{case_name}-windows_search-file_multi",
        f"{base}/script-output-{case_name}-windows_search-file_single",
    ]
    return files


def generate_case(case_name, case_description, test_paths=None):
    """Generate a new test case with template structure."""
    try:
        case_dir = TESTING_DIR / case_name

        if case_dir.exists():
            log_process(
                action="generate-case",
                status="failed",
                case_name=case_name,
                error=f"Case already exists at {case_dir}",
            )
            print(f"Case '{case_name}' already exists at: {case_dir}")
            sys.exit(1)

        template_source = TEMPLATES_DIR / "Case-{case_name}"
        if not template_source.exists():
            log_process(
                action="generate-case",
                status="failed",
                case_name=case_name,
                error=f"Template not found at {template_source}",
            )
            print(f"Template not found at: {template_source}")
            sys.exit(1)

        timestamp = get_local_timestamp()

        # Copy entire template structure
        shutil.copytree(template_source, case_dir)

        # Replace placeholders in directory names and filenames
        timestamp_dir = case_dir / "{YYYY_MM_DD}-{HH_mm}"
        new_timestamp_dir = case_dir / timestamp

        if timestamp_dir.exists():
            timestamp_dir.rename(new_timestamp_dir)

        # Replace {CASE} in filenames
        for file_path in new_timestamp_dir.glob("*"):
            if "{CASE}" in file_path.name:
                new_name = file_path.name.replace("{CASE}", case_name)
                file_path.rename(file_path.parent / new_name)

        # Generate relative file paths
        relative_paths = get_relative_file_paths(case_name, timestamp)

        # Save to parameters.jsonl
        cases = load_parameters()
        cases[case_name] = {
            "case_name": case_name,
            "case_description": case_description,
            "relative_file_paths": relative_paths,
            "test_input_paths": test_paths or [],
            "created_at": timestamp,
        }
        save_parameters(cases)

        log_process(
            action="generate-case",
            status="success",
            case_name=case_name,
            details={"timestamp": timestamp, "file_count": len(relative_paths)},
        )

        # Output relative file paths
        for path in relative_paths:
            print(path)

    except Exception as e:
        log_process(
            action="generate-case",
            status="error",
            case_name=case_name,
            error=e,
        )
        print(f"Error generating case: {e}")
        sys.exit(1)


def update_case(case_name):
    """Create a new timestamped iteration for an existing case."""
    try:
        cases = load_parameters()

        if case_name not in cases:
            log_process(
                action="update-case",
                status="failed",
                case_name=case_name,
                error="Case not found in parameters.jsonl",
            )
            print(f"Case '{case_name}' not found in parameters.jsonl")
            sys.exit(1)

        case_dir = TESTING_DIR / case_name
        if not case_dir.exists():
            log_process(
                action="update-case",
                status="failed",
                case_name=case_name,
                error=f"Case directory not found at {case_dir}",
            )
            print(f"Case directory not found at: {case_dir}")
            sys.exit(1)

        timestamp = get_local_timestamp()
        template_source = TEMPLATES_DIR / "Case-{case_name}" / "{YYYY_MM_DD}-{HH_mm}"

        if not template_source.exists():
            log_process(
                action="update-case",
                status="failed",
                case_name=case_name,
                error=f"Template timestamp directory not found at {template_source}",
            )
            print(f"Template timestamp directory not found at: {template_source}")
            sys.exit(1)

        # Copy template timestamp directory
        new_timestamp_dir = case_dir / timestamp
        shutil.copytree(template_source, new_timestamp_dir)

        # Replace {CASE} in filenames
        for file_path in new_timestamp_dir.glob("*"):
            if "{CASE}" in file_path.name:
                new_name = file_path.name.replace("{CASE}", case_name)
                file_path.rename(file_path.parent / new_name)

        # Generate relative file paths for this iteration
        relative_paths = get_relative_file_paths(case_name, timestamp)

        # Update parameters.jsonl with new paths
        cases[case_name]["relative_file_paths"] = relative_paths
        cases[case_name]["updated_at"] = timestamp
        save_parameters(cases)

        log_process(
            action="update-case",
            status="success",
            case_name=case_name,
            details={"timestamp": timestamp, "file_count": len(relative_paths)},
        )

        # Output relative file paths
        for path in relative_paths:
            print(path)

    except Exception as e:
        log_process(
            action="update-case",
            status="error",
            case_name=case_name,
            error=e,
        )
        print(f"Error updating case: {e}")
        sys.exit(1)


def update_paths(case_name):
    """Dynamically update relative file paths for an existing case."""
    try:
        cases = load_parameters()

        if case_name not in cases:
            log_process(
                action="update-paths",
                status="failed",
                case_name=case_name,
                error="Case not found in parameters.jsonl",
            )
            print(f"Case '{case_name}' not found in parameters.jsonl")
            sys.exit(1)

        case_dir = TESTING_DIR / case_name
        if not case_dir.exists():
            log_process(
                action="update-paths",
                status="failed",
                case_name=case_name,
                error=f"Case directory not found at {case_dir}",
            )
            print(f"Case directory not found at: {case_dir}")
            sys.exit(1)

        # Find all timestamped directories
        timestamped_dirs = sorted([d.name for d in case_dir.iterdir() if d.is_dir()])

        if not timestamped_dirs:
            log_process(
                action="update-paths",
                status="failed",
                case_name=case_name,
                error=f"No timestamped directories found in {case_dir}",
            )
            print(f"No timestamped directories found in: {case_dir}")
            sys.exit(1)

        # Use the most recent timestamp
        latest_timestamp = timestamped_dirs[-1]
        relative_paths = get_relative_file_paths(case_name, latest_timestamp)

        # Update parameters.jsonl
        cases[case_name]["relative_file_paths"] = relative_paths
        cases[case_name]["paths_updated_at"] = get_local_timestamp()
        save_parameters(cases)

        log_process(
            action="update-paths",
            status="success",
            case_name=case_name,
            details={"latest_timestamp": latest_timestamp, "file_count": len(relative_paths)},
        )

        # Output relative file paths
        for path in relative_paths:
            print(path)

    except Exception as e:
        log_process(
            action="update-paths",
            status="error",
            case_name=case_name,
            error=e,
        )
        print(f"Error updating paths: {e}")
        sys.exit(1)


def validate_case(case_name):
    """Validate case outputs against inputs and execution logs."""
    try:
        cases = load_parameters()

        if case_name not in cases:
            log_process(
                action="validate-case",
                status="failed",
                case_name=case_name,
                error="Case not found in parameters.jsonl",
            )
            print(f"Case '{case_name}' not found")
            sys.exit(1)

        case_data = cases[case_name]
        test_inputs = case_data.get("test_input_paths", [])
        output_files = case_data.get("relative_file_paths", [])
        logs_file = TESTING_DIR / "logs" / "execution.jsonl"

        if not test_inputs:
            print(f"No test inputs defined for case '{case_name}'")
            return

        validation_results = {
            "case_name": case_name,
            "timestamp": datetime.now().isoformat(),
            "inputs_tested": len(test_inputs),
            "outputs_generated": len(output_files),
            "validation_checks": [],
        }

        # Check if input files exist
        for input_path in test_inputs:
            check = {
                "input_file": input_path,
                "exists": Path(input_path).exists(),
                "size": Path(input_path).stat().st_size if Path(input_path).exists() else 0,
            }
            validation_results["validation_checks"].append(check)
            if check["exists"]:
                print(f"✓ Input: {input_path} ({check['size']} bytes)")
            else:
                print(f"✗ Input not found: {input_path}")

        # Check if output files exist
        for output_file in output_files:
            full_path = TESTING_DIR / output_file
            exists = full_path.exists()
            size = full_path.stat().st_size if exists else 0

            check = {
                "output_file": output_file,
                "exists": exists,
                "size": size,
            }

            if exists and size > 0:
                # Read and check if inputs are in output
                try:
                    with open(full_path, "r", errors="ignore") as f:
                        content = f.read()

                    check["has_content"] = True
                    check["content_length"] = len(content)
                    check["inputs_found"] = sum(1 for inp in test_inputs if Path(inp).name in content)

                    print(f"✓ Output: {output_file} ({size} bytes, found {check['inputs_found']} input filename(s))")
                except Exception as e:
                    check["error"] = str(e)
                    print(f"⚠ Output: {output_file} (error reading: {e})")
            else:
                print(f"✗ Output missing or empty: {output_file}")

            validation_results["validation_checks"].append(check)

        # Log validation
        log_process(
            action="validate-case",
            status="success",
            case_name=case_name,
            details=validation_results,
        )

        print(f"\nValidation Summary: {validation_results['inputs_tested']} inputs, {validation_results['outputs_generated']} outputs checked")

    except Exception as e:
        log_process(
            action="validate-case",
            status="error",
            case_name=case_name,
            error=e,
        )
        print(f"Error validating case: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Test case management for Copy-MarkdownContent")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate case command
    gen_parser = subparsers.add_parser("generate-case", help="Generate a new test case")
    gen_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case")
    gen_parser.add_argument("-d", "--description", dest="case_description", required=True, help="Description of the test case")
    gen_parser.add_argument("-p", "--paths", dest="test_paths", required=False, help="JSON array of file paths to test")

    # Update case command
    update_parser = subparsers.add_parser("update-case", help="Create new iteration for an existing case")
    update_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case").completer = case_completer

    # Update paths command
    paths_parser = subparsers.add_parser("update-paths", help="Dynamically update relative file paths")
    paths_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case").completer = case_completer

    # Validate case command
    validate_parser = subparsers.add_parser("validate-case", help="Validate case outputs against inputs")
    validate_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case").completer = case_completer

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if args.command == "generate-case":
        test_paths = []
        if args.test_paths:
            try:
                test_paths = json.loads(args.test_paths)
            except json.JSONDecodeError:
                print("Error: --paths must be valid JSON array")
                sys.exit(1)
        generate_case(args.case_name, args.case_description, test_paths)
    elif args.command == "update-case":
        update_case(args.case_name)
    elif args.command == "update-paths":
        update_paths(args.case_name)
    elif args.command == "validate-case":
        validate_case(args.case_name)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
