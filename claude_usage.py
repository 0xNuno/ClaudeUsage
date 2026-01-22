#!/usr/bin/env python3
"""
Claude Usage Tracker - macOS Menu Bar App
Displays Claude AI usage limits in real-time.
"""

import rumps
import requests
import json
import keyring
import webbrowser
from datetime import datetime, timezone
from typing import Optional, Dict, Any

APP_NAME = "Claude Usage"
KEYRING_SERVICE = "claude-usage-tracker"
KEYRING_SESSION_KEY = "session_key"
KEYRING_ORG_ID = "org_id"

API_BASE = "https://claude.ai/api"


class ClaudeAPI:
    """Client for Claude's usage API."""

    def __init__(self, session_key: str, org_id: str):
        self.session_key = session_key
        self.org_id = org_id

    def get_usage(self) -> Optional[Dict[str, Any]]:
        """Fetch usage data from Claude API."""
        try:
            response = requests.get(
                f"{API_BASE}/organizations/{self.org_id}/usage",
                cookies={"sessionKey": self.session_key},
                headers={
                    "User-Agent": "Claude Usage Tracker/1.0",
                    "Accept": "application/json",
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return None


def format_time_until(reset_time: str) -> str:
    """Format time until reset as human-readable string."""
    try:
        reset_dt = datetime.fromisoformat(reset_time.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = reset_dt - now

        if diff.total_seconds() <= 0:
            return "now"

        hours, remainder = divmod(int(diff.total_seconds()), 3600)
        minutes = remainder // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "?"


class ClaudeUsageApp(rumps.App):
    """macOS Menu Bar app for Claude usage tracking."""

    def __init__(self):
        super().__init__(
            name=APP_NAME,
            title="Claude: --%",
            quit_button=None  # We'll add our own
        )

        self.api: Optional[ClaudeAPI] = None
        self.usage_data: Optional[Dict[str, Any]] = None

        # Build menu
        self.menu = [
            rumps.MenuItem("Session Limit", callback=None),
            rumps.MenuItem("Weekly Limit", callback=None),
            rumps.MenuItem("Sonnet Limit", callback=None),
            None,  # Separator
            rumps.MenuItem("Refresh Now", callback=self.refresh_now),
            rumps.MenuItem("Settings...", callback=self.open_settings),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]

        # Load credentials and start
        self.load_credentials()

        # Start refresh timer (every 60 seconds)
        self.timer = rumps.Timer(self.refresh, 60)
        self.timer.start()

        # Initial refresh
        self.refresh(None)

    def load_credentials(self):
        """Load session key and org ID from keyring."""
        session_key = keyring.get_password(KEYRING_SERVICE, KEYRING_SESSION_KEY)
        org_id = keyring.get_password(KEYRING_SERVICE, KEYRING_ORG_ID)

        if session_key and org_id:
            self.api = ClaudeAPI(session_key, org_id)
        else:
            self.api = None

    def save_credentials(self, session_key: str, org_id: str):
        """Save credentials to keyring."""
        keyring.set_password(KEYRING_SERVICE, KEYRING_SESSION_KEY, session_key)
        keyring.set_password(KEYRING_SERVICE, KEYRING_ORG_ID, org_id)
        self.api = ClaudeAPI(session_key, org_id)

    def refresh(self, _):
        """Refresh usage data from API."""
        if not self.api:
            self.title = "Claude: Setup"
            self.menu["Session Limit"].title = "Session: Not configured"
            self.menu["Weekly Limit"].title = "Weekly: Not configured"
            self.menu["Sonnet Limit"].title = "Sonnet: Not configured"
            return

        data = self.api.get_usage()
        if not data:
            self.title = "Claude: Error"
            return

        self.usage_data = data
        self.update_display()

    def update_display(self):
        """Update menu bar and dropdown with current data."""
        if not self.usage_data:
            return

        # Extract usage percentages
        session_pct = self.usage_data.get("five_hour", {}).get("percent_used", 0)
        session_reset = self.usage_data.get("five_hour", {}).get("resets_at", "")

        weekly_pct = self.usage_data.get("seven_day", {}).get("percent_used", 0)
        weekly_reset = self.usage_data.get("seven_day", {}).get("resets_at", "")

        # Sonnet-specific (may not exist for all plans)
        sonnet_data = self.usage_data.get("seven_day_sonnet", {})
        sonnet_pct = sonnet_data.get("percent_used", 0) if sonnet_data else None
        sonnet_reset = sonnet_data.get("resets_at", "") if sonnet_data else ""

        # Update menu bar title
        self.title = f"Claude: {session_pct:.0f}%"

        # Update menu items
        session_time = format_time_until(session_reset) if session_reset else "?"
        self.menu["Session Limit"].title = f"Session: {session_pct:.0f}% (resets in {session_time})"

        weekly_time = format_time_until(weekly_reset) if weekly_reset else "?"
        self.menu["Weekly Limit"].title = f"Weekly: {weekly_pct:.0f}% (resets in {weekly_time})"

        if sonnet_pct is not None:
            sonnet_time = format_time_until(sonnet_reset) if sonnet_reset else "?"
            self.menu["Sonnet Limit"].title = f"Sonnet: {sonnet_pct:.0f}% (resets in {sonnet_time})"
        else:
            self.menu["Sonnet Limit"].title = "Sonnet: N/A"

    @rumps.clicked("Refresh Now")
    def refresh_now(self, _):
        """Manual refresh triggered by user."""
        self.refresh(None)
        print("Refreshed usage data")

    @rumps.clicked("Settings...")
    def open_settings(self, _):
        """Open settings dialog to configure credentials."""
        # Get current values
        current_session = keyring.get_password(KEYRING_SERVICE, KEYRING_SESSION_KEY) or ""
        current_org = keyring.get_password(KEYRING_SERVICE, KEYRING_ORG_ID) or ""

        # Show instructions
        instructions = rumps.alert(
            title="Setup Instructions",
            message=(
                "To get your credentials:\n\n"
                "1. Open claude.ai/settings/usage in your browser\n"
                "2. Open DevTools (Cmd+Option+I) → Network tab\n"
                "3. Find 'usage' request → look at Cookie header\n"
                "4. Copy 'sessionKey' value (starts with sk-ant-sid01-)\n"
                "5. Copy Organization ID from the URL or Settings → Account\n\n"
                "Click OK to enter your credentials."
            ),
            ok="OK",
            cancel="Open Claude Settings"
        )

        if instructions == 0:  # Cancel = Open browser
            webbrowser.open("https://claude.ai/settings/usage")
            return

        # Get session key
        session_window = rumps.Window(
            title="Session Key",
            message="Paste your sessionKey (sk-ant-sid01-...):",
            default_text=current_session[:20] + "..." if len(current_session) > 20 else current_session,
            ok="Next",
            cancel="Cancel",
            dimensions=(400, 100)
        )
        session_response = session_window.run()

        if not session_response.clicked:
            return

        session_key = session_response.text.strip()

        # Get org ID
        org_window = rumps.Window(
            title="Organization ID",
            message="Paste your Organization ID (UUID format):",
            default_text=current_org,
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 50)
        )
        org_response = org_window.run()

        if not org_response.clicked:
            return

        org_id = org_response.text.strip()

        # Validate and save
        if session_key and org_id:
            self.save_credentials(session_key, org_id)
            self.refresh(None)
            rumps.alert(
                title="Settings Saved",
                message="Credentials updated successfully."
            )
        else:
            rumps.alert(
                title="Error",
                message="Both Session Key and Organization ID are required."
            )

    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the application."""
        rumps.quit_application()


def main():
    """Entry point."""
    app = ClaudeUsageApp()
    app.run()


if __name__ == "__main__":
    main()
