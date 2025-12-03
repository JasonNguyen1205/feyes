# 🐧 Visual AOI Linux Launchers - Complete!

## ✅ Linux Launchers Created

### 🚀 Bash Shell Scripts (5 files)

1. **`launch_server.sh`** (6.2 KB)
   - Intelligent server launcher with virtual environment management
   - Auto-installs dependencies
   - Configures GPU (CUDA PTX JIT)
   - Creates shared folder
   - Colored output and progress indicators
   - Built-in help system

2. **`launch_client.sh`** (7.8 KB)
   - Intelligent client launcher with virtual environment management
   - Port conflict detection and resolution
   - Server connectivity verification
   - Optional camera checking
   - Colored output and progress indicators
   - Built-in help system

3. **`launch_all.sh`** (8.5 KB)
   - Master orchestrator for complete system
   - Launches server and client in separate terminals
   - Waits for server readiness
   - Supports multiple terminal emulators (gnome-terminal, xterm, konsole, xfce4-terminal)
   - Sequential mode fallback
   - Built-in help system

4. **`start.sh`** (200 B)
   - Simple wrapper around launch_all.sh
   - Quick launcher for users

5. **`test_launchers.sh`** (5.8 KB)
   - Comprehensive validation script
   - Checks file existence, syntax, permissions
   - Verifies Python, terminal emulators
   - Tests project structure

---

## 🎯 Quick Usage

### Simplest Way
```bash
./start.sh
```

### With Options
```bash
# Debug mode (auto-reload)
./launch_all.sh --debug

# Custom ports
./launch_all.sh --server-port 5001 --client-port 5101

# Sequential mode (same terminal)
./launch_all.sh --sequential

# Server only
./launch_server.sh -p 5000 -d

# Client connecting to remote server
./launch_client.sh -s http://192.168.1.100:5000 -c

# Get help
./launch_all.sh --help
```

---

## 📋 Features Comparison: Windows vs Linux

### Common Features (Both Platforms)
- ✅ Virtual environment auto-creation/activation
- ✅ Dependency auto-installation
- ✅ Port conflict detection/resolution
- ✅ Server health monitoring
- ✅ GPU configuration (CUDA)
- ✅ Shared folder setup
- ✅ Colored console output
- ✅ Progress indicators
- ✅ Built-in help system
- ✅ Debug mode support
- ✅ Custom port configuration
- ✅ Sequential/parallel modes

### Platform-Specific Features

#### Windows Only
- Desktop shortcut creator (`create_shortcuts.ps1`)
- PowerShell cmdlet help (`Get-Help`)
- Batch file shortcuts (`.bat`)
- Process ID tracking via Windows APIs

#### Linux Only
- Multiple terminal emulator support (gnome-terminal, xterm, konsole, xfce4-terminal)
- Executable permission checking
- POSIX-style process management
- Standard Unix signals (SIGINT, SIGTERM)
- Shell script validation

---

## 🔧 Linux-Specific Setup

### Make Scripts Executable
```bash
# One-time setup
chmod +x *.sh

# Or individually
chmod +x launch_all.sh launch_server.sh launch_client.sh start.sh test_launchers.sh
```

### Install Dependencies (Ubuntu/Debian)
```bash
# Python and tools
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv lsof

# Terminal emulator (choose one)
sudo apt-get install gnome-terminal  # GNOME
sudo apt-get install xterm            # Classic
sudo apt-get install konsole          # KDE
sudo apt-get install xfce4-terminal   # XFCE

# Optional: For CIFS shared folder
sudo apt-get install cifs-utils
```

### Install Dependencies (Fedora/RHEL)
```bash
# Python and tools
sudo dnf install python3 python3-pip lsof

# Terminal emulator (choose one)
sudo dnf install gnome-terminal  # GNOME
sudo dnf install xterm           # Classic
sudo dnf install konsole         # KDE

# Optional: For CIFS shared folder
sudo dnf install cifs-utils
```

### Install Dependencies (Arch Linux)
```bash
# Python and tools
sudo pacman -S python python-pip lsof

# Terminal emulator (choose one)
sudo pacman -S gnome-terminal  # GNOME
sudo pacman -S xterm           # Classic
sudo pacman -S konsole         # KDE
```

---

## 🎨 Terminal Emulator Support

The launchers automatically detect and use available terminal emulators in this priority order:

1. **gnome-terminal** (GNOME desktop default)
2. **xterm** (Universal, lightweight)
3. **konsole** (KDE desktop default)
4. **xfce4-terminal** (XFCE desktop default)

If no terminal emulator is found, launchers automatically fall back to sequential mode (same terminal).

### Test Terminal Support
```bash
# Check which terminals you have
which gnome-terminal xterm konsole xfce4-terminal

# Run validation
./test_launchers.sh
```

---

## 📊 Linux Launcher Parameters

### `launch_all.sh`
```bash
./launch_all.sh [OPTIONS]

Options:
  --server-port PORT      Server port (default: 5000)
  --client-port PORT      Client port (default: 5100)
  -d, --debug             Enable debug mode
  -s, --sequential        Run in same terminal
  --help                  Show help
```

### `launch_server.sh`
```bash
./launch_server.sh [OPTIONS]

Options:
  -p, --port PORT         Port to run on (default: 5000)
  -h, --host HOST         Host to bind (default: 0.0.0.0)
  -d, --debug             Enable debug mode
  -n, --no-venv          Skip virtual environment
  --help                  Show help
```

### `launch_client.sh`
```bash
./launch_client.sh [OPTIONS]

Options:
  -p, --port PORT         Port to run on (default: 5100)
  -h, --host HOST         Host to bind (default: 0.0.0.0)
  -s, --server URL        Server URL (default: http://localhost:5000)
  -d, --debug             Enable debug mode
  -n, --no-venv          Skip virtual environment
  -c, --check-camera     Check camera availability
  --help                  Show help
```

---

## 🔍 Linux-Specific Troubleshooting

### Permission Denied
```bash
# Make scripts executable
chmod +x *.sh

# Or run with bash
bash ./launch_all.sh
```

### Port Already in Use
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>

# Or let launcher handle it automatically
./launch_server.sh  # Auto-frees port
```

### Terminal Not Found
```bash
# Install terminal emulator
sudo apt-get install gnome-terminal

# Or use sequential mode
./launch_all.sh --sequential
```

### Python3 Not Found
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip python3-venv

# Fedora/RHEL
sudo dnf install python3 python3-pip

# Verify
python3 --version
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf server/.venv client/.venv
./launch_all.sh
```

### Shared Folder Not Mounted
```bash
# Check mount
ls -la /mnt/visual-aoi-shared

# Setup CIFS mount
cd client
./setup_shared_folder.sh

# Or mount manually
sudo mount -t cifs //server/share /mnt/visual-aoi-shared -o credentials=/path/to/creds
```

---

## 💡 Linux Pro Tips

### 1. Global Access via PATH
```bash
# Add to ~/.bashrc or ~/.bash_profile
export PATH="$PATH:/path/to/visual-aoi"

# Or create symlinks
sudo ln -s /path/to/visual-aoi/start.sh /usr/local/bin/aoi-start
sudo ln -s /path/to/visual-aoi/launch_server.sh /usr/local/bin/aoi-server
sudo ln -s /path/to/visual-aoi/launch_client.sh /usr/local/bin/aoi-client

# Now use anywhere
aoi-start
```

### 2. Bash Aliases
```bash
# Add to ~/.bashrc
alias aoi='cd /path/to/visual-aoi && ./start.sh'
alias aoi-server='cd /path/to/visual-aoi && ./launch_server.sh'
alias aoi-client='cd /path/to/visual-aoi && ./launch_client.sh'
alias aoi-debug='cd /path/to/visual-aoi && ./launch_all.sh --debug'

# Reload
source ~/.bashrc

# Use anywhere
aoi
aoi-debug
```

### 3. Desktop Entry (GUI Launcher)
```bash
# Create ~/.local/share/applications/visual-aoi.desktop
cat > ~/.local/share/applications/visual-aoi.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Visual AOI System
Comment=Launch Visual AOI inspection system
Exec=/path/to/visual-aoi/start.sh
Icon=application-x-executable
Terminal=true
Categories=Development;
EOF

# Make executable
chmod +x ~/.local/share/applications/visual-aoi.desktop

# Now appears in application menu!
```

### 4. systemd Service (Auto-start)
```bash
# Create /etc/systemd/system/visual-aoi-server.service
sudo tee /etc/systemd/system/visual-aoi-server.service << 'EOF'
[Unit]
Description=Visual AOI Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/visual-aoi
ExecStart=/path/to/visual-aoi/launch_server.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable visual-aoi-server
sudo systemctl start visual-aoi-server

# Check status
sudo systemctl status visual-aoi-server
```

### 5. tmux/screen Session
```bash
# Keep running after disconnect
tmux new -s aoi
./launch_all.sh --sequential
# Ctrl+B, D to detach

# Reattach later
tmux attach -t aoi
```

### 6. Log Output to File
```bash
# Capture logs
./launch_server.sh 2>&1 | tee server.log
./launch_client.sh 2>&1 | tee client.log

# Or redirect
./launch_server.sh > server.log 2>&1 &
./launch_client.sh > client.log 2>&1 &
```

---

## 🧪 Testing on Linux

### Run Validation
```bash
# Check everything
./test_launchers.sh

# Output shows:
# ✓ File existence
# ✓ Bash syntax
# ✓ Python availability
# ✓ Project structure
# ✓ Entry points
# ✓ Requirements files
# ✓ Script permissions
# ✓ Terminal emulators
```

### Manual Testing
```bash
# Test server launch
./launch_server.sh -d

# In another terminal, test client
./launch_client.sh -d

# Test full system
./launch_all.sh --debug

# Test sequential mode
./launch_all.sh --sequential
```

---

## 📈 Performance on Linux

### Advantages
- ✅ Native POSIX process management
- ✅ Efficient terminal multiplexing
- ✅ Better GPU driver support (NVIDIA Linux drivers)
- ✅ Lower resource overhead
- ✅ systemd integration for production
- ✅ Better Python performance (native compilation)

### Optimization Tips
```bash
# Use sequential mode to save resources
./launch_all.sh --sequential

# Disable debug in production
./launch_all.sh  # (no --debug flag)

# Use nice for process priority
nice -n -10 ./launch_server.sh

# Monitor resources
htop  # Or top
watch -n 1 'nvidia-smi'  # GPU monitoring
```

---

## 🔄 Migration from Windows

If you're moving from Windows to Linux:

### Command Equivalents

| Windows | Linux |
|---------|-------|
| `.\launch_all.ps1` | `./launch_all.sh` |
| `.\launch_server.ps1 -Port 5001` | `./launch_server.sh -p 5001` |
| `.\launch_client.ps1 -ServerUrl http://...` | `./launch_client.sh -s http://...` |
| `Get-Help .\launch_all.ps1` | `./launch_all.sh --help` |
| `start.bat` | `./start.sh` |

### File Paths
- Windows: `C:\visual-aoi-shared\`
- Linux: `/mnt/visual-aoi-shared/`

### Virtual Environment
- Windows: `.venv\Scripts\Activate.ps1`
- Linux: `.venv/bin/activate`

---

## 📚 Documentation

- **Complete Cross-Platform Guide**: `LAUNCHER_README_CROSSPLATFORM.md`
- **Quick Reference**: `QUICK_REFERENCE.md`
- **Visual Guide**: `LAUNCHER_GUIDE.md`
- **Setup Summary**: `LAUNCHER_SETUP_SUMMARY.md`
- **Main README**: `README.md`

---

## ✨ Summary

**Created**: 5 Linux bash scripts
- 3 main launchers (server, client, all)
- 1 simple launcher (start.sh)
- 1 validation script (test)

**Features**:
- ✅ Parallel terminal support (4 terminal emulators)
- ✅ Sequential fallback mode
- ✅ Complete virtual environment management
- ✅ Port conflict auto-resolution
- ✅ Server health monitoring
- ✅ GPU configuration
- ✅ Colored output
- ✅ Built-in help
- ✅ Permission checking
- ✅ Comprehensive validation

**Cross-Platform**: Works alongside Windows launchers

**Ready to use**: Just run `./start.sh`! 🚀

---

## 🎉 Complete System

You now have **13 cross-platform launchers**:

### Windows (8 files)
- 4 PowerShell scripts (.ps1)
- 3 Batch files (.bat)
- 1 Validation script

### Linux (5 files)
- 4 Bash scripts (.sh)
- 1 Validation script

**Same functionality, native to each platform!** 🌟
