"""Utility helpers for rendering the CLI agent session with a richer TUI."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field
from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, OptionList, RichLog, Static, TextArea
from textual.widgets.option_list import Option

_PROMPT_PLACEHOLDER = "Extend the Planar workflow with..."
_FOLLOW_UP_PROMPT = "Provide the next instruction (or type 'exit' to finish)"
_PERMISSION_FEEDBACK_PLACEHOLDER = "Share feedback or press Enter to skip"
ACTIONS_HELP_TEXT = "Use ↑/↓ to choose · Enter to select · Esc to cancel"

PermissionChoice = Literal["allow", "allow_with_updates", "deny"]


class PromptTextArea(TextArea):
    """TextArea that submits on Enter and uses modifiers for new lines."""

    async def _on_key(self, event: events.Key) -> None:
        key = event.key

        if key in {"enter", "return"}:
            event.stop()
            event.prevent_default()
            submit = getattr(self.app, "action_submit_prompt", None)
            if callable(submit):
                submit()
            return

        if (
            key in {"ctrl+m", "ctrl+j"}
            or ("+enter" in key and key != "enter")
            or ("+return" in key and key != "return")
        ):
            event.stop()
            event.prevent_default()
            self._restart_blink()
            start, end = self.selection
            self._replace_via_keyboard("\n", start, end)
            return

        await super()._on_key(event)


def _format_tool_payload(
    tool_name: str, payload: object, *, language_hint: str | None = None
) -> RenderableType:
    """Return a renderable for a tool payload."""
    if payload is None:
        return Text("(no payload)", style="dim")

    if isinstance(payload, str):
        if language_hint:
            return Syntax(payload, language_hint, theme="ansi_dark", word_wrap=True)
        return Text(payload)

    if isinstance(payload, (bytes, bytearray)):
        return Syntax(
            payload.decode("utf-8", errors="replace"), language_hint or "text"
        )

    if (tool_name == "Edit") and isinstance(payload, dict):
        # For now just show the file path being edited
        return Syntax(payload["file_path"], "text", theme="ansi_dark", word_wrap=True)

    try:
        serialized = json.dumps(payload, indent=2, sort_keys=True)
    except TypeError:
        return Text(repr(payload), style="grey50")

    return Syntax(serialized, "json", theme="ansi_dark", word_wrap=True)


# Command definitions -----------------------------------------------------------------


class CommandPayloadBase(BaseModel):
    """Payload carried by a UI command."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class ShutdownPayload(CommandPayloadBase):
    name: Literal["shutdown"] = "shutdown"


class ShowBannerPayload(CommandPayloadBase):
    name: Literal["show_banner"] = "show_banner"
    instruction: str | None = None


class RenderUserPromptPayload(CommandPayloadBase):
    name: Literal["render_user_prompt"] = "render_user_prompt"
    prompt_text: str
    follow_up: bool = False


class RenderAssistantTextPayload(CommandPayloadBase):
    name: Literal["render_assistant_text"] = "render_assistant_text"
    text: str


class RenderToolUsePayload(CommandPayloadBase):
    name: Literal["render_tool_use"] = "render_tool_use"
    tool_name: str
    payload: Any
    invocation_number: int


class RenderPermissionRequestPayload(CommandPayloadBase):
    name: Literal["render_permission_request"] = "render_permission_request"
    tool_name: str
    payload: Any
    suggestions: list[Any] = Field(default_factory=list)


class RenderSessionResultPayload(CommandPayloadBase):
    name: Literal["render_session_result"] = "render_session_result"
    duration_ms: int | None = None
    total_cost: float | None = None


class RenderChangedFilesPayload(CommandPayloadBase):
    name: Literal["render_changed_files"] = "render_changed_files"
    files: list[str]


class RenderPlanPreviewPayload(CommandPayloadBase):
    name: Literal["render_plan_preview"] = "render_plan_preview"
    plan_text: str


class ShowStatusPayload(CommandPayloadBase):
    name: Literal["show_status"] = "show_status"
    message: str
    style: str = "grey50"


class ClearStatusPayload(CommandPayloadBase):
    name: Literal["clear_status"] = "clear_status"


class LogTextPayload(CommandPayloadBase):
    name: Literal["log_text"] = "log_text"
    text: str
    style: str | None = None


class PromptInputPayload(CommandPayloadBase):
    name: Literal["prompt_input"] = "prompt_input"
    message: str
    placeholder: str
    initial_text: str = ""
    multiline: bool
    helper_text: str


class PromptOption(CommandPayloadBase):
    label: str
    value: str


class PromptOptionsPayload(CommandPayloadBase):
    name: Literal["prompt_options"] = "prompt_options"
    message: str
    helper_text: str
    options: list[PromptOption]


UICommand = Annotated[
    ShutdownPayload
    | ShowBannerPayload
    | RenderUserPromptPayload
    | RenderAssistantTextPayload
    | RenderToolUsePayload
    | RenderPermissionRequestPayload
    | RenderSessionResultPayload
    | RenderChangedFilesPayload
    | RenderPlanPreviewPayload
    | ShowStatusPayload
    | ClearStatusPayload
    | LogTextPayload
    | PromptInputPayload
    | PromptOptionsPayload,
    Field(discriminator="name"),
]


@dataclass(slots=True)
class UICommandEnvelope:
    """Command plus runtime metadata used by the Textual driver."""

    payload: UICommand
    future: asyncio.Future[Any] | None = None
    defer_result: bool = False


# The CLI drives this app through a command queue so UI mutations stay on Textual's task.
class AgentTextualApp(App[None]):
    """Textual application that renders the agent transcript and prompts."""

    CSS = """
    Screen {
        layout: grid;
        grid-rows: auto 1fr auto auto;
        grid-columns: 1fr;
    }

    #banner {
        padding: 1 2;
        border-bottom: solid $surface-darken-2;
    }

    #banner-hint {
        color: $text-muted;
        padding-top: 0;
    }

    #log {
        padding: 1 2;
        overflow-y: auto;
        scrollbar-size: 0 1;
    }

    #status {
        padding: 0 2;
        color: $text-muted;
    }

    #prompt-container {
        padding: 1 2 2 2;
        border-top: solid $surface-darken-2;
    }

    #prompt-helper {
        padding-top: 1;
        color: $text-muted;
    }

    TextArea, Input {
        width: 100%;
        border: solid $surface-darken-2;
        background: transparent;
    }

    TextArea {
        height: 7;
    }

    #prompt-input {
        display: none;
    }

    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        Binding("enter", "submit_prompt", "Submit input", show=False),
        Binding("escape", "cancel_prompt", "Cancel input", show=False),
        Binding("ctrl+c", "interrupt_prompt", "Cancel input", show=False),
    ]

    def __init__(
        self,
        *,
        command_queue: asyncio.Queue[UICommandEnvelope],
        ready_event: asyncio.Event,
        session_name: str,
        permission_mode: str,
        allowed_tools: Sequence[str],
        workspace: str,
    ) -> None:
        super().__init__()
        #   The Textual app has to run its own async event loop (App.run_async) so it can process input, refresh the UI, and react to key bindings. Our agent orchestration loop is also async (waiting on Claude responses,
        #   prompting the user, etc.), but it runs outside the app. Because Textual isn’t thread-safe and its widgets can only be mutated from inside the app’s task, we bridge the two worlds with:

        #   - Command queue – the agent layer pushes “render this panel”, “show prompt”, “clear status”, etc. into an asyncio.Queue. The Textual task consumes and executes those commands on its own loop, guaranteeing UI work
        #     happens where Textual expects it.
        #   - Ready event – after we launch the app task, we wait on an asyncio.Event it sets once the widgets are mounted. That way we don’t send commands before the UI exists.

        self._command_queue = command_queue
        self._ready_event = ready_event
        self._session_name = session_name
        self._permission_mode = permission_mode
        self._allowed_tools = list(allowed_tools)
        self._workspace = workspace

        self._banner_subtitle: str | None = None
        self._banner_rendered = False
        self._status_visible = False
        self._active_prompt: UICommandEnvelope | None = None
        self._prompt_mode: Literal["hidden", "input", "textarea", "options"] = "hidden"
        self._command_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="banner"):
            yield Static(id="banner-panel")
            yield Static(
                "ctrl+c to exit · press enter on an empty prompt to repeat",
                id="banner-hint",
            )
        yield RichLog(id="log", wrap=True, auto_scroll=True)
        yield Static("", id="status")
        with Vertical(id="prompt-container"):
            yield Static("", id="prompt-message")
            yield PromptTextArea(id="prompt-textarea", placeholder="")
            yield Input(id="prompt-input", placeholder="")
            yield OptionList(id="prompt-options")
            yield Static("", id="prompt-helper")

    def on_mount(self) -> None:
        self._banner_panel: Static = self.query_one("#banner-panel", Static)
        self._banner_hint: Static = self.query_one("#banner-hint", Static)
        self._log_widget: RichLog = self.query_one("#log", RichLog)
        self._status: Static = self.query_one("#status", Static)
        self._prompt_container: Vertical = self.query_one("#prompt-container", Vertical)
        self._prompt_message: Static = self.query_one("#prompt-message", Static)
        self._prompt_helper: Static = self.query_one("#prompt-helper", Static)
        self._prompt_textarea: TextArea = self.query_one("#prompt-textarea", TextArea)
        self._prompt_input: Input = self.query_one("#prompt-input", Input)
        self._prompt_options: OptionList = self.query_one("#prompt-options", OptionList)

        self._prompt_container.display = False
        self._prompt_textarea.display = False
        self._prompt_input.display = False
        self._prompt_options.display = False

        self._command_task = asyncio.create_task(self._process_commands())
        self._ready_event.set()

    async def _process_commands(self) -> None:
        while True:
            envelope = await self._command_queue.get()
            payload = envelope.payload
            try:
                match payload:
                    case ShutdownPayload():
                        self._handle_shutdown(payload, envelope)
                        break
                    case ShowBannerPayload():
                        self._handle_show_banner(payload, envelope)
                    case RenderUserPromptPayload():
                        self._handle_render_user_prompt(payload, envelope)
                    case RenderAssistantTextPayload():
                        self._handle_render_assistant_text(payload, envelope)
                    case RenderToolUsePayload():
                        self._handle_render_tool_use(payload, envelope)
                    case RenderPermissionRequestPayload():
                        self._handle_render_permission_request(payload, envelope)
                    case RenderSessionResultPayload():
                        self._handle_render_session_result(payload, envelope)
                    case RenderChangedFilesPayload():
                        self._handle_render_changed_files(payload, envelope)
                    case RenderPlanPreviewPayload():
                        self._handle_render_plan_preview(payload, envelope)
                    case ShowStatusPayload():
                        self._handle_show_status(payload, envelope)
                    case ClearStatusPayload():
                        self._handle_clear_status(payload, envelope)
                    case LogTextPayload():
                        self._handle_log_text(payload, envelope)
                    case PromptInputPayload():
                        self._handle_prompt_input(payload, envelope)
                    case PromptOptionsPayload():
                        self._handle_prompt_options(payload, envelope)
                    case _:
                        if envelope.future and not envelope.future.done():
                            envelope.future.set_result(None)
                        continue

                if (
                    envelope.future is not None
                    and not envelope.future.done()
                    and not envelope.defer_result
                ):
                    envelope.future.set_result(None)
            except Exception as exc:  # pragma: no cover - defensive
                if envelope.future and not envelope.future.done():
                    envelope.future.set_exception(exc)
                raise

    def _handle_shutdown(
        self, payload: ShutdownPayload, envelope: UICommandEnvelope
    ) -> None:
        if envelope.future and not envelope.future.done():
            envelope.future.set_result(None)
        self.exit()

    def _handle_show_banner(
        self, payload: ShowBannerPayload, envelope: UICommandEnvelope
    ) -> None:
        instruction = payload.instruction
        if instruction:
            self._banner_subtitle = instruction

        metadata_table = Table.grid(padding=(0, 1))
        metadata_table.add_column(style="grey58", no_wrap=True)
        metadata_table.add_column()
        metadata_table.add_row(
            "workspace",
            Text(self._workspace, style="cyan"),
        )
        mode_style = "green" if self._permission_mode == "plan" else "yellow"
        metadata_table.add_row(
            "mode",
            Text(self._permission_mode, style=mode_style),
        )
        tools_text = ", ".join(self._allowed_tools) if self._allowed_tools else "(none)"
        metadata_table.add_row(
            "tools",
            Text(tools_text, style="yellow"),
        )
        metadata_table.add_row(
            "session",
            Text(self._session_name, style="magenta"),
        )

        banner_lines: list[RenderableType] = [Text("PLANAR AGENT", style="bold cyan")]
        banner_lines.append(metadata_table)
        if self._banner_subtitle:
            banner_lines.append(Text(self._banner_subtitle, style="italic grey58"))
        self._banner_panel.update(Group(*banner_lines))
        self._banner_rendered = True

    def _handle_render_user_prompt(
        self, payload: RenderUserPromptPayload, envelope: UICommandEnvelope
    ) -> None:
        prompt_text = payload.prompt_text
        follow_up = payload.follow_up
        if not prompt_text.strip():
            self._handle_show_status(
                ShowStatusPayload(message="thinking…", style="magenta"), envelope
            )
            return

        title = "user" if not follow_up else "user (follow-up)"
        content = (
            Text(prompt_text)
            if prompt_text.strip()
            else Text("(no prompt provided)", style="dim")
        )
        self._append_entry(title, content, prefix=">", title_style="cyan")
        self._handle_show_status(
            ShowStatusPayload(message="thinking…", style="magenta"), envelope
        )

    def _handle_render_assistant_text(
        self, payload: RenderAssistantTextPayload, envelope: UICommandEnvelope
    ) -> None:
        self._handle_clear_status(payload, envelope)
        text = payload.text
        content = Markdown(text) if text.strip() else Text("(no response)", style="dim")
        self._append_entry("assistant", content, prefix="<", title_style="green")

    def _handle_render_tool_use(
        self, payload: RenderToolUsePayload, envelope: UICommandEnvelope
    ) -> None:
        self._handle_clear_status(payload, envelope)
        invocation_number = payload.invocation_number
        tool_name = payload.tool_name
        tool_payload = payload.payload
        language_hint = "bash" if tool_name.lower() == "bash" else None
        renderable = _format_tool_payload(
            tool_name,
            tool_payload,
            language_hint=language_hint,
        )
        border_style = "yellow" if tool_name.lower() != "bash" else "bright_yellow"
        title = f"tool {invocation_number}: {tool_name}"
        self._append_entry(
            title,
            renderable,
            prefix="-",
            title_style=border_style,
        )

    def _handle_render_permission_request(
        self, payload: RenderPermissionRequestPayload, envelope: UICommandEnvelope
    ) -> None:
        self._handle_clear_status(payload, envelope)
        tool_name = payload.tool_name
        tool_payload = payload.payload
        suggestions = payload.suggestions or []

        payload_renderable = _format_tool_payload(
            tool_name,
            tool_payload,
        )
        suggestions_renderable: RenderableType
        if suggestions:
            suggestions_renderable = _format_tool_payload(
                "permission-suggestions",
                suggestions,
                language_hint="json",
            )
        else:
            suggestions_renderable = Text("(no suggestions)", style="dim")

        table = Table.grid(padding=(0, 1))
        table.add_column(style="grey58", no_wrap=True)
        table.add_column()
        table.add_row("tool", Text(tool_name, style="yellow"))
        table.add_row("payload", payload_renderable)
        table.add_row("suggestions", suggestions_renderable)

        self._append_entry(
            "permission request",
            table,
            prefix="!",
            title_style="yellow",
        )

    def _handle_render_session_result(
        self, payload: RenderSessionResultPayload, envelope: UICommandEnvelope
    ) -> None:
        self._handle_clear_status(payload, envelope)
        duration_ms = payload.duration_ms
        total_cost = payload.total_cost
        table = Table.grid(padding=(0, 1))
        table.add_column(style="grey58", no_wrap=True)
        table.add_column(justify="right")
        table.add_row(
            "duration", f"{duration_ms} ms" if duration_ms is not None else "–"
        )
        table.add_row(
            "cost",
            f"${total_cost:.4f}" if total_cost is not None else "–",
        )
        self._append_entry(
            "session summary",
            table,
            prefix="=",
            title_style="cyan",
        )

    def _handle_render_changed_files(
        self, payload: RenderChangedFilesPayload, envelope: UICommandEnvelope
    ) -> None:
        self._handle_clear_status(payload, envelope)
        files = payload.files
        if not files:
            return
        file_table = Table.grid()
        file_table.add_column()
        for file_path in files:
            file_table.add_row(Text(file_path, style="green"))
        self._append_entry(
            "changed files",
            file_table,
            prefix="+",
            title_style="green",
        )

    def _handle_render_plan_preview(
        self, payload: RenderPlanPreviewPayload, envelope: UICommandEnvelope
    ) -> None:
        plan_text = payload.plan_text
        if not plan_text.strip():
            return
        self._append_entry(
            "proposed plan",
            Markdown(plan_text),
            prefix="~",
            title_style="yellow",
        )

    def _handle_show_status(
        self, payload: ShowStatusPayload, envelope: UICommandEnvelope
    ) -> None:
        message = payload.message
        style = payload.style
        self._status.update(Text(message, style=style))
        self._status_visible = True

    def _handle_clear_status(
        self, _payload: CommandPayloadBase, _envelope: UICommandEnvelope
    ) -> None:
        if not self._status_visible:
            return
        self._status.update("")
        self._status_visible = False

    def _handle_log_text(
        self, payload: LogTextPayload, envelope: UICommandEnvelope
    ) -> None:
        text = payload.text
        style = payload.style
        self._append_entry(
            text,
            None,
            prefix="-",
            title_style=style,
            spacer=False,
        )

    def _handle_prompt_input(
        self, payload: PromptInputPayload, envelope: UICommandEnvelope
    ) -> None:
        envelope.defer_result = True
        message = payload.message
        placeholder = payload.placeholder
        initial_text = payload.initial_text or ""
        multiline = payload.multiline
        helper_text = payload.helper_text

        self._prompt_message.update(message)
        self._prompt_helper.update(helper_text)
        prompt_mode = "textarea" if multiline else "input"
        self._set_prompt_mode(prompt_mode)

        if multiline:
            self._prompt_textarea.placeholder = placeholder
            self._prompt_textarea.load_text(initial_text)
            self._prompt_textarea.focus()
        else:
            self._prompt_input.placeholder = placeholder
            self._prompt_input.value = initial_text
            self._prompt_input.cursor_position = len(initial_text)
            self._prompt_input.focus()

        self._prompt_container.display = True
        self._active_prompt = envelope

    def _handle_prompt_options(
        self, payload: PromptOptionsPayload, envelope: UICommandEnvelope
    ) -> None:
        envelope.defer_result = True
        self._prompt_message.update(payload.message)
        self._prompt_helper.update(payload.helper_text)
        self._set_prompt_mode("options")
        self._prompt_options.clear_options()
        for option in payload.options:
            self._prompt_options.add_option(Option(option.label, id=option.value))
        if payload.options:
            self._prompt_options.highlighted = 0
        self._prompt_options.focus()
        self._prompt_container.display = True
        self._active_prompt = envelope

    def _set_prompt_mode(self, mode: Literal["input", "textarea", "options"]) -> None:
        self._prompt_mode = mode
        self._prompt_textarea.display = mode == "textarea"
        self._prompt_input.display = mode == "input"
        self._prompt_options.display = mode == "options"

    def _append_entry(
        self,
        title: str,
        body: RenderableType | None = None,
        *,
        prefix: str = "*",
        title_style: str | None = None,
        spacer: bool = True,
    ) -> None:
        header = Text(prefix + " ", style="grey50")
        header.append(title, style=title_style)
        self._log_widget.write(header)
        if body is not None:
            self._log_widget.write(body)
        if spacer:
            self._log_widget.write(Text(""))
        self._log_widget.scroll_end(animate=False)

    def action_submit_prompt(self) -> None:
        if not self._active_prompt or self._prompt_mode == "options":
            return
        value = self._current_prompt_value()
        self._finish_prompt(value)

    def action_cancel_prompt(self) -> None:
        if not self._active_prompt:
            return
        self._finish_prompt("", aborted=True)

    def action_interrupt_prompt(self) -> None:
        if not self._active_prompt:
            self.exit()
            return
        self._finish_prompt("", interrupted=True)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._active_prompt and self._prompt_mode == "input":
            event.stop()
            self._finish_prompt(event.value)

    def _current_prompt_value(self) -> str:
        if self._prompt_mode == "textarea":
            return self._prompt_textarea.text
        if self._prompt_mode == "input":
            return self._prompt_input.value
        return ""

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if not self._active_prompt or self._prompt_mode != "options":
            return
        event.stop()
        option_id = event.option.id if event.option.id is not None else ""
        self._finish_prompt(str(option_id))

    def _finish_prompt(
        self,
        value: str,
        *,
        interrupted: bool = False,
        aborted: bool = False,
    ) -> None:
        if not self._active_prompt:
            return
        command = self._active_prompt
        self._active_prompt = None
        self._prompt_container.display = False
        self._prompt_mode = "hidden"
        self._prompt_textarea.display = False
        self._prompt_input.display = False
        self._prompt_options.display = False
        self._prompt_options.clear_options()
        if interrupted:
            if command.future and not command.future.done():
                command.future.set_exception(KeyboardInterrupt())
        else:
            result = "" if aborted else value
            if command.future and not command.future.done():
                command.future.set_result(result)


@dataclass
class AgentTUI:
    """Render helper for the Planar agent CLI backed by a Textual app."""

    session_name: str
    permission_mode: str
    allowed_tools: Sequence[str]
    workspace: str
    _app: AgentTextualApp | None = field(default=None, init=False, repr=False)
    _app_task: asyncio.Task[None] | None = field(default=None, init=False, repr=False)
    _command_queue: asyncio.Queue[UICommandEnvelope] | None = field(
        default=None, init=False, repr=False
    )
    _ready_event: asyncio.Event | None = field(default=None, init=False, repr=False)
    _tool_invocations: int = field(default=0, init=False)
    _started: bool = field(default=False, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    async def __aenter__(self) -> "AgentTUI":
        await self.start()
        return self

    async def __aexit__(self, _exc_type, _exc, _tb) -> None:
        await self.close()

    async def start(self) -> None:
        if self._started:
            return
        loop = asyncio.get_running_loop()
        self._command_queue = asyncio.Queue[UICommandEnvelope]()
        self._ready_event = asyncio.Event()
        self._app = AgentTextualApp(
            command_queue=self._command_queue,
            ready_event=self._ready_event,
            session_name=self.session_name,
            permission_mode=self.permission_mode,
            allowed_tools=self.allowed_tools,
            workspace=self.workspace,
        )
        self._app_task = loop.create_task(self._app.run_async())
        await self._ready_event.wait()
        self._started = True

    async def close(self) -> None:
        if not self._started or self._closed:
            return
        if not self._command_queue or not self._app_task:
            return
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        envelope = UICommandEnvelope(payload=ShutdownPayload(), future=future)
        await self._command_queue.put(envelope)
        await future
        await self._app_task
        self._closed = True
        self._started = False
        self._app = None
        self._app_task = None
        self._command_queue = None
        self._ready_event = None

    async def wait_for_exit(self) -> None:
        if self._closed:
            return
        if not self._app_task:
            raise RuntimeError("TUI is not running")
        await self._app_task

    async def show_banner(self, instruction: str | None = None) -> None:
        await self._send_payload(ShowBannerPayload(instruction=instruction))

    async def render_user_prompt(
        self, prompt_text: str, *, follow_up: bool = False
    ) -> None:
        await self._send_payload(
            RenderUserPromptPayload(prompt_text=prompt_text, follow_up=follow_up)
        )

    async def prompt_for_initial(self, instruction: str) -> str:
        return await self._prompt_input(
            instruction,
            placeholder=_PROMPT_PLACEHOLDER,
            multiline=True,
        )

    async def prompt_for_follow_up(self) -> str:
        return await self._prompt_input(
            "Provide the next instruction",
            placeholder=_FOLLOW_UP_PROMPT,
            multiline=True,
        )

    async def render_assistant_text(self, text: str) -> None:
        await self._send_payload(RenderAssistantTextPayload(text=text))

    async def render_tool_use(self, tool_name: str, payload: object) -> None:
        self._tool_invocations += 1
        await self._send_payload(
            RenderToolUsePayload(
                tool_name=tool_name,
                payload=payload,
                invocation_number=self._tool_invocations,
            )
        )

    async def render_permission_request(
        self,
        tool_name: str,
        payload: object,
        suggestions: Sequence[object],
    ) -> None:
        await self._send_payload(
            RenderPermissionRequestPayload(
                tool_name=tool_name,
                payload=payload,
                suggestions=list(suggestions),
            )
        )

    async def render_session_result(
        self,
        *,
        duration_ms: int | None,
        total_cost: float | None,
    ) -> None:
        await self._send_payload(
            RenderSessionResultPayload(
                duration_ms=duration_ms,
                total_cost=total_cost,
            )
        )

    async def render_changed_files(self, files: Sequence[str]) -> None:
        await self._send_payload(RenderChangedFilesPayload(files=list(files)))

    async def render_plan_preview(self, plan_text: str) -> None:
        await self._send_payload(RenderPlanPreviewPayload(plan_text=plan_text))

    async def show_status(self, message: str, *, style: str = "grey50") -> None:
        await self._send_payload(ShowStatusPayload(message=message, style=style))

    async def clear_status(self) -> None:
        await self._send_payload(ClearStatusPayload())

    async def log_text(self, text: str, *, style: str | None = None) -> None:
        await self._send_payload(LogTextPayload(text=text, style=style))

    async def _prompt_options(
        self,
        message: str,
        *,
        options: Sequence[tuple[str, str]],
        helper_text: str | None = None,
    ) -> str:
        payload = PromptOptionsPayload(
            message=message,
            helper_text=helper_text or ACTIONS_HELP_TEXT,
            options=[
                PromptOption(label=label, value=value) for label, value in options
            ],
        )
        return await self._send_payload(payload)

    async def confirm_exit_plan(self, plan_text: str) -> PermissionChoice:
        await self.clear_status()
        if plan_text.strip():
            await self.render_plan_preview(plan_text)

        choice = await self._prompt_options(
            "approve plan execution?",
            options=[
                ("yes – execute plan", "allow"),
                ("no – stay in plan mode", "deny"),
            ],
        )
        if choice == "allow":
            await self.log_text("exiting plan mode", style="green")
            return "allow"
        await self.log_text("staying in plan mode", style="yellow")
        return "deny"

    async def prompt_permission_choice(
        self, tool_name: str, *, allow_updates: bool
    ) -> PermissionChoice:
        options: list[tuple[str, str]] = [("yes – allow tool use", "allow")]
        if allow_updates:
            options.append(
                ("yes – allow and apply suggested permissions", "allow_with_updates")
            )
        options.append(("no – provide feedback", "deny"))

        choice = await self._prompt_options(f"{tool_name} permission?", options=options)
        if choice == "allow":
            await self.log_text(f"approved {tool_name}", style="green")
            return "allow"
        if choice == "allow_with_updates":
            await self.log_text(
                f"approved {tool_name} with suggested permissions",
                style="green",
            )
            return "allow_with_updates"
        await self.log_text(f"denied {tool_name}", style="yellow")
        return "deny"

    async def prompt_for_permission_feedback(self, tool_name: str) -> str:
        return await self._prompt_input(
            f"{tool_name} feedback (optional)",
            placeholder=_PERMISSION_FEEDBACK_PLACEHOLDER,
            multiline=True,
        )

    async def _prompt_input(
        self,
        message: str,
        *,
        placeholder: str,
        initial_text: str | None = None,
        multiline: bool,
    ) -> str:
        helper_text = (
            "Enter to submit, CMD+Enter for new line · Ctrl+C to cancel"
            if multiline
            else "Press Enter to submit · Ctrl+C/Esc to cancel"
        )
        return await self._send_payload(
            PromptInputPayload(
                message=message,
                placeholder=placeholder,
                initial_text=initial_text or "",
                multiline=multiline,
                helper_text=helper_text,
            )
        )

    async def _send_payload(self, payload: UICommand) -> Any:
        await self.start()
        if not self._command_queue or not self._app_task:
            raise RuntimeError("TUI is not running")
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        envelope = UICommandEnvelope(payload=payload, future=future)
        await self._command_queue.put(envelope)
        done, _ = await asyncio.wait(
            {future, self._app_task}, return_when=asyncio.FIRST_COMPLETED
        )
        if self._app_task in done:
            app_result = self._app_task.result()
            if isinstance(app_result, BaseException):
                raise app_result
            raise KeyboardInterrupt()
        return future.result()
