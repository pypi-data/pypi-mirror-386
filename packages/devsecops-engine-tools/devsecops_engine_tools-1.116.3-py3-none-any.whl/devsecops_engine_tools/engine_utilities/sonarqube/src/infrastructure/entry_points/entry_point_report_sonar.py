from devsecops_engine_tools.engine_utilities.sonarqube.src.domain.usecases.report_sonar import (
    ReportSonar,
)
from devsecops_engine_tools.engine_core.src.domain.usecases.metrics_manager import (
    MetricsManager,
)
import re
from devsecops_engine_tools.engine_utilities.utils.logger_info import MyLogger
from devsecops_engine_tools.engine_utilities import settings

logger = MyLogger.__call__(**settings.SETTING_LOGGER).get_logger()


def init_report_sonar(
    vulnerability_management_gateway,
    secrets_manager_gateway,
    devops_platform_gateway,
    remote_config_source_gateway,
    sonar_gateway,
    metrics_manager_gateway,
    args,
):
    config_tool = remote_config_source_gateway.get_remote_config(
        args["remote_config_repo"], "/engine_core/ConfigTool.json", args["remote_config_branch"]
    )
    report_config_tool = remote_config_source_gateway.get_remote_config(
        args["remote_config_repo"], "/engine_integrations/report_sonar/ConfigTool.json", args["remote_config_branch"]
    )
    excluded_pipelines = remote_config_source_gateway.get_remote_config(
        args["remote_config_repo"], "/engine_integrations/report_sonar/Exclusions.json", args["remote_config_branch"]
    )

    pipeline_name = devops_platform_gateway.get_variable("pipeline_name")
    branch = devops_platform_gateway.get_variable("branch_tag")

    is_valid_pipeline = pipeline_name not in excluded_pipelines and not any(
        [
            re.match(
                pattern,
                pipeline_name,
                re.IGNORECASE
            ) for pattern in
            [report_config_tool["IGNORE_SEARCH_PATTERN"]] +
            list(excluded_pipelines.get("BY_PATTERN_SEARCH", {}).keys())
        ]
    )
    
    is_valid_branch = any(
        target_branch in str(branch).split("/")
        for target_branch in report_config_tool["TARGET_BRANCHES"]
    )

    is_enabled = config_tool["REPORT_SONAR"]["ENABLED"]

    if is_enabled and is_valid_pipeline and is_valid_branch:
        input_core = ReportSonar(
            vulnerability_management_gateway,
            secrets_manager_gateway,
            devops_platform_gateway,
            remote_config_source_gateway,
            sonar_gateway,
        ).process(args)

        if args["send_metrics"] == "true":
            MetricsManager(devops_platform_gateway, metrics_manager_gateway).process(
                config_tool, input_core, {"module": "report_sonar"}, ""
            )
    else:
        if not is_enabled:
            message = "DevSecOps Engine Tool - {0} in maintenance...".format(
                "report_sonar"
            )
        else:
            message = "Tool skipped by DevSecOps policy"

        print(
            devops_platform_gateway.message("warning", message),
        )
