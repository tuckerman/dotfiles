#!/usr/bin/env bash
set -euo pipefail

REMOTE=${REMOTE:-flathub}

apps=(
  com.discordapp.Discord
  com.github.marhkb.Pods
  com.github.wwmm.easyeffects
  com.slack.Slack
  io.github.kolunmi.Bazaar
  io.missioncenter.MissionCenter
  io.podman_desktop.PodmanDesktop
  it.mijorus.gearlever
  md.obsidian.Obsidian
  org.fkoehler.KTailctl
  org.mitmproxy.mitmproxy
  org.signal.Signal
  org.telegram.desktop
)

flatpak install "$REMOTE" "${apps[@]}"
