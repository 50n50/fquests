import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    HAS_CTK = True
except Exception:
    HAS_CTK = False

from api import fetch_detectable_apps, search_apps, parse_app_executables
from runner import QuestRunner

class QuestSolverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FQuests")
        self.root.geometry("850x650")
        self.root.minsize(750, 550)

        self.apps_list = []
        self.selected_app = None
        self.selected_exec = None
        self.current_runner = None
        
        self.BG_DARK = "#1E1F22"
        self.BG_CARD = "#2B2D31"
        self.BG_INPUT = "#313338"
        self.ACCENT_BLURPLE = "#5865F2"
        self.COLOR_GREEN = "#23A55A"
        self.COLOR_RED = "#F23F43"
        self.COLOR_TEXT = "#F2F3F5"
        self.COLOR_MUTED = "#949BA4"

        if not HAS_CTK:
            self.root.configure(bg=self.BG_DARK)

        self.setup_ui()
        self.load_database_async()

    def setup_ui(self):
        if HAS_CTK:
            self.main_container = ctk.CTkFrame(self.root, fg_color=self.BG_DARK, corner_radius=0)
            self.main_container.pack(fill="both", expand=True)

            left_panel = ctk.CTkFrame(self.main_container, fg_color=self.BG_CARD, width=320, corner_radius=12)
            left_panel.pack(side="left", fill="both", padx=12, pady=12, expand=False)
            left_panel.pack_propagate(False)

            lbl_title = ctk.CTkLabel(left_panel, text="Discord Quest Solver", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.COLOR_TEXT)
            lbl_title.pack(anchor="w", padx=12, pady=(12, 4))

            lbl_sub = ctk.CTkLabel(left_panel, text="Select a game to start 15-min quest", font=ctk.CTkFont(size=12), text_color=self.COLOR_MUTED)
            lbl_sub.pack(anchor="w", padx=12, pady=(0, 8))

            self.search_var = tk.StringVar()
            self.search_var.trace_add("write", self.on_search_change)
            self.entry_search = ctk.CTkEntry(left_panel, placeholder_text="Search game or exe...", textvariable=self.search_var, fg_color=self.BG_INPUT, height=36)
            self.entry_search.pack(fill="x", padx=12, pady=(4, 8))

            lbl_results = ctk.CTkLabel(left_panel, text="Game Catalog:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.COLOR_TEXT)
            lbl_results.pack(anchor="w", padx=12, pady=(8, 2))

            list_frame = ctk.CTkFrame(left_panel, fg_color=self.BG_INPUT, corner_radius=8)
            list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            self.listbox = tk.Listbox(
                list_frame,
                bg=self.BG_INPUT,
                fg=self.COLOR_TEXT,
                selectbackground=self.ACCENT_BLURPLE,
                selectforeground="#FFFFFF",
                bd=0,
                highlightthickness=0,
                font=("Segoe UI", 10)
            )
            self.listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            scrollbar = ctk.CTkScrollbar(list_frame, command=self.listbox.yview)
            scrollbar.pack(side="right", fill="y")
            self.listbox.config(yscrollcommand=scrollbar.set)
            self.listbox.bind("<<ListboxSelect>>", self.on_select_game)

            right_panel = ctk.CTkFrame(self.main_container, fg_color=self.BG_CARD, corner_radius=12)
            right_panel.pack(side="right", fill="both", expand=True, padx=(0, 12), pady=12)

            self.lbl_game_title = ctk.CTkLabel(right_panel, text="No Game Selected", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.COLOR_TEXT)
            self.lbl_game_title.pack(anchor="w", padx=20, pady=(16, 2))

            self.lbl_game_id = ctk.CTkLabel(right_panel, text="Search and choose a game from the list on the left.", font=ctk.CTkFont(size=12), text_color=self.COLOR_MUTED)
            self.lbl_game_id.pack(anchor="w", padx=20, pady=(0, 10))

            exec_frame = ctk.CTkFrame(right_panel, fg_color=self.BG_INPUT, corner_radius=8)
            exec_frame.pack(fill="x", padx=20, pady=6)

            lbl_exec_name = ctk.CTkLabel(exec_frame, text="Target Executable:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.COLOR_TEXT)
            lbl_exec_name.pack(side="left", padx=12, pady=8)

            self.exec_combo = ctk.CTkComboBox(exec_frame, values=["(Select Game First)"], command=self.on_change_exec, fg_color=self.BG_DARK, button_color=self.ACCENT_BLURPLE)
            self.exec_combo.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            timer_card = ctk.CTkFrame(right_panel, fg_color=self.BG_INPUT, corner_radius=12)
            timer_card.pack(fill="x", padx=20, pady=12)

            self.lbl_status = ctk.CTkLabel(timer_card, text="STATUS: READY", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.COLOR_MUTED)
            self.lbl_status.pack(pady=(12, 0))

            self.lbl_timer = ctk.CTkLabel(timer_card, text="15:00", font=ctk.CTkFont(size=48, weight="bold"), text_color=self.COLOR_TEXT)
            self.lbl_timer.pack(pady=2)

            self.progress_bar = ctk.CTkProgressBar(timer_card, height=12, corner_radius=6, progress_color=self.ACCENT_BLURPLE)
            self.progress_bar.set(0.0)
            self.progress_bar.pack(fill="x", padx=24, pady=(4, 8))

            dur_frame = ctk.CTkFrame(timer_card, fg_color="transparent")
            dur_frame.pack(pady=(0, 12))

            lbl_dur = ctk.CTkLabel(dur_frame, text="Duration:", font=ctk.CTkFont(size=11), text_color=self.COLOR_MUTED)
            lbl_dur.pack(side="left", padx=(0, 8))

            self.dur_var = tk.StringVar(value="15")
            btn_15m = ctk.CTkRadioButton(dur_frame, text="15 Min (Quest)", value="15", variable=self.dur_var, command=self.update_timer_display, font=ctk.CTkFont(size=11))
            btn_15m.pack(side="left", padx=6)
            btn_5m = ctk.CTkRadioButton(dur_frame, text="5 Min", value="5", variable=self.dur_var, command=self.update_timer_display, font=ctk.CTkFont(size=11))
            btn_5m.pack(side="left", padx=6)
            btn_1m = ctk.CTkRadioButton(dur_frame, text="10 Sec (Test)", value="0.166", variable=self.dur_var, command=self.update_timer_display, font=ctk.CTkFont(size=11))
            btn_1m.pack(side="left", padx=6)

            self.auto_minimize_var = tk.BooleanVar(value=True)
            chk_minimize = ctk.CTkCheckBox(dur_frame, text="Hide GUI on Start", variable=self.auto_minimize_var, font=ctk.CTkFont(size=11))
            chk_minimize.pack(side="left", padx=(12, 6))

            btn_box = ctk.CTkFrame(right_panel, fg_color="transparent")
            btn_box.pack(fill="x", padx=20, pady=4)

            self.btn_start = ctk.CTkButton(
                btn_box,
                text="START QUEST",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=self.COLOR_GREEN,
                hover_color="#1E8A49",
                height=42,
                corner_radius=8,
                command=self.start_quest
            )
            self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 6))

            self.btn_cancel = ctk.CTkButton(
                btn_box,
                text="CANCEL QUEST",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=self.COLOR_RED,
                hover_color="#C03538",
                height=42,
                corner_radius=8,
                state="disabled",
                command=self.cancel_quest
            )
            self.btn_cancel.pack(side="right", fill="x", expand=True, padx=(6, 0))

            btn_tips = ctk.CTkButton(
                right_panel,
                text="Quest Progress Tips & Troubleshooting",
                font=ctk.CTkFont(size=11),
                fg_color=self.BG_INPUT,
                hover_color=self.ACCENT_BLURPLE,
                height=28,
                command=self.show_quest_tips
            )
            btn_tips.pack(fill="x", padx=20, pady=(6, 0))

            log_frame = ctk.CTkFrame(right_panel, fg_color=self.BG_INPUT, corner_radius=8)
            log_frame.pack(fill="both", expand=True, padx=20, pady=(12, 16))

            lbl_log = ctk.CTkLabel(log_frame, text="Activity Log:", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_MUTED)
            lbl_log.pack(anchor="w", padx=10, pady=(6, 2))

            self.txt_log = ctk.CTkTextbox(log_frame, fg_color=self.BG_DARK, text_color="#A3E635", font=ctk.CTkFont(family="Consolas", size=10))
            self.txt_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        else:
            lbl = tk.Label(self.root, text="Discord Activity Quest Solver", font=("Segoe UI", 16, "bold"), fg="#FFFFFF", bg=self.BG_DARK)
            lbl.pack(pady=20)

    def log(self, text):
        timestamp = time.strftime("[%H:%M:%S] ")
        msg = timestamp + text + "\n"
        if HAS_CTK:
            self.txt_log.insert("end", msg)
            self.txt_log.see("end")
        print(msg, end="")

    def load_database_async(self):
        def worker():
            self.log("Loading Discord detectable games API...")
            try:
                self.apps_list = fetch_detectable_apps()
                self.log(f"Successfully loaded {len(self.apps_list)} games from Discord database.")
                self.root.after(10, self.update_listbox)
            except Exception as e:
                self.log(f"Error loading API: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def update_listbox(self, filter_query=""):
        query = filter_query or self.search_var.get()
        results = search_apps(self.apps_list, query, limit=100)
        
        self.displayed_apps = results
        self.listbox.delete(0, tk.END)
        for app in results:
            execs = parse_app_executables(app)
            exec_str = f" [{execs[0]['name']}]" if execs else ""
            self.listbox.insert(tk.END, f"{app['name']}{exec_str}")

        if results and not self.selected_app:
            self.listbox.selection_set(0)
            self.on_select_game(None)

    def on_search_change(self, *args):
        self.update_listbox()

    def on_select_game(self, event):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.displayed_apps):
            return
        
        app = self.displayed_apps[sel[0]]
        self.selected_app = app
        execs = parse_app_executables(app)

        if HAS_CTK:
            self.lbl_game_title.configure(text=app['name'])
            self.lbl_game_id.configure(text=f"App ID: {app['id']}  |  Aliases: {', '.join(app.get('aliases', [])) or 'None'}")
            
            exec_names = [e['name'] for e in execs] if execs else ["game.exe"]
            self.exec_combo.configure(values=exec_names)
            self.exec_combo.set(exec_names[0])
            self.selected_exec = execs[0] if execs else {"name": "game.exe"}

            exec_rel_path = self.selected_exec['name']
            self.log(f"Selected: {app['name']} (Executable: {exec_rel_path})")

    def on_change_exec(self, choice):
        if not self.selected_app:
            return
        execs = parse_app_executables(self.selected_app)
        for e in execs:
            if e['name'] == choice:
                self.selected_exec = e
                self.log(f"Changed executable target to: {choice}")
                break

    def update_timer_display(self):
        try:
            mins = float(self.dur_var.get())
            secs = int(mins * 60)
            m, s = divmod(secs, 60)
            if HAS_CTK:
                self.lbl_timer.configure(text=f"{m:02d}:{s:02d}")
        except Exception:
            pass

    def start_quest(self):
        if not self.selected_app:
            messagebox.showwarning("No Game Selected", "Please select a game from the list first.")
            return

        if self.current_runner and self.current_runner.is_running:
            messagebox.showwarning("Quest Running", "A quest is already running. Please cancel or wait for it to finish.")
            return

        try:
            dur_mins = float(self.dur_var.get())
            target_secs = int(dur_mins * 60)
        except ValueError:
            target_secs = 900

        self.current_runner = QuestRunner(
            app_data=self.selected_app,
            exec_data=self.selected_exec,
            target_duration_secs=target_secs
        )

        self.current_runner.on_tick = self.on_quest_tick
        self.current_runner.on_complete = self.on_quest_complete
        self.current_runner.on_cancel = self.on_quest_cancel
        self.current_runner.on_process_exit = self.on_process_exit

        try:
            self.current_runner.start()
            
            if HAS_CTK:
                self.btn_start.configure(state="disabled", fg_color="#3F4248")
                self.btn_cancel.configure(state="normal", fg_color=self.COLOR_RED)
                self.lbl_status.configure(text="STATUS: RUNNING (QUEST ACTIVE)", text_color=self.COLOR_GREEN)

            self.log(f"Started quest solver for '{self.selected_app['name']}' ({target_secs} seconds)...")
            self.log(f"Executable path: {self.current_runner.target_exe_path}")

            if getattr(self, "auto_minimize_var", None) and self.auto_minimize_var.get():
                self.root.withdraw()
        except Exception as e:
            self.log(f"Failed to start quest: {e}")
            messagebox.showerror("Execution Error", str(e))

    def cancel_quest(self):
        if self.current_runner and self.current_runner.is_running:
            self.log("User triggered manual cancellation...")
            self.current_runner.cancel()

    def on_quest_tick(self, elapsed_secs, remaining_secs, status_str):
        def ui_update():
            m, s = divmod(remaining_secs, 60)
            total = self.current_runner.target_duration_secs
            progress = elapsed_secs / total if total > 0 else 0.0

            if HAS_CTK:
                self.lbl_timer.configure(text=f"{m:02d}:{s:02d}")
                self.progress_bar.set(progress)

        self.root.after(0, ui_update)

    def on_quest_complete(self, runner):
        def ui_update():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.root.attributes("-topmost", True)
                self.root.attributes("-topmost", False)
            except Exception:
                pass

            if HAS_CTK:
                self.lbl_timer.configure(text="00:00")
                self.progress_bar.set(1.0)
                self.lbl_status.configure(text="STATUS: QUEST COMPLETED!", text_color="#A3E635")
                self.btn_start.configure(state="normal", fg_color=self.COLOR_GREEN)
                self.btn_cancel.configure(state="disabled", fg_color="#3F4248")

            self.log(f"QUEST COMPLETED for '{runner.app_name}'! Process stopped & files cleaned up.")
            messagebox.showinfo("Quest Completed", f"Successfully ran {runner.app_name} for {runner.target_duration_secs // 60} minutes!\nYour Discord Quest is complete.")

        self.root.after(0, ui_update)

    def on_quest_cancel(self, runner):
        def ui_update():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass

            if HAS_CTK:
                self.lbl_status.configure(text="STATUS: CANCELLED", text_color=self.COLOR_RED)
                self.btn_start.configure(state="normal", fg_color=self.COLOR_GREEN)
                self.btn_cancel.configure(state="disabled", fg_color="#3F4248")
                self.update_timer_display()
                self.progress_bar.set(0.0)

            self.log(f"Quest cancelled for '{runner.app_name}'. Cleaned up executable & folders.")

        self.root.after(0, ui_update)

    def on_process_exit(self, runner):
        def ui_update():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass

            if HAS_CTK:
                self.lbl_status.configure(text="STATUS: STOPPED (Game Closed)", text_color=self.COLOR_RED)
                self.btn_start.configure(state="normal", fg_color=self.COLOR_GREEN)
                self.btn_cancel.configure(state="disabled", fg_color="#3F4248")
                self.update_timer_display()
                self.progress_bar.set(0.0)

            self.log(f"Game process for '{runner.app_name}' was closed externally. Quest timer stopped.")

        self.root.after(0, ui_update)

    def show_quest_tips(self):
        tips_text = (
            "DISCORD QUEST PROGRESS TROUBLESHOOTING TIPS:\n\n"
            "1. ACCEPT QUEST FIRST:\n"
            "   Open Discord > User Settings > Gift Inventory / Quests tab and click 'Accept Quest' before running the solver.\n\n"
            "2. PLAY vs. STREAM QUESTS:\n"
            "   - Play Quests: The solver opens a genuine game window named after the game (e.g., Roblox, Overwatch). Keep the spawned window open so Discord hooks into it.\n"
            "   - Stream Quests: If the quest requires streaming to a friend, join a Voice Call / Channel in Discord, click 'Share Screen', select the spawned game window, and stream it for 15 minutes.\n\n"
            "3. DISCORD PRIVACY SETTING:\n"
            "   Ensure Discord Settings > Data & Privacy > 'In-game Rewards (aka Quests)' is toggled ON.\n\n"
            "4. RESTART DISCORD:\n"
            "   If progress bar is still stuck, press Ctrl+R in Discord to reload the client while the game window is open."
        )
        messagebox.showinfo("Discord Quest Tips & Troubleshooting", tips_text)


def launch_gui():
    if HAS_CTK:
        root = ctk.CTk()
    else:
        root = tk.Tk()
    
    app = QuestSolverGUI(root)
    
    def on_close():
        if app.current_runner and app.current_runner.is_running:
            app.current_runner.cancel()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
