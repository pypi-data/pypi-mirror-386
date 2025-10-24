from instant_python.config.infra.question_wizard.step.questionary import Questionary
from instant_python.config.infra.question_wizard.step.steps import Step
from instant_python.shared.supported_licenses import SupportedLicenses
from instant_python.shared.supported_managers import SupportedManagers
from instant_python.shared.supported_python_versions import SupportedPythonVersions


class GeneralStep(Step):
    _KEY = "general"

    def __init__(self, questionary: Questionary) -> None:
        super().__init__(questionary)
        self._answers = {}

    def run(self) -> dict[str, dict[str, str]]:
        self._ask_project_slug()
        self._ask_source_folder_name()
        self._ask_project_description()
        self._ask_project_version()
        self._ask_author_name()
        self._ask_license()
        self._ask_python_version()
        self._ask_dependency_manager()

        return {self._KEY: self._answers}

    def _ask_project_slug(self) -> None:
        answer = self._questionary.free_text_question(
            message="Enter the name of the project (CANNOT CONTAIN SPACES)",
            default="python-project",
        )
        self._answers["slug"] = answer

    def _ask_source_folder_name(self) -> None:
        answer = self._questionary.free_text_question(
            message="Enter the name of the source folder",
            default="src",
        )
        self._answers["source_name"] = answer

    def _ask_project_description(self) -> None:
        answer = self._questionary.free_text_question(
            message="Enter the project description",
            default="Python Project Description",
        )
        self._answers["description"] = answer

    def _ask_project_version(self) -> None:
        answer = self._questionary.free_text_question(
            message="Enter the project initial version",
            default="0.1.0",
        )
        self._answers["version"] = answer

    def _ask_author_name(self) -> None:
        answer = self._questionary.free_text_question(
            message="Enter your name",
        )
        self._answers["author"] = answer

    def _ask_license(self) -> None:
        answer = self._questionary.single_choice_question(
            message="Select a license",
            options=SupportedLicenses.get_supported_licenses(),
        )
        self._answers["license"] = answer

    def _ask_python_version(self) -> None:
        answer = self._questionary.single_choice_question(
            message="Enter the python version",
            options=SupportedPythonVersions.get_supported_versions(),
        )
        self._answers["python_version"] = answer

    def _ask_dependency_manager(self) -> None:
        answer = self._questionary.single_choice_question(
            message="Select a dependency manager",
            options=SupportedManagers.get_supported_managers(),
            default=SupportedManagers.UV,
        )
        self._answers["dependency_manager"] = answer
