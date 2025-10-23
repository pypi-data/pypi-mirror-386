"""Shell command execution service"""

import asyncio
import subprocess
from typing import Tuple


class ShellService:
    """Service for executing shell commands in subprocess"""

    @staticmethod
    async def execute_command(command: str) -> Tuple[str, str, int]:
        """
        Execute a shell command asynchronously.

        Args:
            command: The shell command to execute (without the leading !)

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            # Run command in subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion and get output
            stdout_bytes, stderr_bytes = await process.communicate()

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return_code = process.returncode or 0

            return stdout, stderr, return_code

        except Exception as e:
            # If command execution fails, return error message
            return "", f"Failed to execute command: {str(e)}", 1
