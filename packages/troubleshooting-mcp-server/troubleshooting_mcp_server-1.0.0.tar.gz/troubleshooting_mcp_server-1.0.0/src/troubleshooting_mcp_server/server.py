"""
Troubleshooting MCP Server

A Model Context Protocol server that provides system troubleshooting and diagnostic tools.
"""

from mcp.server.fastmcp import FastMCP
import os
import subprocess
import json
import platform
import socket
import time
from datetime import datetime
from pathlib import Path

# Initialize the MCP server
mcp = FastMCP("Troubleshooting MCP Server")

# Security: Define allowed directories for log access
ALLOWED_LOG_DIRS = [
    os.path.expanduser("~/Library/Logs"),  # macOS system logs
    os.path.expanduser("~/Desktop"),       # Desktop files
    "/var/log",                           # System logs (if accessible)
    "/tmp",                               # Temporary files
    os.path.expanduser("~/.npm/_logs"),   # npm logs
    os.path.expanduser("~/Library/Application Support"), # App data
    os.path.expanduser("~/.local/share"), # Linux app data
    os.path.expanduser("~/AppData/Local"), # Windows app data
]

def is_path_allowed(path: str) -> bool:
    """Check if path is within allowed directories."""
    try:
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(allowed_dir)) 
                  for allowed_dir in ALLOWED_LOG_DIRS)
    except Exception:
        return False

@mcp.tool()
def read_log_file(file_path: str) -> str:
    """Read and return the contents of a log file with security checks."""
    try:
        if not is_path_allowed(file_path):
            return f"Error: Access denied to {file_path}. Path outside allowed directories."
        
        if not os.path.exists(file_path):
            return f"Error: Log file {file_path} does not exist."
        
        # Check file size to prevent reading huge files
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return f"Error: File too large ({file_size / 1024 / 1024:.2f} MB). Use tail_log_file for large files."
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            return f"Log file: {file_path}\nSize: {file_size} bytes\n\n{content}"
    except Exception as e:
        return f"Error reading log file: {str(e)}"

@mcp.tool()
def tail_log_file(file_path: str, lines: int = 50) -> str:
    """Read the last N lines of a log file."""
    try:
        if not is_path_allowed(file_path):
            return f"Error: Access denied to {file_path}."
        
        if not os.path.exists(file_path):
            return f"Error: Log file {file_path} does not exist."
        
        # Use platform-appropriate tail command
        if platform.system() == "Windows":
            # Windows doesn't have tail, use PowerShell
            cmd = f'powershell "Get-Content \'{file_path}\' -Tail {lines}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            # Unix-like systems (macOS, Linux)
            result = subprocess.run(['tail', '-n', str(lines), file_path], 
                                  capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Last {lines} lines of {file_path}:\n\n{result.stdout}"
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Error tailing log file: {str(e)}"

@mcp.tool()
def get_system_info() -> str:
    """Retrieve comprehensive system information."""
    try:
        info = []
        info.append(f"System: {platform.system()} {platform.release()}")
        info.append(f"Machine: {platform.machine()}")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Python: {platform.python_version()}")
        info.append(f"Platform: {platform.platform()}")
        
        # Get system uptime (platform-specific)
        try:
            if platform.system() == "Darwin":  # macOS
                uptime_result = subprocess.run(['uptime'], capture_output=True, text=True)
            elif platform.system() == "Linux":
                uptime_result = subprocess.run(['uptime'], capture_output=True, text=True)
            elif platform.system() == "Windows":
                uptime_result = subprocess.run(['systeminfo'], capture_output=True, text=True)
            else:
                uptime_result = None
            
            if uptime_result and uptime_result.returncode == 0:
                info.append(f"Uptime: {uptime_result.stdout.strip()}")
        except Exception:
            pass
        
        return "\n".join(info)
    except Exception as e:
        return f"Error retrieving system info: {str(e)}"

@mcp.tool()
def get_resource_usage() -> str:
    """Get current system resource usage using built-in tools."""
    try:
        info = []
        
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # CPU and memory info using top
            top_result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                      capture_output=True, text=True, timeout=10)
            if top_result.returncode == 0:
                lines = top_result.stdout.split('\n')
                for line in lines[:10]:  # First 10 lines contain system info
                    if 'CPU usage' in line or 'PhysMem' in line or 'Load Avg' in line:
                        info.append(line.strip())
        
        elif system == "Linux":
            # Use free and top for Linux
            free_result = subprocess.run(['free', '-h'], capture_output=True, text=True)
            if free_result.returncode == 0:
                info.append("Memory Usage:")
                info.append(free_result.stdout)
            
            # Load average
            try:
                with open('/proc/loadavg', 'r') as f:
                    load_avg = f.read().strip()
                    info.append(f"Load Average: {load_avg}")
            except Exception:
                pass
        
        elif system == "Windows":
            # Use wmic for Windows
            try:
                mem_result = subprocess.run(['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory'], 
                                          capture_output=True, text=True)
                if mem_result.returncode == 0:
                    info.append("Memory Info:")
                    info.append(mem_result.stdout)
            except Exception:
                pass
        
        # Disk usage (cross-platform)
        try:
            if system == "Windows":
                df_result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace,caption'], 
                                         capture_output=True, text=True)
            else:
                df_result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            
            if df_result.returncode == 0:
                info.append("\nDisk Usage:")
                info.append(df_result.stdout)
        except Exception:
            pass
        
        return "\n".join(info) if info else "Unable to retrieve resource usage"
    except Exception as e:
        return f"Error retrieving resource usage: {str(e)}"

@mcp.tool()
def run_diagnostic_command(command: str) -> str:
    """Run a system diagnostic command safely."""
    # Platform-specific safe commands
    safe_commands = []
    system = platform.system()
    
    if system == "Darwin":  # macOS
        safe_commands.extend([
            'system_profiler SPHardwareDataType',
            'system_profiler SPSoftwareDataType', 
            'system_profiler SPDisplaysDataType',
            'brew --version',
            'sw_vers'
        ])
    elif system == "Linux":
        safe_commands.extend([
            'lsb_release -a',
            'uname -a',
            'lscpu',
            'lsmem'
        ])
    elif system == "Windows":
        safe_commands.extend([
            'systeminfo',
            'ver',
            'wmic cpu get name',
            'wmic computersystem get model,name,manufacturer'
        ])
    
    # Common cross-platform commands
    safe_commands.extend([
        'node --version',
        'npm --version',
        'python3 --version',
        'python --version',
        'git --version',
        'which python3',
        'which node',
        'which npm',
        'ps aux | head -20',
        'netstat -an | head -20'
    ])
    
    # Check if command is in safe list or starts with safe prefix
    safe_prefixes = ['system_profiler', 'brew list', 'npm list', 'pip list', 'which ', 'wmic ']
    
    is_safe = (command in safe_commands or 
              any(command.startswith(prefix) for prefix in safe_prefixes))
    
    if not is_safe:
        return f"Error: Command '{command}' not in safe command list. Available commands include: {', '.join(safe_commands[:5])}..."
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, 
                              text=True, timeout=30)
        output = f"Command: {command}\nReturn code: {result.returncode}\n\n"
        if result.stdout:
            output += f"Output:\n{result.stdout}\n"
        if result.stderr:
            output += f"Errors:\n{result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Command '{command}' timed out after 30 seconds"
    except Exception as e:
        return f"Error running command: {str(e)}"

@mcp.tool()
def check_network_connectivity(url: str, timeout: int = 5) -> str:
    """Check network connectivity to a URL or host."""
    try:
        # Parse URL to get host and port
        if url.startswith(('http://', 'https://')):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        else:
            # Assume it's just a hostname
            host = url
            port = 80
        
        # Test socket connection
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((host, port))
        end_time = time.time()
        sock.close()
        
        if result == 0:
            return f"✓ Connection to {host}:{port} successful\nResponse time: {(end_time - start_time)*1000:.2f}ms"
        else:
            return f"✗ Connection to {host}:{port} failed\nError code: {result}"
            
    except Exception as e:
        return f"Error checking connectivity to {url}: {str(e)}"

@mcp.tool()
def check_process_status(process_name: str) -> str:
    """Check if a process is running."""
    try:
        system = platform.system()
        
        if system == "Windows":
            # Use tasklist for Windows
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}*'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and process_name.lower() in result.stdout.lower():
                return f"✓ Process '{process_name}' is running\n\n{result.stdout}"
            else:
                return f"✗ Process '{process_name}' not found"
        else:
            # Use pgrep for Unix-like systems
            result = subprocess.run(['pgrep', '-f', process_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                info = f"✓ Process '{process_name}' is running\nPIDs: {', '.join(pids)}\n\n"
                
                # Get detailed info for each PID
                for pid in pids[:3]:  # Limit to first 3 processes
                    ps_result = subprocess.run(['ps', '-p', pid, '-o', 'pid,ppid,cpu,mem,command'], 
                                             capture_output=True, text=True)
                    if ps_result.returncode == 0:
                        info += ps_result.stdout
                return info
            else:
                return f"✗ Process '{process_name}' not found"
    except Exception as e:
        return f"Error checking process status: {str(e)}"

@mcp.tool()
def find_log_files(app_name: str) -> str:
    """Find log files for a specific application."""
    try:
        system = platform.system()
        log_locations = []
        
        if system == "Darwin":  # macOS
            log_locations = [
                f"~/Library/Logs/{app_name}",
                f"~/Library/Application Support/{app_name}",
                f"/var/log/{app_name}",
                f"~/Desktop/*{app_name}*log*",
                f"/tmp/*{app_name}*log*"
            ]
        elif system == "Linux":
            log_locations = [
                f"~/.local/share/{app_name}",
                f"~/.config/{app_name}",
                f"/var/log/{app_name}",
                f"~/Desktop/*{app_name}*log*",
                f"/tmp/*{app_name}*log*"
            ]
        elif system == "Windows":
            log_locations = [
                f"~/AppData/Local/{app_name}",
                f"~/AppData/Roaming/{app_name}",
                f"~/Desktop/*{app_name}*log*"
            ]
        
        found_logs = []
        for location in log_locations:
            expanded_path = os.path.expanduser(location)
            
            # Handle wildcards
            if '*' in expanded_path:
                import glob
                matches = glob.glob(expanded_path)
                found_logs.extend(matches)
            else:
                if os.path.exists(expanded_path):
                    if os.path.isdir(expanded_path):
                        # List log files in directory
                        try:
                            for file in os.listdir(expanded_path):
                                if file.endswith(('.log', '.txt', '.out', '.err')):
                                    found_logs.append(os.path.join(expanded_path, file))
                        except PermissionError:
                            found_logs.append(f"Permission denied: {expanded_path}")
                    else:
                        found_logs.append(expanded_path)
        
        if found_logs:
            return f"Found log files for '{app_name}':\n" + "\n".join(found_logs)
        else:
            return f"No log files found for '{app_name}' in common locations"
    except Exception as e:
        return f"Error finding log files: {str(e)}"

@mcp.tool()
def get_environment_info() -> str:
    """Get environment variables and development tool versions."""
    try:
        info = []
        
        # Important environment variables
        env_vars = ['PATH', 'NODE_ENV', 'PYTHON_PATH', 'JAVA_HOME', 'HOME', 'USER']
        if platform.system() == "Windows":
            env_vars.extend(['USERPROFILE', 'APPDATA', 'LOCALAPPDATA'])
        
        info.append("Environment Variables:")
        for var in env_vars:
            value = os.environ.get(var, 'Not set')
            # Truncate long PATH variables
            if var == 'PATH' and len(value) > 200:
                value = value[:200] + "... (truncated)"
            info.append(f"  {var}: {value}")
        
        # Development tools
        info.append("\nDevelopment Tools:")
        tools = [
            ('Node.js', 'node --version'),
            ('npm', 'npm --version'),
            ('Python3', 'python3 --version'),
            ('Python', 'python --version'),
            ('Git', 'git --version'),
        ]
        
        # Add platform-specific tools
        if platform.system() == "Darwin":
            tools.append(('Homebrew', 'brew --version'))
        elif platform.system() == "Linux":
            tools.append(('apt', 'apt --version'))
        
        for tool_name, command in tools:
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info.append(f"  {tool_name}: {result.stdout.strip()}")
                else:
                    info.append(f"  {tool_name}: Not found or error")
            except Exception:
                info.append(f"  {tool_name}: Not found")
        
        return "\n".join(info)
    except Exception as e:
        return f"Error getting environment info: {str(e)}"

def test_tools():
    """Test the troubleshooting server tools locally."""
    print("Testing Troubleshooting MCP Server tools...")
    print(f"Timestamp: {datetime.now()}")
    print(f"Platform: {platform.system()}")
    
    print("\n1. Testing get_system_info:")
    print(get_system_info())
    
    print("\n2. Testing get_resource_usage:")
    print(get_resource_usage())
    
    print("\n3. Testing check_network_connectivity:")
    print(check_network_connectivity("google.com"))
    
    print("\n4. Testing get_environment_info:")
    print(get_environment_info())
    
    print("\n5. Testing find_log_files:")
    print(find_log_files("node"))

def main():
    """Main entry point for the server."""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_tools()
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()