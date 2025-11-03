"""API endpoints for agent comparison"""

import asyncio
import io
import json
import logging
import uuid
import zipfile
from datetime import datetime
from typing import List

import requests
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.integrations.bolna_agent_config_fetcher import BolnaAgentConfigFetcher
from app.models import AgentComparison, AgentComparisonRun
from app.schemas import (
    AgentComparisonCreate,
    AgentComparisonCreateEnhanced,
    AgentComparisonResponse,
    AgentComparisonRunResponse,
    AgentConfigResponse,
    AgentLookupResponse,
    AgentWithVariables,
    ManualAgentCreate,
)
from app.utils.comparison_orchestrator import ComparisonOrchestrator
from app.utils.scenario_validator import ScenarioValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["agent-comparison"])


@router.get("/agents/{agent_id}", response_model=AgentLookupResponse)
async def lookup_agent(agent_id: str):
    """
    Lookup agent details from Bolna API

    Returns: {"agent_id": str, "agent_name": str, "status": str}
    """
    try:
        if not settings.bolna_api_key:
            raise HTTPException(status_code=500, detail="Bolna API key not configured")

        headers = {
            "Authorization": f"Bearer {settings.bolna_api_key}",
            "Content-Type": "application/json",
        }

        response = requests.get("https://api.bolna.ai/agent/all", headers=headers)
        response.raise_for_status()
        agents = response.json()

        # Find agent by ID
        agent = next(
            (
                a
                for a in agents
                if a.get("id") == agent_id or a.get("agent_id") == agent_id
            ),
            None,
        )

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found in Bolna")

        return AgentLookupResponse(
            agent_id=agent_id,
            agent_name=agent.get("agent_name", agent_id),
            status=agent.get("status", "unknown"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent lookup failed for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/config", response_model=AgentConfigResponse)
async def get_agent_config(agent_id: str):
    """
    Fetch full agent configuration from Bolna

    Returns: Full agent config with system_prompt, hangup_prompt, LLM settings, and supported status
    """
    try:
        if not settings.bolna_api_key:
            raise HTTPException(status_code=500, detail="Bolna API key not configured")

        fetcher = BolnaAgentConfigFetcher(settings.bolna_api_key)
        config = fetcher.fetch(agent_id)

        return AgentConfigResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent config fetch failed for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dead code - script validation not used in scenario-based comparison
# @router.post("/validate-script")
# async def validate_script(script_content: str = Body(..., embed=True)):
#     """
#     Validate multi-turn script format
#
#     Returns: {"is_valid": bool, "error": str | None, "turns": list, "turn_count": int}
#     """
#     is_valid, error, turns = ScriptValidator.validate_script(script_content)
#
#     return {
#         "is_valid": is_valid,
#         "error": error if not is_valid else None,
#         "turns": turns,
#         "turn_count": len(turns),
#     }


@router.post("/comparisons/detect-variables", response_model=List[AgentWithVariables])
async def detect_variables(
    bolna_agent_ids: List[str] = Body(default=None),
    manual_agents: List[ManualAgentCreate] = Body(default=None),
):
    """
    Detect all variables needed across all agents

    Returns list of agents with their required variables
    """
    from app.integrations.manual_agent_manager import ManualAgentManager
    from app.utils.variable_replacer import VariableReplacer

    if not bolna_agent_ids and not manual_agents:
        raise HTTPException(
            status_code=400,
            detail="Must provide either bolna_agent_ids or manual_agents",
        )

    results = []

    # Process Bolna agents
    if bolna_agent_ids:
        if not settings.bolna_api_key:
            raise HTTPException(status_code=500, detail="Bolna API key not configured")

        fetcher = BolnaAgentConfigFetcher(settings.bolna_api_key)
        for agent_id in bolna_agent_ids:
            config = fetcher.fetch(agent_id)
            if config["supported"]:
                variables = VariableReplacer.detect_config_variables(config)
                results.append(
                    AgentWithVariables(
                        agent_id=agent_id,
                        agent_name=config["agent_name"],
                        config=config,
                        required_variables=sorted(list(variables)),
                    )
                )

    # Process manual agents
    if manual_agents:
        for manual in manual_agents:
            config = ManualAgentManager.create_agent_config(
                agent_name=manual.agent_name,
                welcome_message=manual.welcome_message,
                system_prompt=manual.system_prompt,
                hangup_prompt=manual.hangup_prompt,
                llm_model=manual.llm_model,
                temperature=manual.temperature,
                max_tokens=manual.max_tokens,
            )
            variables = VariableReplacer.detect_config_variables(config)
            results.append(
                AgentWithVariables(
                    agent_id=config["agent_id"],
                    agent_name=config["agent_name"],
                    config=config,
                    required_variables=sorted(list(variables)),
                )
            )

    logger.info(f"Detected variables for {len(results)} agents")
    return results


@router.post(
    "/comparisons",
    response_model=AgentComparisonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comparison(
    comparison_data: AgentComparisonCreate, db: Session = Depends(get_db)
):
    """
    Create new agent comparison (legacy - Bolna IDs only)

    Validates scenario and creates comparison record
    """
    # Build scenario config
    scenario_config = {
        "agent_overview": comparison_data.agent_overview,
        "user_persona": comparison_data.user_persona,
        "situation": comparison_data.situation,
        "primary_language": comparison_data.primary_language,
        "expected_outcome": comparison_data.expected_outcome,
    }

    # Validate scenario
    is_valid, error = ScenarioValidator.validate_scenario(scenario_config)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid scenario: {error}")

    # Create comparison
    comparison_id = str(uuid.uuid4())
    comparison = AgentComparison(
        comparison_id=comparison_id,
        name=comparison_data.name,
        scenario_config=scenario_config,
        agent_ids=comparison_data.agent_ids,
        num_simulations=comparison_data.num_simulations,
        status="pending",
    )

    db.add(comparison)
    db.commit()
    db.refresh(comparison)

    logger.info(
        f"Created comparison {comparison_id} with {len(comparison_data.agent_ids)} agents, {comparison_data.num_simulations} simulations each"
    )

    return comparison


@router.post(
    "/comparisons/enhanced",
    response_model=AgentComparisonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comparison_enhanced(
    comparison_data: AgentComparisonCreateEnhanced, db: Session = Depends(get_db)
):
    """
    Create new agent comparison with variable replacement support

    Supports both Bolna agents and manually created agents
    Variables are replaced before execution
    """
    try:
        from app.integrations.manual_agent_manager import ManualAgentManager
        from app.utils.variable_replacer import VariableReplacer

        if not comparison_data.bolna_agent_ids and not comparison_data.manual_agents:
            raise HTTPException(
                status_code=400,
                detail="Must provide either bolna_agent_ids or manual_agents",
            )

        # Build scenario config
        scenario_config = {
            "agent_overview": comparison_data.agent_overview,
            "user_persona": comparison_data.user_persona,
            "situation": comparison_data.situation,
            "primary_language": comparison_data.primary_language,
            "expected_outcome": comparison_data.expected_outcome,
        }

        # Validate scenario
        is_valid, error = ScenarioValidator.validate_scenario(scenario_config)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid scenario: {error}")

        # Fetch/create all agent configs
        agent_configs = []
        agent_ids = []

        if comparison_data.bolna_agent_ids:
            if not settings.bolna_api_key:
                raise HTTPException(
                    status_code=500, detail="Bolna API key not configured"
                )

            fetcher = BolnaAgentConfigFetcher(settings.bolna_api_key)
            for agent_id in comparison_data.bolna_agent_ids:
                config = fetcher.fetch(agent_id)
                if not config["supported"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent {agent_id} uses unsupported LLM family: {config['llm_family']}",
                    )
                agent_configs.append(config)
                agent_ids.append(agent_id)

        if comparison_data.manual_agents:
            for manual in comparison_data.manual_agents:
                config = ManualAgentManager.create_agent_config(
                    agent_name=manual.agent_name,
                    welcome_message=manual.welcome_message,
                    system_prompt=manual.system_prompt,
                    hangup_prompt=manual.hangup_prompt,
                    llm_model=manual.llm_model,
                    temperature=manual.temperature,
                    max_tokens=manual.max_tokens,
                )
                agent_configs.append(config)
                agent_ids.append(config["agent_id"])

        # Replace variables in all configs BEFORE storing
        processed_configs = []
        for config in agent_configs:
            processed = VariableReplacer.replace_config_variables(
                config, comparison_data.variable_values
            )
            processed_configs.append(processed)

        # Store processed configs as JSON in the comparison record
        # We'll store them in scenario_config for now
        scenario_config["processed_agent_configs"] = processed_configs

        # Store advanced settings if provided
        advanced_settings = {}
        if comparison_data.max_concurrent_simulations is not None:
            advanced_settings["max_concurrent_simulations"] = (
                comparison_data.max_concurrent_simulations
            )
        if comparison_data.conversation_timeout_seconds is not None:
            advanced_settings["conversation_timeout_seconds"] = (
                comparison_data.conversation_timeout_seconds
            )
        if comparison_data.max_conversation_turns is not None:
            advanced_settings["max_conversation_turns"] = (
                comparison_data.max_conversation_turns
            )

        if advanced_settings:
            scenario_config["advanced_settings"] = advanced_settings
            logger.info(f"Using advanced settings: {advanced_settings}")

        # Create comparison
        comparison_id = str(uuid.uuid4())
        comparison = AgentComparison(
            comparison_id=comparison_id,
            name=comparison_data.name,
            scenario_config=scenario_config,
            agent_ids=agent_ids,
            num_simulations=comparison_data.num_simulations,
            status="pending",
        )

        db.add(comparison)
        db.commit()
        db.refresh(comparison)

        logger.info(
            f"Created enhanced comparison {comparison_id} with {len(agent_ids)} agents, {comparison_data.num_simulations} simulations each"
        )
        logger.info(
            f"Replaced {len(comparison_data.variable_values)} variables in agent configs"
        )

        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced comparison creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparisons/{comparison_id}/execute")
async def execute_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """
    Execute comparison - fire and forget background task

    Returns immediately with status, frontend polls /status endpoint for progress

    Returns: {"comparison_id": str, "status": "running"}
    """
    import asyncio

    from app.database import SessionLocal

    comparison = (
        db.query(AgentComparison)
        .filter(AgentComparison.comparison_id == comparison_id)
        .first()
    )

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Validate scenario
    is_valid, error = ScenarioValidator.validate_scenario(comparison.scenario_config)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid scenario: {error}")

    # Fire and forget - execute in background
    async def background_execution():
        # Create new db session for background task
        bg_db = SessionLocal()
        try:
            orchestrator = ComparisonOrchestrator()
            await orchestrator.execute_comparison(
                comparison_id=comparison_id,
                agent_ids=comparison.agent_ids,
                scenario=comparison.scenario_config,
                num_simulations=comparison.num_simulations,
                db=bg_db,
            )
            logger.info(f"Background execution completed for {comparison_id}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(
                f"Background execution failed for {comparison_id}: {error_msg}",
                exc_info=True,
            )
            # Update comparison status to failed
            comp = (
                bg_db.query(AgentComparison)
                .filter(AgentComparison.comparison_id == comparison_id)
                .first()
            )
            if comp:
                comp.status = "failed"
                comp.error_message = error_msg
                bg_db.commit()
        finally:
            bg_db.close()

    # Start background task
    asyncio.create_task(background_execution())

    logger.info(f"Started background execution for comparison {comparison_id}")

    return {"comparison_id": comparison_id, "status": "running"}


@router.post("/comparisons/{comparison_id}/rerun")
async def rerun_comparison(
    comparison_id: str,
    num_simulations: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Re-run an existing comparison with the same configuration.

    Creates a new comparison with identical scenario and agents but fresh execution.
    Useful for re-testing agents or verifying consistency.

    Args:
        comparison_id: ID of existing comparison to re-run
        num_simulations: Optional override for number of simulations (uses original if not provided)
        db: Database session

    Returns:
        ExecuteComparisonResponse with new comparison_id and status
    """
    # Fetch existing comparison
    existing = (
        db.query(AgentComparison)
        .filter(AgentComparison.comparison_id == comparison_id)
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Validate existing comparison is completed or failed
    if existing.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot rerun comparison with status '{existing.status}'. Only completed or failed comparisons can be rerun.",
        )

    # Create new comparison with same configuration
    new_comparison_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{existing.name} (Rerun {timestamp})"

    new_comparison = AgentComparison(
        comparison_id=new_comparison_id,
        name=new_name,
        created_by=existing.created_by,
        scenario_config=existing.scenario_config,
        agent_ids=existing.agent_ids,
        num_simulations=num_simulations or existing.num_simulations,
        status="pending",
    )

    db.add(new_comparison)
    db.commit()
    db.refresh(new_comparison)

    logger.info(
        f"Created rerun comparison {new_comparison_id} from {comparison_id} with name: {new_name}"
    )

    # Start orchestrator for new comparison
    orchestrator = ComparisonOrchestrator()

    async def background_execution():
        bg_db = SessionLocal()
        try:
            await orchestrator.execute_comparison(
                comparison_id=new_comparison_id,
                agent_ids=new_comparison.agent_ids,
                scenario=new_comparison.scenario_config,
                num_simulations=new_comparison.num_simulations,
                db=bg_db,
            )
            logger.info(f"Background execution completed for rerun {new_comparison_id}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(
                f"Background execution failed for rerun {new_comparison_id}: {error_msg}",
                exc_info=True,
            )
            comp = (
                bg_db.query(AgentComparison)
                .filter(AgentComparison.comparison_id == new_comparison_id)
                .first()
            )
            if comp:
                comp.status = "failed"
                comp.error_message = error_msg
                bg_db.commit()
        finally:
            bg_db.close()

    asyncio.create_task(background_execution())

    logger.info(f"Started background execution for rerun {new_comparison_id}")

    return {"comparison_id": new_comparison_id, "status": "running"}


# Dead code - process_run endpoint not used in scenario-based comparison
# @router.post("/runs/{run_id}/process")
# async def process_run(
#     run_id: str, call_id: str = Body(..., embed=True), db: Session = Depends(get_db)
# ):
#     """
#     Process completed run - calculates latencies and validates accuracy
#
#     Args:
#         run_id: Test run ID
#         call_id: Associated call ID
#
#     Returns: {"success": bool, "run": dict | None, "error": str | None}
#     """
#     run = (
#         db.query(AgentComparisonRun).filter(AgentComparisonRun.run_id == run_id).first()
#     )
#
#     if not run:
#         raise HTTPException(status_code=404, detail="Run not found")
#
#     comparison = (
#         db.query(AgentComparison)
#         .filter(AgentComparison.comparison_id == run.comparison_id)
#         .first()
#     )
#
#     if not comparison:
#         raise HTTPException(status_code=404, detail="Comparison not found")
#
#     is_valid, error, turns = ScriptValidator.validate_script(comparison.script_content)
#     if not is_valid:
#         raise HTTPException(status_code=400, detail=f"Invalid script: {error}")
#
#     orchestrator = ComparisonOrchestrator()
#     result = await orchestrator.process_run(run_id, call_id, turns, db)
#
#     if not result["success"]:
#         raise HTTPException(
#             status_code=500, detail=result.get("error", "Processing failed")
#         )
#
#     logger.info(f"Processed run {run_id} with call {call_id}")
#
#     return result


@router.get("/comparisons/{comparison_id}/results")
async def get_comparison_results(comparison_id: str, db: Session = Depends(get_db)):
    """
    Get aggregated comparison results

    Returns: {"total_agents": int, "rankings": list}
    """
    comparison = (
        db.query(AgentComparison)
        .filter(AgentComparison.comparison_id == comparison_id)
        .first()
    )

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if comparison.results:
        return comparison.results

    # Aggregate if not already done
    orchestrator = ComparisonOrchestrator()
    results = orchestrator.aggregate_results(comparison_id, db)

    logger.info(
        f"Retrieved comparison results for {comparison_id} with {results.get('total_agents', 0)} agents"
    )

    return results


@router.get("/comparisons/{comparison_id}/transcripts/download")
async def download_transcripts(comparison_id: str, db: Session = Depends(get_db)):
    """
    Download all transcripts for a comparison as a ZIP file

    Returns: ZIP file with transcripts named {agent_name}_sim{simulation_number}.json
    """
    comparison = (
        db.query(AgentComparison)
        .filter(AgentComparison.comparison_id == comparison_id)
        .first()
    )

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Get all runs with transcripts
    runs = (
        db.query(AgentComparisonRun)
        .filter(
            AgentComparisonRun.comparison_id == comparison_id,
            AgentComparisonRun.status == "completed",
            AgentComparisonRun.simulated_transcript.isnot(None),
        )
        .all()
    )

    if not runs:
        raise HTTPException(
            status_code=404, detail="No transcripts found for this comparison"
        )

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for run in runs:
            # Create filename: agent_name_sim1.json
            agent_name = (
                run.agent_name.replace(" ", "_").replace("/", "_")
                if run.agent_name
                else run.agent_id
            )
            filename = f"{agent_name}_sim{run.simulation_number}.json"

            # Add transcript to ZIP
            transcript_json = json.dumps(run.simulated_transcript, indent=2)
            zip_file.writestr(filename, transcript_json)

    # Reset buffer position
    zip_buffer.seek(0)

    logger.info(
        f"Generated transcript ZIP for comparison {comparison_id} with {len(runs)} transcripts"
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=comparison_{comparison_id}_transcripts.zip"
        },
    )


@router.get("/comparisons", response_model=List[AgentComparisonResponse])
async def list_comparisons(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    """
    List all comparisons with pagination

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return (max 100)

    Returns: List of comparison records
    """
    limit = min(limit, 100)  # Cap at 100

    comparisons = (
        db.query(AgentComparison)
        .order_by(AgentComparison.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return comparisons


@router.get("/comparisons/{comparison_id}", response_model=AgentComparisonResponse)
async def get_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """
    Get a specific comparison by ID

    Returns: Comparison details
    """
    comparison = (
        db.query(AgentComparison)
        .filter(AgentComparison.comparison_id == comparison_id)
        .first()
    )

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    return comparison


@router.get("/runs/{run_id}", response_model=AgentComparisonRunResponse)
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """
    Get a specific run by ID

    Returns: Run details with metrics
    """
    run = (
        db.query(AgentComparisonRun).filter(AgentComparisonRun.run_id == run_id).first()
    )

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return run


@router.get("/comparisons/{comparison_id}/status")
async def get_comparison_status(comparison_id: str, db: Session = Depends(get_db)):
    """
    Get real-time status of comparison execution

    Returns: {
        "status": "running" | "completed" | "failed" | "pending",
        "current_phase": "fetching_configs" | "running_simulations" | "aggregating" | "analyzing" | "completed",
        "total_runs": int,
        "completed_runs": int,
        "failed_runs": int,
        "agents_in_progress": [{"agent_id": str, "agent_name": str}]
    }
    """
    comparison = (
        db.query(AgentComparison)
        .filter(AgentComparison.comparison_id == comparison_id)
        .first()
    )

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Get run statistics
    runs = (
        db.query(AgentComparisonRun)
        .filter(AgentComparisonRun.comparison_id == comparison_id)
        .all()
    )

    # Always use expected total from configuration
    # This ensures denominator never shows less than actual runs started
    num_agents = len(comparison.agent_ids)
    total_runs = num_agents * comparison.num_simulations

    completed_runs = sum(1 for r in runs if r.status == "completed")
    failed_runs = sum(1 for r in runs if r.status == "failed")

    # Get agents currently in progress
    running_runs = [r for r in runs if r.status == "running"]
    agents_in_progress = [
        {"agent_id": r.agent_id, "agent_name": r.agent_name} for r in running_runs
    ]

    # Remove duplicates based on agent_id
    seen = set()
    unique_agents = []
    for agent in agents_in_progress:
        if agent["agent_id"] not in seen:
            seen.add(agent["agent_id"])
            unique_agents.append(agent)

    return {
        "status": comparison.status,
        "current_phase": comparison.current_phase,
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "agents_in_progress": unique_agents,
    }
