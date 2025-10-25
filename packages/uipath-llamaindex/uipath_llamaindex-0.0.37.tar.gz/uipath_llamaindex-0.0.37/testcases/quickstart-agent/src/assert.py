import json
import os
import sys

print("Checking quickstart agent output...")

# Check NuGet package
uipath_dir = ".uipath"
if not os.path.exists(uipath_dir):
    print("NuGet package directory (.uipath) not found")
    sys.exit(1)

nupkg_files = [f for f in os.listdir(uipath_dir) if f.endswith(".nupkg")]
if not nupkg_files:
    print("NuGet package file (.nupkg) not found in .uipath directory")
    sys.exit(1)

print(f"NuGet package found: {nupkg_files[0]}")

# Check agent output file
output_file = "__uipath/output.json"
if not os.path.isfile(output_file):
    print("Agent output file not found")
    sys.exit(1)

print("Agent output file found")

# Check status and required fields
try:
    with open(output_file, "r", encoding="utf-8") as f:
        output_data = json.load(f)

    # Check status
    status = output_data.get("status")
    if status != "successful":
        print(f"Agent execution failed with status: {status}")
        sys.exit(1)

    print("Agent execution status: successful")

    # Check required fields for quickstart agent
    if "output" not in output_data:
        print("Missing 'output' field in agent response")
        sys.exit(1)

    output_content = output_data["output"]
    if "joke" not in output_content:
        print("Missing 'joke' field in output")
        sys.exit(1)

    joke = output_content["joke"]
    if not joke or joke.strip() == "":
        print("Joke field is empty")
        sys.exit(1)

    if "critique" not in output_content:
        print("Missing 'critique' field in output")
        sys.exit(1)

    critique = output_content["critique"]
    if not critique or critique.strip() == "":
        print("Critique field is empty")
        sys.exit(1)

    print(f"Joke: {joke}")
    print(f"Critique: {critique}")

    print("Required fields validation passed")
    print("Quickstart agent working correctly.")

except Exception as e:
    print(f"Error checking output: {e}")
    sys.exit(1)
