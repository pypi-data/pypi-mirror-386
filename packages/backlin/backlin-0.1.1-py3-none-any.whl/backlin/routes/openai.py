from __future__ import annotations

from collections import defaultdict
import json
import time
import asyncio
import base64
import logging
import os
import shutil
from typing import Any, Dict, List, Literal, Optional, Set, Union, AsyncGenerator, Iterable, Tuple
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import httpx
from pydantic import BaseModel, typing, Field, AnyUrl, ConfigDict
from pydantic.fields import FieldInfo
from loguru import logger
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi import UploadFile
import openai
from openai import AsyncClient
from openai.pagination import AsyncPage
from openai.types.model import Model
from openai.types.file_object import FileObject
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)

from backlin.routes.apilog import log_api_request


class OpenAIBaseInput(BaseModel):
    user: Optional[str] = None
    # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
    # The extra values given here take precedence over values defined on the client or passed to this method.
    extra_headers: Optional[Dict[str, Any]] = None
    extra_query: Optional[Dict[str, Any]] = None
    extra_json: Optional[Dict] = Field(None, alias="extra_body")
    timeout: Optional[float] = None

    class Config:
        extra = "allow"


class OpenAIChatInput(OpenAIBaseInput):
    messages: List[ChatCompletionMessageParam]
    model: str
    frequency_penalty: Optional[float] = None
    function_call: Optional[completion_create_params.FunctionCall] = None
    functions: List[completion_create_params.Function] = None
    logit_bias: Optional[Dict[str, int]] = None
    logprobs: Optional[bool] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None
    presence_penalty: Optional[float] = None
    response_format: completion_create_params.ResponseFormat = None
    seed: Optional[int] = None
    stop: Union[Optional[str], List[str]] = None
    stream: Optional[bool] = None
    temperature: Optional[float] = 0.0
    tool_choice: Optional[Union[ChatCompletionToolChoiceOptionParam, str]] = None
    tools: List[Union[ChatCompletionToolParam, str]] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None


class OpenAIEmbeddingsInput(OpenAIBaseInput):
    input: Union[str, List[str]]
    model: str
    dimensions: Optional[int] = None
    encoding_format: Optional[Literal["float", "base64"]] = None


class OpenAIImageBaseInput(OpenAIBaseInput):
    model: str
    n: int = 1
    response_format: Optional[Literal["url", "b64_json"]] = None
    size: Optional[Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]] = "256x256"


class OpenAIImageGenerationsInput(OpenAIImageBaseInput):
    prompt: str
    quality: Literal["standard", "hd"] = None
    style: Optional[Literal["vivid", "natural"]] = None


class OpenAIImageVariationsInput(OpenAIImageBaseInput):
    image: Union[UploadFile, AnyUrl]


class OpenAIImageEditsInput(OpenAIImageVariationsInput):
    prompt: str
    mask: Union[UploadFile, AnyUrl]


class OpenAIAudioTranslationsInput(OpenAIBaseInput):
    file: Union[UploadFile, AnyUrl]
    model: str
    prompt: Optional[str] = None
    response_format: Optional[str] = None
    temperature: float = 0.0


class OpenAIAudioTranscriptionsInput(OpenAIAudioTranslationsInput):
    language: Optional[str] = None
    timestamp_granularities: Optional[List[Literal["word", "segment"]]] = None


class OpenAIAudioSpeechInput(OpenAIBaseInput):
    input: str
    model: str
    voice: str
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "pcm", "wav"]] = None
    speed: Optional[float] = None


# class OpenAIFileInput(OpenAIBaseInput):
#     file: UploadFile # FileTypes
#     purpose: Literal["fine-tune", "assistants"] = "assistants"


class MsgType:
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    VIDEO = 4


class OpenAIBaseOutput(BaseModel):
    id: Optional[str] = None
    content: Optional[str] = None
    model: Optional[str] = None
    object: Literal["chat.completion", "chat.completion.chunk"] = "chat.completion.chunk"
    role: Literal["assistant"] = "assistant"
    finish_reason: Optional[str] = None
    created: int = Field(default_factory=lambda: int(time.time()))
    tool_calls: List[Dict] = []

    status: Optional[int] = None  # AgentStatus
    message_type: int = MsgType.TEXT
    message_id: Optional[str] = None  # id in database table
    is_ref: bool = False  # wheather show in seperated expander

    class Config:
        extra = "allow"

    def model_dump(self) -> dict:
        result = {
            "id": self.id,
            "object": self.object,
            "model": self.model,
            "created": self.created,
            "status": self.status,
            "message_type": self.message_type,
            "message_id": self.message_id,
            "is_ref": self.is_ref,
            **(self.model_extra or {}),
        }

        if self.object == "chat.completion.chunk":
            result["choices"] = [
                {
                    "delta": {
                        "content": self.content,
                        "tool_calls": self.tool_calls,
                    },
                    "role": self.role,
                }
            ]
        elif self.object == "chat.completion":
            result["choices"] = [
                {
                    "message": {
                        "role": self.role,
                        "content": self.content,
                        "finish_reason": self.finish_reason,
                        "tool_calls": self.tool_calls,
                    }
                }
            ]
        return result

    def model_dump_json(self):
        return json.dumps(self.model_dump(), ensure_ascii=False)


class OpenAIChatOutput(OpenAIBaseOutput): ...


DEFAULT_API_CONCURRENCIES = 5  # 默认单个模型最大并发数
model_semaphores: Dict[Tuple[str, str], asyncio.Semaphore] = {}  # key: (model_name, platform)
app = APIRouter(prefix="/v1", tags=["OpenAI 兼容平台整合接口"])


class MyBaseModel(BaseModel):
    model_config = ConfigDict(
        use_attribute_docstrings=True,
        extra="allow",
        env_file_encoding="utf-8",
    )


class PlatformConfig(MyBaseModel):
    """模型加载平台配置"""

    platform_name: str = "xinference"
    """平台名称"""

    platform_type: Literal["xinference", "ollama", "oneapi", "fastchat", "openai", "custom openai"] = "xinference"
    """平台类型"""

    api_base_url: str = "http://127.0.0.1:9997/v1"
    """openai api url"""

    api_key: str = "EMPTY"
    """api key if available"""

    api_proxy: str = ""
    """API 代理"""

    api_concurrencies: int = 5
    """该平台单模型最大并发数"""

    auto_detect_model: bool = False
    """是否自动获取平台可用模型列表。设为 True 时下方不同模型类型可自动检测"""

    llm_models: Union[Literal["auto"], List[str]] = [
        "glm4-chat",
        "qwen1.5-chat",
        "qwen2-instruct",
        "gpt-3.5-turbo",
        "gpt-4o",
    ]
    """该平台支持的大语言模型列表，auto_detect_model 设为 True 时自动检测"""

    embed_models: Union[Literal["auto"], List[str]] = [
        "bge-large-zh-v1.5",
    ]
    """该平台支持的嵌入模型列表，auto_detect_model 设为 True 时自动检测"""

    text2image_models: Union[Literal["auto"], List[str]] = []
    """该平台支持的图像生成模型列表，auto_detect_model 设为 True 时自动检测"""

    image2text_models: Union[Literal["auto"], List[str]] = []
    """该平台支持的多模态模型列表，auto_detect_model 设为 True 时自动检测"""

    rerank_models: Union[Literal["auto"], List[str]] = []
    """该平台支持的重排模型列表，auto_detect_model 设为 True 时自动检测"""

    speech2text_models: Union[Literal["auto"], List[str]] = []
    """该平台支持的 STT 模型列表，auto_detect_model 设为 True 时自动检测"""

    text2speech_models: Union[Literal["auto"], List[str]] = []
    """该平台支持的 TTS 模型列表，auto_detect_model 设为 True 时自动检测"""


class ApiModelSettings(MyBaseModel):
    """模型配置项"""

    DEFAULT_LLM_MODEL: str = "glm4-chat"
    """默认选用的 LLM 名称"""

    DEFAULT_EMBEDDING_MODEL: str = "bge-m3"
    """默认选用的 Embedding 名称"""

    HISTORY_LEN: int = 3
    """默认历史对话轮数"""

    TEMPERATURE: float = 0.7
    """LLM通用对话参数"""

    SUPPORT_AGENT_MODELS: List[str] = [
        "chatglm3-6b",
        "glm-4",
        "openai-api",
        "Qwen-2",
        "qwen2-instruct",
        "gpt-3.5-turbo",
        "gpt-4o",
    ]
    """支持的Agent模型"""

    LLM_MODEL_CONFIG: Dict[str, Dict] = {
        # 意图识别不需要输出，模型后台知道就行
        "preprocess_model": {
            "model": "",
            "temperature": 0.05,
            "max_tokens": 4096,
            "history_len": 10,
            "prompt_name": "default",
            "callbacks": False,
        },
        "llm_model": {
            "model": "",
            "temperature": 0.9,
            "max_tokens": 4096,
            "history_len": 10,
            "prompt_name": "default",
            "callbacks": True,
        },
        "action_model": {
            "model": "",
            "temperature": 0.01,
            "max_tokens": 4096,
            "history_len": 10,
            "prompt_name": "ChatGLM3",
            "callbacks": True,
        },
        "postprocess_model": {
            "model": "",
            "temperature": 0.01,
            "max_tokens": 4096,
            "history_len": 10,
            "prompt_name": "default",
            "callbacks": True,
        },
        "image_model": {
            "model": "sd-turbo",
            "size": "256*256",
        },
    }
    """
    LLM模型配置，包括了不同模态初始化参数。
    `model` 如果留空则自动使用 DEFAULT_LLM_MODEL
    """

    MODEL_PLATFORMS: List[PlatformConfig] = [
        # PlatformConfig(
        #     platform_name="xinference-auto",
        #     platform_type="xinference",
        #     api_base_url="http://127.0.0.1:9997/v1",
        #     api_key="EMPTY",
        #     api_concurrencies=5,
        #     auto_detect_model=True,
        #     llm_models=[],
        #     embed_models=[],
        #     text2image_models=[],
        #     image2text_models=[],
        #     rerank_models=[],
        #     speech2text_models=[],
        #     text2speech_models=[],
        # ),
        # PlatformConfig(
        #     platform_name="xinference",
        #     platform_type="xinference",
        #     api_base_url="http://127.0.0.1:9997/v1",
        #     api_key="EMPTY",
        #     api_concurrencies=5,
        #     llm_models=[
        #         "glm4-chat",
        #         "qwen1.5-chat",
        #         "qwen2-instruct",
        #     ],
        #     embed_models=[
        #         "bge-large-zh-v1.5",
        #     ],
        #     text2image_models=[],
        #     image2text_models=[],
        #     rerank_models=[],
        #     speech2text_models=[],
        #     text2speech_models=[],
        # ),
        # PlatformConfig(
        #     platform_name="ollama",
        #     platform_type="ollama",
        #     api_base_url="http://127.0.0.1:11434/v1",
        #     api_key="EMPTY",
        #     api_concurrencies=5,
        #     llm_models=[
        #         "qwen:7b",
        #         "qwen2:7b",
        #     ],
        #     embed_models=[
        #         "quentinz/bge-large-zh-v1.5",
        #     ],
        # ),
        # PlatformConfig(
        #     platform_name="oneapi",
        #     platform_type="oneapi",
        #     api_base_url="http://127.0.0.1:3000/v1",
        #     api_key="sk-",
        #     api_concurrencies=5,
        #     llm_models=[
        #         # 智谱 API
        #         "chatglm_pro",
        #         "chatglm_turbo",
        #         "chatglm_std",
        #         "chatglm_lite",
        #         # 千问 API
        #         "qwen-turbo",
        #         "qwen-plus",
        #         "qwen-max",
        #         "qwen-max-longcontext",
        #         # 千帆 API
        #         "ERNIE-Bot",
        #         "ERNIE-Bot-turbo",
        #         "ERNIE-Bot-4",
        #         # 星火 API
        #         "SparkDesk",
        #     ],
        #     embed_models=[
        #         # 千问 API
        #         "text-embedding-v1",
        #         # 千帆 API
        #         "Embedding-V1",
        #     ],
        #     text2image_models=[],
        #     image2text_models=[],
        #     rerank_models=[],
        #     speech2text_models=[],
        #     text2speech_models=[],
        # ),
        # PlatformConfig(
        #     platform_name="openai",
        #     platform_type="openai",
        #     api_base_url="https://api.openai.com/v1",
        #     api_key="sk-proj-",
        #     api_concurrencies=5,
        #     llm_models=[
        #         "gpt-4o",
        #         "gpt-3.5-turbo",
        #     ],
        #     embed_models=[
        #         "text-embedding-3-small",
        #         "text-embedding-3-large",
        #     ],
        # ),
        PlatformConfig(
            platform_name="deepseek",
            platform_type="openai",
            api_base_url="https://api.deepseek.com/v1",
            api_key="sk-0db95ae420d84f7d94cab45a2fcce83a",
            api_concurrencies=5,
            llm_models=[
                "deepseek-chat",
            ],
        ),
        PlatformConfig(
            platform_name="moonshoot",
            platform_type="openai",
            api_base_url="https://api.moonshot.cn/v1",
            api_key="sk-9LGuljtn6SaEBezBAT50jlNeRlQ6vOkimrentZJUk4SvrckQ",
            api_concurrencies=5,
            llm_models=[
                "moonshot-v1-32k",
            ],
        ),
    ]
    """模型平台配置"""


model_settings = ApiModelSettings()
BASE_TEMP_DIR = "data"


def get_config_platforms() -> Dict[str, Dict]:
    """
    获取配置的模型平台，会将 pydantic model 转换为字典。
    """
    platforms = [m.model_dump() for m in model_settings.MODEL_PLATFORMS]
    return {m["platform_name"]: m for m in platforms}


def get_config_models(
    model_name: str = None,
    platform_name: str = None,
) -> Dict[str, Dict]:
    """
    获取配置的模型列表，返回值为:
    {model_name: {
        "platform_name": xx,
        "platform_type": xx,
        "model_type": xx,
        "model_name": xx,
        "api_base_url": xx,
        "api_key": xx,
        "api_proxy": xx,
    }}
    """
    result = {}
    model_types = [
        "llm_models",
    ]
    for m in list(get_config_platforms().values()):
        if platform_name is not None and platform_name != m.get("platform_name"):
            continue

        for m_type in model_types:
            models = m.get(m_type, [])
            if models == "auto":
                logger.warning("you should not set `auto` without auto_detect_model=True")
                continue
            elif not models:
                continue
            for m_name in models:
                if model_name is None or model_name == m_name:
                    result[m_name] = {
                        "platform_name": m.get("platform_name"),
                        "platform_type": m.get("platform_type"),
                        "model_type": m_type.split("_")[0],
                        "model_name": m_name,
                        "api_base_url": m.get("api_base_url"),
                        "api_key": m.get("api_key"),
                        "api_proxy": m.get("api_proxy"),
                    }
    return result


def get_model_info(model_name: str = None, platform_name: str = None, multiple: bool = False) -> Dict:
    """
    获取配置的模型信息，主要是 api_base_url, api_key
    如果指定 multiple=True，则返回所有重名模型；否则仅返回第一个
    """
    result = get_config_models(model_name=model_name, platform_name=platform_name)
    if len(result) > 0:
        if multiple:
            return result
        else:
            return list(result.values())[0]
    else:
        return {}


def get_OpenAIClient(
    platform_name: str = None,
    model_name: str = None,
    is_async: bool = True,
) -> Union[openai.Client, openai.AsyncClient]:
    """
    construct an openai Client for specified platform or model
    """
    if platform_name is None:
        platform_info = get_model_info(model_name=model_name, platform_name=platform_name)
        if platform_info is None:
            raise RuntimeError(f"cannot find configured platform for model: {model_name}")
        platform_name = platform_info.get("platform_name")
    platform_info = get_config_platforms().get(platform_name)
    assert platform_info, f"cannot find configured platform: {platform_name}"
    params = {
        "base_url": platform_info.get("api_base_url"),
        "api_key": platform_info.get("api_key"),
    }
    httpx_params = {}
    if api_proxy := platform_info.get("api_proxy"):
        httpx_params = {
            "proxies": api_proxy,
            "transport": httpx.HTTPTransport(local_address="0.0.0.0"),
        }

    if is_async:
        if httpx_params:
            params["http_client"] = httpx.AsyncClient(**httpx_params)
        return openai.AsyncClient(**params)
    else:
        if httpx_params:
            params["http_client"] = httpx.Client(**httpx_params)
        return openai.Client(**params)


@asynccontextmanager
async def get_model_client(model_name: str) -> AsyncGenerator[AsyncClient]:
    """
    对重名模型进行调度，依次选择：空闲的模型 -> 当前访问数最少的模型
    """
    max_semaphore = 0
    selected_platform = ""
    model_infos = get_model_info(model_name=model_name, multiple=True)
    assert model_infos, f"specified model '{model_name}' cannot be found in MODEL_PLATFORMS."

    for m, c in model_infos.items():
        key = (m, c["platform_name"])
        api_concurrencies = c.get("api_concurrencies", DEFAULT_API_CONCURRENCIES)
        if key not in model_semaphores:
            model_semaphores[key] = asyncio.Semaphore(api_concurrencies)
        semaphore = model_semaphores[key]
        if semaphore._value >= api_concurrencies:
            selected_platform = c["platform_name"]
            break
        elif semaphore._value > max_semaphore:
            selected_platform = c["platform_name"]

    key = (m, selected_platform)
    semaphore = model_semaphores[key]
    try:
        await semaphore.acquire()
        yield get_OpenAIClient(platform_name=selected_platform, is_async=True)
    except Exception:
        logger.error(f"failed when request to {key}", exc_info=True)
    finally:
        semaphore.release()


async def generator(request: Request, method, body: BaseModel, extra_json: Dict = {}, header: Iterable = [], tail: Iterable = []):
    params = body.model_dump(exclude_unset=True)
    delta = []
    for x in header:
        if isinstance(x, str):
            x = OpenAIChatOutput(content=x, object="chat.completion.chunk")
        elif isinstance(x, dict):
            x = OpenAIChatOutput.model_validate(x)
        else:
            raise RuntimeError(f"unsupported value: {header}")
        for k, v in extra_json.items():
            setattr(x, k, v)
        token_json = x.model_dump_json()
        delta.append(json.loads(token_json))
        yield x

    async for chunk in await method(**params):
        for k, v in extra_json.items():
            setattr(chunk, k, v)
        token_json: str = chunk.model_dump_json()
        delta.append(json.loads(token_json))
        yield chunk

    for x in tail:
        if isinstance(x, str):
            x = OpenAIChatOutput(content=x, object="chat.completion.chunk")
        elif isinstance(x, dict):
            x = OpenAIChatOutput.model_validate(x)
        else:
            raise RuntimeError(f"unsupported value: {tail}")
        for k, v in extra_json.items():
            setattr(x, k, v)
        token_json: str = x.model_dump_json()
        delta.append(json.loads(token_json))
        yield x
    # log
    logger.debug(json.dumps(delta, ensure_ascii=False, indent=2))
    await log_api_request(request, delta, params)


async def openai_request(request: Request, method, body: BaseModel, extra_json: Dict = {}, header: Iterable = [], tail: Iterable = []):
    """
    helper function to make openai request with extra fields
    """
    if hasattr(body, "stream") and body.stream:
        return EventSourceResponse(generator(request, method, body, extra_json, header, tail))
    else:
        params = body.model_dump(exclude_unset=True)
        result = await method(**params)
        for k, v in extra_json.items():
            setattr(result, k, v)
        response = result.model_dump()
        await log_api_request(request, response)
        logger.warning(response)
        return result


class Permission(BaseModel):
    created: int
    id: str
    object: str
    allow_create_engine: bool
    allow_sampling: bool
    allow_logprobs: bool
    allow_search_indices: bool
    allow_view: bool
    allow_fine_tuning: bool
    organization: str
    group: str
    is_blocking: bool


class Model(BaseModel):
    id: str
    """The model identifier, which can be referenced in the API endpoints."""

    created: Optional[int] = None
    """The Unix timestamp (in seconds) when the model was created."""

    object: Literal["model"]
    """The object type, which is always "model"."""

    owned_by: str
    """The organization that owns the model."""

    permission: Optional[List[Permission]] = None
    """The permissions that the user has for the model."""

    platform_name: str
    """The platform that owns the model."""


@app.get("/models", response_model=AsyncPage[Model])
async def list_models():
    """
    整合所有平台的模型列表。
    """

    async def task(name: str, config: Dict):
        try:
            client = get_OpenAIClient(name, is_async=True)
            models = await client.models.list()
            return [{**x.model_dump(), "platform_name": name} for x in models.data]
        except Exception:
            logger.error(f"failed request to platform: {name}", exc_info=True)
            return []

    result = []
    tasks = [asyncio.create_task(task(name, config)) for name, config in get_config_platforms().items()]
    for t in asyncio.as_completed(tasks):
        result += await t

    # return {"object": "list", "data": result}
    return AsyncPage(object="list", data=result)


@app.post("/chat/completions")
async def create_chat_completions(
    request: Request,
    body: OpenAIChatInput,
):
    logger.debug(body)
    async with get_model_client(body.model) as client:
        result = await openai_request(request, client.chat.completions.create, body)
        return result


@app.post("/completions")
async def create_completions(
    request: Request,
    body: OpenAIChatInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.completions.create, body)


@app.post("/embeddings")
async def create_embeddings(
    request: Request,
    body: OpenAIEmbeddingsInput,
):
    params = body.model_dump(exclude_unset=True)
    client = get_OpenAIClient(model_name=body.model)
    return (await client.embeddings.create(**params)).model_dump()


@app.post("/images/generations")
async def create_image_generations(
    request: Request,
    body: OpenAIImageGenerationsInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.images.generate, body)


@app.post("/images/variations")
async def create_image_variations(
    request: Request,
    body: OpenAIImageVariationsInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.images.create_variation, body)


@app.post("/images/edit")
async def create_image_edit(
    request: Request,
    body: OpenAIImageEditsInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.images.edit, body)


@app.post("/audio/translations", deprecated=True)
async def create_audio_translations(
    request: Request,
    body: OpenAIAudioTranslationsInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.audio.translations.create, body)


@app.post("/audio/transcriptions", deprecated=True)
async def create_audio_transcriptions(
    request: Request,
    body: OpenAIAudioTranscriptionsInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.audio.transcriptions.create, body)


@app.post("/audio/speech", deprecated=True)
async def create_audio_speech(
    request: Request,
    body: OpenAIAudioSpeechInput,
):
    async with get_model_client(body.model) as client:
        return await openai_request(request, client.audio.speech.create, body)


# =============================================================
# =========================== stream ==========================
# =============================================================
class ConcurrentStream:
    def __init__(self):
        self.streams: Dict[str, AsyncGenerator] = {}
        self.current: Dict[str, Any] = {}
        self.total: Dict[str, list] = defaultdict(list)
        self.finished: Set[str] = set()

    async def add(self, id, stream: AsyncGenerator):
        logger.info(f"add {id} begin")
        self.streams[id] = stream
        token_json = await stream.__anext__()
        # logger.info(f"add {id} end: {token_json}")
        self.current[id] = json.loads(token_json)
        self.total[id].append(json.loads(token_json))

    async def __aiter__(self):
        while self.current:

            yield SSEResponse(stop=False, current=self.current.copy()).model_dump_json() + "\n\n"  # 使用.copy()来避免修改原始字典
            # yield {"stop": False, "current": self.current.copy()}  # 使用.copy()来避免修改原始字典
            # json_data = {"stop": False, "current": self.current.copy()}  # 使用.copy()来避免修改原始字典
            # yield f"data: {json_data}\n\n"
            pending_ids = list(self.current.keys())
            for id in pending_ids:
                try:
                    # logger.info(f"iter {id} begin")
                    token_json = await self.streams[id].__anext__()
                    self.current[id] = json.loads(token_json)
                    # logger.info(f"iter {id} end: {token_json}")
                    self.total[id].append(json.loads(token_json))
                except StopAsyncIteration:
                    self.finished.add(id)
                except Exception as e:
                    print(e)
            for id in self.finished:
                del self.current[id]
                del self.streams[id]
            self.finished.clear()

        yield SSEResponse(stop=True, total=self.total).model_dump_json() + "\n\n"
        # json_data = {"stop": True, "total": self.total}
        # yield {"stop": True, "total": self.total}
        # yield f"data: {json_data}\n\n"


async def merged_stream(id2stream: Dict[str, AsyncGenerator]):
    concurrent_stream = ConcurrentStream()
    for i, stream in id2stream.items():
        await concurrent_stream.add(i, stream)
    print("start concurrent")
    async for token_json in concurrent_stream:
        # 使用yield from来简化迭代
        logger.info(f"merged_stream: {token_json}")
        yield token_json


class Id2ChatInput(BaseModel):
    id2input: dict[str, OpenAIChatInput]


class SSEResponse(BaseModel):
    stop: bool
    current: Dict[str, dict] = None
    total: Dict[str, List[dict]] = None


@app.post(
    "/chat/multi_completions",
    # response_class=EventSourceResponse,
    #           responses={
    #     200: {
    #         "description": "Server-Sent Events stream",
    #         "content": {
    #             "text/event-stream": {
    #                 "schema": SSEResponse
    #             }
    #         }
    #     }
    # }
)
async def create_chat_multi_completions(
    request: Request,
    body: Id2ChatInput,
):
    logger.debug(body)
    id2stream: Dict[str, AsyncGenerator] = {}
    for id, input in body.id2input.items():
        logger.debug(f"{id}: {input}")
        async with get_model_client(input.model) as client:
            method = client.chat.completions.create
            if hasattr(input, "stream") and input.stream:
                id2stream[id] = generator(request, method, input)
            else:

                async def response_generator(method, body: BaseModel):
                    params = body.model_dump(exclude_unset=True)
                    result = await method(**params)
                    response = result.model_dump()
                    yield response
                    await log_api_request(request, response, params)

                id2stream[id] = response_generator(method, input)

    # async def event_stream(id2stream):
    #     async for data in merged_stream(id2stream):
    #         if data["stop"]:
    #             response = SSEResponse(stop=True, total=data["total"])
    #         else:
    #             response = SSEResponse(stop=False, current=data["current"])
    #         yield response.model_dump_json(exclude_unset=True)
    return EventSourceResponse(merged_stream(id2stream))


# ============================================================
# =========================== files ==========================
# ============================================================


def _get_file_id(
    purpose: str,
    created_at: int,
    filename: str,
) -> str:
    today = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d")
    return base64.urlsafe_b64encode(f"{purpose}/{today}/{filename}".encode()).decode()


def _get_file_info(file_id: str) -> Dict:
    splits = base64.urlsafe_b64decode(file_id).decode().split("/")
    created_at = -1
    size = -1
    file_path = _get_file_path(file_id)
    if os.path.isfile(file_path):
        created_at = int(os.path.getmtime(file_path))
        size = os.path.getsize(file_path)

    return {
        "purpose": splits[0],
        "created_at": created_at,
        "filename": splits[2],
        "bytes": size,
    }


def _get_file_path(file_id: str) -> str:
    file_id = base64.urlsafe_b64decode(file_id).decode()
    return os.path.join(BASE_TEMP_DIR, "openai", file_id)


@app.post("/files")
async def files(
    request: Request,
    file: UploadFile,
    purpose: str = "assistants",
) -> Dict:
    created_at = int(datetime.now().timestamp())
    file_id = _get_file_id(purpose=purpose, created_at=created_at, filename=file.filename)
    file_path = _get_file_path(file_id)
    file_dir = os.path.dirname(file_path)
    os.makedirs(file_dir, exist_ok=True)
    with open(file_path, "wb") as fp:
        shutil.copyfileobj(file.file, fp)
    file.file.close()

    return dict(
        id=file_id,
        filename=file.filename,
        bytes=file.size,
        created_at=created_at,
        object="file",
        purpose=purpose,
    )


@app.get("/files")
def list_files(purpose: str) -> Dict[str, List[Dict]]:
    file_ids = []
    root_path = Path(BASE_TEMP_DIR) / "openai" / purpose
    for dir, sub_dirs, files in os.walk(root_path):
        dir = Path(dir).relative_to(root_path).as_posix()
        for file in files:
            file_id = base64.urlsafe_b64encode(f"{purpose}/{dir}/{file}".encode()).decode()
            file_ids.append(file_id)
    return {"data": [{**_get_file_info(x), "id": x, "object": "file"} for x in file_ids]}


@app.get("/files/{file_id}")
def retrieve_file(file_id: str) -> Dict:
    file_info = _get_file_info(file_id)
    return {**file_info, "id": file_id, "object": "file"}


@app.get("/files/{file_id}/content")
def retrieve_file_content(file_id: str) -> Dict:
    file_path = _get_file_path(file_id)
    return FileResponse(file_path)


@app.delete("/files/{file_id}")
def delete_file(file_id: str) -> Dict:
    file_path = _get_file_path(file_id)
    deleted = False

    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            deleted = True
    except:
        ...

    return {"id": file_id, "deleted": deleted, "object": "file"}
