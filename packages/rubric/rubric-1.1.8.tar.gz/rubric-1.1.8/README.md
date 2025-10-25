<p align="center">
  <a href="https://pypi.org/project/rubric/">
    <img src="https://img.shields.io/pypi/v/rubric" alt="PyPI version" />
  </a>
  <a href="https://pypi.org/project/rubric/">
    <img src="https://img.shields.io/pypi/pyversions/rubric" alt="Python versions" />
  </a>
  <a href="https://github.com/The-LLM-Data-Company/rubric/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
  </a>
</p>

# Rubric

A Python library for LLM-based evaluation using weighted rubrics.

## Installation

```bash
uv add rubric
```

## Usage

1. **Set up environment variables:**

```bash
export OPENAI_API_KEY=your_api_key_here
```

2. **Run the example below**

```python
import asyncio
import os
from openai import AsyncOpenAI
from rubric import Rubric
from rubric.autograders import PerCriterionGrader

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

    grader = PerCriterionGrader(
        generate_fn=generate_with_async_openai,
        system_prompt="This overrides the default system prompt",
    )

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

### Default System Prompts

Each autograder uses a specialized system prompt optimized for its evaluation approach:

**PerCriterionGrader** - Detailed criterion-by-criterion evaluation with strict JSON formatting requirements. The prompt instructs the LLM to evaluate each criterion independently, handling both positive and negative criteria with specific response formats.

**PerCriterionOneShotGrader** - Streamlined prompt for evaluating all criteria in a single response. Focuses on providing verdicts (MET/UNMET) and explanations for each criterion in a structured JSON format.

**RubricAsJudgeGrader** - Holistic evaluation prompt that asks the LLM to consider the output as a whole and provide a single overall score from 0-100, taking into account the weights of all criteria.

You can view the complete default prompts in the source files:

- [`per_criterion_grader.py`](src/rubric/autograders/per_criterion_grader.py#L10-L55)
- [`per_criterion_one_shot_grader.py`](src/rubric/autograders/per_criterion_one_shot_grader.py#L11-L31)
- [`rubric_as_judge_grader.py`](src/rubric/autograders/rubric_as_judge_grader.py#L11-L22)

**Customizing System Prompts:** You can override the default system prompt by passing a `system_prompt` parameter to any autograder:

```python
grader = PerCriterionGrader(
    generate_fn=your_function,
    system_prompt="Your custom system prompt here"
)
```

## Customization

You can customize grading at multiple levels:

**1. Custom `generate_fn` (most common)**
Pass any function that takes `(system_prompt, user_prompt)` and returns a string. Use any LLM provider (OpenAI, Anthropic, local models, etc.):

```python
grader = PerCriterionGrader(generate_fn=your_custom_function)
```

**2. Override specific methods**
Subclass any autograder and override:

- `judge()` - Orchestrates LLM calls to evaluate criteria and parse responses into structured results
- `generate()` - Wraps your `generate_fn` to customize how prompts are sent to the LLM
- `aggregation()` - Transforms individual criterion results into a final score and optional report

**3. Full control**
Override the entire `grade()` method for complete end-to-end control over the grading process.

## Loading Rubrics

```python
# Direct construction
rubric = Rubric([
    Criterion(weight=10.0, requirement="States Q4 2023 base margin as 17.2%"),
    Criterion(weight=8.0, requirement="Explicitly uses Shapley attribution for decomposition"),
    Criterion(weight=-15.0, requirement="Uses total deliveries instead of cash-only deliveries")
])

# From list of dictionaries
rubric = Rubric.from_dict([
    {"weight": 10.0, "requirement": "States Q4 2023 base margin as 17.2%"},
    {"weight": 8.0, "requirement": "Explicitly uses Shapley attribution for decomposition"},
    {"weight": -15.0, "requirement": "Uses total deliveries instead of cash-only deliveries"}
])

# From JSON string
rubric = Rubric.from_json('[{"weight": 10.0, "requirement": "Example requirement"}]')

# From YAML string
yaml_data = '''
- weight: 10.0
  requirement: "Example requirement"
'''
rubric = Rubric.from_yaml(yaml_data)

# From files
rubric = Rubric.from_file('rubric.json')
rubric = Rubric.from_file('rubric.yaml')
```

### JSON Format

```json
[
  {
    "weight": 10.0,
    "requirement": "States Q4 2023 base margin as 17.2%"
  },
  {
    "weight": 8.0,
    "requirement": "Explicitly uses Shapley attribution for decomposition"
  },
  {
    "weight": -15.0,
    "requirement": "Uses total deliveries instead of cash-only deliveries"
  }
]
```

### YAML Format

```yaml
- weight: 10.0
  requirement: "States Q4 2023 base margin as 17.2%"
- weight: 8.0
  requirement: "Explicitly uses Shapley attribution for decomposition"
- weight: -15.0
  requirement: "Uses total deliveries instead of cash-only deliveries"
```

## Requirements

- Python 3.11+
- An LLM API (e.g., OpenAI, Anthropic, OpenRouter) - set appropriate API keys as environment variables

## License

MIT License - see LICENSE file for details.
