from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RelevanceMetricConfig(BaseModel):
    """Configuration for relevance metrics including QueryRelevance and ResponseRelevance"""

    relevance_threshold: Optional[float] = Field(
        default=None,
        description="Threshold for determining relevance when not using LLM judge",
    )
    use_llm_judge: bool = Field(
        default=True,
        description="Whether to use LLM as a judge for relevance scoring",
    )


class RelevanceMetric(BaseModel):
    bert_f_score: Optional[float] = None
    reranker_relevance_score: Optional[float] = None
    llm_relevance_score: Optional[float] = None
    reason: Optional[str] = None
    refinement: Optional[str] = None


class QueryRelevanceMetric(RelevanceMetric):
    """Inherits from RelevanceMetric. This class is left empty so that the openapi response schema remains the same as before, but we have a single source of truth for the relevance metric details."""


class ResponseRelevanceMetric(RelevanceMetric):
    """Inherits from RelevanceMetric. This class is left empty so that the openapi response schema remains the same as before, but we have a single source of truth for the relevance metric details."""


class MetricRequest(BaseModel):
    system_prompt: Optional[str] = Field(
        description="System prompt to be used by GenAI Engine for computing metrics.",
        default=None,
    )
    user_query: Optional[str] = Field(
        description="User query to be used by GenAI Engine for computing metrics.",
        default=None,
    )
    context: List[Dict[str, Any]] = Field(
        description="Conversation history and additional context to be used by GenAI Engine for computing metrics.",
        default_factory=list,
        examples=[
            {"role": "user", "value": "What is the weather in Tokyo?"},
            {"role": "assistant", "value": "WeatherTool", "args": {"city": "Tokyo"}},
            {
                "role": "tool",
                "value": '[{"name": "WeatherTool", "result": {"temperature": "20°C", "humidity": "50%", "condition": "sunny"}}]',
            },
            {
                "role": "assistant",
                "value": "The weather in Tokyo is sunny and the temperature is 20°C.",
            },
        ],
    )
    response: Optional[str] = Field(
        description="Response to be used by GenAI Engine for computing metrics.",
        default=None,
    )
