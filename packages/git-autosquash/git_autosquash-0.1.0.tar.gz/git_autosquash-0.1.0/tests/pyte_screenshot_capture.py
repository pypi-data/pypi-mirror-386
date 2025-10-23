"""
Pyte-based TUI Screenshot Capture System

⚠️  DEPRECATED: This approach had timing and reliability issues.
    Use scripts/generate_screenshots.py for Textual-native screenshots.
    See CLAUDE.md "Screenshot Generation" section for details.

This module provides screenshot capture using the pyte terminal emulator,
which allows us to capture TUI output as text/ANSI without relying on
Textual's private screenshot APIs.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any
from contextlib import contextmanager
import subprocess
import tempfile

import pyte
from PIL import Image, ImageDraw, ImageFont


class PyteScreenshotCapture:
    """
    Screenshot capture using pyte terminal emulator.

    This approach runs the TUI application in a subprocess and captures
    its terminal output using pyte, then converts it to images.
    """

    def __init__(self, output_dir: Path, terminal_size: tuple = (120, 40)):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.terminal_size = terminal_size  # (columns, rows)
        self.screenshot_counter = 0

    async def capture_app_flow(
        self,
        app_command: List[str],
        interactions: List[Dict[str, Any]] | None = None,
        scenario_name: str = "app",
    ) -> List[Path]:
        """
        Capture screenshots of an application flow.

        Args:
            app_command: Command to run the application (e.g., ['git-autosquash'])
            interactions: List of interactions to simulate
            scenario_name: Name for the screenshot series

        Returns:
            List of screenshot file paths
        """
        screenshots: List[Path] = []

        # Create a virtual terminal
        screen = pyte.Screen(self.terminal_size[0], self.terminal_size[1])
        stream = pyte.Stream(screen)

        try:
            # Use ptyprocess for proper terminal emulation
            import ptyprocess

            # Start the application with a PTY
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["COLUMNS"] = str(self.terminal_size[0])
            env["LINES"] = str(self.terminal_size[1])

            # Create PTY process
            pty_process = ptyprocess.PtyProcess.spawn(
                app_command,
                env=env,
                dimensions=(self.terminal_size[1], self.terminal_size[0]),
            )

            # Initial capture after startup
            await asyncio.sleep(1.0)  # Let app initialize

            # Read initial output from PTY
            try:
                if pty_process.isalive():
                    # ptyprocess doesn't have timeout, use read() directly
                    output = pty_process.read()
                    if output:
                        stream.feed(output)
                        screenshot_path = await self._capture_screen(
                            screen, f"{scenario_name}_01_initial"
                        )
                        screenshots.append(screenshot_path)
            except Exception as e:
                print(f"Error reading initial output: {e}")

            # Simulate interactions if provided
            if interactions:
                for i, interaction in enumerate(interactions, 2):
                    await self._simulate_pty_interaction(pty_process, interaction)
                    await asyncio.sleep(0.5)  # Wait for response

                    # Capture output after interaction
                    try:
                        if pty_process.isalive():
                            output = pty_process.read()
                            if output:
                                stream.feed(output)
                                screenshot_path = await self._capture_screen(
                                    screen,
                                    f"{scenario_name}_{i:02d}_interaction_{i - 1}",
                                )
                                screenshots.append(screenshot_path)
                    except Exception as e:
                        print(f"Error reading interaction output: {e}")

            # Final capture
            await asyncio.sleep(0.5)
            try:
                if pty_process.isalive():
                    output = pty_process.read()
                    if output:
                        stream.feed(output)
            except Exception as e:
                print(f"Error reading final output: {e}")

            screenshot_path = await self._capture_screen(
                screen, f"{scenario_name}_final"
            )
            screenshots.append(screenshot_path)

            # Cleanup
            try:
                if pty_process.isalive():
                    pty_process.write(b"q\n")  # Try to quit gracefully
                    await asyncio.sleep(1.0)
                    if pty_process.isalive():
                        pty_process.terminate()
            except Exception as e:
                print(f"Error during cleanup: {e}")

        except Exception as e:
            print(f"Error capturing app flow: {e}")
            # Create error file
            error_path = self.output_dir / f"{scenario_name}_error.txt"
            error_path.write_text(f"Capture failed: {e}")
            screenshots.append(error_path)

        return screenshots

    async def _simulate_interaction(self, process, interaction: Dict[str, Any]):
        """Simulate user interaction with the application."""
        interaction_type = interaction.get("type", "key")

        if interaction_type == "key":
            key = interaction.get("key", "")
            if process.stdin is not None:
                if key == "enter":
                    process.stdin.write(b"\n")
                elif key == "space":
                    process.stdin.write(b" ")
                elif key == "tab":
                    process.stdin.write(b"\t")
                elif key == "escape":
                    process.stdin.write(b"\x1b")
                elif key == "q":
                    process.stdin.write(b"q")
                else:
                    process.stdin.write(key.encode("utf-8"))
                await process.stdin.drain()

        elif interaction_type == "wait":
            duration = interaction.get("duration", 0.5)
            await asyncio.sleep(duration)

    async def _simulate_pty_interaction(self, pty_process, interaction: Dict[str, Any]):
        """Simulate user interaction with the PTY process."""
        interaction_type = interaction.get("type", "key")

        if interaction_type == "key":
            key = interaction.get("key", "")
            if key == "enter":
                pty_process.write(b"\n")
            elif key == "space":
                pty_process.write(b" ")
            elif key == "tab":
                pty_process.write(b"\t")
            elif key == "escape":
                pty_process.write(b"\x1b")
            elif key == "q":
                pty_process.write(b"q")
            else:
                pty_process.write(key.encode("utf-8"))

        elif interaction_type == "wait":
            duration = interaction.get("duration", 0.5)
            await asyncio.sleep(duration)

    async def _capture_screen(self, screen: pyte.Screen, name: str) -> Path:
        """Capture the current screen state as text and convert to image."""

        # Save as text first
        text_path = self.output_dir / f"{name}.txt"
        screen_text = self._screen_to_text(screen)
        text_path.write_text(screen_text)

        # Convert to image
        image_path = self.output_dir / f"{name}.png"
        await self._text_to_image(screen_text, image_path, screen)

        print(f"Captured screenshot: {image_path}")
        return image_path

    def _screen_to_text(self, screen: pyte.Screen) -> str:
        """Convert pyte screen to text representation."""
        lines = []
        for row in range(screen.lines):
            line_chars = []
            for col in range(screen.columns):
                try:
                    char = screen.buffer[row][col]
                    line_chars.append(char.data if hasattr(char, "data") else str(char))
                except (IndexError, KeyError):
                    line_chars.append(" ")
            lines.append("".join(line_chars).rstrip())

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

    async def _text_to_image(self, text: str, image_path: Path, screen: pyte.Screen):
        """Convert text representation to a PNG image."""

        # Try to get a monospace font
        try:
            # Common monospace fonts
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                "/System/Library/Fonts/Monaco.ttf",
                "C:\\Windows\\Fonts\\consola.ttf",
            ]

            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 14)
                    break

            if font is None:
                font = ImageFont.load_default()

        except Exception:
            font = ImageFont.load_default()

        # Calculate image dimensions
        lines = text.split("\n")
        max_width = max(len(line) for line in lines) if lines else 80

        # Get font metrics
        try:
            bbox = font.getbbox("M")  # Use 'M' as reference character
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1] + 2  # Add line spacing
        except Exception:
            char_width = 8
            char_height = 16

        img_width = max_width * char_width + 20  # Add padding
        img_height = len(lines) * char_height + 20  # Add padding

        # Create image
        img = Image.new(
            "RGB", (int(img_width), int(img_height)), color=(12, 12, 12)
        )  # Dark background
        draw = ImageDraw.Draw(img)

        # Draw text with basic color support
        y_offset = 10
        for line in lines:
            # Basic terminal color parsing (simplified)
            clean_line = self._strip_ansi(line)

            # Use white text for now (could be enhanced with ANSI color parsing)
            draw.text((10, y_offset), clean_line, font=font, fill=(255, 255, 255))
            y_offset += char_height

        # Save image
        img.save(image_path)

    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    async def capture_git_autosquash_workflow(
        self, repo_path: Path, scenario_name: str = "git_autosquash"
    ) -> List[Path]:
        """
        Capture a complete git-autosquash workflow.

        Args:
            repo_path: Path to git repository to run autosquash on
            scenario_name: Name for the screenshot series

        Returns:
            List of screenshot file paths
        """

        # Change to the repository directory
        original_cwd = os.getcwd()
        os.chdir(repo_path)

        try:
            # Define interaction sequence for git-autosquash
            interactions: List[Dict[str, Any]] = [
                {"type": "wait", "duration": 1.0},  # Let it load
                {"type": "key", "key": "j"},  # Navigate down
                {"type": "wait", "duration": 0.3},
                {"type": "key", "key": "space"},  # Toggle approval
                {"type": "wait", "duration": 0.3},
                {"type": "key", "key": "j"},  # Navigate down
                {"type": "wait", "duration": 0.3},
                {"type": "key", "key": "enter"},  # Confirm selection
                {"type": "wait", "duration": 0.5},
                {"type": "key", "key": "q"},  # Quit
            ]

            screenshots = await self.capture_app_flow(
                ["git-autosquash"], interactions, scenario_name
            )

        finally:
            os.chdir(original_cwd)

        return screenshots


@contextmanager
def temporary_git_repo_with_changes():
    """Create a temporary git repository with sample changes for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
        )

        # Create initial files
        (repo_path / "main.py").write_text("""def main():
    print("Hello World")
    return 0

if __name__ == "__main__":
    main()
""")

        (repo_path / "utils.py").write_text("""def helper():
    pass
""")

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True
        )

        # Make changes
        (repo_path / "main.py").write_text("""def main():
    print("Hello World!")  # Added exclamation
    print("Starting application...")  # New line
    return 0

if __name__ == "__main__":
    main()
""")

        (repo_path / "utils.py").write_text('''def helper():
    """Helper function for utilities."""  # Added docstring
    pass

def new_helper():  # New function
    return True
''')

        yield repo_path


if __name__ == "__main__":
    # Demo/test the screenshot system
    async def main():
        output_dir = Path("screenshots/pyte_demo")
        capture = PyteScreenshotCapture(output_dir)

        print("Testing pyte screenshot capture...")

        # Test with real git repo

        # Test with real git repo (if possible)
        try:
            with temporary_git_repo_with_changes() as repo_path:
                print(f"Testing with temporary repo at {repo_path}")
                real_screenshots = await capture.capture_git_autosquash_workflow(
                    repo_path, "real_demo"
                )
                print(f"Created {len(real_screenshots)} real screenshots")
        except Exception as e:
            print(f"Real workflow test failed: {e}")

        print(f"Screenshots saved to: {output_dir}")

    asyncio.run(main())
