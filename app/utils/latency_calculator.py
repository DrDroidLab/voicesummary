"""Calculate latency metrics from call transcripts"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import AudioCall

logger = logging.getLogger(__name__)

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning(
        "NumPy not available - latency percentiles will use " "basic calculations"
    )


class LatencyCalculator:
    """Calculate and aggregate latency metrics from calls"""

    def extract_turn_latencies(self, call_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Extract agent response latencies from a call

        Returns: [{"turn": 1, "latency": 1.2}, ...]
        """
        call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
        if not call or not call.transcript:
            logger.warning(f"Call {call_id} not found or has no transcript")
            return []

        latencies = []
        turns = call.transcript.get("turns", [])
        turn_number = 1

        for i in range(len(turns) - 1):
            current_turn = turns[i]
            next_turn = turns[i + 1]

            # Calculate latency only for USER -> AGENT transitions
            current_role = current_turn.get("role", "").upper()
            next_role = next_turn.get("role", "").upper()

            if current_role == "USER" and next_role in [
                "AGENT",
                "AGENT_SPEECH",
                "ASSISTANT",
            ]:
                user_end = current_turn.get("end_time", 0)
                agent_start = next_turn.get("start_time", 0)

                if agent_start > user_end:
                    latency = agent_start - user_end
                    latencies.append(
                        {"turn": turn_number, "latency": round(latency, 3)}
                    )
                    turn_number += 1

        logger.info(f"Extracted {len(latencies)} turn latencies from call {call_id}")
        return latencies

    def calculate_percentiles(
        self, latencies: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate latency percentiles

        Returns: {"median": float, "p75": float, "p99": float,
                  "min": float, "max": float, "avg": float}
        """
        if not latencies:
            return {
                "median": 0.0,
                "p75": 0.0,
                "p99": 0.0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
            }

        latency_values = [latency["latency"] for latency in latencies]

        if HAS_NUMPY:
            latencies_array = np.array(latency_values)

            return {
                "median": round(float(np.median(latencies_array)), 3),
                "p75": round(float(np.percentile(latencies_array, 75)), 3),
                "p99": round(float(np.percentile(latencies_array, 99)), 3),
                "min": round(float(np.min(latencies_array)), 3),
                "max": round(float(np.max(latencies_array)), 3),
                "avg": round(float(np.mean(latencies_array)), 3),
            }
        else:
            # Fallback to basic calculations without NumPy
            sorted_values = sorted(latency_values)
            n = len(sorted_values)

            def percentile(values, p):
                k = (n - 1) * p
                f = int(k)
                c = f + 1 if f + 1 < n else f
                return values[f] + (k - f) * (values[c] - values[f])

            return {
                "median": round(percentile(sorted_values, 0.50), 3),
                "p75": round(percentile(sorted_values, 0.75), 3),
                "p99": round(percentile(sorted_values, 0.99), 3),
                "min": round(min(latency_values), 3),
                "max": round(max(latency_values), 3),
                "avg": round(sum(latency_values) / len(latency_values), 3),
            }

    def aggregate_run_latencies(
        self, run_ids: List[str], db: Session
    ) -> Dict[str, float]:
        """
        Aggregate latencies across multiple test runs

        Returns: Percentiles calculated from all runs combined
        """
        from app.models import AgentComparisonRun

        all_latencies = []

        for run_id in run_ids:
            test_run = (
                db.query(AgentComparisonRun)
                .filter(AgentComparisonRun.run_id == run_id)
                .first()
            )

            if test_run and test_run.call_id and test_run.status == "completed":
                turn_latencies = self.extract_turn_latencies(test_run.call_id, db)
                all_latencies.extend(turn_latencies)

        logger.info(
            f"Aggregated {len(all_latencies)} latencies " f"from {len(run_ids)} runs"
        )
        return self.calculate_percentiles(all_latencies)
