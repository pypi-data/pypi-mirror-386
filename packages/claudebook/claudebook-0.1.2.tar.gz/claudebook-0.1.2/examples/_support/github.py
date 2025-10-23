"""A fake GitHub MCP server (for demo purposes)."""
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp",
# ]
# ///
#

from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("github")


@mcp.tool
def get_pr_contexts(pr_num: int) -> dict[str, Any]:
    """Get the contexts from a GitHub PR"""
    return {
        "buildkite/CI": {
            "status": "failure",
            "url": "https://buildkite.com/org/pipeline/builds/123",
            "description": "Build failed in 3m",
        }
    }


if __name__ == "__main__":
    mcp.run()
