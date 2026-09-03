"""AST boundary gate forbidding live control and network surfaces in the core package."""

from __future__ import annotations

import ast
import stat
from pathlib import Path

NETWORK_MODULES = {"socket", "requests", "httpx", "aiohttp", "ftplib", "smtplib", "telnetlib"}
DYNAMIC_CALLS = {"eval", "exec", "compile", "__import__"}
ROS_PUBLISHER_CALLS = {"create_publisher", "publish"}
CLIENT_CALLS = {
    "create_client",
    "create_service_client",
    "create_action_client",
    "send_goal",
    "send_goal_async",
    "call_async",
}
PLC_CALLS = {"write_plc", "plc_write", "write_register", "write_coil"}


def _call_name(node: ast.Call) -> str:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id.lower()
    if isinstance(function, ast.Attribute):
        return function.attr.lower()
    return ""


def _identifier_violation(name: str) -> str | None:
    normalized = name.lower()
    if normalized in {"controller_address", "controller_addr", "controller_uri", "controller_url"}:
        return "controller address"
    if normalized in {"machine_credentials", "machine_credential", "controller_credentials"}:
        return "machine credential"
    if normalized in {"remote_reset", "request_remote_reset", "send_remote_reset"}:
        return "remote reset"
    if normalized in {"reverse_control_callback", "control_callback", "command_callback"}:
        return "reverse-control callback"
    return None


def _scan_tree(path: Path, relative: str) -> list[str]:
    errors: list[str] = []
    try:
        tree = ast.parse(path.read_bytes(), filename=relative)
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        return [f"unscannable Python source: {relative}: {type(error).__name__}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in NETWORK_MODULES or root == "subprocess":
                    errors.append(
                        f"network client or process execution import: {relative}:{node.lineno}"
                    )
                if root in {"rclpy", "rospy", "roslib"}:
                    errors.append(f"ROS publisher/client import: {relative}:{node.lineno}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if (
                root in NETWORK_MODULES
                or root == "subprocess"
                or module.startswith("urllib.request")
            ):
                errors.append(
                    f"network client or process execution import: {relative}:{node.lineno}"
                )
            if root in {"rclpy", "rospy", "roslib"}:
                errors.append(f"ROS publisher/client import: {relative}:{node.lineno}")
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if isinstance(node.func, ast.Name) and name in DYNAMIC_CALLS:
                errors.append(f"dynamic execution: {relative}:{node.lineno}")
            if name in ROS_PUBLISHER_CALLS:
                errors.append(f"ROS publisher: {relative}:{node.lineno}")
            if name in CLIENT_CALLS:
                errors.append(f"service/action client: {relative}:{node.lineno}")
            plc_attribute_write = (
                isinstance(node.func, ast.Attribute)
                and node.func.attr.lower() in {"write", "send"}
                and isinstance(node.func.value, ast.Name)
                and "plc" in node.func.value.id.lower()
            )
            if name in PLC_CALLS or ("plc" in name and "write" in name) or plc_attribute_write:
                errors.append(f"PLC writer: {relative}:{node.lineno}")
            violation = _identifier_violation(name)
            if violation is not None:
                errors.append(f"{violation}: {relative}:{node.lineno}")
        elif isinstance(node, (ast.Name, ast.Attribute)):
            name = node.id if isinstance(node, ast.Name) else node.attr
            violation = _identifier_violation(name)
            if violation is not None:
                errors.append(f"{violation}: {relative}:{node.lineno}")
    return errors


def scan_core_boundary(package_root: Path) -> tuple[str, ...]:
    """Return stable source findings; comments and string documentation are ignored."""

    if not isinstance(package_root, Path) or not package_root.is_dir():
        return ("core package root is not a directory",)
    errors: list[str] = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).as_posix()
        try:
            metadata = path.lstat()
        except OSError:
            errors.append(f"unreadable Python source: {relative}")
            continue
        if stat.S_ISLNK(metadata.st_mode):
            errors.append(f"symlinked Python source: {relative}")
            continue
        if not stat.S_ISREG(metadata.st_mode):
            errors.append(f"non-regular Python source: {relative}")
            continue
        errors.extend(_scan_tree(path, relative))
    return tuple(sorted(set(errors)))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = scan_core_boundary(root / "src" / "oscillink_safety_ops")
    if errors:
        raise SystemExit("\n".join(errors))
    print("runtime boundary: ok")


if __name__ == "__main__":
    main()
