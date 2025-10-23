from devsecops_engine_tools.engine_sca.engine_container.src.domain.usecases.container_sca_scan import (
    ContainerScaScan,
)
from devsecops_engine_tools.engine_sca.engine_container.src.domain.usecases.handle_remote_config_patterns import (
    HandleRemoteConfigPatterns,
)
from devsecops_engine_tools.engine_sca.engine_container.src.domain.usecases.set_input_core import (
    SetInputCore,
)
from devsecops_engine_tools.engine_utilities.utils.logger_info import MyLogger
from devsecops_engine_tools.engine_utilities import settings
import re

logger = MyLogger.__call__(**settings.SETTING_LOGGER).get_logger()


def init_engine_sca_rm(
    tool_run,
    tool_remote,
    remote_config_source_gateway,
    tool_images,
    tool_deseralizator,
    dict_args,
    secret_tool,
    tool,
):
    remote_config = remote_config_source_gateway.get_remote_config(
        dict_args["remote_config_repo"],
        "engine_sca/engine_container/ConfigTool.json",
        dict_args["remote_config_branch"],
    )
    exclusions = remote_config_source_gateway.get_remote_config(
        dict_args["remote_config_repo"],
        "engine_sca/engine_container/Exclusions.json",
        dict_args["remote_config_branch"],
    )
    pipeline_name = tool_remote.get_variable("pipeline_name")
    regex_clean = remote_config.get("REGEX_CLEAN_END_PIPELINE_NAME")
    if regex_clean:
        pattern = re.compile(regex_clean)
        match = pattern.match(pipeline_name)
        if match:
            pipeline_name= match.group(1)
            
    handle_remote_config_patterns = HandleRemoteConfigPatterns(
        remote_config, exclusions, pipeline_name
    )
    skip_flag = handle_remote_config_patterns.skip_from_exclusion()
    scan_flag = handle_remote_config_patterns.ignore_analysis_pattern()
    branch = tool_remote.get_variable("branch_tag")
    stage = tool_remote.get_variable("stage")
    image_to_scan = dict_args["image_to_scan"]
    image_scanned = None
    base_image = None
    sbom_components = None
    deseralized = []
    input_core = SetInputCore(remote_config, exclusions, pipeline_name, tool, stage)
    if scan_flag and not (skip_flag):
        container_sca_scan = ContainerScaScan(
            tool_run,
            remote_config,
            tool_images,
            tool_deseralizator,
            branch,
            secret_tool,
            dict_args["token_engine_container"],
            image_to_scan,
            exclusions,
            pipeline_name,
            context=dict_args["context"],
            docker_address=dict_args["docker_address"],
        )
        image_scanned, base_image, sbom_components = container_sca_scan.process()
        if image_scanned:
            deseralized = container_sca_scan.deseralizator(image_scanned)
    else:
        print("Tool skipped by DevSecOps policy")
        dict_args["send_metrics"] = "false"
        dict_args["use_vulnerability_management"] = "false"

    core_input = input_core.set_input_core(image_scanned, base_image)

    return deseralized, core_input, sbom_components
