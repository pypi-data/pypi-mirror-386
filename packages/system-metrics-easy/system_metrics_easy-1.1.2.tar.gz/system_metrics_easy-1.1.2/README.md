# System Metrics Easy

[![PyPI version](https://badge.fury.io/py/system-metrics-easy.svg)](https://badge.fury.io/py/system-metrics-easy)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](<https://github.com/hamzaig/system-metrics-easy/workflows/Build%20&%20Publish%20to%20(Test)PyPI/badge.svg>)](https://github.com/hamzaig/system-metrics-easy/actions)

A comprehensive server monitoring tool that collects and sends system metrics to a Socket.IO server. This tool provides real-time monitoring of CPU, memory, disk, network, and GPU usage across different platforms.

## Features

- **Real-time Metrics Collection**: CPU, memory, disk, network, and GPU statistics
- **Multi-Platform Support**: Works on Linux, macOS, and Windows
- **GPU Support**: NVIDIA, Apple Silicon, AMD, and Intel GPUs
- **Socket.IO Integration**: Real-time data transmission to your monitoring server
- **Robust Error Handling**: Graceful handling of system errors and missing dependencies
- **Easy Configuration**: Interactive configuration setup
- **Command Line Interface**: Simple command-line options
- **Background Process Management**: Built-in background running with PID management
- **Smart Reconnection**: Limited reconnection attempts with automatic exit on failure
- **Consecutive Failure Tracking**: Exits after 10 consecutive connection failures
- **Direct Execution Mode**: Simple `python index.py` execution without input prompts

## Installation

### From PyPI (Recommended)

```bash
# Install the package
pip install system-metrics-easy
```

### From TestPyPI (Latest Development)

```bash
# Install from TestPyPI (latest development version)
pip install -i https://test.pypi.org/simple/ system-metrics-easy

# If you have dependencies from regular PyPI
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ system-metrics-easy
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/hamzaig/system-metrics-easy.git
cd system-metrics-easy

# Install the package
pip install -e .
```

**Note**: Make sure you're in the `package` directory when running `pip install -e .` if you're working with the source code directly.

## Current Status

✅ **What Works Now:**

- Install from PyPI: `pip install system-metrics-easy`
- Install from TestPyPI: Latest development versions
- Install from source: `git clone` + `pip install -e .`
- Run the tool: `system-metrics-easy`
- All monitoring features work perfectly
- Background process management works
- **Automated deployment**: Push to main → TestPyPI, Tag releases → PyPI

🚀 **Automated Deployment:**

- **Push to `main` branch** → Automatically publishes to TestPyPI
- **Create version tag** (e.g., `v1.0.0`) → Automatically publishes to PyPI

## Quick Start (Super Simple!)

### Install and Run

```bash
# Install from PyPI (recommended)
pip install system-metrics-easy

# Run it - it will ask you for configuration and start in background!
system-metrics-easy
```

That's it! The script will:

1. **Ask you for configuration** (interval, server URL, server name)
2. **Start monitoring** in background automatically
3. **Save logs** to `system-metrics-easy.log`
4. **Handle all process management** for you

### Simple Commands

```bash
# Start monitoring (asks for config)
system-metrics-easy

# Check if it's running
system-metrics-easy --status

# Stop it
system-metrics-easy --stop
```

**That's it! Just simple commands: `system-metrics-easy`, `--status`, `--stop`**

### Direct Execution Mode (v1.1.0+)

For even simpler usage, you can run the script directly without any input prompts:

```bash
# Direct execution with default settings
python index.py

# Or with environment variables
TIME_INTERVAL=5 SOCKET_SERVER_URL=http://your-server:3000 python index.py
```

**Default Settings:**

- **Interval**: 10 seconds (or set via `TIME_INTERVAL` env var)
- **Server URL**: `http://localhost:8000` (or set via `SOCKET_SERVER_URL` env var)
- **Server ID**: `server-{hostname}` (or set via `SERVER_ID` env var)

## Metrics Collected

### System Information

- Hostname, OS, architecture
- Python version, uptime, boot time

### CPU Metrics

- Total CPU usage percentage
- Per-core CPU usage
- Load average (1min, 5min, 15min)
- Core count

### Memory Metrics

- Total, used, free, and available memory (GB)
- Memory usage percentage
- Swap memory statistics

### Disk Metrics

- Disk usage for all mounted filesystems
- Total, used, and free space (GB)
- Usage percentage per partition

### Network Metrics

- Network throughput per second
- Bytes sent/received per second
- Total bytes sent/received (GB)
- Per-interface statistics

### GPU Metrics

- **NVIDIA**: Utilization, memory usage, temperature
- **Apple Silicon**: Basic GPU information
- **AMD**: ROCm-based monitoring
- **Intel**: Basic GPU detection

## Socket.IO Integration

The tool connects to your Socket.IO server and emits metrics data in the following format:

```json
{
  "timestamp": 1640995200.0,
  "formatted_time": "2022-01-01 12:00:00",
  "server_id": "my-server-001",
  "system_info": { ... },
  "cpu": { ... },
  "memory": { ... },
  "disk": [ ... ],
  "network": [ ... ],
  "gpu": [ ... ],
  "cuda_processes": { ... }
}
```

## Requirements

- Python 3.8 or higher
- psutil (for system metrics)
- python-socketio (for real-time communication)
- python-dotenv (for configuration)

### Optional Dependencies

- **supervisor** (for advanced background process management)
  - Install with: `pip install system-metrics-easy[supervisor]`

## Platform Support

- **Linux**: Full support for all metrics
- **macOS**: Full support including Apple Silicon GPU detection
- **Windows**: Full support with Windows-specific optimizations

## GPU Support

- **NVIDIA**: Requires nvidia-smi (usually included with NVIDIA drivers)
- **Apple Silicon**: Native macOS support
- **AMD**: Requires ROCm tools (rocm-smi)
- **Intel**: Basic detection support

## Error Handling

The tool includes robust error handling:

- Graceful degradation when tools are unavailable
- Retry logic for transient failures
- Comprehensive logging and error messages
- Safe fallbacks for missing data

## Background Running (Super Simple!)

### Easy Background Running

```bash
# Start in background (one command!)
system-metrics-easy

# Check if running
system-metrics-easy --status

# Stop it
system-metrics-easy --stop

# View logs
tail -f system-metrics-easy.log
```

### Advanced Options (Optional)

If you need more control, you can also use:

```bash
# Using nohup
nohup system-metrics-easy > metrics.log 2>&1 &

# Using screen
screen -S metrics
system-metrics-easy
# Press Ctrl+A, D to detach

# Using tmux
tmux new-session -s metrics
system-metrics-easy
# Press Ctrl+B, D to detach
```

## Configuration

### Environment Variables

You can set these environment variables for automatic configuration:

```bash
export TIME_INTERVAL=10
export SOCKET_SERVER_URL=http://localhost:8000
export SERVER_ID=my-server-001
```

### Interactive Configuration

If no environment variables are set, the tool will ask you for:

1. **Time Interval**: How often to collect metrics (seconds)
2. **Server URL**: Your Socket.IO server URL
3. **Server ID**: Unique identifier for this server

## Development

### Setup Development Environment

```bash
git clone https://github.com/hamzaig/system-metrics-easy.git
cd system-metrics-easy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[supervisor]  # Include supervisor for testing
```

### Running Tests

```bash
python -m pytest tests/
```

### Building Package

```bash
python -m build
```

### Automated Deployment

This package uses **GitHub Actions** for automated deployment:

#### **Development Releases (TestPyPI)**

- **Trigger**: Push to `main` branch
- **Result**: Automatically publishes to TestPyPI
- **Install**: `pip install -i https://test.pypi.org/simple/ system-metrics-easy`

#### **Production Releases (PyPI)**

- **Trigger**: Create and push a version tag (e.g., `v1.0.0`)
- **Result**: Automatically publishes to PyPI
- **Install**: `pip install system-metrics-easy`

#### **Creating a New Release**

**Option 1: Using the release script (Recommended)**

```bash
# Make the script executable (first time only)
chmod +x scripts/release.py

# Create a new release (automatically updates versions and creates tag)
python scripts/release.py 1.0.0
```

**Option 2: Manual process**

```bash
# Update version in pyproject.toml and setup.py
# Commit changes
git add .
git commit -m "chore: bump version to 1.0.0"

# Create and push tag
git tag v1.0.0
git push origin main --tags
```

The GitHub Actions workflow will automatically:

1. Build the package
2. Run quality checks
3. Publish to the appropriate PyPI instance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/hamzaig/system-metrics-easy/issues)
- **Documentation**: [GitHub Wiki](https://github.com/hamzaig/system-metrics-easy/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/hamzaig/system-metrics-easy/discussions)

## Changelog

### Version 1.1.2

- **ADDED**: websocket-client dependency for better WebSocket transport support
- **IMPROVED**: More efficient real-time communication with WebSocket instead of polling
- **IMPROVED**: Reduced connection overhead and better performance

### Version 1.1.1

- **FIXED**: Unicode encoding error on Windows systems (replaced emoji characters with text indicators)
- **IMPROVED**: Better cross-platform compatibility for Windows console
- **IMPROVED**: Cleaner, more professional output without emoji dependencies

### Version 1.1.0

- **NEW**: Direct execution mode - run `python index.py` without input prompts
- **NEW**: Smart reconnection with limited attempts (10 max reconnection attempts)
- **NEW**: Consecutive failure tracking - exits after 10 consecutive failures
- **NEW**: Environment variable support for direct execution
- **IMPROVED**: Better error handling and graceful exit on connection failures
- **IMPROVED**: Enhanced reliability with automatic failure detection
- **FIXED**: Script no longer runs indefinitely on connection failures

### Version 1.0.0

- Initial release
- Support for CPU, memory, disk, network, and GPU metrics
- Socket.IO integration
- Multi-platform support
- Command-line interface
- Interactive configuration
- Built-in background process management

## About

System Metrics Easy is a simple yet powerful tool for monitoring server performance. It's designed to be easy to use while providing comprehensive system metrics collection and real-time data transmission to your monitoring infrastructure.

### Resources

- **Repository**: [https://github.com/hamzaig/system-metrics-easy](https://github.com/hamzaig/system-metrics-easy)
- **Documentation**: [GitHub Wiki](https://github.com/hamzaig/system-metrics-easy/wiki)
- **Issues**: [GitHub Issues](https://github.com/hamzaig/system-metrics-easy/issues)

### License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [Moonsys](https://github.com/hamzaig)**
