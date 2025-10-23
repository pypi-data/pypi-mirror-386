"""
UI Actions - Core UI interaction tools for Android device control.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from adbutils import adb
from llama_index.core.workflow import Context

from droidrun.agent.common.events import (
    DragActionEvent,
    InputTextActionEvent,
    KeyPressActionEvent,
    StartAppEvent,
    SwipeActionEvent,
    TapActionEvent,
)
from droidrun.tools.tools import Tools

from droidrun.tools.portal_client import PortalClient

logger = logging.getLogger("droidrun")
PORTAL_DEFAULT_TCP_PORT = 8080


class AdbTools(Tools):
    """Core UI interaction tools for Android device control."""

    def __init__(
        self,
        serial: str | None = None,
        use_tcp: bool = False,
        remote_tcp_port: int = PORTAL_DEFAULT_TCP_PORT,
        app_opener_llm=None,
        text_manipulator_llm=None,
        credential_manager=None,
    ) -> None:
        """Initialize the AdbTools instance.

        Args:
            serial: Device serial number
            use_tcp: Whether to use TCP communication (default: False)
            remote_tcp_port: TCP port for communication on device (default: 8080)
            app_opener_llm: LLM instance for app opening workflow (optional)
            text_manipulator_llm: LLM instance for text manipulation (optional)
            credential_manager: CredentialManager instance for secret handling (optional)
        """
        self.device = adb.device(serial=serial)

        self.portal = PortalClient(self.device, prefer_tcp=use_tcp)

        self._ctx = None
        # Instance‐level cache for clickable elements (index-based tapping)
        self.clickable_elements_cache: List[Dict[str, Any]] = []
        self.last_screenshot = None
        self.reason = None
        self.success = None
        self.finished = False
        # Memory storage for remembering important information
        self.memory: List[str] = []
        # Store all screenshots with timestamps
        self.screenshots: List[Dict[str, Any]] = []
        # Trajectory saving level
        self.save_trajectories = "none"

        # LLM instances for specialized workflows
        self.app_opener_llm = app_opener_llm
        self.text_manipulator_llm = text_manipulator_llm

        # Credential manager for secret handling
        self.credential_manager = credential_manager

        # Set up keyboard
        from droidrun.portal import setup_keyboard

        setup_keyboard(self.device)

    def get_date(self) -> str:
        """
        Get the current date and time on device.
        """
        return self.device.shell("date").strip()

    def _set_context(self, ctx: Context):
        self._ctx = ctx

    @Tools.ui_action
    def _extract_element_coordinates_by_index(self, index: int) -> Tuple[int, int]:
        """
        Extract center coordinates from an element by its index.

        Args:
            index: Index of the element to find and extract coordinates from

        Returns:
            Tuple of (x, y) center coordinates

        Raises:
            ValueError: If element not found, bounds format is invalid, or missing bounds
        """

        def collect_all_indices(elements):
            """Recursively collect all indices from elements and their children."""
            indices = []
            for item in elements:
                if item.get("index") is not None:
                    indices.append(item.get("index"))
                # Check children if present
                children = item.get("children", [])
                indices.extend(collect_all_indices(children))
            return indices

        def find_element_by_index(elements, target_index):
            """Recursively find an element with the given index."""
            for item in elements:
                if item.get("index") == target_index:
                    return item
                # Check children if present
                children = item.get("children", [])
                result = find_element_by_index(children, target_index)
                if result:
                    return result
            return None

        # Check if we have cached elements
        if not self.clickable_elements_cache:
            raise ValueError("No UI elements cached. Call get_state first.")

        # Find the element with the given index (including in children)
        element = find_element_by_index(self.clickable_elements_cache, index)

        if not element:
            # List available indices to help the user
            indices = sorted(collect_all_indices(self.clickable_elements_cache))
            indices_str = ", ".join(str(idx) for idx in indices[:20])
            if len(indices) > 20:
                indices_str += f"... and {len(indices) - 20} more"
            raise ValueError(
                f"No element found with index {index}. Available indices: {indices_str}"
            )

        # Get the bounds of the element
        bounds_str = element.get("bounds")
        if not bounds_str:
            element_text = element.get("text", "No text")
            element_type = element.get("type", "unknown")
            element_class = element.get("className", "Unknown class")
            raise ValueError(
                f"Element with index {index} ('{element_text}', {element_class}, type: {element_type}) has no bounds and cannot be tapped"
            )

        # Parse the bounds (format: "left,top,right,bottom")
        try:
            left, top, right, bottom = map(int, bounds_str.split(","))
        except ValueError as e:
            raise ValueError(
                f"Invalid bounds format for element with index {index}: {bounds_str}"
            ) from e

        # Calculate the center of the element
        x = (left + right) // 2
        y = (top + bottom) // 2

        return x, y

    def tap_by_index(self, index: int) -> str:
        """
        Tap on a UI element by its index.

        This function uses the cached clickable elements
        to find the element with the given index and tap on its center coordinates.

        Args:
            index: Index of the element to tap

        Returns:
            Result message
        """
        try:
            # Extract coordinates using the helper function
            x, y = self._extract_element_coordinates_by_index(index)

            # Get the device and tap at the coordinates
            self.device.click(x, y)
            print(f"Tapped element with index {index} at coordinates ({x}, {y})")

            # Emit coordinate action event for trajectory recording
            if self._ctx:
                # Find element again for event details
                def find_element_by_index(elements, target_index):
                    """Recursively find an element with the given index."""
                    for item in elements:
                        if item.get("index") == target_index:
                            return item
                        # Check children if present
                        children = item.get("children", [])
                        result = find_element_by_index(children, target_index)
                        if result:
                            return result
                    return None

                element = find_element_by_index(self.clickable_elements_cache, index)
                element_text = element.get("text", "No text") if element else "No text"
                element_class = (
                    element.get("className", "Unknown class")
                    if element
                    else "Unknown class"
                )
                bounds_str = element.get("bounds", "") if element else ""

                tap_event = TapActionEvent(
                    action_type="tap",
                    description=f"Tap element at index {index}: '{element_text}' ({element_class}) at coordinates ({x}, {y})",
                    x=x,
                    y=y,
                    element_index=index,
                    element_text=element_text,
                    element_bounds=bounds_str,
                )
                self._ctx.write_event_to_stream(tap_event)

            # Create a descriptive response
            def find_element_by_index(elements, target_index):
                """Recursively find an element with the given index."""
                for item in elements:
                    if item.get("index") == target_index:
                        return item
                    # Check children if present
                    children = item.get("children", [])
                    result = find_element_by_index(children, target_index)
                    if result:
                        return result
                return None

            element = find_element_by_index(self.clickable_elements_cache, index)
            response_parts = []
            response_parts.append(f"Tapped element with index {index}")
            response_parts.append(
                f"Text: '{element.get('text', 'No text') if element else 'No text'}'"
            )
            response_parts.append(
                f"Class: {element.get('className', 'Unknown class') if element else 'Unknown class'}"
            )
            response_parts.append(
                f"Type: {element.get('type', 'unknown') if element else 'unknown'}"
            )

            # Add information about children if present
            if element:
                children = element.get("children", [])
                if children:
                    child_texts = [
                        child.get("text") for child in children if child.get("text")
                    ]
                    if child_texts:
                        response_parts.append(
                            f"Contains text: {' | '.join(child_texts)}"
                        )

            response_parts.append(f"Coordinates: ({x}, {y})")

            return " | ".join(response_parts)
        except ValueError as e:
            return f"Error: {str(e)}"

    # Rename the old tap function to tap_by_coordinates for backward compatibility
    def tap_by_coordinates(self, x: int, y: int) -> bool:
        """
        Tap on the device screen at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Bool indicating success or failure
        """
        try:
            logger.debug(f"Tapping at coordinates ({x}, {y})")
            self.device.click(x, y)
            logger.debug(f"Tapped at coordinates ({x}, {y})")
            return True
        except ValueError as e:
            logger.debug(f"Error: {str(e)}")
            return False

    # Replace the old tap function with the new one
    def tap(self, index: int) -> str:
        """
        Tap on a UI element by its index.

        This function uses the cached clickable elements from the last get_clickables call
        to find the element with the given index and tap on its center coordinates.

        Args:
            index: Index of the element to tap

        Returns:
            Result message
        """
        return self.tap_by_index(index)

    @Tools.ui_action
    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: float = 1000,
    ) -> bool:
        """
        Performs a straight-line swipe gesture on the device screen.
        To perform a hold (long press), set the start and end coordinates to the same values and increase the duration as needed.
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration_ms: Duration of swipe in milliseconds
        Returns:
            Bool indicating success or failure
        """
        try:
            if self._ctx:
                swipe_event = SwipeActionEvent(
                    action_type="swipe",
                    description=f"Swipe from ({start_x}, {start_y}) to ({end_x}, {end_y}) in {duration_ms} milliseconds",
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    duration_ms=duration_ms,
                )
                self._ctx.write_event_to_stream(swipe_event)

            self.device.swipe(start_x, start_y, end_x, end_y, float(duration_ms / 1000))
            time.sleep(duration_ms / 1000)
            print(
                f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y}) in {duration_ms} milliseconds"
            )
            return True
        except ValueError as e:
            print(f"Error: {str(e)}")
            return False

    @Tools.ui_action
    def drag(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 3
    ) -> bool:
        """
        Performs a straight-line drag and drop gesture on the device screen.
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Duration of swipe in seconds
        Returns:
            Bool indicating success or failure
        """
        try:
            logger.debug(
                f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y}) in {duration} seconds"
            )
            self.device.drag(start_x, start_y, end_x, end_y, duration)

            if self._ctx:
                drag_event = DragActionEvent(
                    action_type="drag",
                    description=f"Drag from ({start_x}, {start_y}) to ({end_x}, {end_y}) in {duration} seconds",
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    duration=duration,
                )
                self._ctx.write_event_to_stream(drag_event)

            time.sleep(duration)
            logger.debug(
                f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y}) in {duration} seconds"
            )
            return True
        except ValueError as e:
            print(f"Error: {str(e)}")
            return False

    @Tools.ui_action
    def input_text(self, text: str, index: int = -1, clear: bool = False) -> str:
        """
        Input text on the device.
        Always make sure that the Focused Element is not None before inputting text.

        Args:
            text: Text to input. Can contain spaces, newlines, and special characters including non-ASCII.
            index: Index of the element to input text into. If -1, the focused element will be used.
            clear: Whether to clear the text before inputting.

        Returns:
            Result message
        """
        try:
            if index != -1:
                self.tap_by_index(index)

            # Use PortalClient for text input (automatic TCP/content provider selection)
            success = self.portal.input_text(text, clear)

            if self._ctx:
                input_event = InputTextActionEvent(
                    action_type="input_text",
                    description=f"Input text: '{text[:50]}{'...' if len(text) > 50 else ''}' (clear={clear})",
                    text=text,
                )
                self._ctx.write_event_to_stream(input_event)

            if success:
                print(
                    f"Text input completed (clear={clear}): {text[:50]}{'...' if len(text) > 50 else ''}"
                )
                return f"Text input completed (clear={clear}): {text[:50]}{'...' if len(text) > 50 else ''}"
            else:
                return "Error: Text input failed"

        except Exception as e:
            return f"Error sending text input: {str(e)}"

    @Tools.ui_action
    def back(self) -> str:
        """
        Go back on the current view.
        This presses the Android back button.
        """
        try:
            print("Pressing key BACK")
            self.device.keyevent(4)

            if self._ctx:
                key_event = KeyPressActionEvent(
                    action_type="key_press",
                    description="Pressed key BACK",
                    keycode=4,
                    key_name="BACK",
                )
                self._ctx.write_event_to_stream(key_event)

            return "Pressed key BACK"
        except ValueError as e:
            return f"Error: {str(e)}"

    @Tools.ui_action
    def press_key(self, keycode: int) -> str:
        """
        Press a key on the Android device.

        Common keycodes:
        - 3: HOME
        - 4: BACK
        - 66: ENTER
        - 67: DELETE

        Args:
            keycode: Android keycode to press
        """
        try:
            key_names = {
                66: "ENTER",
                4: "BACK",
                3: "HOME",
                67: "DELETE",
            }
            key_name = key_names.get(keycode, str(keycode))

            if self._ctx:
                key_event = KeyPressActionEvent(
                    action_type="key_press",
                    description=f"Pressed key {key_name}",
                    keycode=keycode,
                    key_name=key_name,
                )
                self._ctx.write_event_to_stream(key_event)

            self.device.keyevent(keycode)
            print(f"Pressed key {key_name}")
            return f"Pressed key {key_name}"
        except ValueError as e:
            return f"Error: {str(e)}"

    @Tools.ui_action
    def start_app(self, package: str, activity: str | None = None) -> str:
        """
        Start an app on the device.

        Args:
            package: Package name (e.g., "com.android.settings")
            activity: Optional activity name
        """
        try:
            print(f"Starting app {package} with activity {activity}")
            if not activity:
                dumpsys_output = self.device.shell(
                    f"cmd package resolve-activity --brief {package}"
                )
                activity = dumpsys_output.splitlines()[1].split("/")[1]

            if self._ctx:
                start_app_event = StartAppEvent(
                    action_type="start_app",
                    description=f"Start app {package}",
                    package=package,
                    activity=activity,
                )
                self._ctx.write_event_to_stream(start_app_event)

            print(f"Activity: {activity}")

            self.device.app_start(package, activity)
            print(f"App started: {package} with activity {activity}")
            return f"App started: {package} with activity {activity}"
        except Exception as e:
            return f"Error: {str(e)}"

    def install_app(
        self, apk_path: str, reinstall: bool = False, grant_permissions: bool = True
    ) -> str:
        """
        Install an app on the device.

        Args:
            apk_path: Path to the APK file
            reinstall: Whether to reinstall if app exists
            grant_permissions: Whether to grant all permissions
        """
        try:
            if not os.path.exists(apk_path):
                return f"Error: APK file not found at {apk_path}"

            logger.debug(
                f"Installing app: {apk_path} with reinstall: {reinstall} and grant_permissions: {grant_permissions}"
            )
            result = self.device.install(
                apk_path,
                nolaunch=True,
                uninstall=reinstall,
                flags=["-g"] if grant_permissions else [],
                silent=True,
            )
            logger.debug(f"Installed app: {apk_path} with result: {result}")
            return result
        except ValueError as e:
            return f"Error: {str(e)}"

    def take_screenshot(self, hide_overlay: bool = True) -> Tuple[str, bytes]:
        """
        Take a screenshot of the device.
        This function captures the current screen and returns the screenshot data.
        Also stores the screenshot in the screenshots list with timestamp for later GIF creation.

        Args:
            hide_overlay: Whether to hide the Portal overlay elements during screenshot (default: True)

        Returns:
            Tuple of (format, image_bytes) where format is "PNG" and image_bytes is the screenshot data
        """
        try:
            logger.debug("Taking screenshot")

            image_bytes = self.portal.take_screenshot(hide_overlay)

            # Store screenshot with timestamp
            self.screenshots.append(
                {
                    "timestamp": time.time(),
                    "image_data": image_bytes,
                    "format": "PNG",
                }
            )
            return "PNG", image_bytes

        except Exception as e:
            raise ValueError(f"Error taking screenshot: {str(e)}") from e

    def list_packages(self, include_system_apps: bool = False) -> List[str]:
        """
        List installed packages on the device.

        Args:
            include_system_apps: Whether to include system apps (default: False)

        Returns:
            List of package names
        """
        try:
            logger.debug("Listing packages")
            return self.device.list_packages(["-3"] if not include_system_apps else [])
        except ValueError as e:
            raise ValueError(f"Error listing packages: {str(e)}") from e

    def get_apps(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        Get installed apps with package name and label in human readable format.

        Args:
            include_system: Whether to include system apps (default: True)

        Returns:
            List of dictionaries containing 'package' and 'label' keys
        """
        return self.portal.get_apps(include_system)

    @Tools.ui_action
    def complete(self, success: bool, reason: str = ""):
        """
        Mark the task as finished.

        Args:
            success: Indicates if the task was successful.
            reason: Reason for failure/success
        """
        if success:
            self.success = True
            self.reason = reason or "Task completed successfully."
            self.finished = True
        else:
            self.success = False
            if not reason:
                raise ValueError("Reason for failure is required if success is False.")
            self.reason = reason
            self.finished = True

    def remember(self, information: str) -> str:
        """
        Store important information to remember for future context.

        This information will be extracted and included into your next steps to maintain context
        across interactions. Use this for critical facts, observations, or user preferences
        that should influence future decisions.

        Args:
            information: The information to remember

        Returns:
            Confirmation message
        """
        if not information or not isinstance(information, str):
            return "Error: Please provide valid information to remember."

        # Add the information to memory
        self.memory.append(information.strip())

        # Limit memory size to prevent context overflow (keep most recent items)
        max_memory_items = 10
        if len(self.memory) > max_memory_items:
            self.memory = self.memory[-max_memory_items:]

        return f"Remembered: {information}"

    def get_memory(self) -> List[str]:
        """
        Retrieve all stored memory items.

        Returns:
            List of stored memory items
        """
        return self.memory.copy()

    def get_state(self) -> Dict[str, Any]:
        """
        Get both the a11y tree and phone state in a single call using the combined /state endpoint.

        Returns:
            Dictionary containing both 'a11y_tree' and 'phone_state' data
        """
        try:
            logger.debug("Getting state")

            # Use PortalClient for state (automatic TCP/content provider selection)
            combined_data = self.portal.get_state()

            # Handle error responses
            if "error" in combined_data:
                return combined_data

            # Validate that both a11y_tree and phone_state are present
            if "a11y_tree" not in combined_data:
                return {
                    "error": "Missing Data",
                    "message": "a11y_tree not found in combined state data",
                }

            if "phone_state" not in combined_data:
                return {
                    "error": "Missing Data",
                    "message": "phone_state not found in combined state data",
                }

            # Filter out the "type" attribute from all a11y_tree elements
            elements = combined_data["a11y_tree"]
            filtered_elements = []
            for element in elements:
                # Create a copy of the element without the "type" attribute
                filtered_element = {k: v for k, v in element.items() if k != "type"}

                # Also filter children if present
                if "children" in filtered_element:
                    filtered_element["children"] = [
                        {k: v for k, v in child.items() if k != "type"}
                        for child in filtered_element["children"]
                    ]

                filtered_elements.append(filtered_element)

            self.clickable_elements_cache = filtered_elements

            return {
                "a11y_tree": filtered_elements,
                "phone_state": combined_data["phone_state"],
            }

        except Exception as e:
            return {
                "error": str(e),
                "message": f"Error getting combined state: {str(e)}",
            }

    def ping(self) -> Dict[str, Any]:
        """
        Test the Portal connection.

        Returns:
            Dictionary with ping result
        """
        return self.portal.ping()


def _shell_test_cli(serial: str, command: str) -> tuple[str, float]:
    """
    Run an adb shell command using the adb CLI and measure execution time.
    Args:
        serial: Device serial number
        command: Shell command to run
    Returns:
        Tuple of (output, elapsed_time)
    """
    import subprocess
    import time

    adb_cmd = ["adb", "-s", serial, "shell", command]
    start = time.perf_counter()
    result = subprocess.run(adb_cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    output = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    return output, elapsed


def _shell_test():
    device = adb.device("emulator-5554")
    # Native Python adb client
    start = time.time()
    res = device.shell("echo 'Hello, World!'")
    end = time.time()
    print(f"[Native] Shell execution took {end - start:.3f} seconds: {res}")

    start = time.time()
    res = device.shell("content query --uri content://com.droidrun.portal/state")
    end = time.time()
    print(f"[Native] Shell execution took {end - start:.3f} seconds: phone_state")

    # CLI version
    output, elapsed = _shell_test_cli("emulator-5554", "echo 'Hello, World!'")
    print(f"[CLI] Shell execution took {elapsed:.3f} seconds: {output}")

    output, elapsed = _shell_test_cli(
        "emulator-5554", "content query --uri content://com.droidrun.portal/state"
    )
    print(f"[CLI] Shell execution took {elapsed:.3f} seconds: phone_state")


def _list_packages():
    tools = AdbTools()
    print(tools.list_packages())


def _start_app():
    tools = AdbTools()
    tools.start_app("com.android.settings", ".Settings")


def _shell_test_cli(serial: str, command: str) -> tuple[str, float]:
    """
    Run an adb shell command using the adb CLI and measure execution time.
    Args:
        serial: Device serial number
        command: Shell command to run
    Returns:
        Tuple of (output, elapsed_time)
    """
    import subprocess
    import time

    adb_cmd = ["adb", "-s", serial, "shell", command]
    start = time.perf_counter()
    result = subprocess.run(adb_cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    output = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    return output, elapsed


def _shell_test():
    device = adb.device("emulator-5554")
    # Native Python adb client
    start = time.time()
    res = device.shell("echo 'Hello, World!'")
    end = time.time()
    print(f"[Native] Shell execution took {end - start:.3f} seconds: {res}")

    start = time.time()
    res = device.shell("content query --uri content://com.droidrun.portal/state")
    end = time.time()
    print(f"[Native] Shell execution took {end - start:.3f} seconds: phone_state")

    # CLI version
    output, elapsed = _shell_test_cli("emulator-5554", "echo 'Hello, World!'")
    print(f"[CLI] Shell execution took {elapsed:.3f} seconds: {output}")

    output, elapsed = _shell_test_cli(
        "emulator-5554", "content query --uri content://com.droidrun.portal/state"
    )
    print(f"[CLI] Shell execution took {elapsed:.3f} seconds: phone_state")


def _list_packages():
    tools = AdbTools()
    print(tools.list_packages())


def _start_app():
    tools = AdbTools()
    tools.start_app("com.android.settings", ".Settings")


if __name__ == "__main__":
    _start_app()
