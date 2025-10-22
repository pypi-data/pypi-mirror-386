from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from marshmallow import RAISE, Schema
from marshmallow_dataclass import class_schema
from qwak.exceptions import QwakException, LoadConfigurationException
from yaml import SafeLoader, dump, load

from .utils import ConfigCliMap, rgetattr, rsetattr

ERROR_OPENING_YAML_FILE_MSG = "Error opening the config file"
ERROR_PARSING_YAML_FILE_MSG = "Error parsing the config file's yaml"
ERROR_IN_CONFIG_MSG = "Error loading the config"


class QwakConfigBase(ABC):
    """Base qwak config object."""

    @property
    @abstractmethod
    def _config_mapping(self) -> List[ConfigCliMap]:
        """Config mapping, Return a list of ConfigCliMap object in order to create the mapping.

        Returns:
            list: List of ConfigCliMap to apply.
        """
        pass

    def merge_cli_argument(
        self, sections: Tuple[str, ...] = (), **kwargs: Dict[str, Any]
    ):
        """Merge and validate cli arguments by supplied mapping.

        Args:
            sections: Sections to validate.
            **kwargs: argument from cli.

        Raises:
            QwakException: In case that the argument is not valid.
        """
        for prop_map in self._config_mapping:
            value = kwargs.get(prop_map.key)
            if value is not None:
                if isinstance(value, (list, tuple)):
                    new_value = list(rgetattr(self, prop_map.prop))
                    new_value.extend(value)
                    value = new_value
                rsetattr(self, prop_map.prop, value)
            if (
                not sections
                or any(
                    list(
                        map(
                            lambda section, _prop_map=prop_map: _prop_map.prop.startswith(
                                section
                            ),
                            sections,
                        )
                    )
                )
                or "." not in prop_map.prop
            ):
                config_value = rgetattr(self, prop_map.prop)
                if not prop_map.validation_func(config_value, prop_map.is_required):
                    raise QwakException(
                        f"{prop_map.key} argument contain invalid argument: "
                        f"{value or config_value}"
                    )
        self._post_merge_cli()

    @abstractmethod
    def _post_merge_cli(self):
        """Actions to perform after merging cli argument in to properties"""
        pass


class YamlConfigMixin(object):
    @classmethod
    def from_yaml(
        cls, yaml_path: str, unknown: str = RAISE, logger: Optional[Logger] = None
    ) -> Any:
        """Create instance of class from yaml and class scheme.

        Args:
            yaml_path (str): Yaml path.

        Returns:
            object: Instance of created class.
        """
        if not yaml_path:
            return cls()
        Schema.Meta.unknown = unknown
        schema = class_schema(cls)
        try:
            yaml_content = Path(yaml_path).read_text()
        except Exception as e:
            if logger:
                logger.error(f"Error opening the config file {yaml_path}")
            raise LoadConfigurationException(ERROR_OPENING_YAML_FILE_MSG) from e

        try:
            yaml_parsed = load(stream=yaml_content, Loader=SafeLoader)
        except Exception as e:
            if logger:
                logger.exception(ERROR_PARSING_YAML_FILE_MSG, e)
            raise LoadConfigurationException(ERROR_PARSING_YAML_FILE_MSG) from e

        try:
            return schema(unknown=unknown).load(yaml_parsed)
        except Exception as e:
            if logger:
                logger.exception(ERROR_IN_CONFIG_MSG, e)
            raise LoadConfigurationException(ERROR_IN_CONFIG_MSG) from e

    def to_yaml(self) -> str:
        """Convert class by scheme to yaml.

        Returns:
            str: Class as yaml string by scheme.
        """
        loaded_type = type(self)
        schema = class_schema(loaded_type)

        return dump(schema().dump(self))
