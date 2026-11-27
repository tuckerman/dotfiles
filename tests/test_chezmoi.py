#!/usr/bin/env python3
"""Generic, low-maintenance validation suite for chezmoi dotfiles.

Checks structural invariants and core smoke assertions so adding, renaming,
or removing dotfiles/scripts rarely requires updating tests.
"""

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
CURRENT_OS = platform.system().lower()


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, env=env, text=True, capture_output=True)
    if result.returncode != 0:
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


def chezmoi_cmd(dest: Path, cfg: Path, state: Path, *args: str) -> list[str]:
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
        *args,
    ]


def init_chezmoi(dest: Path, cfg: Path, state: Path, *, profile: str, enable_onepassword: bool) -> dict:
    run(
        chezmoi_cmd(
            dest,
            cfg,
            state,
            "init",
            "--promptChoice",
            f"Choose your profile={profile}",
            "--promptString",
            "Email address=test@example.com",
            "--promptBool",
            f"Enable 1Password={'true' if enable_onepassword else 'false'}",
            "--promptDefaults",
        )
    )
    assert cfg.is_file(), f"chezmoi init did not create {cfg}"
    parsed = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert parsed["data"]["profile"] == profile
    assert parsed["data"]["email"] == "test@example.com"
    assert parsed["data"]["enable_onepassword"] is enable_onepassword
    assert parsed["data"]["default_shell"]
    assert parsed["age"]["identity"]
    assert parsed["age"]["recipient"]
    return parsed


def parse_powershell(ps_path: Path) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        return
    script = (
        "$tokens = $null; $errors = $null; "
        f"[void][System.Management.Automation.Language.Parser]::ParseFile('{ps_path}', [ref]$tokens, [ref]$errors); "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.ToString() }; exit 1 }"
    )
    run([pwsh, "-NoProfile", "-NonInteractive", "-Command", script])


def validate_applied_files(dest: Path, *, profile: str, enable_onepassword: bool) -> None:
    """Verify core bedrock files, toggle canaries, and generic syntax checks."""
    home_env = {**os.environ, "HOME": str(dest)}

    # Core cross-platform files that should always exist.
    for rel in [
        ".config/git/config",
        ".ssh/config",
        ".vim/vimrc",
        ".editorconfig",
        ".config/starship.toml",
    ]:
        assert (dest / rel).is_file(), f"Missing expected core file: {rel}"

    # OS-specific bedrock shell entrypoints.
    if CURRENT_OS == "windows":
        assert (dest / "Documents/PowerShell/Microsoft.PowerShell_profile.ps1").is_file()
        assert not (dest / ".zshenv").exists(), "Unix symlink .zshenv should not exist on Windows"
    else:
        zshenv = dest / ".zshenv"
        assert zshenv.is_symlink() and zshenv.is_file(), ".zshenv should be a valid symlink"
        assert (dest / ".config/zsh/.zshrc").is_file()

    # Conditional-ignore canaries (one per toggle).
    assert (dest / ".config/git/signing.gitconfig").is_file() is enable_onepassword
    assert (dest / ".ssh/config.d/personal").is_file() is (profile == "personal")

    # Generic syntax checks for all applied config files by type.
    for path in sorted(dest.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".toml":
            tomllib.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".ps1":
            parse_powershell(path)

    run(["git", "config", "--list", "--includes", "--file", str(dest / ".config/git/config")], env=home_env)
    if CURRENT_OS != "windows" and shutil.which("ssh"):
        run(["ssh", "-G", "-F", str(dest / ".ssh/config"), "github.com"], env=home_env)


def lint_managed_scripts(
    dest: Path,
    cfg: Path,
    state: Path,
    tmp: Path,
    *,
    override: dict | None = None,
    target_os: str = CURRENT_OS,
) -> None:
    extra = ["--override-data", json.dumps(override)] if override else []
    managed = run(chezmoi_cmd(dest, cfg, state, *extra, "managed", "--include", "scripts")).stdout
    scripts = [line.strip() for line in managed.splitlines() if line.strip()]
    assert scripts, f"Expected at least one managed script for target_os={target_os}"

    has_bash = shutil.which("bash") is not None
    has_shellcheck = shutil.which("shellcheck") is not None

    for rel_script in scripts:
        if target_os == "windows":
            assert not rel_script.endswith(".sh"), f"Unix shell script should be ignored on Windows: {rel_script}"

        rendered = run(chezmoi_cmd(dest, cfg, state, *extra, "cat", str(dest / rel_script))).stdout
        assert rendered.strip(), f"Script rendered empty: {rel_script}"

        script_file = tmp / Path(rel_script).name
        script_file.write_text(rendered, encoding="utf-8")

        if rel_script.endswith(".sh") and CURRENT_OS != "windows":
            assert rendered.startswith("#!"), f"Shell script missing shebang: {rel_script}"
            if has_bash:
                run(["bash", "-n", str(script_file)])
            if has_shellcheck:
                sc_cmd = ["shellcheck", "-s", "bash"]
                # Allow intentionally short-circuited scripts (`exit 0` at top).
                if "\nexit 0\n" in rendered:
                    sc_cmd += ["-e", "SC2317"]
                run(sc_cmd + [str(script_file)])
        elif rel_script.endswith(".ps1") and CURRENT_OS == "windows":
            parse_powershell(script_file)


def test_native_profiles() -> None:
    """Verify init, apply, verify, and syntax checks on the host OS across profiles."""
    for profile, enable_op in [("personal", True), ("personal", False), ("g", False)]:
        print(f"[{CURRENT_OS}] profile={profile}, enable_onepassword={enable_op}")
        tmp = Path(tempfile.mkdtemp(prefix="chezmoi-test-"))
        try:
            dest = tmp / "home"
            dest.mkdir()
            cfg = tmp / "chezmoi.toml"
            state = tmp / "state.boltdb"

            init_chezmoi(dest, cfg, state, profile=profile, enable_onepassword=enable_op)
            run(chezmoi_cmd(dest, cfg, state, "data"))
            run(chezmoi_cmd(dest, cfg, state, "apply", "--exclude", "scripts,externals"))
            run(chezmoi_cmd(dest, cfg, state, "verify", "--exclude", "scripts,externals"))

            validate_applied_files(dest, profile=profile, enable_onepassword=enable_op)
            lint_managed_scripts(dest, cfg, state, tmp)
        finally:
            rmtree_force(tmp)


def test_script_matrix() -> None:
    """On Linux with shellcheck, render and lint scripts across all OS/distro combinations."""
    if CURRENT_OS != "linux" or not shutil.which("shellcheck"):
        return

    matrix = [
        ("fedora-kde", "personal", True, {"os": "linux", "hostname": "thanatos", "osRelease": {"id": "fedora", "variantID": "kde"}}),
        ("rocky-otto", "otto", False, {"os": "linux", "hostname": "otto", "osRelease": {"id": "rocky"}}),
        ("debian", "container", False, {"os": "linux", "hostname": "devbox", "osRelease": {"id": "debian"}}),
        ("darwin", "personal", True, {"os": "darwin", "hostname": "macbook"}),
        ("windows", "personal", True, {"os": "windows", "hostname": "winbox"}),
    ]

    for name, profile, enable_op, chezmoi_override in matrix:
        print(f"[matrix] {name}")
        tmp = Path(tempfile.mkdtemp(prefix=f"chezmoi-matrix-{name}-"))
        try:
            dest = tmp / "home"
            dest.mkdir()
            cfg = tmp / "chezmoi.toml"
            state = tmp / "state.boltdb"

            init_chezmoi(dest, cfg, state, profile=profile, enable_onepassword=enable_op)
            lint_managed_scripts(
                dest,
                cfg,
                state,
                tmp,
                override={"chezmoi": chezmoi_override},
                target_os=chezmoi_override["os"],
            )
        finally:
            rmtree_force(tmp)


def main() -> int:
    test_native_profiles()
    test_script_matrix()
    print("All chezmoi checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
