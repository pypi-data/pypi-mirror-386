from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Label,
    Input,
    Switch,
    Static,
    Select,
    Collapsible,
    Header,
)
from textual.containers import Grid, Vertical, Horizontal
from textual import on
from mastui.keybind_screen import KeybindScreen

class ConfigScreen(ModalScreen):
    """A modal screen for changing settings."""

    def compose(self):
        config = self.app.config  # Use the app's config object
        with Vertical(id="config-dialog") as d:
            d.border_title = "Mastui Options"

            with Collapsible(title="Timeline Visibility"):
                with Grid(classes="config-group-body"):
                    yield Label("Enable Home timeline?", classes="config-label")
                    yield Switch(
                        value=config.home_timeline_enabled, id="home_timeline_enabled"
                    )
                    yield Static()  # Spacer

                    yield Label("Enable Local timeline?", classes="config-label")
                    yield Switch(
                        value=config.local_timeline_enabled, id="local_timeline_enabled"
                    )
                    yield Static()  # Spacer

                    yield Label(
                        "Enable Notifications timeline?", classes="config-label"
                    )
                    yield Switch(
                        value=config.notifications_timeline_enabled,
                        id="notifications_timeline_enabled",
                    )
                    yield Static()  # Spacer

                    yield Label("Enable Federated timeline?", classes="config-label")
                    yield Switch(
                        value=config.federated_timeline_enabled,
                        id="federated_timeline_enabled",
                    )
                    yield Static()  # Spacer

                    yield Label("Enable Direct Messages timeline?", classes="config-label")
                    yield Switch(
                        value=config.direct_timeline_enabled,
                        id="direct_timeline_enabled",
                    )
                    yield Static()  # Spacer

                    yield Label("Force single-column mode?", classes="config-label")
                    yield Switch(
                        value=config.force_single_column, id="force_single_column"
                    )
                    yield Static() # Spacer

            with Collapsible(title="Auto-Refresh (in minutes)"):
                with Grid(classes="config-group-body"):
                    yield Label("Auto-refresh home?", classes="config-label")
                    yield Switch(value=config.home_auto_refresh, id="home_auto_refresh")
                    yield Input(
                        str(config.home_auto_refresh_interval),
                        id="home_auto_refresh_interval",
                    )

                    yield Label("Auto-refresh local?", classes="config-label")
                    yield Switch(value=config.local_auto_refresh, id="local_auto_refresh")
                    yield Input(
                        str(config.local_auto_refresh_interval),
                        id="local_auto_refresh_interval",
                    )

                    yield Label("Auto-refresh notifications?", classes="config-label")
                    yield Switch(
                        value=config.notifications_auto_refresh,
                        id="notifications_auto_refresh",
                    )
                    yield Input(
                        str(config.notifications_auto_refresh_interval),
                        id="notifications_auto_refresh_interval",
                    )

                    yield Label("Auto-refresh federated?", classes="config-label")
                    yield Switch(
                        value=config.federated_auto_refresh, id="federated_auto_refresh"
                    )
                    yield Input(
                        str(config.federated_auto_refresh_interval),
                        id="federated_auto_refresh_interval",
                    )

            with Collapsible(title="Images & Cache"):
                with Grid(classes="config-group-body"):
                    yield Label("Show images?", classes="config-label")
                    yield Switch(value=config.image_support, id="image_support")
                    yield Select(
                        [
                            ("Auto", "auto"),
                            ("ANSI", "ansi"),
                            ("Sixel", "sixel"),
                            ("TGP (iTerm2)", "tgp"),
                        ],
                        value=config.image_renderer,
                        id="image_renderer",
                    )

                    yield Label(
                        "Auto-prune cache (older than 30 days)?", classes="config-label"
                    )
                    yield Switch(value=config.auto_prune_cache, id="auto_prune_cache")
                    yield Static()  # Spacer

            with Collapsible(title="Notifications"):
                with Grid(classes="config-group-body"):
                    yield Label("Pop-up on new mentions?", classes="config-label")
                    yield Switch(value=config.notifications_popups_mentions, id="notifications_popups_mentions")
                    yield Static()

                    yield Label("Pop-up on new follows?", classes="config-label")
                    yield Switch(value=config.notifications_popups_follows, id="notifications_popups_follows")
                    yield Static()

                    yield Label("Pop-up on new reblogs?", classes="config-label")
                    yield Switch(value=config.notifications_popups_reblogs, id="notifications_popups_reblogs")
                    yield Static()

                    yield Label("Pop-up on new favourites?", classes="config-label")
                    yield Switch(value=config.notifications_popups_favourites, id="notifications_popups_favourites")
                    yield Static()

            with Horizontal(id="config-buttons"):
                yield Button("Customize Keys", id="keybinds")
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_settings()
            self.dismiss(True)
        elif event.button.id == "keybinds":
            self.app.push_screen(KeybindScreen(self.app.keybind_manager), self.on_keybind_screen_dismiss)
        else:
            self.dismiss(False)

    def on_keybind_screen_dismiss(self, result: bool) -> None:
        if result:
            self.app.bind_keys()


    @on(Collapsible.Toggled)
    def on_collapsible_toggled(self, event: Collapsible.Toggled) -> None:
        """When a collapsible is opened, close the others."""
        if not event.collapsible.collapsed:
            for collapsible in self.query(Collapsible):
                if collapsible is not event.collapsible:
                    collapsible.collapsed = True

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "auto_prune_cache" and event.value:
            self.app.prune_cache()

    def save_settings(self):
        """Saves the current settings to the config object."""
        config = self.app.config
        config.home_auto_refresh = self.query_one("#home_auto_refresh").value
        config.home_auto_refresh_interval = int(
            self.query_one("#home_auto_refresh_interval").value
        )
        config.local_auto_refresh = self.query_one("#local_auto_refresh").value
        config.local_auto_refresh_interval = int(
            self.query_one("#local_auto_refresh_interval").value
        )
        config.notifications_auto_refresh = self.query_one(
            "#notifications_auto_refresh"
        ).value
        config.notifications_auto_refresh_interval = int(
            self.query_one("#notifications_auto_refresh_interval").value
        )
        config.federated_auto_refresh = self.query_one("#federated_auto_refresh").value
        config.federated_auto_refresh_interval = int(
            self.query_one("#federated_auto_refresh_interval").value
        )
        config.image_support = self.query_one("#image_support").value
        config.image_renderer = self.query_one("#image_renderer").value
        config.auto_prune_cache = self.query_one("#auto_prune_cache").value
        config.home_timeline_enabled = self.query_one("#home_timeline_enabled").value
        config.local_timeline_enabled = self.query_one("#local_timeline_enabled").value
        config.notifications_timeline_enabled = self.query_one(
            "#notifications_timeline_enabled"
        ).value
        config.federated_timeline_enabled = self.query_one(
            "#federated_timeline_enabled"
        ).value
        config.direct_timeline_enabled = self.query_one(
            "#direct_timeline_enabled"
        ).value
        config.force_single_column = self.query_one("#force_single_column").value

        # Save notification settings
        config.notifications_popups_mentions = self.query_one("#notifications_popups_mentions").value
        config.notifications_popups_follows = self.query_one("#notifications_popups_follows").value
        config.notifications_popups_reblogs = self.query_one("#notifications_popups_reblogs").value
        config.notifications_popups_favourites = self.query_one("#notifications_popups_favourites").value
        
        config.save_config()
