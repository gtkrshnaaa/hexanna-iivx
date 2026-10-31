#!/usr/bin/env bash
# ==============================================================================
# Hexanna IIVX: Universal OS Installer
# ==============================================================================
# Installs the 'hexanna' executable to the system so it can be run from any path.
# ==============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_MODE="auto"

for arg in "$@"; do
    case "$arg" in
        --user)
            TARGET_MODE="user"
            ;;
        --system)
            TARGET_MODE="system"
            ;;
        --uninstall)
            TARGET_MODE="uninstall"
            ;;
        -h|--help)
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --user       Install to user binary directory (~/.local/bin) [default for non-root]"
            echo "  --system     Install to system binary directory (/usr/local/bin) [requires root/sudo]"
            echo "  --uninstall  Remove hexanna launcher from install directory"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Run './install.sh --help' for usage."
            exit 1
            ;;
    esac
done

# Resolve destination directory
if [ "$TARGET_MODE" = "system" ]; then
    INSTALL_DIR="/usr/local/bin"
elif [ "$TARGET_MODE" = "user" ]; then
    INSTALL_DIR="${HOME}/.local/bin"
else
    if [ "$(id -u)" -eq 0 ]; then
        INSTALL_DIR="/usr/local/bin"
    else
        INSTALL_DIR="${HOME}/.local/bin"
    fi
fi

LAUNCHER_PATH="${INSTALL_DIR}/hexanna"

# Handle uninstall
if [ "$TARGET_MODE" = "uninstall" ]; then
    echo "=========================================================="
    echo "Hexanna IIVX: Uninstall"
    echo "=========================================================="
    if [ -f "$LAUNCHER_PATH" ]; then
        rm -f "$LAUNCHER_PATH"
        echo "[OK] Removed launcher at: $LAUNCHER_PATH"
    else
        echo "[INFO] No launcher found at: $LAUNCHER_PATH"
    fi
    exit 0
fi

echo "=========================================================="
echo "Hexanna IIVX: OS Installer"
echo "=========================================================="
echo "[*] Repository root: $REPO_DIR"
echo "[*] Installation target: $LAUNCHER_PATH"

# Ensure target directory exists
mkdir -p "$INSTALL_DIR"

# Build Docker image if docker is available
if command -v docker >/dev/null 2>&1; then
    echo "[*] Docker detected. Building container image 'hexanna:latest'..."
    docker build -t hexanna:latest "$REPO_DIR"
    echo "[OK] Docker image built successfully."
else
    echo "[WARN] Docker not detected on host. Native Python environment will be required at runtime."
fi

# Generate the standalone hexanna launcher script
cat << 'EOF' > "$LAUNCHER_PATH"
#!/usr/bin/env bash
set -euo pipefail

# 1. Native Python fast-path: if hexanna is in host Python path, execute directly
if command -v python3 >/dev/null 2>&1 && python3 -c "import hexanna" >/dev/null 2>&1; then
    exec python3 -m hexanna "$@"
fi

# 2. Containerized execution via Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: hexanna is not available natively and Docker is not installed on this system." >&2
    exit 1
fi

# TTY allocation
DOCKER_FLAGS=""
if [ -t 0 ] && [ -t 1 ]; then
    DOCKER_FLAGS="-it"
elif [ -t 0 ] || [ -t 1 ]; then
    DOCKER_FLAGS="-i"
fi

# Dynamic host resource calculation (50% cap per Prime Directive 7)
HOST_CPUS=$(nproc 2>/dev/null || echo 2)
LIMIT_CPUS=$(( (HOST_CPUS + 1) / 2 ))
[ "$LIMIT_CPUS" -lt 1 ] && LIMIT_CPUS=1

HOST_MEM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 4194304)
LIMIT_MEM_MB=$(( HOST_MEM_KB / 1024 / 2 ))
[ "$LIMIT_MEM_MB" -lt 512 ] && LIMIT_MEM_MB=512

# Volume mounts: mount HOME, PWD, and /tmp so relative/absolute host paths work transparently
MOUNTS=()
if [ -n "${HOME:-}" ] && [ -d "$HOME" ]; then
    MOUNTS+=(-v "$HOME:$HOME")
fi
if [ -n "${PWD:-}" ] && [ -d "$PWD" ]; then
    MOUNTS+=(-v "$PWD:$PWD")
fi
if [ -d "/tmp" ]; then
    MOUNTS+=(-v "/tmp:/tmp")
fi

exec docker run --rm $DOCKER_FLAGS \
    --user "$(id -u):$(id -g)" \
    --cpus="$LIMIT_CPUS" \
    --memory="${LIMIT_MEM_MB}m" \
    -e HOME="${HOME:-/tmp}" \
    -e LLM_API_KEY="${LLM_API_KEY:-}" \
    -e LLM_BASE_URL="${LLM_BASE_URL:-}" \
    -e HEXANNA_TEMP_DIR="${HEXANNA_TEMP_DIR:-}" \
    -e TERM="${TERM:-xterm-256color}" \
    "${MOUNTS[@]}" \
    -w "$PWD" \
    hexanna:latest \
    "$@"
EOF

chmod +x "$LAUNCHER_PATH"

echo "[OK] Launcher installed at: $LAUNCHER_PATH"

# PATH check
case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        echo "[OK] $INSTALL_DIR is in your system PATH."
        ;;
    *)
        echo "[WARN] $INSTALL_DIR is NOT currently in your PATH."
        echo "       Add it by running:"
        echo "       echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
        ;;
esac

echo ""
echo "[*] Verifying installation with: hexanna --help"
"$LAUNCHER_PATH" --help >/dev/null 2>&1
echo "[OK] Hexanna IIVX is ready to use from any path!"
echo "     Run 'hexanna' or 'hexanna repl' to launch the interactive REPL."
