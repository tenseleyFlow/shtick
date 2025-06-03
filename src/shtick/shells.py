"""
Shell syntax definitions for shtick - SECURE VERSION
"""

import shlex
from typing import Callable


class ShellSyntax:
    """Holds syntax patterns for different shell types with secure escaping"""

    def __init__(
        self,
        name: str,
        alias_fmt: Callable[[str, str], str],
        env_fmt: Callable[[str, str], str],
        function_fmt: Callable[[str, str], str],
    ):
        self.name = name
        self.alias_fmt = alias_fmt
        self.env_fmt = env_fmt
        self.function_fmt = function_fmt


# Helper function for safe function body handling
def escape_function_body(body: str) -> str:
    """Escape function body - less aggressive than shlex.quote for function contents"""
    # For function bodies, we need to be more careful - they often contain
    # complex commands that shouldn't be over-escaped
    # This is a simplified approach - in production you might want more sophisticated handling
    return body.replace("'", "'\"'\"'")


# Shell syntax table - using secure escaping with lambdas
SHELLS = {
    "bash": ShellSyntax(
        "bash",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "zsh": ShellSyntax(
        "zsh",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "fish": ShellSyntax(
        "fish",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)} {shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"set -x {shlex.quote(k)} {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"function {shlex.quote(k)}\n    {escape_function_body(v)}\nend\n",
    ),
    "ksh": ShellSyntax(
        "ksh",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "mksh": ShellSyntax(
        "mksh",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "yash": ShellSyntax(
        "yash",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "dash": ShellSyntax(
        "dash",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "csh": ShellSyntax(
        "csh",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)} {shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"setenv {shlex.quote(k)} {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"# csh doesn't support functions - skipping {shlex.quote(k)}\n",
    ),
    "tcsh": ShellSyntax(
        "tcsh",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)} {shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"setenv {shlex.quote(k)} {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"# tcsh doesn't support functions - skipping {shlex.quote(k)}\n",
    ),
    "xonsh": ShellSyntax(
        "xonsh",
        alias_fmt=lambda k, v: f"aliases[{shlex.quote(k)}] = {shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"${{{shlex.quote(k)}}} = {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"def {shlex.quote(k)}():\n    return {shlex.quote(v)}\n",
    ),
    "elvish": ShellSyntax(
        "elvish",
        alias_fmt=lambda k, v: f"fn {shlex.quote(k)} {{ {escape_function_body(v)} }}\n",
        env_fmt=lambda k, v: f"E:{shlex.quote(k)} = {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"fn {shlex.quote(k)} {{ {escape_function_body(v)} }}\n",
    ),
    "rc": ShellSyntax(
        "rc",
        alias_fmt=lambda k, v: f"fn {shlex.quote(k)} {{ {escape_function_body(v)} }}\n",
        env_fmt=lambda k, v: f"{shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"fn {shlex.quote(k)} {{ {escape_function_body(v)} }}\n",
    ),
    "es": ShellSyntax(
        "es",
        alias_fmt=lambda k, v: f"fn-{shlex.quote(k)} = {{ {escape_function_body(v)} }}\n",
        env_fmt=lambda k, v: f"{shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"fn-{shlex.quote(k)} = {{ {escape_function_body(v)} }}\n",
    ),
    "nushell": ShellSyntax(
        "nushell",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)} = {escape_function_body(v)}\n",
        env_fmt=lambda k, v: f"let-env {shlex.quote(k)} = {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"def {shlex.quote(k)} [] {{ {escape_function_body(v)} }}\n",
    ),
    "powershell": ShellSyntax(
        "powershell",
        alias_fmt=lambda k, v: f"Set-Alias -Name {shlex.quote(k)} -Value {shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"$env:{shlex.quote(k)} = {shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"function {shlex.quote(k)} {{ {escape_function_body(v)} }}\n",
    ),
    "oil": ShellSyntax(
        "oil",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
    "default": ShellSyntax(
        "default",
        alias_fmt=lambda k, v: f"alias {shlex.quote(k)}={shlex.quote(v)}\n",
        env_fmt=lambda k, v: f"export {shlex.quote(k)}={shlex.quote(v)}\n",
        function_fmt=lambda k, v: f"{shlex.quote(k)}() {{\n    {escape_function_body(v)}\n}}\n",
    ),
}


def get_supported_shells():
    """Return list of supported shell names (excluding default)"""
    return [name for name in SHELLS.keys() if name != "default"]


def get_shell_syntax(shell_name):
    """Get syntax for a specific shell, falling back to default"""
    return SHELLS.get(shell_name, SHELLS["default"])
