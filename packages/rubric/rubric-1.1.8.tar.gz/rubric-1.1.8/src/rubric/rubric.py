"""Core Rubric class for evaluating text outputs against a set of weighted criteria."""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from rubric.autograders import Autograder, PerCriterionGrader
from rubric.types import Criterion, EvaluationReport
from rubric.utils import default_generate_fn


class Rubric:
    """A rubric is a list of criteria used to evaluate text outputs.

    Each criterion has a weight and requirement. Use the grade() method
    to evaluate text against this rubric using different autograder strategies.
    """

    def __init__(self, rubric: list[Criterion]):
        self.rubric = rubric

    async def grade(
        self,
        to_grade: str,
        autograder: Autograder | None = None,
        **kwargs: Any,
    ) -> EvaluationReport:
        """Grade text against this rubric using an autograder class or function."""
        if autograder is None:
            autograder = PerCriterionGrader(generate_fn=default_generate_fn)
        return await autograder.grade(to_grade=to_grade, rubric=self.rubric)

    @staticmethod
    def validate_and_create_criteria(data: list[dict[str, Any]]) -> list[Criterion]:
        """Validate and create Criterion objects from raw data."""
        if not isinstance(data, list):
            raise ValueError(
                f"Invalid rubric format. Expected a list of criteria, got {type(data).__name__}"
            )

        criteria = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Invalid criterion at index {idx} expected a dictionary, "
                    f"got {type(item).__name__}"
                )

            try:
                criteria.append(Criterion(**item))  # type: ignore[arg-type]
            except ValidationError as e:
                error_details = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    error_details.append(f"{field}: {error['msg']}")

                error_msg = f"Invalid criterion at index {idx}:\n  " + "\n  ".join(error_details)
                raise ValueError(error_msg) from e
            except Exception as e:
                raise ValueError(f"Failed to create criterion at index {idx}: {e}") from e

        if not criteria:
            raise ValueError("No criteria found")

        return criteria

    @classmethod
    def from_yaml(cls, yaml_string: str) -> "Rubric":
        """Parse rubric from a YAML string."""
        try:
            data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML string: {e}") from e

        criteria = cls.validate_and_create_criteria(data)
        return cls(criteria)

    @classmethod
    def from_json(cls, json_string: str) -> "Rubric":
        """Parse rubric from a JSON string."""
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON string: {e}") from e

        criteria = cls.validate_and_create_criteria(data)
        return cls(criteria)

    @classmethod
    def from_file(cls, source: str | Any) -> "Rubric":
        """Load rubric from a file path or file-like object, auto-detecting format."""
        if hasattr(source, "read"):
            file_name = getattr(source, "name", "")  # type: ignore[arg-type]
            extension = Path(file_name).suffix.lower() if file_name else ""

            if not extension:
                raise ValueError(
                    "Cannot determine file format from file object. "
                    "File object must have a 'name' attribute with a file extension."
                )

            try:
                content = source.read()  # type: ignore[misc]
            except Exception as e:
                raise ValueError(f"Failed to read from file object: {e}") from e

            if extension in [".yaml", ".yml"]:
                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise ValueError(f"Failed to parse YAML from file object: {e}") from e
                criteria = cls.validate_and_create_criteria(data)
                return cls(criteria)
            elif extension == ".json":
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse JSON from file object: {e}") from e
                criteria = cls.validate_and_create_criteria(data)
                return cls(criteria)
            else:
                raise ValueError(
                    f"Unsupported file format '{extension}' for file object: {file_name}\n"
                    f"Supported formats: .yaml, .yml, .json"
                )

        elif isinstance(source, str):
            path = Path(source)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")

            extension = path.suffix.lower()

            if extension in [".yaml", ".yml"]:
                with open(source) as f:
                    try:
                        data = yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        raise ValueError(f"Failed to parse YAML file: {e}") from e
                criteria = cls.validate_and_create_criteria(data)
                return cls(criteria)
            elif extension == ".json":
                with open(source) as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Failed to parse JSON file: {e}") from e
                criteria = cls.validate_and_create_criteria(data)
                return cls(criteria)
            else:
                raise ValueError(
                    f"Unsupported file format '{extension}' for file: {source}\n"
                    f"Supported formats: .yaml, .yml, .json"
                )
        else:
            raise ValueError(
                f"Invalid source type: expected str (file path) or file-like object, "
                f"got {type(source).__name__}"
            )

    @classmethod
    def from_dict(cls, data: list[dict[str, Any]]) -> "Rubric":
        """Create rubric from a list of dictionaries."""
        criteria = cls.validate_and_create_criteria(data)
        return cls(criteria)
