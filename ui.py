import threading

import customtkinter as ctk

from main import MODEL, process_command


# ============================================================
# CONFIG
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


BACKGROUND = "#070B12"
PANEL = "#0D1420"
PANEL_LIGHT = "#121C2A"

BLUE = "#1688FF"
BLUE_HOVER = "#0872DB"

TEXT = "#F3F6FA"
TEXT_SECONDARY = "#8897AA"

GREEN = "#2ED573"
BORDER = "#233247"


# ============================================================
# APP
# ============================================================

app = ctk.CTk()

app.title("Traveo Local AI")
app.geometry("1100x720")
app.minsize(900, 600)

app.configure(
    fg_color=BACKGROUND
)

app.grid_columnconfigure(
    0,
    weight=1,
)

app.grid_rowconfigure(
    1,
    weight=1,
)


# ============================================================
# HEADER
# ============================================================

header = ctk.CTkFrame(
    app,
    fg_color=PANEL,
    corner_radius=0,
    height=82,
)

header.grid(
    row=0,
    column=0,
    sticky="ew",
)

header.grid_columnconfigure(
    0,
    weight=1,
)


# ------------------------------------------------------------
# BRAND
# ------------------------------------------------------------

brand_frame = ctk.CTkFrame(
    header,
    fg_color="transparent",
)

brand_frame.grid(
    row=0,
    column=0,
    padx=28,
    pady=18,
    sticky="w",
)


title = ctk.CTkLabel(
    brand_frame,
    text="TRAVEO",
    text_color=TEXT,
    font=ctk.CTkFont(
        size=25,
        weight="bold",
    ),
)

title.pack(
    side="left",
)


subtitle = ctk.CTkLabel(
    brand_frame,
    text="LOCAL AI",
    text_color=BLUE,
    font=ctk.CTkFont(
        size=13,
        weight="bold",
    ),
)

subtitle.pack(
    side="left",
    padx=(12, 0),
)


# ------------------------------------------------------------
# MODEL INFO
# ------------------------------------------------------------

model_label = ctk.CTkLabel(
    header,
    text=f"Ollama  •  {MODEL}",
    text_color=TEXT_SECONDARY,
    font=ctk.CTkFont(
        size=12,
    ),
)

model_label.grid(
    row=0,
    column=1,
    padx=(10, 20),
)


# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

status_frame = ctk.CTkFrame(
    header,
    fg_color=PANEL_LIGHT,
    corner_radius=18,
)

status_frame.grid(
    row=0,
    column=2,
    padx=(0, 28),
    pady=20,
)


status_dot = ctk.CTkLabel(
    status_frame,
    text="●",
    text_color=GREEN,
    font=ctk.CTkFont(
        size=15,
    ),
)

status_dot.pack(
    side="left",
    padx=(12, 4),
    pady=6,
)


status_text = ctk.CTkLabel(
    status_frame,
    text="LOCAL",
    text_color=TEXT,
    font=ctk.CTkFont(
        size=11,
        weight="bold",
    ),
)

status_text.pack(
    side="left",
    padx=(0, 12),
    pady=6,
)


# ============================================================
# MAIN AREA
# ============================================================

main_container = ctk.CTkFrame(
    app,
    fg_color="transparent",
)

main_container.grid(
    row=1,
    column=0,
    sticky="nsew",
    padx=24,
    pady=24,
)

main_container.grid_columnconfigure(
    0,
    weight=3,
)

main_container.grid_columnconfigure(
    1,
    weight=1,
)

main_container.grid_rowconfigure(
    0,
    weight=1,
)


# ============================================================
# CHAT PANEL
# ============================================================

chat_panel = ctk.CTkFrame(
    main_container,
    fg_color=PANEL,
    corner_radius=18,
)

chat_panel.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 12),
)

chat_panel.grid_columnconfigure(
    0,
    weight=1,
)

chat_panel.grid_rowconfigure(
    1,
    weight=1,
)


chat_title = ctk.CTkLabel(
    chat_panel,
    text="Assistant",
    text_color=TEXT,
    font=ctk.CTkFont(
        size=18,
        weight="bold",
    ),
)

chat_title.grid(
    row=0,
    column=0,
    sticky="w",
    padx=22,
    pady=(20, 12),
)


chat_box = ctk.CTkTextbox(
    chat_panel,
    fg_color=PANEL_LIGHT,
    text_color=TEXT,
    corner_radius=12,
    border_width=1,
    border_color=BORDER,
    wrap="word",
    font=ctk.CTkFont(
        size=14,
    ),
)

chat_box.grid(
    row=1,
    column=0,
    sticky="nsew",
    padx=20,
    pady=(0, 15),
)

chat_box.insert(
    "end",
    (
        "TRAVEO\n"
        "Local AI assistant ready.\n\n"
        "Try: \"Open VS Code\"\n\n"
    ),
)

chat_box.configure(
    state="disabled",
)


# ============================================================
# COMMAND INPUT
# ============================================================

input_frame = ctk.CTkFrame(
    chat_panel,
    fg_color="transparent",
)

input_frame.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=20,
    pady=(0, 20),
)

input_frame.grid_columnconfigure(
    0,
    weight=1,
)


command_entry = ctk.CTkEntry(
    input_frame,
    placeholder_text="Ask Traveo to do something...",
    height=50,
    corner_radius=12,
    fg_color=PANEL_LIGHT,
    border_color=BORDER,
    border_width=1,
    text_color=TEXT,
    font=ctk.CTkFont(
        size=14,
    ),
)

command_entry.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(0, 10),
)


send_button = ctk.CTkButton(
    input_frame,
    text="Send",
    width=105,
    height=50,
    corner_radius=12,
    fg_color=BLUE,
    hover_color=BLUE_HOVER,
    text_color="white",
    font=ctk.CTkFont(
        size=14,
        weight="bold",
    ),
)

send_button.grid(
    row=0,
    column=1,
)


# ============================================================
# SIDE PANEL
# ============================================================

side_panel = ctk.CTkFrame(
    main_container,
    fg_color=PANEL,
    corner_radius=18,
)

side_panel.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=(12, 0),
)

side_panel.grid_columnconfigure(
    0,
    weight=1,
)

side_panel.grid_rowconfigure(
    6,
    weight=1,
)


quick_title = ctk.CTkLabel(
    side_panel,
    text="Quick Actions",
    text_color=TEXT,
    font=ctk.CTkFont(
        size=18,
        weight="bold",
    ),
)

quick_title.grid(
    row=0,
    column=0,
    sticky="w",
    padx=20,
    pady=(20, 14),
)


quick_buttons = []


# ============================================================
# CHAT HELPERS
# ============================================================

def add_chat_message(
    sender: str,
    message: str,
) -> None:

    chat_box.configure(
        state="normal",
    )

    chat_box.insert(
        "end",
        f"{sender}\n{message}\n\n",
    )

    chat_box.configure(
        state="disabled",
    )

    chat_box.see("end")


def add_activity(
    message: str,
) -> None:

    activity_box.configure(
        state="normal",
    )

    activity_box.insert(
        "end",
        f"{message}\n",
    )

    activity_box.configure(
        state="disabled",
    )

    activity_box.see("end")


def backend_activity(
    message: str,
) -> None:

    app.after(
        0,
        lambda msg=message: add_activity(msg),
    )


# ============================================================
# BUSY STATE
# ============================================================

def set_busy(
    busy: bool,
) -> None:

    if busy:

        send_button.configure(
            state="disabled",
            text="Thinking...",
        )

        status_text.configure(
            text="THINKING",
        )

        for button in quick_buttons:
            button.configure(
                state="disabled",
            )

    else:

        send_button.configure(
            state="normal",
            text="Send",
        )

        status_text.configure(
            text="LOCAL",
        )

        for button in quick_buttons:
            button.configure(
                state="normal",
            )


# ============================================================
# EXECUTE COMMAND
# ============================================================

def execute_command(
    command: str,
) -> None:

    try:

        result = process_command(
            command,
            activity_callback=backend_activity,
        )

        app.after(
            0,
            lambda result_text=result: add_chat_message(
                "TRAVEO",
                result_text,
            ),
        )

    except Exception as error:

        error_text = str(error)

        app.after(
            0,
            lambda text=error_text: add_chat_message(
                "SYSTEM",
                f"Error: {text}",
            ),
        )

        app.after(
            0,
            lambda text=error_text: add_activity(
                f"Error: {text}",
            ),
        )

    finally:

        app.after(
            0,
            lambda: set_busy(False),
        )

        app.after(
            0,
            lambda: command_entry.focus_set(),
        )


# ============================================================
# SEND COMMAND
# ============================================================

def send_command() -> None:

    command = command_entry.get().strip()

    if not command:
        return

    command_entry.delete(
        0,
        "end",
    )

    add_chat_message(
        "YOU",
        command,
    )

    add_activity(
        f"> {command}",
    )

    set_busy(True)

    worker = threading.Thread(
        target=execute_command,
        args=(command,),
        daemon=True,
    )

    worker.start()


send_button.configure(
    command=send_command,
)


# ============================================================
# ENTER KEY
# ============================================================

def handle_enter(event=None):

    send_command()

    # Prevent additional default processing
    return "break"


command_entry.bind(
    "<Return>",
    handle_enter,
)


# ============================================================
# QUICK ACTIONS
# ============================================================

def quick_command(
    command: str,
) -> None:

    command_entry.delete(
        0,
        "end",
    )

    command_entry.insert(
        0,
        command,
    )

    send_command()


open_vscode_button = ctk.CTkButton(
    side_panel,
    text="Open VS Code",
    height=43,
    corner_radius=10,
    fg_color=PANEL_LIGHT,
    hover_color="#19283C",
    border_width=1,
    border_color=BORDER,
    anchor="w",
    command=lambda: quick_command(
        "Open VS Code"
    ),
)

open_vscode_button.grid(
    row=1,
    column=0,
    sticky="ew",
    padx=20,
    pady=5,
)

quick_buttons.append(
    open_vscode_button
)


create_folder_button = ctk.CTkButton(
    side_panel,
    text="Create Demo Folder",
    height=43,
    corner_radius=10,
    fg_color=PANEL_LIGHT,
    hover_color="#19283C",
    border_width=1,
    border_color=BORDER,
    anchor="w",
    command=lambda: quick_command(
        "Create a folder called Traveo Demo on my desktop"
    ),
)

create_folder_button.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=20,
    pady=5,
)

quick_buttons.append(
    create_folder_button
)


organize_button = ctk.CTkButton(
    side_panel,
    text="Organize Downloads",
    height=43,
    corner_radius=10,
    fg_color=PANEL_LIGHT,
    hover_color="#19283C",
    border_width=1,
    border_color=BORDER,
    anchor="w",
    command=lambda: quick_command(
        "Organize my Downloads folder"
    ),
)

organize_button.grid(
    row=3,
    column=0,
    sticky="ew",
    padx=20,
    pady=5,
)

quick_buttons.append(
    organize_button
)


# ============================================================
# ACTIVITY PANEL
# ============================================================

activity_separator = ctk.CTkFrame(
    side_panel,
    height=1,
    fg_color=BORDER,
)

activity_separator.grid(
    row=4,
    column=0,
    sticky="ew",
    padx=20,
    pady=(22, 15),
)


activity_title = ctk.CTkLabel(
    side_panel,
    text="Tool Activity",
    text_color=TEXT,
    font=ctk.CTkFont(
        size=14,
        weight="bold",
    ),
)

activity_title.grid(
    row=5,
    column=0,
    sticky="w",
    padx=20,
    pady=(0, 8),
)


activity_box = ctk.CTkTextbox(
    side_panel,
    fg_color=PANEL_LIGHT,
    text_color=TEXT_SECONDARY,
    corner_radius=10,
    border_width=1,
    border_color=BORDER,
    font=ctk.CTkFont(
        family="Consolas",
        size=11,
    ),
    wrap="word",
)

activity_box.grid(
    row=6,
    column=0,
    sticky="nsew",
    padx=20,
    pady=(0, 20),
)

activity_box.insert(
    "end",
    "System ready.\n"
    f"Model: {MODEL}\n"
    "Runtime: Ollama\n\n",
)

activity_box.configure(
    state="disabled",
)


# ============================================================
# START APP
# ============================================================

command_entry.focus_set()

app.mainloop()