import logging
logger = logging.getLogger(__name__)

from anthropic.types.beta import BetaMessage
import httpx

from cua.config import get_config

from cua_protocol.schemas import LLMRequest, BaseLLMResponse

TIMEOUT = 10 * 60 # 10 minutes
ENDPOINT = "/llm"


async def make_request(request: LLMRequest) -> BaseLLMResponse:
    config = get_config()
    
    # make http request
    response = await httpx.AsyncClient(timeout=TIMEOUT).post(
        config.backend_api_base_url + ENDPOINT,
        json=request.model_dump(mode="json")
    )
    response.raise_for_status()
    return BaseLLMResponse.model_validate(response.json())