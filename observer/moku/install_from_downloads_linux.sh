#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install --no-index --find-links packages moku==4.2.2.1
