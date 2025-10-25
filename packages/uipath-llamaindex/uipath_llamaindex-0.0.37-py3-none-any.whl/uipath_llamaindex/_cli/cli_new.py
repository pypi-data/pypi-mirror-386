import os
import shutil

import click
from uipath._cli._utils._console import ConsoleLogger
from uipath._cli.middlewares import MiddlewareResult

console = ConsoleLogger()


def generate_script(target_directory):
    template_script_path = os.path.join(
        os.path.dirname(__file__), "_templates/main.py.template"
    )
    target_path = os.path.join(target_directory, "main.py")

    shutil.copyfile(template_script_path, target_path)

    template_llama_index_json_path = os.path.join(
        os.path.dirname(__file__), "_templates/llama_index.json.template"
    )
    target_path = os.path.join(target_directory, "llama_index.json")
    shutil.copyfile(template_llama_index_json_path, target_path)


def generate_pyproject(target_directory, project_name):
    project_toml_path = os.path.join(target_directory, "pyproject.toml")
    toml_content = f"""[project]
name = "{project_name}"
version = "0.0.1"
description = "{project_name}"
authors = [{{ name = "John Doe", email = "john.doe@myemail.com" }}]
dependencies = [
    "uipath-llamaindex>=0.0.27",
    "llama-index-llms-openai>=0.2.2"
]
requires-python = ">=3.10"
"""

    with open(project_toml_path, "w") as f:
        f.write(toml_content)


def llamaindex_new_middleware(name: str) -> MiddlewareResult:
    """Middleware to create demo llamaindex agent"""

    directory = os.getcwd()

    try:
        with console.spinner(f"Creating new agent {name} in current directory ..."):
            generate_pyproject(directory, name)
            generate_script(directory)
            console.success("Created 'main.py' file.")
            console.success("Created 'llama_index.json' file.")
            generate_pyproject(directory, name)
            console.success("Created 'pyproject.toml' file.")
            console.config(
                f""" Please ensure to define {click.style("OPENAI_API_KEY", fg="bright_yellow")} in your .env file. """
            )
            init_command = """uipath init"""
            run_command = """uipath run agent '{"topic": "UiPath"}'"""
            console.hint(
                f""" Initialize project: {click.style(init_command, fg="cyan")}"""
            )
            console.hint(f""" Run agent: {click.style(run_command, fg="cyan")}""")
        return MiddlewareResult(should_continue=False)
    except Exception as e:
        console.error(f"Error creating demo agent {str(e)}")
        return MiddlewareResult(
            should_continue=False,
            should_include_stacktrace=True,
        )
