#!/usr/bin/env bash
echo "Starting socat to forward port 25 to MailPit..."
socat TCP-LISTEN:25,fork TCP:mailpit:1025 &

echo "Starting socat to forward port 5432 to PostgreSQL..."
socat TCP-LISTEN:5432,fork TCP:postgres:5432 &

echo "Installing the latest version of odoo-toolkit..."
uv tool install --force git+https://github.com/dylankiss/odoo-toolkit.git

echo "Setting up shell completion..."
otk --install-completion

echo "Starting ssh-agent..."
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

echo "Container startup complete. Keeping the process alive..."
tail -f /dev/null
