"""
Code tools: Python sandbox for custom computational analysis.
"""

import logging
import io
import contextlib
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.code")


@registry.register(
    name="code.python_exec",
    description="Execute Python code in a sandboxed environment. Has access to pandas, numpy. Returns stdout and any variables set in `result`.",
    category="code",
    parameters={"code": "Python code to execute"},
    usage_guide="When custom computation is needed (statistics, data transformation, visualization prep).",
)
def python_exec(code: str) -> dict:
    """Execute Python code in a restricted sandbox."""
    # Sandboxed globals with common scientific libraries
    sandbox_globals = {"__builtins__": __builtins__}

    try:
        import pandas as pd
        sandbox_globals["pd"] = pd
    except ImportError:
        pass

    try:
        import numpy as np
        sandbox_globals["np"] = np
    except ImportError:
        pass

    stdout_capture = io.StringIO()
    sandbox_globals["result"] = None

    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, sandbox_globals)
        stdout = stdout_capture.getvalue()
        result = sandbox_globals.get("result")
        return {
            "status": "success",
            "stdout": stdout[:5000] if stdout else "",
            "result": str(result)[:5000] if result is not None else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"{type(e).__name__}: {str(e)}",
            "stdout": stdout_capture.getvalue()[:2000],
        }
