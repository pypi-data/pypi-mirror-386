import tempfile
import subprocess
import ctypes
import json
import os
from pathlib import Path
import shutil
import sys
import time
import urllib.request

from rich.console import Console

from atomicshop.wrappers import githubw

from ..infra import registrys


console = Console()


SCRIPT_NAME: str = "TesseractOCR Manager"
AUTHOR: str = "Denis Kras"
VERSION: str = "1.1.0"
RELEASE_COMMENT: str = "Added languages and configs download options."


# Constants for GitHub wrapper.
RELEASE_STRING_PATTERN: str = "*tesseract*exe"

# Constants for Tesseract installation on Windows.
WINDOWS_TESSERACT_DEFAULT_INSTALLATION_DIRECTORY: str = r"C:\Program Files\Tesseract-OCR"


# Constants for vcpkg and Tesseract compilation.
VCPKG_DIR: Path = Path.home() / "vcpkg"
TRIPLET: str = "x64-windows"  # or "x64-windows-static"
PORT: str = f"tesseract[training-tools]:{TRIPLET}"
DEPENDENCIES = [
    f'curl[ssl,sspi,http2,idn2,psl,ssh,brotli,zstd]:{TRIPLET}',
    f'libarchive[bzip2,lz4,lzma,zstd,crypto]:{TRIPLET}',
    PORT,  # tesseract[training-tools]:<triplet>
]

VSWHERE_EXE: Path = Path(
    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
TESSERACT_VCPKG_TOOLS_DIR: Path = VCPKG_DIR / "installed" / TRIPLET / "tools" / "tesseract"
TESSERACT_VCPKG_TOOLS_EXE: Path = TESSERACT_VCPKG_TOOLS_DIR / 'tesseract.exe'
TESSDATA_DIR: Path = TESSERACT_VCPKG_TOOLS_DIR / "tessdata"


TESSERACT_GITHUB_WRAPPER: githubw.GitHubWrapper = githubw.GitHubWrapper(
    user_name="tesseract-ocr",
    repo_name="tesseract",
    branch="main"
)

TESSERACT_TESSCONFIGS_GITHUB_WRAPPER: githubw.GitHubWrapper = githubw.GitHubWrapper(
    user_name="tesseract-ocr",
    repo_name="tessconfigs",
    branch="main"
)
TESSERACT_TESSDATA_FAST_GITHUB_WRAPPER: githubw.GitHubWrapper = githubw.GitHubWrapper(
    user_name="tesseract-ocr",
    repo_name="tessdata_fast",
    branch="main"
)
TESSERACT_TESSDATA_BEST_GITHUB_WRAPPER: githubw.GitHubWrapper = githubw.GitHubWrapper(
    user_name="tesseract-ocr",
    repo_name="tessdata_best",
    branch="main"
)



def get_latest_installer_version() -> str:
    """
    Get the latest Tesseract OCR installer version from GitHub.
    This function fetches the latest release information from the Tesseract OCR GitHub repository.
    It returns the version number of the latest installer available.
    """

    latest_release: str = TESSERACT_GITHUB_WRAPPER.get_latest_release_version(
        asset_pattern=RELEASE_STRING_PATTERN,
    )

    return latest_release


def use_installer(
        set_path: bool = False
) -> None:
    """
    Install Tesseract OCR on Windows.
    This function downloads the latest available Tesseract installer from GitHub and installs it.
    It also adds the Tesseract installation directory to the system PATH.
    The latest installer maybe lower than the latest available version, so if you need the latest you will need
    to use the compiler version.

    :param set_path: If True, adds the Tesseract installation directory to the system PATH.
    """

    temp_file_path: str = tempfile.gettempdir()
    tesseract_installer = TESSERACT_GITHUB_WRAPPER.download_latest_release(
        target_directory=temp_file_path,
        asset_pattern=RELEASE_STRING_PATTERN,
        find_latest_available_asset=True
    )

    # The Admin needed to install Tesseract.
    subprocess.check_call([tesseract_installer, "/S"])

    # Add Tesseract to the PATH.
    if set_path:
        registrys.ensure_exe_dir_in_path(f'{TESSERACT_VCPKG_TOOLS_DIR}{os.sep}tesseract.exe')
        registrys.set_environment_variable('TESSDATA_PREFIX', WINDOWS_TESSERACT_DEFAULT_INSTALLATION_DIRECTORY + os.sep + 'tessdata')



def get_latest_compiled_version() -> str:
    """
    Get the latest compiled version of Tesseract OCR.
    This function fetches the latest release information from the Tesseract OCR GitHub repository
    and returns the version number of the latest compiled release.
    """

    latest_release: str = TESSERACT_GITHUB_WRAPPER.get_latest_release_version()
    return latest_release


def compile_exe(
        set_path: bool = False
) -> int:
    """
    Compile the ltest Tesseract version from source.
    """

    def run(cmd, *, ok=(0,), **kw):
        print(f"[+] {cmd}")
        process_instance = subprocess.run(cmd, shell=True, **kw)
        if process_instance.returncode not in ok:
            raise subprocess.CalledProcessError(process_instance.returncode, cmd)

    def is_admin():
        # noinspection PyUnresolvedReferences
        return bool(ctypes.windll.shell32.IsUserAnAdmin())

    def have(exe):
        return shutil.which(exe) is not None

    def have_msvc():
        if not VSWHERE_EXE.exists():
            return False

        try:
            out = subprocess.check_output(
                f'"{VSWHERE_EXE}" -latest -products Microsoft.VisualStudio.Product.BuildTools -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json',
                shell=True, text=True)
            return bool(json.loads(out))
        except subprocess.CalledProcessError:
            return False

    def install_build_tools() -> int:
        if have_msvc():
            return 0

        print("Installing Visual Studio 2022 Build Tools + C++ workload …")
        url = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
        with tempfile.TemporaryDirectory() as td:
            exe = Path(td) / "vs_BuildTools.exe"
            urllib.request.urlretrieve(url, exe)
            run(
                f'"{exe}" --passive --wait --norestart '
                '--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended',
                ok=(0, 3010, 1641))
        print("Waiting for Build Tools to register …")
        for _ in range(60):
            if have_msvc():
                return 0
            time.sleep(5)

        console.print("Timed out waiting for Build Tools to register.", style="red")
        return 1

    if os.name != "nt":
        console.print("This script is for Windows only.", style="red")
        return 1
    if not is_admin():
        console.print("This script requires administrative privileges to run.", style="red")
        return 1

    execution_result: int = install_build_tools()
    if execution_result != 0:
        return execution_result

    if not have("git"):
        console.print("Git is not installed. Please install Git for Windows.", style="red")
        return 1

    if not VCPKG_DIR.exists():
        run(f'git clone https://github.com/microsoft/vcpkg "{VCPKG_DIR}"')
    else:
        console.print(f"vcpkg exists in [{VCPKG_DIR}]. Updating...", style="blue")
        run(f'git -C "{VCPKG_DIR}" pull')
    run(f'"{VCPKG_DIR / "bootstrap-vcpkg.bat"}"')

    vcpkg = VCPKG_DIR / "vcpkg.exe"
    console.print(f"Creating {PORT} port in vcpkg...", style="blue")
    # run(f'"{vcpkg}" install {PORT} --disable-metrics')        # minimal, no dependencies.
    run(f'"{vcpkg}" install ' + ' '.join(DEPENDENCIES) + ' --disable-metrics --recurse')
    run(f'"{vcpkg}" integrate install --disable-metrics')

    os.makedirs(TESSDATA_DIR, exist_ok=True)

    if set_path:
        registrys.ensure_exe_dir_in_path(f'{TESSERACT_VCPKG_TOOLS_DIR}{os.sep}tesseract.exe')
        registrys.set_environment_variable('TESSDATA_PREFIX', str(TESSDATA_DIR))

    console.print("\nDone. Open a NEW CMD terminal and run [tesseract --version] to verify the installation.", style="green", markup=False)
    return 0


def get_environment_path() -> str | None:
    """
    Check if Tesseract is set in the environment variables.
    This function checks if the Tesseract command is available in the system PATH.
    Returns the path of tesseract if exists, otherwise None.
    """
    return shutil.which("tesseract")


def get_executable_version(exe_path: str) -> str:
    """
    Get the version of the Tesseract executable.
    This function runs the Tesseract command with the `--version` flag and returns the version string.
    If the executable is not found, it returns an empty string.
    """
    try:
        result = subprocess.run([exe_path, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            string_result = result.stdout.strip()
            full_version: str = string_result.split('\n')[0]  # Get the first line which contains the version.
            numeric_string: str = full_version.split(' ')[-1]  # Get the last part which is the version number.
            return numeric_string
        else:
            return ""
    except FileNotFoundError:
        return ""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Install Tesseract OCR on Windows.")
    parser.add_argument(
        "-i", "--installer-usage", action="store_true",
        help="Use the latest Tesseract installer from GitHub Releases.")
    parser.add_argument(
        "-c", "--compile-portable", action="store_true",
        help="Compile the latest Tesseract version from source in GitHub Releases. "
             "This could take a while, an hour or more, depending on your system."
             "This installs Visual Studio Build Tools and all the tesseract dependencies.")
    parser.add_argument(
        "-iv", "--installer-version-string-fetch", action="store_true",
        help="Fetch the latest Tesseract installer version string from GitHub Releases.")
    parser.add_argument(
        "-cv", "--compile-version-string-fetch", action="store_true",
        help="Fetch the latest Tesseract compiled version string from GitHub Releases.")
    parser.add_argument(
        "--get-path", action="store_true",
        help="Return the path of [tesseract] command from the PATH.")
    parser.add_argument(
        "--set-path", action="store_true",
        help="set the path of [tesseract] command to the PATH, based on any of the installation methods.\n"
             "Use it with [--exe-path] to set the path to a custom Tesseract executable.\n"
             "TESSDATA_PREFIX will also be set automatically to the [tessdata] folder near the executable.")
    parser.add_argument(
        "-f", "--force", action="store_true",
        help="Force any action without asking.")
    parser.add_argument(
        "--exe-path", type=str, default=None,
        help="Path to the Tesseract executable if you want to set it manually. If you set any of the above installation methods, the version will checked against the latest available version in GitHub Releases, and you will be asked if you want to update it.")

    parser.add_argument(
        "-l", "--languages",
        choices=["b", "f", "bs", "fs"],
        metavar="{b,f,bs,fs}",
        help=("Select the tessdata set: "
              "b=best trained models, \n"
              "f=fast (int) models, \n"
              "bs=scripts of best models, \n"
              "fs=scripts of fast models.")
    )

    # list vs download are mutually exclusive
    lang_group = parser.add_mutually_exclusive_group()
    lang_group.add_argument(
        "-ls", "--list",
        dest="lang_list",
        action="store_true",
        help="With -l/--languages, list available files that can be downloaded from the selected tessdata language set."
    )
    lang_group.add_argument(
        "-d", "--download",
        dest="lang_download",
        type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
        metavar="CODES",
        help=("With -l/--languages (and not --list), comma-separated language/script codes to download "
              "from the selected tessdata language set. Example: -l bs -d eng,fin\n"
              "ALL - will download all the files in the category. Example: -l fs -d ALL\n"
              "The codes can be found with the --list option.\n"
              "The languages will be downloaded to the tessdata folder from the ENV TESSDATA_PREFIX.")
    )

    parser.add_argument(
        "-dc", "--download-configs", action="store_true",
        help="Download 'configs' and 'tessconfigs' from the 'tessconfigs' repo to ENV TESSDATA_PREFIX folder.")

    return parser


def main(
        installer_usage: bool = False,
        compile_portable: bool = False,
        installer_version_string_fetch: bool = False,
        compile_version_string_fetch: bool = False,
        get_path: bool = False,
        set_path: bool = False,
        force: bool = False,
        exe_path: str = None,
        languages: str = None,
        lang_list: bool = False,
        lang_download: list[str] = None,
        download_configs: bool = False
) -> int:

    if (installer_version_string_fetch + compile_version_string_fetch + get_path) > 1:
        print("You cannot more than 1 argument of [--installer-version-string-fetch], [--compile-version-string-fetch], [--get-path] arguments at the same time.")
        return 1

    if (lang_list or lang_download) and languages is None:
        print("You need to provide the [--languages] argument when using [--list] or [--download] arguments.")
        return 1

    if lang_list and lang_download:
        print("You cannot use both [--list] and [--download] arguments at the same time.")
        return 1

    if lang_download is not None and len(lang_download) == 0:
        print("You need to provide at least one language/script code to download when using the [--download] argument.")
        return 1

    if installer_version_string_fetch or compile_version_string_fetch or get_path:
        result: str = ""
        selected_argument: str = ""
        if installer_version_string_fetch:
            result = get_latest_installer_version()
            selected_argument = 'installer_version_string_fetch'
        if compile_version_string_fetch:
            result = get_latest_compiled_version()
            selected_argument = 'compile_version_string_fetch'
        if get_path:
            result = get_environment_path()
            selected_argument = 'get_path'

        print(result)

        if any([installer_usage, compile_portable, set_path]):
            print(f"You need to remove the [--{selected_argument}] argument, to use other arguments...")

        return 0

    if compile_portable and installer_usage:
        print("You cannot use both [--installer_usage] and [--compile_portable] arguments at the same time.")
        return 1

    current_environment_path: str = get_environment_path()

    if exe_path:
        # If 'current_environment_path' is set and not None, and 'set_path' is True to change the PATH to provided 'exe_path' and
        # the provided 'exe_path' is different from the current one, ask the user if they want to change it.
        if current_environment_path and set_path and current_environment_path.lower() != exe_path.lower() and not force:
            print(f"Current System Environment PATH Tesseract executable path: {current_environment_path}\n"
                  f"Do you want to update it with provided executable path?: {exe_path}\n"
                  f"(y/n)")
            if input().strip().lower() != 'y':
                print("Exiting without updating the path.")
                return 0

        executable_parent_path: str = os.path.dirname(exe_path)
        tessdata_parent_path: str = os.path.join(executable_parent_path, "tessdata")

        if compile_portable:
            latest_compiled_version: str = get_latest_compiled_version()
            provided_exe_version: str = get_executable_version(exe_path)

            # Check if the provided executable path exists and only then overwrite.
            if latest_compiled_version != provided_exe_version:
                if os.path.exists(exe_path) and not force:
                    console.print(f"The provided Tesseract executable version: [{provided_exe_version}] "
                          f"is not the latest available version: [{latest_compiled_version}]. "
                          f"Do you want to update it and overwrite? (y/n)", style="yellow")
                    if input().strip().lower() != 'y':
                        print("Exiting without updating the provided tesseract executable.")
                        return 0

                execution_result: int = compile_exe(set_path=False)
                if execution_result != 0:
                    console.print("Failed to compile Tesseract from source. "
                          "Please check the logs for more details.", style="red")
                    return execution_result

                # Backing up the current version of Tesseract executable. But backup only if the folder exists, since if it is not it's new installation.
                if os.path.exists(executable_parent_path):
                    parent_of_the_current_parent_path: str = os.path.dirname(executable_parent_path)
                    exe_parent_dir_name: str = os.path.basename(executable_parent_path)
                    backup_path: str = os.path.join(parent_of_the_current_parent_path, f"{exe_parent_dir_name}_{provided_exe_version}_backup")
                    # Rename the current executable directory to back up.
                    shutil.move(executable_parent_path, backup_path)
                    print(f"Backed up the current Tesseract executable to: {backup_path}")

                # Create new empty directory for the new Tesseract executable.
                os.makedirs(executable_parent_path, exist_ok=True)

                # Copy all the files from the compiled Tesseract directory to the provided executable path.
                for item in TESSERACT_VCPKG_TOOLS_DIR.iterdir():
                    if item.is_file():
                        shutil.copy(item, executable_parent_path)
                    elif item.is_dir():
                        shutil.copytree(item, os.path.join(executable_parent_path, item.name), dirs_exist_ok=True)
            else:
                print(f"The provided Tesseract executable version: {provided_exe_version} "
                      f"is already the latest available version: {latest_compiled_version}. "
                      f"No need to update.")

            set_path = True

        if set_path:
            # Remove the old executable from the PATH if it exists.
            if not current_environment_path or current_environment_path.lower() != exe_path.lower():
                # Set the new Tesseract executable path and TESSDATA_PREFIX.
                registrys.ensure_exe_dir_in_path(exe_path)
                registrys.set_environment_variable('TESSDATA_PREFIX', tessdata_parent_path)
                print(f"Tesseract directory path set to: {executable_parent_path}")
                print(f"TESSDATA_PREFIX set to: {tessdata_parent_path}")
            return 0

        if installer_usage:
            print("This option is not implemented yet, please use the [--compile_portable] option to compile Tesseract from source.")
            return 0

    if compile_portable:
        if not force:
            print("Compiling Tesseract from source can take time ~2h. "
                  "Do you want to continue? (y/n)")
            if input().strip().lower() != 'y':
                return 0

            if current_environment_path != TESSERACT_VCPKG_TOOLS_EXE and set_path:
                print(f"Current Tesseract executable path: {current_environment_path}\n"
                      f"Do you want to update it with compiled executable path?: {TESSERACT_VCPKG_TOOLS_EXE}?\n"
                      f"(y/n)")
            if input().strip().lower() != 'y':
                print("Exiting without compiling Tesseract.")
                return 0

        execution_result: int = compile_exe(set_path=set_path)
        if execution_result != 0:
            print("Failed to compile Tesseract from source. "
                  "Please check the logs for more details.")
            return execution_result
        else:
            print("Tesseract OCR compiled successfully.")
            return 0

    if languages:
        tessdata_path: str | None = os.environ.get("TESSDATA_PREFIX", None)
        if tessdata_path is None:
            print("TESSDATA_PREFIX environment variable is not set. Cannot proceed with language operations.")
            return 1

        if 's' in languages:
            tessdata_path = os.path.join(tessdata_path, 'script')

        os.makedirs(tessdata_path, exist_ok=True)

        repo_path: str | None = None
        if languages == 'b':
            selected_github_wrapper: githubw.GitHubWrapper = TESSERACT_TESSDATA_BEST_GITHUB_WRAPPER
        elif languages == 'f':
            selected_github_wrapper: githubw.GitHubWrapper = TESSERACT_TESSDATA_FAST_GITHUB_WRAPPER
        elif languages == 'bs':
            repo_path = 'script'
            selected_github_wrapper: githubw.GitHubWrapper = TESSERACT_TESSDATA_BEST_GITHUB_WRAPPER
        elif languages == 'fs':
            repo_path = 'script'
            selected_github_wrapper: githubw.GitHubWrapper = TESSERACT_TESSDATA_FAST_GITHUB_WRAPPER
        else:
            print(f"Invalid languages option: {languages}")
            return 1

        available_files: list[str] = selected_github_wrapper.list_files(pattern='*.traineddata', recursive=False, path=repo_path)

        if lang_list:
            print("Available language/script files:")
            for file in available_files:
                print(f"- {file.replace('.traineddata', '').replace('script/', '')}")
            return 0

        if lang_download is not None:
            for file_name in lang_download:
                if '.traineddata' not in file_name:
                    file_name = f"{file_name}.traineddata"

                # If it is a script, adjust the file path.
                if 's' in languages and 'script' not in file_name:
                    file_name = f"script/{file_name}"

                if file_name in available_files:
                    print(f"Downloading language/script file: {file_name} ...")
                    selected_github_wrapper.download_file(
                        file_name=file_name,
                        target_dir=tessdata_path
                    )
                    console.print(f"Downloaded {file_name} to {tessdata_path}", style="cyan")
                else:
                    console.print(f"Language/script code '{file_name}' not found in the selected tessdata set.", style="red")

    if download_configs:
        tessdata_path: str | None = os.environ.get("TESSDATA_PREFIX", None)
        if tessdata_path is None:
            print("TESSDATA_PREFIX environment variable is not set. Cannot proceed with downloading configs.")
            return 1

        os.makedirs(tessdata_path, exist_ok=True)

        print(f"Downloading config files.")
        TESSERACT_TESSCONFIGS_GITHUB_WRAPPER.download_and_extract_branch(target_directory=tessdata_path, archive_remove_first_directory=True)
        console.print(f"Downloaded configs to {tessdata_path}", style="cyan")
    return 0


if __name__ == '__main__':
    exec_parser = _make_parser()
    args = exec_parser.parse_args()
    sys.exit(main(**vars(args)))