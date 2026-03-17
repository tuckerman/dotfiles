#!/usr/bin/env bash
set -euo pipefail

groups=(
  development-tools
)

packages=(
  1password
  android-tools
  btrfs-assistant
  code
  ghostty
  google-chrome-canary
  google-chrome-stable
  google-cloud-cli
  mediawriter
  tailscale
  chezmoi
  fastfetch
  gcc-c++
  git
  keyd
  koji
  mise
  mock
  ninja-build
  nodejs
  podman-compose
  podman-docker
  podman-sequoia
  uv
  vim
  starship
  zsh
)

if ((${#groups[@]})); then
  sudo dnf group install -y "${groups[@]}"
fi

if ((${#packages[@]})); then
  sudo dnf install -y "${packages[@]}"
fi
