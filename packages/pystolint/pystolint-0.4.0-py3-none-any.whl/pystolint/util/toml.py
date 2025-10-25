from __future__ import annotations

from pathlib import Path
from typing import Union, cast
from urllib.request import urlopen

import tomli_w
from poetry.core.constraints.version.exceptions import ParseConstraintError
from poetry.core.constraints.version.parser import parse_constraint
from poetry.core.constraints.version.version_range_constraint import VersionRangeConstraint

try:
    import tomllib  # type: ignore[import-not-found,unused-ignore]
except ImportError:
    import tomli as tomli_fallback  # type: ignore[import-not-found,unused-ignore]

    tomllib = tomli_fallback  # type: ignore[no-redef,unused-ignore]


NestedValue = Union['NestedDict', 'NestedList', str, int, float, bool, None]
NestedDict = dict[str, NestedValue]
NestedList = list[NestedValue]


def deep_merge(base_toml_dict: NestedDict, override_toml_dict: NestedDict) -> None:
    for key, value in override_toml_dict.items():
        if key in base_toml_dict and isinstance(base_toml_dict[key], dict) and isinstance(value, dict):
            deep_merge(cast('NestedDict', base_toml_dict[key]), cast('NestedDict', value))
        elif key in base_toml_dict and isinstance(base_toml_dict[key], list) and isinstance(value, list):
            cast('NestedList', base_toml_dict[key]).extend(cast('NestedList', value))
        else:
            base_toml_dict[key] = value


def get_base_config(base_toml_path_provided: str | None, local_config: NestedDict) -> NestedDict:
    tool_settings = local_config.get('tool', {})
    assert isinstance(tool_settings, dict)
    pystolint_settings = tool_settings.get('pystolint', {})
    assert isinstance(pystolint_settings, dict)
    config_default = pystolint_settings.get('base_toml_path')
    assert config_default is None or isinstance(config_default, str)

    path_override = base_toml_path_provided or config_default
    if path_override and path_override.startswith(('http://', 'https://')):
        with urlopen(path_override) as response:
            toml_str = response.read().decode('utf-8')
            base_config: NestedDict = tomllib.loads(toml_str)
    else:
        pth = path_override or str(Path(__file__).parent.parent / 'default_config/pyproject.toml')
        base_config = tomllib.loads(Path(pth).read_text())

    return base_config


def ensure_ruff_extend_is_absolute(merged_config: NestedDict, local_toml_path: str) -> None:
    tool = merged_config.get('tool')
    if not isinstance(tool, dict):
        return

    ruff_settings = tool.get('ruff')
    if not isinstance(ruff_settings, dict):
        return

    extend_config_path = ruff_settings.get('extend')
    if extend_config_path is None:
        return

    assert isinstance(extend_config_path, str)
    if not Path(extend_config_path).is_absolute():
        extend_config_path = str(Path(local_toml_path).parent.resolve() / extend_config_path)

    assert isinstance(merged_config['tool'], dict)
    assert isinstance(merged_config['tool']['ruff'], dict)
    merged_config['tool']['ruff']['extend'] = extend_config_path
    if not Path(extend_config_path).is_file():
        merged_config['tool']['ruff'].pop('extend')


def get_merged_config(
    local_toml_path_provided: str | None = None, base_toml_path_provided: str | None = None
) -> NestedDict:
    local_toml_path = local_toml_path_provided or 'pyproject.toml'
    local_config = tomllib.loads(Path(local_toml_path).read_text())
    base_config = get_base_config(base_toml_path_provided, local_config)

    python_target_version: str | None = get_python_min_version(local_config)
    if python_target_version is not None:
        assert isinstance(base_config['tool'], dict)
        if 'ruff' in base_config['tool']:
            assert isinstance(base_config['tool']['ruff'], dict)
            base_config['tool']['ruff']['target-version'] = 'py' + python_target_version.replace('.', '')
        if 'mypy' in base_config['tool']:
            assert isinstance(base_config['tool']['mypy'], dict)
            base_config['tool']['mypy']['python_version'] = python_target_version

    merged_config: NestedDict = base_config.copy()
    deep_merge(merged_config, local_config)

    ensure_ruff_extend_is_absolute(merged_config, local_toml_path)
    return merged_config


def dump_merged_config(
    local_toml_path_provided: str | None, base_toml_path_provided: str | None, dest_path: str
) -> None:
    dest_path = dest_path.removesuffix('.toml')
    merged_config = get_merged_config(local_toml_path_provided, base_toml_path_provided).get('tool', {})
    assert isinstance(merged_config, dict)

    ruff_config = merged_config.get('ruff', {})
    assert isinstance(ruff_config, dict)
    with Path(dest_path + '.ruff.toml').open('wb') as f:
        tomli_w.dump(ruff_config, f)

    mypy_config = merged_config.get('mypy', {})
    mypy_config = {'tool': {'mypy': mypy_config}}
    with Path(dest_path + '.mypy.toml').open('wb') as f:
        tomli_w.dump(mypy_config, f)


def parse_min_version(version_spec: str) -> str | None:
    try:
        constraint = parse_constraint(version_spec)
    except ParseConstraintError:
        return None

    if not isinstance(constraint, VersionRangeConstraint):
        return None

    allowed_min = constraint.allowed_min
    if allowed_min is None:
        return None

    if allowed_min.minor and constraint.include_min:
        minor = allowed_min.minor
    elif allowed_min.minor and not constraint.include_min:
        minor = allowed_min.minor + 1
    else:
        minor = 0

    return f'{allowed_min.major}.{minor}'


def get_python_min_version(local_config: NestedDict) -> str | None:
    version_spec = None

    # Check Poetry project
    if 'tool' in local_config and isinstance(local_config['tool'], dict) and 'poetry' in local_config['tool']:
        assert isinstance(local_config['tool']['poetry'], dict)
        dependencies = local_config['tool']['poetry'].get('dependencies', {})
        assert isinstance(dependencies, dict)
        version_spec = dependencies.get('python')

    # Check setuptools project (PEP 621)
    elif (
        'project' in local_config
        and isinstance(local_config['project'], dict)
        and 'requires-python' in local_config['project']
    ):
        version_spec = local_config['project']['requires-python']

    if version_spec is None:
        return None

    assert isinstance(version_spec, str)
    return parse_min_version(version_spec)
