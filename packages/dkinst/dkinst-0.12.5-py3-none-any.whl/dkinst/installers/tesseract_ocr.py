from pathlib import Path
from types import ModuleType
from typing import Literal
import os

from . import _base
from . helpers.modules import tesseract_ocr_manager


class TesseractOCR(_base.BaseInstaller):
    def __init__(self):
        super().__init__()
        self.name: str = Path(__file__).stem
        self.description: str = "Tesseract OCR Installer"
        self.version: str = tesseract_ocr_manager.VERSION
        self.platforms: list = ["windows"]
        self.helper: ModuleType = tesseract_ocr_manager

        self.dir_path: str = str(Path(self.base_path) / self.name)
        self.exe_path: str = str(Path(self.dir_path) / "tesseract.exe")

    def install(
            self,
            force: bool = False
    ):
        return install_internal(exe_path=self.exe_path, force=force)

    def update(
            self,
            force: bool = False
    ):
        return self.install(force=force)

    def _show_help(
            self,
            method: Literal["install", "uninstall", "update"]
    ) -> None:
        if method == "install":
            method_help: str = (
                "This method uses the [tesseract_ocr_manager.py] with the following arguments:\n"
                "  --compile-portable               - compile the latest tesseract executable.\n"
                "  --set-path                       - set system PATH variable to provided executable.\n"
                f'  --exe-path "{self.exe_path}"                      - Specify the target executable\n'
                "\n"
                "  --force                          - force reinstallation/recompilation of the latest version even if executable is already present.\n"
                "  This one is used only if you provide it explicitly to the 'install' command. Example:\n"
                "    dkinst install tesseract_ocr force\n"
                "\n"
                "You can also use the 'manual' method to provide custom arguments to the helper script.\n"
                "Example:\n"
                "  dkinst manual tesseract_ocr help\n"
                "  dkinst manual tesseract_ocr --compile-portable --set-path\n"
                "\n"
            )
            print(method_help)
        elif method == "update":
            print("In this installer 'update()' is the same as 'install()'.")
        else:
            raise ValueError(f"Unknown method '{method}'.")


def install_internal(
        exe_path: str,
        force: bool = False
) -> int:
    tesseract_ocr_manager.main(
        compile_portable=True,
        set_path=True,
        exe_path=exe_path,
        force=force
    )

    tesseract_ocr_manager.main(
        languages='f',
        lang_download=['eng', 'osd'],
        download_configs=True
    )

    # Remove duplicate config files from tessdata folder.
    files_list: list[str] = [
        'batch',
        'batch.nochop',
        'eng.user-patterns',
        'eng.user-words',
        'LICENSE',
        'Makefile.am',
        'matdemo',
        'msdemo',
        'nobatch',
        'README.md',
        'segdemo'
    ]

    # Get tessdata environment variable
    tessdata_path: str | None = os.environ.get("TESSDATA_PREFIX", None)
    if tessdata_path is not None:
        for file_name in files_list:
            file_path: str = str(Path(tessdata_path) / file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    return 0