#!/bin/bash
# Install autostart desktop file for Zorin OS

APP_NAME="pushtimer"
DESKTOP_FILE="$HOME/.config/autostart/$APP_NAME.desktop"
EXEC_PATH="$HOME/.local/bin/$APP_NAME"

# Create autostart directory if it doesn't exist
mkdir -p "$HOME/.config/autostart"

# Create desktop file
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Pushup Timer
Comment=Reminds you to do pushups every 35 minutes
Exec=$EXEC_PATH
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
EOF

echo "Autostart file created at: $DESKTOP_FILE"
echo "Make sure the app is installed at: $EXEC_PATH"
