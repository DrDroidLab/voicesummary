"""Orchestrate parallel agent comparison execution with real-time simulation"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.integrations.bolna_agent_config_fetcher import BolnaAgentConfigFetcher
from app.models import AgentComparison, AgentComparisonAggregate, AgentComparisonRun
from app.utils.conversation_simulator import ConversationSimulator
from app.utils.latency_calculator import LatencyCalculator
from app.utils.turn_accuracy_validator import TurnAccuracyValidator

logger = logging.getLogger(__name__)


class ComparisonOrchestrator:
    """Orchestrate parallel execution of agent comparison with real-time simulation"""

    def __init__(self):
        self.latency_calc = LatencyCalculator()
        try:
            self.accuracy_validator = TurnAccuracyValidator()
        except Exception as e:
            logger.warning(f"Accuracy validator not available: {e}")
            self.accuracy_validator = None

    async def execute_comparison(
        self,
        comparison_id: str,
        agent_ids: List[str],
        scenario: Dict[str, str],
        num_simulations: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Execute comparison - fetch agent configs, validate, and run N simulations per agent.

        Args:
            comparison_id: Comparison ID
            agent_ids: List of Bolna agent IDs
            scenario: Scenario configuration with user_persona, situation, etc.
            num_simulations: Number of simulations to run per agent
            db: Database session

        Returns:
            Dictionary with comparison_id, run_ids, and total_agents

        Raises:
            ValueError: If any agent is not supported (non-OpenAI models)
        """
        try:
            logger.info(
                f"Starting comparison execution for {comparison_id} with {len(agent_ids)} agents"
            )

            # Update status to running
            comparison = (
                db.query(AgentComparison)
                .filter(AgentComparison.comparison_id == comparison_id)
                .first()
            )
            comparison.status = "running"
            comparison.current_phase = "fetching_configs"
            db.commit()

            # 1. Check if we have pre-processed configs (enhanced comparison with variables)
            if "processed_agent_configs" in scenario:
                logger.info("Using pre-processed agent configs from scenario")
                configs = scenario["processed_agent_configs"]
            else:
                # Fetch all agent configs in parallel from Bolna API
                logger.info("Fetching agent configs from Bolna API")
                fetcher = BolnaAgentConfigFetcher(settings.bolna_api_key)
                configs = await asyncio.gather(
                    *[
                        asyncio.to_thread(fetcher.fetch, agent_id)
                        for agent_id in agent_ids
                    ]
                )

            # 2. Validate all agents are supported (OpenAI only)
            unsupported = [c for c in configs if not c["supported"]]
            if unsupported:
                unsupported_names = [
                    f"{c['agent_name']} ({c['llm_family']})" for c in unsupported
                ]
                raise ValueError(
                    f"Only OpenAI models supported. Unsupported agents: {', '.join(unsupported_names)}"
                )

            # 3. Extract advanced settings if provided
            advanced_settings = scenario.get("advanced_settings", {})
            max_concurrent = advanced_settings.get(
                "max_concurrent_simulations", settings.max_concurrent_simulations
            )
            timeout_seconds = advanced_settings.get(
                "conversation_timeout_seconds",
                settings.conversation_timeout_seconds,
            )
            max_turns = advanced_settings.get(
                "max_conversation_turns", settings.max_conversation_turns
            )

            if advanced_settings:
                logger.info(
                    f"Using advanced settings: concurrency={max_concurrent}, "
                    f"timeout={timeout_seconds}s, max_turns={max_turns}"
                )

            # 4. Run multiple simulations per agent in parallel
            logger.info(f"Running {num_simulations} simulations per agent")
            comparison.current_phase = "running_simulations"
            db.commit()

            aggregated_results = await asyncio.gather(
                *[
                    self._run_multi_simulation_for_agent(
                        agent_id=config["agent_id"],
                        agent_config=config,
                        scenario=scenario,
                        num_simulations=num_simulations,
                        comparison_id=comparison_id,
                        db=db,
                        max_concurrent=max_concurrent,
                        timeout_seconds=timeout_seconds,
                        max_turns=max_turns,
                    )
                    for config in configs
                ]
            )

            # 4. Store aggregate results and update comparison
            comparison.current_phase = "aggregating"
            db.commit()

            for aggregate_result in aggregated_results:
                await asyncio.to_thread(
                    self._store_aggregate_result, aggregate_result, comparison_id, db
                )

            # 5. Update comparison with final aggregated results
            comparison.current_phase = "analyzing"
            db.commit()

            self.aggregate_comparison_results(comparison_id, db)

            logger.info(f"Successfully completed comparison {comparison_id}")

            # Get all run IDs from database
            all_runs = (
                db.query(AgentComparisonRun)
                .filter(AgentComparisonRun.comparison_id == comparison_id)
                .all()
            )

            return {
                "comparison_id": comparison_id,
                "run_ids": [run.run_id for run in all_runs],
                "total_agents": len(agent_ids),
                "total_runs": len(all_runs),
                "simulations_per_agent": num_simulations,
            }

        except Exception as e:
            logger.error(f"Comparison execution failed for {comparison_id}: {e}")
            raise

    async def _process_simulation_result(
        self,
        run: AgentComparisonRun,
        agent_config: Dict[str, Any],
        simulation_result: Dict[str, Any],
        scenario: Dict[str, str],
        db: Session,
    ):
        """
        Process a single simulation result and update the run record.

        Args:
            run: The run record to update
            agent_config: Agent configuration
            simulation_result: Result from conversation simulator
            scenario: Scenario configuration
            db: Database session
        """
        try:
            run.status = "running"
            db.commit()

            # Extract simulation data
            transcript = simulation_result["transcript"]
            latencies = simulation_result["latencies"]

            # Convert latencies to structured format expected by calculator
            structured_latencies = [
                {"turn": i + 1, "latency": lat / 1000}  # Convert ms to seconds
                for i, lat in enumerate(latencies)
            ]

            # Calculate latency percentiles
            percentiles = self.latency_calc.calculate_percentiles(structured_latencies)

            # Validate accuracy and calculate outcome orientation
            accuracy_results = {}
            outcome_score = None

            if self.accuracy_validator:
                try:
                    # Validate simulated transcript
                    logger.info(f"Starting validation for run {run.run_id}")
                    # Pass transcript with turns key as expected by validator
                    transcript_with_turns = {"turns": transcript}
                    accuracy_results = (
                        await self.accuracy_validator.validate_simulated_transcript(
                            transcript=transcript_with_turns, scenario=scenario, db=db
                        )
                    )
                    logger.info(
                        f"Validation completed for run {run.run_id}, results: {accuracy_results}"
                    )

                    # Extract outcome from comprehensive validation
                    outcome_score = accuracy_results.get("outcome_orientation")
                    logger.info(f"Outcome score for run {run.run_id}: {outcome_score}")

                except Exception as e:
                    logger.error(
                        f"Validation failed for run {run.run_id}: {e}", exc_info=True
                    )
                    accuracy_results = {
                        "turn_accuracy": [],
                        "humanlike_rating": None,
                        "overall_accuracy": None,
                        "least_accurate_turns": [],
                    }
                    outcome_score = 5.0

            # Update run record
            run.simulated_transcript = transcript
            run.total_turns = simulation_result["total_turns"]
            run.turn_latencies = [
                {"turn": i + 1, "latency_ms": lat} for i, lat in enumerate(latencies)
            ]
            run.turn_accuracy = accuracy_results.get("turn_accuracy", [])
            run.latency_median = percentiles.get("median")
            run.latency_p75 = percentiles.get("p75")
            run.latency_p99 = percentiles.get("p99")
            run.overall_accuracy = accuracy_results.get("overall_accuracy")
            run.humanlike_rating = accuracy_results.get("humanlike_rating")
            run.outcome_orientation = outcome_score
            run.least_accurate_turns = accuracy_results.get("least_accurate_turns", [])
            run.status = "completed"
            run.completed_at = datetime.utcnow()

            logger.info(
                f"Processed simulation for agent {agent_config['agent_name']}: "
                f"run_id={run.run_id}, turns={run.total_turns}, outcome={outcome_score}, median_latency={run.latency_median}ms"
            )

        except Exception as e:
            logger.error(
                f"Failed to process simulation result for run {run.run_id}: {e}"
            )
            run.status = "failed"
            raise

    async def _run_multi_simulation_for_agent(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        scenario: Dict[str, str],
        num_simulations: int,
        comparison_id: str,
        db: Session,
        max_concurrent: int = None,
        timeout_seconds: int = None,
        max_turns: int = None,
    ) -> Dict[str, Any]:
        """
        Run N simulations for a single agent and aggregate results.

        Args:
            agent_id: Agent ID
            agent_config: Full agent configuration from Bolna
            scenario: Scenario configuration
            num_simulations: Number of simulations to run
            comparison_id: Comparison ID
            db: Database session

        Returns:
            Aggregated results across all simulations
        """
        # Use override values or fall back to settings
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_simulations
        if timeout_seconds is None:
            timeout_seconds = settings.conversation_timeout_seconds
        if max_turns is None:
            max_turns = settings.max_conversation_turns

        logger.info(
            f"Starting {num_simulations} simulations for agent "
            f"{agent_config['agent_name']} (concurrency={max_concurrent})"
        )

        simulator = ConversationSimulator(settings.openai_api_key)

        # Create tasks for parallel execution
        tasks = []
        for sim_num in range(1, num_simulations + 1):
            tasks.append(
                self._run_single_simulation(
                    agent_id=agent_id,
                    agent_config=agent_config,
                    scenario=scenario,
                    simulation_number=sim_num,
                    comparison_id=comparison_id,
                    simulator=simulator,
                    db=db,
                    timeout_seconds=timeout_seconds,
                    max_turns=max_turns,
                )
            )

        # Execute simulations with concurrency limit to prevent API rate limits
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(task):
            async with semaphore:
                return await task

        logger.info(
            f"Executing {num_simulations} simulations with max "
            f"{max_concurrent} concurrent"
        )
        results = await asyncio.gather(
            *[run_with_semaphore(task) for task in tasks], return_exceptions=True
        )

        # Separate successful and failed runs
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]

        if failed:
            logger.warning(
                f"{len(failed)}/{num_simulations} simulations failed for agent {agent_id}"
            )
            for exc in failed:
                logger.error(f"Simulation error: {exc}")

        if not successful:
            logger.error(f"All simulations failed for agent {agent_id}")
            return {
                "agent_id": agent_id,
                "agent_name": agent_config["agent_name"],
                "total_simulations": num_simulations,
                "successful_simulations": 0,
                "failed_simulations": num_simulations,
                "error": "All simulations failed",
            }

        # Aggregate metrics from successful runs
        aggregated = self._aggregate_simulation_results(successful)
        aggregated.update(
            {
                "agent_id": agent_id,
                "agent_name": agent_config["agent_name"],
                "total_simulations": num_simulations,
                "successful_simulations": len(successful),
                "failed_simulations": len(failed),
            }
        )

        logger.info(
            f"Completed {num_simulations} simulations for {agent_config['agent_name']}: "
            f"{len(successful)} successful, {len(failed)} failed"
        )

        return aggregated

    async def _run_single_simulation(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        scenario: Dict[str, str],
        simulation_number: int,
        comparison_id: str,
        simulator: ConversationSimulator,
        db: Session,
        timeout_seconds: int = None,
        max_turns: int = None,
    ) -> Dict[str, Any]:
        """
        Run a single simulation and store the result.

        Args:
            agent_id: Agent ID
            agent_config: Full agent configuration
            scenario: Scenario configuration
            simulation_number: Simulation number (1-indexed)
            comparison_id: Comparison ID
            simulator: ConversationSimulator instance
            db: Database session (unused, each simulation creates its own)

        Returns:
            Simulation result with metrics
        """
        # Create a new session for this simulation to avoid concurrent access issues
        session = SessionLocal()
        try:
            run_id = str(uuid.uuid4())

            # Create run record
            run = AgentComparisonRun(
                run_id=run_id,
                comparison_id=comparison_id,
                agent_id=agent_id,
                agent_name=agent_config["agent_name"],
                simulation_number=simulation_number,
                status="pending",
                agent_config=agent_config,
            )

            await asyncio.to_thread(session.add, run)
            await asyncio.to_thread(session.commit)

            try:
                # Run simulation with timeout (use override or default)
                effective_timeout = (
                    timeout_seconds
                    if timeout_seconds is not None
                    else settings.conversation_timeout_seconds
                )
                effective_max_turns = (
                    max_turns
                    if max_turns is not None
                    else settings.max_conversation_turns
                )
                simulation_result = await asyncio.wait_for(
                    simulator.simulate(
                        agent_config, scenario, max_turns=effective_max_turns
                    ),
                    timeout=effective_timeout,
                )

                # Process the result
                await self._process_simulation_result(
                    run, agent_config, simulation_result, scenario, session
                )
                await asyncio.to_thread(session.commit)

                # Return metrics for aggregation
                return {
                    "run_id": run_id,
                    "latency_median": run.latency_median,
                    "latency_p75": run.latency_p75,
                    "latency_p99": run.latency_p99,
                    "overall_accuracy": run.overall_accuracy,
                    "humanlike_rating": run.humanlike_rating,
                    "outcome_orientation": run.outcome_orientation,
                    "total_turns": run.total_turns,
                    "composite_score": self._calculate_composite_score(run),
                }

            except asyncio.TimeoutError:
                logger.error(
                    f"Simulation {simulation_number} timed out for agent {agent_id}"
                )
                run.status = "failed"
                await asyncio.to_thread(session.commit)
                raise ValueError(f"Simulation {simulation_number} timed out")
            except Exception as e:
                logger.error(
                    f"Simulation {simulation_number} failed for agent {agent_id}: {e}"
                )
                run.status = "failed"
                await asyncio.to_thread(session.commit)
                raise
        finally:
            await asyncio.to_thread(session.close)

    def _aggregate_simulation_results(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate mean, std, min, max across all simulation runs.

        Args:
            results: List of simulation results with metrics

        Returns:
            Aggregated statistics
        """
        if not results:
            return {}

        # Extract metrics from all runs
        latency_medians = [
            r["latency_median"] for r in results if r.get("latency_median") is not None
        ]
        latency_p75s = [
            r["latency_p75"] for r in results if r.get("latency_p75") is not None
        ]
        latency_p99s = [
            r["latency_p99"] for r in results if r.get("latency_p99") is not None
        ]
        accuracies = [
            r["overall_accuracy"]
            for r in results
            if r.get("overall_accuracy") is not None
        ]
        humanlikes = [
            r["humanlike_rating"]
            for r in results
            if r.get("humanlike_rating") is not None
        ]
        outcomes = [
            r["outcome_orientation"]
            for r in results
            if r.get("outcome_orientation") is not None
        ]
        turns = [r["total_turns"] for r in results if r.get("total_turns") is not None]
        composite_scores = [
            r["composite_score"]
            for r in results
            if r.get("composite_score") is not None
        ]

        # Count successful hangups (conversations that ended before max_turns)
        max_turns = settings.max_conversation_turns
        hangup_successes = sum(
            1 for r in results if r.get("total_turns", max_turns) < max_turns
        )
        hangup_rate = hangup_successes / len(results) if results else 0.0

        return {
            "latency_median_mean": (
                float(np.mean(latency_medians)) if latency_medians else None
            ),
            "latency_median_std": (
                float(np.std(latency_medians)) if latency_medians else None
            ),
            "latency_p75_mean": float(np.mean(latency_p75s)) if latency_p75s else None,
            "latency_p75_std": float(np.std(latency_p75s)) if latency_p75s else None,
            "latency_p99_mean": float(np.mean(latency_p99s)) if latency_p99s else None,
            "latency_p99_std": float(np.std(latency_p99s)) if latency_p99s else None,
            "accuracy_mean": float(np.mean(accuracies)) if accuracies else None,
            "accuracy_std": float(np.std(accuracies)) if accuracies else None,
            "accuracy_min": float(np.min(accuracies)) if accuracies else None,
            "accuracy_max": float(np.max(accuracies)) if accuracies else None,
            "humanlike_mean": float(np.mean(humanlikes)) if humanlikes else None,
            "humanlike_std": float(np.std(humanlikes)) if humanlikes else None,
            "humanlike_min": float(np.min(humanlikes)) if humanlikes else None,
            "humanlike_max": float(np.max(humanlikes)) if humanlikes else None,
            "outcome_mean": float(np.mean(outcomes)) if outcomes else None,
            "outcome_std": float(np.std(outcomes)) if outcomes else None,
            "outcome_min": float(np.min(outcomes)) if outcomes else None,
            "outcome_max": float(np.max(outcomes)) if outcomes else None,
            "composite_score_mean": (
                float(np.mean(composite_scores)) if composite_scores else None
            ),
            "composite_score_std": (
                float(np.std(composite_scores)) if composite_scores else None
            ),
            "avg_turns_mean": float(np.mean(turns)) if turns else None,
            "avg_turns_std": float(np.std(turns)) if turns else None,
            "hangup_success_rate": round(hangup_rate, 3),
        }

    def _store_aggregate_result(
        self, aggregate_data: Dict[str, Any], comparison_id: str, db: Session
    ):
        """
        Store aggregated results in the database.

        Args:
            aggregate_data: Aggregated statistics
            comparison_id: Comparison ID
            db: Database session
        """
        aggregate_id = str(uuid.uuid4())

        aggregate = AgentComparisonAggregate(
            aggregate_id=aggregate_id,
            comparison_id=comparison_id,
            agent_id=aggregate_data["agent_id"],
            agent_name=aggregate_data["agent_name"],
            total_simulations=aggregate_data["total_simulations"],
            successful_simulations=aggregate_data["successful_simulations"],
            failed_simulations=aggregate_data["failed_simulations"],
            latency_median_mean=aggregate_data.get("latency_median_mean"),
            latency_median_std=aggregate_data.get("latency_median_std"),
            latency_p75_mean=aggregate_data.get("latency_p75_mean"),
            latency_p75_std=aggregate_data.get("latency_p75_std"),
            latency_p99_mean=aggregate_data.get("latency_p99_mean"),
            latency_p99_std=aggregate_data.get("latency_p99_std"),
            accuracy_mean=aggregate_data.get("accuracy_mean"),
            accuracy_std=aggregate_data.get("accuracy_std"),
            accuracy_min=aggregate_data.get("accuracy_min"),
            accuracy_max=aggregate_data.get("accuracy_max"),
            humanlike_mean=aggregate_data.get("humanlike_mean"),
            humanlike_std=aggregate_data.get("humanlike_std"),
            humanlike_min=aggregate_data.get("humanlike_min"),
            humanlike_max=aggregate_data.get("humanlike_max"),
            outcome_mean=aggregate_data.get("outcome_mean"),
            outcome_std=aggregate_data.get("outcome_std"),
            outcome_min=aggregate_data.get("outcome_min"),
            outcome_max=aggregate_data.get("outcome_max"),
            composite_score_mean=aggregate_data.get("composite_score_mean"),
            composite_score_std=aggregate_data.get("composite_score_std"),
            avg_turns_mean=aggregate_data.get("avg_turns_mean"),
            avg_turns_std=aggregate_data.get("avg_turns_std"),
            hangup_success_rate=aggregate_data.get("hangup_success_rate"),
        )

        db.add(aggregate)
        db.commit()

        logger.info(
            f"Stored aggregate results for agent {aggregate_data['agent_name']}"
        )

    def _calculate_composite_score(self, run: AgentComparisonRun) -> float:
        """
        Calculate composite score from accuracy, humanlike, outcome, latency, and hangup.

        Weights:
        - Accuracy: 30%
        - Humanlike: 30%
        - Outcome: 30%
        - Hangup success: 10% (lower weight as requested)

        All metrics normalized to 0-10 scale.
        """
        weighted_sum = 0.0
        total_weight = 0.0

        # Accuracy: 0-1 scale -> convert to 0-10, weight 0.3
        if run.overall_accuracy is not None:
            weighted_sum += (run.overall_accuracy * 10) * 0.3
            total_weight += 0.3

        # Humanlike: already 0-10 scale, weight 0.3
        if run.humanlike_rating is not None:
            weighted_sum += run.humanlike_rating * 0.3
            total_weight += 0.3

        # Outcome: already 0-10 scale, weight 0.3
        if run.outcome_orientation is not None:
            weighted_sum += run.outcome_orientation * 0.3
            total_weight += 0.3

        # Hangup success: Binary score converted to 0-10, weight 0.1
        # 10 if conversation ended before max_turns, 0 otherwise
        if run.total_turns is not None:
            max_turns = settings.max_conversation_turns
            hangup_score = 10.0 if run.total_turns < max_turns else 0.0
            weighted_sum += hangup_score * 0.1
            total_weight += 0.1

        if total_weight == 0:
            return 0.0

        # Normalize by total weight to handle missing metrics
        return round(weighted_sum / total_weight, 2)

    async def process_run(
        self, run_id: str, call_id: str, script_turns: List[Dict[str, str]], db: Session
    ) -> Dict[str, Any]:
        """
        Legacy method for processing runs with actual call data.
        Kept for backward compatibility but not used in new scenario-based flow.
        """
        logger.warning(f"process_run called for {run_id} - this is a legacy method")
        return {
            "success": False,
            "error": "Legacy method not supported in scenario-based comparison",
        }

    def aggregate_comparison_results(
        self, comparison_id: str, db: Session
    ) -> Dict[str, Any]:
        """
        Aggregate comparison results using the aggregate records from all agents.

        Ranks agents by composite score mean from aggregated data.
        Secondary sort by latency_median_mean (lower is better).

        Args:
            comparison_id: Comparison ID
            db: Database session

        Returns:
            Aggregated results with rankings
        """
        comparison = (
            db.query(AgentComparison)
            .filter(AgentComparison.comparison_id == comparison_id)
            .first()
        )

        if not comparison:
            raise ValueError(f"Comparison {comparison_id} not found")

        aggregates = (
            db.query(AgentComparisonAggregate)
            .filter(AgentComparisonAggregate.comparison_id == comparison_id)
            .all()
        )

        if not aggregates:
            logger.warning(f"No aggregate results for comparison {comparison_id}")
            return {"error": "No aggregate results"}

        # Sort by composite score mean descending, then by latency_median_mean ascending
        sorted_aggregates = sorted(
            aggregates,
            key=lambda a: (
                a.composite_score_mean if a.composite_score_mean is not None else 0.0,
                -(a.latency_median_mean if a.latency_median_mean is not None else 999),
            ),
            reverse=True,
        )

        results = {
            "total_agents": len(aggregates),
            "simulations_per_agent": comparison.num_simulations,
            "rankings": [
                {
                    "rank": i + 1,
                    "agent_id": agg.agent_id,
                    "agent_name": agg.agent_name,
                    "total_simulations": agg.total_simulations,
                    "successful_simulations": agg.successful_simulations,
                    "failed_simulations": agg.failed_simulations,
                    "latency": {
                        "median_mean": agg.latency_median_mean,
                        "median_std": agg.latency_median_std,
                        "p75_mean": agg.latency_p75_mean,
                        "p75_std": agg.latency_p75_std,
                        "p99_mean": agg.latency_p99_mean,
                        "p99_std": agg.latency_p99_std,
                    },
                    "accuracy": {
                        "mean": agg.accuracy_mean,
                        "std": agg.accuracy_std,
                        "min": agg.accuracy_min,
                        "max": agg.accuracy_max,
                    },
                    "humanlike": {
                        "mean": agg.humanlike_mean,
                        "std": agg.humanlike_std,
                        "min": agg.humanlike_min,
                        "max": agg.humanlike_max,
                    },
                    "outcome_orientation": {
                        "mean": agg.outcome_mean,
                        "std": agg.outcome_std,
                        "min": agg.outcome_min,
                        "max": agg.outcome_max,
                    },
                    "composite_score": {
                        "mean": agg.composite_score_mean,
                        "std": agg.composite_score_std,
                    },
                    "avg_turns": {"mean": agg.avg_turns_mean, "std": agg.avg_turns_std},
                    "hangup_success_rate": agg.hangup_success_rate,
                }
                for i, agg in enumerate(sorted_aggregates)
            ],
        }

        # Analyze best agent for critical issues
        if results["rankings"]:
            from app.utils.critical_issues_analyzer import CriticalIssuesAnalyzer

            analyzer = CriticalIssuesAnalyzer()
            best_agent = results["rankings"][0]
            critical_issues = analyzer.analyze_agent(
                best_agent,
                agent_id=best_agent.get("agent_id"),
                comparison_id=comparison_id,
                db=db,
            )
            results["critical_issues"] = critical_issues
            logger.info(
                f"Identified {len(critical_issues)} critical issues in best agent {best_agent['agent_name']}"
            )

        # Update comparison
        comparison.results = results
        comparison.status = "completed"
        comparison.completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Aggregated comparison results for {comparison_id} with {results['total_agents']} agents"
        )

        return results
