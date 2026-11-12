#!/bin/bash
# Self-contained flagchecker solve, runs ENTIRELY inside the VM (Docker only).
# Builds the challenge container (pinning the author's validators version so the
# input validation works), serves it single-worker for clean timing, runs the
# timing-attack solver, prints the recovered flag, and validates it against the
# container's own FLAG env. Cleans up after itself.
#
# Usage (in the VM):
#   bash run_flagchecker_in_vm.sh /path/to/challenge-repo/2026/CSAW-Quals/web/flagchecker
set -e
CHAL="${1:-$HOME/challenge-repo/2026/CSAW-Quals/web/flagchecker}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT=5055

echo "[*] challenge dir: $CHAL"
WORK="$(mktemp -d)"
cp -R "$CHAL"/. "$WORK"/
cd "$WORK"
# Pin the author's validators API (min=/max=), which newer pip versions broke.
sed -i 's/^validators$/validators==0.20.0/' requirements.txt

echo "[*] building image..."
docker build -q -t flagchecker_vm . >/dev/null

echo "[*] starting single-worker service on :$PORT ..."
docker rm -f flagchecker_vm_run >/dev/null 2>&1 || true
docker run -d --name flagchecker_vm_run -p ${PORT}:5000 flagchecker_vm \
    gunicorn -w 1 -k sync -b 0.0.0.0:5000 app:app >/dev/null
sleep 6

echo "[*] running timing attack (this takes a few minutes)..."
FLAG=$(python3 "$HERE/solve_flagchecker.py" "http://localhost:${PORT}/check" | tee /dev/stderr | awk '/FLAG:/{print $3}')

echo
echo "[*] recovered: $FLAG"
REAL=$(docker exec flagchecker_vm_run sh -c 'grep -o "csaw{[^}]*}" .env' 2>/dev/null || true)
if [ -n "$FLAG" ] && [ "$FLAG" = "$REAL" ]; then
    echo "[✓] VALIDATED: matches the service's own flag."
else
    echo "[!] recovered=$FLAG  service-env=$REAL  (re-run if they differ; timing can need more samples)"
fi

docker rm -f flagchecker_vm_run >/dev/null 2>&1 || true
rm -rf "$WORK"
