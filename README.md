# My Dotfiles

Managed with [chezmoi](https://chezmoi.io).

Installation:

Ensure git is installed, then:

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply tuckerman --ssh
```

### Fedora and Rocky Linux

Run the system playbook before applying chezmoi on a fresh machine. From the
repository root, with Ansible installed:

```bash
ansible-playbook -i localhost, ansible/linux.yml --ask-become-pass
chezmoi init --apply --source "$PWD"
```

The playbook reads the repository definitions, package groups, and packages from
`home/.chezmoidata/packages.yaml`. It configures Fedora's keyd service using
`etc/keyd/`. Chezmoi manages home-directory configuration and Fedora's user
Flatpaks. Re-run the playbook after editing the system inventory or to restore
managed system settings. Package management is additive.

For a Fedora x86_64 gaming host such as `moros`, pass the features you want on
each run. Either feature can be used independently.

```bash
ansible-playbook -i localhost, ansible/linux.yml --ask-become-pass \
  -e '{"gaming": true, "nvidia": true}'
```

The NVIDIA option installs RPM Fusion's akmod and driver packages. Secure Boot
key enrollment, when needed, is a separate step.
