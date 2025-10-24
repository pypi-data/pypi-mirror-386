"""
Utility functions for SFNX library.
"""
import json
import platform
import shutil
import subprocess
from typing import Optional, List, Any, Dict, Union


def find_sf_executable() -> Optional[str]:
    """Find the Salesforce CLI executable in the system PATH.
    
    Returns:
        Optional[str]: The path to the SF CLI executable if found, None otherwise
    """
    if platform.system() == "Windows":
        # On Windows, try different possible executable names
        for exe_name in ['sf.cmd', 'sf.exe', 'sf']:
            executable_path = shutil.which(exe_name)
            if executable_path:
                return executable_path
    else:
        # On Unix-like systems, just use 'sf'
        return shutil.which('sf')
    
    return None


def sf_run(command: str, params: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """Run a Salesforce CLI command with automatic JSON output and error handling.
    
    Args:
        command: SF CLI command (e.g., 'data query', 'org display')
        params: Dictionary of parameters to pass as --key value pairs
        **kwargs: Additional arguments to pass to subprocess.run
        
    Returns:
        Dict[str, Any]: Parsed JSON result from the command
        
    Raises:
        RuntimeError: If Salesforce CLI is not found or command fails
    """
    sf_executable = find_sf_executable()
    if sf_executable is None:
        raise RuntimeError("Salesforce CLI not found in PATH")
    
    # Build command arguments
    args = command.split()
    
    # Add parameters as --key value pairs
    if params:
        for key, value in params.items():
            args.extend([f'--{key}', str(value)])
    
    # Always add --json for consistent output
    args.append('--json')
    
    # Set default capture_output and text for JSON parsing
    kwargs.setdefault('capture_output', True)
    kwargs.setdefault('text', True)
    
    result = subprocess.run([sf_executable] + args, **kwargs)
    
    if result.returncode != 0:
        error_message = result.stderr or result.stdout or 'Unknown error'
        
        # Provide helpful error messages for common issues
        if "not found" in error_message.lower():
            raise RuntimeError(
                f"Salesforce CLI not found. Please ensure the Salesforce CLI is installed and available in your PATH. "
                f"Original error: {error_message}"
            )
        
        raise RuntimeError(f"SF CLI command failed: {error_message}")
    
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse SF CLI JSON output: {e}")
    
    if 'result' not in payload:
        raise RuntimeError("Unexpected SF CLI response: missing 'result' field")
    
    return payload['result']
