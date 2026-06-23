"""Local-only mock LMS server.

This is a tiny HTTP server that wraps the in-process state machine. It is
deliberately small and dependency-free so the test suite can spawn it
without external services.

The server's contract:
- It listens on 127.0.0.1 only.
- It implements only the *shape* of the protocol described in
  ``docs/protocol-research-method.md``. It does NOT mimic any real
  vendor's behavior.
- It always returns HTTP 200 for well-formed requests, but the JSON body
  separates ``http_ok``, ``business_accepted``, ``progress_updated`` and
  ``reason``. That separation is the entire reason this harness exists.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from .state_machine import (
    HeartbeatEvent,
    ServerState,
    process_event,
)


def make_handler(states: dict[int, ServerState]):
    """Build a request handler bound to a state map."""

    class Handler(BaseHTTPRequestHandler):
        # Quiet the default stderr logging; tests assert on response bodies.
        def log_message(self, format, *args):  # noqa: A002
            return

        def _send(self, code: int, body: dict) -> None:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):  # noqa: N802
            if self.path != "/heartbeat":
                self._send(404, {"error": "not_found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                form = parse_qs(raw, keep_blank_values=True)
            except Exception:
                self._send(400, {"error": "bad_form"})
                return

            try:
                event = HeartbeatEvent(
                    video_id=int(form.get("video_id", ["0"])[0]),
                    seq=int(form.get("seq", ["0"])[0]),
                    et=form.get("et", [""])[0],
                    cp=float(form.get("cp", ["0"])[0]),
                    ts_ms=int(form.get("ts_ms", ["0"])[0]),
                    sp=int(form.get("sp", ["1"])[0]),
                )
            except (ValueError, TypeError):
                self._send(400, {"error": "bad_event_shape"})
                return

            state = states.get(event.video_id)
            if state is None:
                self._send(
                    200,
                    {
                        "http_ok": True,
                        "business_accepted": False,
                        "progress_updated": False,
                        "reason": "unknown_video",
                    },
                )
                return

            accepted, http_ok, reason = process_event(state, event)
            self._send(
                200,
                {
                    "http_ok": http_ok,
                    "business_accepted": accepted,
                    "progress_updated": accepted,
                    "reason": reason,
                    "video_id": event.video_id,
                    "seq": event.seq,
                    "state": {
                        "accepted": state.accepted,
                        "rejected": state.rejected,
                        "business_completed": state.business_completed,
                        "last_cp": state.last_cp,
                    },
                },
            )

        def do_GET(self):  # noqa: N802
            if self.path.startswith("/state/"):
                try:
                    vid = int(self.path[len("/state/"):])
                except ValueError:
                    self._send(400, {"error": "bad_video_id"})
                    return
                state = states.get(vid)
                if state is None:
                    self._send(404, {"error": "unknown_video"})
                    return
                self._send(
                    200,
                    {
                        "video_id": state.video_id,
                        "duration": state.duration,
                        "expected_count": state.expected_count,
                        "accepted": state.accepted,
                        "rejected": state.rejected,
                        "business_completed": state.business_completed,
                        "last_cp": state.last_cp,
                        "last_reason": state.last_reason,
                    },
                )
                return
            self._send(404, {"error": "not_found"})

    return Handler


class MockLMSServer:
    """Convenience wrapper around ThreadingHTTPServer."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        states: dict[int, ServerState] | None = None,
    ) -> None:
        self.states: dict[int, ServerState] = states or {}
        self._server = ThreadingHTTPServer(
            (host, port), make_handler(self.states)
        )
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def register(self, video_id: int, duration: float, expected_count: int) -> None:
        self.states[video_id] = ServerState(
            video_id=video_id,
            duration=duration,
            expected_count=expected_count,
        )