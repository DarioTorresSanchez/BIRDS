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
    silence_joblib_cache_noise,
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

    def test_the_worker_is_a_daemon(self, silent_tile_server, monkeypatch):
        """Past the deadline the thread is still running -- a Python
        thread cannot be killed -- so it has to be a daemon.

        This is why the fetch does not use ThreadPoolExecutor, whose
        workers are not daemons: an abandoned download would hold the
        interpreter open and closing the app would hang on it.

        Asserted on the thread as it is created rather than by hunting
        for a survivor afterwards.  Whether one survives depends on how
        fast the fetch happens to fail, which made that version of this
        test flaky.
        """
        created = []
        real_thread = threading.Thread

        def record(*args, **kwargs):
            thread = real_thread(*args, **kwargs)
            created.append(thread)
            return thread

        monkeypatch.setattr(threading, "Thread", record)
        _fetch_basemap(BOUNDS, silent_tile_server, timeout_s=0.5)

        ours = [t for t in created if t.name == "birds-basemap"]
        assert len(ours) == 1, f"expected one worker, got {len(ours)}"
        assert ours[0].daemon, (
            "a non-daemon worker would block interpreter exit")


class TestTheJoblibNoise:
    """contextily memoises its tile fetcher with joblib, which now and
    then decides the cached function is not the one it cached and says
    so at length in the terminal.

    joblib's own answer to that mismatch is to drop the entry and call
    the function again -- one tile re-downloaded -- so nothing reaches
    the map wrong.  The view filters the message because it reads like a
    crash, not because it matters.

    Each test reinstalls the filter inside its own ``catch_warnings``
    block: pytest resets the global filters around every test, so the
    one the module installs at import is long gone by now.
    """

    MESSAGE = ("Possible name collisions between functions '_fetch_tile' "
               "(/x/contextily/tile.py:-1) and '_fetch_tile' "
               "(/x/contextily/tile.py:327)")

    @staticmethod
    def _collision():
        return pytest.importorskip("joblib.memory").JobLibCollisionWarning

    def _caught(self, message, category):
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            silence_joblib_cache_noise()
            warnings.warn(message, category, stacklevel=2)
        return caught

    def test_the_collision_message_is_filtered(self):
        assert self._caught(self.MESSAGE, self._collision()) == []

    def test_other_joblib_warnings_still_get_through(self):
        """Filtered on the message as well as the category, so this is
        not a blanket mute of everything joblib has to say."""
        assert len(self._caught("the cache directory changed",
                                self._collision())) == 1

    def test_the_same_words_in_another_category_get_through(self):
        """And not a substring match against any warning at all."""
        assert len(self._caught(self.MESSAGE, UserWarning)) == 1


class TestSettings:

    def test_tiles_are_fetched_several_at_a_time(self):
        """contextily defaults to one connection, which is what made a
        slow provider so slow."""
        assert _TILE_CONNECTIONS > 1

    def test_the_default_deadline_is_a_wait_not_a_hang(self):
        assert 5.0 <= BASEMAP_TIMEOUT_S <= 60.0
