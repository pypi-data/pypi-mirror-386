import typer

from instant_python.config.application.config_generator import ConfigGenerator
from instant_python.config.infra.parser.parser import Parser
from instant_python.config.infra.question_wizard.step.questionary import Questionary
from instant_python.config.infra.question_wizard.questionary_console_wizard import QuestionaryConsoleWizard
from instant_python.config.infra.writer.yaml_config_writer import YamlConfigWriter

app = typer.Typer()


@app.command("config", help="Generate the configuration file for a new project")
def generate_ipy_configuration_file() -> None:
    config_generator = ConfigGenerator(
        question_wizard=QuestionaryConsoleWizard(questionary=(Questionary())),
        writer=YamlConfigWriter(),
        parser=Parser(),
    )
    config_generator.execute()
