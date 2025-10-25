import logging
logger = logging.getLogger(__name__)


from sqlalchemy import select

from cua.state import state

from cua.db.database import get_session
from cua.db.models import DB_Step, DB_AgentLoop
from cua.ai.tool_box import ToolBox
from cua.ai.tools.linkedin_crustdata import LinkedInTool
from cua.ai.tools.computer_use import ComputerUseTool
from cua.ai.tools.subagent_legacy import LegacySubAgentTool

from cua.ai.loop import load_steps, checkin, llm_call, get_next_tool_call, run_tool_call, refresh_latest_step, clean_up_context


MAIN_LOOP_ID = 0 # default for main loop

async def run_loop():
    # check if main loop and initial step exists, if not, create them
    await _ensure_main_loop_exists()
    
    # load all steps from main loop
    steps = await load_steps(MAIN_LOOP_ID)
        
    tool_box = ToolBox()
    # tool_box.register_tool(LinkedInTool())
    # tool_box.register_tool(ComputerUseTool())
    # tool_box.register_tool(SubAgentTool())
    tool_box.register_tool(LegacySubAgentTool())
        
    while True:
        await checkin(steps, tool_box)
        await llm_call(_compile_system_prompt(), steps, tool_box)

        async for tool in get_next_tool_call(steps):
            await checkin(steps, tool_box)
            await run_tool_call(tool, tool_box)
        
        # need to refresh latest step since tool calls may have modified it
        await refresh_latest_step(steps)
        
        await clean_up_context(steps, n_images_to_keep=10)
            

async def _ensure_main_loop_exists():
    async with get_session() as session:
        # check if loop exists, if not, create it
        result = await session.execute(
            select(DB_AgentLoop)
            .where(DB_AgentLoop.id == MAIN_LOOP_ID))
        loop = result.scalar_one_or_none()
        if loop is None:
            loop = DB_AgentLoop(id=MAIN_LOOP_ID, name="MainLoop")
            session.add(loop)
            await session.commit()
    
        # count steps
        from sqlalchemy import func
        result = await session.execute(
            select(func.count())
            .select_from(DB_Step)
            .where(DB_Step.agent_loop_id == MAIN_LOOP_ID))
        step_count = result.scalar()
        
        # if no steps, create initial step
        if step_count == 0:
            initial_step = DB_Step(agent_loop_id=MAIN_LOOP_ID, sequence=1)
            session.add(initial_step)
            await session.commit()
            
            
def _compile_system_prompt() -> str:
    return state.data.last_checkin_response.system_prompt + f"\n<workflows>\n{state.data.last_checkin_response.legacy_subagent_workflows}\n</workflows>"