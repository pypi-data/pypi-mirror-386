from devsecops_engine_tools.engine_sca.engine_container.src.domain.model.gateways.tool_gateway import (
    ToolGateway,
)
from devsecops_engine_tools.engine_sca.engine_container.src.domain.model.gateways.images_gateway import (
    ImagesGateway,
)
from devsecops_engine_tools.engine_sca.engine_container.src.domain.model.gateways.deserealizator_gateway import (
    DeseralizatorGateway,
)

import os


class ContainerScaScan:
    def __init__(
        self,
        tool_run: ToolGateway,
        remote_config,
        tool_images: ImagesGateway,
        tool_deseralizator: DeseralizatorGateway,
        branch,
        secret_tool,
        token_engine_container,
        image_to_scan,
        exclusions,
        pipeline_name,
        context,
        docker_address,
    ):
        self.tool_run = tool_run
        self.remote_config = remote_config
        self.tool_images = tool_images
        self.tool_deseralizator = tool_deseralizator
        self.branch = branch
        self.secret_tool = secret_tool
        self.token_engine_container = token_engine_container
        self.image_to_scan = image_to_scan
        self.exclusions = exclusions
        self.pipeline_name = pipeline_name
        self.context = context
        self.docker_address = docker_address

    def _is_compressed_file(self, image_to_scan):
        """Check if the input is a compressed file (tar, tar.gz, etc.)"""
        return any(
            image_to_scan.lower().endswith(ext) 
            for ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz']
        )

    def process(self):
        """
        Process SCA scanning.

        Returns:
            string: file scanning results name.
        """
        base_image = None
        image_scanned = None
        sbom_components = None
        
        is_compressed_file = self._is_compressed_file(self.image_to_scan)
        
        if is_compressed_file:
            if not os.path.exists(self.image_to_scan):
                print(f"Compressed file not found: {self.image_to_scan}. Tool skipped.")
                return image_scanned, base_image, sbom_components
                
            matching_image = None
            image_name = self.image_to_scan
            print(f"Processing compressed file: {image_name}")
        else:
            matching_image = self._get_image(self.image_to_scan)
            if not matching_image:
                print(f"'Not image found for {self.image_to_scan}'. Tool skipped.")
                return image_scanned, base_image, sbom_components
                
            image_name = matching_image.tags[0]
            
            if self.remote_config["GET_IMAGE_BASE"]["ENABLED"]:
                base_image = self._get_base_image(matching_image)
            if self.remote_config["VALIDATE_BASE_IMAGE_DATE"][
                "ENABLED"
            ] and not self.exclusions.get(self.pipeline_name, {}).get(
                "VALIDATE_BASE_IMAGE_DATE"
            ):
                self._validate_base_image_date(
                    matching_image,
                    self.remote_config["VALIDATE_BASE_IMAGE_DATE"]["REFERENCE_IMAGE_DATE"],
                )
            if self.remote_config["BLACK_LIST_BASE_IMAGE"][
                "ENABLED"
            ] and not self.exclusions.get(self.pipeline_name, {}).get(
                "BLACK_LIST_BASE_IMAGE"
            ):
                self._validate_black_list_base_image(
                    base_image, self.remote_config["BLACK_LIST_BASE_IMAGE"]["BLACK_LIST"]
                )

        generate_sbom = self.remote_config["SBOM"]["ENABLED"] and any(
            branch in str(self.branch)
            for branch in self.remote_config["SBOM"]["BRANCH_FILTER"]
        )

        result_file = image_name.replace("/", "_").replace(".", "_") + "_scan_result.json"
        
        if not is_compressed_file and image_name in self._get_images_already_scanned():
            print(f"The image {image_name} has already been scanned previously.")
            return image_scanned, base_image, sbom_components
            
        image_scanned, sbom_components = self.tool_run.run_tool_container_sca(
            self.remote_config,
            self.secret_tool,
            self.token_engine_container,
            image_name,
            result_file,
            base_image,
            self.exclusions,
            generate_sbom,
            self.docker_address,
            is_compressed_file,
        )
        
        if not is_compressed_file:
            self._set_image_scanned(image_name)
            
        return image_scanned, base_image, sbom_components

    def deseralizator(self, image_scanned):
        """
        Process the results deserializer.

        Returns:
            list: Deserialized list of findings.
        """
        context_flag = self.context
        if context_flag == "true":
            self.tool_deseralizator.get_container_context_from_results(image_scanned)

        return self.tool_deseralizator.get_list_findings(image_scanned, module="engine_container")

    def _get_image(self, image_to_scan):
        """
        Process the list of images.

        Returns:
            list: List of processed images.
        """
        return self.tool_images.list_images(image_to_scan)

    def _get_base_image(self, matching_image):
        """
        Process the base image.

        Returns:
            String: base image.
        """
        return self.tool_images.get_base_image(matching_image, self.remote_config["GET_IMAGE_BASE"]["BASE_IMAGE_LABELS"]), self.remote_config["GET_IMAGE_BASE"].get("LABEL_KEYS", None)

    def _validate_base_image_date(self, matching_image, referenced_date):
        """
        Process the base image date validation.

        Returns:
            string: base image date.
        """
        return self.tool_images.validate_base_image_date(
            matching_image, 
            referenced_date, 
            self.remote_config["GET_IMAGE_BASE"]["BASE_IMAGE_LABELS"],
            self.remote_config["GET_IMAGE_BASE"].get("LABEL_KEYS")
        )

    def _validate_black_list_base_image(self, base_image, black_list):
        """
        Process the black list image base validation.

        Returns:
            string: blacklist.
        """
        if not base_image or not base_image[0]:
            return True
        return self.tool_images.validate_black_list_base_image(base_image[0][0], black_list)

    def _get_images_already_scanned(self):
        """
        Create images scanned file if it does not exist and get the images that have already been scanned.
        """
        scanned_images_file = os.path.join(os.getcwd(), "scanned_images.txt")
        if not os.path.exists(scanned_images_file):
            open(scanned_images_file, "w").close()
        with open(scanned_images_file, "r") as file:
            images_scanned = file.read().splitlines()
        return images_scanned

    def _set_image_scanned(self, result_file):
        """
        Write in scanned_images.txt the result file
        """
        with open("scanned_images.txt", "a") as file:
            file.write(result_file + "\n")
