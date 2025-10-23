from devsecops_engine_tools.engine_sca.engine_dependencies.src.domain.model.gateways.tool_gateway import (
    ToolGateway,
)
from devsecops_engine_tools.engine_sca.engine_dependencies.src.infrastructure.driven_adapters.dependency_check.dependency_check_deserialize import (
    DependencyCheckDeserialize,
)
from devsecops_engine_tools.engine_sca.engine_dependencies.src.domain.model.context_dependencies import (
    ContextDependencies,
)

import requests
import subprocess
import os
import platform
import shutil
from dataclasses import asdict
import json

from devsecops_engine_tools.engine_utilities.utils.utils import Utils
from devsecops_engine_tools.engine_sca.engine_dependencies.src.infrastructure.helpers.get_artifacts import (
    GetArtifacts,
)
from devsecops_engine_tools.engine_utilities.utils.logger_info import MyLogger
from devsecops_engine_tools.engine_utilities import settings

logger = MyLogger.__call__(**settings.SETTING_LOGGER).get_logger()


class DependencyCheckTool(ToolGateway):
    def __init__(self):
        self.download_tool_called = False

    def download_tool(self, cli_version):
        try:
            self.download_tool_called = True
            url = f"https://github.com/dependency-check/DependencyCheck/releases/download/v{cli_version}/dependency-check-{cli_version}-release.zip"
            response = requests.get(url, allow_redirects=True)
            home_directory = os.path.expanduser("~")
            zip_name = os.path.join(
                home_directory, f"dependency_check_{cli_version}.zip"
            )
            with open(zip_name, "wb") as f:
                f.write(response.content)

            utils = Utils()
            utils.unzip_file(zip_name, home_directory)
        except Exception as ex:
            logger.error(f"An error ocurred downloading dependency-check {ex}")

    def install_tool(self, cli_version, is_windows=False):
        command_prefix = "dependency-check.bat" if is_windows else "dependency-check.sh"

        installed = shutil.which(command_prefix)
        if installed:
            return command_prefix

        home_directory = os.path.expanduser("~")
        bin_route = os.path.join(
            home_directory, f"dependency-check/bin/{command_prefix}"
        )

        if shutil.which(bin_route):
            return bin_route

        self.download_tool(cli_version)

        try:
            if os.path.exists(bin_route):
                if not is_windows:
                    subprocess.run(["chmod", "+x", bin_route], check=True)
                return bin_route
        except Exception as e:
            logger.error(f"Error installing OWASP dependency check: {e}")
            return None

    def scan_dependencies(self, command_prefix, file_to_scan, token):
        try:
            command = [
                command_prefix,
                "--format",
                "XML",
                "--scan",
                file_to_scan,
            ]

            if token:
                command.extend([
                    "--nvdApiKey",
                    token
                ])
            
            if not self.download_tool_called:
                command.append("--noupdate")

            result = subprocess.run(command, capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing OWASP dependency check scan: {e.stderr}")

    def select_operative_system(self, cli_version):
        os_platform = platform.system()

        if os_platform in ["Linux", "Darwin"]:
            return self.install_tool(cli_version, is_windows=False)
        elif os_platform == "Windows":
            return self.install_tool(cli_version, is_windows=True)
        else:
            logger.warning(f"{os_platform} is not supported.")
            return None

    def search_result(self):
        try:
            file_result = os.path.join(os.getcwd(), "dependency-check-report.xml")
            return file_result
        except Exception as ex:
            logger.error(f"An error ocurred search dependency-check results {ex}")
            return None

    def is_java_installed(self):
        return shutil.which("java") is not None

    def run_tool_dependencies_sca(
        self,
        remote_config,
        dict_args,
        exclusion,
        pipeline_name,
        to_scan,
        token,
        token_engine_dependencies,
        **kwargs,
    ):
        if not self.is_java_installed():
            logger.error(
                "Java is not installed, please install it to run dependency check"
            )
            return None

        cli_version = remote_config["DEPENDENCY_CHECK"]["CLI_VERSION"]

        get_artifacts = GetArtifacts()

        pattern = get_artifacts.excluded_files(
            remote_config, pipeline_name, exclusion, "DEPENDENCY_CHECK"
        )
        ignore_files = remote_config.get("IGNORE_FILES", [])
        to_scan = get_artifacts.find_artifacts(
            to_scan, pattern, remote_config["DEPENDENCY_CHECK"]["PACKAGES_TO_SCAN"], ignore_files
        )

        if not to_scan:
            return None

        command_prefix = self.select_operative_system(cli_version)
        self.scan_dependencies(command_prefix, to_scan, token_engine_dependencies)
        return self.search_result()

    def get_dependencies_context_from_results(self, path_file_results, remote_config):
        deserializer = DependencyCheckDeserialize()
        dependencies, namespace = deserializer.filter_vulnerabilities_by_confidence(path_file_results, remote_config)
        context_dependencies_list = []

        for dependency in dependencies:
            vulnerabilities_node = dependency.find('ns:vulnerabilities', namespace)
            if vulnerabilities_node:
                vulnerabilities = vulnerabilities_node.findall('ns:vulnerability', namespace)
                for vulnerability in vulnerabilities:
                    data = deserializer.extract_common_vuln_data(vulnerability, dependency, namespace)
                    references = deserializer.extract_references(vulnerability, namespace)

                    context = ContextDependencies(
                        cve_id=[data["id"]],
                        severity=data["severity"],
                        component=data["where"],
                        package_name=data["where"].split(":")[0] if data["where"] else "",
                        installed_version=data["where"].split(":")[2].lower() if len(data["where"].split(":")) == 3 else data["where"].split(":")[1].lower(),
                        fixed_version=[data["fix"]] if data["fix"] else [],
                        impact_paths=[],
                        description=data["description"],
                        references=references,
                        source_tool="Dependency Check"
                    )
                    context_dependencies_list.append(context)

        print("===== BEGIN CONTEXT OUTPUT =====")
        print(
            json.dumps(
                {
                    "dependencies_context": [
                        asdict(context) for context in context_dependencies_list
                    ]
                },
                indent=4,
            )
        )
        print("===== END CONTEXT OUTPUT =====")
        