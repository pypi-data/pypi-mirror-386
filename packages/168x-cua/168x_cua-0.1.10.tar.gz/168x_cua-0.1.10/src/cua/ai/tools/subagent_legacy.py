import logging
logger = logging.getLogger(__name__)

import asyncio
from pydantic import BaseModel, Field

from cua.ai.tool_box import ToolBox, Tool, ToolResult
from cua.ai.tools.computer_use import ComputerUseTool

from cua.ai.loop import load_steps, checkin, llm_call, get_next_tool_call, run_tool_call, refresh_latest_step, clean_up_context
from cua.db.database import get_session
from cua.db.models import DB_AgentLoop, DB_Step, RequestContent, ContentType, ContentBlock

from cua.state import state

class LegacySubAgentArgs(BaseModel):
    title: str = Field(description="Short 3-5 keyword description of the goal. This is only to inform the user of what is happening.")
    step_name: str = Field(description="Name of the step as defined in the <workflows>.")
    input_data: str | None = Field(default=None, description="Input data for the step. Preferably in JSON format.")

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


class LegacySubAgentTool(Tool):
    def __init__(self):
        super().__init__(
            name="run_step",
            description="Runs a step of a workflow",
            input_model=LegacySubAgentArgs,
        )
        
        
    def get_ui_tool_name(self, args) -> str:
        return f"{args.title}"
    

    async def __call__(self, args: LegacySubAgentArgs) -> ToolResult:
        system_prompt = SYSTEM_PROMPT.format(workflows=state.data.last_checkin_response.legacy_subagent_workflows)
        input_message = INPUT_MESSAGE_TEMPLATE.format(step_name=args.step_name, input_data=args.input_data)
        
        response_text = await _run_subagent_until_end_turn(system_prompt, input_message)
        
        return ToolResult(text=response_text)
    
    
async def _run_subagent_until_end_turn(system_prompt: str, input_message: str) -> str:    
    # initialize new loop
    loop = await _init_new_subagent_loop(input_message)
    
    # hardcode toolbox for now
    tool_box = ToolBox()
    tool_box.register_tool(ComputerUseTool())
    
    # create new loop with inital step
    steps = await load_steps(loop.id)
    
    try:
        while True:
            await checkin(steps, tool_box, subagent_mode=True)
            await llm_call(system_prompt, steps, tool_box, subagent_mode=True)

            async for tool in get_next_tool_call(steps):
                await checkin(steps, tool_box, subagent_mode=True)
                await run_tool_call(tool, tool_box)
            
            # need to refresh latest step since tool calls may have modified it
            await refresh_latest_step(steps)
        
            # If end turn, return response text
            if steps[-1].end_turn:
                return steps[-1].response_text
            
            await clean_up_context(steps, n_images_to_keep=10)
    except asyncio.CancelledError:
        logger.info("Subagent was aborted by user")
        return "Subagent did not finish (aborted by user). Last message from subagent: " + steps[-1].response_text

async def _init_new_subagent_loop(message: str) -> DB_AgentLoop:
    async with get_session() as session:
        loop = DB_AgentLoop(name="LegacySubagent")
        session.add(loop)
        await session.flush() # get the id
        
        # create initial step
        initial_step = DB_Step(agent_loop_id=loop.id, sequence=1)
        initial_step.request_content = RequestContent(content_list=[ContentBlock(type=ContentType.TEXT, content=message)])
        session.add(initial_step)
        
        # commit
        await session.commit()
        
        return loop