"""
Critical Issues Analyzer for Agent Comparison Results

Analyzes the best performing agent and identifies top 3 critical issues
that need immediate attention for improvement.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CriticalIssuesAnalyzer:
    """Analyze agent metrics and identify critical issues requiring immediate fixes"""

    ACCURACY_THRESHOLD_CRITICAL = 0.5
    ACCURACY_THRESHOLD_HIGH = 0.7
    HANGUP_RATE_THRESHOLD_CRITICAL = 0.4
    HANGUP_RATE_THRESHOLD_HIGH = 0.6
    LATENCY_P99_THRESHOLD_HIGH = 3.0
    HUMANLIKE_THRESHOLD_MEDIUM = 5.0
    OUTCOME_THRESHOLD_MEDIUM = 7.0
    ZERO_VARIANCE_THRESHOLD = 0.001

    def analyze_agent(
        self,
        agent_ranking: Dict[str, Any],
        agent_id: str = None,
        comparison_id: str = None,
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single agent and return top 3 critical issues.

        Args:
            agent_ranking: Agent ranking dictionary with all metrics
            agent_id: Agent ID for fetching turn-level data
            comparison_id: Comparison ID for fetching turn-level data
            db: Database session for fetching turn-level data

        Returns:
            List of critical issues (max 3), sorted by severity
        """
        issues = []

        # Check hangup success rate
        hangup_issue = self._check_hangup_rate(agent_ranking)
        if hangup_issue:
            issues.append(hangup_issue)

        # Check accuracy with turn-level examples
        accuracy_issue = self._check_accuracy(
            agent_ranking, agent_id, comparison_id, db
        )
        if accuracy_issue:
            issues.append(accuracy_issue)

        # Check for zero variance (duplicate data issues)
        variance_issue = self._check_zero_variance(agent_ranking)
        if variance_issue:
            issues.append(variance_issue)

        # Check latency
        latency_issue = self._check_latency(agent_ranking)
        if latency_issue:
            issues.append(latency_issue)

        # Check humanlike score
        humanlike_issue = self._check_humanlike(agent_ranking)
        if humanlike_issue:
            issues.append(humanlike_issue)

        # Check outcome orientation
        outcome_issue = self._check_outcome(agent_ranking)
        if outcome_issue:
            issues.append(outcome_issue)

        # Sort by severity (critical > high > medium) and return top 3
        severity_order = {"critical": 0, "high": 1, "medium": 2}
        sorted_issues = sorted(issues, key=lambda x: severity_order[x["severity"]])

        logger.info(
            f"Found {len(issues)} issues for agent {agent_ranking.get('agent_name')}, "
            f"returning top {min(3, len(issues))}"
        )

        return sorted_issues[:3]

    def _check_hangup_rate(self, agent: Dict[str, Any]) -> Dict[str, Any] | None:
        """Check if hangup success rate is too low"""
        hangup_rate = agent.get("hangup_success_rate")

        if hangup_rate is None:
            return None

        if hangup_rate < self.HANGUP_RATE_THRESHOLD_CRITICAL:
            return {
                "severity": "critical",
                "title": "Very Low Hangup Success Rate",
                "description": f"Only {hangup_rate * 100:.0f}% of conversations ended properly. "
                f"Most conversations are hitting max turn limits instead of natural endings.",
                "metric_value": f"{hangup_rate * 100:.0f}%",
                "threshold": f"{self.HANGUP_RATE_THRESHOLD_CRITICAL * 100:.0f}%",
                "recommended_fix": "Review and strengthen hangup prompt logic. Add explicit conversation "
                "ending markers. Test with various conversation endings (refusals, "
                "commitments, goodbyes). Consider timeout-based fallback detection.",
            }
        elif hangup_rate < self.HANGUP_RATE_THRESHOLD_HIGH:
            return {
                "severity": "high",
                "title": "Low Hangup Success Rate",
                "description": f"Only {hangup_rate * 100:.0f}% of conversations ended properly. "
                f"Agent failing to detect when conversations should end.",
                "metric_value": f"{hangup_rate * 100:.0f}%",
                "threshold": f"{self.HANGUP_RATE_THRESHOLD_HIGH * 100:.0f}%",
                "recommended_fix": "Improve hangup prompt to better recognize conversation completion signals. "
                "Add more explicit end-of-conversation patterns.",
            }

        return None

    def _check_accuracy(
        self,
        agent: Dict[str, Any],
        agent_id: str = None,
        comparison_id: str = None,
        db: Session = None,
    ) -> Dict[str, Any] | None:
        """Check if accuracy is too low and include turn-level examples"""
        accuracy = agent.get("accuracy", {})
        accuracy_mean = accuracy.get("mean")

        if accuracy_mean is None:
            return None

        # Fetch turn-level examples if database access provided
        poor_turns = []
        if agent_id and comparison_id and db:
            poor_turns = self._get_poor_accuracy_turns(agent_id, comparison_id, db)

        turn_examples = ""
        if poor_turns:
            turn_examples = " Examples of poor turns: " + "; ".join(
                [
                    f"Turn {t['turn']} (accuracy: {t['accuracy']}/10): {t['reasoning'][:100]}"
                    for t in poor_turns[:2]
                ]
            )

        if accuracy_mean < self.ACCURACY_THRESHOLD_CRITICAL:
            return {
                "severity": "critical",
                "title": "Very Low Turn Accuracy",
                "description": f"Average accuracy of {accuracy_mean * 100:.1f}% is critically low. "
                f"Agent making frequent incorrect decisions and not following instructions properly."
                + turn_examples,
                "metric_value": f"{accuracy_mean * 100:.1f}%",
                "threshold": f"{self.ACCURACY_THRESHOLD_CRITICAL * 100:.0f}%",
                "recommended_fix": "Investigate turn accuracy validator logic. Review validation criteria - may be too strict. "
                "Check if language handling (Hindi/English) needs improvement. Add detailed logging "
                "to identify which specific turns are failing validation.",
                "poor_turns": poor_turns,
            }
        elif accuracy_mean < self.ACCURACY_THRESHOLD_HIGH:
            return {
                "severity": "high",
                "title": "Low Turn Accuracy",
                "description": f"Average accuracy of {accuracy_mean * 100:.1f}% is below acceptable threshold. "
                f"Agent responses not consistently meeting quality standards."
                + turn_examples,
                "metric_value": f"{accuracy_mean * 100:.1f}%",
                "threshold": f"{self.ACCURACY_THRESHOLD_HIGH * 100:.0f}%",
                "recommended_fix": "Review agent prompt quality and conversation flow adherence. "
                "Check validation logic for potential issues. Improve agent training or prompt engineering.",
                "poor_turns": poor_turns,
            }

        return None

    def _get_poor_accuracy_turns(
        self, agent_id: str, comparison_id: str, db: Session, max_examples: int = 3
    ) -> List[Dict[str, Any]]:
        """Fetch examples of poor accuracy turns from database"""
        from app.models import AgentComparisonRun

        try:
            runs = (
                db.query(AgentComparisonRun)
                .filter(
                    AgentComparisonRun.comparison_id == comparison_id,
                    AgentComparisonRun.agent_id == agent_id,
                    AgentComparisonRun.status == "completed",
                )
                .all()
            )

            poor_turns_all = []
            for run in runs:
                if run.least_accurate_turns:
                    poor_turns_all.extend(run.least_accurate_turns)

            # Sort by accuracy (lowest first) and return top examples
            poor_turns_all.sort(key=lambda x: x.get("accuracy", 10))
            return poor_turns_all[:max_examples]

        except Exception as e:
            logger.warning(f"Failed to fetch poor turns for agent {agent_id}: {e}")
            return []

    def _check_zero_variance(self, agent: Dict[str, Any]) -> Dict[str, Any] | None:
        """Check for suspicious zero variance in metrics"""
        accuracy_std = agent.get("accuracy", {}).get("std", 1.0)
        humanlike_std = agent.get("humanlike", {}).get("std", 1.0)
        turns_std = agent.get("avg_turns", {}).get("std", 1.0)

        zero_variance_metrics = []
        if accuracy_std is not None and accuracy_std < self.ZERO_VARIANCE_THRESHOLD:
            zero_variance_metrics.append("accuracy")
        if humanlike_std is not None and humanlike_std < self.ZERO_VARIANCE_THRESHOLD:
            zero_variance_metrics.append("humanlike")
        if turns_std is not None and turns_std < self.ZERO_VARIANCE_THRESHOLD:
            zero_variance_metrics.append("turn count")

        if len(zero_variance_metrics) >= 2:
            return {
                "severity": "high",
                "title": "Zero Variance in Multiple Metrics",
                "description": f"Suspicious zero variance detected in {', '.join(zero_variance_metrics)}. "
                f"This suggests possible duplicate simulation data or overly deterministic behavior.",
                "metric_value": f"{len(zero_variance_metrics)} metrics with std=0",
                "threshold": "Expected natural variation",
                "recommended_fix": "Investigate aggregation logic for potential bugs. Verify simulations are actually "
                "different and not being duplicated. Check if LLM temperature is too low causing "
                "deterministic responses. Add run-level uniqueness validation.",
            }

        return None

    def _check_latency(self, agent: Dict[str, Any]) -> Dict[str, Any] | None:
        """Check if P99 latency is too high"""
        latency = agent.get("latency", {})
        p99_mean = latency.get("p99_mean")

        if p99_mean is None:
            return None

        if p99_mean > self.LATENCY_P99_THRESHOLD_HIGH:
            return {
                "severity": "high",
                "title": "High P99 Latency",
                "description": f"P99 latency of {p99_mean:.2f}s is above acceptable threshold. "
                f"Slowest responses may cause poor user experience.",
                "metric_value": f"{p99_mean:.2f}s",
                "threshold": f"{self.LATENCY_P99_THRESHOLD_HIGH:.1f}s",
                "recommended_fix": "Optimize agent response generation. Consider using faster LLM model. "
                "Review token generation settings (max_tokens, temperature). "
                "Check for network or API bottlenecks.",
            }

        return None

    def _check_humanlike(self, agent: Dict[str, Any]) -> Dict[str, Any] | None:
        """Check if humanlike score is too low"""
        humanlike = agent.get("humanlike", {})
        humanlike_mean = humanlike.get("mean")

        if humanlike_mean is None:
            return None

        if humanlike_mean < self.HUMANLIKE_THRESHOLD_MEDIUM:
            return {
                "severity": "medium",
                "title": "Low Human-like Score",
                "description": f"Human-like rating of {humanlike_mean:.1f}/10 indicates responses feel robotic. "
                f"Agent not sounding natural enough in conversations.",
                "metric_value": f"{humanlike_mean:.1f}/10",
                "threshold": f"{self.HUMANLIKE_THRESHOLD_MEDIUM:.0f}/10",
                "recommended_fix": "Improve conversational tone in system prompt. Add natural fillers, vary sentence "
                "structure, and use more context-aware emotional responses. Review conversation "
                "examples to identify patterns that sound unnatural.",
            }

        return None

    def _check_outcome(self, agent: Dict[str, Any]) -> Dict[str, Any] | None:
        """Check if outcome orientation score is too low"""
        outcome = agent.get("outcome_orientation", {})
        outcome_mean = outcome.get("mean")

        if outcome_mean is None:
            return None

        if outcome_mean < self.OUTCOME_THRESHOLD_MEDIUM:
            return {
                "severity": "medium",
                "title": "Low Outcome Orientation Score",
                "description": f"Outcome score of {outcome_mean:.1f}/10 suggests agent not effectively "
                f"achieving conversation goals (payment commitments, issue resolution).",
                "metric_value": f"{outcome_mean:.1f}/10",
                "threshold": f"{self.OUTCOME_THRESHOLD_MEDIUM:.0f}/10",
                "recommended_fix": "Strengthen goal-oriented conversation strategies. Review negotiation tactics "
                "and escalation paths. Ensure agent maintains focus on desired outcomes "
                "throughout conversation.",
            }

        return None
