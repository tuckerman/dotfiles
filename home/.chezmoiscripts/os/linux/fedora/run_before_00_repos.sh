#!/bin/bash

# RPM Fusion
if ! rpm -q rpmfusion-free-release; then
  sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
fi

if ! rpm -q rpmfusion-nonfree-release; then
  sudo dnf install -y https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
fi

# Google Chrome
if ! rpm -q google-chrome-stable; then
  sudo dnf install -y https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
fi

if ! rpm -q google-chrome-canary; then
  sudo dnf install -y https://dl.google.com/linux/direct/google-chrome-canary_current_x86_64.rpm
fi

# Tailscale
if [ ! -f /etc/yum.repos.d/tailscale.repo ]; then
  sudo dnf config-manager addrepo --from-repofile=https://pkgs.tailscale.com/stable/fedora/tailscale.repo
fi

# Terra
if [ ! -f /etc/yum.repos.d/terra.repo ]; then
  sudo dnf install --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release
fi

# 1Password
if [ ! -f /etc/yum.repos.d/1password.repo ]; then
  sudo rpm --import https://downloads.1password.com/linux/keys/1password.asc
  sudo sh -c 'echo -e "[1password]\nname=1Password Stable Channel\nbaseurl=https://downloads.1password.com/linux/rpm/stable/\$basearch\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=\"https://downloads.1password.com/linux/keys/1password.asc\"" > /etc/yum.repos.d/1password.repo'
fi

# Google Cloud SDK
if [ ! -f /etc/yum.repos.d/google-cloud-sdk.repo ]; then
  sudo tee -a /etc/yum.repos.d/google-cloud-sdk.repo << EOM
[google-cloud-cli]
name=Google Cloud CLI
baseurl=https://packages.cloud.google.com/yum/repos/cloud-sdk-el10-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=0
gpgkey=https://packages.cloud.google.com/yum/doc/rpm-package-key-v10.gpg
EOM
fi

sudo dnf config-manager setopt \
  rpmfusion-free.enabled=1 \
  rpmfusion-nonfree.enabled=1 \
  rpmfusion-free-updates.enabled=1 \
  rpmfusion-nonfree-updates.enabled=1 \
  rpmfusion-nonfree-nvidia-driver.enabled=1 \
  rpmfusion-nonfree-steam.enabled=1 \
  fedora-cisco-openh264.enabled=1
