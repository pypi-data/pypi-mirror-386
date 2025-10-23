from __future__ import annotations

from enum import Enum
from typing import Set
import litellm


class APIScorerType(str, Enum):
    """
    Collection of proprietary scorers implemented by Judgment.

    These are ready-made evaluation scorers that can be used to evaluate
    Examples via the Judgment API.
    """

    PROMPT_SCORER = "Prompt Scorer"
    TRACE_PROMPT_SCORER = "Trace Prompt Scorer"
    FAITHFULNESS = "Faithfulness"
    ANSWER_RELEVANCY = "Answer Relevancy"
    ANSWER_CORRECTNESS = "Answer Correctness"
    INSTRUCTION_ADHERENCE = "Instruction Adherence"
    EXECUTION_ORDER = "Execution Order"
    CUSTOM = "Custom"

    @classmethod
    def __missing__(cls, value: str) -> APIScorerType:
        for member in cls:
            if member.value == value.lower():
                return member

        raise ValueError(f"Invalid scorer type: {value}")


LITELLM_SUPPORTED_MODELS: Set[str] = set(litellm.model_list)


TOGETHER_SUPPORTED_MODELS = [
    "meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
    "Qwen/Qwen2-VL-72B-Instruct",
    "meta-llama/Llama-Vision-Free",
    "Gryphe/MythoMax-L2-13b",
    "Qwen/Qwen2.5-72B-Instruct-Turbo",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    "deepseek-ai/DeepSeek-R1",
    "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
    "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
    "google/gemma-2-27b-it",
    "mistralai/Mistral-Small-24B-Instruct-2501",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
    "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-classifier",
    "deepseek-ai/DeepSeek-V3",
    "Qwen/Qwen2-72B-Instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct-Lite",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "upstage/SOLAR-10.7B-Instruct-v1.0",
    "togethercomputer/MoA-1",
    "Qwen/QwQ-32B-Preview",
    "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "databricks/dbrx-instruct",
    "meta-llama/Llama-3-8b-chat-hf",
    "google/gemma-2b-it",
    "meta-llama/Meta-Llama-3-70B-Instruct-Lite",
    "google/gemma-2-9b-it",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-p",
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "Gryphe/MythoMax-L2-13b-Lite",
    "meta-llama/Llama-2-7b-chat-hf",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    "meta-llama/Llama-2-13b-chat-hf",
    "scb10x/scb10x-llama3-typhoon-v1-5-8b-instruct",
    "scb10x/scb10x-llama3-typhoon-v1-5x-4f316",
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "microsoft/WizardLM-2-8x22B",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "scb10x/scb10x-llama3-1-typhoon2-60256",
    "Qwen/Qwen2.5-7B-Instruct-Turbo",
    "scb10x/scb10x-llama3-1-typhoon-18370",
    "meta-llama/Llama-3.2-3B-Instruct-Turbo",
    "meta-llama/Llama-3-70b-chat-hf",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "togethercomputer/MoA-1-Turbo",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
    "mistralai/Mistral-7B-Instruct-v0.1",
]

JUDGMENT_SUPPORTED_MODELS = {"osiris-large", "osiris-mini", "osiris"}

ACCEPTABLE_MODELS = (
    set(litellm.model_list) | set(TOGETHER_SUPPORTED_MODELS) | JUDGMENT_SUPPORTED_MODELS
)
