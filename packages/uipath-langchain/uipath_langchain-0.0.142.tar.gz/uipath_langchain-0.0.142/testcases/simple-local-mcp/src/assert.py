import os
import json

print("Checking simple local MCP agent output...")

# Check NuGet package
uipath_dir = ".uipath"
assert os.path.exists(uipath_dir), "NuGet package directory (.uipath) not found"

nupkg_files = [f for f in os.listdir(uipath_dir) if f.endswith('.nupkg')]
assert nupkg_files, "NuGet package file (.nupkg) not found in .uipath directory"

print(f"NuGet package found: {nupkg_files[0]}")

# Check agent output file
output_file = "__uipath/output.json"
assert os.path.isfile(output_file), "Agent output file not found"

print("Agent output file found")

# Check status and required fields
with open(output_file, 'r', encoding='utf-8') as f:
    output_data = json.load(f)

# Check status
status = output_data.get("status")
assert status == "successful", f"Agent execution failed with status: {status}"

print("Agent execution status: successful")

# Check required fields for simple local MCP agent
assert "output" in output_data, "Missing 'output' field in agent response"

output_content = output_data["output"]
assert "messages" in output_content, "Missing 'messages' field in output"

messages = output_content["messages"]
assert messages and isinstance(messages, list), "Messages field is empty or not a list"

with open("local_run_output.log", 'r', encoding='utf-8') as f:
    local_run_output = f.read()

# Check if response contains 'Successful execution.'
assert "Successful execution." in local_run_output, f"Response does not contain 'Successful execution.'. Actual response: {local_run_output}"

print("Required fields validation passed")