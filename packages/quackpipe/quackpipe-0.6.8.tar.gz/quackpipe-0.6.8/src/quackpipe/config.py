"""
Defines the typed configuration objects for quackpipe.
"""
import os
from dataclasses import dataclass, field
from enum import Enum

import yaml
from jsonschema import validate

from quackpipe.exceptions import ConfigError
from quackpipe.utils import DotDict

SourceParams = DotDict

def validate_config(config_data: dict) -> None:
    """
    Validates the given configuration data against the schema.

    Args:
        config_data: The configuration data to validate.

    Raises:
        ValidationError: If the configuration is invalid.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "config.schema.yml")
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    validate(instance=config_data, schema=schema)


@dataclass(frozen=True)
class Plugin:
    """A structured definition for a DuckDB plugin that may require special installation."""
    name: str
    repository: str | None = None


class SourceType(Enum):
    """Enumeration of supported source types."""
    POSTGRES = "postgres"
    MYSQL = "mysql"
    S3 = "s3"
    AZURE = "azure"
    DUCKLAKE = "ducklake"
    SQLITE = "sqlite"
    PARQUET = "parquet"
    CSV = "csv"


@dataclass
class SourceConfig:
    """
    A structured configuration object for a single data source.
    """
    name: str
    type: SourceType
    config: SourceParams = field(default_factory=SourceParams)
    secret_name: str | None = None
    before_source_statements: list[str] = field(default_factory=list)
    after_source_statements: list[str] = field(default_factory=list)


def get_config_yaml(path: str | None) -> dict | None:
    """
    Loads and returns the parsed YAML configuration from the given path
    or from the QUACKPIPE_CONFIG_PATH environment variable.

    Returns None if no valid path is found.
    """
    config_path = path or os.environ.get("QUACKPIPE_CONFIG_PATH")
    if config_path:
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError as e:
            raise ConfigError(f"Configuration file not found at '{config_path}'.") from e
    return None


def parse_config_from_yaml(raw_config: dict) -> list[SourceConfig]:
    """
    Gets the content of a parsed YAML file, validates it and prepares a list of SourceConfig objects
    """

    # We import here to avoid a circular import at the top level
    from jsonschema.exceptions import ValidationError

    try:
        validate_config(raw_config)
    except ValidationError as e:
        raise ConfigError(f"Configuration is invalid: {e.message}") from e

    source_configs = []
    for name, details in raw_config.get('sources', {}).items():
        details_copy = details.copy()

        try:
            source_type_str = details_copy.pop('type')
            source_type = SourceType(source_type_str)
        except (KeyError, ValueError) as e:
            raise ConfigError(f"Missing or invalid 'type' for source '{name}'.") from e

        secret_name = details_copy.pop('secret_name', None)
        before_statements = details_copy.pop('before_source_statements', [])
        after_statements = details_copy.pop('after_source_statements', [])
        source_specific_config = details_copy

        source_configs.append(SourceConfig(
            name=name,
            type=source_type,
            secret_name=secret_name,
            before_source_statements=before_statements,
            after_source_statements=after_statements,
            config=source_specific_config
        ))

    return source_configs


def get_configs(
        config_path: str | None = None,
        configs: list[SourceConfig] | None = None
) -> list[SourceConfig]:
    """
    A helper function to load source configurations. The priority is:
    1. A direct list from the `configs` argument.
    2. A file path from the `config_path` argument.
    3. A file path from the `QUACKPIPE_CONFIG_PATH` environment variable.

    This logic is shared by `session` and `etl_utils`.
    """
    # If configs are directly provided, return them immediately
    if configs:
        return configs

    # Try to load from config_path or environment variable
    config_yaml = get_config_yaml(config_path)
    if config_yaml:
        return parse_config_from_yaml(config_yaml)

    # This provides a clear error message if no configuration source is given.
    raise ConfigError(
        "Must provide either a 'config_path', a 'configs' list, or set the "
        "'QUACKPIPE_CONFIG_PATH' environment variable to a valid config yaml file."
    )


def get_global_statements(config_path: str | None = None) -> dict:
    """
    Extracts global statements from the configuration file.

    Returns a dictionary with 'before_all_statements' and 'after_all_statements'.
    Returns empty lists if no configuration is found.
    """
    raw_config = get_config_yaml(config_path) or {}
    return {
        'before_all_statements': raw_config.get('before_all_statements', []),
        'after_all_statements': raw_config.get('after_all_statements', []),
    }
