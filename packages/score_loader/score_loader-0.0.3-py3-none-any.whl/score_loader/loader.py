import re
from pathlib import Path
from typing import Any, Dict, Union

import yaml
from pydantic import ValidationError

from src.score_loader.types import ScoreSpec

_TEMPLATE = re.compile(r"\$\{([^}]+)\}")


def _get_by_path(data: Any, path: str) -> Any:
    """
    Retrieve a value from nested dict/list structures given a dot-separated path.
    Example: "metadata.name" -> data["metadata"]["name"]
    """
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"Path '{path}': key '{part}' not found")
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                raise KeyError(f"Path '{path}': list index '{part}' is not an integer")
            if not (0 <= idx < len(cur)):
                raise KeyError(f"Path '{path}': list index {idx} out of range")
            cur = cur[idx]
        else:
            raise KeyError(f"Path '{path}': cannot traverse into non-container type")
    return cur


def _resolve_string(value: str, context: Any, *, max_passes: int = 5) -> str:
    """
    Replace ${dot.path} occurrences using values from context.
    Runs multiple passes to allow chained substitutions if they appear after replacement.
    """
    result = value
    for _ in range(max_passes):
        changed = False

        def repl(match: re.Match) -> str:
            nonlocal changed
            path = match.group(1).strip()
            try:
                resolved = _get_by_path(context, path)
            except KeyError:
                # Leave unresolved; you may choose to raise instead
                return match.group(0)
            changed = True
            return str(resolved)

        new_result = _TEMPLATE.sub(repl, result)
        result = new_result
        if not changed:
            break
    return result


def _resolve_any(node: Any, context: Any) -> Any:
    """
    Recursively resolve templates in a Python structure loaded from YAML.
    Only strings are templated; other types pass through.
    """
    if isinstance(node, str):
        return _resolve_string(node, context)
    elif isinstance(node, list):
        return [_resolve_any(item, context) for item in node]
    elif isinstance(node, dict):
        # Resolve values; keys are left as-is (you can add key resolution if needed)
        return {k: _resolve_any(v, context) for k, v in node.items()}
    else:
        return node


def load_score_file(path: Union[str, Path]) -> ScoreSpec:
    """
    Load a YAML Score spec from 'path', resolve ${...} placeholders against the
    full document context, and return a validated Pydantic ScoreSpec.

    Parameters
    ----------
    path : str | Path
        Path to the YAML file.

    Returns
    -------
    ScoreSpec
        The validated, template-resolved spec.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw: Any = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Top-level YAML must be a mapping/object")

    # Resolve templates using the raw data as the context
    resolved: Dict[str, Any] = _resolve_any(raw, raw)

    try:
        return ScoreSpec(**resolved)
    except ValidationError as e:
        # Re-raise with a bit more context
        raise ValueError(f"Spec validation failed:\n{e}") from e
