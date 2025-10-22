from dataclasses import dataclass
from typing import Iterator, Tuple, Union, List, Literal, Mapping, Optional, Callable
from enum import Enum
from collections.abc import AsyncGenerator
from typing import Any

@dataclass
class DType(Enum):
    F16 = "f16"
    BF16 = "bf16"
    F32 = "f32"

@dataclass
class GenerationOutput:
    seq_id: int
    prompt_length: int
    prompt_start_time: int
    decode_start_time: int
    decode_finish_time: int
    decoded_length: int
    decode_output: str

@dataclass
class GenerationConfig:
    temperature: Optional[float]
    top_p: Optional[float]
    top_k: Optional[int]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]

@dataclass
class EngineConfig:
    model_id: Optional[str]
    weight_path: Optional[str]
    weight_file: Optional[str]
    hf_token: Optional[str]
    hf_token_path: Optional[str]
    tokenizer: Optional[str]
    tokenizer_config: Optional[str]
    num_blocks: Optional[int]
    max_num_seqs: Optional[int]
    max_model_len: Optional[int]
    max_tokens: Optional[int]
    max_num_batched_tokens: Optional[int]
    isq: Optional[str]
    num_shards: Optional[int]
    device_id: Optional[int]
    generation_cfg: Optional[GenerationConfig]
    seed: Optional[int]
    flash_context: Optional[bool]
    fp8_kvcache: Optional[bool]
    server_mode: Optional[bool]

@dataclass
class SamplingParams:
    temperature: Optional[float]
    max_tokens: Optional[int]
    ignore_eos: Optional[bool]
    top_k: Optional[int]
    top_p: Optional[float]
    session_id: Optional[str]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]

@dataclass
class Message:
    role: str
    content: str

@dataclass
class StepOutput(Enum):
    Token: int
    Tokens: List[int]

@dataclass
class StreamItem:
    """
    An item returned by the EngineStream iterator.
    Check the `type` attribute to determine how to interpret the `data`.
    """
    @property
    def datatype(self) -> Literal["TOKEN", "TOKEN_ID", "COMPLETION", "DONE", "ERROR"]:
        """The type of the stream item."""
        ...

    @property
    def data(self) -> Union[
        str,                         # For TOKEN or ERROR
        int,                         # For TOKEN_ID
        Tuple[int, int, int, int],   # For DONE
        Tuple[int, int, int, List[int]] # For COMPLETION
    ]:
        """The data payload of the stream item."""
        ...

class EngineStream:
    finished: bool
    seq_id: int
    prompt_length: int
    cancelled: bool
    def cancel(self): ...
    def __iter__(self) -> Iterator[StreamItem]: ...
    def __next__(self) -> StreamItem: ...

class Engine:
    def __init__(econfig: EngineConfig, dtype: DType) -> Engine:
        """
        Create a vllm.rs engine with given engine config and dtype ("f16", "bf16", and "f32")
        """

    def apply_chat_template(self, params: SamplingParams, messages: List[Message], log: bool) -> str:
        """
        Apply chat template to given messages
        """

    def generate_sync(self,
        params: List[SamplingParams],
        prompts: List[str],
    ) -> List[GenerationOutput]:
        """
        Chat completion using given prompts and sampling parameters
        """
    def generate_stream(
        self,
        params: SamplingParams,
        prompt: str,
    ) -> Tuple[int, int, EngineStream]:
        """
        Chat streaming using given prompts and sampling parameters.

        Return: (seq_id, prompt_length, stream) tuples
        """

    def get_num_cached_tokens(
        self,
    ) -> int:
        """
        Call this function when context-cache feature enabled

        Return: total number of context cached for all requests
        """

    def get_available_kv_tokens(
        self,
    ) -> int:
        """
        Return: total number of available kvcache tokens
        """