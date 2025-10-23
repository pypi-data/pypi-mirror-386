from pathlib import Path
from types import ModuleType
from typing import Literal
import os
import subprocess

from rich.console import Console

from . import _base
from .helpers.infra import system


console = Console()


class Brew(_base.BaseInstaller):
    def __init__(self):
        super().__init__()
        self.name: str = Path(__file__).stem
        self.description: str = "Brew Installer"
        self.version: str = "1.0.0"
        self.platforms: list = ["debian"]
        self.helper: ModuleType | None = None

    def install(
            self,
            force: bool = False
    ):
        return install_brew()

    def _show_help(
            self,
            method: Literal["install", "uninstall", "update"]
    ) -> None:
        if method == "install":
            method_help: str = (
                "This method installs brew and its prerequisites from apt repositories\n"
            )
            print(method_help)
        else:
            raise ValueError(f"Unknown method '{method}'.")


def import_brew_env():
    # Start a bash, eval brew’s shellenv, then print the full env as NUL-separated
    out = subprocess.check_output(
        ['bash','-lc','eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"; env -0']
    )
    for entry in out.split(b'\x00'):
        if not entry:
            continue
        k, _, v = entry.partition(b'=')
        os.environ[k.decode()] = v.decode()


def install_brew():
    script_lines = [
        """

sudo apt update
sudo apt install curl git build-essential -y

# Install Homebrew (if you don't have it)
NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"


# Add brew to PATH for this shell (and put it in your shell rc later)
# choose the right rc file, nounset-safe
if [ -n "${ZSH_VERSION-}" ]; then
  RC="$HOME/.zshrc"
elif [ -n "${BASH_VERSION-}" ]; then
  RC="$HOME/.bashrc"
else
  case "${SHELL-}" in
    */zsh)  RC="$HOME/.zshrc"  ;;
    */bash) RC="$HOME/.bashrc" ;;
    *)      RC="$HOME/.profile";;
  esac
fi

LINE='eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"'

# append once (idempotent)
grep -qxF "$LINE" "$RC" 2>/dev/null || printf '\n%s\n' "$LINE" >> "$RC"

# apply to current shell
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"


# Install dependencies
brew install gcc
"""]

    system.execute_bash_script_string(script_lines)
    import_brew_env()

    return 0