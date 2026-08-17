import os
import sys
import time
import shutil
import subprocess
import threading
import winsound
import ctypes
from generator import build_dummy_base

try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
except Exception:
    toaster = None

def notify_user(title, message):
    print(f"[NOTIFICATION] {title}: {message}")
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    if toaster:
        try:
            threading.Thread(
                target=lambda: toaster.show_toast(title, message, duration=5, threaded=True),
                daemon=True
            ).start()
            return
        except Exception:
            pass

    def show_fallback():
        try:
            ps_script = f'''
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.Visible = $true
            $notify.ShowBalloonTip(5000, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info)
            '''
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
        except Exception:
            pass

    threading.Thread(target=show_fallback, daemon=True).start()


class QuestRunner:
    def __init__(self, app_data, exec_data=None, run_dir=None, target_duration_secs=900):
        self.app_data = app_data
        self.app_name = app_data.get("name", "Unknown Game")
        self.app_id = app_data.get("id", "")
        
        if not exec_data:
            execs = app_data.get("executables", [])
            win_execs = [e for e in execs if e.get("os", "").lower() in ["win32", "win64", "windows", ""] or not e.get("os")]
            exec_data = win_execs[0] if win_execs else (execs[0] if execs else {"name": "game.exe"})
        
        self.exec_rel_path = exec_data.get("name", "game.exe").replace("/", os.sep).replace("\\", os.sep)
        self.base_dir = os.path.abspath(run_dir or os.getcwd())
        self.target_exe_path = os.path.normpath(os.path.join(self.base_dir, self.exec_rel_path))
        self.created_dirs = []
        
        self.target_duration_secs = target_duration_secs
        self.elapsed_secs = 0
        self.is_running = False
        self.is_paused = False
        self.is_completed = False
        self.is_cancelled = False
        
        self.process = None
        self.timer_thread = None
        
        self.on_tick = None
        self.on_complete = None
        self.on_cancel = None
        self.on_process_exit = None

    def prepare_executable(self):
        dummy_base = build_dummy_base()
        target_dir = os.path.dirname(self.target_exe_path)
        
        curr = target_dir
        dirs_to_create = []
        while curr and curr != self.base_dir and not os.path.exists(curr):
            dirs_to_create.append(curr)
            curr = os.path.dirname(curr)
            
        dirs_to_create.reverse()
        for d in dirs_to_create:
            os.makedirs(d, exist_ok=True)
            self.created_dirs.append(d)
            
        shutil.copy2(dummy_base, self.target_exe_path)

    def start(self):
        if self.is_running:
            return

        self.prepare_executable()
        
        try:
            self.process = subprocess.Popen(
                [self.target_exe_path, self.app_name],
                cwd=os.path.dirname(self.target_exe_path)
            )
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to spawn dummy process: {e}")

        self.is_running = True
        self.is_completed = False
        self.is_cancelled = False
        self.elapsed_secs = 0

        self.timer_thread = threading.Thread(target=self._run_timer_loop, daemon=True)
        self.timer_thread.start()

    def _run_timer_loop(self):
        while self.is_running and self.elapsed_secs < self.target_duration_secs:
            if self.process and self.process.poll() is not None:
                self.is_running = False
                self.cleanup()
                if hasattr(self, "on_process_exit") and self.on_process_exit:
                    try:
                        self.on_process_exit(self)
                    except Exception:
                        pass
                return

            if not self.is_paused:
                time.sleep(1)
                self.elapsed_secs += 1
                
                remaining = self.target_duration_secs - self.elapsed_secs
                status = f"Running: {self.app_name}"
                
                if self.on_tick:
                    try:
                        self.on_tick(self.elapsed_secs, max(0, remaining), status)
                    except Exception:
                        pass
            else:
                time.sleep(0.5)

        if self.is_running and self.elapsed_secs >= self.target_duration_secs:
            self.is_completed = True
            self.is_running = False
            
            self.cleanup()
            
            notify_user("Discord Quest Completed!", f"Successfully ran {self.app_name} for 15 minutes. Quest complete!")
            
            if self.on_complete:
                try:
                    self.on_complete(self)
                except Exception as e:
                    pass

    def cancel(self):
        if not self.is_running and not self.process:
            return

        self.is_cancelled = True
        self.is_running = False
        
        self.cleanup()
        
        notify_user("Discord Quest Cancelled", f"Stopped quest session for {self.app_name}.")
        
        if self.on_cancel:
            try:
                self.on_cancel(self)
            except Exception as e:
                pass

    def cleanup(self):
        if self.process:
            try:
                if self.process.poll() is None:
                    self.process.terminate()
                    time.sleep(0.3)
                    if self.process.poll() is None:
                        self.process.kill()
            except Exception:
                pass
            finally:
                self.process = None

        if os.path.exists(self.target_exe_path):
            try:
                os.remove(self.target_exe_path)
            except Exception:
                pass

        for d in self.created_dirs:
            if os.path.exists(d):
                try:
                    if not os.listdir(d):
                        os.rmdir(d)
                except Exception:
                    pass

if __name__ == "__main__":
    test_app = {
        "id": "356875221078245376",
        "name": "Overwatch",
        "executables": [{"name": "test_game_folder/overwatch.exe", "os": "win32"}]
    }
    runner = QuestRunner(test_app, target_duration_secs=5)
    runner.start()
    time.sleep(7)
