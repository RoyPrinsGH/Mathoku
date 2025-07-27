#!/usr/bin/env python3
from __future__ import annotations
import os, sys, subprocess
from pathlib import Path
from pick import pick
from typing import cast, List, Tuple, Callable

def run_mathoku_dev_console(args):
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
            .add_call("Validate environment", validate_environment) \
            .add_call("Set up environment", set_up_environment) \
            .add_exit("Back") \
            .build()
    
    run_single_select_menu(main_menu)

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
        return run_mathoku_dev_console([])

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

    return run_mathoku_dev_console(passthrough)

ANDROID_TARGETS: List[str] = [
    "arm64-v8a", "armeabi-v7a", "x86_64"
]

def validate_environment():
    """Validates the environment setup for MMathoku development."""

    components = get_environment_components()

    all_ok = True

    for component in components:
        if not component.validate_set_up():
            all_ok = False
    if all_ok:
        print("\n✅ Environment validation succeeded.")
    else:
        print("\n❌ Environment validation failed.")

    input("\nPress Enter to continue...")

def set_up_environment():
    """Performs the first-time setup for the development environment."""
    components = get_environment_components()

    all_ok = True

    for component in components:
        if not component.validate_pre_set_up():
            print(f"\n❌ {component.__class__.__name__} is not set up correctly. Please fix the issues above.")
            all_ok = False
    if not all_ok:
        input("\nPress Enter to continue...")
        return
    
    print("\nAll components are valid. Proceeding with setup...")

    for component in components:
        if component.validate_set_up():
            print(f"\n✅ {component.__class__.__name__} is already set up correctly.")
            continue
        if not component.set_up():
            print(f"\n❌ Failed to set up {component.__class__.__name__}. Please fix the issues above.")
            all_ok = False
    if all_ok:
        print("\n✅ Environment setup completed successfully.")
    else:
        print("\n❌ Environment setup failed. Please fix the issues above.")

    input("\nPress Enter to continue...")

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

    for (target, jni_target) in ANDROID_TARGETS:
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

## ------ Environment Components ------

def get_environment_components() -> List[EnvComponent]:
    """
    Returns a list of environment components that need to be validated and set up.
    """
    return [
        RustupAndroidTargetsComponent(),
        AndroidSdkComponent(),
        JavaEnvironmentComponent()
    ]

class EnvComponent:
    def validate_pre_set_up(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")
    
    def set_up(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")
    
    def validate_set_up(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")

class RustupAndroidTargetsComponent(EnvComponent):
    def validate_pre_set_up(self) -> bool:
        try:
            subprocess.check_output(["rustup", "--version"], text=True)
            return True
        except subprocess.CalledProcessError:
            print("Rustup is not installed or not found in PATH.")
            return False

    def set_up(self) -> bool:
        print("Setting up Rustup Android targets...")
        try:
            run(["rustup", "target", "add"] + ANDROID_TARGETS)
            print("Rustup Android targets set up successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to set up Rustup Android targets: {e}", file=sys.stderr)
            return False
        
    def validate_set_up(self) -> bool:
        try:
            rustup_output = subprocess.check_output(["rustup", "target", "list", "--installed"], text=True)
            installed_targets = [line.split()[0] for line in rustup_output.strip().splitlines()]
        except subprocess.CalledProcessError as e:
            print(f"Failed to list Rustup targets: {e}", file=sys.stderr)
            return False

        success = True

        for target in ANDROID_TARGETS:
            if target not in installed_targets:
                print(f"Target {target} is not installed.")
                success = False

        return success

class AndroidSdkComponent(EnvComponent):
    def validate_pre_set_up(self) -> bool:
        return True

    def set_up(self) -> bool:
        return True
    
    def validate_set_up(self) -> bool:
        android_home = os.environ.get("ANDROID_HOME")
        if android_home is None:
            print("ANDROID_HOME is not set.")
            return False
        
        android_home_path = Path(android_home)
        if not android_home_path.is_dir():
            print(f"ANDROID_HOME path '{android_home}' does not exist or is not a directory.")
            return False
        
        # Check for Android 7 SDK
        sdk_version = "24"
        platform_path = android_home_path / "platforms" / f"android-{sdk_version}"

        if not platform_path.is_dir():
            print(f"Android SDK platform path '{platform_path}' does not exist or is not a directory.")
            return False

        return True
    
class JavaEnvironmentComponent(EnvComponent):
    def validate_pre_set_up(self) -> bool:
        return True

    def set_up(self) -> bool:
        return True
    
    def validate_set_up(self) -> bool:
        java_home = os.environ.get("JAVA_HOME")
        if java_home is None:
            print("JAVA_HOME is not set.")
            return False
        
        java_home_path = Path(java_home)
        if not java_home_path.is_dir():
            print(f"JAVA_HOME path '{java_home}' does not exist or is not a directory.")
            return False
        
        # Check for JDK 17
        jdk_version_file = java_home_path / "release"
        if not jdk_version_file.exists():
            print(f"JDK version file '{jdk_version_file}' does not exist.")
            return False
        
        with open(jdk_version_file, "r") as f:
            content = f.read()
            if "JAVA_VERSION=\"17" not in content:
                print("JAVA_HOME does not point to JDK 17.")
                return False
        
        return True

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

    def get_options(self, show_exit_options: bool = True) -> List[str]:
        return [name for name, action in self.items if isinstance(action, FunctionCall) or (show_exit_options and isinstance(action, Exit))]

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
        options = menu_data.get_options(show_exit_options=True)
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
        options = menu_data.get_options(show_exit_options=False)
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

if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)