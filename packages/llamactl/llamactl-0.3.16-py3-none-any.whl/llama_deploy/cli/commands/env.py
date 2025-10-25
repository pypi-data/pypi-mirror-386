from importlib import metadata as importlib_metadata

import click
import questionary
from llama_deploy.cli.config.schema import Environment
from llama_deploy.cli.styles import (
    ACTIVE_INDICATOR,
    HEADER_COLOR,
    MUTED_COL,
    PRIMARY_COL,
    WARNING,
)
from packaging import version as packaging_version
from rich import print as rprint
from rich.table import Table
from rich.text import Text

from ..app import console
from ..config.env_service import service
from ..options import global_options, interactive_option
from .auth import auth


@auth.group(
    name="env",
    help="Manage environments (control plane API URLs)",
    no_args_is_help=True,
)
@global_options
def env_group() -> None:
    pass


@env_group.command("list")
@global_options
def list_environments_cmd() -> None:
    try:
        envs = service.list_environments()
        current_env = service.get_current_environment()

        if not envs:
            rprint(f"[{WARNING}]No environments found[/]")
            return

        table = Table(show_edge=False, box=None, header_style=f"bold {HEADER_COLOR}")
        table.add_column("  API URL", style=PRIMARY_COL)
        table.add_column("Requires Auth", style=MUTED_COL)

        for env in envs:
            text = Text()
            if env == current_env:
                text.append("* ", style=ACTIVE_INDICATOR)
            else:
                text.append("  ")
            text.append(env.api_url)
            table.add_row(text, Text("true" if env.requires_auth else "false"))

        console.print(table)
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        raise click.Abort()


@env_group.command("add")
@click.argument("api_url", required=False)
@interactive_option
@global_options
def add_environment_cmd(api_url: str | None, interactive: bool) -> None:
    try:
        if not api_url:
            if not interactive:
                raise click.ClickException("API URL is required when not interactive")
            current_env = service.get_current_environment()
            entered = questionary.text(
                "Enter control plane API URL", default=current_env.api_url
            ).ask()
            if not entered:
                rprint(f"[{WARNING}]No environment entered[/]")
                return
            api_url = entered.strip()

        api_url = api_url.rstrip("/")
        env = service.probe_environment(api_url)
        service.create_or_update_environment(env)
        rprint(
            f"[green]Added environment[/green] {env.api_url} (requires_auth={env.requires_auth}, min_llamactl_version={env.min_llamactl_version or '-'})."
        )
        _maybe_warn_min_version(env.min_llamactl_version)
    except Exception as e:
        rprint(f"[red]Failed to add environment: {e}[/red]")
        raise click.Abort()


@env_group.command("delete")
@click.argument("api_url", required=False)
@interactive_option
@global_options
def delete_environment_cmd(api_url: str | None, interactive: bool) -> None:
    try:
        if not api_url:
            if not interactive:
                raise click.ClickException("API URL is required when not interactive")
            result = _select_environment(
                service.list_environments(),
                service.get_current_environment(),
                "Select environment to delete",
            )

            if not result:
                rprint(f"[{WARNING}]No environment selected[/]")
                return
            api_url = result.api_url

        api_url = api_url.rstrip("/")
        deleted = service.delete_environment(api_url)
        if not deleted:
            raise click.ClickException(f"Environment '{api_url}' not found")
        rprint(
            f"[green]Deleted environment[/green] {api_url} and all associated profiles"
        )
    except Exception as e:
        rprint(f"[red]Failed to delete environment: {e}[/red]")
        raise click.Abort()


@env_group.command("switch")
@click.argument("api_url", required=False)
@interactive_option
@global_options
def switch_environment_cmd(api_url: str | None, interactive: bool) -> None:
    try:
        selected_url = api_url

        if not selected_url and interactive:
            result = _select_environment(
                service.list_environments(),
                service.get_current_environment(),
                "Select environment",
            )
            if not result:
                rprint(f"[{WARNING}]No environment selected[/]")
                return
            selected_url = result.api_url

        if not selected_url:
            if interactive:
                rprint(f"[{WARNING}]No environment selected[/]")
                return
            raise click.ClickException("API URL is required when not interactive")

        selected_url = selected_url.rstrip("/")

        # Ensure environment exists and switch
        env = service.switch_environment(selected_url)
        try:
            env = service.auto_update_env(env)
        except Exception as e:
            rprint(f"[{WARNING}]Failed to resolve environment: {e}[/]")
            return
        service.current_auth_service().select_any_profile()
        rprint(f"[green]Switched to environment[/green] {env.api_url}")
        _maybe_warn_min_version(env.min_llamactl_version)
    except Exception as e:
        rprint(f"[red]Failed to switch environment: {e}[/red]")
        raise click.Abort()


def _get_cli_version() -> str | None:
    try:
        return importlib_metadata.version("llamactl")
    except Exception:
        return None


def _maybe_warn_min_version(min_required: str | None) -> None:
    if not min_required:
        return
    current = _get_cli_version()
    if not current:
        return
    try:
        if packaging_version.parse(current) < packaging_version.parse(min_required):
            rprint(
                f"[{WARNING}]Warning:[/] This environment requires llamactl >= [bold]{min_required}[/bold], you have [bold]{current}[/bold]."
            )
    except Exception:
        # If packaging is not available or parsing fails, skip strict comparison
        pass


def _select_environment(
    envs: list[Environment],
    current_env: Environment,
    message: str = "Select environment",
) -> Environment | None:
    envs = service.list_environments()
    current_env = service.get_current_environment()
    if not envs:
        raise click.ClickException(
            "No environments found. This is a bug and shouldn't happen."
        )
    return questionary.select(
        message,
        choices=[
            questionary.Choice(
                title=f"{env.api_url} {'(current)' if env.api_url == current_env.api_url else ''}",
                value=env,
            )
            for env in envs
        ],
    ).ask()
