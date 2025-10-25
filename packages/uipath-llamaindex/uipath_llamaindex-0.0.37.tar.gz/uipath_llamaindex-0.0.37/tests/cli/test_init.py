import json
import os

from click.testing import CliRunner
from uipath._cli.cli_init import init  # type: ignore


class TestInit:
    def test_init_basic_config_generation(
        self,
        runner: CliRunner,
        temp_dir: str,
        simple_script_basic_config: str,
        llama_config: str,
    ) -> None:
        """Test configuration file generation with StartEvent and StopEvent."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Create agent script
            with open("main.py", "w") as f:
                f.write(simple_script_basic_config)

            with open("llama_index.json", "w") as f:
                f.write(llama_config)

            result = runner.invoke(init)
            assert result.exit_code == 0
            assert os.path.exists("uipath.json")

            with open("uipath.json", "r") as f:
                config = json.load(f)

                # Verify config structure
                assert "entryPoints" in config
                assert "bindings" in config

                # Verify entryPoints properties
                entry = config["entryPoints"][0]
                assert entry["filePath"] == "agent"
                assert entry["type"] == "agent"

                # Verify input schema
                assert "input" in entry
                input_schema = entry["input"]
                assert input_schema["type"] == "object"
                assert "properties" in input_schema
                assert "required" in input_schema
                assert isinstance(input_schema["properties"], dict)
                assert isinstance(input_schema["required"], list)

                # Verify output schema
                assert "output" in entry
                output_schema = entry["output"]
                assert "properties" in output_schema
                assert "result" in output_schema["properties"]
                assert "title" in output_schema["properties"]["result"]
                assert "type" in output_schema["properties"]["result"]
                assert output_schema["properties"]["result"]["type"] == "object"
                assert output_schema["properties"]["result"]["title"] == "Result"
                assert "required" in output_schema
                assert output_schema["required"] == ["result"]
                assert output_schema["type"] == "object"

                # Verify bindings
                assert config["bindings"]["version"] == "2.0"
                assert "resources" in config["bindings"]
                assert isinstance(config["bindings"]["resources"], list)

    def test_init_custom_config_generation(
        self,
        runner: CliRunner,
        temp_dir: str,
        simple_script_custom_config: str,
        llama_config: str,
    ) -> None:
        """Test configuration file generation with custom StartEvent and StopEvent."""
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Create agent script
            with open("main.py", "w") as f:
                f.write(simple_script_custom_config)

            with open("llama_index.json", "w") as f:
                f.write(llama_config)

            result = runner.invoke(init)
            assert result.exit_code == 0
            assert os.path.exists("uipath.json")

            with open("uipath.json", "r") as f:
                config = json.load(f)

                # Verify config structure
                assert "entryPoints" in config
                assert "bindings" in config

                # Verify entryPoints properties
                entry = config["entryPoints"][0]
                assert entry["filePath"] == "agent"
                assert entry["type"] == "agent"

                # Verify input schema
                assert "input" in entry
                input_schema = entry["input"]
                assert input_schema["type"] == "object"
                assert "properties" in input_schema
                assert "required" in input_schema

                # Verify input properties
                props = input_schema["properties"]
                assert "topic" in props
                assert props["topic"]["type"] == "string"

                assert "param" in props
                assert props["param"]["type"] == "string"
                assert props["param"]["nullable"]

                # Verify required fields in input
                assert input_schema["required"] == ["topic"]

                # Verify output schema
                assert "output" in entry
                output_schema = entry["output"]
                assert output_schema["type"] == "object"
                assert "properties" in output_schema
                assert "required" in output_schema

                # Verify output properties
                out_props = output_schema["properties"]
                assert "joke" in out_props
                assert out_props["joke"]["type"] == "string"

                assert "critique" in out_props
                assert out_props["critique"]["type"] == "string"

                assert "param" in out_props
                assert out_props["param"]["type"] == "string"
                assert out_props["param"]["nullable"]

                # Verify required fields in output
                assert output_schema["required"] == ["joke", "critique"]

                # Verify bindings
                assert config["bindings"]["version"] == "2.0"
                assert "resources" in config["bindings"]
                assert isinstance(config["bindings"]["resources"], list)
