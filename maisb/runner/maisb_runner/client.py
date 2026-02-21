"""AndroidHarnessClient - HTTP client for the MAISB Android harness."""
import requests
from typing import Optional


class AndroidHarnessClient:
    """Client for communicating with the MAISB Android harness Ktor server."""

    def __init__(self, base_url: str = "http://localhost:8765", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def arm(self, scenario_id: str, channel: str, payload: str, defense_profile: str = "D4") -> dict:
        resp = requests.post(
            f"{self.base_url}/arm",
            json={"scenario_id": scenario_id, "channel": channel, "payload": payload, "defense_profile": defense_profile},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def execute(self, scenario_id: str, channel: str, defense_profile: str = "D4") -> dict:
        resp = requests.post(
            f"{self.base_url}/execute",
            json={"scenario_id": scenario_id, "channel": channel, "defense_profile": defense_profile},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def inject_qr(self, text: str) -> dict:
        """Inject QR code text into the harness channel state."""
        resp = requests.post(
            f"{self.base_url}/inject_qr",
            json={"text": text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def inject_webview(self, html: str, extracted_text: str) -> dict:
        """Inject WebView HTML and extracted text into the harness channel state."""
        resp = requests.post(
            f"{self.base_url}/inject_webview",
            json={"html": html, "extracted_text": extracted_text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def inject_notification(self, text: str) -> dict:
        """Inject notification text into the harness channel state."""
        resp = requests.post(
            f"{self.base_url}/inject_notification",
            json={"text": text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()
