#!/usr/bin/env python3
"""End-to-end validation suite for chezmoi dotfiles across Linux, macOS, and Windows."""

from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_OS = {
    "Linux": "linux",
    "Darwin": "darwin",
    "Windows": "windows",
}[platform.system()]


def run(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


def rmtree_force(path: Path) -> None:
    def on_error(func, p, _exc_info):
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
        func(p)

    if path.exists():
        shutil.rmtree(path, onerror=on_error)


def chezmoi_base_args(dest: Path, cfg: Path, state: Path) -> list[str]:
    return [
        "chezmoi",
        "--source",
        str(REPO_ROOT),
        "--destination",
        str(dest),
        "--config",
        str(cfg),
        "--persistent-state",
        str(state),
    ]


def init_chezmoi(
    dest: Path,
    cfg: Path,
    state: Path,
    *,
    profile: str,
    enable_onepassword: bool,
    email: str = "test@example.com",
) -> None:
    cmd = chezmoi_base_args(dest, cfg, state) + [
        "init",
        "--promptChoice",
        f"Choose your profile={profile}",
        "--promptString",
        f"Email address={email}",
        "--promptBool",
        f"Enable 1Password={'true' if enable_onepassword else 'false'}",
        "--promptDefaults",
    ]
    run(cmd)


def parse_powershell_file(ps_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    assert pwsh, "Neither pwsh nor powershell found in PATH"
    script = (
        "$tokens = $null; $errors = $null; "
        f"[void][System.Management.Automation.Language.Parser]::ParseFile('{ps_path}', [ref]$tokens, [ref]$errors); "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.ToString() }; exit 1 }"
    )
    run([pwsh, "-NoProfile", "-NonInteractive", "-Command", script])


def test_native_apply_scenarios() -> None:
    scenarios = [
        ("personal", True),
        ("personal", False),
        ("g", False),
    ]

    for profile, enable_op in scenarios:
        print(f"[native:{CURRENT_OS}] testing profile={profile}, enable_onepassword={enable_op}")
        tmp = Path(tempfile.mkdtemp(prefix="chezmoi-test-"))
        try:
            dest = tmp / "home"
            dest.mkdir()
            cfg = tmp / "chezmoi.toml"
            state = tmp / "state.boltdb"

            init_chezmoi(
                dest,
                cfg,
                state,
                profile=profile,
                enable_onepassword=enable_op,
            )

            # Verify generated chezmoi.toml is valid TOML (catches Windows backslash escaping bugs).
            parsed_cfg = tomllib.loads(cfg.read_text(encoding="utf-8"))
            assert parsed_cfg["data"]["profile"] == profile
            assert parsed_cfg["data"]["enable_onepassword"] is enable_op

            base = chezmoi_base_args(dest, cfg, state)

            # Verify packages.yaml and template data load cleanly.
            data_out = run(base + ["data"]).stdout
            data = json.loads(data_out)
            assert "packages" in data

            # Apply all files/dirs/symlinks (skipping system scripts and SSH externals).
            run(base + ["apply", "--exclude", "scripts,externals"])
            # Verify idempotency.
            run(base + ["verify", "--exclude", "scripts,externals"])

            # Validate git config parses cleanly.
            git_cfg = dest / ".config" / "git" / "config"
            assert git_cfg.is_file(), f"Missing {git_cfg}"
            git_env = {**os.environ, "HOME": str(dest)}
            git_list = run(
                ["git", "config", "--list", "--includes", "--file", str(git_cfg)],
                env=git_env,
            ).stdout
            assert "user.email=test@example.com" in git_list

            signing_cfg = dest / ".config" / "git" / "signing.gitconfig"
            if enable_op:
                assert signing_cfg.is_file(), "signing.gitconfig should exist when 1Password is enabled"
                assert "commit.gpgsign=true" in git_list
                if CURRENT_OS == "windows":
                    assert "op-ssh-sign.exe" in git_list
                    assert "core.sshcommand=C:/Windows/System32/OpenSSH/ssh.exe" in git_list
                elif CURRENT_OS == "darwin":
                    assert "/Applications/1Password.app/Contents/MacOS/op-ssh-sign" in git_list
                else:
                    assert "/opt/1Password/op-ssh-sign" in git_list
            else:
                assert not signing_cfg.exists(), "signing.gitconfig should be ignored when 1Password is disabled"
                assert "commit.gpgsign=true" not in git_list

            # Validate starship.toml is valid TOML.
            starship_cfg = dest / ".config" / "starship.toml"
            assert starship_cfg.is_file()
            starship_data = tomllib.loads(starship_cfg.read_text(encoding="utf-8"))
            assert starship_data["custom"]["ssh"]["os"] == "unix"
            assert starship_data["custom"]["direnv"]["os"] == "unix"

            # Validate 1Password agent.toml location & TOML syntax.
            unix_agent = dest / ".config" / "1Password" / "ssh" / "agent.toml"
            win_agent = dest / "AppData" / "Local" / "1Password" / "config" / "ssh" / "agent.toml"
            if CURRENT_OS == "windows":
                assert not unix_agent.exists()
                if enable_op:
                    assert win_agent.is_file()
                    tomllib.loads(win_agent.read_text(encoding="utf-8"))
                else:
                    assert not win_agent.exists()
            else:
                assert not win_agent.exists()
                if enable_op:
                    assert unix_agent.is_file()
                    tomllib.loads(unix_agent.read_text(encoding="utf-8"))
                else:
                    assert not unix_agent.exists()

            # Validate SSH config & profile filtering.
            ssh_cfg = dest / ".ssh" / "config"
            assert ssh_cfg.is_file()
            personal_ssh = dest / ".ssh" / "config.d" / "personal"
            if profile == "personal":
                assert personal_ssh.is_file()
                expected_null = "UserKnownHostsFile=NUL" if CURRENT_OS == "windows" else "UserKnownHostsFile=/dev/null"
                assert expected_null in personal_ssh.read_text(encoding="utf-8")
            else:
                assert not personal_ssh.exists()

            if CURRENT_OS != "windows" and shutil.which("ssh"):
                ssh_env = {**os.environ, "HOME": str(dest)}
                ssh_resolved = run(["ssh", "-G", "-F", str(ssh_cfg), "github.com"], env=ssh_env).stdout
                assert "hostname github.com" in ssh_resolved
                assert "user git" in ssh_resolved
                if enable_op:
                    assert "identityagent" in ssh_resolved

            # OS-specific file presence/absence assertions.
            chrome_desktop = dest / ".local" / "share" / "applications" / "google-chrome.desktop"
            steam_desktop = dest / ".local" / "share" / "applications" / "steam.desktop"
            karabiner = dest / ".config" / "karabiner" / "karabiner.json"
            ps_profile = dest / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
            zshenv = dest / ".zshenv"

            if CURRENT_OS == "linux":
                assert not karabiner.exists()
                assert not ps_profile.exists()
                assert steam_desktop.is_file()
                assert "/usr/bin/steam steam://open/friends" in steam_desktop.read_text(encoding="utf-8")
                if profile == "g":
                    assert not chrome_desktop.exists(), "google-chrome.desktop should be ignored for profile=g on Linux"
                else:
                    assert chrome_desktop.is_file()
            elif CURRENT_OS == "darwin":
                assert karabiner.is_file()
                assert not chrome_desktop.exists()
                assert not steam_desktop.exists()
                assert not ps_profile.exists()
                if enable_op:
                    op_ssh = (dest / ".ssh" / "config.d" / "onepassword").read_text(encoding="utf-8")
                    assert '"~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"' in op_ssh
            elif CURRENT_OS == "windows":
                assert not zshenv.exists(), ".zshenv symlink must be ignored on Windows"
                assert not karabiner.exists()
                assert not chrome_desktop.exists()
                assert not (dest / ".ssh" / "config.d" / "onepassword").exists()
                assert ps_profile.is_file()
                parse_powershell_file(ps_profile)

                # Also syntax-check the rendered Windows winget script.
                ps_script = tmp / "install_packages.ps1"
                rendered_ps = run(
                    base + ["cat", str(dest / ".chezmoiscripts" / "os" / "windows" / "00_install_packages.ps1")]
                ).stdout
                ps_script.write_text(rendered_ps, encoding="utf-8")
                parse_powershell_file(ps_script)
        finally:
            rmtree_force(tmp)


def test_simulated_matrix_and_shellcheck() -> None:
    """On Linux, simulate every OS/distro/profile combination and lint all rendered shell scripts."""
    if CURRENT_OS != "linux":
        return

    has_shellcheck = shutil.which("shellcheck") is not None
    print(f"[matrix] running cross-OS/distro script matrix (shellcheck={'yes' if has_shellcheck else 'no'})")

    matrix = [
        {
            "name": "fedora-kde-thanatos-personal",
            "profile": "personal",
            "enable_onepassword": True,
            "override": {
                "chezmoi": {
                    "os": "linux",
                    "hostname": "thanatos",
                    "osRelease": {"id": "fedora", "variantID": "kde"},
                }
            },
            "expected_scripts": {
                ".chezmoiscripts/host/thanatos/enable_fingerprint_reader.sh",
                ".chezmoiscripts/os/linux/fedora/00_install_packages.sh",
                ".chezmoiscripts/os/linux/fedora/configure_keyd.sh",
                ".chezmoiscripts/os/linux/install_ghostty_terminfo.sh",
                ".chezmoiscripts/os/linux/kde/set_kde_keyboard_shortcuts.sh",
                ".chezmoiscripts/os/linux/set_chezmoi_repo_to_use_ssh_transport.sh",
                ".chezmoiscripts/os/linux/set_default_shell.sh",
                ".chezmoiscripts/profile/personal/authorize_ssh_key.sh",
            },
        },
        {
            "name": "rocky-otto",
            "profile": "otto",
            "enable_onepassword": False,
            "override": {
                "chezmoi": {
                    "os": "linux",
                    "hostname": "otto",
                    "osRelease": {"id": "rocky"},
                }
            },
            "expected_scripts": {
                ".chezmoiscripts/os/linux/install_ghostty_terminfo.sh",
                ".chezmoiscripts/os/linux/rocky/00_install_packages.sh",
                ".chezmoiscripts/os/linux/rocky/install_starship.sh",
                ".chezmoiscripts/os/linux/set_chezmoi_repo_to_use_ssh_transport.sh",
                ".chezmoiscripts/os/linux/set_default_shell.sh",
                ".chezmoiscripts/profile/otto/authorize_ssh_key.sh",
                ".chezmoiscripts/profile/otto/install_obsidian.sh",
            },
        },
        {
            "name": "debian-container",
            "profile": "container",
            "enable_onepassword": False,
            "override": {
                "chezmoi": {
                    "os": "linux",
                    "hostname": "devbox",
                    "osRelease": {"id": "debian"},
                }
            },
            "expected_scripts": {
                ".chezmoiscripts/os/linux/install_ghostty_terminfo.sh",
                ".chezmoiscripts/os/linux/set_chezmoi_repo_to_use_ssh_transport.sh",
                ".chezmoiscripts/os/linux/set_default_shell.sh",
            },
        },
        {
            "name": "darwin-personal",
            "profile": "personal",
            "enable_onepassword": True,
            "override": {
                "chezmoi": {
                    "os": "darwin",
                    "hostname": "macbook",
                }
            },
            "expected_scripts": {
                ".chezmoiscripts/os/darwin/accept_xcode_license.sh",
                ".chezmoiscripts/os/darwin/defaults.sh",
                ".chezmoiscripts/profile/personal/authorize_ssh_key.sh",
            },
        },
        {
            "name": "windows-personal",
            "profile": "personal",
            "enable_onepassword": True,
            "override": {
                "chezmoi": {
                    "os": "windows",
                    "hostname": "winbox",
                }
            },
            "expected_scripts": {
                ".chezmoiscripts/os/windows/00_install_packages.ps1",
            },
        },
    ]

    for case in matrix:
        print(f"  [matrix] {case['name']}")
        tmp = Path(tempfile.mkdtemp(prefix=f"chezmoi-matrix-{case['name']}-"))
        try:
            dest = tmp / "home"
            dest.mkdir()
            cfg = tmp / "chezmoi.toml"
            state = tmp / "state.boltdb"

            init_chezmoi(
                dest,
                cfg,
                state,
                profile=case["profile"],
                enable_onepassword=case["enable_onepassword"],
            )

            base = chezmoi_base_args(dest, cfg, state) + [
                "--override-data",
                json.dumps(case["override"]),
            ]

            managed_out = run(base + ["managed", "--include", "scripts"]).stdout
            scripts = {line.strip() for line in managed_out.splitlines() if line.strip()}
            assert scripts == case["expected_scripts"], (
                f"[{case['name']}] managed scripts mismatch:\n"
                f"  expected: {sorted(case['expected_scripts'])}\n"
                f"  actual:   {sorted(scripts)}"
            )

            for rel_script in sorted(scripts):
                rendered = run(base + ["cat", str(dest / rel_script)]).stdout
                assert rendered.strip(), f"[{case['name']}] {rel_script} rendered empty"

                if rel_script.endswith(".sh"):
                    assert rendered.startswith("#!"), f"[{case['name']}] {rel_script} is missing a shebang"
                    script_file = tmp / Path(rel_script).name
                    script_file.write_text(rendered, encoding="utf-8")
                    run(["bash", "-n", str(script_file)])
                    if has_shellcheck:
                        # Skip unreachable-code SC2317 only for the intentionally short-circuited fingerprint script.
                        sc_cmd = ["shellcheck", "-s", "bash"]
                        if rel_script.endswith("enable_fingerprint_reader.sh"):
                            sc_cmd += ["-e", "SC2317"]
                        sc_cmd.append(str(script_file))
                        run(sc_cmd)
        finally:
            rmtree_force(tmp)


def main() -> int:
    test_native_apply_scenarios()
    test_simulated_matrix_and_shellcheck()
    print("All chezmoi checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
