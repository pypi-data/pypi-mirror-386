import os
import sys
from pathlib import Path
from importlib.util import find_spec

import modal

from .main import app as web_app

HF_HOME_PATH = Path("/hf_home")

# Add builtin_flows to sys.path if pi_flows is not already importable
# This allows using builtin flows by default, or custom flows via PYTHONPATH
# This has to be done before building the image so the right pi_flows is included
try:
    import pi_flows  # noqa: F401
    print("Loaded pi_flows from PYTHONPATH", file=sys.stderr)
except ImportError:
    builtin_flows_path = Path(__file__).parent / "builtin_flows"
    sys.path.insert(0, str(builtin_flows_path))
    print(f"Added {builtin_flows_path} to sys.path for builtin flows", file=sys.stderr)
    import pi_flows  # noqa: F401

# Find the pi_flows module directory and locate requirements.txt
pi_flows_spec = find_spec("pi_flows")
if pi_flows_spec is None or pi_flows_spec.origin is None:
    raise ImportError("Could not find pi_flows module")

pi_flows_dir = Path(pi_flows_spec.origin).parent
pi_flows_requirements = pi_flows_dir / "requirements.txt"

# Locate requirements_gen.txt in the same directory as this file
current_dir = Path(__file__).parent
requirements_gen = current_dir / "requirements_gen.txt"

# Modal doesn't support Workspaces, but we can get around it a bit by preloading workspace packages
# before running uv_sync.
image = (
    modal.Image.debian_slim()
    .apt_install("git")
    .uv_pip_install(requirements=[str(pi_flows_requirements), str(requirements_gen)])
    .env(
        {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "USER": os.getenv("USER", "None"),
            "HF_HOME": str(HF_HOME_PATH),
        }
    )
    .add_local_python_source("data_model", "clients", "pi_flows")
)

volume = modal.Volume.from_name("hf_home", create_if_missing=True)

# Use PI_APP_ID if set, otherwise fall back to USER for backward compatibility
app_name = os.getenv("PI_APP_ID") or f"search-{os.getenv('USER', 'None')}"

app = modal.App(
    app_name,
    image=image,
    secrets=[modal.Secret.from_name("zach-withpi")],
    volumes={str(HF_HOME_PATH): volume},
)


@app.function(min_containers=1, max_containers=1)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    return web_app
