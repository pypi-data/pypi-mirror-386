"""
Registry of prompt templates by type.

Import prompt templates from prompts.py and map them to string keys.
No model names are included in prompt templates.
"""
from .prompts import (
    prompt_assertion_reason,
    prompt_solution_with_o4_mini,
    prompt_match,
    prompt_mcq_problem_with_tikz_solution_o4_mini,
    prompt_mcq_problem_with_solution_o4_mini,
)

PROMPT_TYPES = {
    "assertion_reason": prompt_assertion_reason,
    "solution_o4_mini": prompt_solution_with_o4_mini,
    "match": prompt_match,
    "mcq_with_tikz_solution_o4_mini": prompt_mcq_problem_with_tikz_solution_o4_mini,
    "mcq_with_solution_o4_mini": prompt_mcq_problem_with_solution_o4_mini,
}

def get_prompt(prompt_type: str) -> str:
    """
    Get the prompt template for the given prompt type.

    Args:
        prompt_type: Key of the prompt template in PROMPT_TYPES.

    Returns:
        The prompt template string.
    """
    try:
        return PROMPT_TYPES[prompt_type]
    except KeyError:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
