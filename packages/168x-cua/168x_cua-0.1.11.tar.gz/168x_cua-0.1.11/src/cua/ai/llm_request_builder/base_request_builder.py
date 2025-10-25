from abc import ABC, abstractmethod

from cua_protocol.schemas import LLMRequest

from cua.db.models import DB_Step
from cua.ai.tool_box import ToolBox


class BaseRequestBuilder(ABC): 
    
    @abstractmethod
    async def build_request(
        self, 
        steps: list[DB_Step], 
        tool_box: ToolBox, 
        system_prompt: str
    ) -> LLMRequest:
        raise NotImplementedError