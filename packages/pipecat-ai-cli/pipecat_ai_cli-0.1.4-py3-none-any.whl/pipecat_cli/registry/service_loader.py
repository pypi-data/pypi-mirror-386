#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Service loading and validation logic.

This module handles loading services, validating configurations,
and providing utilities for working with the service registry.
"""

from ._configs import SERVICE_CONFIGS
from .service_metadata import BotType, ServiceDefinition, ServiceRegistry, ServiceType


def extract_package_extra(package: str) -> str | None:
    """
    Extract the extra name from a package string.

    Args:
        package: Package string like "pipecat-ai[deepgram]" or "pipecat-ai"

    Returns:
        The extra name (e.g., "deepgram") or None if no extra

    Examples:
        >>> extract_package_extra("pipecat-ai[deepgram]")
        'deepgram'
        >>> extract_package_extra("pipecat-ai")
        None
    """
    if "[" in package and "]" in package:
        return package.split("[")[1].split("]")[0]
    return None


class ServiceLoader:
    """Handles loading and validating services from the registry."""

    @staticmethod
    def get_service_by_value(
        service_list: list[ServiceDefinition], value: str
    ) -> ServiceDefinition | None:
        """
        Find a service definition by its value.

        Args:
            service_list: List of service definitions to search
            value: Service value to find

        Returns:
            Service definition or None if not found
        """
        for service in service_list:
            if service.value == value:
                return service
        return None

    @staticmethod
    def get_all_services_by_type(service_type: ServiceType) -> list[ServiceDefinition]:
        """
        Get all services of a specific type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            List of service definitions
        """
        type_map = {
            "transport": ServiceRegistry.WEBRTC_TRANSPORTS + ServiceRegistry.TELEPHONY_TRANSPORTS,
            "stt": ServiceRegistry.STT_SERVICES,
            "llm": ServiceRegistry.LLM_SERVICES,
            "tts": ServiceRegistry.TTS_SERVICES,
            "realtime": ServiceRegistry.REALTIME_SERVICES,
        }
        return type_map.get(service_type, [])

    @staticmethod
    def get_service_config(service_value: str) -> str | None:
        """
        Get the initialization code for a service.

        Args:
            service_value: Service identifier (e.g., "deepgram_stt")

        Returns:
            Initialization code string or None if not found
        """
        return SERVICE_CONFIGS.get(service_value)

    @staticmethod
    def get_service_import(service_value: str) -> list[str]:
        """
        Get import statements for a service.

        Args:
            service_value: Service identifier

        Returns:
            List of import statements
        """
        return ServiceRegistry.IMPORTS.get(service_value, [])

    @staticmethod
    def extract_extras_for_services(services: dict[str, str | list[str]]) -> set[str]:
        """
        Extract all package extras needed for selected services.

        Args:
            services: Dict mapping service type to service value(s)
                     e.g., {"transports": ["daily"], "stt": "deepgram_stt", ...}

        Returns:
            Set of package extras (e.g., {"daily", "deepgram", "openai"})
        """
        extras = set()

        # Always include runner and silero
        extras.add("runner")
        extras.add("silero")

        # Process transports
        if "transports" in services:
            transport_list = (
                services["transports"]
                if isinstance(services["transports"], list)
                else [services["transports"]]
            )
            all_transports = (
                ServiceRegistry.WEBRTC_TRANSPORTS + ServiceRegistry.TELEPHONY_TRANSPORTS
            )
            for transport in transport_list:
                transport_def = ServiceLoader.get_service_by_value(all_transports, transport)
                if transport_def:
                    extra = extract_package_extra(transport_def.package)
                    if extra:
                        extras.add(extra)

        # Process service types (stt, llm, tts, realtime)
        service_type_map = {
            "stt": ServiceRegistry.STT_SERVICES,
            "llm": ServiceRegistry.LLM_SERVICES,
            "tts": ServiceRegistry.TTS_SERVICES,
            "realtime": ServiceRegistry.REALTIME_SERVICES,
        }

        for service_type, service_list in service_type_map.items():
            if service_type in services and services[service_type]:
                service_def = ServiceLoader.get_service_by_value(
                    service_list, services[service_type]
                )
                if service_def:
                    extra = extract_package_extra(service_def.package)
                    if extra:
                        extras.add(extra)

        return extras

    @staticmethod
    def validate_service_exists(service_value: str) -> bool:
        """
        Check if a service exists in the registry.

        Args:
            service_value: Service identifier to check

        Returns:
            True if service exists, False otherwise
        """
        # Check if it's in SERVICE_CONFIGS
        if service_value in SERVICE_CONFIGS:
            return True

        # Check if it's a transport
        all_transports = ServiceRegistry.WEBRTC_TRANSPORTS + ServiceRegistry.TELEPHONY_TRANSPORTS
        if ServiceLoader.get_service_by_value(all_transports, service_value):
            return True

        return False

    @staticmethod
    def get_transport_options(bot_type: BotType) -> list[ServiceDefinition]:
        """
        Get transport options based on bot type.

        Args:
            bot_type: Type of bot ("web" or "telephony")

        Returns:
            List of transport service definitions
        """
        if bot_type == "web":
            return ServiceRegistry.WEBRTC_TRANSPORTS
        elif bot_type == "telephony":
            return ServiceRegistry.TELEPHONY_TRANSPORTS
        return []

    @staticmethod
    def get_imports_for_services(
        services: dict[str, str | list[str]], features: dict[str, bool], bot_type: str = "web"
    ) -> list[str]:
        """
        Get all necessary import statements for selected services and features.

        Args:
            services: Dict mapping service type to service value(s)
            features: Dict of enabled features
            bot_type: Type of bot ("web" or "telephony")

        Returns:
            List of import statements
        """
        imports = set(ServiceRegistry.BASE_IMPORTS)

        # Always add pipeline, context, runner, and vad imports
        imports.update(ServiceRegistry.FEATURE_IMPORTS["pipeline"])
        imports.update(ServiceRegistry.FEATURE_IMPORTS["context"])
        imports.update(ServiceRegistry.FEATURE_IMPORTS["runner"])
        imports.update(ServiceRegistry.FEATURE_IMPORTS["vad"])

        # Add RTVI imports only for web apps
        if bot_type == "web":
            imports.update(ServiceRegistry.FEATURE_IMPORTS["rtvi"])

        # Handle transport imports (can be multiple)
        if "transports" in services:
            transport_list = (
                services["transports"]
                if isinstance(services["transports"], list)
                else [services["transports"]]
            )
            for transport in transport_list:
                if transport in ServiceRegistry.IMPORTS:
                    imports.update(ServiceRegistry.IMPORTS[transport])

        # Handle service imports
        for service_type in ["stt", "llm", "tts", "realtime"]:
            if service_type in services:
                service_value = services[service_type]
                if service_value in ServiceRegistry.IMPORTS:
                    imports.update(ServiceRegistry.IMPORTS[service_value])

        # Add feature imports
        if features.get("recording"):
            imports.update(ServiceRegistry.FEATURE_IMPORTS["recording"])
        if features.get("transcription"):
            imports.update(ServiceRegistry.FEATURE_IMPORTS["transcription"])
        if features.get("smart_turn"):
            imports.update(ServiceRegistry.FEATURE_IMPORTS["smart_turn"])
        if features.get("observability"):
            imports.update(ServiceRegistry.FEATURE_IMPORTS["observability"])

        return list(imports)

    @staticmethod
    def get_missing_services() -> dict[str, list[str]]:
        """
        Find services that are defined but missing configs or imports.

        Returns:
            Dict with 'missing_configs' and 'missing_imports' lists
        """
        missing = {"missing_configs": [], "missing_imports": []}

        # Check all service types
        all_services = []
        all_services.extend(ServiceRegistry.STT_SERVICES)
        all_services.extend(ServiceRegistry.LLM_SERVICES)
        all_services.extend(ServiceRegistry.TTS_SERVICES)
        all_services.extend(ServiceRegistry.REALTIME_SERVICES)

        for service in all_services:
            service_value = service.value

            # Check if config exists
            if service_value not in SERVICE_CONFIGS:
                missing["missing_configs"].append(service_value)

            # Check if imports exist
            if service_value not in ServiceRegistry.IMPORTS:
                missing["missing_imports"].append(service_value)

        return missing
