import os
from control_plane_openapi_mcp.config import mcp

# Prompt for generating scripts using Control Plane APIs
@mcp.prompt(name="Control Plane API Script Generation")
def generate_api_script() -> str:
    """
    Prompt to be used for creating scripts that interact with Control Plane APIs.
    This will read from the `api_script_guide.md` file.

    Returns:
        The content of the prompt read from the markdown file.
    """
    guide_message = ""
    try:
        # Get the directory of the current file
        base_dir = os.path.dirname(__file__)
        # Construct the full path to the markdown file
        file_path = os.path.join(base_dir, "api_script_guide.md")

        with open(file_path, "r") as file:
            guide_message = file.read()
    except FileNotFoundError:
        guide_message = "Error: The `api_script_guide.md` file was not found."
    return guide_message
