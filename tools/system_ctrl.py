import os
import subprocess
import shutil
import psutil
import logging
from config import Config

logger = logging.getLogger(__name__)

class SystemTools:
    def __init__(self):
        self.is_windows = Config.is_windows()
        self.is_macos = Config.is_macos()

    def run_command(self, command):
        """Executes a shell command and returns output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return f"Error: {e.stderr}"

    def manage_packages(self, action, package_name):
        """
        Manages software packages.
        action: 'install', 'uninstall'
        """
        if self.is_windows:
            pkg_manager = "winget"
            # Winget arguments vary slightly, simple install:
            cmd = f"winget {action} {package_name}"
            # Note: winget often needs confirmation, might need --accept-source-agreements etc.
            if action == "install":
                cmd += " --silent --accept-package-agreements --accept-source-agreements"
        elif self.is_macos:
            pkg_manager = "brew"
            cmd = f"brew {action} {package_name}"
        else:
            pkg_manager = "pip" # Fallback or Linux
            cmd = f"pip {action} {package_name}"

        logger.info(f"Running package manager: {cmd}")
        return self.run_command(cmd)

    def check_health(self):
        """Returns system health stats."""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery()

        status = f"CPU Load: {cpu}%\nMemory Used: {memory.percent}%"
        if battery:
            status += f"\nBattery: {battery.percent}% ({'Charging' if battery.power_plugged else 'Discharging'})"

        return status

    def compile_rom(self, script_name):
        """
        Triggers a build script from the build_scripts/ directory.
        """
        script_path = os.path.join(Config.BUILD_SCRIPTS_DIR, script_name)

        if not os.path.exists(script_path):
            return f"Script {script_name} not found in {Config.BUILD_SCRIPTS_DIR}. Are you hallucinating files again? 🧐"

        # Check if executable
        if not os.access(script_path, os.X_OK) and not self.is_windows:
             # Make executable
             os.chmod(script_path, 0o755)

        logger.info(f"Starting ROM build: {script_path}")

        # We might want to run this in background or blocking. For now blocking to capture output.
        # But ROM builds are long.
        # AGENTS.md says "trigger local shell scripts".
        # Better to run in background and return a "Started" message.

        try:
            # Running as detached process
            if self.is_windows:
                # 'start' command in shell
                subprocess.Popen(["start", "cmd", "/k", script_path], shell=True)
            else:
                # MacOS/Linux: open in new terminal or just run in background?
                # "open -a Terminal script_path" executes it in a new window on macOS
                if self.is_macos:
                     subprocess.Popen(["open", "-a", "Terminal", script_path])
                else:
                     subprocess.Popen([script_path], shell=True)

            return f"Started build script: {script_name}. Time to grab a coffee! ☕"
        except Exception as e:
            logger.error(f"Failed to start build: {e}")
            return f"Failed to launch build: {e}"

    def open_app(self, app_name):
        """Opens an application."""
        # Using simple system commands instead of PyAutoGUI for opening apps as it's more reliable for just launching
        if self.is_macos:
            return self.run_command(f"open -a '{app_name}'")
        elif self.is_windows:
            # Using start command
            return self.run_command(f"start {app_name}")
        else:
            return "I don't know how to open apps on this OS yet."

    def get_process_list(self):
        """Optional: List top processes"""
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent']):
            try:
                procs.append(p.info)
            except:
                pass
        # Sort by CPU
        procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return procs[:5]
