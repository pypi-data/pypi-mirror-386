from cua.settings import settings

if settings.CUA_ENVIRONMENT == "development":
    from cua.logging.logging_config_dev import setup_logging
    setup_logging(level="DEBUG")
elif settings.CUA_ENVIRONMENT == "windows":
    from cua.logging.logging_config_windows import setup_logging
    setup_logging(level="DEBUG")


import logging
logger = logging.getLogger(__name__)

# Log all settings
settings.log_all()

from pathlib import Path
import time
import asyncio
import httpx
from importlib.metadata import version, PackageNotFoundError

from cua.config import get_config, init_config_from_json_file
from cua.state import state, FSMState
from cua.ai.mainloop import run_loop
from cua.db.database import init_db
from cua.utils import get_primary_ip

from cua_protocol import RegisterRequest, RegisterResponse

def get_version():
    """Get the package version"""
    try:
        return version("168x-cua")
    except PackageNotFoundError:
        return "unknown"

async def main():    
    logger.info(f"Starting CUA (version: {get_version()})")
    
    # load config until succeeded
    await initialize()
    
    # Main FSM loop
    while True:
        logger.debug(f"State data: {state.data}")
        match state.data.fsm_state:
            case FSMState.INITIALIZED:
                await register()
                
            case FSMState.REGISTERED:
                await run_loop()

async def initialize():
    """Initialize by loading configuration"""
    while True:
        if not _load_config():
            logger.info("Config not found, retrying in 1 second...")
            await asyncio.sleep(1)
        else:
            break
        
    await init_db()

def _load_config():
    path = Path(settings.CUA_ROOT_DIR) / "data" / "config.json"
    if not path.exists():
        return False
    
    logger.info(f"Loading config: {path}")
    init_config_from_json_file(path)
    return True
  

async def _register_once():
    url = f"{get_config().backend_api_base_url}/v2/agent-comm/register"
    logger.info(f"Registering with backend: {url}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            json=RegisterRequest(
                agent_instance_id=get_config().agent_instance_id,
                secret_key=get_config().secret_key,
                type=get_config().type,
                azure_vm_id=get_config().azure_vm_id,
                private_ip=get_primary_ip(),
            ).model_dump(mode="json")
        )
        response.raise_for_status()
        return RegisterResponse.model_validate(response.json()).accepted


async def register(poll_interval: float = 5):
    """Register with backend and transition to REGISTERED state"""
    while True:
        try:
            # reload config as it might have been updated
            _load_config()
            # attempting to register
            accepted = await _register_once()
        except httpx.HTTPStatusError as e:
            # Extract detailed error message from response body
            try:
                error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            logger.error(f"Error registering with backend: {error_detail} (status: {e.response.status_code})")
            await asyncio.sleep(poll_interval)
            continue
        except Exception as e:
            logger.error(f"Error registering with backend: {e}")
            await asyncio.sleep(poll_interval)
            continue
        
        if accepted:
            async with state.transaction():
                state.data.fsm_state = FSMState.REGISTERED
            logger.info("Registration accepted.")
            break
        else:
            logger.info(f"Registration not accepted. Retrying in {poll_interval} seconds...")
            await asyncio.sleep(poll_interval)

    
    


def cli():
    """CLI entry point"""
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("\nClient interrupted by user")
            exit(0)
        except Exception as e:
            logger.exception(f"Client error: {e}")
            logger.info("Restarting in 5 seconds...")
            time.sleep(5.0)


if __name__ == "__main__":
    cli()