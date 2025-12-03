# Friwo Eyes - Visual AOI System

An application for product quality inspection using camera and AI vision.

This is a combined repository containing both the client and server components of the Visual AOI (Automated Optical Inspection) system.

## Quick Start

### Windows

#### Option 1: Launch Everything (Recommended)

```powershell
.\start.bat
# or
.\launch_all.ps1
```

#### Option 2: Launch Components Separately

```powershell
# Start server first
.\server.bat

# Then start client (in another terminal)
.\client.bat
```

### Linux

#### Option 1: Launch Everything (Recommended)

```bash
./start.sh
# or
./launch_all.sh
```

#### Option 2: Launch Components Separately

```bash
# Start server first
./launch_server.sh

# Then start client (in another terminal)
./launch_client.sh
```

**Default URLs:**

- Client UI: <http://localhost:5100>
- Server API: <http://localhost:5000>
- Swagger UI: <http://localhost:5000/apidocs/>

See [LAUNCHER_README_CROSSPLATFORM.md](./LAUNCHER_README_CROSSPLATFORM.md) for complete cross-platform guide.

## Project Structure

```text
friwo-eyes/
├── client/          # Frontend application (Flask web UI + TIS camera)
├── server/          # Backend application (Flask API + AI processing)
├── Windows Launchers
│   ├── launch_all.ps1        # PowerShell launcher (all)
│   ├── launch_server.ps1     # PowerShell launcher (server)
│   ├── launch_client.ps1     # PowerShell launcher (client)
│   ├── start.bat             # Batch launcher (all)
│   ├── server.bat            # Batch launcher (server)
│   └── client.bat            # Batch launcher (client)
└── Linux Launchers
    ├── launch_all.sh         # Bash launcher (all)
    ├── launch_server.sh      # Bash launcher (server)
    ├── launch_client.sh      # Bash launcher (client)
    └── start.sh              # Simple launcher (all)
```

## Getting Started

### Prerequisites

**Common Requirements:**

- **Python 3.8+** with pip
- **NVIDIA GPU** (optional, for AI acceleration)
- **TIS Camera** (optional, for image capture)

**Windows-Specific:**

- **PowerShell 5.1+** (included in Windows 10/11)

**Linux-Specific:**

- **bash** shell (standard on most distributions)
- **Terminal emulator** for parallel mode (gnome-terminal, xterm, konsole, or xfce4-terminal)
- **lsof** for port checking (usually pre-installed)

### Manual Setup

#### Client Setup

See [client/README.md](./client/README.md) for client-specific instructions.

#### Server Setup

See [server/README.md](./server/README.md) for server-specific instructions.

## Original Repositories

- Client: <https://github.com/JasonNguyen1205/visual-aoi-client>
- Server: <https://github.com/JasonNguyen1205/visual-aoi-server>
