#!/usr/bin/env python3
from __future__ import annotations
import os, sys, subprocess
from pathlib import Path
from unittest import case
from pick import pick
from typing import cast, List, Tuple, Callable, Union
from enum import Enum

VENV_DIR_NAME = ".mathoku-dev-console-venv"
REQ_FILE = "requirements.txt"

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent
VENV_PATH = PROJECT_ROOT / VENV_DIR_NAME
IS_WINDOWS = os.name == "nt"

def venv_python_path(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")

def in_our_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV_PATH.resolve()

def run(cmd, *, check=True):
    print(">>", " ".join(map(str, cmd)), flush=True)
    return subprocess.check_call(cmd) if check else subprocess.call(cmd)

def create_venv():
    print(f"Creating virtual environment at {VENV_PATH} ...")
    run([sys.executable, "-m", "venv", str(VENV_PATH)])
    print("Virtual environment created.")

def install_requirements(python: Path):
    req_path = PROJECT_ROOT / REQ_FILE
    if not req_path.exists():
        print(f"Warning: {REQ_FILE} not found; skipping dependency install.", file=sys.stderr)
        return
    print(f"Installing dependencies from {REQ_FILE} ...")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    run([str(python), "-m", "pip", "install", "-r", str(req_path)])
    print("Dependencies installed.")

def parse_args(argv):
    sync = False
    no_spawn = False
    rest = []
    for a in argv:
        if a == "--sync":
            sync = True
        elif a == "--no-spawn":
            no_spawn = True   # replaces --no-reexec
        else:
            rest.append(a)
    return sync, no_spawn, rest

def main():
    if os.environ.get("SKIP_VENV_BOOTSTRAP") == "1":
        print("Skipping venv bootstrap due to SKIP_VENV_BOOTSTRAP=1.")
        return real_main([])

    sync, no_spawn, passthrough = parse_args(sys.argv[1:])

    # Ensure venv present / updated
    if not VENV_PATH.exists():
        create_venv()
        install_requirements(venv_python_path(VENV_PATH))
    elif sync:
        install_requirements(venv_python_path(VENV_PATH))

    if not in_our_venv() and not no_spawn:
        python = venv_python_path(VENV_PATH)
        if not python.exists():
            print(f"Error: expected venv python at {python} not found. Recreating.", file=sys.stderr)
            create_venv()
            install_requirements(venv_python_path(VENV_PATH))
            python = venv_python_path(VENV_PATH)
        # Spawn child instead of exec
        sys.exit(subprocess.call([str(python), str(SCRIPT_PATH)] + passthrough))

    return real_main(passthrough)

ANDROID_TARGETS_OF_INTEREST: Tuple[Tuple[str, str], ...] = (
    ("aarch64-linux-android", "arm64-v8a"),
    ("armv7-linux-androideabi", "armeabi-v7a"),
    ("x86_64-linux-android", "x86_64"),
)

def get_android_target_installation_statuses():
    """
    Return list of (target_triple, installed_bool) for all targets of interest.
    Never raises due to rustup issues; prints a concise message instead.
    """
    try:
        out = subprocess.check_output(
            ["rustup", "target", "list", "--installed"],
            text=True
        )
        installed_targets = {line.strip() for line in out.splitlines() if line.strip()}
    except Exception as e:
        # Graceful fallback: report all as missing
        print(f"[warn] Could not query rustup targets ({e}); treating all as missing.")
        installed_targets = set()

    return [((target, jni_target), target in installed_targets) for (target, jni_target) in ANDROID_TARGETS_OF_INTEREST]

def validate_environment():
    statuses = get_android_target_installation_statuses()
    all_ok = all(installed for _, installed in statuses)
    if all_ok:
        print("\n✅ Environment validation succeeded.")
    else:
        print("\n❌ Environment validation failed.")
    print("Android targets:")
    for (triple, _), ok in statuses:
        mark = "✓" if ok else "✗"
        print(f"  {mark} {triple}")
    if not all_ok:
        missing = [target for (target, _), ok in statuses if not ok]
        print("\nInstall missing with:\n  rustup target add " + " ".join(missing))

    android_home = os.environ.get("ANDROID_HOME")
    android_home_ok = android_home is not None and Path(android_home).is_dir()

    # Print ANDROID_HOME status
    print("Environment variables:")
    mark_android = "✓" if android_home_ok else "✗"
    if android_home_ok:
        print(f"  {mark_android} ANDROID_HOME is set to: {android_home}")
    else:
        if android_home:
            print(f"  {mark_android} ANDROID_HOME is set, but the path '{android_home}' does not exist or is not a directory.")
        else:
            print(f"  {mark_android} ANDROID_HOME is not set.")
        print("\n  Please install the Android 7 SDK and set the ANDROID_HOME environment variable to point to your Android SDK location.")
        print("  You can download the Android 7 SDK by installing Android Studio from https://developer.android.com/studio, and selecting the Android 7 SDK component during installation.")

    java_home = os.environ.get("JAVA_HOME")
    java_home_ok = java_home is not None and Path(java_home).is_dir()
    # Print JAVA_HOME status
    mark_java = "✓" if java_home_ok else "✗"
    if java_home_ok:
        print(f"  {mark_java} JAVA_HOME is set to: {java_home}")
    else:
        if java_home:
            print(f"  {mark_java} JAVA_HOME is set, but the path '{java_home}' does not exist or is not a directory.")
        else:
            print(f"  {mark_java} JAVA_HOME is not set.")
        print("\n  Please set JAVA_HOME to your JDK 17 installation folder.")
        print("  You can download JDK 17 from https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html")

    input("\nPress Enter to continue...")

def first_time_setup():
    """Install all required Android targets."""
    print("Starting first-time setup for Android targets...")
    statuses = get_android_target_installation_statuses()
    missing = [target for (target, _), ok in statuses if not ok]

    if not missing:
        print("\nAll required Android targets are already installed.")
    else:
        print(f"\nInstalling missing targets: {', '.join(missing)}")
        try:
            run(["rustup", "target", "add"] + missing)
            print("\n✅ Successfully installed missing targets.")
        except subprocess.CalledProcessError:
            print("\n❌ Failed to install targets. Please check the output above.")

    android_home = os.environ.get("ANDROID_HOME")
    android_home_ok = android_home is not None and Path(android_home).is_dir()
    if not android_home_ok:
        print("\n  Please install the Android 7 SDK and set the ANDROID_HOME environment variable to point to your Android SDK location.")
        print("  You can download the Android 7 SDK by installing Android Studio from https://developer.android.com/studio, and selecting the Android 7 SDK component during installation.")
        print("  Please re-run this script after setting ANDROID_HOME.")
        return
    
    print("\nChecking Java environment variables...")
    java_home = os.environ.get("JAVA_HOME")
    java_home_ok = java_home is not None and Path(java_home).is_dir()
    
    mark_java = "✓" if java_home_ok else "✗"
    if java_home_ok:
        print(f"  {mark_java} JAVA_HOME is set to: {java_home}")
    else:
        if java_home:
            print(f"  {mark_java} JAVA_HOME is set, but the path '{java_home}' does not exist or is not a directory.")
        else:
            print(f"  {mark_java} JAVA_HOME is not set.")
        print("\n  Please set JAVA_HOME to your JDK 17 installation folder.")
        print("  You can download JDK 17 from https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html")
        print("  After setting JAVA_HOME, please re-run this script to validate your environment.")
        return

    # Show final status
    validate_environment()

def build_mathoku_core(profile: str):
    """Builds the mathoku-core crate for all Android targets."""
    print(f"Building mathoku-core (profile: {profile})...")
    base_cmd = ["cargo", "ndk"]
    build_cmd_suffix = ["build"]
    if profile == "release":
        build_cmd_suffix.append("--release")

    core_path = PROJECT_ROOT / "mathoku-core"
    if not core_path.is_dir():
        print(f"\n❌ Error: mathoku-core directory not found at {core_path}")
        input("\nPress Enter to continue...")
        return

    for (target, jni_target) in ANDROID_TARGETS_OF_INTEREST:
        cmd = base_cmd + ["-t", target, "-o", f"../mathoku-kotlin-rust-wrapper/src/main/jniLibs"] + build_cmd_suffix
        try:
            # The 'run' helper doesn't support 'cwd', so we use subprocess directly
            print(">>", " ".join(map(str, cmd)), f"(in {core_path})", flush=True)
            subprocess.check_call(cmd, cwd=core_path)
        except subprocess.CalledProcessError:
            print(f"\n❌ Failed to build for target {target}. Please check the output above.")
            input("\nPress Enter to continue...")
            return
    
    print(f"\n✅ Successfully built mathoku-core for all targets (profile: {profile}).")
    input("\nPress Enter to continue...")

def execute_steps(steps: List[Callable[[], bool]]) -> bool:
    """
    Executes a list of steps, each represented by a callable.
    If any step returns False, the process is aborted.
    """
    for step in steps:
        step_success = step()

        if not step_success:
            print("Process aborted due to a step failure.")
            return False
        
    return True
class NamedExecutablePlan:
    """Represents a named sequence of executable steps."""
    def __init__(self, name: str, steps: List[Callable[[], bool]]):
        """
        Initializes the NamedExecutablePlan.

        Args:
            name: The name of the plan.
            steps: A list of callables representing the steps of the plan.
        """
        self.name = name
        self.steps = steps

    def execute(self) -> bool:
        """
        Executes the plan's steps sequentially.

        Returns:
            True if all steps executed successfully, False otherwise.
        """
        print(f"Executing plan: {self.name}")
        return execute_steps(self.steps)

class NamedExecutablePlanBuilder:
    """A builder for creating NamedExecutablePlan objects."""

    def __init__(self, name: str):
        self.name = name
        self.steps: List[Callable[[], bool]] = []

    def add_step(self, step: Callable[[], bool]) -> NamedExecutablePlanBuilder:
        self.steps.append(step)
        return self

    def build(self) -> NamedExecutablePlan:
        return NamedExecutablePlan(self.name, self.steps)

class FunctionCall:
    """Represents a menu action."""
    def __init__(self, func: Callable[[], None]):
        self.func = func

    def __call__(self):
        self.func()

class Exit:
    """Represents an exit action."""

type MenuItem = Tuple[str, FunctionCall | Exit]

class Menu:
    """A data storage class to manage menu options and their associated actions."""

    def __init__(self, items: List[MenuItem]):
        self.items = items

    def get_options(self) -> List[str]:
        return [name for name, _ in self.items]

    def get_action(self, name: str) -> FunctionCall | Exit:
        for item_name, item in self.items:
            if item_name == name:
                return item
            
        raise ValueError(f"Action '{name}' not found in menu data.")
    
class MenuBuilder:
    def __init__(self):
        self.items: List[MenuItem] = []

    def add_call(self, name: str, action: Callable[[], None]) -> MenuBuilder:
        self.items.append((name, FunctionCall(action)))
        return self
    
    def add_exit(self, name: str) -> MenuBuilder:
        self.items.append((name, Exit()))
        return self

    def build(self) -> Menu:
        return Menu(self.items)

def run_single_select_menu(menu_data: Menu):
    """
    Displays a menu and executes the selected action.

    Args:
        menu_data: An instance of MenuData containing the menu options and actions.
    """
    while True:
        title = "Select an option:"
        options = menu_data.get_options()
        choice, _ = pick(options, title, indicator=">>")

        # pick's typing is not great, so we coerce to str
        choice = cast(str, choice)

        try:
            # Can throw ValueError if choice not found
            action = menu_data.get_action(choice)
            
            if isinstance(action, FunctionCall):
                action()
            elif isinstance(action, Exit):
                return
            else:
                raise ValueError(f"Unexpected action type for choice '{choice}': {type(action)}")
            
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)

def run_multi_select_menu(menu_data: Menu):
    """
    Displays a multi-select menu and executes the selected action(s).

    Args:
        menu_data: An instance of MenuData containing the menu options and actions.
    """
    while True:
        title = "Select one or more options (use space to select, enter to confirm, confirm empty selection to go back):"
        options = menu_data.get_options()
        choices = pick(options, title, indicator=">>", multiselect=True)

        # pick's typing is not great, so we coerce to a tuple of str + indexes
        choices = cast(List[Tuple[str, int]], choices)

        if len(choices) == 0:
            return

        for choice, _ in choices:
            try:
                # Can throw ValueError if choice not found
                action = menu_data.get_action(choice)
                
                if isinstance(action, FunctionCall):
                    action()
                elif isinstance(action, Exit):
                    raise ValueError("Exit action selected, but multi-select does not support exit options.")
                else:
                    raise ValueError(f"Unexpected action type for choice '{choice}': {type(action)}")
                
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)

def real_main(args):
    main_menu = MenuBuilder() \
            .add_call("Environment Setup", lambda: run_single_select_menu(environment_setup_menu)) \
            .add_call("Build", lambda: run_multi_select_menu(build_menu)) \
            .add_exit("Exit") \
            .build()
    
    build_menu = MenuBuilder() \
            .add_call("mathoku-core -- debug", lambda: build_mathoku_core(profile="debug")) \
            .add_call("mathoku-core -- release", lambda: build_mathoku_core(profile="release")) \
            .add_exit("Back") \
            .build()
    
    environment_setup_menu = MenuBuilder() \
            .add_call("First-time setup (install Android targets)", first_time_setup) \
            .add_call("Validate environment", validate_environment) \
            .add_exit("Back") \
            .build()
    
    run_single_select_menu(main_menu)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
