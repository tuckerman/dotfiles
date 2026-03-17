#!/usr/bin/env bash
set -euo pipefail

cfg="${XDG_CONFIG_HOME:-$HOME/.config}/kglobalshortcutsrc"

# Ghostty: toggle quick terminal
kwriteconfig6 --file "$cfg" \
  --group "com.mitchellh.ghostty" \
  --key "LOGO+backslash" \
  $'Meta+\\\\,Meta+\\\\,toggle_quick_terminal'

# Ghostty: launch new window
kwriteconfig6 --file "$cfg" \
  --group "services" --group "com.mitchellh.ghostty.desktop" \
  --key "new-window" \
  $'Meta+T\tMeta+Return'

# 1Password: Quick Access
kwriteconfig6 --file "$cfg" \
  --group "services" --group "1password.desktop" \
  --key "QuickAccess" \
  "Ctrl+Shift+Space"

# Launch Google Chrome with Meta+Backspace.
kwriteconfig6 --file kglobalshortcutsrc \
  --group "services" --group "google-chrome.desktop" \
  --key "new-window" \
  "Meta+Backspace"

# Ask KDE to reread config if possible.
# If these fail harmlessly, log out/in or restart plasma/kglobalaccel.
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
qdbus6 org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel.reloadConfig >/dev/null 2>&1 || true
