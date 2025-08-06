from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Input, Button, Footer, Label
from rich.text import Text
import subprocess
import sys
import asyncio
import json

VERSION = "0.1"
DEVELOPER = "Rico"
GITHUB_URL = "https://github.com/mambuzrrr/pipPilot"

class PipPilotApp(App):
    CSS = """
    Screen {
        background: #1e1e2e;
        color: #cdd6f4;
        align: center middle;
    }
    #main {
        align: center middle;
    }
    #menu {
        width: 50%;
        max-height: 70vh;
        padding: 1;
        border: round #89b4fa;
        background: #313244;
        overflow: auto;
    }
    #title {
        content-align: center middle;
        text-style: bold;
        color: #f5c2e7;
        padding-bottom: 1;
    }
    #description {
        content-align: center middle;
        color: #a6adc8;
        padding-bottom: 1;
    }
    #github {
        content-align: center middle;
        color: #89b4fa;
        padding-bottom: 1;
    }
    Button {
        width: 100%;
        margin: 1 0;
        background: #45475a;
        border: round #89b4fa;
        content-align: center middle;
    }
    Button:hover {
        background: #585b70;
    }
    Input {
        width: 60%;
        margin: 1 0;
        background: #45475a;
        border: round #89b4fa;
    }
    #prompt {
        padding: 1;
    }
    #output {
        padding: 1;
        height: 80%;
        overflow: auto;
        background: #45475a;
        border: round #89b4fa;
    }
    #status {
        dock: bottom;
        height: 1;
        content-align: center middle;
        background: #11111b;
        color: #f5c2e7;
    }
    Footer {
        background: #11111b;
        color: #f5c2e7;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Static("pipPilot CLI", id="title"),
                Static("A simple CLI tool to manage Python packages with pip.", id="description"),
                Static(f"GitHub: {GITHUB_URL}", id="github"),
                Button("Install Package", id="install"),
                Button("Update Package", id="update"),
                Button("Uninstall Package", id="uninstall"),
                Button("Find Package Info", id="find"),
                Button("List Installed Packages", id="list_installed"),
                Button("Update All Packages", id="update_all"),
                Button("Quit", id="quit"),
                id="menu",
            ),
            id="main",
        )
        yield Static(f"v{VERSION} by {DEVELOPER}", id="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "install":
                self.push_screen(PackageInputScreen("install"))
            case "update":
                self.push_screen(PackageInputScreen("update"))
            case "uninstall":
                self.push_screen(PackageInputScreen("uninstall"))
            case "find":
                self.push_screen(FindPackageScreen())
            case "list_installed":
                self.push_screen(ListPackagesScreen())
            case "update_all":
                self.push_screen(UpdateAllPackagesScreen())
            case "quit":
                self.exit()
            case _:
                # z.B. "back" landet hier, aber wird in den Screens sauber behandelt
                pass

class PackageInputScreen(Screen):
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode

    def compose(self) -> ComposeResult:
        yield Label(f"Enter package name to {self.mode}:", id="prompt")
        yield Input(placeholder="requests", id="pkg_input")
        yield Button("Run", id="run")
        yield Button("Back", id="back")
        yield Static(f"v{VERSION} by {DEVELOPER}", id="status")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "run":
            pkg = self.query_one(Input).value.strip()
            if not pkg:
                return
            await self.app.push_screen(OutputScreen(f"Running pip {self.mode} on '{pkg}'...\n"))
            result = await asyncio.to_thread(self._run_pip, pkg)
            await self.app.push_screen(OutputScreen(result))

    def _run_pip(self, pkg: str) -> str:
        args = (["install", pkg] if self.mode == "install"
                else ["install", "--upgrade", pkg] if self.mode == "update"
                else ["uninstall", "-y", pkg])
        try:
            output = subprocess.check_output(
                [sys.executable, "-m", "pip"] + args,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=60
            )
            return f"✅ Success:\n{output}"
        except subprocess.TimeoutExpired:
            return "❌ Error: pip command timed out."
        except subprocess.CalledProcessError as e:
            return f"❌ Error:\n{e.output}"

class FindPackageScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Enter package name to search:", id="prompt")
        yield Input(placeholder="flask", id="pkg_input")
        yield Button("Search", id="run")
        yield Button("Back", id="back")
        yield Static(f"v{VERSION} by {DEVELOPER}", id="status")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "run":
            pkg = self.query_one(Input).value.strip()
            if not pkg:
                return
            await self.app.push_screen(OutputScreen(f"Searching for '{pkg}'...\n"))
            result = await asyncio.to_thread(self._search_pkg, pkg)
            await self.app.push_screen(OutputScreen(result))

    def _search_pkg(self, pkg: str) -> str:
        try:
            show = subprocess.check_output(
                [sys.executable, "-m", "pip", "show", pkg],
                stderr=subprocess.DEVNULL,
                text=True
            )
            installed = next((l.split(":",1)[1].strip()
                              for l in show.splitlines() if l.startswith("Version")), "Unknown")
        except Exception:
            installed = "Not installed"
        try:
            latest = subprocess.check_output(
                [sys.executable, "-m", "pip", "index", "versions", pkg],
                stderr=subprocess.DEVNULL,
                text=True
            )
        except Exception:
            latest = "Could not fetch latest version."
        return f"📦 Package: {pkg}\nInstalled: {installed}\n\n{latest}"

class ListPackagesScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Fetching installed packages...", id="output")
        yield Button("Back", id="back")
        yield Static(f"v{VERSION} by {DEVELOPER}", id="status")
        yield Footer()

    async def on_mount(self) -> None:
        result = await asyncio.to_thread(self._get_package_list_with_updates)
        self.query_one("#output", Static).update(result)

    def _get_package_list_with_updates(self) -> Text:
        try:
            installed_raw = subprocess.check_output(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                stderr=subprocess.STDOUT, text=True, timeout=30
            )
            outdated_raw = subprocess.check_output(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                stderr=subprocess.STDOUT, text=True, timeout=30
            )
            outdated_json = json.loads(outdated_raw)
        except Exception as e:
            return Text(f"❌ Error fetching package list:\n{e}", style="bold red")

        installed = {
            name.lower(): ver
            for name, ver in (line.split("==",1) for line in installed_raw.splitlines() if "==" in line)
        }
        outdated = {
            pkg["name"].lower(): (pkg["version"], pkg["latest_version"])
            for pkg in outdated_json
        }

        text = Text("Installed Packages:\n\n", style="bold")
        for name, curr in sorted(installed.items()):
            if name in outdated:
                inst_v, lat_v = outdated[name]
                text.append(f"{name} ", style="bold")
                text.append(f"{inst_v}", style="red")
                text.append(" -> Can be updated to ")
                text.append(f"{lat_v}\n", style="green")
            else:
                text.append(f"{name} {curr}\n", style="white")
        return text

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

class UpdateAllPackagesScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Starting update of all installed packages...\nPlease wait.", id="output")
        yield Button("Back", id="back")
        yield Static(f"v{VERSION} by {DEVELOPER}", id="status")
        yield Footer()

    async def on_mount(self) -> None:
        result = await asyncio.to_thread(self._update_all_packages)
        self.query_one("#output", Static).update(result)

    def _update_all_packages(self) -> str:
        try:
            installed_raw = subprocess.check_output(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                stderr=subprocess.STDOUT, text=True, timeout=60
            )
            packages = [line.split("==",1)[0] for line in installed_raw.splitlines() if "==" in line]

            output = ""
            for pkg in packages:
                output += f"Updating {pkg}...\n"
                try:
                    out = subprocess.check_output(
                        [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                        stderr=subprocess.STDOUT, text=True, timeout=60
                    )
                    output += out + "\n"
                except subprocess.CalledProcessError as e:
                    output += f"Failed to update {pkg}:\n{e.output}\n"
                except subprocess.TimeoutExpired:
                    output += f"Timeout while updating {pkg}\n"
            return output
        except Exception as e:
            return f"❌ Error during update:\n{e}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

class OutputScreen(Screen):
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield Static(self.text, id="output", expand=True)
        yield Button("Back", id="back")
        yield Static(f"v{VERSION} by {DEVELOPER}", id="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            self.app.pop_screen()

if __name__ == "__main__":
    PipPilotApp().run()
