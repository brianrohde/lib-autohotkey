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


def safe_print(text):
    """Print text safely, handling Unicode encoding errors."""
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Replace Unicode characters with ASCII alternatives
        safe_text = text.replace('✓', '[OK]').replace('✗', '[X]').replace('⚠', '[!]')
        safe_text = safe_text.replace('📋', '[*]').replace('⏳', '[...]').replace('🔄', '[>>]')
        safe_text = safe_text.replace('📊', '[STATS]').replace('📂', '[DIR]')
        print(safe_text)

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


def generate_case(case_name, case_description, test_paths=None, use_fixtures=None):
    """Generate a new test case with template structure and optional fixtures."""
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

        # Setup inputs directory and copy fixtures if requested
        inputs_dir = case_dir / "inputs"
        inputs_dir.mkdir(exist_ok=True)
        copied_fixtures = []

        if use_fixtures:
            fixtures_dir = TEMPLATES_DIR / "fixtures"
            if fixtures_dir.exists():
                fixture_list = use_fixtures if isinstance(use_fixtures, list) else [use_fixtures]
                for fixture in fixture_list:
                    fixture_path = fixtures_dir / fixture
                    if fixture_path.exists():
                        dest_path = inputs_dir / fixture
                        shutil.copy2(fixture_path, dest_path)
                        copied_fixtures.append(str(dest_path))
                        try:
                            print(f"✓ Copied fixture: {fixture}")
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            print(f"[+] Copied fixture: {fixture}")
                    else:
                        try:
                            print(f"⚠ Fixture not found: {fixture}")
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            print(f"[!] Fixture not found: {fixture}")

        # Generate relative file paths
        relative_paths = get_relative_file_paths(case_name, timestamp)

        # Save to parameters.jsonl
        cases = load_parameters()
        cases[case_name] = {
            "case_name": case_name,
            "case_description": case_description,
            "relative_file_paths": relative_paths,
            "test_input_paths": test_paths or [],
            "fixture_files": copied_fixtures,
            "created_at": timestamp,
        }
        save_parameters(cases)

        log_process(
            action="generate-case",
            status="success",
            case_name=case_name,
            details={"timestamp": timestamp, "file_count": len(relative_paths), "fixtures_copied": len(copied_fixtures)},
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


def loop_cases(json_out=False):
    """Iterate through all test cases and run them, outputting results for agent consumption."""
    try:
        cases = load_parameters()

        if not cases:
            safe_print("No test cases found in parameters.jsonl")
            if json_out:
                safe_print(json.dumps({"status": "no_cases", "cases": []}))
            return

        safe_print(f"[>>] Running {len(cases)} test case(s)...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "total_cases": len(cases),
            "cases": [],
        }

        case_names = sorted(cases.keys())
        for i, case_name in enumerate(case_names, 1):
            case_data = cases[case_name]
            safe_print(f"\n[{i}/{len(cases)}] Running: {case_name}")
            safe_print(f"      Description: {case_data.get('case_description', 'N/A')}")

            case_result = {
                "case_name": case_name,
                "description": case_data.get("case_description", ""),
                "fixtures_count": len(case_data.get("fixture_files", [])),
                "status": "unknown",
                "execution_log": None,
                "validation_summary": None,
            }

            # Check if execution logs exist for this case
            logs_file = TESTING_DIR / "logs" / "execution.jsonl"
            if logs_file.exists():
                try:
                    with open(logs_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            # Find last valid JSON line
                            for line in reversed(lines):
                                try:
                                    last_log = json.loads(line.strip())
                                    if last_log:
                                        case_result["execution_log"] = last_log
                                        case_result["status"] = last_log.get("status", "unknown")
                                        safe_print(f"      Execution: {last_log.get('status')} "
                                                   f"({last_log.get('files_processed')}/{last_log.get('files_requested')} processed)")
                                        break
                                except json.JSONDecodeError:
                                    continue
                except Exception as e:
                    safe_print(f"      [!] Could not read logs: {e}")

            # Check for captured outputs
            script_outputs = list(TESTING_DIR.glob("script-output-*.txt"))
            if script_outputs:
                case_result["captured_outputs"] = len(script_outputs)
                safe_print(f"      Outputs: {len(script_outputs)} clipboard capture(s)")

            # Get validation status
            fixture_files = case_data.get("fixture_files", [])
            if fixture_files:
                fixtures_exist = sum(1 for f in fixture_files if Path(f).exists())
                case_result["fixtures_ready"] = fixtures_exist == len(fixture_files)
                safe_print(f"      Fixtures: {fixtures_exist}/{len(fixture_files)} ready")

            results["cases"].append(case_result)

        # Calculate summary
        results["summary"] = {
            "success_count": sum(1 for c in results["cases"] if c["status"] == "success"),
            "partial_count": sum(1 for c in results["cases"] if c["status"] == "partial"),
            "failed_count": sum(1 for c in results["cases"] if c["status"] == "failed"),
            "no_files_count": sum(1 for c in results["cases"] if c["status"] == "no_files"),
        }

        # Log the loop execution
        log_process(
            action="loop-cases",
            status="success",
            details=results,
        )

        safe_print(f"\n[STATS] Summary:")
        safe_print(f"  [OK] Success: {results['summary']['success_count']}")
        safe_print(f"  [!] Partial: {results['summary']['partial_count']}")
        safe_print(f"  [X] Failed: {results['summary']['failed_count']}")
        safe_print(f"  [ ] No files: {results['summary']['no_files_count']}")

        if json_out:
            safe_print("\n" + json.dumps(results, indent=2))

    except Exception as e:
        log_process(
            action="loop-cases",
            status="error",
            error=e,
        )
        safe_print(f"Error running loop: {e}")
        if json_out:
            safe_print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


def run_case(case_name, scenarios=None):
    """Run a test case: setup inputs, trigger script, capture output, validate results."""
    try:
        cases = load_parameters()

        if case_name not in cases:
            log_process(
                action="run-case",
                status="failed",
                case_name=case_name,
                error="Case not found in parameters.jsonl",
            )
            safe_print(f"Case '{case_name}' not found")
            sys.exit(1)

        case_data = cases[case_name]
        fixture_files = case_data.get("fixture_files", [])

        safe_print(f"Running test case: {case_name}")

        # Setup phase: ensure input files exist
        if fixture_files:
            safe_print(f"[OK] {len(fixture_files)} fixture file(s) available")
            for fixture in fixture_files:
                if Path(fixture).exists():
                    safe_print(f"  [OK] {Path(fixture).name} ({Path(fixture).stat().st_size} bytes)")
        else:
            safe_print("[!] No fixture files set up for this case")

        # Log the run
        log_process(
            action="run-case",
            status="started",
            case_name=case_name,
            details={"fixtures_count": len(fixture_files), "scenarios": scenarios or "all"},
        )

        # Instructions for manual trigger
        safe_print("\n[*] Instructions:")
        safe_print("1. Open Windows Explorer or file search window")
        if fixture_files:
            safe_print("2. Navigate to and select these files:")
            for fixture in fixture_files:
                safe_print(f"   {fixture}")
        safe_print("3. Press Ctrl+Shift+Alt+C to trigger the script")
        safe_print("4. Script will log output to testing/ directory")
        safe_print("5. Run 'python test.py validate-case -n \"" + case_name + "\"' to check results")

        log_process(
            action="run-case",
            status="awaiting_input",
            case_name=case_name,
            details={"message": "Waiting for manual script trigger"},
        )

        safe_print("\n[...] Waiting for script execution (press Enter when done, or Ctrl+C to cancel)...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            safe_print("\nCancelled.")
            log_process(
                action="run-case",
                status="cancelled",
                case_name=case_name,
            )
            return

        # Check for execution logs
        logs_file = TESTING_DIR / "logs" / "execution.jsonl"
        if logs_file.exists():
            try:
                with open(logs_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        for line in reversed(lines):
                            try:
                                last_log = json.loads(line.strip())
                                if last_log:
                                    safe_print(f"\n[OK] Script executed:")
                                    safe_print(f"  Status: {last_log.get('status')}")
                                    safe_print(f"  Files requested: {last_log.get('files_requested')}")
                                    safe_print(f"  Files processed: {last_log.get('files_processed')}")
                                    safe_print(f"  Files failed: {last_log.get('files_failed')}")
                                    safe_print(f"  Files skipped: {last_log.get('files_skipped')}")
                                    break
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                safe_print(f"[!] Could not read logs: {e}")

        # Run validation
        safe_print("\nValidating results...")
        validate_case(case_name)

        log_process(
            action="run-case",
            status="success",
            case_name=case_name,
        )

    except Exception as e:
        log_process(
            action="run-case",
            status="error",
            case_name=case_name,
            error=e,
        )
        safe_print(f"Error running case: {e}")
        sys.exit(1)


def validate_case(case_name):
    """Validate case outputs against inputs and check captured clipboard outputs."""
    try:
        cases = load_parameters()

        if case_name not in cases:
            log_process(
                action="validate-case",
                status="failed",
                case_name=case_name,
                error="Case not found in parameters.jsonl",
            )
            safe_print(f"Case '{case_name}' not found")
            sys.exit(1)

        case_data = cases[case_name]
        test_inputs = case_data.get("test_input_paths", [])
        fixture_files = case_data.get("fixture_files", [])
        output_files = case_data.get("relative_file_paths", [])
        logs_file = TESTING_DIR / "logs" / "execution.jsonl"

        validation_results = {
            "case_name": case_name,
            "timestamp": datetime.now().isoformat(),
            "inputs_tested": len(test_inputs),
            "fixtures_used": len(fixture_files),
            "outputs_generated": len(output_files),
            "validation_checks": [],
            "captured_outputs": [],
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
                safe_print(f"[OK] Input: {input_path} ({check['size']} bytes)")
            else:
                safe_print(f"[X] Input not found: {input_path}")

        # Check fixture files
        for fixture_path in fixture_files:
            check = {
                "fixture_file": fixture_path,
                "exists": Path(fixture_path).exists(),
                "size": Path(fixture_path).stat().st_size if Path(fixture_path).exists() else 0,
            }
            validation_results["validation_checks"].append(check)
            if check["exists"]:
                print(f"✓ Fixture: {fixture_path} ({check['size']} bytes)")
            else:
                print(f"✗ Fixture not found: {fixture_path}")

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

                    # Check for markdown headers and input filenames
                    headers = [line for line in content.split('\n') if line.startswith('# ')]
                    check["markdown_headers"] = len(headers)

                    # Check for fixture/input file references
                    inputs_found = sum(1 for inp in test_inputs if Path(inp).name in content)
                    fixtures_found = sum(1 for fix in fixture_files if Path(fix).name in content)
                    check["inputs_found"] = inputs_found
                    check["fixtures_found"] = fixtures_found
                    check["has_markdown_formatting"] = len(headers) > 0

                    print(f"✓ Output: {output_file} ({size} bytes, {len(headers)} headers)")
                except Exception as e:
                    check["error"] = str(e)
                    safe_print(f"[!] Output: {output_file} (error reading: {e})")
            else:
                safe_print(f"[X] Output missing or empty: {output_file}")

            validation_results["validation_checks"].append(check)

        # Check for script output files (clipboard captures)
        testing_dir = TESTING_DIR
        script_outputs = list(testing_dir.glob("script-output-*.txt"))
        if script_outputs:
            safe_print(f"\n[*] Found {len(script_outputs)} captured clipboard outputs:")
            for output_path in sorted(script_outputs):
                try:
                    size = output_path.stat().st_size
                    with open(output_path, "r", errors="ignore") as f:
                        content = f.read()

                    headers = [line for line in content.split('\n') if line.startswith('# ')]
                    capture_info = {
                        "filename": output_path.name,
                        "size": size,
                        "headers_found": len(headers),
                        "has_markdown": len(headers) > 0,
                        "content_length": len(content),
                    }

                    # Check if fixture files are referenced
                    fixtures_in_output = sum(1 for fix in fixture_files if Path(fix).name in content)
                    if fixtures_in_output > 0:
                        capture_info["fixtures_referenced"] = fixtures_in_output

                    validation_results["captured_outputs"].append(capture_info)
                    safe_print(f"  [OK] {output_path.name}: {len(headers)} headers, {size} bytes")
                except Exception as e:
                    safe_print(f"  [!] {output_path.name}: error reading ({e})")

        # Log validation
        log_process(
            action="validate-case",
            status="success",
            case_name=case_name,
            details=validation_results,
        )

        summary = f"Validation Summary: {validation_results['inputs_tested']} inputs, {validation_results['fixtures_used']} fixtures, {len(script_outputs)} clipboard outputs checked"
        safe_print(f"\n{summary}")

    except Exception as e:
        log_process(
            action="validate-case",
            status="error",
            case_name=case_name,
            error=e,
        )
        safe_print(f"Error validating case: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Test case management for Copy-MarkdownContent")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate case command
    gen_parser = subparsers.add_parser("generate-case", help="Generate a new test case")
    gen_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case")
    gen_parser.add_argument("-d", "--description", dest="case_description", required=True, help="Description of the test case")
    gen_parser.add_argument("-p", "--paths", dest="test_paths", required=False, help="JSON array of file paths to test")
    gen_parser.add_argument("-f", "--fixtures", dest="use_fixtures", required=False, help="JSON array of fixture files to copy (e.g., '[\"small.md\", \"large.txt\"]')")

    # Update case command
    update_parser = subparsers.add_parser("update-case", help="Create new iteration for an existing case")
    update_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case").completer = case_completer

    # Update paths command
    paths_parser = subparsers.add_parser("update-paths", help="Dynamically update relative file paths")
    paths_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case").completer = case_completer

    # Loop cases command
    loop_parser = subparsers.add_parser("loop-cases", help="Run all test cases and output results for agents")
    loop_parser.add_argument("-j", "--json-out", dest="json_out", action="store_true", help="Output results as JSON")

    # Run case command
    run_parser = subparsers.add_parser("run-case", help="Run a test case and validate results")
    run_parser.add_argument("-n", "--name", dest="case_name", required=True, help="Name of the test case").completer = case_completer
    run_parser.add_argument("-s", "--scenarios", dest="scenarios", required=False, help="Comma-separated scenarios to test (e.g., single,multi,large)")

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

        use_fixtures = None
        if args.use_fixtures:
            try:
                use_fixtures = json.loads(args.use_fixtures)
            except json.JSONDecodeError:
                print("Error: --fixtures must be valid JSON array")
                sys.exit(1)

        generate_case(args.case_name, args.case_description, test_paths, use_fixtures)
    elif args.command == "update-case":
        update_case(args.case_name)
    elif args.command == "update-paths":
        update_paths(args.case_name)
    elif args.command == "loop-cases":
        loop_cases(json_out=args.json_out)
    elif args.command == "run-case":
        scenarios = args.scenarios.split(",") if args.scenarios else None
        run_case(args.case_name, scenarios)
    elif args.command == "validate-case":
        validate_case(args.case_name)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
