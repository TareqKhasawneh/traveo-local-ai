# TRAVEO Local AI

**Turn natural language into real Windows actions—with a model running on your own PC.**

TRAVEO is a free, open-source local AI assistant built for the TRAVEO YouTube community. It combines **Ollama**, **Qwen3 4B**, and **Python** to open applications, create text and source files, and organize folders. Use the desktop interface or the terminal.

No paid AI API or API key is required. After installing dependencies and downloading the model, inference runs locally with the default Ollama connection. Applications you launch can still use the internet independently.

> **Start with a disposable demo folder.** Tools execute immediately: this version has no confirmation dialog, preview, or undo. File updates can replace existing content, and organization moves files.

## How it works

| Component | Responsibility |
| --- | --- |
| Desktop UI / terminal | Collects your command and displays results and activity. |
| Ollama | Hosts and runs the downloaded Qwen model locally. |
| Qwen (`qwen3:4b`) | Interprets your instruction and selects structured tool names and arguments. |
| Python tool router | Looks up the requested name in the six registered tools and invokes it. |
| Windows tools | Perform the actual application launch or filesystem operation using your account's permissions. |

For **“Open Google Chrome”**, Qwen requests `open_app` with `{"app_name": "Google Chrome"}`. The Python router then calls the real function, which searches Windows for the installed application and launches it.

Qwen chooses the operation; **Python performs the Windows action**. The model does not execute Python code. When tools run, TRAVEO returns their actual results directly, without asking Qwen to rewrite them. Non-tool replies are displayed as model text with leaked thinking blocks removed.

Each command starts a fresh model request. There is no persistent conversation memory or iterative agent loop, although one response may request multiple tools.

## Features

- **Open installed apps:** searches PATH, Start Menu/Desktop shortcuts, registry App Paths, and Windows Start Apps. Common aliases include Chrome and VS Code; discovery is not limited to those aliases.
- **Create folders:** supports nested folders and Windows user-folder aliases.
- **Create text or source files:** write `.txt`, `.py`, `.html`, `.json`, `.cpp`, and other text formats.
- **Update or append text:** replace content or add text to a file.
- **Organize folders:** sort top-level files by category or extension, leave existing directories in place, and skip destination filename collisions.
- **List directory contents:** show files and folders, with a configurable limit capped at 500.
- **Desktop and terminal modes:** a dark CustomTkinter UI with activity output, or a command-line interface.

## Installation (Windows)

### 1. Install prerequisites

- **Windows 10 or 11.** Application discovery and launching use Windows APIs and utilities.
- **Python 3.11 or newer:** download from [python.org](https://www.python.org/downloads/windows/). Include **pip** and **Tcl/Tk** in the installer, and enable **Add Python to PATH**. The code requires Python 3.10+ syntax; 3.11+ is the setup baseline used here.
- **Ollama:** install the current Windows version from [ollama.com/download/windows](https://ollama.com/download/windows). Keep the Ollama application running.
- **Git:** install from [git-scm.com](https://git-scm.com/downloads/win), or use GitHub's **Code → Download ZIP** option.

Reserve several gigabytes of disk space for the model and Python environment. Runtime memory and speed depend on your hardware and model context. A supported GPU can accelerate inference; CPU execution is slower.

Open a new **PowerShell** window after installation and check:

```powershell
python --version
ollama --version
```

### 2. Download Qwen locally

```powershell
ollama pull qwen3:4b
ollama list
```

Use the exact tag **`qwen3:4b`** (including the `b`), which matches `MODEL` in `main.py`. The Python `ollama` dependency is a client library; it does not install the Ollama application or download model weights.

Optional: verify the model with `ollama run qwen3:4b`, send a greeting, then type `/bye` to leave that interactive session.

### 3. Get the project

```powershell
git clone https://github.com/TareqKhasawneh/traveo-local-ai.git
cd traveo-local-ai
```

If you downloaded a ZIP instead, extract it and open PowerShell in the extracted folder containing `main.py`, `ui.py`, and `requirements.txt`.

### 4. Create an isolated Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

Direct dependencies are pinned to the versions in the supplied project environment: `ollama==0.6.3` and `customtkinter==6.0.0`. Pip installs their transitive dependencies. `tkinter`, `winreg`, and the other standard-library imports do not belong in `requirements.txt`.

**If PowerShell blocks activation**, you can use the environment directly without changing your execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ui.py
```

### 5. Start TRAVEO

With your virtual environment activated and Ollama running:

**Desktop interface**

```powershell
python ui.py
```

Type a command and press **Enter** or **Send**. The activity panel shows requested tools, arguments, and results. Close the window to exit. The **Organize Downloads** quick action moves real files immediately; try the demo commands below first.

**Terminal interface**

```powershell
python main.py
```

Type `exit`, `quit`, or `bye` to stop. Without activation, use `.\.venv\Scripts\python.exe main.py` instead.

## Try it: a small demo

Send these commands **one at a time**. Keep the example folder disposable.

```text
Open Notepad
Create a folder called Traveo Demo on my desktop
Create hello.py inside desktop/Traveo Demo that prints Hello World
Create notes.txt inside desktop/Traveo Demo containing Welcome to TRAVEO
List the files inside desktop/Traveo Demo
Append the text "Made with local AI" to desktop/Traveo Demo/notes.txt
Organize desktop/Traveo Demo by category
List the files inside desktop/Traveo Demo
```

The organization command should move `hello.py` into `Code` and `notes.txt` into `Documents`. Model interpretation can vary; check the reported tool arguments and results.

Other examples:

```text
Open Google Chrome
Open VS Code
Create a folder at documents/Projects/Traveo
List my Downloads
Sort desktop/Traveo Demo by extension
```

Use explicit locations when a task depends on a particular folder. Python resolves aliases such as `desktop`, `downloads`, `documents`, `pictures`, `videos`, `music`, and `home`. Desktop/Documents/Pictures/Videos/Music prefer existing folders under `~/OneDrive`; Downloads uses `~/Downloads`. Absolute Windows paths and `~` are also supported. Other relative paths resolve from the project directory. The prompt asks the model to default new files without a location to Desktop.

## Safety architecture

### Implemented safeguards

- The router only calls functions registered in `ALLOWED_TOOLS`; unknown names are rejected.
- There is no generic shell-command tool and no `eval` or `exec` of model text. Application launches use discovered paths or Windows file associations; Start Apps discovery uses a fixed PowerShell command.
- Invalid invocation arguments and tool execution errors are caught and reported. This is error handling, not comprehensive semantic validation.
- `create_file` refuses to replace an existing file by default unless `overwrite=True` is supplied.
- `organize_directory` processes top-level files only, leaves existing directories in place, and skips existing destination filenames in normal operation.
- Tool results are displayed directly instead of being rewritten by the model.

### Boundaries of this version

**The tool allowlist is not a filesystem sandbox or an application allowlist.** Tools can access any path your Windows account can access, and application discovery accepts arbitrary installed applications or direct paths. Opening a file can launch its associated program, including a script or executable.

There is **no confirmation gate, dry run, automatic backup, undo, or comprehensive path/content validation**. In particular, `write_file` replaces content by default, and Qwen can request `create_file(overwrite=True)`. Prompt instructions are not a security boundary. Concurrent changes to files can also undermine checks made before an operation.

Run under a normal Windows account, start with copied test files, and do not organize the project directory or important folders without backups. The activity view can display paths, filenames, and generated file content; consider that before recording or sharing your screen.

## Current limitations

- Designed for Windows; full application automation is not supported on macOS or Linux.
- Text input only: no microphone, speech output, vision, browser interaction, or general mouse/keyboard control.
- No persistent memory, automatic retries, or multi-step planning loop based on earlier tool results. Use one clear task per command.
- Small models can choose the wrong tool, infer the wrong path, produce poor code, or answer without calling a tool.
- Application matching uses name similarity and may select an unintended match. Exact names or full paths help.
- Folder aliases assume English folder names and a simple OneDrive layout; customized or localized Windows known folders may need explicit paths.
- File creation writes UTF-8 text. Naming a text file `.png`, `.pdf`, or `.docx` does **not** create a valid binary document.
- Organization moves files and does not provide rollback. Directory listing is nonrecursive and limited to 500 entries.
- The UI does not implement cancellation or streaming model responses; loading the model may take time.
- Local inference requires Ollama to remain available. Changing `OLLAMA_HOST` can send requests to another server; retain the default local setup for local processing.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `python` is not recognized or opens the Microsoft Store | Install Python with PATH enabled and reopen PowerShell. If `py` works, use `py -3` to create the environment, then its explicit Python executable. |
| `ollama` is not recognized | Install Ollama for Windows and reopen PowerShell. |
| Cannot communicate with Ollama / connection refused | Start the Ollama application. If you run it manually, use `ollama serve` in a separate terminal only when no server is running. The default endpoint is `http://localhost:11434`. |
| Model not found | Run `ollama pull qwen3:4b`, then verify it appears in `ollama list`. |
| `ModuleNotFoundError` | Install requirements with the same interpreter used to run the app. Prefer `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. |
| An unexpected `think` argument error | Check `python -m pip show ollama` and reinstall the pinned requirements in the active environment. Update the Ollama Windows application if necessary. |
| Tkinter import/display error | Modify the Windows Python installation to include Tcl/Tk; `python -m tkinter` should open a test window. Use a desktop session for the UI. |
| App cannot be found or wrong app opens | Confirm installation, use its exact name, or supply its full executable path. |
| Access denied | Choose a writable folder and check Windows/OneDrive permissions. |
| Slow first response | The model may be loading; memory pressure or CPU inference can make it slower. |

## Project files

| File | Purpose |
| --- | --- |
| `main.py` | Model configuration, prompts, Windows discovery, six tools, router, and terminal entry point. |
| `ui.py` | CustomTkinter interface and background worker for commands. |
| `requirements.txt` | Direct Python dependency versions. |
| `.gitignore` | Excludes environments, caches, secrets, local data, and generated artifacts. |
| `LICENSE` | MIT license for this project's source. |

## Contributing

Issues and pull requests are welcome. Include your Windows/Python/Ollama versions, reproduction steps, and the tool result when reporting a bug; redact personal paths and file content. Test changes in a disposable folder and describe any change to permissions, overwrite behavior, or tool access.

## License and acknowledgments

TRAVEO's source is released under the [MIT License](LICENSE). Ollama, Qwen model weights, and Python dependencies retain their own licenses; model weights are downloaded separately.

Built with [Ollama](https://ollama.com/), [Qwen](https://ollama.com/library/qwen3:4b), and [CustomTkinter](https://customtkinter.tomschimansky.com/).
