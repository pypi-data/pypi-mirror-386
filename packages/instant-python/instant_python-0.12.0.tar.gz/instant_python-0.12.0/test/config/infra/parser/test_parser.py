import json
from pathlib import Path

import pytest
import yaml
from approvaltests import verify
from expects import expect, raise_error, be_none

from instant_python.config.infra.parser.parser import Parser
from instant_python.config.infra.parser.errors import (
    ConfigKeyNotPresent,
    EmptyConfigurationNotAllowed,
    MissingMandatoryFields,
)


class TestParser:
    def setup_method(self) -> None:
        self._parser = Parser()

    def test_should_raise_error_if_answers_is_empty(self) -> None:
        empty_answers = {}

        expect(lambda: self._parser.parse(empty_answers)).to(raise_error(EmptyConfigurationNotAllowed))

    def test_should_raise_error_if_some_section_is_missing(self) -> None:
        answers = self._read_fake_answers_from_file("missing_keys_answers")

        expect(lambda: self._parser.parse(answers)).to(raise_error(ConfigKeyNotPresent))

    @pytest.mark.parametrize(
        "file_name",
        [
            pytest.param("missing_general_fields", id="missing_general_fields"),
            pytest.param("missing_dependencies_fields", id="missing_dependencies_fields"),
            pytest.param("missing_template_fields", id="missing_template_fields"),
            pytest.param("missing_git_fields", id="missing_git_fields"),
        ],
    )
    def test_should_raise_error_when_mandatory_fields_are_missing_inside_answers_section(self, file_name: str) -> None:
        answers = self._read_fake_answers_from_file(file_name)

        expect(lambda: self._parser.parse(answers)).to(raise_error(MissingMandatoryFields))

    def test_should_parse_valid_answers(self) -> None:
        answers = self._read_fake_answers_from_file("valid_answers")

        config = self._parser.parse(answers)

        expect(config).to_not(be_none)
        verify(json.dumps(config.to_primitives(), indent=2))

    @staticmethod
    def _read_fake_answers_from_file(file_name: str) -> dict[str, dict]:
        with open(Path(__file__).parent / "resources" / f"{file_name}.yml") as answers:
            return yaml.safe_load(answers)
