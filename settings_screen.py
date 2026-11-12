""" SettingsScreen: Manage audio formats, output paths, platforms, and cookies. """

from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Input, Select, Static, Label
from textual.binding import Binding
import os

class SettingsScreen(Screen):

    CSS = """
    SettingsScreen {
        align: center middle;
    }

    #settings-container {
        width: 70;
        height: auto;
        border: solid $border;
        background: $panel;
        padding: 2 4;
    }

    .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
        margin-top: 1;
    }

    .row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }

    Label {
        width: 25;
        content-align: left middle;
    }

    Input {
        width: 40;
    }

    Select {
        width: 40;
    }

    #actions {
        margin-top: 2;
        align: right middle;
    }
    
    Button {
        margin-left: 2;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Hub"),
    ]

    def compose(self):
        yield Header()
        yield Vertical(
            Static("Configuration Settings", classes="section-title"),
            
            Horizontal(
                Label("Audio Format:"),
                Select(
                    [("MP3", "mp3"), ("M4A", "m4a"), ("FLAC", "flac")],
                    id="select_format",
                    value=self.app.settings.get("format", "mp3")
                ),
                classes="row"
            ),
            
            Horizontal(
                Label("Platform:"),
                Select(
                    [("YouTube Music", "ytmusic"), ("YouTube", "youtube")],
                    id="select_platform",
                    value=self.app.settings.get("platform", "ytmusic")
                ),
                classes="row"
            ),

            Horizontal(
                Label("Output Path:"),
                Input(
                    value=self.app.settings.get("output_path", "."),
                    id="input_output_path"
                ),
                classes="row"
            ),

            Horizontal(
                Label("Cookie File Path:"),
                Input(
                    value=self.app.settings.get("cookie_file", "") or "",
                    placeholder="Optional (path to cookies.txt)",
                    id="input_cookie"
                ),
                classes="row"
            ),

            Horizontal(
                Button("Save Settings", variant="primary", id="btn_save"),
                Button("Back", id="btn_back"),
                id="actions"
            ),
            Static("", id="settings_status"),
            id="settings-container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_save":
            self.save_settings()
        elif event.button.id == "btn_back":
            self.action_back()

    def save_settings(self):
        status = self.query_one("#settings_status", Static)
        
        fmt = self.query_one("#select_format", Select).value
        plat = self.query_one("#select_platform", Select).value
        out_path = self.query_one("#input_output_path", Input).value.strip()
        cookie = self.query_one("#input_cookie", Input).value.strip()

        if not out_path:
            status.update("[red]Output path cannot be empty.[/red]")
            return

        # Update app-wide settings dictionary
        self.app.settings["format"] = fmt
        self.app.settings["platform"] = plat
        self.app.settings["output_path"] = out_path
        self.app.settings["cookie_file"] = cookie if cookie else None

        status.update("[green]Settings saved successfully![/green]")

    def action_back(self):
        from hub_screen import HubScreen
        self.app.switch_screen(HubScreen())