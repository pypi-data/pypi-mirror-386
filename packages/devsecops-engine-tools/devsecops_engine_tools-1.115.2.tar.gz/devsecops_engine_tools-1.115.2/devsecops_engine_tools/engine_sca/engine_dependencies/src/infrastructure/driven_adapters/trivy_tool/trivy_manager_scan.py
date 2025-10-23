from devsecops_engine_tools.engine_sca.engine_dependencies.src.domain.model.gateways.tool_gateway import (
    ToolGateway,
)
from devsecops_engine_tools.engine_sca.engine_dependencies.src.domain.model.context_dependencies import (
    ContextDependencies,
)
from devsecops_engine_tools.engine_utilities.trivy_utils.infrastructure.driven_adapters.trivy_manager_scan_utils import (
    TrivyManagerScanUtils
)
import os
import json
import subprocess
from dataclasses import asdict
from devsecops_engine_tools.engine_utilities.utils.logger_info import MyLogger
from devsecops_engine_tools.engine_utilities import settings

logger = MyLogger.__call__(**settings.SETTING_LOGGER).get_logger()


class TrivyScanSBOM(ToolGateway):
    def run_tool_dependencies_sca(
        self,
        remote_config,
        dict_args,
        exclusion,
        pipeline_name,
        to_scan,
        secret_tool,
        token_engine_dependencies,
        **kwargs,
    ):
        trivy_version = remote_config["TRIVY"]["CLI_VERSION"]
        command_prefix = TrivyManagerScanUtils().identify_os_and_install(trivy_version)
        sbom = f"{pipeline_name}_SBOM.json"

        if not command_prefix:
            return None

        if not os.path.exists(sbom):
            raise FileNotFoundError("SBOM file not found, enable SBOM generation to scan with Trivy.")

        dependencies_scanned = self._scan_dependencies_sbom(command_prefix, sbom)

        return dependencies_scanned

    def get_dependencies_context_from_results(
            self, 
            path_file_results, 
            remote_config
    ):
        dependencies_container_list = []

        with open(path_file_results, "rb") as file:
            image_object = file.read()
            json_data = json.loads(image_object)

        results = json_data.get("Results", [])

        for result in results:
            vulnerabilities = result.get("Vulnerabilities", [])
            for vul in vulnerabilities:
                context_container = ContextDependencies(
                    cve_id=[vul.get("VulnerabilityID", "unknown")],
                    severity=vul.get("Severity", "unknown").lower(),
                    component=vul.get("PkgID", "unknown"),
                    package_name=vul.get("PkgName", "unknown"),
                    installed_version=vul.get("InstalledVersion", "unknown"),
                    fixed_version=vul.get("FixedVersion", "unknown").split(", "),
                    impact_paths=[],
                    description=vul.get("Description", "unknown").replace("\n", ""),
                    references=vul.get("References", "unknown"),
                    source_tool="Trivy"
                )
                dependencies_container_list.append(context_container)

        print("===== BEGIN CONTEXT OUTPUT =====")
        print(
            json.dumps(
                {
                    "dependencies_context": [
                        asdict(context) for context in dependencies_container_list
                    ]
                },
                indent=2,
            )
        )
        print("===== END CONTEXT OUTPUT =====")

    def _scan_dependencies_sbom(self, command_prefix, sbom_path):
        result_file = f"{sbom_path.replace('.json', '')}_scan_result.json"

        command = [
            command_prefix,
            "sbom",
            sbom_path,
            "-f",
            "json",
            "--scanners",
            "vuln",
            "-o",
            result_file,
        ]

        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"The SBOM {sbom_path} was scanned")

            return result_file

        except Exception as e:
            logger.error(f"Error during SBOM scan of {sbom_path}: {e}")
