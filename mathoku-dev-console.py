#!/usr/bin/env python3
from __future__ import annotations

import abc
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem


def run_mathoku_dev_console() -> None:
    main_menu = ConsoleMenu("main menu")

    build_menu = ConsoleMenu("build")
    build_menu.append_item(FunctionItem("mathoku-core -- debug", function=build_mathoku_core, kwargs={"profile": "debug"}))
    build_menu.append_item(FunctionItem("mathoku-core -- release", function=build_mathoku_core, kwargs={"profile": "release"}))
    build_menu.append_item(FunctionItem("mathoku-kotlin-rust-wrapper -- debug", function=build_kotlin_wrapper, kwargs={"profile": "debug"}))
    build_menu.append_item(FunctionItem("mathoku-kotlin-rust-wrapper -- release", function=build_kotlin_wrapper, kwargs={"profile": "release"}))

    environment_setup_menu = ConsoleMenu("environment")
    environment_setup_menu.append_item(FunctionItem("Validate environment", validate_environment))
    environment_setup_menu.append_item(FunctionItem("Set up environment", set_up_environment))

    main_menu.append_item(SubmenuItem("Environment Setup", environment_setup_menu, main_menu))
    main_menu.append_item(SubmenuItem("Build", build_menu, main_menu))
    main_menu.append_item(FunctionItem("Run Mathoku Android App", function=run_application))
    main_menu.show()


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent
IS_WINDOWS = os.name == "nt"


def venv_python_path(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def run(cmd, *, check=True) -> int:
    print(">>", " ".join(map(str, cmd)), flush=True)
    return subprocess.check_call(cmd) if check else subprocess.call(cmd)


def main():
    return run_mathoku_dev_console()


ANDROID_RUSTUP_TARGETS: list[str] = [
    "aarch64-linux-android",
    "armv7-linux-androideabi",
    "x86_64-linux-android",
]

ANDROID_TARGETS: list[str] = [
    "arm64-v8a", "armeabi-v7a", "x86_64"
]


def success_or_failure_text_builder(task: str, success: bool, prefix: str = "\n") -> str:
    return f"{prefix}✅ {task} succeeded." if success else f"{prefix}❌ {task} failed."


def await_enter(func: Callable[..., None], *args, **kwargs) -> Callable[[], None]:
    def wrapper(*args, **kwargs) -> None:
        func(*args, **kwargs)
        input("\nPress Enter to continue...")
    return wrapper


@await_enter
def validate_environment() -> None:
    """Validates the environment setup for Mathoku development."""

    validations = [component.validate_set_up() for component in get_environment_components()]
    print(success_or_failure_text_builder("Environment validation", all(validations)))


@await_enter
def set_up_environment() -> None:
    """Performs the first-time setup for the development environment."""
    components = get_environment_components()

    pre_validations = [component.validate_pre_set_up() for component in components]
    print(success_or_failure_text_builder("Pre-setup validation", all(pre_validations)))
    if not all(pre_validations):
        return

    setup_validations = [component.validate_set_up() for component in components]
    print(success_or_failure_text_builder("Setup-validation", all(setup_validations)))
    if all(setup_validations):
        return

    setup_all_invalid = [component.set_up() for i, component in enumerate(components) if not setup_validations[i]]
    print(success_or_failure_text_builder("Environment setup", all(setup_all_invalid)))


@await_enter
def build_mathoku_core(profile: str) -> None:
    """Builds the mathoku-core crate for all Android targets."""
    print(f"Building mathoku-core (profile: {profile})...")
    base_cmd = ["cargo", "ndk"]
    build_cmd_suffix = ["build"]
    if profile == "release":
        build_cmd_suffix.append("--release")

    core_path = PROJECT_ROOT / "mathoku-core"
    if not core_path.is_dir():
        print(f"\n❌ Error: mathoku-core directory not found at {core_path}")
        return

    for target in ANDROID_TARGETS:
        cmd = base_cmd + ["-t", target, "-o", "../mathoku-kotlin-rust-wrapper/src/main/jniLibs"] + build_cmd_suffix
        try:
            # The 'run' helper doesn't support 'cwd', so we use subprocess directly
            print(">>", " ".join(map(str, cmd)), f"(in {core_path})", flush=True)
            subprocess.check_call(cmd, cwd=core_path)
        except subprocess.CalledProcessError:
            print(f"\n❌ Failed to build for target {target}. Please check the output above.")
            return

    print(f"\n✅ Successfully built mathoku-core for all targets (profile: {profile}).")


@await_enter
def build_kotlin_wrapper(profile: str) -> None:
    """Builds the Kotlin wrapper for the mathoku-core crate."""
    print("Building Kotlin wrapper...")
    wrapper_path = PROJECT_ROOT / "mathoku-kotlin-rust-wrapper"
    if not wrapper_path.is_dir():
        print(f"\n❌ Error: mathoku-kotlin-rust-wrapper directory not found at {wrapper_path}")
        return

    cmd_base = ["gradlew.bat"] if IS_WINDOWS else ["./gradlew"]

    if profile == "release":
        cmd_base.append(":assembleRelease")
    elif profile == "debug":
        cmd_base.append(":assembleDebug")
    else:
        print(f"\n❌ Error: Invalid profile '{profile}'. Use 'debug' or 'release'.")
        return

    try:
        print(">>", " ".join(map(str, cmd_base)), f"(in {wrapper_path})", flush=True)
        subprocess.check_call(cmd_base, cwd=wrapper_path, shell=True)
    except subprocess.CalledProcessError:
        print("\n❌ Failed to build Kotlin wrapper. Please check the output above.")
        return

    print("\n✅ Successfully built Kotlin wrapper.")


@await_enter
def run_application() -> None:
    """Runs the Mathoku android app."""
    print("Running Mathoku android app...")
    react_native_app_path = PROJECT_ROOT / "mathoku_ui"
    if not react_native_app_path.is_dir():
        print(f"\n❌ Error: mathoku_ui directory not found at {react_native_app_path}")
        return

    run_cmd = ["npm", "install"]
    try:
        print(">>", " ".join(map(str, run_cmd)), f"(in {react_native_app_path})", flush=True)
        subprocess.check_call(run_cmd, cwd=react_native_app_path, shell=True)
    except subprocess.CalledProcessError:
        print("\n❌ Failed to install Mathoku android app. Please check the output above.")
        return

    run_cmd = ["npm", "run", "android"]
    try:
        print(">>", " ".join(map(str, run_cmd)), f"(in {react_native_app_path})", flush=True)
        subprocess.check_call(run_cmd, cwd=react_native_app_path, shell=True)
    except subprocess.CalledProcessError:
        print("\n❌ Failed to run Mathoku android app. Please check the output above.")
        return

    print("\n✅ Successfully started Mathoku android app.")


# ------ Environment Components ------

def get_environment_components() -> list[EnvComponent]:
    """
    Returns a list of environment components that need to be validated and set up.
    """
    return [
        RustupAndroidTargetsComponent(),
        TypeshareComponent(),
        AndroidSdkComponent(),
        JavaEnvironmentComponent()
    ]


def success_or_failure(task_type):
    def decorator(func: Callable[..., bool]):
        def inner(self, *args, **kwargs) -> bool:
            task = f"{self.display_name} {task_type}"
            print(f"\nPerforming {task}...")
            success = func(self, *args, **kwargs)
            print(success_or_failure_text_builder(task, success, prefix=""))
            return success
        return inner
    return decorator


class EnvComponent:
    __metaclass__ = abc.ABCMeta

    def __init__(self, display_name="EnvComponent"):
        self.display_name = display_name

    def __init_subclass__(cls):
        method_name_map = {
            cls.validate_pre_set_up: "pre-setup validation",
            cls.set_up: "setup",
            cls.validate_set_up: "setup validation",
        }
        for method, task_type in method_name_map.items():
            setattr(cls, method.__name__, success_or_failure(task_type)(method))

    @abc.abstractmethod
    def validate_pre_set_up(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")

    @abc.abstractmethod
    def set_up(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")

    @abc.abstractmethod
    def validate_set_up(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")


class RustupAndroidTargetsComponent(EnvComponent):
    def __init__(self):
        super().__init__("Rustup Android targets")

    def validate_pre_set_up(self) -> bool:
        try:
            subprocess.check_output(["rustup", "--version"], text=True)
            return True
        except subprocess.CalledProcessError:
            print("\n❌ Rustup is not installed or not found in PATH.")
            return False

    def set_up(self) -> bool:
        try:
            run(["rustup", "target", "add"] + ANDROID_RUSTUP_TARGETS)
            return True
        except subprocess.CalledProcessError:
            return False

    def validate_set_up(self) -> bool:
        installed_targets = []
        success = False
        try:
            rustup_output = subprocess.check_output(["rustup", "target", "list", "--installed"], text=True)
            installed_targets = [line.split()[0] for line in rustup_output.strip().splitlines()]
            success = True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to list Rustup targets: {e}", file=sys.stderr)
            return False
        finally:
            for target in ANDROID_RUSTUP_TARGETS:
                if target not in installed_targets:
                    print(f"\n❌ Target {target} is not installed.")
                    success = False
        return success


class TypeshareComponent(EnvComponent):
    def validate_pre_set_up(self) -> bool:
        try:
            subprocess.check_output(["cargo", "-V"], text=True)
            return True
        except subprocess.CalledProcessError:
            print("Cargo is not installed or not found in PATH.")
            return False

    def set_up(self) -> bool:
        print("Setting up Typeshare...")
        try:
            run(["cargo", "install", "typeshare-cli"])
            print("Typeshare set up successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to set up Typeshare: {e}", file=sys.stderr)
            return False

    def validate_set_up(self) -> bool:
        try:
            cargo_output = subprocess.check_output(["cargo", "install", "--list"], text=True)
            installed_components = [line.split()[0] for line in cargo_output.strip().splitlines()]
        except subprocess.CalledProcessError as e:
            print(f"Failed to list Cargo components: {e}", file=sys.stderr)
            return False

        return "typeshare-cli" in installed_components


class AndroidSdkComponent(EnvComponent):
    def __init__(self):
        super().__init__("Android sdk")

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
    def __init__(self):
        super().__init__("Java environment")

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

        with open(jdk_version_file) as f:
            content = f.read()
            if "JAVA_VERSION=\"17" not in content:
                print("JAVA_HOME does not point to JDK 17.")
                return False

        return True


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
