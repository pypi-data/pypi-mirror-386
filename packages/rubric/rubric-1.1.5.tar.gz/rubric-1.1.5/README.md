# Rubrics

A Python library for LLM-based evaluation using weighted rubrics.

## Installation

```bash
uv add rubric
```

## Usage

```python
import asyncio
import os
from openai import AsyncOpenAI
from rubric import Rubric
from autograders.per_criterion_grader import PerCriterionGrader

async def generate_with_async_openai(system_prompt: str, user_prompt: str) -> str:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
        temperature=0.0,
    )
    return response.choices[0].message.content or ""

async def main():
    rubric = Rubric.from_dict([
        {"weight": 10.0, "requirement": "States Q4 2023 base margin as 17.2%"},
        {"weight": 8.0, "requirement": "Explicitly uses Shapley attribution for decomposition"},
        {"weight": -15.0, "requirement": "Uses total deliveries instead of cash-only deliveries"}
    ])

    grader = PerCriterionGrader(generate_fn=generate_with_async_openai)
    
    result = await rubric.grade(
        to_grade="Your text to evaluate...",
        autograder=grader
    )

    print(f"Score: {result.score}/100")
    for criterion in result.report:
        print(f"  {criterion.verdict}: {criterion.requirement}")

asyncio.run(main())
```

## Autograder Strategies

- `PerCriterionGrader` - Evaluates each criterion in parallel LLM calls
- `PerCriterionOneShotGrader` - Evaluates all criteria in a single LLM call
- `RubricAsJudgeGrader` - Holistic evaluation, LLM returns final score directly

## Customization

You can customize grading at multiple levels:

**1. Custom `generate_fn` (most common)**
Pass any function that takes `(system_prompt, user_prompt)` and returns a string. Use any LLM provider (OpenAI, Anthropic, local models, etc.):

```python
grader = PerCriterionGrader(generate_fn=your_custom_function)
```

**2. Override specific methods**
Subclass any autograder and override:
- `judge()` - How rubric criteria are evaluated against the text
- `generate()` - How prompts are constructed and LLM is called, typically calls the generate_fn
- `aggregation()` - How individual criterion scores are combined

**3. Full control**
Override the entire `grade()` method for complete end-to-end control over the grading process.

## Loading Rubrics

```python
rubric = Rubric.from_dict([...])
rubric = Rubric.from_json('{"criteria": [...]}')
rubric = Rubric.from_yaml('...')
rubric = Rubric.from_file('rubric.yaml')
```

## Requirements

- Python 3.13+
- An LLM API (e.g., OpenAI, OpenRouter) - set appropriate API keys as environment variables

## License

MIT License - see LICENSE file for details.
