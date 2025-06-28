"""
AI Tools - Tools for AI-assisted development.

This module provides tools that use AI models to help with development tasks
like fixing tests and explaining code.
"""

from fastmcp import Context

from uvmgr.core import paths, process
from uvmgr.mcp._mcp_instance import mcp
from uvmgr.mcp.server import OperationResult
from uvmgr.ops import ai as ai_ops

# -----------------------------------------------------------------------------
# AI Tools
# -----------------------------------------------------------------------------


@mcp.tool()
async def ai_fix_tests(
    ctx: Context,
    model: str = "ollama/qwen3:latest",
) -> str:
    """
    Use AI to suggest fixes for failing tests.

    Parameters
    ----------
    - ctx: MCP context
    - model: AI model to use
    """
    try:
        await ctx.info("Analyzing failing tests with AI...")

        # First run tests to get failures
        test_output = process.run(["pytest", "-v"], capture=True)

        if test_output and "failed" in test_output.lower():
            # Use AI to analyze
            result = ai_ops.fix_tests(model)

            return OperationResult(
                success=True, message="AI analysis complete", details={"analysis": result}
            ).to_string()
        return OperationResult(
            success=True, message="All tests are passing!", details={}
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False, message="Failed to analyze tests", details={"error": str(e)}
        ).to_string()


@mcp.tool()
async def ai_explain_code(
    ctx: Context,
    file_path: str,
    model: str = "ollama/qwen3:latest",
) -> str:
    """
    Use AI to explain code in a file.

    Parameters
    ----------
    - ctx: MCP context
    - file_path: Path to file to explain
    - model: AI model to use
    """
    try:
        await ctx.info(f"Getting AI explanation for: {file_path}")
        # Read file
        full_path = paths.project_root() / file_path
        if not full_path.exists():
            return OperationResult(
                success=False, message="File not found", details={"path": file_path}
            ).to_string()

        content = full_path.read_text(encoding="utf-8")
        prompt = f"Explain this Python code:\n\n{content}"

        explanation = ai_ops.ask(model, prompt)

        return OperationResult(
            success=True, message="Code explanation generated", details={"explanation": explanation}
        ).to_string()

    except Exception as e:
        return OperationResult(
            success=False,
            message="Failed to explain code",
            details={"error": str(e), "file": file_path},
        ).to_string()
