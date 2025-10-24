from devsecops_engine_tools.engine_sca.engine_dependencies.src.domain.model.gateways.deserializator_gateway import (
    DeserializatorGateway,
)
from devsecops_engine_tools.engine_core.src.domain.model.finding import (
    Finding,
    Category,
)
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
from packageurl import PackageURL
from cpe import CPE
from devsecops_engine_tools.engine_utilities.utils.logger_info import MyLogger
from devsecops_engine_tools.engine_utilities import settings

logger = MyLogger.__call__(**settings.SETTING_LOGGER).get_logger()


@dataclass
class DependencyCheckDeserialize(DeserializatorGateway):
    TOOL = "DEPENDENCY_CHECK"

    def get_list_findings(self, dependencies_scanned_file, remote_config={}, module="") -> "list[Finding]":
        dependencies, namespace = self.filter_vulnerabilities_by_confidence(dependencies_scanned_file, remote_config)
        list_open_vulnerabilities = []

        for dependency in dependencies:
            vulnerabilities_node = dependency.find('ns:vulnerabilities', namespace)
            if vulnerabilities_node:
                vulnerabilities = vulnerabilities_node.findall('ns:vulnerability', namespace)
                for vulnerability in vulnerabilities:
                    data = self.extract_common_vuln_data(vulnerability, dependency, namespace)
                    cvss_node = vulnerability.find('ns:cvssV3', namespace)
                    cvss = ", ".join(f"{child.tag.split('}')[-1]}: {child.text}" for child in cvss_node) if cvss_node else ""

                    finding_open = Finding(
                        id=data["id"],
                        cvss=cvss,
                        where=data["where"],
                        description=data["description"][:120].replace("\n\n", " ").replace("\n", " ").strip() if data["description"] else "No description available",
                        severity=data["severity"],
                        identification_date=datetime.now().strftime("%d%m%Y"),
                        published_date_cve=None,
                        module="engine_dependencies",
                        category=Category.VULNERABILITY,
                        requirements=data["fix"] or "Not found",
                        tool="DEPENDENCY_CHECK",
                    )
                    list_open_vulnerabilities.append(finding_open)

        return list_open_vulnerabilities

    def filter_vulnerabilities_by_confidence(self, dependencies_scanned_file, remote_config):
        data_result = ET.parse(dependencies_scanned_file)
        root = data_result.getroot()

        namespace_uri = root.tag.split('}')[0].strip('{')
        namespace = {'ns': namespace_uri}
        ET.register_namespace('', namespace_uri)

        confidence_levels = ["low", "medium", "high", "highest"]
        confidences = remote_config[self.TOOL]["VULNERABILITY_CONFIDENCE"]

        dependencies = root.find('ns:dependencies', namespace)
        if dependencies:
            to_remove = []
            for dep in dependencies.findall('ns:dependency', namespace):
                identifiers = dep.find('ns:identifiers', namespace)
                if identifiers:
                    vulnerability_ids = identifiers.findall('ns:vulnerabilityIds', namespace)
                    if vulnerability_ids:
                        vul_ids_confidences = [conf.get("confidence", "").lower() for conf in vulnerability_ids]
                        if len(vul_ids_confidences) > 0:
                            if not max(vul_ids_confidences, key=lambda c: confidence_levels.index(c)) in confidences: 
                                to_remove.append(dep)
                    elif not "no_confidence" in confidences:
                        to_remove.append(dep)
            for dep in to_remove: dependencies.remove(dep)
            data_result.write(dependencies_scanned_file, encoding="utf-8", xml_declaration=True)
        
        return dependencies, namespace

    def get_where(self, dependency, namespace):
        identifiers_node = dependency.find("ns:identifiers", namespace)
        if identifiers_node:
            package_node = identifiers_node.find(".//ns:package", namespace)
            if package_node:
                id = package_node.find("ns:id", namespace).text
                purl = PackageURL.from_string(id)
                purl_parts = purl.to_dict()
                component_name = (
                    purl_parts["namespace"] + ":"
                    if purl_parts["namespace"]
                    and len(purl_parts["namespace"]) > 0
                    else ""
                )
                component_name += (
                    purl_parts["name"]
                    if purl_parts["name"] and len(purl_parts["name"]) > 0
                    else ""
                )
                component_name = component_name or None
                component_version = (
                    purl_parts["version"]
                    if purl_parts["version"] and len(purl_parts["version"]) > 0
                    else ""
                )
                return f"{component_name}:{component_version}"

            cpe_node = identifiers_node.find(
                ".//ns:identifier[@type='cpe']", namespace
            )
            if cpe_node:
                id = cpe_node.find("ns:name", namespace).text
                cpe = CPE(id)
                component_name = (
                    cpe.get_vendor()[0] + ":"
                    if len(cpe.get_vendor()) > 0
                    else ""
                )
                component_name += (
                    cpe.get_product()[0] if len(cpe.get_product()) > 0 else ""
                )
                component_name = component_name or None
                component_version = (
                    cpe.get_version()[0]
                    if len(cpe.get_version()) > 0
                    else None
                )
                return f"{component_name}:{component_version}"

            maven_node = identifiers_node.find(
                ".//ns:identifier[@type='maven']", namespace
            )
            if maven_node:
                maven_parts = maven_node.find("ns:name", namespace).text.split(
                    ":",
                )

                if len(maven_parts) == 3:
                    component_name = maven_parts[0] + ":" + maven_parts[1]
                    component_version = maven_parts[2]
                    return f"{component_name}:{component_version}"
        
        evidence_collected_node = dependency.find(
            ".//ns:evidenceCollected", namespace
        )
        if evidence_collected_node:
            product_node = evidence_collected_node.find(
                ".//ns:evidence[@type='product']", namespace
            )
            if product_node:
                component_name = product_node.find("ns:value", namespace).text
                version_node = evidence_collected_node.find(
                    ".//ns:evidence[@type='version']", namespace
                )
                if version_node:
                    component_version = version_node.find("ns:value", namespace).text

                return f"{component_name}:{component_version}"
        
        return ""
    
    def extract_fix_version(self, vulnerability, namespace):
        fix = "Not found"
        vulnerable_software = vulnerability.find('ns:vulnerableSoftware', namespace)
        if vulnerable_software:
            software = vulnerable_software.findall('ns:software', namespace)
            if software:
                fix = software[0].get("versionEndExcluding", "Not found").lower()
        return fix if fix != "Not found" else None

    def extract_common_vuln_data(self, vulnerability, dependency, namespace):
        fix = self.extract_fix_version(vulnerability, namespace)
        id = vulnerability.find('ns:name', namespace).text[:28]

        where = self.get_where(dependency, namespace)

        description = vulnerability.find('ns:description', namespace)
        description_text = description.text if description is not None and description.text else ""

        severity = vulnerability.find('ns:severity', namespace).text.lower()

        return {
            "id": id,
            "fix": fix,
            "where": where,
            "description": description_text,
            "severity": severity
        }

    def extract_references(self, vulnerability, namespace):
        references_list = []
        references_node = vulnerability.find('ns:references', namespace)
        if references_node:
            references = references_node.findall('ns:reference', namespace)
            for ref in references:
                url = ref.find('ns:url', namespace).text
                if url:
                    references_list.append(url)
        return list(set(references_list))