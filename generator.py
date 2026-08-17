import os
import sys
import subprocess
import shutil

DUMMY_CS_SOURCE = """using System;
using System.Drawing;
using System.Threading;
using System.Windows.Forms;

class Program {
    [STAThread]
    static void Main(string[] args) {
        string windowTitle = args.Length > 0 ? args[0] : "Game Window";
        
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        
        Form gameForm = new Form();
        gameForm.Text = windowTitle;
        gameForm.Size = new Size(1280, 720);
        gameForm.StartPosition = FormStartPosition.CenterScreen;
        gameForm.BackColor = Color.FromArgb(20, 20, 25);
        
        Label statusLabel = new Label();
        statusLabel.Text = "Discord Quest Active: " + windowTitle + "\\n\\nKeep this window open for 15 minutes to complete your quest!";
        statusLabel.Font = new Font("Segoe UI", 16, FontStyle.Bold);
        statusLabel.ForeColor = Color.FromArgb(240, 240, 245);
        statusLabel.Dock = DockStyle.Fill;
        statusLabel.TextAlign = ContentAlignment.MiddleCenter;
        
        gameForm.Controls.Add(statusLabel);
        
        Application.Run(gameForm);
    }
}
"""

DUMMY_BASE_EXE = "dummy_base.exe"

def find_csc_compiler():
    possible_paths = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework64\v3.5\csc.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    csc_path = shutil.which("csc")
    if csc_path:
        return csc_path
        
    return None

def build_dummy_base(target_exe=DUMMY_BASE_EXE):
    if os.path.exists(target_exe):
        return os.path.abspath(target_exe)

    csc_compiler = find_csc_compiler()
    if not csc_compiler:
        raise RuntimeError("Windows .NET C# compiler (csc.exe) not found on system.")

    temp_cs_file = "temp_dummy_source.cs"
    try:
        with open(temp_cs_file, "w", encoding="utf-8") as f:
            f.write(DUMMY_CS_SOURCE)

        cmd = [
            csc_compiler,
            "/nologo",
            "/target:winexe",
            "/r:System.Windows.Forms.dll",
            "/r:System.Drawing.dll",
            f"/out:{target_exe}",
            temp_cs_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"csc.exe compilation failed: {result.stderr or result.stdout}")

        return os.path.abspath(target_exe)
    finally:
        if os.path.exists(temp_cs_file):
            try:
                os.remove(temp_cs_file)
            except Exception:
                pass

if __name__ == "__main__":
    if os.path.exists(DUMMY_BASE_EXE):
        os.remove(DUMMY_BASE_EXE)
    exe_path = build_dummy_base()
    print("Compiled dummy exe at:", exe_path)
