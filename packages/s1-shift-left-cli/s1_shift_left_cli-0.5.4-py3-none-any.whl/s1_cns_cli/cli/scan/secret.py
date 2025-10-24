import hashlib
import json
import logging
import os.path
import subprocess
import sys
import tempfile
import uuid

from tabulate import tabulate

from s1_cns_cli.cli.config import get_config_manager
from s1_cns_cli.cli.registry import CodeTypeSubParser, BASELINE_FILE, MissingRequiredFlagsException, \
    MissingDependenciesException, \
    LogColors, PUBLISH_ISSUES_API, OUTPUT_FORMAT, \
    SEVERITY_MAP, ScanNotEnabledException, HttpMethod, ScanFailedException
from s1_cns_cli.cli.utils import read_json_file, write_json_to_file, get_version, \
    print_output_on_file, get_severity_color, get_wrapping_length, wrap_text, get_priority, \
    get_output_file_and_format, get_sarif_payload, get_actionable_and_non_actionable, make_request

LOGGER = logging.getLogger("cli")
HASH_STRING = "pingsafe_hashing_string"


def print_detectors(args, detectors, global_config_data):
    output_file, output_format = get_output_file_and_format(args)
    required_width = get_wrapping_length(4)
    if len(detectors) > 0:
        table_data = []
        for detector in detectors:
            severity_color = get_severity_color(detector["severity"])
            table_data.append({
                "Type": detector["type"],
                "Severity": wrap_text(severity_color + detector["severity"] + LogColors.ENDC, required_width),
                "Can-Verify": wrap_text(str(detector["can_verify"]), required_width),
            })
        print(tabulate(table_data, headers="keys", tablefmt="psql"))
        print_output_on_file(detectors, output_file, output_format)
    else:
        LOGGER.info("No detectors found.")
    return 0


def secret_parser(args, cache_directory):
    secret_pre_evaluation(args)

    manager = get_config_manager()
    global_config_data = manager.get_global()
    secret_config_data = manager.get_secret()

    # Calling secret-detector binary
    issues = call_secret_detector(args, global_config_data, secret_config_data, cache_directory)

    if args.generate_baseline and args.range:
        return generate_baseline(issues, args.directory)

    if args.list_detectors:
        return print_detectors(args, issues, global_config_data)

    if len(issues) > 0:
        return secret_post_evaluation(args, issues, secret_config_data, global_config_data)
    else:
        print(LogColors.OKGREEN + "RESULT\tScan completed. No issue found!" + LogColors.ENDC)
    return 0


def is_git_installed():
    try:
        result = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def secret_pre_evaluation(args):
    if args.generate_baseline and (len(args.range) < 2):
        raise MissingRequiredFlagsException("Please provide mandatory flag --range while generating baseline.")

    if args.publish_result and not args.pull_request and not args.pre_commit:
        raise MissingRequiredFlagsException(
            "Publish result for secret scanning will only works with pre-commit or pull-request.")

    if (args.all_commits or args.range or args.pull_request or
        args.scan_commit or args.pre_commit) and not is_git_installed():
        raise MissingDependenciesException("git not found. Please install Git or ensure it's in your system's PATH.")

    if args.list_detectors:
        return

    manager = get_config_manager()
    secret_config = manager.get_secret()
    secret_scan_enabled = secret_config.get("enabled", False)
    if not secret_scan_enabled:
        raise ScanNotEnabledException("secret scan is disabled")


def generate_baseline(issues, repo_path):
    baseline_path = os.path.join(repo_path, BASELINE_FILE)

    result_hash = [generate_components_hash(issue["detectedSecret"]["patches"], issue["type"]) for issue in issues]

    write_json_to_file(baseline_path, {"ignored_secrets_hash": list(set(result_hash))})
    LOGGER.info(f"Baseline generated successfully at {baseline_path}")
    return 0


def secret_post_evaluation(args, issues, secret_config_data, global_config_data):
    filtered_findings = []
    ignored_secrets_hash = []
    exit_code = 0

    baseline_path = os.path.join(args.directory, BASELINE_FILE)
    if os.path.exists(baseline_path):
        baseline_data = read_json_file(baseline_path)
        ignored_secrets_hash = baseline_data["ignored_secrets_hash"]

    for issue in issues:
        if args.include_ignored:
            filtered_findings.append(issue)
        elif generate_components_hash(issue["detectedSecret"]["patches"], issue["type"]) not in ignored_secrets_hash:
            filtered_findings.append(issue)

    show_commit_id = False
    if args.all_commits or args.range or args.pull_request or args.scan_commit:
        show_commit_id = True

    if len(filtered_findings) > 0:
        sorted_findings = sorted(filtered_findings, key=get_priority)
        actionable_findings, _ = get_actionable_and_non_actionable(sorted_findings, secret_config_data["severity"])

        if bool(secret_config_data["exitOnlyOnVerifiedSecret"]):
            actionable_findings = [af for af in actionable_findings if af["isSecretVerified"]]

        exit_code = 1 if len(actionable_findings) > 0 else 0

        if args.show_all_findings:
            actionable_findings = sorted_findings

        # as shell is not available in pre-commit, hence not printing table on console
        if args.pre_commit and not args.quiet and not args.verbose:
            LOGGER.warning(
                "Please use --quiet/-q(recommended) or --verbose mode with pre-commit. By default, results are shown in quiet mode.")
            args.quiet = True

        print_issue_on_console(actionable_findings, args.quiet, args.verbose, show_commit_id, args.disable_verification)
        save_issues_on_file(args, actionable_findings, global_config_data)
        send_result_to_sentinelone(args, actionable_findings, global_config_data)
        print("RESULT\tScan completed. Found " + str(len(actionable_findings)) + " issues.")
    else:
        print(LogColors.OKGREEN + "RESULT\tScan completed. No issue found!" + LogColors.ENDC)

    return exit_code


def call_secret_detector(args, global_config_data, secret_config_data, cache_directory):
    output_file_for_secret_detector = ""
    try:
        output_file_for_secret_detector = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.json")

        command = generate_command(args, global_config_data, secret_config_data, output_file_for_secret_detector,
                                   cache_directory)
        result = subprocess.run(command)
        exit_code = result.returncode
        if exit_code != 0:
            raise ScanFailedException()
        if os.path.exists(output_file_for_secret_detector):
            return read_json_file(output_file_for_secret_detector)
        return []
    except Exception as e:
        raise e
    finally:
        if os.path.exists(output_file_for_secret_detector):
            os.remove(output_file_for_secret_detector)


def generate_command(args, global_config_data, secret_config_data, output_file, cache_directory):
    workers_count = global_config_data["workers_count"]
    if args.global_workers_count:
        workers_count = args.global_workers_count

    version = get_version()
    secret_detector_binary_path = os.path.join(cache_directory, "bin", version, "bin_secret_detector")
    if not os.path.exists(secret_detector_binary_path):
        raise MissingDependenciesException(f"Missing bin_secret_detector {version}")

    command = [secret_detector_binary_path, "--output-path", output_file]
    if args.list_detectors:
        command.extend(["--list-detectors"])
        return command

    if len(args.directory) == 0:
        LOGGER.warning("Please provide mandatory flag -d/directory")
        sys.exit(0)

    command.extend(["--repo-path", args.directory, "--worker-count",
                    str(workers_count)])

    paths_to_skip = args.skip_paths + global_config_data.get("pathToIgnore", [])
    exclude_detectors = get_detectors_to_exclude(secret_config_data, args.exclude_detectors)
    extensions_to_exclude = args.exclude_extensions
    if len(extensions_to_exclude) == 0:
        extensions_to_exclude = secret_config_data.get("excludeExtensions", [])

    if args.verified_only:
        command.extend(["--verified-only"])
    if args.all_commits:
        command.extend(["--all-commits"])
    if args.pre_commit:
        command.extend(["--pre-commit"])
    if args.scan_commit is not None:
        command.extend(["--scan-commit", "--commit", args.scan_commit])
    if args.disable_verification:
        command.extend(["--disable-verification"])
    if len(paths_to_skip) > 0:
        for path in paths_to_skip:
            if os.path.isabs(path):
                LOGGER.error("absolute paths are not allowed in skip-path")
                sys.exit(1)
            if args.all_commits or args.scan_commit or args.pre_commit or args.pull_request:
                if os.path.isdir(os.path.join(args.directory, path)):
                    """
                    In all cases other than cur-dir scan we get path from git
                    path-from-git =>  parent/abc.txt
                    skip-path => parent
                    
                    expected-behaviour => skip parent dir
                    but doublestar won't block it as glob pattern not matching str
                    in case of cur-dir scan we block as we traverse file-system
                    
                    to align it with other scanners, we check if its is a valid dir or not
                    if yes append **/* to block the path 
                    """
                    path += "**/*"
            command.extend(["--skip-path", path])
    if args.range:
        command.extend(["--range", "--start", args.range[0], "--end", args.range[1]])
    if args.pull_request:
        command.extend(["--pull-request", "--start", args.pull_request[1], "--end", args.pull_request[0]])
    if len(exclude_detectors) > 0:
        for detector in exclude_detectors:
            command.extend(["--excluded-detectors", detector])
    if args.debug:
        command.extend(["--debug"])
    if args.mask_secret:
        command.extend(["--mask-secret"])
    if len(extensions_to_exclude) > 0:
        for extension in extensions_to_exclude:
            command.extend(["--exclude-extension", extension])

    return command


def get_detectors_to_exclude(secret_config_data, exclude_detectors):
    admin_blacklisted_detectors = []
    insuppressible_detectors = []

    if "blacklistedDetectors" in secret_config_data:
        admin_blacklisted_detectors = secret_config_data.get(["blacklistedDetectors", []])
    if "insuppressibleDetectors" in secret_config_data:
        insuppressible_detectors = secret_config_data.get("insuppressibleDetectors", [])

    uniq_detectors_to_exclude = list(set(admin_blacklisted_detectors + exclude_detectors))

    return [detector for detector in uniq_detectors_to_exclude if detector not in insuppressible_detectors]


def generate_components_hash(secret_patches, detector_type):
    sorted_components = sorted(secret_patches.keys())
    return detector_type.lower() + "_" + calculate_hash(
        "".join(secret_patches[component]["value"] for component in sorted_components), "sha256")


def calculate_hash(string, algorithm):
    string += HASH_STRING
    hash_object = hashlib.new(algorithm)
    hash_object.update(string.encode("utf-8"))
    return hash_object.hexdigest()


def print_issue_on_console(issues, quiet, verbose, show_commit_id, is_verification_disabled):
    if verbose:
        print(json.dumps(issues, indent=4))
        return

    table_data = []
    for issue in issues:
        line_numbers = [str(line)
                        for patch in issue["detectedSecret"]["patches"].values()
                        for line in patch["lines"]]
        line_numbers = sorted(set(line_numbers))
        if quiet:
            verified_message = "" if is_verification_disabled else "verified " if issue[
                "isSecretVerified"] else "unverified "
            message = LogColors.FAIL + f'[ISSUE]\tFound {verified_message}hardcoded {issue["title"]} at {issue["filePath"]} in line {",".join(line_numbers)}' + LogColors.ENDC
            if show_commit_id:
                message += f" for commit id {issue['commitId']}"
            print(message)
        else:
            table_data.append(generate_table_row(issue, show_commit_id, is_verification_disabled))

    if len(table_data) > 0:
        print(tabulate(table_data, headers="keys", tablefmt="psql"))


def generate_table_row(issue, show_commit_id, is_verification_disabled):
    line_numbers = [str(line)
                    for patch in issue["detectedSecret"]["patches"].values()
                    for line in patch["lines"]]
    line_numbers = sorted(set(line_numbers))
    verification_color = LogColors.FAIL if issue["isSecretVerified"] else LogColors.WARNING
    verification_message = str(issue["isSecretVerified"])
    if is_verification_disabled:
        verification_color = LogColors.BOLD
        verification_message = "Unknown"
    severity_color = get_severity_color(issue["severity"])

    required_width = get_wrapping_length(5)
    table_data = {
        "Title": wrap_text(issue["title"], required_width),
        "Severity": wrap_text(severity_color + issue["severity"] + LogColors.ENDC, required_width),
        "Verified": wrap_text(verification_color + verification_message + LogColors.ENDC, required_width),
        "File": wrap_text(issue["filePath"], required_width),
        "Line(s)": wrap_text(",".join(line_numbers), required_width),
    }
    if show_commit_id:
        if "commitId" in issue:
            table_data["Commit Id"] = issue["commitId"]
        else:
            table_data["Commit Id"] = "-"
    return table_data


def send_result_to_sentinelone(args, results, global_config_data):
    if not args.publish_result:
        return

    if len(results) == 0:
        return

    if args.mask_secret:
        LOGGER.warning(
            "Failed to publish results to SentinelOne CNS! Please remove --mask-secret flag to publish scan results.")
        return

    to_send = {
        "scanType": CodeTypeSubParser.SECRET,
        "issues": results,
        "repositoryFullName": args.repo_full_name,
        "repoUrl": args.repo_url,
        "provider": args.provider
    }

    management_console_url = global_config_data["management_console_url"]
    api_token = global_config_data["service_user_api_token"]
    url = management_console_url + PUBLISH_ISSUES_API
    query_params = {
        "scopeType": global_config_data["scope_type"],
        "scopeIds": global_config_data["scope_id"]
    }
    make_request(HttpMethod.POST, url, api_token, query_params, to_send)
    LOGGER.info("Successfully published secret issues to SentinelOne CNS.")


def save_issues_on_file(args, filtered_issues, global_config_data):
    output_file, output_format = get_output_file_and_format(args)
    if output_format == OUTPUT_FORMAT.SARIF:
        filtered_issues = convert_issues_to_sarif(filtered_issues)
    print_output_on_file(filtered_issues, output_file, output_format)


def convert_issues_to_sarif(issues):
    rules = []
    results = []
    sarif_result = get_sarif_payload("SentinelOne CNS Secret Detector")

    for issue in issues:
        rule, result = get_sarif_rule_and_result(issue)
        rules.append(rule)
        results.append(result)
    sarif_result["runs"][0]["results"] = results
    sarif_result["runs"][0]["tool"]["driver"]["rules"] = rules
    return sarif_result


def get_sarif_rule_and_result(issue):
    title = issue.get("title", "")
    full_description = issue.get("description", "")
    help_uri = issue.get("infoLink", "")
    severity = issue.get("severity", "LOW")
    file_path = issue.get("filePath", "")
    verified = issue.get("isSecretVerified", False)
    line = issue.get("detectedSecret", {}).get("primaryComponentLine", 0)

    return {
        "id": title,
        "name": title,
        "fullDescription": {
            "text": full_description
        },
        **({"helpUri": help_uri} if help_uri is not None and len(help_uri) != 0 else {}),
        "properties": {
            "security-severity": SEVERITY_MAP[severity]
        },
        "help": {
            "text": f"Severity: {severity}\nVerified: {verified}\nFile: {file_path}\nLine: {line}\n",
            "markdown": f'| Severity | Verified | File | Line |\n| --- | --- | --- | --- |\n| {severity} | {verified} | {file_path} | {line}|\n'
        }
    }, {
        "ruleId": title,
        "message": {
            "text": f"Hardcoded {title} found",
        },
        "locations": [{
            "physicalLocation": {
                "artifactLocation": {
                    "uri": file_path
                },
                "region": {
                    "startLine": line,
                }
            }
        }]
    }
