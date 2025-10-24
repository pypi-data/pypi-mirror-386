# Troubleshooting MCP Server

A Model Context Protocol (MCP) server that provides system troubleshooting and diagnostic tools for developers and system administrators.

## Features

- **System Information**: Get comprehensive system details including OS, hardware, and software versions
- **Resource Monitoring**: Check CPU, memory, and disk usage
- **Log File Access**: Read and tail log files from common system locations
- **Network Diagnostics**: Test connectivity to hosts and services
- **Process Management**: Check if processes are running and get detailed information
- **Environment Analysis**: Inspect environment variables and development tool versions
- **Safe Command Execution**: Run whitelisted diagnostic commands securely

## Installation

### Using uvx (recommended)

```bash
uvx troubleshooting-mcp-server
```

### Using pip

```bash
pip install troubleshooting-mcp-server
```

### From source

```bash
git clone https://github.com/yourusername/troubleshooting-mcp-server
cd troubleshooting-mcp-server
pip install -e .
```

## Usage

### As an MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "troubleshooting": {
      "command": "uvx",
      "args": ["troubleshooting-mcp-server"],
      "env": {}
    }
  }
}
```

### Standalone Testing

```bash
python -m troubleshooting_mcp_server.server test
```

## Available Tools

### System Information
- `get_system_info()`: Get OS, hardware, and software details
- `get_resource_usage()`: Monitor CPU, memory, and disk usage
- `get_environment_info()`: Check environment variables and tool versions

### Log Management
- `read_log_file(file_path)`: Read complete log files (with size limits)
- `tail_log_file(file_path, lines=50)`: Get last N lines of a log file
- `find_log_files(app_name)`: Locate log files for specific applications

### Network & Process Diagnostics
- `check_network_connectivity(url, timeout=5)`: Test network connections
- `check_process_status(process_name)`: Check if processes are running
- `run_diagnostic_command(command)`: Execute safe diagnostic commands

## Security Features

- **Path Restrictions**: Log file access limited to safe directories
- **Command Whitelist**: Only approved diagnostic commands can be executed
- **File Size Limits**: Large files require using tail function
- **Timeout Protection**: Commands have execution time limits

## Supported Platforms

- macOS (primary support)
- Linux (basic support)
- Windows (limited support)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker.