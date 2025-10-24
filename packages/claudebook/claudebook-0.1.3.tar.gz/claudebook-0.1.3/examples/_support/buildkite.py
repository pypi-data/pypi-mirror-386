"""A fake Buildkite MCP server (for demo purposes)."""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp",
# ]
# ///
#
import textwrap

from fastmcp import FastMCP

mcp = FastMCP("buildkite")


@mcp.tool
def get_logs(build: int) -> str:
    """Get the logs for the Buildkite build"""
    return textwrap.dedent(
        """\
        (00:05:27) INFO: Build completed, 1 tests FAILED, 77 total actions
        //thing:tests/app_test                                                    FAILED in 0.2s
          /var/lib/buildkite-agent/.cache/bazel/_bazel_buildkite-agent/ec321eb2cc2d0f8f91b676b6d4c66c29/execroot/_main/bazel-out/k8-fastbuild/testlogs/absl/tests/app_test/test.log
        """
    )


if __name__ == "__main__":
    mcp.run()
