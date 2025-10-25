"""Git repository validation widget for Textual CLI"""

import logging
import webbrowser
from typing import Literal, cast

from llama_deploy.cli.client import get_project_client as get_client
from llama_deploy.cli.textual.github_callback_server import GitHubCallbackServer
from llama_deploy.cli.textual.llama_loader import PixelLlamaLoader
from llama_deploy.core.schema.git_validation import RepositoryValidationResponse
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Widget
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, Static

logger = logging.getLogger(__name__)


class ValidationResultMessage(Message):
    """Message sent when validation completes successfully"""

    def __init__(self, repo_url: str, pat: str | None = None):
        super().__init__()
        self.repo_url = repo_url
        self.pat = pat


class ValidationCancelMessage(Message):
    """Message sent when validation is cancelled"""

    pass


States = Literal["validating", "options", "pat_input", "github_auth", "success"]


class GitValidationWidget(Widget):
    """Widget for handling repository validation and GitHub App authentication"""

    DEFAULT_CSS = """
    GitValidationWidget {
        layout: vertical;
        height: auto;
    }


    .validation-options {
        layout: vertical;
        margin-top: 1;
        align: center middle;
        height: auto;
    }

    .validation-options Button {
        max-width: 40;
    }

    .option-button {
        margin-bottom: 1;
        width: 100%;
    }

    .pat-input-section {
        layout: vertical;
        margin: 2 0;
        border: solid $primary-muted;
        padding: 1;
    }

    .url-link {
        text-style: underline;
        color: $accent;
    }

    """

    validation_response: reactive[RepositoryValidationResponse | None] = reactive(
        cast(RepositoryValidationResponse | None, None), recompose=True
    )
    current_state: reactive[States] = reactive(
        cast(States, "validating"), recompose=True
    )
    error_message: reactive[str] = reactive("", recompose=True)
    repo_url: str = ""
    deployment_id: str | None = None
    github_callback_server: GitHubCallbackServer | None = None

    def __init__(
        self,
        repo_url: str,
        deployment_id: str | None = None,
        pat: str | None = None,
    ):
        super().__init__()
        self.repo_url = repo_url
        self.deployment_id = deployment_id
        self.initial_pat = pat

    def on_mount(self) -> None:
        """Start validation when widget mounts"""
        self.run_worker(self._validate_repository(self.initial_pat))

    def compose(self) -> ComposeResult:
        yield Static("Repository Validation", classes="primary-message")

        if self.current_state == "validating":
            yield Static("Validating repository access...")
            yield PixelLlamaLoader(classes="mb-1")

        elif self.current_state == "options":
            if not self.validation_response:
                yield Static(self.error_message, classes="error-message")
            else:
                yield Static(self.validation_response.message, classes="error-message")

            with Widget(classes="validation-options"):
                if self.validation_response is not None:
                    if self.validation_response.github_app_installation_url:
                        # GitHub repository with app available
                        yield Button(
                            "Install GitHub App (Recommended)",
                            id="install_github_app",
                            classes="option-button",
                            variant="primary",
                            compact=True,
                        )
                        yield Button(
                            "Use Personal Access Token (PAT)",
                            id="use_pat",
                            classes="option-button",
                            variant="primary",
                            compact=True,
                        )
                    else:
                        # Non-GitHub or GitHub without app
                        yield Button(
                            "Retry with Personal Access Token (PAT)",
                            id="use_pat",
                            classes="option-button",
                            variant="primary",
                            compact=True,
                        )
                yield Button(
                    "Save Anyway",
                    id="save_anyway",
                    classes="option-button",
                    variant="warning",
                    compact=True,
                )

        elif self.current_state == "pat_input":
            if self.error_message:
                yield Static(self.error_message, classes="text-error mb-1")

            with Widget(classes="two-column-form-grid mb-1"):
                yield Label("Personal Access Token:", classes="form-label")
                yield Input(
                    placeholder="Enter your PAT",
                    password=True,
                    id="pat_input",
                    compact=True,
                )

        elif self.current_state == "github_auth":
            yield Static("Waiting for GitHub App installation...")
            if self.error_message:
                yield Static(self.error_message, classes="error-message mt-1")
            yield PixelLlamaLoader(classes="mb-1")

            if (
                self.validation_response
                and self.validation_response.github_app_installation_url
            ):
                yield Static(
                    Content.from_markup(
                        f'Open this URL to Install: [link="{self.validation_response.github_app_installation_url}"]{self.validation_response.github_app_installation_url}[/link]'
                    ),
                    classes="mb-1",
                )

        elif self.current_state == "success":
            yield Static("Validation Successful", classes="text-success mb-2")
            if self.error_message:
                yield Static(self.error_message, classes="text-warning mb-2")

        # Single button row for all states
        with HorizontalGroup(classes="button-row"):
            if self.current_state == "pat_input":
                yield Button(
                    "Validate", id="validate_pat", variant="primary", compact=True
                )
                yield Button(
                    "Back", id="back_to_options", variant="default", compact=True
                )
            elif self.current_state == "github_auth":
                yield Button(
                    "Recheck", id="recheck_github", variant="primary", compact=True
                )
                yield Button(
                    "Cancel", id="cancel_github_auth", variant="default", compact=True
                )
            elif self.current_state == "success":
                yield Button(
                    "Continue", id="continue_success", variant="primary", compact=True
                )
            # Always show cancel button
            yield Button("Back to Edit", id="cancel", variant="default", compact=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "install_github_app":
            self._start_github_auth()
        elif event.button.id == "use_pat":
            self.current_state = "pat_input"
            self.error_message = ""
        elif event.button.id == "save_anyway":
            logging.info("saving anyway")
            self.post_message(ValidationResultMessage(self.repo_url))
        elif event.button.id == "validate_pat":
            self._validate_with_pat()
        elif event.button.id == "back_to_options":
            self.current_state = "options"
            self.error_message = ""
        elif event.button.id == "cancel_github_auth":
            self.run_worker(self._cancel_github_auth())
        elif event.button.id == "recheck_github":
            self.run_worker(self._recheck_github_auth())
        elif event.button.id == "continue_success":
            # For PAT obsolescence case, send empty PAT to clear it
            pat_to_send = (
                ""
                if self.validation_response and self.validation_response.pat_is_obsolete
                else None
            )
            self.post_message(ValidationResultMessage(self.repo_url, pat_to_send))
        elif event.button.id == "cancel":
            self.post_message(ValidationCancelMessage())

    def _start_github_auth(self) -> None:
        """Start GitHub App authentication flow"""
        if (
            not self.validation_response
            or not self.validation_response.github_app_installation_url
        ):
            return

        self.current_state = "github_auth"

        # Open browser to GitHub App installation URL
        try:
            webbrowser.open(self.validation_response.github_app_installation_url)
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")

        # # Start callback server
        self.github_callback_server = GitHubCallbackServer()
        self.run_worker(self._wait_for_callback())

    async def _cancel_github_auth(self) -> None:
        """Cancel GitHub authentication and return to options"""
        if self.github_callback_server:
            await self.github_callback_server.stop()
            self.github_callback_server = None
        self.current_state = "options"

    def _validate_with_pat(self) -> None:
        """Validate repository with PAT from input"""
        pat_input = self.query_one("#pat_input", Input)
        pat = pat_input.value.strip()

        if not pat:
            self.error_message = "Please enter a Personal Access Token"
            return

        self.run_worker(self._validate_repository(pat))

    async def _validate_repository(self, pat: str | None = None) -> None:
        """Perform repository validation"""
        self.current_state = "validating"
        self.error_message = ""
        try:
            client = get_client()
            self.validation_response = await client.validate_repository(
                repo_url=self.repo_url, deployment_id=self.deployment_id, pat=pat
            )

            resp = self.validation_response
            if resp and resp.accessible:
                # Success - post result message with appropriate messaging
                if resp.pat_is_obsolete:
                    # Show success message about PAT obsolescence before proceeding
                    self.current_state = "success"
                    self.error_message = "Repository accessible via GitHub App. Your Personal Access Token is now obsolete and will be removed."
                else:
                    self.post_message(ValidationResultMessage(self.repo_url, pat))
            else:
                # Failed - show options
                self.current_state = "options"

        except Exception as e:
            self.error_message = f"Validation failed: {e}"
            self.current_state = "options"

    async def _recheck_github_auth(self) -> None:
        """Re-validate repository while staying in github_auth state"""
        self.error_message = ""
        try:
            client = get_client()
            self.validation_response = await client.validate_repository(
                repo_url=self.repo_url, deployment_id=self.deployment_id
            )

            resp = self.validation_response
            if resp and resp.accessible:
                # Success - post result message with appropriate messaging
                self.current_state = "success"
                self.post_message(
                    ValidationResultMessage(
                        self.repo_url, "" if resp.pat_is_obsolete else None
                    )
                )
            else:
                # Failed - stay in github_auth and show error
                self.error_message = (
                    f"Still not accessible: {resp.message if resp else ''}"
                )

        except Exception as e:
            # Failed - stay in github_auth and show error
            self.error_message = f"Recheck failed: {e}"

    async def _wait_for_callback(self) -> None:
        """Wait for GitHub callback and re-validate"""
        if not self.github_callback_server:
            return

        try:
            # Wait for callback with timeout
            await self.github_callback_server.start_and_wait(timeout=300)
            # Process callback - re-validate without PAT since GitHub App should now be available
            await self._validate_repository()

        except TimeoutError:
            logger.info("callback timed out")
            self.error_message = "Authentication timed out"
            self.current_state = "options"
        except Exception as e:
            logger.error("callback failed", exc_info=True)
            self.error_message = f"Callback failed: {e}"
            self.current_state = "options"
        finally:
            if self.github_callback_server:
                self.github_callback_server.stop()
                self.github_callback_server = None
