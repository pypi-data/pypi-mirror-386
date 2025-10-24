"""PromptInput widget. Credits to Elia (https://github.com/darrenburns/elia)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from textual import on
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import TextArea


if TYPE_CHECKING:
    from textual import events


class PromptInput(TextArea):
    """Widget for user input with prompt functionality."""

    @dataclass
    class PromptSubmitted(Message):
        """Message sent when a prompt is submitted."""

        text: str
        prompt_input: PromptInput

    @dataclass
    class CursorEscapingTop(Message):
        """Message sent when the cursor escapes the top of the widget."""

    @dataclass
    class CursorEscapingBottom(Message):
        """Message sent when the cursor escapes the bottom of the widget."""

    BINDINGS: ClassVar = [
        Binding("ctrl+j,ctrl+enter", "submit_prompt", "Send message", key_display="^J/^↵")
    ]

    submit_ready = reactive(True)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            language="markdown",
        )

    def on_key(self, event: events.Key):
        if self.cursor_location == (0, 0) and event.key == "up":
            event.prevent_default()
            self.post_message(self.CursorEscapingTop())
            event.stop()
        elif self.cursor_at_end_of_text and event.key == "down":
            event.prevent_default()
            self.post_message(self.CursorEscapingBottom())
            event.stop()

    def watch_submit_ready(self, submit_ready: bool):
        self.set_class(not submit_ready, "-submit-blocked")

    def on_mount(self):
        self.border_title = "Enter your message..."

    @on(TextArea.Changed)
    async def prompt_changed(self, event: TextArea.Changed):
        text_area = event.text_area
        if text_area.text.strip() != "":
            text_area.border_subtitle = "[[white]^j[/]] Send message"
        else:
            text_area.border_subtitle = None

        text_area.set_class(text_area.wrapped_document.height > 1, "multiline")

        # TODO - when the height of the textarea changes
        #  things don't appear to refresh correctly.
        #  I think this may be a Textual bug.
        #  The refresh below should not be required.
        assert self.parent
        self.parent.refresh()

    def action_submit_prompt(self):
        if self.text.strip() == "":
            self.notify("Cannot send empty message!")
            return

        if self.submit_ready:
            message = self.PromptSubmitted(self.text, prompt_input=self)
            self.clear()
            self.post_message(message)
        else:
            self.app.bell()
            self.notify("Please wait for response to complete.")


if __name__ == "__main__":
    from textualicious import show

    show(PromptInput())
