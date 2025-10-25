import asyncio
import json
import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path

import click
import httpx
import questionary
from dotenv import set_key
from llama_deploy.cli.auth.client import (
    DeviceAuthorizationRequest,
    OIDCClient,
    PlatformAuthClient,
    PlatformAuthDiscoveryClient,
    TokenRequestDeviceCode,
    decode_jwt_claims,
    decode_jwt_claims_from_device_oidc,
)
from llama_deploy.cli.config._config import ConfigManager
from llama_deploy.cli.config.auth_service import AuthService
from llama_deploy.cli.config.env_service import service
from llama_deploy.cli.styles import (
    ACTIVE_INDICATOR,
    HEADER_COLOR,
    MUTED_COL,
    PRIMARY_COL,
    WARNING,
)
from llama_deploy.cli.utils.env_inject import env_vars_from_profile
from llama_deploy.core.client.manage_client import (
    ControlPlaneClient,
)
from llama_deploy.core.schema.projects import ProjectSummary
from rich import print as rprint
from rich.table import Table
from rich.text import Text

from ..app import app, console
from ..config.schema import Auth, DeviceOIDC
from ..options import global_options, interactive_option


# Create sub-applications for organizing commands
@app.group(
    help="Login to llama cloud control plane to manage deployments",
    no_args_is_help=True,
)
@global_options
def auth() -> None:
    """Login to llama cloud control plane"""
    pass


@auth.command("token")
@global_options
@click.option(
    "--project-id",
    help="Project ID to use for the login when creating non-interactively",
)
@click.option(
    "--api-key",
    help="API key to use for the login when creating non-interactively",
)
@interactive_option
def create_api_key_profile(
    project_id: str | None,
    api_key: str | None,
    interactive: bool,
) -> None:
    """Authenticate with an API key and create a profile in the current environment."""
    try:
        auth_svc = service.current_auth_service()

        # Non-interactive mode: require both api-key and project-id
        if not interactive:
            if not api_key or not project_id:
                raise click.ClickException(
                    "--api-key and --project-id are required in non-interactive mode"
                )
            created = auth_svc.create_profile_from_token(project_id, api_key)
            rprint(
                f"[green]Created API key profile '{created.name}' and set as current[/green]"
            )
            return

        # Interactive mode: prompt for token (masked) and validate
        token_value = api_key or _prompt_for_api_key()
        projects = _prompt_validate_api_key_and_list_projects(auth_svc, token_value)

        # Select or enter project ID
        selected_project_id = project_id or _select_or_enter_project(
            projects, auth_svc.env.requires_auth
        )
        if not selected_project_id:
            rprint(f"[{WARNING}]No project selected[/]")
            return

        # Create and set profile
        created = auth_svc.create_profile_from_token(selected_project_id, token_value)
        rprint(
            f"[green]Created API key profile '{created.name}' and set as current[/green]"
        )
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@auth.command("login")
@global_options
def device_login() -> None:
    """Login via web browser"""

    try:
        created = _create_device_profile()
        rprint(
            f"[green]Created login profile '{created.name}' and set as current[/green]"
        )

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@auth.command("list")
@global_options
def list_profiles() -> None:
    """List all logged in users/tokens"""
    try:
        auth_svc = service.current_auth_service()
        profiles = auth_svc.list_profiles()
        current = auth_svc.get_current_profile()

        if not profiles:
            rprint(f"[{WARNING}]No profiles found[/]")
            if auth_svc.env.requires_auth:
                rprint("Create one with: [cyan]llamactl auth login[/cyan]")
            else:
                rprint("Create one with: [cyan]llamactl auth token[/cyan]")
            return

        table = Table(show_edge=False, box=None, header_style=f"bold {HEADER_COLOR}")
        table.add_column("  Name", style=PRIMARY_COL)
        table.add_column("Active Project", style=MUTED_COL)

        for profile in profiles:
            text = Text()
            if profile == current:
                text.append("* ", style=ACTIVE_INDICATOR)
            else:
                text.append("  ")
            text.append(profile.name)
            active_project = profile.project_id or "-"
            table.add_row(
                text,
                active_project,
            )

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@auth.command("destroy", hidden=True)
@global_options
def destroy_database() -> None:
    """Destroy the database"""
    if not questionary.confirm(
        "Are you sure you want to destroy all of your local logins? This action cannot be undone."
    ).ask():
        return
    ConfigManager(init_database=False).destroy_database()
    rprint("[green]Database destroyed[/green]")


@auth.command("show-db", hidden=True)
@global_options
def config_database() -> None:
    """Config the database"""
    path = service.config_manager().db_path
    rprint(f"[bold]{path}[/bold]")


@auth.command("switch")
@global_options
@click.argument("name", required=False)
@interactive_option
def switch_profile(name: str | None, interactive: bool) -> None:
    """Switch to a different profile"""
    auth_svc = service.current_auth_service()
    try:
        selected_auth = _select_profile(auth_svc, name, interactive)
        if not selected_auth:
            rprint(f"[{WARNING}]No profile selected[/]")
            return

        auth_svc.set_current_profile(selected_auth.name)
        rprint(f"[green]Switched to profile '{selected_auth.name}'[/green]")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@auth.command("logout")
@global_options
@click.argument("name", required=False)
@interactive_option
def delete_profile(name: str | None, interactive: bool) -> None:
    """Logout from a profile and wipe all associated data"""
    try:
        auth_svc = service.current_auth_service()
        auth = _select_profile(auth_svc, name, interactive)
        if not auth:
            rprint(f"[{WARNING}]No profile selected[/]")
            return

        if asyncio.run(auth_svc.delete_profile(auth.name)):
            rprint(f"[green]Logged out from '{auth.name}'[/green]")
        else:
            rprint(f"[red]Profile '{auth.name}' not found[/red]")

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


# Very simple introspection: decode current token via provider JWKS
@auth.command("me", hidden=True)
@global_options
def me() -> None:
    """Print JWT claims for the current profile's token using provider JWKS.

    Assumes the stored API key is a JWT (e.g., OIDC id_token).
    """
    try:
        auth_svc = service.current_auth_service()
        profile = auth_svc.get_current_profile()
        if not profile or not profile.device_oidc:
            raise click.ClickException(
                "No OIDC profile selected. Run `llamactl auth login` or switch to an existing OIDC profile."
            )

        claims = asyncio.run(decode_jwt_claims_from_device_oidc(profile.device_oidc))
        click.echo(json.dumps(claims, indent=2, sort_keys=True))
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


# Projects commands
@auth.command("project")
@click.argument("project_id", required=False)
@interactive_option
@global_options
def change_project(project_id: str | None, interactive: bool) -> None:
    """Change the active project for the current profile"""
    profile = validate_authenticated_profile(interactive)
    if project_id and profile.project_id == project_id:
        return
    auth_svc = service.current_auth_service()
    if project_id:
        if auth_svc.env.requires_auth:
            projects = _list_projects(auth_svc)
            if not next(
                (project for project in projects if project.project_id == project_id),
                None,
            ):
                raise click.ClickException(f"Project {project_id} not found")
        auth_svc.set_project(profile.name, project_id)
        rprint(f"Set active project to [bold green]{project_id}[/]")
        return
    if not interactive:
        raise click.ClickException(
            "No --project-id provided. Run `llamactl auth project --help` for more information."
        )
    try:
        projects = _list_projects(auth_svc)

        if not projects:
            rprint(f"[{WARNING}]No projects found[/]")
            return
        result = questionary.select(
            "Select a project",
            choices=[
                questionary.Choice(
                    title=f"{project.project_name} ({project.deployment_count} deployments)",
                    value=project.project_id,
                )
                for project in projects
            ]
            + (
                [questionary.Choice(title="Create new project", value="__CREATE__")]
                if not auth_svc.env.requires_auth
                else []
            ),
        ).ask()
        if result == "__CREATE__":
            project_id = questionary.text("Enter project ID").ask()
            result = project_id
        if result:
            selected_project = next(
                (project for project in projects if project.project_id == result), None
            )
            name = selected_project.project_name if selected_project else result
            auth_svc.set_project(profile.name, result)
            rprint(f"Set active project to [bold {PRIMARY_COL}]{name}[/]")
        else:
            rprint(f"[{WARNING}]No project selected[/]")
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@auth.command("inject")
@global_options
@click.option(
    "--env-file",
    "env_file",
    default=Path(".env"),
    type=click.Path(dir_okay=False, resolve_path=True, path_type=Path),
    help="Path to the .env file to write",
)
@interactive_option
def inject_env_vars(
    env_file: Path,
    interactive: bool,
) -> None:
    """Inject auth environment variables into a .env file.

    Writes LLAMA_CLOUD_API_KEY, LLAMA_CLOUD_BASE_URL, and LLAMA_DEPLOY_PROJECT_ID
    based on the current profile. Always overwrites and creates the file if missing.
    """
    try:
        auth_svc = service.current_auth_service()
        profile = auth_svc.get_current_profile()
        if not profile:
            if interactive:
                profile = validate_authenticated_profile(True)
            else:
                raise click.ClickException(
                    "No profile configured. Run `llamactl auth token` to create a profile."
                )
        if not profile.api_key:
            raise click.ClickException(
                "Current profile is unauthenticated (missing API key)"
            )

        vars = env_vars_from_profile(profile)
        if not vars:
            rprint(f"[{WARNING}]No variables to inject[/]")
            return
        env_file.parent.mkdir(parents=True, exist_ok=True)
        for key, value in vars.items():
            set_key(str(env_file), key, value)
        rel = os.path.relpath(env_file, Path.cwd())
        rprint(
            f"[green]Wrote environment variables: {', '.join(vars.keys())} to {rel}[/green]"
        )
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


def _auto_device_name() -> str:
    try:
        if sys.platform == "darwin":  # macOS
            return (
                subprocess.check_output(["scutil", "--get", "ComputerName"])
                .decode()
                .strip()
            )
        elif sys.platform.startswith("win"):
            return os.environ["COMPUTERNAME"]
        else:  # Linux / Unix
            return platform.node()
    except Exception:
        return platform.node()


async def _create_or_update_agent_api_key(auth_svc: AuthService, profile: Auth) -> None:
    """
    Mutates and updates the profile with an agent API key if it does not exist or is invalid.
    """
    if profile.api_key is not None:
        async with PlatformAuthClient(profile.api_url, profile.api_key) as client:
            try:
                await client.me()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # must have been deleted
                    profile.api_key = None
                    profile.api_key_id = None
                else:
                    raise
    if profile.api_key is None:
        async with auth_svc.profile_client(profile) as client:
            name = f"{profile.name} llamactl on {profile.device_oidc.device_name if profile.device_oidc else 'unknown'}"
            api_key = await client.create_agent_api_key(name)
        profile.api_key = api_key.token
        profile.api_key_id = api_key.id
        auth_svc.update_profile(profile)


def _create_device_profile() -> Auth:
    auth_svc = service.current_auth_service()
    if not auth_svc.env.requires_auth:
        raise click.ClickException("This environment does not support authentication")

    base_url = auth_svc.env.api_url.rstrip("/")

    oidc_device = asyncio.run(_run_device_authentication(base_url))

    # Obtain or prompt for project ID and create profile
    projects = _list_projects(auth_svc, oidc_device.device_access_token)
    selected_project_id = _select_or_enter_project(projects, True)
    if not selected_project_id:
        raise click.ClickException(
            "Project is required. Does this user have access to any projects?"
        )
    created = auth_svc.create_or_update_profile_from_oidc(
        selected_project_id, oidc_device
    )
    asyncio.run(_create_or_update_agent_api_key(auth_svc, created))
    return created


async def _run_device_authentication(base_url: str) -> DeviceOIDC:
    device_name = _auto_device_name()
    # 1) Discover upstream and CLI client_id via client
    async with PlatformAuthDiscoveryClient(base_url) as discovery:
        disc = await discovery.oidc_discovery()
    upstream = disc.discovery_url
    client_ids = disc.client_ids or {}
    client_ids_list = list(client_ids.values())
    client_id = client_ids.get("cli") or (
        client_ids_list[0] if len(client_ids_list) == 1 else None
    )
    if not client_id:
        raise click.ClickException(
            "Expected 'cli' Client ID not found from auth discovery"
        )

    # 2) Device flow via typed OIDC client
    async with OIDCClient() as oidc:
        provider = await oidc.fetch_provider_configuration(upstream)
        device_endpoint = provider.device_authorization_endpoint
        token_endpoint = provider.token_endpoint
        if not device_endpoint or not token_endpoint:
            raise click.ClickException("Device Authorization not supported by provider")

        scope_value = " ".join(sorted({"openid", "profile", "email", "offline_access"}))

        # 3) Start device authorization
        da = await oidc.device_authorization(
            device_endpoint,
            DeviceAuthorizationRequest(client_id=client_id, scope=scope_value),
        )

        rprint(
            "[bold]complete authentication by visiting the verification URI and confirming the device:[/bold]"
        )
        if da.verification_uri:
            rprint(
                f"Verification URI: {da.verification_uri} (will open in your browser if supported)"
            )
        if da.user_code:
            rprint(f"User Code: {da.user_code} to confirm the device")
        if da.verification_uri_complete:
            try:
                webbrowser.open(da.verification_uri_complete)
            except Exception:
                pass

        # 4) Poll token endpoint
        interval = int(da.interval or 5)
        while True:
            await asyncio.sleep(interval)
            token = await oidc.token_with_device_code(
                token_endpoint,
                TokenRequestDeviceCode(
                    device_code=da.device_code,
                    client_id=client_id,
                ),
            )
            if token.error in {"authorization_pending", "slow_down"}:
                if token.error == "slow_down":
                    interval += 5
                continue
            if token.error:
                raise click.ClickException(
                    f"Token polling failed: {token.error} {token.error_description or ''}"
                )
            if token.id_token:
                if not token.access_token:
                    raise click.ClickException(
                        "Device flow failed: token response missing access_token"
                    )
                claims = await decode_jwt_claims(token.id_token, provider.jwks_uri)
                email = claims.get("email")
                if not email:
                    raise click.ClickException(
                        "Device flow failed: email not found in token"
                    )
                user_id = claims.get("sub") or email
                return DeviceOIDC(
                    device_name=device_name,
                    email=email,
                    user_id=user_id,
                    client_id=client_id,
                    discovery_url=upstream,
                    device_access_token=token.access_token,
                    device_refresh_token=token.refresh_token,
                    device_id_token=token.id_token,
                )
            raise click.ClickException("Device flow failed: unexpected token response")


def validate_authenticated_profile(interactive: bool) -> Auth:
    """Validate that the user is authenticated within the current environment.

    - If there is a current profile, return it.
    - If multiple profiles exist in the current environment, prompt to select in interactive mode.
    - If none exist:
      - If environment requires_auth: run token flow inline.
      - Else: create profile without token after selecting a project.
    """

    auth_svc = service.current_auth_service()
    existing = auth_svc.get_current_profile()
    if existing:
        return existing

    if not interactive:
        raise click.ClickException(
            "No profile configured. Run `llamactl auth token` to create a profile."
        )

    # Filter profiles by current environment
    env_profiles = auth_svc.list_profiles()
    current_env = auth_svc.env

    if len(env_profiles) > 1:
        # Prompt to select
        choice: Auth | None = questionary.select(
            "Select profile",
            choices=[questionary.Choice(title=p.name, value=p) for p in env_profiles],
        ).ask()
        if not choice:
            raise click.ClickException("No profile selected")
        auth_svc.set_current_profile(choice.name)
        return choice
    if len(env_profiles) == 1:
        only = env_profiles[0]
        auth_svc.set_current_profile(only.name)
        return only

    # No profiles exist for this env
    if current_env.requires_auth:
        # Inline token flow
        created = _create_device_profile()
        return created
    else:
        # No auth required: select project and create a default profile without token
        project_id: str | None = questionary.text("Enter project ID").ask()
        if not project_id:
            raise click.ClickException("No project ID provided")
        created = auth_svc.create_profile_from_token(project_id, None)
        return created


# -----------------------------
# Helpers for token/profile flow
# -----------------------------


def _prompt_for_api_key() -> str:
    entered = questionary.password("Enter API key token to login").ask()
    if entered:
        return entered.strip()
    raise click.ClickException("No API key entered")


def _list_projects(
    auth_svc: AuthService,
    api_key: str | None = None,
) -> list[ProjectSummary]:
    async def _run():
        profile = auth_svc.get_current_profile()
        async with ControlPlaneClient.ctx(
            auth_svc.env.api_url,
            api_key or (profile.api_key if profile else None),
            None if api_key is not None else auth_svc.auth_middleware(profile),
        ) as client:
            return await client.list_projects()

    return asyncio.run(_run())


def _prompt_validate_api_key_and_list_projects(
    auth_svc: AuthService, api_key: str
) -> list[ProjectSummary]:
    try:
        return _list_projects(auth_svc, api_key)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            rprint("[red]Invalid API key. Please try again.[/red]")
            return _prompt_validate_api_key_and_list_projects(
                auth_svc, _prompt_for_api_key()
            )
        if e.response.status_code == 403:
            rprint("[red]This environment requires a valid API key.[/red]")
            return _prompt_validate_api_key_and_list_projects(
                auth_svc, _prompt_for_api_key()
            )
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to validate API key: {e}")


def _select_or_enter_project(
    projects: list[ProjectSummary], requires_auth: bool
) -> str | None:
    if not projects:
        return None
    # select the only authorized project if there is only one
    elif len(projects) == 1 and requires_auth:
        return projects[0].project_id
    else:
        choice = questionary.select(
            "Select a project",
            choices=[
                questionary.Choice(
                    title=f"{p.project_name} ({p.deployment_count} deployments)",
                    value=p.project_id,
                )
                for p in projects
            ],
        ).ask()
        return choice


def _token_flow_for_env(auth_service: AuthService) -> Auth:
    token_value = _prompt_for_api_key()
    projects = _prompt_validate_api_key_and_list_projects(auth_service, token_value)
    project_id = _select_or_enter_project(projects, auth_service.env.requires_auth)
    if not project_id:
        raise click.ClickException("No project selected")
    created = auth_service.create_profile_from_token(project_id, token_value)
    return created


def _select_profile(
    auth_svc: AuthService, profile_name: str | None, is_interactive: bool
) -> Auth | None:
    """
    Select a profile interactively if name not provided.
    Returns the selected profile name or None if cancelled.

    In non-interactive sessions, returns None if profile_name is not provided.
    """
    if profile_name:
        profile = auth_svc.get_profile(profile_name)
        if profile:
            return profile

    # Don't attempt interactive selection in non-interactive sessions
    if not is_interactive:
        return None

    try:
        profiles = auth_svc.list_profiles()

        if not profiles:
            rprint(f"[{WARNING}]No profiles found[/]")
            return None

        choices = []
        current = auth_svc.get_current_profile()

        for profile in profiles:
            title = f"{profile.name} ({profile.api_url})"
            if profile == current:
                title += " [current]"
            choices.append(questionary.Choice(title=title, value=profile))

        return questionary.select("Select profile:", choices=choices).ask()

    except Exception as e:
        rprint(f"[red]Error loading profiles: {e}[/red]")
        return None
