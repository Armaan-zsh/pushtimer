#!/bin/bash
# Install Pushup Timer locally without system-wide installation

PROJECT_DIR="/home/spacecadet/Documents/github-all/pushtimer"
VENV_DIR="$PROJECT_DIR/venv"
DESKTOP_FILE="$HOME/.config/autostart/pushtimer.desktop"
LAUNCHER="$PROJECT_DIR/launch_pushtimer.sh"

echo "Setting up Pushup Timer..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv and install dependencies
echo "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install PySide6

# Create launcher script
echo "Creating launcher script..."
cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF
chmod +x "$LAUNCHER"

# Create autostart entry
echo "Creating autostart entry..."
mkdir -p "$HOME/.config/autostart"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Pushup Timer
Comment=Reminds you to do pushups every 35 minutes
Exec=$LAUNCHER
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
EOF

echo "Installation complete!"
echo "You can now run the app with: $LAUNCHER"
echo "It will auto-start on your next login."
