#!/usr/bin/env bash
# Run this inside a Jubail Desktop terminal (NYUAD HPC, Open OnDemand) to check
# whether it can host this CTF work without Docker/root. Answers everything in
# one shot -- paste the whole thing, read the SUMMARY at the end.
echo "================ JUBAIL CAPABILITY CHECK ================"

echo; echo "--- outbound internet (HTTPS to github.com) ---"
curl -sS -m 8 -o /dev/null -w "HTTP %{http_code}\n" https://github.com && NET_OK=1 || NET_OK=0

echo; echo "--- sudo / root ---"
sudo -n true 2>/dev/null && { echo "have passwordless sudo"; SUDO_OK=1; } || { echo "no sudo (expected on HPC)"; SUDO_OK=0; }

echo; echo "--- docker ---"
command -v docker >/dev/null 2>&1 && { docker info >/dev/null 2>&1 && echo "docker daemon reachable" || echo "docker CLI present but daemon not reachable (needs root, as expected)"; DOCKER_OK=$(docker info >/dev/null 2>&1 && echo 1 || echo 0); } || { echo "no docker"; DOCKER_OK=0; }

echo; echo "--- apptainer / singularity (rootless container runtime HPC usually ships instead) ---"
module avail apptainer singularity 2>&1 | grep -iE "apptainer|singularity" || echo "nothing via module avail"
command -v apptainer >/dev/null 2>&1 && echo "apptainer: $(apptainer --version)"
command -v singularity >/dev/null 2>&1 && echo "singularity: $(singularity --version)"

echo; echo "--- toolchain: python3 / node / gcc / gdb / php ---"
for c in python3 node npm gcc g++ gdb php; do
  if command -v "$c" >/dev/null 2>&1; then
    echo "$c: $($c --version 2>&1 | head -1)"
  else
    echo "$c: MISSING -- checking module avail..."
    module avail "$c" 2>&1 | grep -i "$c" | head -3
  fi
done

echo; echo "--- can we install user-space npm global packages without sudo? ---"
npm config get prefix 2>/dev/null
mkdir -p "$HOME/.npm-global" && npm config set prefix "$HOME/.npm-global" 2>/dev/null && echo "npm prefix set OK (no sudo needed for global installs)"

echo; echo "--- walltime: how long was this session requested for? ---"
echo "(check the OnDemand 'My Interactive Sessions' page -- 'Number of hours' you picked)"

echo; echo "================ SUMMARY ================"
echo "Internet egress:  $([ "$NET_OK" = 1 ] && echo OK || echo BLOCKED -- dealbreaker, nothing here works without this)"
echo "Docker:            $([ "${DOCKER_OK:-0}" = 1 ] && echo WORKS || echo "no (expected, fine -- almost nothing here actually needs it)")"
echo "Everything else above just needs python3/node/gcc/gdb/php to be present"
echo "(via module load if not already on PATH) -- re-run with 'module load <name>'"
echo "for anything marked MISSING, then re-check that one line."
