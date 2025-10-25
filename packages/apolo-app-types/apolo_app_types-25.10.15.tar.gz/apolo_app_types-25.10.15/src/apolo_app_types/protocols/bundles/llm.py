import typing
from enum import Enum
from typing import Literal

from pydantic import Field

from apolo_app_types.protocols.common import (
    AppInputs,
    SchemaExtraMetadata,
)
from apolo_app_types.protocols.common.hugging_face import (
    HuggingFaceToken,
)


TSize = typing.TypeVar("TSize")


class Llama4Size(str, Enum):
    scout = "Llama-4-Scout-17B-16E"
    scout_instruct = "Llama-4-Scout-17B-16E-Instruct"


class DeepSeekR1Size(str, Enum):
    r1 = "R1"
    r1_zero = "R1-Zero"
    r1_distill_llama_70b = "R1-Distill-Llama-70B"
    r1_distill_llama_8b = "R1-Distill-Llama-8B"  # noqa: N815
    r1_distill_qwen_1_5_b = "R1-Distill-Qwen-1.5B"


class MistralSize(str, Enum):
    mistral_7b_v02 = "Mistral-7B-Instruct-v0.2"
    mistral_7b_v03 = "Mistral-7B-Instruct-v0.3"
    mistral_31_24b_instruct = "Mistral-Small-3.1-24B-Instruct-2503"
    mistral_32_24b_instruct = "Mistral-Small-3.2-24B-Instruct-2506"


class GptOssSize(str, Enum):
    gpt_oss_120b = "gpt-oss-120b"
    gpt_oss_20b = "gpt-oss-20b"


class LLMBundleInputs(AppInputs, typing.Generic[TSize]):
    """
    Base class for LLM bundle inputs.
    This class can be extended by specific LLM bundle input classes.
    """

    hf_token: HuggingFaceToken
    autoscaling_enabled: bool = Field(  # noqa: N815
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            description="Enable or disable autoscaling for the LLM.",
            title="Enable Autoscaling",
        ).as_json_schema_extra(),
    )

    size: TSize


class LLama4Inputs(LLMBundleInputs[Llama4Size]):
    """
    Inputs for the Llama4 bundle.
    This class extends LLMBundleInputs to include specific fields for Llama4.
    """

    size: Llama4Size
    llm_class: Literal["llama4"] = "llama4"


class GptOssInputs(LLMBundleInputs[GptOssSize]):
    """
    Inputs for the GptOss bundle.
    This class extends LLMBundleInputs to include specific fields for OpenAIs GptOss.
    """

    size: GptOssSize
    llm_class: Literal["gpt-oss"] = "gpt-oss"


class DeepSeekR1Inputs(LLMBundleInputs[DeepSeekR1Size]):
    """
    Inputs for the DeepSeekR1 bundle.
    This class extends LLMBundleInputs to include specific fields for DeepSeekR1.
    """

    llm_class: Literal["deepseek_r1"] = "deepseek_r1"
    size: DeepSeekR1Size


class MistralInputs(LLMBundleInputs[MistralSize]):
    """
    Inputs for the Mistral bundle.
    This class extends LLMBundleInputs to include specific fields for Mistral.
    """

    llm_class: Literal["mistral"] = "mistral"
    size: MistralSize
