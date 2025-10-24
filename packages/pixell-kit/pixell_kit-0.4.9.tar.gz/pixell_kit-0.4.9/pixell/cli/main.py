import click
import time
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
from typing import List, Dict, Any
import asyncio

try:
    __version__ = version("pixell-kit")
except PackageNotFoundError:
    __version__ = "0.1.0-dev"


@click.group()
@click.version_option(version=__version__, prog_name="pixell")
def cli():
    """Pixell Kit - Package AI agents into portable APKG files."""
    pass


@cli.command()
@click.argument("name")
@click.option(
    "--surface",
    "surfaces",
    type=click.Choice(["a2a", "rest", "ui"], case_sensitive=False),
    multiple=True,
    help="Which surfaces to include (repeatable). Defaults to all.",
)
def init(name, surfaces):
    """Initialize a new agent project (Python) with optional A2A/REST/UI surfaces."""
    project_dir = Path(name).resolve()

    if project_dir.exists():
        click.secho(f"Directory already exists: {project_dir}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)

    if not surfaces:
        surfaces = ("a2a", "rest", "ui")

    # Create directories
    (project_dir / "src").mkdir(parents=True)
    if "rest" in surfaces:
        (project_dir / "src" / "rest").mkdir(parents=True)
    if "a2a" in surfaces:
        (project_dir / "src" / "a2a").mkdir(parents=True)
    if "ui" in surfaces:
        (project_dir / "ui").mkdir(parents=True)

    # agent.yaml
    normalized_name = name.replace("_", "-").lower()
    display_name = name.replace("-", " ").replace("_", " ").title()

    agent_yaml = {
        "version": "1.0",
        "name": normalized_name,
        "display_name": display_name,
        "description": "A Pixell agent",
        "author": "Your Name",
        "license": "MIT",
        # Entrypoint optional when REST or A2A present, include a default sample
        "entrypoint": "src.main:handler",
        "runtime": "python3.11",
        "environment": {},
        "dependencies": [
            "fastapi>=0.112.0",
            "uvicorn>=0.30.0",
            "watchdog>=4.0.0",
        ],
        "metadata": {"version": "0.1.0"},
    }

    if "a2a" in surfaces:
        agent_yaml["a2a"] = {"service": "src.a2a.server:serve"}
    if "rest" in surfaces:
        agent_yaml["rest"] = {"entry": "src.rest.index:mount"}
    if "ui" in surfaces:
        agent_yaml["ui"] = {"path": "ui"}

    import yaml as _yaml

    (project_dir / "agent.yaml").write_text(_yaml.safe_dump(agent_yaml, sort_keys=False))

    # src/main.py
    (project_dir / "src" / "main.py").write_text(
        '''def handler(context):
    """Example entrypoint."""
    return {"message": "Hello from handler", "received": context}
'''
    )

    # REST scaffold
    if "rest" in surfaces:
        (project_dir / "src" / "rest" / "index.py").write_text(
            """from fastapi import FastAPI


def mount(app: FastAPI) -> None:
    @app.get("/api/hello")
    async def hello():
        return {"message": "Hello from REST"}
"""
        )

    # A2A scaffold (stub)
    if "a2a" in surfaces:
        (project_dir / "src" / "a2a" / "server.py").write_text(
            """def serve() -> None:
    # TODO: Implement gRPC server per A2A protocol
    print("A2A server stub - implement gRPC service here")
"""
        )

    # UI scaffold
    if "ui" in surfaces:
        (project_dir / "ui" / "index.html").write_text(
            """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pixell Agent UI</title>
    <style>body{font-family:system-ui, sans-serif; margin:40px}</style>
  </head>
  <body>
    <h1>Pixell Agent UI</h1>
    <p>Open <code>/api/hello</code> to test REST.</p>
  </body>
  </html>
"""
        )

    # requirements.txt
    (project_dir / "requirements.txt").write_text(
        "\n".join(
            [
                "fastapi>=0.112.0",
                "uvicorn>=0.30.0",
                "watchdog>=4.0.0",
            ]
        )
        + "\n"
    )

    # .env.example
    (project_dir / ".env.example").write_text(
        """# Environment Variables Template
# Copy this file to `.env` and set values.

# SECURITY: The `.env` file is included in your APKG package.
# Use safe defaults or placeholders if you do not want to embed real secrets.

# Example: OpenAI API Key
# OPENAI_API_KEY=your-api-key-here

# Example: Network bindings (use 0.0.0.0 in containers)
# API_HOST=0.0.0.0
# API_PORT=8080

# Example: Database connection (prefer service names in Docker)
# DB_HOST=database
# DB_PORT=5432
"""
    )

    # README
    (project_dir / "README.md").write_text(
        f"""# {agent_yaml["display_name"]}

Local dev:

- Install deps: `pip install -r requirements.txt`
- Run dev: `pixell dev -p . --port 8080` then open http://localhost:8080/ui/
- Try REST: http://localhost:8080/api/hello
"""
    )

    click.secho(f"✓ Initialized project at {project_dir}", fg="green")


@cli.command()
@click.option("--path", "-p", default=".", help="Path to agent project directory")
@click.option("--output", "-o", help="Output directory for APKG file")
def build(path, output):
    """Build agent into APKG file."""
    from pathlib import Path
    from pixell.core.builder import AgentBuilder, BuildError

    project_dir = Path(path).resolve()
    click.echo(f"Building agent from {project_dir}...")

    try:
        builder = AgentBuilder(project_dir)
        output_path = builder.build(output_dir=Path(output) if output else None)

        # Show build info
        size_mb = output_path.stat().st_size / (1024 * 1024)
        click.echo()
        click.secho("SUCCESS: Build successful!", fg="green", bold=True)
        click.echo(f"  [Package] {output_path.name}")
        click.echo(f"  [Location] {output_path.parent}")
        click.echo(f"  [Size] {size_mb:.2f} MB")

    except BuildError as e:
        click.secho(f"FAILED: Build failed: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except Exception as e:
        click.secho(f"ERROR: Unexpected error: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)


@cli.command(name="run-dev")
@click.option("--path", "-p", default=".", help="Path to agent project directory")
@click.option("--port", default=8080, help="Port to run the server on")
def run_dev(path, port):
    """Run agent locally for development."""
    from pathlib import Path
    from pixell.dev_server.server import DevServer

    project_dir = Path(path).resolve()

    try:
        server = DevServer(project_dir, port=port)
        server.run()
    except KeyboardInterrupt:
        click.echo("\nShutting down development server...")
    except Exception as e:
        click.secho(f"ERROR: Server error: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)


@cli.command(name="dev")
@click.option("--path", "-p", default=".", help="Path to agent project directory")
@click.option("--port", default=8080, help="Port to run the server on")
def dev(path, port):
    """Alias for run-dev."""
    return run_dev.callback(path, port)  # type: ignore[attr-defined]


@cli.command()
@click.option("--path", "path_", default=".", help="Path to agent project")
@click.option(
    "--level",
    "level",
    type=click.Choice(["static", "build", "install", "runtime", "integration"]),
    default="integration",
    help="Test level to run",
)
@click.option(
    "--category",
    "category",
    type=click.Choice(["security", "grpc", "rest", "env", "all"]),
    default="all",
    help="Test category to run",
)
@click.option("--json", "json_output", is_flag=True, help="Output JSON for CI/CD")
@click.option("--verbose", "verbose", is_flag=True, help="Verbose output")
def test(path_: str, level: str, category: str, json_output: bool, verbose: bool):
    """Test agent comprehensively before deployment."""

    import sys
    from pixell.test.test_runner import AgentTester, TestLevel

    project_dir = Path(path_)

    if not json_output:
        click.secho(f"\n🧪 Testing agent at: {project_dir}", fg="cyan", bold=True)
        click.secho("=" * 60, fg="cyan")

    # Currently category filtering is not implemented in runner; accept for future use
    _ = category  # placeholder to avoid linter warnings

    tester = AgentTester(project_dir, TestLevel(level), silent=json_output)
    result = asyncio.run(tester.run_all_tests())

    if json_output:
        import json as json_lib

        output = {
            "success": result.success,
            "passed": result.passed,
            "failed": result.failed,
            "warnings": result.warnings,
            "skipped": result.skipped,
        }
        click.echo(json_lib.dumps(output, indent=2))
    else:
        click.echo("\n")
        click.secho("=" * 60, fg="cyan")
        click.secho("📊 Test Results", fg="cyan", bold=True)
        click.secho("=" * 60, fg="cyan")

        for msg in result.passed:
            click.secho(msg, fg="green")
        for msg in result.warnings:
            click.secho(msg, fg="yellow")
        for msg in result.failed:
            click.secho(msg, fg="red")
        for msg in result.skipped:
            click.secho(msg, fg="blue")

        click.echo("\n")
        if result.success:
            click.secho("✅ All tests passed!", fg="green", bold=True)
            sys.exit(0)
        else:
            click.secho("❌ Tests failed", fg="red", bold=True)
            sys.exit(1)


@cli.command()
@click.argument("package")
def inspect(package):
    """Inspect an APKG package."""
    click.echo(f"Inspecting package: {package}")
    click.echo("Not implemented yet")


@cli.command()
@click.option("--path", "-p", default=".", help="Path to agent project directory")
def validate(path):
    """Validate agent.yaml and package structure."""
    from pathlib import Path
    from pixell.core.validator import AgentValidator

    project_dir = Path(path).resolve()
    click.echo(f"Validating agent in {project_dir}...")

    validator = AgentValidator(project_dir)
    is_valid, errors, warnings = validator.validate()

    # Display results
    if errors:
        click.secho("FAILED: Validation failed:", fg="red", bold=True)
        for error in errors:
            click.echo(f"  - {error}")

    if warnings:
        click.echo()
        click.secho("WARNING: Warnings:", fg="yellow", bold=True)
        for warning in warnings:
            click.echo(f"  - {warning}")

    if is_valid:
        click.echo()
        click.secho("SUCCESS: Validation passed!", fg="green", bold=True)
        ctx = click.get_current_context()
        ctx.exit(0)
    else:
        ctx = click.get_current_context()
        ctx.exit(1)


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "detailed"]),
    default="table",
    help="Output format (table, json, or detailed)",
)
@click.option("--search", "-s", help="Search for agents by name, description, or tags")
@click.option("--show-sub-agents", is_flag=True, help="Show sub-agents in table view")
def list(format, search, show_sub_agents):
    """List installed agents with detailed information."""
    from pixell.core.registry import Registry
    import json

    registry = Registry()

    # Get agents based on search
    if search:
        agents = registry.search_agents(search)
        if not agents:
            click.echo(f"No agents found matching '{search}'")
            return
    else:
        agents = registry.list_agents(detailed=(format == "detailed" or show_sub_agents))

    if format == "table":
        # Table format with basic info
        if not agents:
            click.echo("No agents installed.")
            click.echo("\nUse 'pixell install <package>' to install an agent.")
            return

        # Calculate column widths
        name_width = max(20, max(len(a.display_name) for a in agents) + 2)
        version_width = 10
        author_width = max(15, max(len(a.author) for a in agents) + 2)

        # Header
        click.echo()
        header = f"{'Name':<{name_width}} {'Version':<{version_width}} {'Author':<{author_width}} Description"
        click.echo(header)
        click.echo("-" * len(header))

        # Agent rows
        for agent in agents:
            desc = (
                agent.description[:50] + "..." if len(agent.description) > 50 else agent.description
            )
            click.echo(
                f"{agent.display_name:<{name_width}} {agent.version:<{version_width}} {agent.author:<{author_width}} {desc}"
            )

            # Show sub-agents if requested
            if show_sub_agents and agent.sub_agents:
                for sub in agent.sub_agents:
                    sub_desc = (
                        sub.description[:40] + "..."
                        if len(sub.description) > 40
                        else sub.description
                    )
                    public_tag = "[public]" if sub.public else "[private]"
                    click.echo(
                        f"  |-- {sub.name:<{name_width - 3}} {'':<{version_width}} {public_tag:<{author_width}} {sub_desc}"
                    )

        click.echo()
        click.echo(f"Total: {len(agents)} agent(s)")
        click.echo("\nUse 'pixell list --format detailed' for full information")
        click.echo("Use 'pixell list --show-sub-agents' to see sub-agents")

    elif format == "json":
        # JSON format with all details
        agents_data = [agent.to_dict() for agent in registry.list_agents(detailed=True)]
        click.echo(json.dumps(agents_data, indent=2))

    else:  # detailed format
        # Detailed format with extensive information
        for i, agent in enumerate(agents):
            if i > 0:
                click.echo("\n" + "=" * 80 + "\n")

            # Basic info
            click.secho(f"{agent.display_name} v{agent.version}", fg="green", bold=True)
            click.echo(f"Package name: {agent.name}")
            click.echo(f"Author: {agent.author}")
            click.echo(f"License: {agent.license}")
            if agent.homepage:
                click.echo(f"Homepage: {agent.homepage}")

            # Description
            click.echo(f"\n{agent.description}")

            # Extensive description
            if agent.extensive_description:
                click.echo("\nDetailed Description:")
                for line in agent.extensive_description.strip().split("\n"):
                    click.echo(f"  {line}")

            # Capabilities and tags
            if agent.capabilities:
                click.echo(f"\nCapabilities: {', '.join(agent.capabilities)}")
            if agent.tags:
                click.echo(f"Tags: {', '.join(agent.tags)}")

            # Sub-agents
            if agent.sub_agents:
                click.echo("\nSub-agents:")
                for sub in agent.sub_agents:
                    status = "PUBLIC" if sub.public else "PRIVATE"
                    click.echo(f"  - {sub.name} [{status}]")
                    click.echo(f"    Description: {sub.description}")
                    click.echo(f"    Endpoint: {sub.endpoint}")
                    click.echo(f"    Capabilities: {', '.join(sub.capabilities)}")

            # Usage guide
            if agent.usage_guide:
                click.echo("\nUsage Guide:")
                for line in agent.usage_guide.strip().split("\n"):
                    click.echo(f"  {line}")

            # Examples
            if agent.examples:
                click.echo("\nExamples:")
                for example in agent.examples:
                    click.echo(f"  {example['title']}:")
                    click.echo(f"    {example['code']}")

            # Technical details
            click.echo("\nTechnical Details:")
            if agent.runtime_requirements:
                click.echo(f"  Runtime: {agent.runtime_requirements}")
            if agent.dependencies:
                click.echo(f"  Dependencies: {', '.join(agent.dependencies)}")
            if agent.install_date:
                click.echo(f"  Installed: {agent.install_date.strftime('%Y-%m-%d %H:%M:%S')}")
            if agent.install_path:
                click.echo(f"  Location: {agent.install_path}")
            if agent.package_size:
                size_mb = agent.package_size / (1024 * 1024)
                click.echo(f"  Size: {size_mb:.1f} MB")


@cli.command()
@click.argument("deployment_id")
@click.option(
    "--env",
    "-e",
    type=click.Choice(["local", "prod"]),
    default="prod",
    help="Deployment environment (local or prod)",
)
@click.option(
    "--api-key", "-k", help="API key for authentication (can also use PIXELL_API_KEY env var)"
)
@click.option("--follow", "-f", is_flag=True, help="Follow deployment progress in real-time")
@click.option("--json", "json_output", is_flag=True, help="Output status as JSON")
def status(deployment_id, env, api_key, follow, json_output):
    """Monitor deployment status."""
    from pixell.core.deployment import (
        DeploymentClient,
        DeploymentError,
        AuthenticationError,
        get_api_key,
    )
    import json as jsonlib

    # Get API key from parameter, environment, or config
    if not api_key:
        api_key = get_api_key()

    if not api_key:
        click.secho(
            "ERROR: No API key provided. Use --api-key, set PIXELL_API_KEY environment variable, or configure in ~/.pixell/config.json",
            fg="red",
        )
        ctx = click.get_current_context()
        ctx.exit(1)

    # Create deployment client
    try:
        client = DeploymentClient(environment=env, api_key=api_key)

        if follow:
            # Follow deployment progress
            click.echo(f"Following deployment {deployment_id}...")
            click.echo()

            last_step = None
            while True:
                try:
                    response = client.get_deployment_status(deployment_id)
                    deployment = response["deployment"]

                    # Check if deployment is complete
                    if deployment["status"] in ["completed", "failed"]:
                        # Show final status
                        if deployment["status"] == "completed":
                            click.secho(
                                "✓ Deployment completed successfully!", fg="green", bold=True
                            )
                        else:
                            click.secho("✗ Deployment failed!", fg="red", bold=True)
                            if "error" in deployment:
                                click.echo(f"  Error: {deployment['error']}")

                        if "completed_at" in deployment:
                            click.echo(f"  Completed at: {deployment['completed_at']}")
                        if "duration_seconds" in deployment:
                            click.echo(f"  Duration: {deployment['duration_seconds']} seconds")

                        break

                    # Show progress
                    if "progress" in deployment:
                        progress = deployment["progress"]
                        current_step = progress.get("current_step", "")

                        if current_step != last_step:
                            last_step = current_step
                            click.echo(f"Current step: {current_step}")

                            # Show step details
                            for step in progress.get("steps", []):
                                status_symbol = {
                                    "completed": "✓",
                                    "processing": "▶",
                                    "pending": "○",
                                    "failed": "✗",
                                }.get(step["status"], "?")

                                status_color = {
                                    "completed": "green",
                                    "processing": "yellow",
                                    "failed": "red",
                                }.get(step["status"], None)

                                step_text = f"  {status_symbol} {step['name']}"
                                if status_color:
                                    click.secho(step_text, fg=status_color)
                                else:
                                    click.echo(step_text)

                    time.sleep(3)

                except KeyboardInterrupt:
                    click.echo("\nMonitoring cancelled.")
                    break

        else:
            # Single status check
            response = client.get_deployment_status(deployment_id)

            if json_output:
                click.echo(jsonlib.dumps(response, indent=2))
            else:
                deployment = response["deployment"]

                # Basic info
                click.echo(f"Deployment ID: {deployment['id']}")
                click.echo(f"Status: {deployment['status']}")
                click.echo(f"Version: {deployment.get('version', 'N/A')}")
                click.echo(f"Created: {deployment.get('created_at', 'N/A')}")

                if deployment.get("started_at"):
                    click.echo(f"Started: {deployment['started_at']}")
                if deployment.get("completed_at"):
                    click.echo(f"Completed: {deployment['completed_at']}")

                # Progress information
                if "progress" in deployment:
                    progress = deployment["progress"]
                    click.echo()
                    click.echo(f"Current step: {progress.get('current_step', 'N/A')}")
                    click.echo("Steps:")

                    for step in progress.get("steps", []):
                        status_symbol = {
                            "completed": "✓",
                            "processing": "▶",
                            "pending": "○",
                            "failed": "✗",
                        }.get(step["status"], "?")

                        click.echo(f"  {status_symbol} {step['name']} [{step['status']}]")

                        if step.get("started_at"):
                            click.echo(f"    Started: {step['started_at']}")
                        if step.get("completed_at"):
                            click.echo(f"    Completed: {step['completed_at']}")

                # Error information
                if deployment["status"] == "failed" and "error" in deployment:
                    click.echo()
                    click.secho("Error:", fg="red", bold=True)
                    click.echo(f"  {deployment['error']}")

    except AuthenticationError as e:
        click.secho(f"AUTHENTICATION ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except DeploymentError as e:
        click.secho(f"DEPLOYMENT ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except Exception as e:
        click.secho(f"UNEXPECTED ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)


@cli.command()
@click.option(
    "--apkg-file",
    "-f",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the APKG file to deploy",
)
@click.option(
    "--env",
    "-e",
    type=click.Choice(["local", "prod"]),
    default="prod",
    help="Deployment environment (local or prod)",
)
@click.option(
    "--app-id",
    "-a",
    help="Agent app ID to deploy to (can also use PIXELL_APP_ID env var or config file)",
)
@click.option(
    "--version", "-v", help="Version string (optional, will extract from package if not provided)"
)
@click.option("--release-notes", "-r", help="Release notes for this deployment")
@click.option(
    "--signature",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    help="Path to signature file for signed packages",
)
@click.option(
    "--api-key", "-k", help="API key for authentication (can also use PIXELL_API_KEY env var)"
)
@click.option("--wait", is_flag=True, help="Wait for deployment to complete")
@click.option("--timeout", default=300, help="Timeout in seconds when waiting for deployment")
@click.option("--force", is_flag=True, help="Force overwrite existing version")
def deploy(
    apkg_file, env, app_id, version, release_notes, signature, api_key, wait, timeout, force
):
    """Deploy an APKG file to Pixell Agent Cloud."""
    from pixell.core.deployment import (
        DeploymentClient,
        DeploymentError,
        AuthenticationError,
        InsufficientCreditsError,
        ValidationError,
        get_api_key,
        get_app_id,
    )

    # Get API key from parameter, environment, or config
    if not api_key:
        api_key = get_api_key()

    if not api_key:
        click.secho(
            "ERROR: No API key provided. Use --api-key, set PIXELL_API_KEY environment variable, or configure in ~/.pixell/config.json",
            fg="red",
        )
        ctx = click.get_current_context()
        ctx.exit(1)

    # Get app ID from parameter, environment, or config
    if not app_id:
        app_id = get_app_id(env)

    if not app_id:
        click.secho(
            f"ERROR: No app ID provided for environment '{env}'. Use --app-id, set PIXELL_APP_ID environment variable, or configure in ~/.pixell/config.json",
            fg="red",
        )
        click.secho(
            "Example config file structure:",
            fg="yellow",
        )
        click.secho(
            '{\n  "api_key": "your-api-key",\n  "environments": {\n    "prod": {"app_id": "your-prod-app-id"},\n    "local": {"app_id": "your-local-app-id"}\n  }\n}',
            fg="yellow",
        )
        ctx = click.get_current_context()
        ctx.exit(1)

    # Create deployment client
    try:
        client = DeploymentClient(environment=env, api_key=api_key)

        click.echo(f"Deploying {apkg_file.name} to {client.ENVIRONMENTS[env]['name']}...")
        click.echo(f"Target: {client.base_url}")
        click.echo(f"App ID: {app_id}")

        if version:
            click.echo(f"Version: {version}")
        if release_notes:
            click.echo(f"Release notes: {release_notes}")
        if force:
            click.echo(click.style("Force overwrite: ENABLED", fg="yellow", bold=True))

        # Start deployment
        response = client.deploy(
            app_id=app_id,
            apkg_file=apkg_file,
            version=version,
            release_notes=release_notes,
            signature_file=signature,
            force_overwrite=force,
        )

        deployment = response["deployment"]
        package = response["package"]
        tracking = response["tracking"]

        # Show deployment info
        click.echo()
        click.secho("✓ Deployment initiated successfully!", fg="green", bold=True)
        click.echo(f"  Deployment ID: {deployment['id']}")
        click.echo(f"  Package ID: {package['id']}")
        click.echo(f"  Status: {deployment['status']}")
        click.echo(f"  Version: {package['version']}")
        click.echo(f"  Size: {package['size_bytes'] / (1024 * 1024):.1f} MB")
        click.echo(f"  Queued at: {deployment['queued_at']}")

        if "estimated_duration_seconds" in deployment:
            click.echo(f"  Estimated duration: {deployment['estimated_duration_seconds']} seconds")

        click.echo()
        click.echo(f"Track deployment status: {tracking['status_url']}")

        # Wait for completion if requested
        if wait:
            click.echo()
            click.echo("Waiting for deployment to complete...")

            try:
                with click.progressbar(length=timeout, label="Deploying") as bar:
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        status = client.get_deployment_status(deployment["id"])
                        deployment_status = status["deployment"]["status"]

                        if deployment_status == "completed":
                            bar.update(timeout)  # Complete the progress bar
                            click.echo()
                            click.secho(
                                "✓ Deployment completed successfully!", fg="green", bold=True
                            )

                            # Show final status
                            final_deployment = status["deployment"]
                            if "completed_at" in final_deployment:
                                click.echo(f"  Completed at: {final_deployment['completed_at']}")

                            return
                        elif deployment_status == "failed":
                            bar.update(timeout)  # Complete the progress bar
                            click.echo()
                            click.secho("✗ Deployment failed!", fg="red", bold=True)
                            error_msg = status["deployment"].get("error", "Unknown error")
                            click.echo(f"  Error: {error_msg}")
                            ctx = click.get_current_context()
                            ctx.exit(1)

                        # Update progress
                        elapsed = int(time.time() - start_time)
                        bar.update(min(elapsed, timeout))
                        time.sleep(5)

                # Timeout reached
                click.echo()
                click.secho("⚠ Deployment timed out", fg="yellow", bold=True)
                click.echo(f"  Check status manually: {tracking['status_url']}")

            except KeyboardInterrupt:
                click.echo()
                click.echo("Deployment monitoring cancelled. Check status manually:")
                click.echo(f"  {tracking['status_url']}")

    except AuthenticationError as e:
        click.secho(f"AUTHENTICATION ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except InsufficientCreditsError as e:
        click.secho(f"INSUFFICIENT CREDITS: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except ValidationError as e:
        click.secho(f"VALIDATION ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except DeploymentError as e:
        click.secho(f"DEPLOYMENT ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)
    except Exception as e:
        click.secho(f"UNEXPECTED ERROR: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)


@cli.group()
def ui():
    """UI-related commands."""
    pass


@ui.command(name="validate")
@click.option("--file", "file_path", required=True, help="Path to UI spec JSON file")
def ui_validate(file_path: str):
    """Validate a UI spec JSON file against the current schema and Pydantic models."""
    import json
    from pixell.ui import validate_spec

    with open(Path(file_path), "r") as f:
        data = json.load(f)
    try:
        validate_spec(data)
        click.secho("UI spec is valid", fg="green")
    except Exception as e:
        click.secho(f"Invalid UI spec: {e}", fg="red")
        ctx = click.get_current_context()
        ctx.exit(1)


@ui.command(name="schema")
@click.option("--print", "print_only", is_flag=True, help="Print current UI schema JSON to stdout")
@click.option("--out", "out_path", required=False, help="Write schema JSON to file")
def ui_schema(print_only: bool, out_path: str | None):
    """Print or write the current UISpec JSON Schema."""
    import json
    from pixell.ui.spec import UISpec

    schema = UISpec.model_json_schema()
    if print_only:
        click.echo(json.dumps(schema, indent=2))
    elif out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(schema, indent=2))
        click.secho(f"Wrote schema to {out_path}", fg="green")
    else:
        click.echo("Use --print to print schema or --out to write to a file.")


@cli.command(name="validate-intents")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True),
    multiple=True,
    help="JSON file(s) containing protocol envelopes to validate",
)
@click.option("--stdin", is_flag=True, help="Read a single JSON envelope from stdin")
@click.option("--strict", is_flag=True, help="Fail on first error")
@click.option(
    "--intent-schema",
    type=click.Path(exists=True),
    help="Optional path to a per-intent params schema JSON file",
)
def validate_intents(file, stdin, strict, intent_schema):
    """Validate protocol envelopes (ui.event, action.result, ui.patch) against JSON Schemas.
    Also validates per-intent params for `ui.event` when schemas are available.
    """
    import json
    import sys
    from jsonschema import ValidationError
    from pixell.protocol.validate import validate_envelope
    from pixell.intent.validate import validate_intent_params

    def _validate_payload(payload: Dict[str, Any]) -> List[str]:
        errs: List[str] = []
        try:
            validate_envelope(payload)
        except ValidationError as exc:
            errs.append(f"Schema validation error: {exc.message}")
        except Exception as exc:
            errs.append(f"Validation error: {exc}")
        # Per-intent params validation for ui.event
        if payload.get("type") == "ui.event":
            try:
                validate_intent_params(
                    payload.get("intent", ""), payload.get("params", {}), intent_schema
                )
            except FileNotFoundError as exc:
                # Only warn if schema not provided/found
                errs.append(f"Intent params schema not found: {exc}")
            except ValidationError as exc:
                errs.append(f"Intent params validation error: {exc.message}")
        return errs

    errors: List[str] = []

    if stdin:
        try:
            payload = json.load(sys.stdin)
            errors.extend(_validate_payload(payload))
        except Exception as exc:
            errors.append(f"Failed to read stdin JSON: {exc}")

    for path in file:
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            errors.extend(_validate_payload(payload))
        except Exception as exc:
            errors.append(f"{path}: {exc}")
            if strict:
                break

    if errors:
        click.secho("FAILED:", fg="red", bold=True)
        for e in errors:
            click.echo(f"  - {e}")
        ctx = click.get_current_context()
        ctx.exit(1)
    else:
        click.secho("SUCCESS: All envelopes valid", fg="green", bold=True)
        ctx = click.get_current_context()
        ctx.exit(0)


@cli.command()
@click.option(
    "--topic",
    "-t",
    type=click.Choice(["build", "all"]),
    default="all",
    help="Specific topic to show guide for",
)
def guide(topic):
    """Display the agent development guide."""

    build_guide = """
# Pixell Build Guide

## Quick Start

To build an agent package (.apkg file), you need:
1. An agent.yaml manifest file
2. Source code in a src/ directory
3. The pixell build command

## Commands

  pixell build                    # Build in current directory
  pixell build --output ./dist    # Custom output directory
  pixell build --path ./my-agent  # Build from specific directory
  pixell validate                 # Validate before building

## Project Structure (Required)

  my-agent/
  |-- agent.yaml          # REQUIRED: Agent manifest
  |-- src/                # REQUIRED: Agent source code
  |   |-- __init__.py
  |   |-- main.py         # Your agent implementation
  |-- .env                # REQUIRED: Environment variables (included in APKG)
  |-- requirements.txt    # Optional: Python dependencies
  |-- mcp.json           # Optional: MCP configuration
  |-- README.md          # Optional: Documentation
  |-- LICENSE            # Optional: License file

## agent.yaml - Required Fields

  version: "1.0"                         # Manifest version (always "1.0")
  name: "my-agent-name"                  # Package name (lowercase, hyphens only)
  display_name: "My Agent"               # Human-readable name
  description: "What your agent does"    # Short description
  author: "Your Name"                    # Author name
  license: "MIT"                         # License (MIT, Apache-2.0, etc.)
  entrypoint: "src.main:handler"         # Module:function entry point
  metadata:
    version: "1.0.0"                     # Your agent's version

## agent.yaml - Optional Fields

  capabilities:                          # What your agent can do
    - "text-generation"
    - "data-processing"
  
  runtime: "python3.11"                  # Runtime (python3.9, python3.11, node18, node20, go1.21)
  
  environment:                           # Environment variables
    API_KEY: "${API_KEY}"
    DEBUG: "false"
  
  dependencies:                          # Python packages (if no requirements.txt)
    - "requests>=2.28.0"
    - "pandas>=2.0.0"
  
  mcp:                                   # MCP configuration
    enabled: true
    config_file: "mcp.json"

## Entry Point Example

  # src/main.py
  def handler(context):
      '''Main entry point for the agent.'''
      # Your agent logic here
      return {"status": "success", "data": result}

## Validation Rules

  - Name: lowercase letters, numbers, hyphens only
  - Entrypoint: must be in module:function format
  - Runtime: must be a supported runtime
  - Dependencies: must follow pip format (package>=1.0.0)
  - Structure: agent.yaml and src/ directory must exist

## Common Errors

  "Required file missing: agent.yaml"
  -> Ensure agent.yaml exists in project root

  "Source directory 'src/' not found"
  -> Create a src/ directory with your code

  "Entrypoint module not found"
  -> Check that entrypoint path matches your file structure
  -> Example: src.main:handler needs src/main.py with handler function

  "Invalid dependency format"
  -> Use pip format: package>=1.0.0, package==2.1.3

  "Name must be lowercase letters, numbers, and hyphens only"
  -> Valid: my-agent, text-processor-2
  -> Invalid: My_Agent, agent.v1, AGENT

## Build Output

The build creates: {agent-name}-{version}.apkg

This ZIP archive contains:
  - agent.yaml
  - src/ directory (excluding __pycache__ and .pyc)
  - Optional files (requirements.txt, README.md, LICENSE)
  - Package metadata (.pixell/package.json)

## Next Steps

After building your .apkg file:
  - Test locally: pixell run-dev --path .
  - Deploy: pixell deploy -f my-agent-1.0.0.apkg -a <app-id>
  - Install: pixell install my-agent-1.0.0.apkg

For more information, visit: https://github.com/pixell-global/pixell-kit
"""

    if topic == "build" or topic == "all":
        click.echo_via_pager(build_guide)

    if topic == "all":
        click.echo("\n" + "=" * 80 + "\n")
        click.echo("For specific topics, use: pixell guide --topic build")


@cli.group()
def config():
    """Manage Pixell configuration."""
    pass


@config.command("set")
@click.option("--api-key", "-k", help="Set API key")
@click.option("--app-id", "-a", help="Set app ID")
@click.option("--environment", "-e", help="Set default environment")
@click.option("--env-app-id", help="Set app ID for specific environment (format: env:app-id)")
@click.option(
    "--global", "is_global", is_flag=True, help="Set global configuration (default: project-level)"
)
def config_set(api_key, app_id, environment, env_app_id, is_global):
    """Set configuration values."""
    import json
    from pathlib import Path

    # Determine config file location
    if is_global:
        config_dir = Path.home() / ".pixell"
        config_file = config_dir / "config.json"
    else:
        config_dir = Path(".pixell")
        config_file = config_dir / "config.json"

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Load existing config
    config = {}
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
        except Exception:
            pass

    # Update config values
    if api_key:
        config["api_key"] = api_key
        click.secho(f"✓ API key set in {config_file}", fg="green")

    if app_id:
        config["app_id"] = app_id
        click.secho(f"✓ App ID set in {config_file}", fg="green")

    if environment:
        config["default_environment"] = environment
        click.secho(f"✓ Default environment set to '{environment}' in {config_file}", fg="green")

    if env_app_id:
        if ":" not in env_app_id:
            click.secho("ERROR: env-app-id must be in format 'environment:app-id'", fg="red")
            return

        env_name, env_app_id_value = env_app_id.split(":", 1)
        if "environments" not in config:
            config["environments"] = {}
        config["environments"][env_name] = {"app_id": env_app_id_value}
        click.secho(f"✓ App ID for environment '{env_name}' set in {config_file}", fg="green")

    # Save config
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    if not any([api_key, app_id, environment, env_app_id]):
        click.secho("No values provided. Use --help to see available options.", fg="yellow")


@config.command("show")
@click.option(
    "--global", "is_global", is_flag=True, help="Show global configuration (default: project-level)"
)
def config_show(is_global):
    """Show current configuration."""
    import json
    from pathlib import Path

    # Determine config file location
    if is_global:
        config_file = Path.home() / ".pixell" / "config.json"
        config_type = "Global"
    else:
        config_file = Path(".pixell") / "config.json"
        config_type = "Project"

    if not config_file.exists():
        click.secho(f"No {config_type.lower()} configuration found at {config_file}", fg="yellow")
        return

    try:
        with open(config_file) as f:
            config = json.load(f)

        click.secho(f"{config_type} Configuration ({config_file}):", fg="cyan", bold=True)
        click.echo(json.dumps(config, indent=2))
    except Exception as e:
        click.secho(f"Error reading config file: {e}", fg="red")


@config.command("init")
@click.option("--api-key", "-k", prompt="API Key", help="Your Pixell API key")
@click.option("--app-id", "-a", prompt="App ID", help="Your default app ID")
@click.option("--environment", "-e", default="prod", help="Default environment")
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    help="Initialize global configuration (default: project-level)",
)
def config_init(api_key, app_id, environment, is_global):
    """Initialize configuration with interactive setup."""
    import json
    from pathlib import Path

    # Determine config file location
    if is_global:
        config_dir = Path.home() / ".pixell"
        config_file = config_dir / "config.json"
    else:
        config_dir = Path(".pixell")
        config_file = config_dir / "config.json"

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create initial config
    config = {"api_key": api_key, "app_id": app_id, "default_environment": environment}

    # Save config
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    click.secho(f"✓ Configuration initialized at {config_file}", fg="green")
    click.secho(
        "You can now deploy without specifying --api-key and --app-id every time!", fg="cyan"
    )


if __name__ == "__main__":
    cli()
