#!/bin/sh
set -eu
if [ -z "${ADMIN_PASSWORD:-}" ]; then echo 'ADMIN_PASSWORD doit être défini avant le démarrage.' >&2; exit 1; fi
exec python3 app.py
