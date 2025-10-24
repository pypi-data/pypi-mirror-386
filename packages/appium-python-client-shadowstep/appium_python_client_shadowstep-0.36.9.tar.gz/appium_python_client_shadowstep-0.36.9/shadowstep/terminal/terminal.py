"""Terminal interface for Shadowstep framework.

This module provides the Terminal class for executing ADB commands
through Appium server, including device management, app operations,
input simulation, file operations.
"""

from __future__ import annotations

import base64
import logging
import re
import sys
import time
import traceback
from typing import TYPE_CHECKING, cast

from selenium.common import InvalidSessionIdException, NoSuchDriverException

from shadowstep.ui_automator.mobile_commands import MobileCommands
from shadowstep.utils.utils import get_current_func_name

# Configure the root logger (basic configuration)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
MIN_PS_COLUMNS_COUNT = 9

if TYPE_CHECKING:
    from appium.webdriver.webdriver import WebDriver

    from shadowstep.shadowstep import Shadowstep


class NotProvideCredentialsError(Exception):
    """Raised when SSH credentials are not provided for terminal connection.

    This exception is raised when attempting to establish a terminal
    connection without providing the required SSH credentials.
    """

    def __init__(
        self,
        message: str = "Not provided credentials for ssh connection "
        "in connect() method (ssh_username, ssh_password)",
    ) -> None:
        """Initialize the TerminalCredentialsError.

        Args:
            message: Error message describing the missing credentials.

        """
        super().__init__(message)
        self.message = message


class AdbShellError(Exception):
    """Adb_shell error."""


class Terminal:
    """Allows you to perform adb actions using the appium server. Useful for remote connections.

    Required ssh
    """

    shadowstep: Shadowstep
    driver: WebDriver

    def __init__(self) -> None:
        """Initialize the Terminal."""
        from shadowstep.shadowstep import Shadowstep  # noqa: PLC0415

        self.shadowstep: Shadowstep = Shadowstep.get_instance()
        self.driver: WebDriver = self.shadowstep.driver
        self.mobile_commands = MobileCommands()

    def adb_shell(self, command: str, args: str = "", tries: int = 3) -> str:
        """Execute commands via ADB on a mobile device."""
        for _ in range(tries):
            try:
                result = self.mobile_commands.shell({"command": command, "args": [args]})
                return cast("str", result)
            except NoSuchDriverException:  # noqa: PERF203
                logger.warning("No such driver found")
                self.shadowstep.reconnect()
            except InvalidSessionIdException:
                logger.warning("Invalid session id found")
                self.shadowstep.reconnect()
            except KeyError:
                logger.exception("KeyError in get_page_source")
                traceback_info = "".join(traceback.format_tb(sys.exc_info()[2]))
                logger.exception(traceback_info)
        msg = f"adb_shell failed after {tries} tries: {command} {args}"
        raise AdbShellError(msg)

    def start_activity(self, package: str, activity: str) -> bool:
        """Start activity on the device.

        :param package: The package name of the application.
        :param activity: The activity to start.
        :return: True if the activity was started successfully, False otherwise.
        :raises KeyError: If the command fails due to missing keys in the response.
        """
        try:
            self.adb_shell(command="am", args=f"start -n {package}/{activity}")
        except KeyError:
            logger.exception("appium_extended_terminal.start_activity()")
            return False
        else:
            return True

    def get_current_app_package(self) -> str:
        """Retrieve the package name of the currently focused application on the device.

        :return: The package name of the currently focused application, or None if it cannot be determined.
        """
        try:
            result = self.adb_shell(command="dumpsys", args="window windows")
            lines = result.split("\n")
            for line in lines:
                if "mCurrentFocus" in line or "mFocusedApp" in line:
                    matches = re.search(
                        r"(([A-Za-z]{1}[A-Za-z\d_]*\.)+([A-Za-z][A-Za-z\d_]*)/)",
                        line,
                    )
                    if matches:
                        return matches.group(1)[:-1]  # removing trailing slash
        except KeyError:
            logger.exception("appium_extended_terminal.get_current_app_package()")
            return ""
        else:
            return ""

    def close_app(self, package: str) -> bool:
        """Close the specified application on the device.

        :param package: The package name of the application to close.
        :return: True if the application was closed successfully, False otherwise.
        :raises KeyError: If the command fails due to missing keys in the response.
        """
        try:
            self.adb_shell(command="am", args=f"force-stop {package}")
        except KeyError:
            logger.exception("appium_extended_terminal.close_app()")
            return False
        else:
            return True

    def reboot_app(self, package: str, activity: str) -> bool:
        """Restarts the specified application on the device by closing it and then starting it again.

        :param package: The package name of the application to reboot.
        :param activity: The activity to start after rebooting the application.
        :return: True if the application was successfully rebooted, False otherwise.
        """
        if not self.close_app(package=package):
            return False
        return self.start_activity(package=package, activity=activity)

    def is_app_installed(self, package: str) -> bool:
        """Check if the specified application package is installed on the device.

        :param package: The package name of the application to check.
        :return: True if the application is installed, False otherwise.
        """
        logger.debug("is_app_installed() < package=%s", package)

        try:
            result = self.adb_shell(command="pm", args="list packages")
            if any(line.strip().endswith(package) for line in result.splitlines()):
                logger.debug("is_app_installed() > True")
                return True
            logger.debug("is_app_installed() > False")
        except KeyError:
            logger.exception("appium_extended_terminal.is_app_installed() > False")
            return False
        else:
            return False

    def uninstall_app(self, package: str) -> bool:
        """Uninstalls the specified application from the device.

        :param package: The package name of the application to uninstall.
        :return: True if the application was successfully uninstalled, False otherwise.
        """
        try:
            self.driver.remove_app(app_id=package)
        except NoSuchDriverException:
            self.shadowstep.reconnect()
            return False
        except InvalidSessionIdException:
            self.shadowstep.reconnect()
            return False
        except KeyError:
            logger.exception("appium_extended_terminal.uninstall_app()")
            return False
        else:
            return True

    def press_home(self) -> bool:
        """Simulate pressing the home button on the device.

        :return: True if the home button press was successfully simulated, False otherwise.
        """
        try:
            self.input_keycode(keycode="KEYCODE_HOME")
        except KeyError:
            logger.exception("appium_extended_terminal.press_home()")
            return False
        else:
            return True

    def press_back(self) -> bool:
        """Simulate pressing the back button on the device.

        :return: True if the back button press was successfully simulated, False otherwise.
        """
        try:
            self.input_keycode(keycode="KEYCODE_BACK")
        except KeyError:
            logger.exception("appium_extended_terminal.press_back()")
            return False
        else:
            return True

    def press_menu(self) -> bool:
        """Simulate pressing the menu button on the device.

        :return: True if the menu button press was successfully simulated, False otherwise.
        """
        try:
            self.input_keycode(keycode="KEYCODE_MENU")
        except KeyError:
            logger.exception("appium_extended_terminal.press_menu()")
            return False
        else:
            return True

    def input_keycode_num_(self, num: int) -> bool:
        """Send a numeric key event to the device using ADB.

        0-9, ADD, COMMA, DIVIDE, DOT, ENTER, EQUALS (read https://developer.android.com/reference/android/view/KeyEvent)

        :param num: The numeric value of the key to press.
        :return: True if the command was executed successfully, False otherwise.
        """
        try:
            self.adb_shell(command="input", args=f"keyevent KEYCODE_NUMPAD_{num}")
        except KeyError:
            logger.exception("appium_extended_terminal.input_keycode_num_()")
            return False
        else:
            return True

    def input_keycode(self, keycode: str) -> bool:
        """Send a key event to the device using ADB.

        :param keycode: The keycode to send to the device.
        :return: True if the command was executed successfully, False otherwise.
        """
        try:
            self.adb_shell(command="input", args=f"keyevent {keycode}")
        except KeyError:
            logger.exception("appium_extended_terminal.input_keycode()")
            return False
        else:
            return True

    def input_text(self, text: str) -> bool:
        """Input text on the device.

        :param text: The text to input.
        :return: True if the text was successfully inputted, False otherwise.
        """
        try:
            self.adb_shell(command="input", args=f"text {text}")
        except KeyError:
            logger.exception("appium_extended_terminal.input_text()")
            return False
        else:
            return True

    def tap(self, x: int, y: int) -> bool:
        """Simulate tapping at the specified coordinates on the device's screen.

        :param x: The x-coordinate of the tap.
        :param y: The y-coordinate of the tap.
        :return: True if the tap was successful, False otherwise.
        """
        try:
            self.adb_shell(command="input", args=f"tap {x!s} {y!s}")
        except KeyError:
            logger.exception("appium_extended_terminal.tap()")
            return False
        else:
            return True

    def swipe(
        self,
        start_x: str | int,
        start_y: str | int,
        end_x: str | int,
        end_y: str | int,
        duration: int = 300,
    ) -> bool:
        """Simulate a swipe gesture from one point to another on the device's screen.

        :param start_x: The x-coordinate of the starting point of the swipe.
        :param start_y: The y-coordinate of the starting point of the swipe.
        :param end_x: The x-coordinate of the ending point of the swipe.
        :param end_y: The y-coordinate of the ending point of the swipe.
        :param duration: The duration of the swipe in milliseconds (default is 300).
        :return: True if the swipe was successful, False otherwise.
        """
        try:
            self.adb_shell(
                command="input",
                args=f"swipe {start_x!s} {start_y!s} {end_x!s} {end_y!s} {duration!s}",
            )
        except KeyError:
            logger.exception("appium_extended_terminal.swipe()")
            return False
        else:
            return True

    def swipe_right_to_left(self, duration: int = 300) -> bool:
        """Simulate a swipe gesture from right to left on the device's screen.

        :param duration: The duration of the swipe in milliseconds (default is 300).
        :return: True if the swipe was successful, False otherwise.
        """
        window_size = self.get_screen_resolution()
        width = window_size[0]
        height = window_size[1]
        left = int(width * 0.1)
        right = int(width * 0.9)
        return self.swipe(
            start_x=right,
            start_y=height // 2,
            end_x=left,
            end_y=height // 2,
            duration=duration,
        )

    def swipe_left_to_right(self, duration: int = 300) -> bool:
        """Simulate a swipe gesture from left to right on the device's screen.

        :param duration: The duration of the swipe in milliseconds (default is 300).
        :return: True if the swipe was successful, False otherwise.
        """
        window_size = self.get_screen_resolution()
        width = window_size[0]
        height = window_size[1]
        left = int(width * 0.1)
        right = int(width * 0.9)
        return self.swipe(
            start_x=left,
            start_y=height // 2,
            end_x=right,
            end_y=height // 2,
            duration=duration,
        )

    def swipe_top_to_bottom(self, duration: int = 300) -> bool:
        """Simulate a swipe gesture from top to bottom on the device's screen.

        :param duration: The duration of the swipe in milliseconds (default is 300).
        :return: True if the swipe was successful, False otherwise.
        """
        window_size = self.get_screen_resolution()
        height = window_size[1]
        top = int(height * 0.1)
        bottom = int(height * 0.9)
        return self.swipe(
            start_x=top,
            start_y=height // 2,
            end_x=bottom,
            end_y=height // 2,
            duration=duration,
        )

    def swipe_bottom_to_top(self, duration: int = 300) -> bool:
        """Simulate a swipe gesture from bottom to top on the device's screen.

        :param duration: The duration of the swipe in milliseconds (default is 300).
        :return: True if the swipe was successful, False otherwise.
        """
        window_size = self.get_screen_resolution()
        height = window_size[1]
        top = int(height * 0.1)
        bottom = int(height * 0.9)
        return self.swipe(
            start_x=bottom,
            start_y=height // 2,
            end_x=top,
            end_y=height // 2,
            duration=duration,
        )

    def check_vpn(self, ip_address: str = "") -> bool:
        """Check if a VPN connection is established on the device.

        :param ip_address: Optional IP address to check for VPN connection (default is '').
        :return: True if a VPN connection is established, False otherwise.
        """
        try:
            output = self.adb_shell(command="netstat", args="")
            lines = output.split("\n")
            for line in lines:
                if ip_address in line and "ESTABLISHED" in line:
                    logger.debug("check_VPN() True")
                    return True
            logger.debug("check_VPN() False")
        except KeyError:
            logger.exception("appium_extended_terminal.check_VPN")
            return False
        else:
            return False

    def stop_logcat(self) -> bool:
        """Stop the logcat process running on the device.

        :return: True if the logcat process was successfully stopped, False otherwise.
        """
        try:
            process_list = self.adb_shell(command="ps", args="")
        except KeyError:
            logger.exception("appium_extended_terminal.stop_logcat")
            return False
        for process in process_list.splitlines():
            if "logcat" in process:
                pid = process.split()[1]
                try:
                    self.adb_shell(command="kill", args=f"-SIGINT {pid!s}")
                except KeyError:
                    logger.exception("appium_extended_terminal.stop_logcat")
                    traceback_info = "".join(traceback.format_tb(sys.exc_info()[2]))
                    logger.exception(traceback_info)
                    return False
        return True

    def know_pid(self, name: str) -> int | None:
        """Retrieve the process ID (PID) of the specified process name.

        :param name: The name of the process.
        :return: The PID of the process if found, None otherwise.
        """
        processes = self.adb_shell(command="ps")
        if name not in processes:
            logger.exception("know_pid() [Process not found]")
            return None
        lines = processes.strip().split("\n")
        for line in lines[1:]:
            columns = line.split()
            if len(columns) >= MIN_PS_COLUMNS_COUNT:
                pid, process_name = columns[1], columns[8]
                if name == process_name:
                    logger.debug("know_pid() > %s", pid)
                    return int(pid)
        logger.exception("know_pid() [Process not found]")
        return None

    def is_process_exist(self, name: str) -> bool:
        """Check if a process with the specified name exists.

        :param name: The name of the process.
        :return: True if the process exists, False otherwise.
        """
        processes = self.adb_shell(command="ps")
        if name not in processes:
            logger.debug("is_process_exist() > False")
            return False
        lines = processes.strip().split("\n")
        for line in lines[1:]:
            columns = line.split()
            if len(columns) >= MIN_PS_COLUMNS_COUNT:
                _, process_name = columns[1], columns[8]
                if name == process_name:
                    logger.debug("is_process_exist() > True")
                    return True
        logger.debug("is_process_exist() > False")
        return False

    def run_background_process(self, command: str, args: str = "", process: str = "") -> bool:
        """Run a background process on the device using the specified command.

        :param command: The command to run.
        :param args: Additional arguments for the command (default is "").
        :param process: The name of the process to check for existence (default is "").
        :return: True if the background process was successfully started, False otherwise.
        """
        logger.debug("run_background_process() < command=%s", command)

        try:
            self.adb_shell(command=command, args=args + " nohup > /dev/null 2>&1 &")
            if process != "":
                time.sleep(1)
                if not self.is_process_exist(name=process):
                    return False
        except KeyError:
            logger.exception("KeyError in is_app_installed")
            return False
        else:
            return True

    def kill_by_pid(self, pid: int) -> bool:
        """Kills the process with the specified PID.

        :param pid: The process ID (PID) of the process to kill.
        :return: True if the process was successfully killed, False otherwise.
        """
        try:
            self.adb_shell(command="kill", args=f"-s SIGINT {pid!s}")
        except KeyError:
            logger.exception("KeyError in kill_by_pid")
            return False
        return True

    def kill_by_name(self, name: str) -> bool:
        """Kills the process with the specified name.

        :param name: The name of the process to kill.
        :return: True if the process was successfully killed, False otherwise.
        """
        logger.debug("kill_by_name() < name=%s", name)
        try:
            self.adb_shell(command="pkill", args=f"-l SIGINT {name!s}")
        except KeyError:
            logger.exception("kill_by_name() > False")
            return False
        logger.debug("kill_by_name() > True")
        return True

    def kill_all(self, name: str) -> bool:
        """Kills all processes with the specified name.

        :param name: The name of the processes to kill.
        :return: True if the processes were successfully killed, False otherwise.
        """
        try:
            self.adb_shell(command="pkill", args=f"-f {name!s}")
        except KeyError:
            logger.exception("appium_extended_terminal.kill_all")
            return False
        return True

    def delete_files_from_internal_storage(self, path: str) -> bool:
        """Delete files from the internal storage of the device.

        :param path: The path of the files to delete.
        :return: True if the files were successfully deleted, False otherwise.
        """
        try:
            self.adb_shell(command="rm", args=f"-rf {path}*")
        except KeyError:
            logger.exception("appium_extended_terminal.delete_files_from_internal_storage")
            return False
        return True

    def delete_file_from_internal_storage(self, path: str, filename: str) -> bool:
        """Delete a file from the internal storage of the device.

        :param path: The path of the file's directory.
        :param filename: The name of the file to delete.
        :return: True if the file was successfully deleted, False otherwise.
        """
        try:
            path = path.removesuffix("/")
            self.adb_shell(command="rm", args=f"-rf {path}/{filename}")
        except KeyError:
            logger.exception("appium_extended_terminal.delete_file_from_internal_storage")
            return False
        return True

    def record_video(self, **options: str | float | bool) -> bool:
        """Record a video of the device screen (3 MIN MAX).

        :param options: Additional options for video recording.
        :return: True if the video recording started successfully, False otherwise.
        """
        try:
            self.driver.start_recording_screen(**options)
        except NoSuchDriverException:
            self.shadowstep.reconnect()
        except InvalidSessionIdException:
            self.shadowstep.reconnect()
        except KeyError:
            logger.exception("appium_extended_terminal.record_video")
            return False
        return True

    def stop_video(self, **options: str | float | bool) -> bytes | None:
        """Stop the video recording of the device screen and returns the recorded video data (Base64 bytes).

        :param options: Additional options for stopping the video recording.
        :return: The recorded video data as bytes if the recording stopped successfully, None otherwise.
        """
        try:
            str_based64_video = self.driver.stop_recording_screen(**options)
            return base64.b64decode(str_based64_video)
        except NoSuchDriverException:
            self.shadowstep.reconnect()
        except InvalidSessionIdException:
            self.shadowstep.reconnect()
        except KeyError:
            logger.exception("appium_extended_terminal.stop_video")
            return None

    def reboot(self) -> bool:
        """Reboot the device safely. If adb connection drops, ignores the error."""
        try:
            self.adb_shell(command="reboot")
        except Exception as e:  # noqa: BLE001
            logger.warning("Reboot likely initiated. Caught exception: %s", e)
        return True

    def get_screen_resolution(self) -> tuple[int, int]:
        """Retrieve the screen resolution of the device.

        :return: A tuple containing the width and height of the screen in pixels if successful,
                 or None if the resolution couldn't be retrieved.
        """
        try:
            output = self.adb_shell(command="wm", args="size")
            if "Physical size" in output:
                resolution_str = output.split(":")[1].strip()
                width, height = resolution_str.split("x")
                return int(width), int(height)
            logger.warning("%s: Physical size not in output", get_current_func_name())
        except Exception:
            logger.exception("Exception in get_screen_size")
            raise
        else:
            return 0, 0

    def past_text(self, text: str, tries: int = 3) -> None:
        """Place given text in clipboard, then paste it."""
        for _ in range(tries):
            try:
                self.driver.set_clipboard_text(text=text)
                self.input_keycode("279")
            except NoSuchDriverException:  # noqa: PERF203
                self.shadowstep.reconnect()
            except InvalidSessionIdException:
                self.shadowstep.reconnect()
            else:
                return

    def get_prop(self) -> dict[str, str]:
        """Retrieve system properties from the device.

        :return: A dictionary containing the system properties as key-value pairs.
        """
        raw_properties = self.adb_shell(command="getprop")
        lines = raw_properties.replace("\r", "").strip().split("\n")
        result_dict: dict[str, str] = {}
        for line in lines:
            try:
                key, value = line.strip().split(":", 1)
                key = key.strip()[1:-1]
                value = value.strip()[1:-1]
                result_dict[key] = value
            except ValueError:  # noqa: PERF203
                continue
        return result_dict

    def get_prop_hardware(self) -> str:
        """Retrieve the hardware information from the system properties of the device.

        :return: A string representing the hardware information.
        """
        return self.get_prop()["ro.boot.hardware"]

    def get_prop_model(self) -> str:
        """Retrieve the model name of the device from the system properties.

        :return: A string representing the model name of the device.
        """
        return self.get_prop()["ro.product.model"]

    def get_prop_serial(self) -> str:
        """Retrieve the serial number of the device from the system properties.

        :return: A string representing the serial number of the device.
        """
        return self.get_prop()["ro.serialno"]

    def get_prop_build(self) -> str:
        """Retrieve the build description from the system properties.

        :return: A string representing the build description of the device.
        """
        return self.get_prop()["ro.build.description"]

    def get_prop_device(self) -> str:
        """Retrieve the device name from the system properties.

        :return: A string representing the device name.
        """
        return self.get_prop()["ro.product.device"]

    def get_prop_uin(self) -> str:
        """Retrieve the unique identification number (UIN) from the system properties.

        :return: A string representing the unique identification number.
        """
        return self.get_prop()["sys.atol.uin"]

    def get_packages(self) -> list[str]:
        """Retrieve the list of installed packages on the device.

        :return: A list of package names.
        """
        output = self.adb_shell(command="pm", args="list packages")
        lines = output.strip().split("\n")
        return [line.split(":")[-1].replace("\r", "") for line in lines]

    def get_wifi_ip(self) -> str:
        """Retrieve Wi-Fi ip address of device.

        :return: ip address str.
        """
        output = self.adb_shell(command="ifconfig", args="")
        if "command not found" in output or "usage" in output.lower():
            # fallback to ip addr
            output = self.adb_shell(command="ip addr show wlan0", args="")
            return self._extract_ip_from_ip_addr(output)
        return self._extract_ip_from_ifconfig(output)

    def _extract_ip_from_ifconfig(self, output: str) -> str:
        blocks = output.split("\n\n")
        for block in blocks:
            if "wlan0" in block and "inet addr" in block:
                # Find IPv4
                match = re.search(r"inet addr:([\d.]+)", block)
                if match:
                    return match.group(1)
        msg = "Failed resolve IP address"
        raise AssertionError(msg)

    def _extract_ip_from_ip_addr(self, output: str) -> str:
        match = re.search(r"inet\s+([\d.]+)/\d+\s+brd.*wlan0", output)
        if match:
            return match.group(1)
        msg = "Failed resolve IP address"
        raise AssertionError(msg)
