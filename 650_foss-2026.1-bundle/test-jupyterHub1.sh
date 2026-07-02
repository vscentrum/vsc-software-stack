#!/usr/bin/env bash

set -euo pipefail

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "== JupyterHub CLI =="
command -v jupyterhub
jupyterhub --version
jupyterhub --help >/dev/null

echo
echo "== Configurable HTTP proxy =="
command -v configurable-http-proxy
configurable-http-proxy --version || configurable-http-proxy --help >/dev/null

echo
echo "== Python imports and package metadata =="
python -s <<'PY'
import importlib
import importlib.metadata as md

dists = [
    'jupyterhub',
    'certipy',
    'pamela',
    'oauthlib',
    'prometheus-client',
    'rfc3339-validator',
    'rfc3986-validator',
    'python-json-logger',
    'jupyter-events',
    'batchspawner',
    'jupyterhub-systemdspawner',
    'jupyterhub-simplespawner',
    'ldap3',
    'jupyterhub-ldapauthenticator',
    'PyJWT',
    'jupyterhub-jwtauthenticator-v2',
    'onetimepass',
    'jupyterhub-nativeauthenticator',
    'tornado',
    'SQLAlchemy',
    'pydantic',
]

modules = [
    'jupyterhub',
    'certipy',
    'pamela',
    'oauthlib',
    'prometheus_client',
    'rfc3339_validator',
    'rfc3986_validator',
    'pythonjsonlogger',
    'jupyter_events',
    'batchspawner',
    'systemdspawner',
    'simplespawner',
    'ldap3',
    'ldapauthenticator',
    'jwt',
    'jwtauthenticator',
    'onetimepass',
    'nativeauthenticator',
    'tornado',
    'sqlalchemy',
    'pydantic',
]

for name in modules:
    importlib.import_module(name)
    print(f"import OK: {name}")

print()
for name in dists:
    try:
        print(f"{name}: {md.version(name)}")
    except md.PackageNotFoundError:
        raise SystemExit(f"missing distribution metadata: {name}")

major = int(md.version('pydantic').split('.', 1)[0])
assert major >= 2, md.version('pydantic')

print()
print("metadata OK")
PY

echo
echo "== JupyterHub dependency-level imports =="
python -s <<'PY'
from jupyterhub.app import JupyterHub
from jupyterhub.auth import Authenticator, PAMAuthenticator
from jupyterhub.orm import User
from jupyterhub.proxy import ConfigurableHTTPProxy
from jupyterhub.spawner import Spawner

print("JupyterHub core classes OK")
print("Authenticator:", Authenticator.__name__)
print("PAMAuthenticator:", PAMAuthenticator.__name__)
print("Spawner:", Spawner.__name__)
print("Proxy:", ConfigurableHTTPProxy.__name__)
print("ORM user:", User.__name__)
PY

echo
echo "== Bundled spawners/authenticators =="
python -s <<'PY'
import importlib

checks = {
    'batchspawner': [
        'TorqueSpawner',
        'PBSSpawner',
        'SlurmSpawner',
    ],
    'systemdspawner': [
        'SystemdSpawner',
    ],
    'simplespawner': [
        'SimpleLocalProcessSpawner',
    ],
    'ldapauthenticator': [
        'LDAPAuthenticator',
    ],
    'nativeauthenticator': [
        'NativeAuthenticator',
    ],
    'jwtauthenticator.jwtauthenticator': [
        'JSONWebTokenAuthenticator',
        'JSONWebTokenLocalAuthenticator',
    ],
}

for modname, classes in checks.items():
    mod = importlib.import_module(modname)
    print(f"module OK: {modname}")
    for clsname in classes:
        cls = getattr(mod, clsname)
        print(f"class OK: {modname}.{cls.__name__}")
PY

echo
echo "== Generate default config =="
cd "$tmpdir"
jupyterhub --generate-config >/dev/null
test -s jupyterhub_config.py
grep -q "JupyterHub" jupyterhub_config.py
echo "generated config: $tmpdir/jupyterhub_config.py"

echo
echo "== Minimal startup smoke test =="
cat > "$tmpdir/jupyterhub_config.py" <<'PY'
c.JupyterHub.bind_url = 'http://127.0.0.1:8000'
c.JupyterHub.hub_ip = '127.0.0.1'
c.JupyterHub.cookie_secret_file = 'jupyterhub_cookie_secret'
c.JupyterHub.db_url = 'sqlite:///jupyterhub.sqlite'
c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.JupyterHub.spawner_class = 'simple'
c.Authenticator.allow_all = True
c.JupyterHub.log_level = 'INFO'
PY

jupyterhub -f "$tmpdir/jupyterhub_config.py" >"$tmpdir/jupyterhub.log" 2>&1 &
hub_pid=$!

for _ in $(seq 1 30); do
    if grep -q "JupyterHub is now running" "$tmpdir/jupyterhub.log"; then
        echo "JupyterHub startup OK"
        kill "$hub_pid"
        wait "$hub_pid" || true
        echo
        echo "== All JupyterHub smoke tests passed =="
        exit 0
    fi

    if ! kill -0 "$hub_pid" 2>/dev/null; then
        echo "JupyterHub exited unexpectedly"
        cat "$tmpdir/jupyterhub.log"
        exit 1
    fi

    sleep 1
done

echo "JupyterHub did not report successful startup"
cat "$tmpdir/jupyterhub.log"
kill "$hub_pid" 2>/dev/null || true
wait "$hub_pid" || true
exit 1