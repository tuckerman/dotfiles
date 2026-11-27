# My Dotfiles

Managed with [chezmoi](https://chezmoi.io).

## Installation

### Linux / macOS

Ensure `git` is installed, then:

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply tuckerman --ssh
```

### Windows (PowerShell)

Install `git` and `chezmoi` (for example via `winget install Git.Git twpayne.chezmoi`), then:

```powershell
chezmoi init --apply tuckerman --ssh
```
