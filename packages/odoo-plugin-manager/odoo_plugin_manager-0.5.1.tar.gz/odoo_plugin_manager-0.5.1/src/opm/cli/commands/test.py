from __future__ import annotations
import shlex
from pathlib import Path
import typer
import os

from datetime import datetime
import time

from ...core.env import load_config
from ...core.utils import info, run

def _module_exists_on_host(module: str, host_addons: str | None) -> bool:
    if not host_addons:
        return False
    p = Path(host_addons).expanduser().resolve() / module
    return p.is_dir()

def _module_exists_in_container(module: str, container: str) -> bool:
    # /mnt/extra-addons altında var mı?
    code, out, _ = run([
        "bash", "-lc",
        f"docker exec -i {shlex.quote(container)} sh -lc '[ -d /mnt/extra-addons/{shlex.quote(module)} ] && echo OK || true'"
    ])
    return (code == 0) and ("OK" in (out or ""))

def test(
    module: str = typer.Argument(..., help="Module name (e.g. opm_dev_helper)"),
    db: str = typer.Option(None, "--db", "-d", help="Database name (fallback: runtime.db)"),
    container: str = typer.Option(None, "--container", "-c", help="Docker container name for Odoo (use `docker ps`)"),
    addons: str = typer.Option(None, "--addons", help="Host addons path (fallback: runtime.addons[0])"),
    extra_ports: bool = typer.Option(True, "--extra-ports/--no-extra-ports", help="Avoid port clashes by using 8070+"),
    debug: bool = typer.Option(False, "--debug", help="Enable Odoo debug logging"),
    no_tty: bool = typer.Option(False, "--no-tty", help="Disable TTY for docker exec (use -i instead of -it)"),
):
    
    """
    Run Odoo module tests (⚠️ development use only, not for production).
    """
    
    cfg = load_config()
    info("[opm] 🧪 Starting test run…")
    container = container or cfg.get("runtime", "container")
    db = db or cfg.get("runtime", "db") or "odoo"
    
    info(f"[opm] Target DB: {db}")
    info(f"[opm] Target container: {container or 'LOCAL (odoo in PATH)'}")

    db_host = cfg.get("runtime", "db_host") or ""
    db_port = cfg.get("runtime", "db_port") or ""
    db_user = cfg.get("runtime", "db_user") or ""
    db_password = cfg.get("runtime", "db_password") or ""

    db_args = []
    if db_host:     db_args += [f"--db_host={db_host}"]
    if db_port:     db_args += [f"--db_port={db_port}"]
    if db_user:     db_args += [f"--db_user={db_user}"]
    if db_password: db_args += [f"--db_password={db_password}"]

    if db_host or db_port or db_user or db_password:
        info(f"[opm] DB conn: host={db_host or '-'} port={db_port or '-'} user={db_user or '-'}")

    # Resolve addons path (host)
    host_addons = addons
    if not host_addons:
        rta = cfg.get("runtime", "addons") or []
        if rta:
            host_addons = str(Path(rta[0]).expanduser().resolve())

    info(f"[opm] Host addons: {host_addons or '(not provided)'}")

    # --- preflight module existence check ---
    found_locally = _module_exists_on_host(module, host_addons)
    found_in_container = False
    if container:
        try:
            found_in_container = _module_exists_in_container(module, container)
        except Exception:
            found_in_container = False

    if not (found_locally or found_in_container):
        info(
            f"❌ Module '{module}' not found under any addons path.\n"
            f"   Checked host: {host_addons or '(unset)'}\n"
            f"   Checked container: /mnt/extra-addons/{module} (container={container or 'N/A'})\n"
            f"   Hints:\n"
            f"   • Ensure runtime.addons points to the folder that contains '{module}/'.\n"
            f"   • If running in Docker, bind-mount that folder to /mnt/extra-addons.\n"
            f"   • Or pass --addons /path/to/addons explicitly."
        )
        raise typer.Exit(2)

    # Build addons-path (inside container)
    addons_path = "/usr/lib/python3/dist-packages/odoo/addons"
    if host_addons:
        # assumes your compose mounts host_addons -> /mnt/extra-addons
        addons_path = f"{addons_path},/mnt/extra-addons"

    info(f"[opm] In-container addons-path: {addons_path}")
    info("[opm] Install/Upgrade mode: auto (-i & -u)")

    if container:
        info("[opm] Detecting Odoo binary inside the container…")
        # Detect odoo binary inside the container (odoo or odoo-bin)
        code, out, err = run([
            "bash", "-lc",
            f"docker exec -i {shlex.quote(container)} sh -lc 'command -v odoo || command -v odoo-bin'",
        ])
        if code != 0 or not (out or "").strip():
            info(f"❌ No 'odoo' or 'odoo-bin' found in container: {container}")
            raise typer.Exit(1)
        odoo_bin = (out or "").strip()
        info(f"[opm] Odoo binary: {odoo_bin}")

        # --- Determine extra ports (Odoo 18: --longpolling-port removed) ---
        if extra_ports:
            # Detect supported port flags inside the container (odoo --help)
            code_h, out_h, _ = run([
                "bash", "-lc",
                f"docker exec -i {shlex.quote(container)} sh -lc '{shlex.quote(odoo_bin)} --help || true'"
            ])
            help_txt = (out_h or "")

            parts = []
            # --http-port is still valid
            if "--http-port" in help_txt:
                parts.append("--http-port=8070")
            # --longpolling-port existed up to v17; skip on v18+
            if "--longpolling-port" in help_txt:
                parts.append("--longpolling-port=8071")

            ports = " ".join(parts)
            if parts:
                info(f"[opm] Extra ports enabled: {ports}")
            else:
                info("[opm] No extra port flags supported by this Odoo build.")
        else:
            ports = ""
            info("[opm] Extra ports disabled (using container defaults)")

        tty_flag = "-i" if no_tty else "-it"
        log_flag = "--log-level=debug" if debug else ""
        # Always force Odoo to write to STDOUT so we can capture logs reliably
        log_file_flag = "--logfile=-"
        container_log = f"/tmp/opm_test_{int(time.time())}.log"
        # Force logfile to a container path we can copy back reliably
        log_file_flag = f"--logfile={container_log}"

        db_args_str = " ".join(db_args)
        cmd = f"""docker exec {tty_flag} {shlex.quote(container)} {shlex.quote(odoo_bin)} -d {shlex.quote(db)} \
                  -i {shlex.quote(module)} -u {shlex.quote(module)} --test-enable --stop-after-init \
                  --addons-path={shlex.quote(addons_path)} {db_args_str} {ports} {log_flag} {log_file_flag}"""
    else:
        # bare-metal fallback (expects `odoo` in PATH)
        db_args_str = " ".join(db_args)
        extra_log = " --log-level=debug" if debug else ""
        cmd = f"""stdbuf -oL -eL odoo -d {shlex.quote(db)} -i {shlex.quote(module)} -u {shlex.quote(module)} \
                  --test-enable --stop-after-init --addons-path={shlex.quote(addons_path)} {db_args_str} --logfile=-{extra_log}"""

    info("[opm] ▶️  Executing test command…")
    info(f"[opm] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    t0 = time.time()
    # redacted preview (do not leak db password in logs)
    redacted_cmd = cmd
    if db_password:
        redacted_cmd = redacted_cmd.replace(f"--db_password={db_password}", "--db_password=******")
    # Uncomment the next line if you want to see the full command for debugging
    # info(f"[opm] running: {redacted_cmd}")

    if no_tty:
        info("[opm] no-tty mode active (docker exec -i; stdout/stderr will be captured)")

    # Ensure artifacts dir and wrap command to capture ALL output (stdout+stderr) to a host log file
    artifacts_dir = Path(".opm/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    host_log = artifacts_dir / "test_last.log"

    # Use bash pipefail + tee so we both capture and persist logs; preserve real exit code via PIPESTATUS
    wrapped = (
        f"{cmd}; ec=$?; "
        f"docker cp {shlex.quote(container)}:{shlex.quote(container_log)} {shlex.quote(str(host_log.resolve()))} >/dev/null 2>&1 || true; "
        f"exit $ec"
    )

    code, out, err = run(["bash", "-lc", wrapped])
    info(f"[opm] ⏱️  Duration: {time.time() - t0:.1f}s")
    if code == 0:
        info("✅ Tests finished successfully.")
    else:
        info("❌ Tests failed. Command (redacted):")
        print(redacted_cmd)
        info("Last lines:")
        tail = (out or err or "").splitlines()[-80:]
        if not tail and host_log.exists():
            try:
                tail = host_log.read_text(errors="ignore").splitlines()[-200:]
            except Exception:
                tail = []
        print("\n".join(tail))
        info(f"[opm] 📄 Full log: {host_log}")
        raise typer.Exit(code)