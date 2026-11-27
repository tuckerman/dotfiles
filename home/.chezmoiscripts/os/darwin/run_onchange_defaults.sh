#!/usr/bin/env bash
set -euo pipefail

# Disable guest profile in Chrome.
defaults write com.google.Chrome BrowserGuestModeEnabled -bool false

# Show some extra info on the login screen (system-wide preference).
sudo defaults write /Library/Preferences/com.apple.loginwindow AdminHostInfo HostName

# Show ~/Library
chflags nohidden "$HOME/Library/"

# Don't create .DS_Store files on network drives/USB drives
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# Disable autocorrect / smart substitutions
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false

# Don't show all extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool false

# Don't show hidden files in Finder
defaults write com.apple.finder AppleShowAllFiles -bool false

# Screenshots
mkdir -p "$HOME/Pictures/Screenshots"
defaults write com.apple.screencapture location -string "$HOME/Pictures/Screenshots"
defaults write com.apple.screencapture type -string "jpg"

# Expand save and print panels by default
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true

# Default Finder to home directory
defaults write com.apple.finder NewWindowTarget -string "PfLo"
defaults write com.apple.finder NewWindowTargetPath -string "file://${HOME}/"

# TextEdit plain text by default
defaults write com.apple.TextEdit RichText -int 0

# Disable reopening windows on reboot
defaults write com.apple.loginwindow TALLogoutSavesState -bool false
defaults write com.apple.loginwindow LoginwindowLaunchesRelaunchApps -bool false
