#!/usr/bin/env bash
set -euo pipefail

exit 0

copr_repo='copr:copr.fedorainfracloud.org:cwt:libfprint-cs9711'

if ! dnf -C repolist enabled | grep -Fq "$copr_repo"; then
  sudo dnf -y copr enable cwt/libfprint-cs9711
fi

sudo dnf -y install libfprint-cs9711 --allowerasing