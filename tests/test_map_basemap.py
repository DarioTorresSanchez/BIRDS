"""The basemap download must never take the interface with it.

``contextily`` fetches tiles one at a time through ``requests.get``
with no timeout (``contextily.tile._retryer``), and ``add_basemap``
forwards neither ``n_connections`` nor ``max_retries``, so there is no
way to bound it from the outside.  Called straight from the redraw, as
the Map view used to, a slow provider freezes the window for as long as
the server likes -- one measured CartoDB Positron fetch took 1204 s
against 3.5 s for Esri on the same extent.

These tests use a local socket that accepts connections and then says
nothing, so they prove the deadline without depending on the weather on
someone else's CDN.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest
import xyzservices

from birds.views.map_view import (
    BASEMAP_TIMEOUT_S,
    _TILE_CONNECTIONS,
    _fetch_basemap,
)


@pytest.fixture
def silent_tile_server():
    """A server that accepts a connection and never answers."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(16)
    port = listener.getsockname()[1]
    stop = threading.Event()
    held = []

    def _accept():
        listener.settimeout(0.2)
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except (TimeoutError, OSError):
                continue
            held.append(connection)          # keep it open, send nothing

    thread = threading.Thread(target=_accept, daemon=True)
    thread.start()
    yield xyzservices.TileProvider(
        name="silent test server",
        url=f"http://127.0.0.1:{port}/{{z}}/{{x}}/{{y}}.png",
        attribution="silent test server",
        max_zoom=19,
    )
    stop.set()
    thread.join(2.0)
    for connection in held:
        connection.close()
    listener.close()


#: A small extent somewhere over land, in EPSG:3857 metres.
BOUNDS = (-11_000_000.0, 2_200_000.0, -10_970_000.0, 2_230_000.0)


class TestTheDeadline:

    def test_a_server_that_never_answers_gives_up_on_time(
            self, silent_tile_server):
        started = time.monotonic()
        got = _fetch_basemap(BOUNDS, silent_tile_server, timeout_s=1.0)
        elapsed = time.monotonic() - started
        assert got is None
        assert elapsed < 4.0, (
            f"waited {elapsed:.1f} s for a 1 s deadline")
        assert elapsed >= 0.9, (
            "returned before the deadline; the wait was not real")

    def test_the_deadline_is_what_sets_the_wait(self, silent_tile_server):
        """Two deadlines, two waits -- so the bound is the deadline and
        not something else finishing early."""
        short = time.monotonic()
        _fetch_basemap(BOUNDS, silent_tile_server, timeout_s=0.5)
        short = time.monotonic() - short

        longer = time.monotonic()
        _fetch_basemap(BOUNDS, silent_tile_server, timeout_s=2.0)
        longer = time.monotonic() - longer

        assert longer > short + 0.8

    def test_a_refused_connection_is_not_an_error(self):
        """Nothing is listening, so the fetch fails at once.  The view
        wants ``None`` back, not an exception to handle."""
        closed = socket.socket()
        closed.bind(("127.0.0.1", 0))
        port = closed.getsockname()[1]
        closed.close()
        provider = xyzservices.TileProvider(
            name="nothing here",
            url=f"http://127.0.0.1:{port}/{{z}}/{{x}}/{{y}}.png",
            attribution="nothing here", max_zoom=19)
        assert _fetch_basemap(BOUNDS, provider, timeout_s=5.0) is None


class TestTheWaitDoesNotFreezeTheWindow:

    def test_the_tick_runs_while_the_fetch_is_out(self, silent_tile_server):
        """The view passes ``QApplication.processEvents`` here, which is
        what keeps the window painting rather than greying out."""
        ticks = []
        _fetch_basemap(BOUNDS, silent_tile_server, timeout_s=1.0,
                       on_tick=lambda: ticks.append(time.monotonic()))
        assert len(ticks) > 5, f"only {len(ticks)} ticks in a 1 s wait"
        # Spread across the wait, not all at the end.
        assert ticks[-1] - ticks[0] > 0.5

    def test_no_tick_is_also_fine(self, silent_tile_server):
        assert _fetch_basemap(BOUNDS, silent_tile_server,
                              timeout_s=0.5) is None


class TestTheAbandonedFetch:

    def test_the_worker_cannot_keep_the_app_from_closing(
            self, silent_tile_server):
        """The thread outlives the deadline by design -- a Python thread
        cannot be killed -- so it has to be a daemon.

        This is why the fetch does not use ThreadPoolExecutor, whose
        workers are not daemons: an abandoned download would hold the
        interpreter open and closing the app would hang on it.
        """
        # By identity, not by name: an earlier test in this file leaves
        # its own orphan behind, and they all share the one name.
        before = {id(t) for t in threading.enumerate()}
        _fetch_basemap(BOUNDS, silent_tile_server, timeout_s=0.5)
        orphans = [t for t in threading.enumerate()
                   if id(t) not in before and t.name == "birds-basemap"]
        assert orphans, "expected the fetch to still be running"
        assert all(t.daemon for t in orphans), (
            "a non-daemon orphan would block interpreter exit")


class TestSettings:

    def test_tiles_are_fetched_several_at_a_time(self):
        """contextily defaults to one connection, which is what made a
        slow provider so slow."""
        assert _TILE_CONNECTIONS > 1

    def test_the_default_deadline_is_a_wait_not_a_hang(self):
        assert 5.0 <= BASEMAP_TIMEOUT_S <= 60.0
