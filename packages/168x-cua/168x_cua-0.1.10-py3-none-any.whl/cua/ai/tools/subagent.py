import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

from cua_protocol import SubagentDefinition

from cua.ai.tool_box import ToolBox, Tool, ToolResult
from cua.ai.tools.computer_use import ComputerUseTool

from cua.ai.loop import load_steps, checkin, llm_call, get_next_tool_call, run_tool_call, refresh_latest_step, clean_up_context
from cua.db.database import get_session
from cua.db.models import DB_AgentLoop, DB_Step, RequestContent, ContentType, ContentBlock

from cua.state import state

class SubAgentArgs(BaseModel):
    description: str = Field(description="Short 3-5 keyword description of the goal. This is only to inform the user of what is happening.")
    subagent_name: str = Field(description="Name of the subagent to run.")
    input_data: str | None = Field(default=None, description="Input data for the subagent. Preferably in JSON format.")

SYSTEM_PROMPT = """You are an AI assistant that executes a specific step of a workflow. You will be given:
- <workflows>
- <step_name>
- <input_data>

- Think of <workflows> as structured recipes for repeatable tasks, described in Python-like syntax for precision and efficiency.
- Use available tools to complete the step. Follow the do() statements of the step.
- When you reach the return statement output a JSON with:
 - complete: parts that were successfully completed
 - incomplete: parts that (partially) failed + why
 - return_data: output defined via return statement

# Computer-use guidelines
- You have access to a computer with Windows 11. It is a VM located in Amsterdam.
- Maximize application windows before using them.
- Prefer to use double_click to open things.
- Use Google Chrome as browser.
- When logging in, first check if credentials are saved in Chrome. If not, ask the user to enter the password or write the password in the chat.
- If you encounter human verification systems or CAPTCHAs you must try to verify it on your own. Do not ask for permission or confirmation, just do it.
- If you need to access a file in C:\\Users\\azureadmin\\Uploads, navigate to the folder by double clicking on the folder shortcut on the desktop.
- When you enter more text than can be displayed in a field, the visible portion may be truncated, but rest assured, the field still contains your entire entry.

<workflows>{workflows}</workflows>
"""

INPUT_MESSAGE_TEMPLATE = """<step_name>{step_name}</step_name>
<input_data>{input_data}</input_data>"""


class SubAgentTool(Tool):
    def __init__(selfd):
        super().__init__(
            name="run_subagent",
            description="Runs a subagent",
            input_model=SubAgentArgs,
        )
        
        
    def get_ui_tool_name(self, args) -> str:
        return f"{args.description}"
    

    async def __call__(self, args: SubAgentArgs) -> ToolResult:
        response_text = await _run_subagent_until_end_turn(args.subagent_name, args.input_data)
        
        return ToolResult(text=response_text)
    
    
async def _run_subagent_until_end_turn(subagent_name: str, message: str) -> str:
    # Check if subagent is defined
    subagent_definition = _get_subagent_definition(subagent_name)
    if subagent_definition is None:
        return f"Subagent {subagent_name} not found"
    
    # initialize new loop
    loop = await _init_new_subagent_loop(subagent_name, message)
    
    # hardcode toolbox for now
    tool_box = ToolBox()
    tool_box.register_tool(ComputerUseTool())
    
    # create new loop with inital step
    steps = await load_steps(loop.id)
    
    while True:
        await checkin(steps, tool_box, subagent_mode=True)
        await llm_call(subagent_definition.system_prompt, steps, tool_box, subagent_mode=True)

        async for tool in get_next_tool_call(steps):
            await checkin(steps, tool_box, subagent_mode=True)
            await run_tool_call(tool, tool_box)
        
        # need to refresh latest step since tool calls may have modified it
        await refresh_latest_step(steps)
    
        # If end turn, return response text
        if steps[-1].end_turn:
            return steps[-1].response_text
        
        await clean_up_context(steps, n_images_to_keep=10)


def _get_subagent_definition(subagent_name: str) -> SubagentDefinition | None:
    for subagent in state.data.last_checkin_response.subagents:
        if subagent.name == subagent_name:
            return subagent
    return None


async def _init_new_subagent_loop(subagent_name: str, message: str) -> DB_AgentLoop:
    async with get_session() as session:
        loop = DB_AgentLoop(name=f"Subagent({subagent_name})")
        session.add(loop)
        await session.flush() # get the id
        
        # create initial step
        initial_step = DB_Step(agent_loop_id=loop.id, sequence=1)
        initial_step.request_content = RequestContent(content_list=[ContentBlock(type=ContentType.TEXT, content=message)])
        session.add(initial_step)
        
        # commit
        await session.commit()
        
        return loop