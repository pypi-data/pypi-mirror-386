"""Development server for testing agents locally."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Type imports

from pixell.models.agent_manifest import AgentManifest
from pixell.core.validator import AgentValidator
from pixell.utils import parse_dotenv, merge_envs
from pixell.secrets import get_provider_from_env


class AgentRequest(BaseModel):
    """Request model for agent invocation."""

    action: str
    data: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Response model for agent invocation."""

    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentReloader(FileSystemEventHandler):
    """Watches for file changes and triggers reload."""

    def __init__(self, callback):
        self.callback = callback
        self.last_reload = 0

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only reload for Python files and agent.yaml
        if event.src_path.endswith((".py", "agent.yaml")):
            # Debounce rapid changes
            import time

            current_time = time.time()
            if current_time - self.last_reload > 1:
                self.last_reload = current_time
                self.callback()


class DevServer:
    """Development server for testing agents."""

    def __init__(self, project_dir: Path, port: int = 8080):
        self.project_dir = Path(project_dir).resolve()
        self.port = port
        self.app = FastAPI(title="Pixell Agent Development Server")
        self.manifest: Optional[AgentManifest] = None
        self.observer: Optional[Any] = None  # Observer type

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.on_event("startup")
        async def startup():
            """Load agent on startup."""
            self._load_agent()
            self._start_file_watcher()
            # Mount optional REST and UI surfaces
            try:
                self._mount_optional_surfaces()
            except Exception as exc:
                print(f"[WARN] Failed to mount optional surfaces: {exc}")

        @self.app.on_event("shutdown")
        async def shutdown():
            """Cleanup on shutdown."""
            if self.observer:
                self.observer.stop()
                self.observer.join()

        @self.app.get("/")
        async def root():
            """Health check and agent info."""
            if not self.manifest:
                return {"status": "error", "message": "No agent loaded"}

            return {
                "status": "ready",
                "agent": {
                    "name": self.manifest.name,
                    "display_name": self.manifest.display_name,
                    "version": self.manifest.metadata.version,
                    "capabilities": self.manifest.capabilities,
                },
            }

        @self.app.post("/invoke", response_model=AgentResponse)
        async def invoke(request: AgentRequest):
            """Invoke the agent."""
            if not self.manifest:
                raise HTTPException(status_code=500, detail="No agent loaded")

            try:
                result = await self._invoke_agent(request.dict())
                return AgentResponse(status="success", data=result)
            except Exception as e:
                return AgentResponse(status="error", error=str(e))

        @self.app.post("/reload")
        async def reload():
            """Manually reload the agent."""
            try:
                self._load_agent()
                return {"status": "success", "message": "Agent reloaded"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def _load_agent(self):
        """Load or reload the agent."""
        # Validate first
        validator = AgentValidator(self.project_dir)
        is_valid, errors, _ = validator.validate()

        if not is_valid:
            raise RuntimeError(f"Validation failed: {', '.join(errors)}")

        # Load manifest
        manifest_path = self.project_dir / "agent.yaml"
        import yaml

        with open(manifest_path, "r") as f:
            data = yaml.safe_load(f)

        self.manifest = AgentManifest(**data)

        # Load secrets via provider (service-bound) then .env for local parity
        base_env = os.environ.copy()
        provider = get_provider_from_env()
        provider_vars: Dict[str, str] = {}
        if provider:
            try:
                provider_vars = provider.fetch_secrets()
                if provider_vars:
                    keys_preview = ", ".join(sorted(provider_vars.keys()))
                    print(
                        f"[INFO] Secrets provider loaded ({len(provider_vars)} vars): {keys_preview}"
                    )
            except Exception as exc:
                print(f"[WARN] Secrets provider error: {exc}")

        env_file = self.project_dir / ".env"
        dotenv_vars = parse_dotenv(env_file)
        if dotenv_vars:
            keys_preview = ", ".join(sorted(dotenv_vars.keys()))
            print(f"[INFO] .env loaded ({len(dotenv_vars)} vars): {keys_preview}")

        # Precedence (Phase 3 dev approximation): provider > .env > base env
        merged = merge_envs(base_env, dotenv_vars)
        merged = merge_envs(merged, provider_vars)
        # Apply only overrides to process env
        for k, v in merged.items():
            if os.environ.get(k) != v:
                os.environ[k] = v

        # Add project directory to Python path
        if str(self.project_dir) not in sys.path:
            sys.path.insert(0, str(self.project_dir))

        print(
            f"[SUCCESS] Loaded agent: {self.manifest.display_name} v{self.manifest.metadata.version}"
        )

    def _start_file_watcher(self):
        """Start watching for file changes."""

        def reload_callback():
            print("[RELOAD] Detected changes, reloading agent...")
            try:
                self._load_agent()
                try:
                    self._mount_optional_surfaces()
                except Exception as exc:
                    print(f"[WARN] Failed to remount optional surfaces: {exc}")
                print("[SUCCESS] Agent reloaded successfully")
            except Exception as e:
                print(f"[ERROR] Reload failed: {e}")

        event_handler = AgentReloader(reload_callback)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.project_dir), recursive=True)
        self.observer.start()

    async def _invoke_agent(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the agent with the given request."""
        if not self.manifest:
            raise RuntimeError("No manifest loaded")
        entrypoint = self.manifest.entrypoint
        if not entrypoint:
            raise RuntimeError(
                "Agent entrypoint is not configured. Define an entrypoint in agent.yaml or "
                "configure an appropriate surface."
            )
        module_path, function_name = entrypoint.split(":", 1)

        # Prepare the environment
        env = os.environ.copy()
        env.update(self.manifest.environment)

        # Create a subprocess to run the agent
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            f"""
import sys
import json
sys.path.insert(0, '{self.project_dir}')

from {module_path} import {function_name}

# Read input
input_data = {json.dumps(request_data)}

# Call the function
result = {function_name}(input_data)

# Output result
print(json.dumps(result))
""",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Agent execution failed: {stderr.decode()}")

        try:
            result: Dict[str, Any] = json.loads(stdout.decode())
            # Validate outbound in dev if envelope-like
            try:
                from pixell.protocol import validate_outbound_if_dev

                if isinstance(result, dict) and "type" in result:
                    validate_outbound_if_dev(result)
            except Exception:
                pass
            return result
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response from agent: {stdout.decode()}")

    def run(self):
        """Start the development server."""
        print(f"Starting Pixell development server on http://localhost:{self.port}")
        print(f"Serving agent from: {self.project_dir}")
        print("Watching for file changes...")
        print("\nPress Ctrl+C to stop")

        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
            reload=False,  # We handle reloading ourselves
        )

    def _mount_optional_surfaces(self):
        """Mount REST routes and UI static assets when configured."""
        if not self.manifest:
            return

        # Mount REST routes if specified
        try:
            if getattr(self.manifest, "rest", None) and self.manifest.rest:
                entry = self.manifest.rest.entry
                module_path, func_name = entry.split(":", 1)
                import importlib
                import sys

                # Add project directory to Python path for imports
                if str(self.project_dir) not in sys.path:
                    sys.path.insert(0, str(self.project_dir))

                # Clear any cached modules with same path so missing files raise correctly
                module_parts = module_path.split(".")
                for i in range(len(module_parts), 0, -1):
                    sys.modules.pop(".".join(module_parts[:i]), None)

                module = importlib.import_module(module_path)
                mount_func = getattr(module, func_name)
                # Expecting mount_func(FastAPI) -> None
                mount_func(self.app)
                print(f"[REST] Mounted routes from {entry}")
        except Exception as exc:
            print(f"[WARN] REST mount failed: {exc}")

        # Serve UI static assets if specified
        try:
            if getattr(self.manifest, "ui", None) and self.manifest.ui and self.manifest.ui.path:
                ui_dir = Path(self.project_dir) / self.manifest.ui.path
                if ui_dir.exists() and ui_dir.is_dir():
                    # Mount at /ui to avoid clobbering root
                    # If already mounted, first unmounting isn't straightforward; rely on reload process restart in dev
                    self.app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")
                    print(f"[UI] Serving static assets from {ui_dir} at /ui")
                else:
                    print(f"[WARN] UI path not found or not a directory: {ui_dir}")
        except Exception as exc:
            print(f"[WARN] UI mount failed: {exc}")
