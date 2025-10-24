# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from metrics_computation_engine.models.requests import LLMJudgeConfig
from metrics_computation_engine.llm_judge.jury import Jury
from metrics_computation_engine.models.eval import MetricResult
from metrics_computation_engine.types import AggregationLevel
from metrics_computation_engine.dal.api_client import get_api_client
from metrics_computation_engine.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_PROVIDER = "NATIVE"


class BaseMetric(ABC):
    """Base class for generic metric"""

    def __init__(self, jury: Optional[Jury] = None, dataset: Optional[Dict] = None):
        self.jury = jury
        self.dataset = dataset
        self.name: str = ""  # Set by concrete implementations
        self.aggregation_level: AggregationLevel  # Set by concrete implementations

    @abstractmethod
    def init_with_model(self, model: Any) -> bool:
        """Set the model that will be used by the metric"""
        pass

    @abstractmethod
    def get_model_provider(self) -> Optional[str]:
        """Return the model provider, if a model is needed by the metric"""
        pass

    @abstractmethod
    def create_model(self, llm_config: LLMJudgeConfig) -> Any:
        """Create the LLM model handler for the metric, using the config passed"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the plugin configuration"""
        pass

    @property
    @abstractmethod
    def required_parameters(self) -> List[str]:
        """Return list of required parameters for this metric"""
        pass

    def supports_agent_computation(self) -> bool:
        """
        Indicate whether this metric supports agent-level computation.

        By default, metrics do not support agent-level computation.
        Subclasses can override this method to enable agent-level processing.

        Returns:
            bool: True if the metric supports agent-level computation, False otherwise
        """
        return False

    async def compute_with_dispatch(
        self, *args, **context
    ) -> Union[MetricResult, List[MetricResult]]:
        """
        Compute method with centralized dispatch logic.

        This method automatically routes to session-level or agent-level computation
        based on the agent_computation context flag.

        Args:
            *args: Arguments (typically session data)
            **context: Additional context including agent_computation flag

        Returns:
            MetricResult for session-level or List[MetricResult] for agent-level
        """
        # Check for agent computation flag in context
        is_agent_computation = context.get("agent_computation", False)

        # Check if this is agent-level computation
        if self.supports_agent_computation() and is_agent_computation:
            return await self.compute_agent_level(*args)

        # Session-level computation (default)
        return await self.compute(*args, **context)

    @abstractmethod
    async def compute(self, *args, **context) -> MetricResult:
        """
        Compute metric at session level (default behavior).

        This method must be implemented by all metrics to handle session-level computation.

        Args:
            *args: Arguments (typically session data)
            **context: Additional context

        Returns:
            MetricResult: Single result for the session
        """
        pass

    async def compute_agent_level(self, *args) -> List[MetricResult]:
        """
        Compute metric at agent level.

        This method should be overridden by metrics that support agent-level computation.

        Args:
            *args: Arguments (typically session data)

        Returns:
            List[MetricResult]: One result per agent

        Raises:
            NotImplementedError: If the metric doesn't support agent computation
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support agent-level computation. "
            f"Override compute_agent_level() method or return False from supports_agent_computation()."
        )

    def _create_success_result(
        self,
        score: float,
        category: str,
        app_name: str,
        agent_id: Optional[str] = None,
        reasoning: str = "",
        entities_involved: Optional[List[str]] = None,
        span_ids: Optional[List[str]] = None,
        session_ids: Optional[List[str]] = None,
        description: Optional[str] = "",
    ) -> MetricResult:
        """
        Create a successful MetricResult for LLM-as-a-judge metrics.

        Args:
            score: Computed score
            reasoning: LLM reasoning for the score
            span_ids: List of span IDs involved in the computation
            session_ids: List of session IDs involved in the computation

        Returns:
            MetricResult object for success case
        """
        return MetricResult(
            metric_name=self.name,
            description=description,
            value=score,
            unit="",
            aggregation_level=self.aggregation_level,
            category=category,
            app_name=app_name,
            agent_id=agent_id,
            span_id=span_ids or [],
            session_id=session_ids or [],
            source="native",
            entities_involved=entities_involved,
            edges_involved=[],
            success=True,
            metadata={"metric_type": "llm-as-a-judge"},
            error_message=None,
            reasoning=reasoning,
        )

    def _create_error_result(
        self,
        category: str,
        app_name: str,
        agent_id: Optional[str] = None,
        error_message: str = "Computation failed",
        entities_involved: Optional[List[str]] = None,
        span_ids: Optional[List[str]] = None,
        session_ids: Optional[List[str]] = None,
        description: Optional[str] = "",
    ) -> MetricResult:
        """
        Create an error MetricResult for when computation fails.

        Args:
            error_message: Descriptive error message
            span_ids: List of span IDs involved in the computation
            session_ids: List of session IDs involved in the computation

        Returns:
            MetricResult object for error case
        """
        return MetricResult(
            metric_name=self.name,
            description=description,
            value=-1.0,
            reasoning="",
            unit="",
            aggregation_level=self.aggregation_level,
            category=category,
            app_name=app_name,
            agent_id=agent_id,
            span_id=span_ids or [],
            session_id=session_ids or [],
            source="native",
            entities_involved=entities_involved,
            edges_involved=[],
            success=False,
            metadata={"metric_type": "llm-as-a-judge"},
            error_message=error_message,
        )

    def get_cache_metric(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a cache key for this metric computation.

        Override this method in concrete metrics if you need custom cache key logic.
        Default implementation uses metric name + data hash.

        Args:
            data: The data being processed by the metric
            context: Optional context data

        Returns:
            A unique cache key string for this computation
        """
        import hashlib

        data_str = str(data) if data else ""
        context_str = str(context) if context else ""
        combined = f"{self.name}:{data_str}:{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def check_cache_metric(
        self,
        metric_name: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Union[MetricResult, List[MetricResult]]]:
        """Check if this metric result exists in cache/database.

        Returns the cached result if found, None otherwise.
        Only checks cache if METRICS_CACHE_ENABLED is True.

        Args:
            metric_name: Name of the metric
            session_id: Session ID
            context: Optional context data (for agent-specific caching)

        Returns:
            Cached MetricResult or List[MetricResult] if found, None otherwise
        """

        def _check_metrics_conditions(
            list_of_json_objects: list, metric_name: str
        ) -> bool:
            """
            Analyzes a list of JSON objects to check if any object's 'metrics' attribute
            matches specific conditions.

            Used conditionally to decide whether to skip writing metrics for a session.
            Returns True if:
            - 'metrics.aggregation_level' is set AND
            - 'metrics.category' is set AND
            - 'metrics.name' is set

            Otherwise, returns False.

            Args:
                list_of_json_objects (list): A list of dictionaries (representing JSON objects).

            Returns:
                bool: True if any object meets the conditions, False otherwise.
                Dict: the metric read from db as a db dict
            """
            for obj in list_of_json_objects:
                if isinstance(obj, dict) and "metrics" in obj:
                    metrics = obj["metrics"]
                    # Parse JSON string if metrics is stored as string
                    if isinstance(metrics, str):
                        try:
                            import json

                            metrics = json.loads(metrics)
                        except (json.JSONDecodeError, TypeError):
                            continue

                    if isinstance(metrics, dict):
                        read_metric_name = metrics.get("metric_name", "")

                        # Condition
                        if metric_name == read_metric_name:
                            return True, obj
            return False, None

        # Check if caching is enabled
        if not os.getenv("METRICS_CACHE_ENABLED", "false").lower() == "true":
            return None

        # database retrieval here
        metrics = get_api_client().get_session_metrics(session_id=session_id)

        # Handle agent-specific caching
        if context and context.get("agent_computation"):
            if "agent_id" in context:
                # Looking for specific agent result
                return self._check_agent_cache(
                    metrics, metric_name, context["agent_id"]
                )
            else:
                # Looking for all agent results for this session
                return self._check_all_agents_cache(metrics, metric_name)
        else:
            # Regular session/span cache lookup - only look for session-level metrics
            is_cached_metric, metric = self._check_session_cache(metrics, metric_name)

            if is_cached_metric:
                metric_data = metric.get("metrics", {})

                # Parse JSON string if metrics is stored as string
                if isinstance(metric_data, str):
                    try:
                        import json

                        metric_data = json.loads(metric_data)
                    except (json.JSONDecodeError, TypeError):
                        return None

                metric_data["from_cache"] = True

                # Ensure required fields are present for backward compatibility with cached data
                if "category" not in metric_data:
                    metric_data["category"] = "application"  # Default category
                if "app_name" not in metric_data:
                    metric_data["app_name"] = "unknown"  # Default app_name

                return MetricResult(**metric_data)
            return None

    def _check_agent_cache(
        self, metrics: List, metric_name: str, agent_id: str
    ) -> Optional[MetricResult]:
        """Check cache for specific agent result"""
        for obj in metrics:
            if isinstance(obj, dict) and "metrics" in obj:
                metric_data = obj["metrics"]

                # Parse JSON string if metrics is stored as string
                if isinstance(metric_data, str):
                    try:
                        import json

                        metric_data = json.loads(metric_data)
                    except (json.JSONDecodeError, TypeError):
                        continue

                if isinstance(metric_data, dict):
                    # Check if this matches our metric and agent
                    if (
                        metric_data.get("metric_name") == metric_name
                        and metric_data.get("metadata", {}).get("agent_id") == agent_id
                    ):
                        metric_data["from_cache"] = True
                        # Ensure backward compatibility
                        if "category" not in metric_data:
                            metric_data["category"] = "application"
                        if "app_name" not in metric_data:
                            metric_data["app_name"] = "unknown"

                        return MetricResult(**metric_data)
        return None

    def _check_all_agents_cache(
        self, metrics: List, metric_name: str
    ) -> Optional[List[MetricResult]]:
        """Check cache for all agent results for this session"""
        agent_results = []

        for obj in metrics:
            if isinstance(obj, dict) and "metrics" in obj:
                metric_data = obj["metrics"]

                # Parse JSON string if metrics is stored as string
                if isinstance(metric_data, str):
                    try:
                        import json

                        metric_data = json.loads(metric_data)
                    except (json.JSONDecodeError, TypeError):
                        continue

                if isinstance(metric_data, dict):
                    # Check if this is an agent result for our metric
                    if metric_data.get(
                        "metric_name"
                    ) == metric_name and "agent_id" in metric_data.get("metadata", {}):
                        metric_data["from_cache"] = True
                        if "category" not in metric_data:
                            metric_data["category"] = "application"
                        if "app_name" not in metric_data:
                            metric_data["app_name"] = "unknown"

                        agent_results.append(MetricResult(**metric_data))

        return agent_results if agent_results else None

    def _check_session_cache(
        self, metrics: List, metric_name: str
    ) -> tuple[bool, dict]:
        """Check cache for session-level metrics only (excludes agent metrics)"""
        for obj in metrics:
            if isinstance(obj, dict) and "metrics" in obj:
                metric_data = obj["metrics"]

                # Parse JSON string if metrics is stored as string
                if isinstance(metric_data, str):
                    try:
                        import json

                        metric_data = json.loads(metric_data)
                    except (json.JSONDecodeError, TypeError):
                        continue

                if isinstance(metric_data, dict):
                    read_metric_name = metric_data.get("metric_name", "")
                    aggregation_level = metric_data.get("aggregation_level", "")
                    has_agent_id = "agent_id" in metric_data.get("metadata", {})

                    # Only match session-level metrics (not agent-level)
                    if (
                        metric_name == read_metric_name
                        and aggregation_level == "session"
                        and not has_agent_id
                    ):
                        return True, obj
        return False, None

    def get_default_provider(self) -> str:
        return DEFAULT_PROVIDER

    def get_provider_no_model_needed(self):
        return None

    def create_no_model(self, llm_config: LLMJudgeConfig):
        return None

    def create_native_model(self, llm_config: LLMJudgeConfig) -> Any:
        jury = Jury(llm_config.model_dump())
        return jury


class CustomBaseMetric(BaseMetric, ABC):
    """
    Simplified metric base: User only sets 'aggregation_level' as a class variable and implements 'compute'.
    """

    name: Optional[str] = None  # User must set this in the class definition
    aggregation_level: Optional[AggregationLevel] = (
        None  # User must set this in the class definition
    )

    def __init__(self, metric_name: Optional[str] = None):
        super().__init__()
        if metric_name is None:
            metric_name = self.__class__.__name__
        self.name = metric_name
        # Optionally check that subclass has defined aggregation_level
        if self.aggregation_level is None:
            raise ValueError(
                "aggregation_level must be set as a class variable in your metric subclass."
            )

    @property
    def required_parameters(self) -> List[str]:
        return []

    def validate_config(self) -> bool:
        return True

    @abstractmethod
    async def compute(self, data: Any):
        pass
