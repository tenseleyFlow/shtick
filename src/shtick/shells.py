"""
Shell syntax definitions for shtick
"""


class ShellSyntax:
    """Holds syntax patterns for different shell types"""

    def __init__(self, name, alias_fmt, env_fmt, function_fmt):
        self.name = name
        self.alias_fmt = alias_fmt
        self.env_fmt = env_fmt
        self.function_fmt = function_fmt


# Shell syntax table - using the most natural syntax for each type
SHELLS = {
    "bash": ShellSyntax(
        "bash",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "zsh": ShellSyntax(
        "zsh",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "fish": ShellSyntax(
        "fish",
        alias_fmt="alias {} '{}'\n",
        env_fmt="set -x {} '{}'\n",
        function_fmt="function {}\n    {}\nend\n",
    ),
    "ksh": ShellSyntax(
        "ksh",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "mksh": ShellSyntax(
        "mksh",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "yash": ShellSyntax(
        "yash",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "dash": ShellSyntax(
        "dash",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "csh": ShellSyntax(
        "csh",
        alias_fmt="alias {} '{}'\n",
        env_fmt="setenv {} '{}'\n",
        function_fmt="# csh doesn't support functions - skipping {}\n",
    ),
    "tcsh": ShellSyntax(
        "tcsh",
        alias_fmt="alias {} '{}'\n",
        env_fmt="setenv {} '{}'\n",
        function_fmt="# tcsh doesn't support functions - skipping {}\n",
    ),
    "xonsh": ShellSyntax(
        "xonsh",
        alias_fmt="aliases['{}'] = '{}'\n",
        env_fmt="${} = '{}'\n",
        function_fmt="def {}():\n    return '{}'\n",
    ),
    "elvish": ShellSyntax(
        "elvish",
        alias_fmt="fn {} {{ {} }}\n",
        env_fmt="E:{} = '{}'\n",
        function_fmt="fn {} {{ {} }}\n",
    ),
    "rc": ShellSyntax(
        "rc",
        alias_fmt="fn {} {{ {} }}\n",
        env_fmt="{}='{}'\n",
        function_fmt="fn {} {{ {} }}\n",
    ),
    "es": ShellSyntax(
        "es",
        alias_fmt="fn-{} = {{ {} }}\n",
        env_fmt="{}='{}'\n",
        function_fmt="fn-{} = {{ {} }}\n",
    ),
    "nushell": ShellSyntax(
        "nushell",
        alias_fmt="alias {} = {}\n",
        env_fmt="let-env {} = '{}'\n",
        function_fmt="def {} [] {{ {} }}\n",
    ),
    "powershell": ShellSyntax(
        "powershell",
        alias_fmt="Set-Alias -Name {} -Value '{}'\n",
        env_fmt="$env:{} = '{}'\n",
        function_fmt="function {} {{ {} }}\n",
    ),
    "oil": ShellSyntax(
        "oil",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
    "default": ShellSyntax(
        "default",
        alias_fmt="alias {}='{}'\n",
        env_fmt="export {}='{}'\n",
        function_fmt="{}() {{\n    {}\n}}\n",
    ),
}


def get_supported_shells():
    """Return list of supported shell names (excluding default)"""
    return [name for name in SHELLS.keys() if name != "default"]


def get_shell_syntax(shell_name):
    """Get syntax for a specific shell, falling back to default"""
    return SHELLS.get(shell_name, SHELLS["default"])
