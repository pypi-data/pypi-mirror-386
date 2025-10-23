import json
import os
import pathlib
import re
from typing import Required, TypedDict

import cyclopts
import yaml

APP = cyclopts.App(name="claudebook")

RUN_PROMPT = """\
You are about to be given a markdown document documenting a procedure.

Your task is to follow the procedure step-by-step, ensuring that each step is completed accurately and thoroughly.

If you encounter any issues or errors, you should troubleshoot them and try to resolve them before moving on to the next step.

If you are unsure about how to proceed, you can ask for help from the user.

<RUNBOOK>
{RUNBOOK}
</RUNBOOK>
"""


class StdioMCPConfig(TypedDict, total=False):
    command: Required[str]
    args: list[str]
    env: dict[str, str]


# @TODO: Other MCP types


class Config(TypedDict, total=False):
    mcp: dict[str, StdioMCPConfig]


def _extract_config(contents: str) -> tuple[Config, str]:
    match = next(
        re.finditer(r"\n```yaml\n(.*?)\n```\n", contents, re.MULTILINE | re.DOTALL),
        None,
    )
    if not match:
        return {}, contents

    raw = match.group(1)
    config = yaml.safe_load(raw)
    for server_config in config.values():
        server_config.setdefault("type", "stdio")
        # server_config.setdefault("args", [])
        # server_config.setdefault("env", {})
    return yaml.safe_load(raw), contents[match.end(0) :]


def _write_to_stdin(s: str) -> None:
    r, w = os.pipe()
    os.write(w, s.encode())
    os.close(w)
    os.dup2(r, 0)
    os.close(r)


# @TODO: Commands for interactive or not
@APP.command
def run(path: str):
    markdown = pathlib.Path(path).read_text()
    config, markdown = _extract_config(markdown)

    argv: list[str] = []
    if mcp_config := config.get("mcp", None):
        argv.extend(["--mcp-config", json.dumps({"mcpServers": mcp_config})])
        argv.extend(
            [
                "--allowed-tools",
                ",".join(f"mcp__{servername}__*" for servername in mcp_config.keys()),
            ]
        )

    _write_to_stdin(RUN_PROMPT.format(RUNBOOK=markdown))
    os.execlp("claude", "claude", *argv)


# @TODO: Other commands (like `improve` or `mcp add`)

if __name__ == "__main__":
    APP()
