import json
import os
import re
import shutil
import subprocess
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Optional

import ollama

try:
    import winreg
except ImportError:
    winreg = None


# ============================================================
# CONFIG
# ============================================================

MODEL = "qwen3:4b"

PROJECT_DIR = Path(__file__).resolve().parent

# Important:
# Prevent subprocesses from inheriting a deleted/stale VS Code
# working directory.
os.chdir(PROJECT_DIR)

ActivityCallback = Optional[Callable[[str], None]]


# ============================================================
# ACTIVITY
# ============================================================

def emit_activity(
    callback: ActivityCallback,
    message: str,
) -> None:

    if callback is None:
        return

    try:
        callback(message)

    except Exception:
        pass


# ============================================================
# CLEAN MODEL OUTPUT
# ============================================================

def clean_model_text(
    text: str | None,
) -> str:
    """
    Remove Qwen thinking/reasoning blocks if they leak into output.
    """

    if not text:
        return ""

    text = str(text)

    # --------------------------------------------------------
    # Sometimes Qwen returns a closing </think> without
    # returning the opening <think>.
    # --------------------------------------------------------

    lower_text = text.lower()

    if "</think>" in lower_text:

        index = lower_text.rfind(
            "</think>"
        )

        text = text[
            index + len("</think>"):
        ]

    # --------------------------------------------------------
    # Complete thinking blocks
    # --------------------------------------------------------

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Unclosed thinking block
    # --------------------------------------------------------

    text = re.sub(
        r"<think>.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return text.strip()


# ============================================================
# KNOWN WINDOWS LOCATIONS
# ============================================================

def get_known_locations() -> dict[str, Path]:

    home = Path.home()

    onedrive = home / "OneDrive"

    def prefer_onedrive(
        folder_name: str,
    ) -> Path:

        onedrive_path = (
            onedrive
            / folder_name
        )

        normal_path = (
            home
            / folder_name
        )

        if onedrive_path.exists():
            return onedrive_path

        return normal_path

    return {

        "home":
            home,

        "desktop":
            prefer_onedrive(
                "Desktop"
            ),

        "downloads":
            home
            / "Downloads",

        "documents":
            prefer_onedrive(
                "Documents"
            ),

        "pictures":
            prefer_onedrive(
                "Pictures"
            ),

        "videos":
            prefer_onedrive(
                "Videos"
            ),

        "music":
            prefer_onedrive(
                "Music"
            ),
    }


# ============================================================
# PATH RESOLUTION
# ============================================================

def resolve_path(
    raw_path: str,
) -> Path:
    """
    Supports paths such as:

        desktop/test.py
        downloads
        documents/project
        C:\\Projects\\file.txt
        ~/Downloads/test.txt

    Relative paths resolve from the Traveo project directory.
    """

    value = (
        str(raw_path)
        .strip()
        .strip('"')
        .strip("'")
    )

    if not value:
        raise ValueError(
            "Path cannot be empty."
        )

    known = get_known_locations()

    normalized = value.replace(
        "\\",
        "/",
    )

    normalized_lower = (
        normalized.lower()
    )

    aliases = {

        "my desktop":
            "desktop",

        "desktop":
            "desktop",

        "my downloads":
            "downloads",

        "downloads":
            "downloads",

        "download":
            "downloads",

        "my documents":
            "documents",

        "documents":
            "documents",

        "document":
            "documents",

        "my pictures":
            "pictures",

        "pictures":
            "pictures",

        "photos":
            "pictures",

        "my videos":
            "videos",

        "videos":
            "videos",

        "my music":
            "music",

        "music":
            "music",

        "home":
            "home",
    }

    # --------------------------------------------------------
    # KNOWN LOCATION PREFIXES
    # --------------------------------------------------------

    for alias, location_key in aliases.items():

        alias_lower = alias.lower()

        if normalized_lower == alias_lower:

            return (
                known[
                    location_key
                ]
            )

        prefix = (
            alias_lower
            + "/"
        )

        if normalized_lower.startswith(
            prefix
        ):

            remainder = normalized[
                len(prefix):
            ]

            return (
                known[
                    location_key
                ]
                / Path(
                    remainder
                )
            )

    # --------------------------------------------------------
    # NORMAL WINDOWS / USER PATH
    # --------------------------------------------------------

    expanded = os.path.expandvars(
        os.path.expanduser(
            value
        )
    )

    path = Path(
        expanded
    )

    if path.is_absolute():
        return path

    return (
        PROJECT_DIR
        / path
    )


def looks_like_path(
    value: str,
) -> bool:

    value = str(
        value
    ).strip()

    return (
        "\\" in value
        or "/" in value
        or value.lower().endswith(
            ".exe"
        )
        or value.lower().endswith(
            ".lnk"
        )
        or value.startswith(
            "~"
        )
        or bool(
            re.match(
                r"^[A-Za-z]:",
                value,
            )
        )
    )


# ============================================================
# APPLICATION NAME MATCHING
# ============================================================

def normalize_app_name(
    value: str,
) -> str:

    value = str(
        value
    ).lower()

    value = re.sub(
        r"\.(exe|lnk)$",
        "",
        value,
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def similarity_score(
    requested: str,
    candidate: str,
) -> float:

    requested = normalize_app_name(
        requested
    )

    candidate = normalize_app_name(
        candidate
    )

    if not requested or not candidate:
        return 0.0

    if requested == candidate:
        return 1.0

    if requested in candidate:
        return 0.98

    if candidate in requested:
        return 0.92

    requested_words = set(
        requested.split()
    )

    candidate_words = set(
        candidate.split()
    )

    overlap = 0.0

    if requested_words:

        overlap = (
            len(
                requested_words
                & candidate_words
            )
            / len(
                requested_words
            )
        )

    sequence = SequenceMatcher(
        None,
        requested,
        candidate,
    ).ratio()

    return max(
        overlap,
        sequence,
    )


def get_app_search_names(
    app_name: str,
) -> list[str]:
    """
    These are convenience aliases, NOT a whitelist.

    Unknown applications can still be discovered dynamically.
    """

    normalized = normalize_app_name(
        app_name
    )

    aliases = {

        "chrome": [
            "Google Chrome",
            "Chrome",
            "chrome.exe",
        ],

        "google chrome": [
            "Google Chrome",
            "Chrome",
            "chrome.exe",
        ],

        "vs code": [
            "Visual Studio Code",
            "Code",
            "code.exe",
        ],

        "vscode": [
            "Visual Studio Code",
            "Code",
            "code.exe",
        ],

        "visual studio code": [
            "Visual Studio Code",
            "Code",
            "code.exe",
        ],

        "edge": [
            "Microsoft Edge",
            "msedge",
            "msedge.exe",
        ],

        "microsoft edge": [
            "Microsoft Edge",
            "msedge",
            "msedge.exe",
        ],

        "discord": [
            "Discord",
        ],

        "spotify": [
            "Spotify",
        ],

        "steam": [
            "Steam",
        ],

        "blender": [
            "Blender",
        ],

        "calculator": [
            "Calculator",
            "calc.exe",
        ],

        "notepad": [
            "Notepad",
            "notepad.exe",
        ],
    }

    result = [
        app_name
    ]

    for alias in aliases.get(
        normalized,
        [],
    ):

        if alias not in result:
            result.append(
                alias
            )

    return result


# ============================================================
# FIND EXECUTABLE ON PATH
# ============================================================

def find_path_executable(
    app_name: str,
) -> Optional[str]:

    for search_name in get_app_search_names(
        app_name
    ):

        variants = [
            search_name,
            search_name.replace(
                " ",
                "",
            ),
        ]

        if not search_name.lower().endswith(
            ".exe"
        ):

            variants.extend(
                [
                    f"{search_name}.exe",
                    (
                        search_name.replace(
                            " ",
                            "",
                        )
                        + ".exe"
                    ),
                ]
            )

        for candidate in variants:

            located = shutil.which(
                candidate
            )

            if located:
                return located

    return None


# ============================================================
# SEARCH START MENU SHORTCUTS
# ============================================================

def find_start_menu_shortcut(
    app_name: str,
) -> Optional[Path]:

    directories = []

    appdata = os.environ.get(
        "APPDATA"
    )

    programdata = os.environ.get(
        "PROGRAMDATA"
    )

    if appdata:

        directories.append(
            Path(appdata)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )

    if programdata:

        directories.append(
            Path(programdata)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )

    directories.append(
        get_known_locations()[
            "desktop"
        ]
    )

    search_names = get_app_search_names(
        app_name
    )

    best_match = None
    best_score = 0.0

    for directory in directories:

        if not directory.exists():
            continue

        try:

            shortcuts = directory.rglob(
                "*.lnk"
            )

            for shortcut in shortcuts:

                for search_name in search_names:

                    score = similarity_score(
                        search_name,
                        shortcut.stem,
                    )

                    if score > best_score:

                        best_score = score
                        best_match = shortcut

        except (
            PermissionError,
            OSError,
        ):
            continue

    if (
        best_match is not None
        and best_score >= 0.55
    ):

        return best_match

    return None


# ============================================================
# SEARCH WINDOWS REGISTRY APP PATHS
# ============================================================

def find_registry_app(
    app_name: str,
) -> Optional[str]:

    if winreg is None:
        return None

    registry_locations = [

        (
            winreg.HKEY_CURRENT_USER,
            (
                r"Software\Microsoft\Windows"
                r"\CurrentVersion\App Paths"
            ),
        ),

        (
            winreg.HKEY_LOCAL_MACHINE,
            (
                r"Software\Microsoft\Windows"
                r"\CurrentVersion\App Paths"
            ),
        ),

        (
            winreg.HKEY_LOCAL_MACHINE,
            (
                r"Software\WOW6432Node"
                r"\Microsoft\Windows"
                r"\CurrentVersion\App Paths"
            ),
        ),
    ]

    search_names = get_app_search_names(
        app_name
    )

    best_path = None
    best_score = 0.0

    for root, registry_path in registry_locations:

        try:

            base_key = winreg.OpenKey(
                root,
                registry_path,
            )

        except OSError:
            continue

        try:

            index = 0

            while True:

                try:

                    subkey_name = (
                        winreg.EnumKey(
                            base_key,
                            index,
                        )
                    )

                except OSError:
                    break

                index += 1

                try:

                    with winreg.OpenKey(
                        base_key,
                        subkey_name,
                    ) as subkey:

                        executable_path, _ = (
                            winreg.QueryValueEx(
                                subkey,
                                None,
                            )
                        )

                    executable_path = str(
                        executable_path
                    )

                    path = Path(
                        executable_path
                    )

                    candidate_names = [
                        subkey_name,
                        path.stem,
                        path.parent.name,
                    ]

                    score = 0.0

                    for search_name in search_names:

                        for candidate in candidate_names:

                            candidate_score = (
                                similarity_score(
                                    search_name,
                                    candidate,
                                )
                            )

                            score = max(
                                score,
                                candidate_score,
                            )

                    if (
                        score > best_score
                        and path.exists()
                    ):

                        best_score = score
                        best_path = executable_path

                except (
                    OSError,
                    ValueError,
                ):
                    continue

        finally:

            try:
                winreg.CloseKey(
                    base_key
                )
            except Exception:
                pass

    if (
        best_path
        and best_score >= 0.50
    ):

        return best_path

    return None


# ============================================================
# GET WINDOWS START APPS
# ============================================================

def get_windows_start_apps() -> list[dict]:

    command = (
        "Get-StartApps "
        "| Select-Object Name,AppID "
        "| ConvertTo-Json -Compress"
    )

    try:

        process = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(
                PROJECT_DIR
            ),
        )

        if process.returncode != 0:
            return []

        output = (
            process.stdout
            .strip()
        )

        if not output:
            return []

        parsed = json.loads(
            output
        )

        if isinstance(
            parsed,
            dict,
        ):
            return [
                parsed
            ]

        if isinstance(
            parsed,
            list,
        ):
            return parsed

    except Exception:
        pass

    return []


def find_windows_start_app(
    app_name: str,
) -> Optional[dict]:

    apps = get_windows_start_apps()

    if not apps:
        return None

    search_names = get_app_search_names(
        app_name
    )

    best_app = None
    best_score = 0.0

    for app in apps:

        candidate_name = str(
            app.get(
                "Name",
                "",
            )
        )

        for search_name in search_names:

            score = similarity_score(
                search_name,
                candidate_name,
            )

            if score > best_score:

                best_score = score
                best_app = app

    if (
        best_app is not None
        and best_score >= 0.55
    ):

        return best_app

    return None


# ============================================================
# TOOL 1: OPEN APPLICATION
# ============================================================

def open_app(
    app_name: str,
) -> str:
    """
    Dynamically find and open an installed Windows application.

    Examples:
        Google Chrome
        Discord
        Spotify
        Blender
        Steam
        VS Code

    A full executable path may also be supplied.
    """

    app_name = str(
        app_name
    ).strip()

    if not app_name:
        return (
            "Application name cannot be empty."
        )

    # --------------------------------------------------------
    # DIRECT PATH
    # --------------------------------------------------------

    if looks_like_path(
        app_name
    ):

        try:

            direct_path = resolve_path(
                app_name
            )

            if (
                direct_path.exists()
                and direct_path.is_file()
            ):

                os.startfile(
                    str(
                        direct_path
                    )
                )

                return (
                    f"Opened '{direct_path.name}' successfully."
                )

        except Exception:
            pass

    # --------------------------------------------------------
    # PATH ENVIRONMENT
    # --------------------------------------------------------

    executable = find_path_executable(
        app_name
    )

    if executable:

        try:

            subprocess.Popen(
                [
                    executable
                ],
                cwd=str(
                    PROJECT_DIR
                ),
            )

            return (
                f"Opened '{app_name}' successfully."
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # START MENU SHORTCUT
    # --------------------------------------------------------

    shortcut = find_start_menu_shortcut(
        app_name
    )

    if shortcut:

        try:

            os.startfile(
                str(
                    shortcut
                )
            )

            return (
                f"Opened '{shortcut.stem}' successfully."
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # REGISTRY
    # --------------------------------------------------------

    registry_app = find_registry_app(
        app_name
    )

    if registry_app:

        try:

            subprocess.Popen(
                [
                    registry_app
                ],
                cwd=str(
                    PROJECT_DIR
                ),
            )

            return (
                f"Opened '{app_name}' successfully."
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # WINDOWS START APPS
    # --------------------------------------------------------

    start_app = find_windows_start_app(
        app_name
    )

    if start_app:

        app_id = str(
            start_app.get(
                "AppID",
                "",
            )
        )

        app_display_name = str(
            start_app.get(
                "Name",
                app_name,
            )
        )

        if app_id:

            try:

                subprocess.Popen(
                    [
                        "explorer.exe",
                        (
                            "shell:AppsFolder\\"
                            + app_id
                        ),
                    ],
                    cwd=str(
                        PROJECT_DIR
                    ),
                )

                return (
                    f"Opened '{app_display_name}' successfully."
                )

            except Exception:
                pass

    return (
        f"I couldn't find an installed application "
        f"matching '{app_name}'. "
        "You can also provide its full executable path."
    )


# ============================================================
# TOOL 2: CREATE FOLDER
# ============================================================

def create_folder(
    directory_path: str,
) -> str:
    """
    Create a folder anywhere the current Windows user
    has permission to write.

    Examples:

        desktop/My Project
        downloads/Test
        documents/Projects/App
        C:\\Projects\\Traveo
    """

    try:

        path = resolve_path(
            directory_path
        )

    except Exception as error:

        return (
            f"Invalid directory path: {error}"
        )

    if path.exists():

        if path.is_dir():

            return (
                f"Folder already exists: {path}"
            )

        return (
            f"A file already exists at: {path}"
        )

    try:

        path.mkdir(
            parents=True,
            exist_ok=False,
        )

        return (
            f"Folder created successfully: {path}"
        )

    except PermissionError:

        return (
            f"Windows denied permission to create: {path}"
        )

    except Exception as error:

        return (
            f"Could not create folder: {error}"
        )


# ============================================================
# TOOL 3: CREATE FILE
# ============================================================

def create_file(
    file_path: str,
    content: str = "",
    overwrite: bool = False,
) -> str:
    """
    Create a text/source/configuration file.

    No extension whitelist is used.

    Examples:

        desktop/hello.py
        documents/notes.txt
        desktop/index.html
        desktop/data.json
        C:\\Projects\\main.cpp

    overwrite=False prevents accidental replacement.

    This function creates text-based files. Merely naming
    something image.png or document.docx does NOT create
    a valid binary PNG/DOCX file.
    """

    try:

        path = resolve_path(
            file_path
        )

    except Exception as error:

        return (
            f"Invalid file path: {error}"
        )

    if path.exists():

        if path.is_dir():

            return (
                f"A folder already exists at: {path}"
            )

        if not overwrite:

            return (
                f"File already exists: {path}. "
                "Set overwrite=true only if replacement "
                "is intentionally requested."
            )

    try:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            str(
                content
            ),
            encoding="utf-8",
        )

        return (
            f"File created successfully: {path}"
        )

    except PermissionError:

        return (
            f"Windows denied permission to write to: {path}"
        )

    except Exception as error:

        return (
            f"Could not create file: {error}"
        )


# ============================================================
# TOOL 4: WRITE / UPDATE FILE
# ============================================================

def write_file(
    file_path: str,
    content: str,
    append: bool = False,
) -> str:
    """
    Write text to an existing or new text/source file.

    append=False:
        Replace current contents.

    append=True:
        Add content to the end.
    """

    try:

        path = resolve_path(
            file_path
        )

    except Exception as error:

        return (
            f"Invalid file path: {error}"
        )

    if path.exists() and path.is_dir():

        return (
            f"The supplied path is a directory: {path}"
        )

    try:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if append:

            with path.open(
                "a",
                encoding="utf-8",
            ) as file:

                file.write(
                    str(
                        content
                    )
                )

            return (
                f"Content appended successfully to: {path}"
            )

        path.write_text(
            str(
                content
            ),
            encoding="utf-8",
        )

        return (
            f"File written successfully: {path}"
        )

    except PermissionError:

        return (
            f"Windows denied permission to write to: {path}"
        )

    except Exception as error:

        return (
            f"Could not write file: {error}"
        )


# ============================================================
# FILE CATEGORIES
# ============================================================

FILE_CATEGORIES = {

    "Images": {

        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
        ".svg",
        ".ico",
        ".tiff",
        ".tif",
        ".raw",
        ".heic",
    },

    "Documents": {

        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".csv",
        ".md",
        ".epub",
    },

    "Videos": {

        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".wmv",
        ".flv",
        ".m4v",
    },

    "Audio": {

        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
        ".wma",
    },

    "Archives": {

        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
    },

    "Code": {

        ".py",
        ".pyw",

        ".js",
        ".jsx",

        ".ts",
        ".tsx",

        ".html",
        ".htm",

        ".css",
        ".scss",
        ".sass",
        ".less",

        ".cpp",
        ".cc",
        ".cxx",

        ".c",

        ".h",
        ".hpp",

        ".cs",

        ".java",

        ".kt",
        ".kts",

        ".go",

        ".rs",

        ".php",

        ".rb",

        ".swift",

        ".dart",

        ".json",

        ".xml",

        ".yaml",
        ".yml",

        ".toml",

        ".sql",

        ".sh",

        ".ps1",

        ".bat",
        ".cmd",

        ".vue",

        ".svelte",
    },

    "Executables": {

        ".exe",
        ".msi",
        ".msix",
        ".appx",
    },

    "Fonts": {

        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
    },

    "3D": {

        ".blend",
        ".fbx",
        ".obj",
        ".stl",
        ".gltf",
        ".glb",
    },

    "Design": {

        ".psd",
        ".ai",
        ".fig",
        ".xd",
        ".sketch",
    },
}


def category_for_file(
    file_path: Path,
) -> str:

    extension = (
        file_path
        .suffix
        .lower()
    )

    for category, extensions in FILE_CATEGORIES.items():

        if extension in extensions:
            return category

    return "Other"


# ============================================================
# TOOL 5: ORGANIZE DIRECTORY
# ============================================================

def organize_directory(
    directory_path: str,
    strategy: str = "category",
) -> str:
    """
    Organize top-level files inside ANY accessible directory.

    strategy="category":
        Images
        Documents
        Videos
        Audio
        Code
        Archives
        Executables
        etc.

    strategy="extension":
        PNG
        JPG
        PY
        JSON
        MP4
        etc.

    Existing directories are not moved.
    Existing destination files are never overwritten.
    """

    try:

        directory = resolve_path(
            directory_path
        )

    except Exception as error:

        return (
            f"Invalid directory path: {error}"
        )

    if not directory.exists():

        return (
            f"Directory does not exist: {directory}"
        )

    if not directory.is_dir():

        return (
            f"The supplied path is not a directory: {directory}"
        )

    strategy = (
        str(
            strategy
        )
        .strip()
        .lower()
    )

    if strategy not in {
        "category",
        "extension",
    }:

        return (
            "Unknown organization strategy. "
            "Use 'category' or 'extension'."
        )

    try:

        items = list(
            directory.iterdir()
        )

    except PermissionError:

        return (
            f"Windows denied permission to read: {directory}"
        )

    moved_files = []
    skipped_files = []
    failed_files = []

    for item in items:

        # Existing directories are not touched.
        if not item.is_file():
            continue

        # ----------------------------------------------------
        # DESTINATION CATEGORY
        # ----------------------------------------------------

        if strategy == "category":

            folder_name = category_for_file(
                item
            )

        else:

            extension = (
                item
                .suffix
                .lower()
                .lstrip(".")
            )

            if extension:

                folder_name = (
                    extension.upper()
                )

            else:

                folder_name = (
                    "No Extension"
                )

        destination_folder = (
            directory
            / folder_name
        )

        try:

            destination_folder.mkdir(
                exist_ok=True
            )

        except Exception as error:

            failed_files.append(
                f"{item.name}: {error}"
            )

            continue

        destination = (
            destination_folder
            / item.name
        )

        # Never overwrite.
        if destination.exists():

            skipped_files.append(
                item.name
            )

            continue

        try:

            shutil.move(
                str(
                    item
                ),
                str(
                    destination
                ),
            )

            moved_files.append(
                f"{item.name} -> {folder_name}"
            )

        except Exception as error:

            failed_files.append(
                f"{item.name}: {error}"
            )

    if (
        not moved_files
        and not skipped_files
        and not failed_files
    ):

        return (
            f"No files needed organizing in {directory}."
        )

    results = []

    if moved_files:

        results.append(
            (
                f"Organized {len(moved_files)} "
                "files successfully."
            )
        )

    if skipped_files:

        results.append(
            (
                f"Skipped {len(skipped_files)} files "
                "because a file with the same name "
                "already existed in the destination."
            )
        )

    if failed_files:

        results.append(
            (
                f"{len(failed_files)} files "
                "could not be moved."
            )
        )

    return " ".join(
        results
    )


# ============================================================
# TOOL 6: LIST DIRECTORY
# ============================================================

def list_directory(
    directory_path: str,
    limit: int = 100,
) -> str:
    """
    Show files/folders in an accessible directory.
    """

    try:

        directory = resolve_path(
            directory_path
        )

    except Exception as error:

        return (
            f"Invalid directory path: {error}"
        )

    if not directory.exists():

        return (
            f"Directory does not exist: {directory}"
        )

    if not directory.is_dir():

        return (
            f"Path is not a directory: {directory}"
        )

    try:

        items = sorted(
            directory.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower(),
            ),
        )

    except PermissionError:

        return (
            f"Windows denied permission to read: {directory}"
        )

    safe_limit = max(
        1,
        min(
            int(limit),
            500,
        ),
    )

    items = items[
        :safe_limit
    ]

    if not items:

        return (
            f"Directory is empty: {directory}"
        )

    lines = [
        f"Contents of {directory}:"
    ]

    for item in items:

        if item.is_dir():

            item_type = "DIR"

        else:

            item_type = "FILE"

        lines.append(
            f"[{item_type}] {item.name}"
        )

    return "\n".join(
        lines
    )


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = [

    open_app,

    create_folder,

    create_file,

    write_file,

    organize_directory,

    list_directory,
]


# ============================================================
# TOOL ROUTER
# ============================================================

ALLOWED_TOOLS = {

    tool.__name__:
        tool

    for tool in TOOLS
}


def normalize_tool_arguments(
    arguments,
) -> dict:

    if arguments is None:
        return {}

    if isinstance(
        arguments,
        dict,
    ):
        return arguments

    if isinstance(
        arguments,
        str,
    ):

        try:

            parsed = json.loads(
                arguments
            )

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

        except Exception:
            pass

    try:

        return dict(
            arguments
        )

    except Exception:

        return {}


def route_tool_call(
    tool_call,
    activity_callback: ActivityCallback = None,
) -> str:

    tool_name = (
        tool_call
        .function
        .name
    )

    arguments = normalize_tool_arguments(
        tool_call
        .function
        .arguments
    )

    emit_activity(
        activity_callback,
        f"Tool requested: {tool_name}",
    )

    emit_activity(
        activity_callback,
        f"Arguments: {arguments}",
    )

    if tool_name not in ALLOWED_TOOLS:

        result = (
            f"Tool '{tool_name}' does not exist."
        )

        emit_activity(
            activity_callback,
            result,
        )

        return result

    tool_function = (
        ALLOWED_TOOLS[
            tool_name
        ]
    )

    try:

        result = tool_function(
            **arguments
        )

        emit_activity(
            activity_callback,
            f"Result: {result}",
        )

        return result

    except TypeError as error:

        result = (
            f"Invalid tool arguments: {error}"
        )

        emit_activity(
            activity_callback,
            result,
        )

        return result

    except Exception as error:

        result = (
            f"Tool execution failed: {error}"
        )

        emit_activity(
            activity_callback,
            result,
        )

        return result


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are Traveo, a local AI assistant running on the user's Windows PC.

You interpret natural-language instructions and select Python tools.

IMPORTANT:

You do NOT directly control Windows.

The language model decides WHICH Python operation is appropriate and
supplies arguments.

Python performs the real operation.


AVAILABLE TOOLS


1. open_app

Dynamically finds and opens installed Windows applications.

It is NOT restricted to a hardcoded application list.

Examples:

User:
Open Google Chrome

Call:
open_app(app_name="Google Chrome")


User:
Open Discord

Call:
open_app(app_name="Discord")


User:
Launch Blender

Call:
open_app(app_name="Blender")


Do NOT claim that an application is disallowed merely because its name
was not used in an example.


2. create_folder

Creates folders at any accessible Windows path.

Examples:

User:
Create Projects on my desktop

Call:
create_folder(
    directory_path="desktop/Projects"
)


User:
Create Test inside Documents

Call:
create_folder(
    directory_path="documents/Test"
)


User:
Create C:\\Projects\\Traveo

Call:
create_folder(
    directory_path="C:\\Projects\\Traveo"
)


3. create_file

Creates text, source-code, configuration and similar files.

There is no extension whitelist.

Examples include:

.txt
.py
.cpp
.c
.h
.hpp
.cs
.java
.js
.ts
.html
.css
.json
.xml
.yaml
.md
.sql
.php
.go
.rs

Example:

User:
Create hello.py on my desktop that prints Hello World

Call:
create_file(
    file_path="desktop/hello.py",
    content="print('Hello World')"
)


User:
Create notes.txt in Documents

Call:
create_file(
    file_path="documents/notes.txt",
    content=""
)


If the user does not specify a location when creating a new file,
default to:

desktop/<filename>


IMPORTANT:

A filename extension does not automatically create a valid binary file.

For example, writing text into:

image.png

does not create a real PNG.

Likewise .docx, .pdf, .exe and other binary formats require dedicated
format-generation functionality.


4. write_file

Writes or appends text to text/source/configuration files.

Use append=true only when the user specifically wants existing content
preserved and new content added to the end.


5. organize_directory

Organizes files in ANY directory the user specifies.

It is NOT limited to Downloads.

Examples:

User:
Organize my Downloads

Call:
organize_directory(
    directory_path="downloads",
    strategy="category"
)


User:
Organize my Documents

Call:
organize_directory(
    directory_path="documents",
    strategy="category"
)


User:
Organize C:\\Projects\\RandomFiles

Call:
organize_directory(
    directory_path="C:\\Projects\\RandomFiles",
    strategy="category"
)


User:
Sort my Downloads by extension

Call:
organize_directory(
    directory_path="downloads",
    strategy="extension"
)


6. list_directory

Use this when the user asks what files or folders exist in a directory.


GENERAL RULES

1. Use a tool whenever the user requests a supported computer action.

2. Never claim success unless the Python tool actually reports success.

3. Never invent tools.

4. Applications are NOT restricted to a predefined app list.

5. File locations are NOT restricted to Desktop or Downloads.

6. Text/source file extensions are NOT restricted.

7. Do not invent a path when the user's request requires a specific path
   that cannot reasonably be inferred.

8. Never output internal reasoning.

9. Never output chain-of-thought.

10. Never output <think> blocks.

11. Keep final conversational responses short.

12. Do not output Python-like tool syntax as a conversational response
    when a real tool is available. Actually call the tool.
"""


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(
    user_input: str,
    activity_callback: ActivityCallback = None,
) -> str:

    user_input = str(
        user_input
    ).strip()

    if not user_input:

        return (
            "Please enter a command."
        )

    emit_activity(
        activity_callback,
        f"Sending request to {MODEL}...",
    )

    messages = [

        {
            "role":
                "system",

            "content":
                SYSTEM_PROMPT,
        },

        {
            "role":
                "user",

            "content":
                user_input,
        },
    ]

    try:

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            think=False,
        )

    except Exception as error:

        emit_activity(
            activity_callback,
            "Ollama communication failed.",
        )

        return (
            f"Could not communicate with Ollama: {error}"
        )

    # ========================================================
    # TOOL CALLS
    # ========================================================

    tool_calls = (
        response
        .message
        .tool_calls
    )

    if tool_calls:

        emit_activity(
            activity_callback,
            (
                f"Model requested "
                f"{len(tool_calls)} tool call(s)."
            ),
        )

        tool_results = []

        for tool_call in tool_calls:

            result = route_tool_call(
                tool_call,
                activity_callback,
            )

            tool_results.append(
                result
            )

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Do NOT send the tool result back to Qwen just so it
        # can rewrite it.
        #
        # Python already knows exactly what happened.
        # Returning the real tool result avoids hallucinations
        # and avoids Qwen leaking reasoning.
        # ----------------------------------------------------

        emit_activity(
            activity_callback,
            "Command processing completed.",
        )

        return "\n".join(
            str(
                result
            )
            for result
            in tool_results
        )

    # ========================================================
    # NORMAL NON-TOOL RESPONSE
    # ========================================================

    content = clean_model_text(
        response
        .message
        .content
    )

    emit_activity(
        activity_callback,
        "Response received.",
    )

    if content:
        return content

    return (
        "I couldn't determine what to do."
    )


# ============================================================
# TERMINAL VERSION
# ============================================================

def run_cli() -> None:

    print()

    print(
        "======================================"
    )

    print(
        "        TRAVEO LOCAL ASSISTANT"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Project:",
        PROJECT_DIR,
    )

    print(
        "Model:",
        MODEL,
    )

    print(
        "Tools:",
        [
            tool.__name__
            for tool in TOOLS
        ],
    )

    print()

    print(
        "Type 'exit' to quit."
    )

    print()

    while True:

        user_input = input(
            "You > "
        ).strip()

        if not user_input:
            continue

        if user_input.lower() in {
            "exit",
            "quit",
            "bye",
        }:

            print()

            print(
                "Traveo > Goodbye!"
            )

            break

        result = process_command(
            user_input,
            activity_callback=print,
        )

        print()

        print(
            f"Traveo > {result}"
        )

        print()


# ============================================================
# START TERMINAL ONLY WHEN main.py IS RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    run_cli()