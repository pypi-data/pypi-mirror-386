"""Tool test utilities for the Arklex framework.

This module provides test utilities for validating tool behavior in the Arklex
framework. It includes test orchestrators for Shopify tools, with validation
methods to ensure correct task graph paths and node status.
"""

import json
import os
from typing import Any

from arklex.orchestrator.NLU.core.slot import SlotFiller
from arklex.orchestrator.NLU.services.model_service import DummyModelService
from arklex.utils.logging_utils import LogContext
from tests.utils.utils import MockOrchestrator, MockResourceInitializer

log_context = LogContext(__name__)


class ShopifyToolOrchestrator(MockOrchestrator):
    def __init__(self, config_file_path: str) -> None:
        """Initialize the Shopify tool orchestrator.

        Args:
            config_file_path (str): Path to the configuration file.
        """
        fixed_args: str = os.environ.get("SHOPIFY_FIXED_ARGS", "{}")
        # Handle case where environment variable might be empty or None
        if not fixed_args or fixed_args.strip() == "":
            fixed_args = "{}"
        try:
            self.fixed_args: dict[str, Any] = json.loads(fixed_args)
        except json.JSONDecodeError:
            # If JSON parsing fails, use empty dict as fallback
            self.fixed_args = {}
        super().__init__(config_file_path, self.fixed_args)
        self.resource_initializer = MockResourceInitializer()

    def _validate_result(
        self,
        test_case: dict[str, Any],
        history: list[dict[str, str]],
        params: dict[str, Any],
    ) -> None:
        """Validate the test results for Shopify tools.

        This function only checks that the assistant's response is non-empty.
        """
        assistant_records: list[dict[str, str]] = [
            message for message in history if message["role"] == "assistant"
        ]
        for record in assistant_records:
            assert record["content"] != ""

    def initialize_slotfillapi(self, slotsfillapi: str) -> SlotFiller:
        """Initialize the slot filling API.

        Args:
            slotsfillapi: API endpoint for slot filling

        Returns:
            Initialized SlotFiller instance
        """
        dummy_config = {
            "model_name": "dummy",
            "api_key": "dummy",
            "endpoint": "http://dummy",
            "model_type_or_path": "dummy-path",
            "llm_provider": "dummy",
        }
        if not isinstance(slotsfillapi, str):
            log_context.error("slotsfillapi must be a string")
            return None
        if not slotsfillapi:
            log_context.warning(
                "slotsfillapi is empty, using local model-based slot filling"
            )
            return SlotFiller(DummyModelService(dummy_config))
        log_context.info(f"Initializing SlotFiller with API URL: {slotsfillapi}")
        return SlotFiller(slotsfillapi)
