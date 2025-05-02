# Cameron's Dotfiles

My dotfiles, managed with [chezmoi](https://chezmoi.io).

Installation:

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply tuckerman --ssh
```

You might need to install `git` first.

To install on an ephemeral machine:

```bash
EPHEMERAL=1 sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply tuckerman --ssh
```

You can also set `INSTALL_TEX=1`, `ENABLE_TAILSCALE=1`, or `DISABLE_TAILSCALE=1`.
