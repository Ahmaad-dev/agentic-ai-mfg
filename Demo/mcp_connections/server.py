"""FastMCP server exposing the AP5 review tool adapter."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools

# Token-Validierung der MCP-Tools ist out-of-scope für PT4.
mcp = FastMCP(
    "PT4 Review Tools",
    instructions=(
        "Review pending correction proposals and inspect snapshot/dashboard status. "
        "Decision tools record the human decision; application stays in the existing UI workflow."
    ),
    json_response=True,
)

mcp.tool()(tools.get_pending_reviews)
mcp.tool()(tools.get_review_details)
mcp.tool()(tools.approve_correction)
mcp.tool()(tools.reject_correction)
mcp.tool()(tools.modify_correction)
mcp.tool()(tools.get_snapshot_status)
mcp.tool()(tools.get_dashboard_metrics)
mcp.tool()(tools.create_email_draft)
mcp.tool()(tools.get_email_draft)
mcp.tool()(tools.revise_email_draft)
mcp.tool()(tools.send_email_draft)
mcp.tool()(tools.cancel_email_draft)


def main() -> None:
    """Run the standard MCP stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
