#!/usr/bin/env bash
set -euo pipefail

if command -v xcodebuild >/dev/null 2>&1; then
  sudo xcodebuild -license accept
fi