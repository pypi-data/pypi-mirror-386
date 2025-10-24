from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import Optional
import asyncio
import threading
from collections import deque

try:
    import websockets  # type: ignore
    from websockets.exceptions import (
        ConnectionClosed, ConnectionClosedOK, ConnectionClosedError
    )
except Exception:  # pragma: no cover
    websockets = None

import typer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ...core.env import load_config
from ...core.odoo_rpc import OdooRPC
from ...core.utils import info, run


# ----------------------------------------------------------------------
# 💬 WebSocket Bus (with visibility logs & throttled no-client log)
# ----------------------------------------------------------------------
class _WSBus:
    def __init__(self):
        self.clients = set()
        self._last_no_client_log = 0.0  # throttle "no clients" log

    async def handler(self, ws):
        """Handle a connected client and re-broadcast any received messages to all clients."""
        self.clients.add(ws)
        try:
            async for msg in ws:
                try:
                    text = msg.decode() if isinstance(msg, (bytes, bytearray)) else str(msg)
                    if text:
                        await self.broadcast(text)
                except Exception as e:
                    info(f"[opm] WS handler relay error: {e}")
                    continue
        except (ConnectionClosed, ConnectionClosedOK, ConnectionClosedError):
            pass
        except Exception as e:
            info(f"[opm] WS handler error: {e}")
        finally:
            self.clients.discard(ws)

    async def broadcast(self, msg: str):
        """Send message to all clients (skip closed) and log count."""
        if not self.clients:
            now = time.time()
            if now - self._last_no_client_log > 10:
                info("[opm] WS: no connected clients; skipping broadcast")
                self._last_no_client_log = now
            return
        dead = []
        for c in list(self.clients):
            try:
                await c.send(msg)
            except Exception:
                dead.append(c)
        for c in dead:
            try:
                await c.close(code=1011, reason="send failed")
            except Exception:
                pass
            self.clients.discard(c)
        info(f"[opm] WS: broadcast '{msg}' to {len(self.clients)} client(s)")


# ----------------------------------------------------------------------
# 🔎 Detect --dev=all from the Docker container (reliable)
# ----------------------------------------------------------------------
def _detect_dev_all_from_container(container: str | None) -> bool:
    """Return True if the running Odoo process includes --dev=all."""
    if not container:
        return False
    code, out, _ = run([
        "bash", "-lc",
        f"docker exec {container} ps aux | grep -E 'odoo(.bin)? .*(--dev=all|--dev=\\S*all\\S*)' | grep -v grep || true"
    ])
    return (code == 0) and ("--dev=all" in (out or ""))


# ----------------------------------------------------------------------
# ⚙️ WebSocket Server Runner
# ----------------------------------------------------------------------
def _start_ws_server(host: str, port: int, ping_interval: int = 30, ping_timeout: int = 60):
    """
    Start a lightweight WS server in a background thread.
    Returns (broadcast_sync, stop_sync). If websockets is unavailable, both are no-ops.
    """
    if websockets is None:
        def _noop(*_a, **_k): return None
        return _noop, _noop

    bus = _WSBus()
    loop = asyncio.new_event_loop()
    ready = threading.Event()
    stopped = {"flag": False}

    async def _serve_once(h: str, p: int):
        return await websockets.serve(
            bus.handler, h, p,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            close_timeout=1,
            max_size=2**20,
            max_queue=32,
        )

    async def _main():
        srv = None
        bind_port = port
        for _ in range(10):  # try up to 10 consecutive ports if busy
            try:
                srv = await _serve_once(host, bind_port)
                info(f"[opm] WebSocket listening on ws://{host}:{bind_port} (ping {ping_interval}s / timeout {ping_timeout}s)")
                break
            except OSError:
                bind_port += 1
                continue
        if srv is None:
            info("[opm] WS could not bind to any port; live-reload disabled.")
            ready.set()
            return

        ready.set()
        while not stopped["flag"]:
            await asyncio.sleep(0.5)
        srv.close()
        await srv.wait_closed()

    def _runner():
        try:
            loop.run_until_complete(_main())
        finally:
            try:
                loop.stop()
            except Exception:
                pass
            loop.close()

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    ready.wait()

    def broadcast_sync(msg: str):
        if loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(bus.broadcast(msg), loop)
        except Exception:
            pass

    def stop_sync():
        stopped["flag"] = True

    return broadcast_sync, stop_sync


# ----------------------------------------------------------------------
# 👀 Watchdog Event Handler
# ----------------------------------------------------------------------
class _WatchHandler(FileSystemEventHandler):
    def __init__(self, on_change):
        super().__init__()
        self.on_change = on_change

    def on_modified(self, event):
        if event.is_directory:
            return
        self.on_change(Path(event.src_path))


# ----------------------------------------------------------------------
# 🚀 dev command
# ----------------------------------------------------------------------
def dev(
    env: Optional[str] = typer.Option(
        None, "--env", "-e",
        help="Environment name (from opm.yaml 'environments'); if not provided, uses default runtime"
    ),
    config: str = typer.Option(None, help="Path to opm.yaml"),
    addons: Optional[str] = typer.Option("./addons", help="Watch path for addons"),
    module: Optional[str] = typer.Option(None, help="Only target this module for quick upgrades"),
):
    """
    Watch files and trigger RPC-powered hot-reload-like actions.
    """
    cfg = load_config(config)

    # Decide environment
    if env:
        if not hasattr(cfg, "resolve_env"):
            raise typer.BadParameter("Your config does not support 'environments'.")
        try:
            resolved = cfg.resolve_env(env)
        except Exception as e:
            raise typer.BadParameter(f"Environment '{env}' not found/invalid in opm.yaml: {e}")
        if getattr(resolved, "kind", "runtime") != "runtime":
            raise typer.BadParameter(f"'dev' requires kind=runtime, got kind={resolved.kind!r}")
        data = resolved.data
        info(f"Using environment '{env}' → URL: {data.get('odoo_url')}")
    else:
        info("No environment provided, using default runtime configuration.")
        data = {
            "odoo_url": cfg.get("runtime", "odoo_url"),
            "db":       cfg.get("runtime", "db"),
            "user":     cfg.get("runtime", "user"),
            "pass":     cfg.get("runtime", "pass"),
        }

    # Resolve addons path
    if not addons or addons == "./addons":
        candidate = None
        if env:
            env_addons = (data.get("addons") or [])
            if isinstance(env_addons, list) and env_addons:
                candidate = env_addons[0]
        if not candidate:
            rt_addons = (cfg.get("runtime", "addons") or [])
            if isinstance(rt_addons, list) and rt_addons:
                candidate = rt_addons[0]
        if not candidate and Path("./addons").exists():
            candidate = "./addons"
        addons = candidate
        if addons:
            info(f"No --addons provided, using resolved addons path: {addons}")
        else:
            raise typer.BadParameter("No addons path resolved. Pass --addons or define addons in env/runtime or create ./addons")

    addons_path = Path(addons).expanduser()
    if not addons_path.exists():
        raise typer.BadParameter(f"Addons path does not exist: {addons_path}")
    if not addons_path.is_dir():
        raise typer.BadParameter(f"Addons path is not a directory: {addons_path}")

    # Connect to Odoo
    rpc = OdooRPC(data["odoo_url"], data["db"], data["user"], data["pass"])
    rpc.login()
    info(f"Connected to Odoo environment '{env or 'runtime'}'. Watching for changes in: {addons_path}")

    # WebSocket
    ws_host = (cfg.get("runtime", "ws_host") or "127.0.0.1")
    try:
        ws_port = int(cfg.get("runtime", "ws_port") or 8765)
    except Exception:
        ws_port = 8765
    try:
        ws_ping_interval = int(cfg.get("runtime", "ws_ping_interval") or 30)
    except Exception:
        ws_ping_interval = 30
    try:
        ws_ping_timeout = int(cfg.get("runtime", "ws_ping_timeout") or 60)
    except Exception:
        ws_ping_timeout = 60

    broadcast, stop_ws = _start_ws_server(ws_host, ws_port, ws_ping_interval, ws_ping_timeout)
    if websockets is None:
        info("[opm] websockets package not installed; live-reload WS disabled (pip install websockets)")
        def broadcast(_msg: str): return None
        def stop_ws(): return None

    # Debounce & ignore temp files
    _last_events = deque(maxlen=1)  # (path, ts)
    IGNORE_SUFFIXES = ('.swp', '.swo', '.tmp', '.bak', '~')

    # on_change handler
    def on_change(path: Path):
        p = str(path)
        if p.endswith(IGNORE_SUFFIXES):
            return

        # Debounce: skip repeated events for the same file within 300ms
        now = time.time()
        if _last_events and _last_events[0][0] == p and (now - _last_events[0][1]) < 0.3:
            return
        _last_events.append((p, now))

        lower = p.lower()
        try:
            # ---- XML (views/menus/data) ----
            if p.endswith(".xml"):
                needs_upgrade = ("menu" in lower) or ("/data/" in lower)
                if needs_upgrade:
                    target_module = module or Path(p).parts[-2]
                    info(f"[opm] XML (menu/data) changed: {p} → quick upgrade {target_module}")
                    try:
                        rpc.call("opm.dev.tools", "quick_upgrade", target_module)
                    except Exception as e:
                        info(f"[opm] upgrade error: {e}")
                else:
                    info(f"[opm] XML (view) changed: {p} → flush caches")
                    try:
                        rpc.call("opm.dev.tools", "flush_caches")
                    except Exception as e:
                        info(f"[opm] flush error: {e}")
                try:
                    broadcast("reload")
                except Exception:
                    pass
                return

            # ---- Front-end assets ----
            if p.endswith((".scss", ".js")):
                info(f"[opm] Asset changed: {p} → flush caches")
                try:
                    rpc.call("opm.dev.tools", "flush_caches")
                except Exception as e:
                    info(f"[opm] flush error: {e}")
                finally:
                    try:
                        broadcast("reload")
                    except Exception:
                        pass
                return

            # ---- Python / manifest ----
            if p.endswith(".py") or p.endswith("__manifest__.py"):
                target_module = module or Path(p).parts[-2]
                info(f"[opm] Python/manifest changed: {p}")

                # 1) Try to detect dev=all via config parameter
                is_dev_all = False
                try:
                    mode = rpc.call("ir.config_parameter", "get_param", "dev_mode")
                    if mode and "all" in str(mode).lower():
                        is_dev_all = True
                except Exception as e:
                    info(f"[opm] dev_mode check failed (possibly during reload): {e}")

                # 2) Fallback: inspect the running container command
                if not is_dev_all:
                    container_name = cfg.get("runtime", "container")
                    if _detect_dev_all_from_container(container_name):
                        is_dev_all = True

                if is_dev_all:
                    info("[opm] Detected Odoo dev=all → skip quick_upgrade RPC; broadcasting reload only")
                    try:
                        broadcast(f"reload:{target_module}")
                    except Exception:
                        pass
                    return

                # Normal mode → perform quick upgrade, but tolerate gateway errors
                info(f"[opm] Performing quick upgrade for {target_module}")
                try:
                    rpc.call("opm.dev.tools", "quick_upgrade", target_module)
                except Exception as e:
                    # If Odoo is hot-reloading and Nginx returns 502, don't fail dev loop
                    if "502" in str(e) or "Bad Gateway" in str(e):
                        info("[opm] Odoo likely reloading (502) → broadcasting safe reload without RPC")
                    else:
                        info(f"[opm] upgrade error: {e}")
                finally:
                    try:
                        broadcast(f"reload:{target_module}")
                    except Exception:
                        pass
                return

            # ---- Other files ----
            info(f"[opm] Changed: {p} (no action)")

        except Exception as e:
            # Guard against any unexpected watcher errors
            info(f"[opm] on_change error: {e}")
            try:
                broadcast("reload")
            except Exception:
                pass

    # Start watchdog
    handler = _WatchHandler(on_change)
    observer = Observer()
    observer.schedule(handler, path=str(addons_path), recursive=True)
    observer.start()

    # ------------------------------------------------------------------
    # ⌨️  Keyboard listener: press 'r' to broadcast a reload (TTY only)
    # ------------------------------------------------------------------
    def _keyboard_listener():
        """Listen for keyboard input ('r' or 'R') to trigger a browser reload."""
        if not sys.stdin.isatty():
            info("[opm] stdin is not a TTY; manual 'r' reload disabled.")
            return
        info("[opm] Press 'r' to manually trigger browser reload.")
        while True:
            try:
                ch = sys.stdin.read(1)
                if not ch:
                    time.sleep(0.2)
                    continue
                if ch.lower() == 'r':
                    info("[opm] Manual reload requested → broadcasting 'reload'")
                    try:
                        broadcast("reload")
                    except Exception as e:
                        info(f"[opm] Manual reload broadcast failed: {e}")
            except Exception:
                break

    if sys.stdin.isatty():
        threading.Thread(target=_keyboard_listener, daemon=True).start()

    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        try:
            stop_ws()
        except Exception:
            pass
    observer.join()