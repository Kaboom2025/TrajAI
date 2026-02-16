from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from unitai.core.trajectory import Trajectory, TrajectoryStep

class TrajectoryFormatter:
    """Generates human-readable summaries of agent trajectories."""

    def __init__(self, value_limit: int = 100, max_steps: int = 20):
        self.value_limit = value_limit
        self.max_steps = max_steps

    def format(self, trajectory: Trajectory, highlights: Optional[Dict[int, str]] = None) -> str:
        """Format a trajectory into a readable string summary."""
        highlights = highlights or {}
        steps = trajectory.steps
        total_steps = len(steps)
        
        if total_steps == 0:
            return "Actual trajectory: (empty)"

        output = [f"Actual trajectory ({total_steps} steps):"]
        
        # Determine which steps to show
        indices_to_show = self._get_relevant_indices(total_steps, highlights)
        
        last_idx = -1
        for idx in sorted(indices_to_show):
            # Add ellipsis if there's a gap
            if last_idx != -1 and idx > last_idx + 1:
                gap = idx - last_idx - 1
                output.append(f"    ... ({gap} more steps) ...")
            
            step = steps[idx]
            line = self._format_step(step, idx + 1)
            
            # Add highlight arrow
            if idx in highlights:
                line += f"  ← {highlights[idx]}"
            
            output.append(f"    {line}")
            last_idx = idx
            
        return "\n".join(output)

    def _get_relevant_indices(self, total_steps: int, highlights: Dict[int, str]) -> set[int]:
        """Determine which step indices to show based on limits and highlights."""
        if total_steps <= self.max_steps:
            return set(range(total_steps))
        
        # Always show first and last
        indices = {0, total_steps - 1}
        
        # Show all highlighted steps and their context (1 before, 1 after)
        for idx in highlights:
            indices.add(idx)
            if idx > 0:
                indices.add(idx - 1)
            if idx < total_steps - 1:
                indices.add(idx + 1)
                
        return indices

    def _format_step(self, step: TrajectoryStep, display_index: int) -> str:
        """Format a single trajectory step."""
        if step.step_type == "tool_call":
            args_str = self._truncate(str(step.tool_args))
            result_str = self._truncate(str(step.tool_result))
            return f"{display_index}. [tool]  {step.tool_name}({args_str}) → {result_str}"
        
        elif step.step_type == "llm_call":
            meta = []
            if step.model: meta.append(step.model)
            if step.prompt_tokens is not None:
                tokens = step.prompt_tokens + (step.completion_tokens or 0)
                meta.append(f"{tokens} tokens")
            if step.cost is not None: meta.append(f"${step.cost:.4f}")
            
            meta_str = f" ({', '.join(meta)})" if meta else ""
            return f"{display_index}. [llm]   {step.model or 'unknown'}{meta_str}"
            
        elif step.step_type == "state_change":
            old_v = self._truncate(str(step.old_value))
            new_v = self._truncate(str(step.new_value))
            return f"{display_index}. [state] {step.key}: {old_v} → {new_v}"
            
        return f"{display_index}. [{step.step_type}]"

    def _truncate(self, value: str) -> str:
        """Truncate a string value if it exceeds the limit."""
        if len(value) <= self.value_limit:
            return value
        return value[:self.value_limit] + "..."