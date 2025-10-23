"""
LLM-based evaluation judge.

This module provides an evaluation judge that uses an LLM to score trajectories.
"""

import json
from typing import Dict, List, Optional

from ..._cancellation_token import CancellationToken
from ...llm import BaseChatCompletionClient
from ...messages import SystemMessage, UserMessage
from ...types import EvalScore, EvalTrajectory
from .._base import BaseEvalJudge


class LLMEvalJudge(BaseEvalJudge):
    """LLM-based evaluation judge that uses another model to score trajectories."""

    def __init__(
        self,
        client: BaseChatCompletionClient,
        name: Optional[str] = None,
        default_criteria: Optional[List[str]] = None,
        answer_strategy: str = "last_non_empty",
    ):
        """Initialize the LLM judge.

        Args:
            client: LLM client to use for scoring
            name: Optional custom name (defaults to model name)
            default_criteria: Default evaluation criteria if none specified
            answer_strategy: How to extract answer from trajectory
                Note: LLM judges often benefit from seeing full context
        """
        super().__init__(
            name or f"LLM-{getattr(client, 'model', 'Judge')}", answer_strategy
        )
        self.client = client
        self.default_criteria = default_criteria or [
            "accuracy",
            "completeness",
            "helpfulness",
        ]

    async def score(
        self,
        trajectory: EvalTrajectory,
        criteria: Optional[List[str]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> EvalScore:
        """Score an evaluation trajectory using LLM.

        Args:
            trajectory: The execution trajectory to score
            criteria: Optional list of evaluation dimensions to score
            cancellation_token: Optional token to cancel scoring

        Returns:
            EvalScore with overall and dimensional scores
        """
        # Use provided criteria or default
        eval_criteria = criteria or self.default_criteria

        try:
            # Build the evaluation prompt
            system_prompt = self._build_system_prompt(eval_criteria)
            user_prompt = self._build_user_prompt(trajectory)

            messages = [
                SystemMessage(content=system_prompt, source="system"),
                UserMessage(content=user_prompt, source="user"),
            ]

            # Get LLM response (note: cancellation_token not passed to client as it's not part of the base interface)
            result = await self.client.create(messages)
            response_content = result.message.content

            # Parse the structured response
            score_data = self._parse_llm_response(response_content, eval_criteria)

            return EvalScore(
                overall=score_data["overall"],
                dimensions=score_data["dimensions"],
                reasoning=score_data["reasoning"],
                trajectory=trajectory,
                metadata={
                    "judge_name": self.name,
                    "model": result.model,
                    "criteria_used": eval_criteria,
                    "raw_response": response_content,
                },
            )

        except Exception as e:
            # Return fallback score on error
            return EvalScore(
                overall=5.0,  # Neutral score
                dimensions={dim: 5.0 for dim in eval_criteria},
                reasoning={dim: f"Judge error: {str(e)}" for dim in eval_criteria},
                trajectory=trajectory,
                metadata={
                    "judge_name": self.name,
                    "error": str(e),
                    "criteria_used": eval_criteria,
                },
            )

    def _build_system_prompt(self, criteria: List[str]) -> str:
        """Build the system prompt for the evaluation LLM."""
        criteria_descriptions = {
            "accuracy": "How factually correct and truthful is the response?",
            "completeness": "How thoroughly does the response address the task?",
            "helpfulness": "How useful and actionable is the response?",
            "clarity": "How clear and well-structured is the response?",
            "creativity": "How creative and original is the response?",
            "safety": "How safe and appropriate is the response?",
        }

        criteria_details = []
        for criterion in criteria:
            description = criteria_descriptions.get(
                criterion, f"Quality of {criterion}"
            )
            criteria_details.append(f"- {criterion}: {description}")

        return f"""You are an expert evaluation judge. Your task is to score AI agent conversations based on specific criteria.

Evaluation Criteria (each scored 0-10):
{chr(10).join(criteria_details)}

Instructions:
1. Analyze the task, expected output (if provided), and the complete agent conversation
2. Consider both the final outcome AND the process (reasoning, communication, error handling)
3. Score each criterion from 0-10 (0=poor, 5=average, 10=excellent)
4. Calculate overall score as average of dimensional scores
5. Provide brief reasoning for each score

Respond with this EXACT JSON format:
{{
  "overall": <overall_score>,
  "dimensions": {{
    "{criteria[0]}": <score>,
    {', '.join(f'"{c}": <score>' for c in criteria[1:]) if len(criteria) > 1 else ''}
  }},
  "reasoning": {{
    "{criteria[0]}": "<brief_reason>",
    {', '.join(f'"{c}": "<brief_reason>"' for c in criteria[1:]) if len(criteria) > 1 else ''}
  }}
}}"""

    def _build_user_prompt(self, trajectory: EvalTrajectory) -> str:
        """Build the user prompt containing the trajectory to evaluate."""
        task_info = f"Task: {trajectory.task.name}\\nInput: {trajectory.task.input}"

        if trajectory.task.expected_output:
            task_info += f"\\nExpected Output: {trajectory.task.expected_output}"

        if trajectory.success and trajectory.messages:
            # Get the full conversation - messages already have proper string formatting
            actual_output = "\n".join(str(msg) for msg in trajectory.messages)

            conversation_summary = f"Messages exchanged: {len(trajectory.messages)}"
            if trajectory.usage:
                conversation_summary += f", Tokens: {trajectory.usage.tokens_input + trajectory.usage.tokens_output}"
        else:
            actual_output = f"EXECUTION FAILED: {trajectory.error or 'Unknown error'}"
            conversation_summary = "No successful execution"

        return f"""{task_info}

Execution Summary: {conversation_summary}
Success: {trajectory.success}

Complete Agent Conversation:
{actual_output}

Please evaluate this complete conversation according to the specified criteria."""

    def _parse_llm_response(self, response: str, criteria: List[str]) -> Dict:
        """Parse the LLM's structured response."""
        try:
            # Try to extract JSON from the response
            response = response.strip()

            # Find JSON block if wrapped in code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            # Parse the JSON
            parsed = json.loads(response)

            # Validate structure
            if not all(key in parsed for key in ["overall", "dimensions", "reasoning"]):
                raise ValueError("Missing required keys")

            # Ensure all criteria are present
            for criterion in criteria:
                if criterion not in parsed["dimensions"]:
                    parsed["dimensions"][criterion] = 5.0
                if criterion not in parsed["reasoning"]:
                    parsed["reasoning"][criterion] = "No reasoning provided"

            return parsed

        except Exception:
            # Fallback to neutral scores
            return {
                "overall": 5.0,
                "dimensions": {dim: 5.0 for dim in criteria},
                "reasoning": {
                    dim: "Failed to parse judge response" for dim in criteria
                },
            }
