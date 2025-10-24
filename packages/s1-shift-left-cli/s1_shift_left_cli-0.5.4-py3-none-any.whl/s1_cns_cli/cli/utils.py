import base64
import csv
import hashlib
import json
import logging
import os.path
import platform
import shutil
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError

import requests
from alive_progress import alive_bar
from sentry_sdk import capture_exception, configure_scope

from s1_cns_cli import version
from s1_cns_cli.cli.registry import CONFIG_FILE_NAME, CodeTypeSubParser, IacConfigData, HttpMethod, \
    Severity, PIP_COMMAND, PYPI_URL, GET_PRE_SIGNED_URL_API, BINARY_LIST, DEFAULT_TIMEOUT, LogColors, \
    DEFAULT_SENTINELONE_CNS_DIR, SENTINELONE_CNS_LOCAL_CONFIG_PATH, PlatformNotSupportedException, \
    HttpConnectionException, \
    RequestTimeoutException, \
    SENTRY_TAGS, DownloadException, OUTPUT_FORMAT, UnauthorizedUserException, BINARY_DIR, SEVERITIES, NotFoundException, \
    SEVERITY_TO_NUMBER, BadRequestException, ServiceNotAvailableException, AccessDeniedException, UnprocessableEntity

LOGGER = logging.getLogger("cli")


# Custom formatter class
class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.ERROR: LogColors.FAIL + '%(levelname)s\t%(message)s' + LogColors.ENDC,
        logging.WARNING: LogColors.WARNING + '%(levelname)s\t%(message)s' + LogColors.ENDC,
        logging.INFO: '%(levelname)s\t%(message)s',
        logging.DEBUG: '%(levelname)s\t%(message)s',
        logging.CRITICAL: LogColors.FAIL + '%(levelname)s\t%(message)s' + LogColors.ENDC,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def initialize_logger(name, level):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter()
    handler.setFormatter(formatter)
    logger.propagate = False
    logger.addHandler(handler)


def get_os_and_architecture():
    operating_system = platform.system().lower()
    arch = platform.machine().lower()
    return operating_system, arch


def handle_error(response):
    if "error" in response:
        return response["error"]
    elif "errors" in response:
        return ", ".join(err["detail"] for err in response["errors"])
    elif "detail" in response:
        return response["detail"]
    elif "message" in response:
        return response["message"]
    else:
        return "something went wrong"



def make_request(method, url, service_user_api_token, query_params=None, data=None):
    try:
        request_headers = generate_headers(service_user_api_token)
        response = requests.request(
            method=method,
            url=url,
            data=json.dumps(data) if data is not None else "",
            headers=request_headers,
            params=query_params,
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code == 400:
            raise BadRequestException(handle_error(response.json()))
        if response.status_code == 401:
            raise UnauthorizedUserException(handle_error(response.json()))
        if response.status_code == 403:
            raise AccessDeniedException(handle_error(response.json()))
        if response.status_code == 404:
            raise NotFoundException(handle_error(response.json()))
        if response.status_code == 422:
            raise UnprocessableEntity(handle_error(response.json()))
        if response.status_code == 501:
            raise PlatformNotSupportedException(f"Platform {request_headers['x-runtime-arch']} is not supported.")
        if response.status_code == 503:
            raise ServiceNotAvailableException("Service is temporarily unavailable. Please try again later")
        if response.status_code >= 400 and response.status_code < 600:
            raise Exception(handle_error(response.json()))
        return response
    except requests.ConnectionError as e:
        raise HttpConnectionException(f"Unable to send request to url: {url} due to connection error")
    except requests.Timeout as e:
        raise RequestTimeoutException(f"Request timed out for url:{url}")


def delete_all_cache(cache_directory):
    try:
        if os.path.exists(cache_directory):
            shutil.rmtree(cache_directory, ignore_errors=True)
            shutil.rmtree(os.path.join(os.path.expanduser('~'), DEFAULT_SENTINELONE_CNS_DIR), ignore_errors=True)
    except Exception as e:
        print(e)


def read_json_file(file_path):
    try:
        if os.path.getsize(file_path) > 0:
            with open(file_path) as infile:
                return json.load(infile)
    except JSONDecodeError as e:
        LOGGER.error(str(e))


def read_from_file(file_path):
    try:
        if os.path.getsize(file_path) > 0:
            with open(file_path) as infile:
                return infile.read()
    except FileNotFoundError as e:
        LOGGER.error(str(e))


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def write_json_to_file(file_path, data):
    with open(file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4, cls=SetEncoder, default=str)


def write_csv_to_file(file_path, data):
    if len(data) <= 0:
        return
    field_names = data[0].keys()
    with open(file_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def generate_headers(service_user_api_token):
    version = get_version()
    current_os, arch = get_os_and_architecture()
    return {
        'Content-Type': "application/json",
        'Authorization': f'Bearer {service_user_api_token}',
        'user-agent': f's1-cns-cli-{version}',
        'x-runtime-arch': f'{current_os}_{arch}'
    }


def check_if_paths_exist(paths):
    for path in paths:
        if not os.path.exists(path):
            return False
    return True


def add_global_config_file(args):
    if not os.path.exists(args.cache_directory):
        os.makedirs(args.cache_directory)

    global_config_file_path = os.path.join(args.cache_directory, CONFIG_FILE_NAME)
    global_config = generate_custom_config(args)

    if os.path.exists(global_config_file_path):
        os.remove(global_config_file_path)
    write_json_to_file(global_config_file_path, global_config)

    local_config_dir = get_home_path(DEFAULT_SENTINELONE_CNS_DIR)
    if not os.path.exists(local_config_dir):
        os.makedirs(local_config_dir)
    write_json_to_file(get_home_path(SENTINELONE_CNS_LOCAL_CONFIG_PATH), {"cache_directory": args.cache_directory})


def add_iac_config_file(cache_directory, admin_configs, last_refreshed_time=None):
    iac_cache_dir = os.path.join(cache_directory, CodeTypeSubParser.IAC)
    iac_config_file_path = os.path.join(iac_cache_dir, CONFIG_FILE_NAME)
    iac_config_data = admin_configs[CodeTypeSubParser.IAC]
    iac_config_data[IacConfigData.LAST_REFRESHED_AT] = last_refreshed_time

    if not os.path.exists(iac_cache_dir):
        os.makedirs(iac_cache_dir)
    if os.path.exists(iac_config_file_path):
        os.remove(iac_config_file_path)
    write_json_to_file(iac_config_file_path, iac_config_data)


def add_secret_config_file(cache_directory, admin_configs):
    secret_cache_dir = os.path.join(cache_directory, CodeTypeSubParser.SECRET)
    secret_config_file_path = os.path.join(secret_cache_dir, CONFIG_FILE_NAME)
    secret_config_data = admin_configs[CodeTypeSubParser.SECRET]

    if not os.path.exists(secret_cache_dir):
        os.makedirs(secret_cache_dir)
    if os.path.exists(secret_config_file_path):
        os.remove(secret_config_file_path)
    write_json_to_file(secret_config_file_path, secret_config_data)


def add_vulnerability_config_file(cache_directory, admin_configs):
    vulnerability_cache_dir = os.path.join(cache_directory, CodeTypeSubParser.VULN)
    vulnerability_config_file_path = os.path.join(vulnerability_cache_dir, CONFIG_FILE_NAME)
    vulnerability_config_data = admin_configs[CodeTypeSubParser.VULN]

    if not os.path.exists(vulnerability_cache_dir):
        os.makedirs(vulnerability_cache_dir)
    if os.path.exists(vulnerability_config_file_path):
        os.remove(vulnerability_config_file_path)
    write_json_to_file(vulnerability_config_file_path, vulnerability_config_data)


def invalidate_cache(cache_directory):
    global_config_file_path = get_config_path(cache_directory)
    iac_config_file_path = get_config_path(cache_directory, CodeTypeSubParser.IAC)

    if os.path.exists(global_config_file_path):
        global_config_data = read_json_file(global_config_file_path)
        global_config_data["version"] = 0
        write_json_to_file(global_config_file_path, global_config_data)

    if os.path.exists(iac_config_file_path):
        iac_config_data = read_json_file(iac_config_file_path)
        iac_config_data[IacConfigData.LAST_REFRESHED_AT] = None
        write_json_to_file(iac_config_file_path, iac_config_data)


def generate_custom_config(args):
    return {
        "service_user_api_token": args.service_user_api_token,
        "management_console_url": args.management_console_url,
        "scope_type": args.scope_type,
        "scope_id": args.scope_id,
        "cache_directory": args.cache_directory,
        "on_crash_exit_code": args.on_crash_exit_code,
        "workers_count": args.workers_count,
        "iac_last_refreshed_at": None,
        "tag": args.tag
    }


def get_config_path(cache_directory, provider=""):
    if provider != "":
        return os.path.join(cache_directory, provider, CONFIG_FILE_NAME)
    return os.path.join(cache_directory, CONFIG_FILE_NAME)


def get_cache_directory():
    local_config_path = get_home_path(SENTINELONE_CNS_LOCAL_CONFIG_PATH)
    if os.path.exists(local_config_path):
        local_config = read_json_file(local_config_path)
        return local_config["cache_directory"]
    return ""


def check_for_cli_updates(current_version):
    response = requests.get(f'{PYPI_URL}')
    if response.status_code != 200:
        LOGGER.error(f"[PyPi] Failed to check for updates, err: {response.text} {PYPI_URL}")
        return
    latest_version = response.json()['info']['version']
    if current_version < latest_version:
        LOGGER.debug(PIP_COMMAND)
        LOGGER.debug(f"Update available, updating to latest version: {latest_version}")
        subprocess.call(PIP_COMMAND)
    else:
        LOGGER.debug("No updates available")


def calculate_sha256(file_path):
    hash_object = hashlib.sha256()
    try:
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                hash_object.update(chunk)
        return hash_object.hexdigest()
    except IOError as e:
        raise Exception(f"File could not be opened: {e}")


def download_file(url, destination):
    with requests.get(url, stream=True) as r:
        if r.status_code != 200:
            raise DownloadException(f"Failed to download dependencies, err: {r.text}", r.url,
                                    os.path.basename(destination))
        with open(destination, 'wb') as f:
            # Download the file in chunks (8192 => 8kb)
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        os.chmod(destination, 0o755)
        # todo: download checksum file from s3 and then verify
        # expected_sha_sum = r.headers.get("x-amz-meta-checksum")
        # current_sha_sum = calculate_sha256(destination)
        # if current_sha_sum != expected_sha_sum:
        #     raise Exception("Failed to configure SentinelOne CNS CLI, please try again.")


def get_presigned_urls(cache, binary_list):
    data = {}
    for binary in binary_list:
        data[binary] = True
    global_config_file_path = get_config_path(cache)
    global_config_data = read_json_file(global_config_file_path)

    management_console_url = global_config_data["management_console_url"]
    query_params = {
        "scopeType": global_config_data["scope_type"],
        "scopeIds": global_config_data["scope_id"]
    }
    response = make_request(HttpMethod.POST, management_console_url + GET_PRE_SIGNED_URL_API, global_config_data["service_user_api_token"], query_params,
                            data)
    if response.status_code != 200:
        LOGGER.error(f"Failed to get pre-signed urls, err: {response.text}")
        return {}
    else:
        return response.json()["data"]


def download(version, binary, url, cache):
    download_path = os.path.join(cache, BINARY_DIR)
    if not os.path.exists(download_path):
        try:
            os.mkdir(download_path)
        except FileExistsError:
            pass

    version_path = os.path.join(download_path, version)
    if not os.path.exists(version_path):
        try:
            os.mkdir(version_path)
        except FileExistsError:
            pass

    file_path = os.path.join(version_path, binary)
    global_config_file_path = get_config_path(cache)
    global_config_data = read_json_file(global_config_file_path)
    download_file(url, file_path)
    LOGGER.debug(f"Successfully downloaded {binary} for version: {version}")


def get_exit_code_on_crash(cache_directory):
    try:
        if os.path.exists(get_config_path(cache_directory)):
            return read_json_file(get_config_path(cache_directory))["on_crash_exit_code"]
        return 1
    except Exception as e:
        logging.getLogger("cli").exception("Exception while get_exit_code_on_crash", e)
        return 1


# upsert_s1_cns_cli: will check that if any new s1-cns-cli version is available at PyPi, it will upgrade now
# and on next run it will download new binaries and run updated s1-cns-cli with updated binaries
def upsert_s1_cns_cli(cache_directory):
    current_version = get_version()
    paths = []
    for binary in BINARY_LIST:
        paths.append(os.path.join(cache_directory, BINARY_DIR, current_version, binary))

    download_required = not check_if_paths_exist(paths)
    if download_required:
        # deleting bin, so that when new version is available we only keep the latest version
        bin_path = os.path.join(cache_directory, BINARY_DIR)
        if os.path.exists(bin_path):
            shutil.rmtree(bin_path, ignore_errors=True)

        signed_urls = get_presigned_urls(cache_directory, BINARY_LIST)
        LOGGER.debug("Downloading required dependencies...")
        with ThreadPoolExecutor() as executor:
            futures = []
            for binary, signed_url in signed_urls.items():
                futures.append(executor.submit(download, current_version, binary, signed_url, cache_directory))
            with alive_bar(len(futures), title='Downloading Runtime Dependencies', bar='blocks',
                           spinner='waves') as bar:
                for future in futures:
                    future.result()
                    bar()
        LOGGER.debug("Successfully downloaded dependencies!")


def get_home_path(directory):
    return os.path.join(os.path.expanduser("~"), directory)


def get_version():
    return version.version


def add_sentry_tags(scope, cache_directory):
    scope.set_tag("cli_version", version.version)
    system_os, arch = get_os_and_architecture()
    scope.set_tag("os", system_os)
    scope.set_tag("arch", arch)
    if cache_directory != "":
        global_config_data = read_json_file(os.path.join(cache_directory, CONFIG_FILE_NAME))
        for tag in SENTRY_TAGS:
            if tag in global_config_data:
                scope.set_tag(tag, global_config_data[tag])


def send_exception_to_sentry(e, cache_directory):
    try:
        with configure_scope() as scope:
            add_sentry_tags(scope, cache_directory)
            capture_exception(e)
    except Exception as e:
        LOGGER.debug(e)


def print_output_on_file(results, output_file, output_format):
    if output_file != "":
        if output_format == OUTPUT_FORMAT.JSON or output_format == OUTPUT_FORMAT.SARIF:
            write_json_to_file(output_file, results)
        elif output_format == OUTPUT_FORMAT.CSV:
            write_csv_to_file(output_file, results)
        else:
            LOGGER.warning("Invalid output format. Please update output format using s1-cns-cli config --output-format <JSON/CSV>")
            return
        LOGGER.info(f"Result generated successfully at {output_file}")


def get_output_file_and_format(args):
    output_file = ""
    output_format = None

    if len(args.global_output_file) > 0:
        output_file = args.global_output_file
    if len(args.output_file) > 0:
        output_file = args.output_file

    if args.global_output_format is not None:
        output_format = args.global_output_format
    if args.output_format is not None:
        output_format = args.output_format

    # checking if output format is passed in command but output file is not passed
    if output_format is not None and len(output_format) > 0 and len(output_file) == 0:
        LOGGER.warning("Output format given without output file. Please provide"
                       " --output-file flag to get result on desired file.")

    # setting default behaviour for output format as JSON when output file path is given but output format is skipped
    if len(output_file) > 0 and (output_format is None or len(output_format) == 0):
        output_format = OUTPUT_FORMAT.JSON

    return output_file, output_format


def get_severity_color(severity):
    if severity == Severity.CRITICAL:
        return LogColors.FAIL
    elif severity == Severity.HIGH:
        return LogColors.OKORANGE
    elif severity == Severity.MEDIUM:
        return LogColors.WARNING
    else:
        return LogColors.BOLD


def wrap_text(text, width):
    if width == 0:
        return text
    return "\n".join(textwrap.wrap(text, width))


def get_wrapping_length(total_columns):
    try:
        terminal_width = os.get_terminal_size().columns
        return terminal_width // total_columns
    except OSError:
        # returning 0 when shell is not available
        return 0


def get_priority(obj):
    obj_severity = obj.get("severity", "NA")
    return SEVERITIES.get(obj_severity.upper(), 5)


def get_sarif_payload(name):
    return {
        "version": "2.1.0",
        "$schema": "https://github.com/oasis-tcs/sarif-spec/blob/main/Documents/CommitteeSpecifications/2.1.0/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": name,
                        "organization": "SentinelOne CNS",
                        "rules": []
                    }
                },
                "results": []
            }
        ]
    }

def get_actionable_and_non_actionable(issues: list, severity: str) -> (list, list):
    idx = find_last_idx_for_severity(issues, severity)
    if idx == -1:
        return ([], issues)
    actionable_issues = issues[0: idx + 1]
    non_actionable_issues = issues[idx + 1:]
    return (actionable_issues, non_actionable_issues)

def find_last_idx_for_severity(issues: list, severity: str) -> int:
    severity = severity.upper()

    first_issue_severity = issues[0]["severity"].upper()
    last_issue_severity = issues[-1]["severity"].upper()

    # edge case when all the issues have higher severity
    if SEVERITY_TO_NUMBER[last_issue_severity] < SEVERITY_TO_NUMBER[severity]:
        return len(issues) - 1

    # edge case when all the issues have lower severity
    if SEVERITY_TO_NUMBER[first_issue_severity] > SEVERITY_TO_NUMBER[severity]:
        return -1

    lo = 0
    hi = len(issues) - 1
    while lo < hi:
        mid = lo + (hi - lo + 1) // 2
        mid_issue_severity = issues[mid]["severity"].upper()
        val = SEVERITY_TO_NUMBER[mid_issue_severity]
        if val <= SEVERITY_TO_NUMBER[severity]:
            lo = mid
        else:
            hi = mid - 1

    return lo

def decode_base_64(encoded_string):
    decoded_bytes = base64.b64decode(encoded_string)
    return decoded_bytes.decode("utf-8")

def write_to_file(path, content):
    with open(path, 'w') as file:
        file.write(content)