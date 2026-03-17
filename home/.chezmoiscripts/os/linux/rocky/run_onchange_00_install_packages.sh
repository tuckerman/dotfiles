#!/usr/bin/env bash
# Version: 2026031701

set -euo pipefail

{{- if .packages.linux.rocky.repos.setopt }}
sudo dnf config-manager setopt \
{{- range .packages.linux.rocky.repos.setopt }}
  {{ . | quote }} \
{{- end }}
;
{{- end }}

# install repo/bootstrap RPMs if their package is missing
{{- range .packages.linux.rocky.repos.rpms }}
if ! rpm -q {{ .package | quote }} >/dev/null 2>&1; then
  sudo dnf install -y {{ .url }}
fi
{{- end }}

# add repos from repofiles if the target .repo file is absent
{{- range .packages.linux.rocky.repos.addrepo }}
if [ ! -f {{ .path | quote }} ]; then
  sudo dnf config-manager addrepo --from-repofile={{ .repofile }}
fi
{{- end }}

# write .repo files if absent
{{- range .packages.linux.rocky.repos.files }}
if [ ! -f {{ .path | quote }} ]; then
  {{- $keyImport := get . "key_import" }}
  {{- if $keyImport }}
    sudo rpm --import {{ $keyImport | quote }}
  {{- end }}
  sudo tee {{ .path | quote }} >/dev/null <<'EOF'
{{ .content }}
EOF
fi
{{- end }}

groups=(
  {{ range .packages.linux.rocky.dnf_groups -}}
  {{ . }}
  {{ end -}}
)

if ((${#groups[@]})); then
  sudo dnf group install -y "${groups[@]}"
fi

packages=(
  {{ range .packages.linux.rocky.dnf_packages -}}
  {{ . }}
  {{ end -}}
)

if ((${#packages[@]})); then
  sudo dnf install -y "${packages[@]}"
fi

apps=(
  {{ range .packages.linux.rocky.flatpak -}}
  {{ . }}
  {{ end -}}
)

if ((${#apps[@]})); then
  flatpak install flathub "${apps[@]}"
fi
