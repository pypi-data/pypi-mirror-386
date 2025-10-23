#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# rsyncx - CLI de sincronización segura basada en rsync (Synology + multi-equipo)
# -----------------------------------------------------------------------------
# Comandos:
#   configure  -> instala dependencias y crea ~/.xsoft/rsyncx/config.py desde rsyncx/config.dist.py
#   push       -> SUBE (local -> remoto) con papelera versionada en remoto
#   pull       -> BAJA (remoto -> local) y sincroniza también _papelera (solo pull)
#   run        -> push + pull (primer uso seguro: pull inicial si no hay .datarsyncx)
#   purge      -> borra papeleras local y remota
#   time       -> muestra último timestamp de sincronización por grupo
#
# Consideraciones:
#   - La "papelera maestra" es la del Synology. La local es un espejo (solo pull).
#   - En push NO subimos la papelera local.
#   - En pull NO borramos archivos locales si no existen en remoto (protección).
#   - En pull SÍ espejamos la papelera (remota) en local.
# -----------------------------------------------------------------------------

import argparse
import os
import sys
import subprocess
import shutil
import platform
import importlib.util
import socket
import json
import getpass
from datetime import datetime, timezone
from pathlib import Path

# Import de nuestro helper de rsync (para PUSH)
from rsyncx.rsync_command import build_rsync_command, run_rsync

# Rutas fijas del proyecto/config
CONFIG_DIR = Path.home() / ".xsoft" / "rsyncx"
CONFIG_PATH = CONFIG_DIR / "config.py"
PACKAGE_DIR = Path(__file__).resolve().parent
RSYNC_FILTER_FILE = Path.home() / ".xsoft/rsyncx/.rsync-filter"
CONFIG_DIST = PACKAGE_DIR / "config.dist.py"  # plantilla incluida en el paquete

# -----------------------------------------------------------------------------
# Utilidades de presentación
# -----------------------------------------------------------------------------

def print_header():
    print("rsyncx - sincronizador seguro (push/pull) con papelera remota")

def iso_now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def format_ago(when_iso: str) -> str:
    try:
        when = datetime.fromisoformat(when_iso)
    except Exception:
        return "desconocido"
    now = datetime.now(when.tzinfo or timezone.utc)
    delta = now - when
    secs = int(delta.total_seconds())
    if secs < 0:
        secs = 0
    m = secs // 60
    h = m // 60
    d = h // 24
    if secs < 60:
        return f"hace {secs} s"
    if m < 60:
        return f"hace {m} min"
    if h < 24:
        rem = m % 60
        return f"hace {h} h {rem} min" if rem else f"hace {h} h"
    remh = h % 24
    return f"hace {d} d {remh} h" if remh else f"hace {d} d"

# -----------------------------------------------------------------------------
# Estado por grupo (.datarsyncx en la carpeta local del grupo)
# -----------------------------------------------------------------------------

def meta_path_for_group(local_path: Path) -> Path:
    return Path(local_path) / ".datarsyncx"

def read_group_meta(local_path: Path):
    p = meta_path_for_group(local_path)
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8") or "{}")
    except Exception:
        pass
    return None

def write_group_meta(local_path: Path, action: str):
    p = meta_path_for_group(local_path)
    meta = {
        "last_sync": iso_now(),
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "last_action": action,  # "push" | "pull" | "run"
    }
    try:
        p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"⚠ No se pudo actualizar .datarsyncx en {local_path}: {e}")

def ensure_group_meta_exists(local_path: Path):
    p = meta_path_for_group(local_path)
    if not p.exists():
        try:
            p.write_text("", encoding="utf-8")
        except Exception:
            pass  # no es crítico

def meta_exists_and_nonempty(local_path: Path) -> bool:
    p = meta_path_for_group(local_path)
    try:
        return p.exists() and p.stat().st_size > 0
    except Exception:
        return False

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

def ensure_config_exists():
    """Crea ~/.xsoft/rsyncx/config.py y ~/.xsoft/rsyncx/.rsync-filter si no existen; y si hay grupos con carpeta local existente, crea .datarsyncx vacío."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # --- CONFIG PRINCIPAL ---
    if not CONFIG_PATH.exists():
        if CONFIG_DIST.exists():
            shutil.copyfile(CONFIG_DIST, CONFIG_PATH)
            print(f"✔ Config creado: {CONFIG_PATH}")
        else:
            CONFIG_PATH.write_text(
                "# Config de ejemplo para rsyncx\n\n"
                "parallel = 2\n"
                "rsync_path = '/usr/bin/rsync'\n\n"
                "servers = {\n"
                "    'default': {\n"
                "        'host_local': '192.168.1.185',\n"
                "        'host_vpn': '100.95.203.63',\n"
                "        'port': 2908,\n"
                "        'user': 'rsyncx_user',\n"
                "        'remote': '/volume1/devBackup/rsyncx_mac/',\n"
                "        'identity': 'passw',\n"
                "        'file': '',\n"
                "        'passw': 'cambia_esto'\n"
                "    }\n"
                "}\n\n"
                "SINCRONIZAR = [\n"
                "    {\n"
                "        'grupo': 'ejemplo',\n"
                "        'server': 'default',\n"
                "        'name_folder_backup': 'carpetaEjemplo',\n"
                "        'sync': '~/rsyncx_demo/'\n"
                "    }\n"
                "]\n"
            )
            print(f"✔ Config de emergencia generado: {CONFIG_PATH}")
    else:
        print(f"✔ Config existente: {CONFIG_PATH}")

    # --- FILTRO RSYNC ---
    FILTER_PATH = CONFIG_DIR / ".rsync-filter"
    if not FILTER_PATH.exists():
        FILTER_PATH.write_text(
            "# Filtros globales de rsyncx\n"
            "# Formato rsync-filter:\n"
            "# - Excluir => \"- pattern\"\n"
            "# + Incluir => \"+ pattern\"\n\n"
            "# Carpetas del sistema y ocultas\n"
            "- @eaDir/\n"
            "- .Trash*/\n"
            "- .Spotlight*/\n"
            "- .fseventsd/\n"
            "- .TemporaryItems/\n"
            "- .cache/\n"
            "- .idea/\n"
            "- **/.idea/\n\n"
            "# Carpetas de entornos virtuales\n"
            "- venv/\n"
            "- **/venv/\n"
            "- VENV/\n"
            "- **/VENV/\n"
            "- menv/\n"
            "- **/menv/\n\n"
            "# Carpetas de compilación y temporales\n"
            "- __pycache__/\n"
            "- **/__pycache__/\n"
            "- node_modules/\n"
            "- **/node_modules/\n"
            "- dist/\n"
            "- **/dist/\n"
            "- build/\n"
            "- **/build/\n\n"
            "# Archivos temporales y de sistema\n"
            "- .DS_Store\n"
            "- Thumbs.db\n"
            "- *.pyc\n"
            "- *.pyo\n"
            "- *.tmp\n"
            "- *.swp\n"
            "- *.swo\n"
            "- *.log\n"
            "- @eaDir\n"
        )
        print(f"✔ Filtro creado: {FILTER_PATH}")
    else:
        print(f"✔ Filtro existente: {FILTER_PATH}")

    # Crear .datarsyncx vacío para grupos con carpeta ya existente
    # (esto es un “nice to have”; si no existe, se creará en el primer run/push/pull)
    try:
        cfg = load_config(silent=True)
        for g in getattr(cfg, "SINCRONIZAR", []):
            lp = Path(g.get("sync", "")).expanduser()
            if lp.is_dir():
                ensure_group_meta_exists(lp)
    except Exception:
        pass

def load_config(silent: bool = False):
    """Carga ~/.xsoft/rsyncx/config.py como módulo."""
    if not CONFIG_PATH.exists():
        print("❌ No se encontró configuración. Ejecuta: rsyncx configure")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("rsyncx_user_config", str(CONFIG_PATH))
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    if not silent:
        return config
    return config

def install_if_missing(pkg):
    """Instala (si es posible) un paquete del SO (rsync, sshpass) en macOS/Linux. En otros SO, solo avisa."""
    print(f"• comprobando {pkg}...")
    if shutil.which(pkg):
        print(f"  ✔ {pkg} ya está instalado.")
        return True

    system = platform.system().lower()
    if "darwin" in system:
        if shutil.which("brew"):
            print(f"  ➜ instalando {pkg} con Homebrew...")
            os.system(f"brew install {pkg}")
            ok = shutil.which(pkg) is not None
            print("  ✔ ok" if ok else "  ✖ fallo")
            return ok
        else:
            print(f"  ✖ Homebrew no encontrado. Instala {pkg} manualmente: https://brew.sh/")
            return False
    elif "linux" in system:
        print(f"  ➜ intentando apt/dnf para {pkg}...")
        rc = os.system(f"sudo apt-get install -y {pkg} || sudo dnf install -y {pkg}")
        ok = (rc == 0) and shutil.which(pkg)
        print("  ✔ ok" if ok else "  ✖ fallo")
        return bool(ok)
    else:
        print(f"  ✖ instalación automática no soportada en {system}. Instala {pkg} manualmente.")
        return False

def configure():
    """Instala dependencias (en lo posible) y crea el config desde la plantilla del paquete."""
    print_header()
    print("⚙ Preparando entorno (configure)...")

    ensure_config_exists()

    print("\n🔍 Comprobando dependencias del sistema...")
    rsync_ok = install_if_missing("rsync")
    sshpass_ok = install_if_missing("sshpass")

    if rsync_ok and sshpass_ok:
        print("✔ Todas las dependencias necesarias están disponibles.")
    else:
        print("⚠ Algunas dependencias faltan. Revisa manualmente su instalación.")

    print("\n✔ Configuración inicial lista. Edita si hace falta:")
    print(f"  {CONFIG_PATH}")

# -----------------------------------------------------------------------------
# Red y remoto
# -----------------------------------------------------------------------------

def choose_reachable_host(server_conf):
    local_host = server_conf.get("host_local")
    vpn_host = server_conf.get("host_vpn")
    port = int(server_conf.get("port", 22))

    if local_host:
        try:
            with socket.create_connection((local_host, port), timeout=1):
                print(f"🌐 Usando host local: {local_host}")
                return local_host
        except Exception:
            pass

    if vpn_host:
        print(f"🛰 Usando host VPN: {vpn_host}")
        return vpn_host

    print("❌ No hay host_local ni host_vpn definido en el server.")
    sys.exit(1)

def ensure_remote_dirs(server_conf, host_selected, remote_root):
    """Crea el arbol remoto vía sshpass -e; silencia errores de auth (dejamos que rsync con pass haga el trabajo)."""
    env = os.environ.copy()
    env["SSHPASS"] = server_conf.get("passw", "")

    cmd = [
        "sshpass", "-e",
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-p", str(server_conf["port"]),
        f"{server_conf['user']}@{host_selected}",
        f"mkdir -p '{remote_root}' '{remote_root}/_papelera'"
    ]

    print(f"🛠 Verificando estructura remota ({host_selected})...")
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, env=env)
        if result.stdout.strip():
            print(result.stdout.strip())
        print("🧱 Estructura remota verificada correctamente.")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip().lower()
        if "permission denied" in stderr or "please try again" in stderr:
            # Silencio: en el paso de rsync usaremos sshpass y funcionará
            pass
        else:
            print(f"⚠ No se pudo asegurar la estructura remota: {e.stderr.strip() if e.stderr else e}")

# -----------------------------------------------------------------------------
# PUSH / PULL
# -----------------------------------------------------------------------------

def sync_push(group_conf, server_conf):
    print(f"\n🟢 SUBIENDO (push) grupo: {group_conf['grupo']}")
    local_path = Path(group_conf["sync"]).expanduser()
    remote_root = os.path.join(server_conf["remote"], group_conf["name_folder_backup"])

    host_selected = choose_reachable_host(server_conf)
    ensure_remote_dirs(server_conf, host_selected, remote_root)

    server_conf = dict(server_conf)
    server_conf["selected_host"] = host_selected

    cmd, env = build_rsync_command(server_conf, str(local_path), remote_root)
    run_rsync(cmd, env)  # si falla, ya imprime

    # Marca estado
    write_group_meta(local_path, "push")

def rsync_pull_main(server_conf, host_selected, remote_root, local_path):
    """Pull del contenido principal: traer nuevos/actualizados; no borrar local."""
    passw = server_conf.get("passw", "")
    ssh_e = f"ssh -o StrictHostKeyChecking=no -p {server_conf['port']}"
    src = f"{server_conf['user']}@{host_selected}:{remote_root}/"
    dst = f"{str(local_path)}/"

    cmd = [
        "sshpass", "-p", passw,
        "rsync",
        "-avz",
        "--update",
        "--progress",
        "--partial",
        "--exclude-from", str(RSYNC_FILTER_FILE),
        "--exclude", "_papelera/",
        "-e", ssh_e,
        src, dst
    ]
    print("🔵 Descargando (pull) contenido principal...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en pull (main): {e}")

def rsync_pull_trash(server_conf, host_selected, remote_root, local_path):
    """Espeja la papelera remota en local (_papelera)."""
    print("🔵 Descargando (pull) papelera remota...")
    cmd = [
        "sshpass", "-p", server_conf["passw"],
        "rsync", "-avz", "--update", "--progress", "--partial", "--delete",
        "-e", f"ssh -o StrictHostKeyChecking=no -p {server_conf['port']}",
        f"{server_conf['user']}@{host_selected}:{remote_root}/_papelera/",
        f"{local_path}/_papelera/"
    ]
    try:
        subprocess.run(cmd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        if "No such file or directory" in stderr or "No such file" in stderr:
            print("🗑 No hay papelera remota. Se creará automáticamente al subir archivos borrados.")
        else:
            print(f"⚠ Error en pull (trash): {stderr.strip()}")

def sync_pull(group_conf, server_conf):
    print(f"\n🔵 DESCARGANDO (pull) grupo: {group_conf['grupo']}")
    local_path = Path(group_conf["sync"]).expanduser()
    local_path.mkdir(parents=True, exist_ok=True)
    remote_root = os.path.join(server_conf["remote"], group_conf["name_folder_backup"])

    host_selected = choose_reachable_host(server_conf)

    rsync_pull_main(server_conf, host_selected, remote_root, local_path)
    rsync_pull_trash(server_conf, host_selected, remote_root, local_path)

    # Marca estado
    write_group_meta(local_path, "pull")

# -----------------------------------------------------------------------------
# RUN (primer uso seguro)
# -----------------------------------------------------------------------------

def sync_run(group_conf, server_conf):
    local_path = Path(group_conf["sync"]).expanduser()
    first_time = not meta_exists_and_nonempty(local_path)

    if first_time:
        print(f"\n🛡️ Primer uso detectado para '{group_conf['grupo']}' → realizando PULL inicial seguro.")
        sync_pull(group_conf, server_conf)
        # Después del pull inicial, hacemos push para normalizar (por si hay cambios locales mínimos)
        sync_push(group_conf, server_conf)
        write_group_meta(local_path, "run")
    else:
        # Flujo normal
        sync_push(group_conf, server_conf)
        sync_pull(group_conf, server_conf)
        write_group_meta(local_path, "run")

    print("✨ Sincronización completa (push + pull).")

# -----------------------------------------------------------------------------
# PURGE: limpia papeleras local y remota
# -----------------------------------------------------------------------------

def purge_group_trash(group_conf, server_conf):
    print(f"\n🧹 Limpiando papelera: {group_conf['grupo']}")
    local_trash = Path(group_conf["sync"]).expanduser() / "_papelera"
    if local_trash.exists():
        try:
            shutil.rmtree(local_trash)
            print(f"  ✔ Papelera local vaciada: {local_trash}")
        except Exception as e:
            print(f"  ⚠ No se pudo limpiar papelera local: {e}")
    local_trash.mkdir(parents=True, exist_ok=True)

    host = choose_reachable_host(server_conf)
    remote_trash = os.path.join(server_conf["remote"], group_conf["name_folder_backup"], "_papelera")
    passw = server_conf.get("passw", "")
    cmd = [
        "sshpass", "-p", passw,
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-p", str(server_conf["port"]),
        f"{server_conf['user']}@{host}",
        f"find {remote_trash} -mindepth 1 -exec rm -rf {{}} +"
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"  ✔ Papelera remota vaciada: {remote_trash}")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ No se pudo limpiar papelera remota: {e}")

def purge_all(config):
    for g in config.SINCRONIZAR:
        purge_group_trash(g, config.servers[g["server"]])
    print("\n✅ Papeleras limpiadas (local y remota).")

# -----------------------------------------------------------------------------
# TIME: ver último timestamp por grupo
# -----------------------------------------------------------------------------

def show_last_sync_times(config):
    print("\n🕒 Últimas sincronizaciones por grupo\n")
    rows = []
    for g in config.SINCRONIZAR:
        name = g.get("grupo", "(sin nombre)")
        lp = Path(g.get("sync", "")).expanduser()
        meta = read_group_meta(lp) or {}
        ts = meta.get("last_sync")
        act = meta.get("last_action", "-")
        host = meta.get("hostname", "-")
        user = meta.get("username", "-")
        if ts:
            ago = format_ago(ts)
            rows.append((name, ts, ago, act, user, host, str(lp)))
        else:
            rows.append((name, "-", "-", "-", "-", "-", str(lp)))

    # Pretty print
    if not rows:
        print("  (No hay grupos definidos en config)")
        return

    colw = [0]*7
    for r in rows:
        for i, val in enumerate(r):
            colw[i] = max(colw[i], len(val))

    headers = ("Grupo", "Último sync (ISO)", "Hace", "Acción", "Usuario", "Host", "Carpeta local")
    hrow = []
    for i, h in enumerate(headers):
        hrow.append(h.ljust(colw[i]))
    print("  " + "  |  ".join(hrow))
    print("  " + "-".join(["-"*(w+4) for w in colw]))

    for r in rows:
        line = "  " + "  |  ".join(val.ljust(colw[i]) for i, val in enumerate(r))
        print(line)
    print()

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="rsyncx - sincronizador seguro basado en rsync",
        add_help=True
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("configure", help="Instala dependencias y crea el archivo de configuración")

    p_push = sub.add_parser("push", help="Sube cambios (local -> remoto) con papelera versionada en remoto")
    p_push.add_argument("grupo", nargs="?", help="Nombre del grupo a sincronizar (opcional). Si se omite, todos.")

    p_pull = sub.add_parser("pull", help="Descarga cambios (remoto -> local) y sincroniza la papelera remota")
    p_pull.add_argument("grupo", nargs="?", help="Nombre del grupo a sincronizar (opcional). Si se omite, todos.")

    p_run = sub.add_parser("run", help="Ejecuta push y luego pull (primer uso hace pull inicial seguro)")
    p_run.add_argument("grupo", nargs="?", help="Nombre del grupo a sincronizar (opcional). Si se omite, todos.")

    sub.add_parser("purge", help="Limpia papelera local y remota de todos los grupos")
    sub.add_parser("time", help="Muestra último timestamp de sincronización por grupo")

    return parser

def print_usage_examples():
    print("""
Uso:
  rsyncx configure
  rsyncx push [grupo]
  rsyncx pull [grupo]
  rsyncx run  [grupo]
  rsyncx purge
  rsyncx time

Ejemplos:
  rsyncx configure
  rsyncx push                # sube todos los grupos
  rsyncx push nombreGrupo    # sube solo ese grupo
  rsyncx pull                # descarga todos los grupos (incluye papelera remota)
  rsyncx run                 # push + pull (primer uso: pull inicial)
  rsyncx purge               # limpia papeleras (local y remota)
  rsyncx time                # ver últimos timestamps de sync
""")

def main():
    # Si no hay argumentos, mostramos ayuda breve
    if len(sys.argv) == 1:
        print_header()
        print_usage_examples()
        return 0

    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command == "configure":
        configure()
        return 0

    # Para el resto de comandos necesitamos config cargada
    ensure_config_exists()
    config = load_config()

    # Resolver grupos
    if getattr(args, "grupo", None):
        grupos = [g for g in config.SINCRONIZAR if g["grupo"] == args.grupo]
        if not grupos:
            print(f"❌ Grupo '{args.grupo}' no encontrado en config.")
            return 1
    else:
        grupos = list(config.SINCRONIZAR)

    if args.command == "push":
        for g in grupos:
            server_conf = config.servers[g["server"]]
            # asegurar meta vacío si no existe
            ensure_group_meta_exists(Path(g["sync"]).expanduser())
            sync_push(g, server_conf)
        print("\n✔ push terminado.")
        return 0

    if args.command == "pull":
        for g in grupos:
            server_conf = config.servers[g["server"]]
            ensure_group_meta_exists(Path(g["sync"]).expanduser())
            sync_pull(g, server_conf)
        print("\n✔ pull terminado.")
        return 0

    if args.command == "run":
        for g in grupos:
            server_conf = config.servers[g["server"]]
            ensure_group_meta_exists(Path(g["sync"]).expanduser())
            sync_run(g, server_conf)
        print("\n✔ run terminado.")
        return 0

    if args.command == "purge":
        purge_all(config)
        return 0

    if args.command == "time":
        show_last_sync_times(config)
        return 0

    # Si cae aquí, mostramos ayuda
    print_usage_examples()
    return 0

if __name__ == "__main__":
    sys.exit(main())