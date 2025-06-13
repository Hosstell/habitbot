#!/usr/bin/env bash

# This script automates the setup of the HabitBot systemd service.
# It must be run with sudo.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
SERVICE_NAME="habitbot.service"

# --- Pre-flight Checks ---

# Check if the script is being run with sudo/root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo."
  exit 1
fi

# Check that SUDO_USER is set, so we know which user to run the service as
if [ -z "$SUDO_USER" ]; then
    echo "Error: SUDO_USER environment variable is not set. Cannot determine the user to run the service."
    exit 1
fi

SERVICE_USER=$SUDO_USER
# Get the absolute path of the project directory (where this script is located)
PROJECT_DIR=$(dirname "$(realpath "$0")")
PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
ENV_FILE="$PROJECT_DIR/.env"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

# Check if the required files and directories exist
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Error: Virtual environment '.venv' not found in $PROJECT_DIR"
    echo "Please create it and install dependencies from requirements.txt before running this script."
    exit 1
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: main.py not found at $MAIN_SCRIPT"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: .env file not found at $ENV_FILE. The bot might not work correctly."
fi

# --- Main Execution ---

echo "Creating systemd service file at $SERVICE_FILE..."

# Create the systemd service file using a here-document
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=HabitBot Telegram Bot
After=network.target

[Service]
User=$SERVICE_USER
Group=$(id -gn "$SERVICE_USER")

WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$PYTHON_EXEC $MAIN_SCRIPT

Restart=always
StandardOutput=journal
StandardError=journal
SyslogIdentifier=habitbot

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created successfully."

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling $SERVICE_NAME to start on boot..."
systemctl enable "$SERVICE_NAME"

echo "Starting $SERVICE_NAME..."
systemctl start "$SERVICE_NAME"

# --- Post-Execution ---

echo ""
echo "Setup complete!"
echo "The HabitBot service is now running."
echo ""
echo "To check the status, run: sudo systemctl status $SERVICE_NAME"
echo "To view live logs, run:   sudo journalctl -u $SERVICE_NAME -f"
