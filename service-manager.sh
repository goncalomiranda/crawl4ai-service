#!/bin/bash
# Service management script for Crawl4AI API

APP_DIR="$(dirname "$(readlink -f "$0")")"
TEMPLATE_FILE="$APP_DIR/crawler-api.service.template"
VENV_DIR="${CRAWL4AI_VENV:-$HOME/crawl4ai-env}"
SERVICE_USER="${CRAWL4AI_USER:-$(id -un)}"
SYSTEMD_PATH="/etc/systemd/system/crawler-api.service"
ENV_FILE="/etc/crawl4ai/crawler-api.env"

require_environment_file() {
    if [[ ! -r "$ENV_FILE" ]]; then
        echo "Missing or unreadable $ENV_FILE; configure the database environment before starting the service." >&2
        return 1
    fi
}

case "$1" in
    install)
        echo "Installing crawler-api service..."
        if [[ ! -x "$VENV_DIR/bin/uvicorn" ]]; then
            echo "uvicorn not found in $VENV_DIR. Set CRAWL4AI_VENV to the virtual environment." >&2
            exit 1
        fi
        rendered="$(mktemp)"
        trap 'rm -f "$rendered"' EXIT
        sed -e "s|__USER__|$SERVICE_USER|g" \
            -e "s|__APP_DIR__|$APP_DIR|g" \
            -e "s|__VENV_DIR__|$VENV_DIR|g" \
            "$TEMPLATE_FILE" > "$rendered"
        sudo cp "$rendered" "$SYSTEMD_PATH"
        sudo systemctl daemon-reload
        sudo systemctl enable crawler-api
        echo "✓ Service installed and enabled"
        echo "Start it with: sudo systemctl start crawler-api"
        ;;
    start)
        require_environment_file || exit 1
        sudo systemctl start crawler-api
        echo "✓ Service started"
        ;;
    stop)
        sudo systemctl stop crawler-api
        echo "✓ Service stopped"
        ;;
    restart)
        require_environment_file || exit 1
        sudo systemctl restart crawler-api
        echo "✓ Service restarted"
        ;;
    status)
        sudo systemctl status crawler-api
        ;;
    logs)
        sudo journalctl -u crawler-api -f
        ;;
    logs-api)
        tail -f "$APP_DIR/logs/crawler_api.log"
        ;;
    logs-newsletter)
        tail -f "$APP_DIR/logs/newsletter_crawl.log"
        ;;
    logs-all)
        tail -f "$APP_DIR"/logs/*.log
        ;;
    dev)
        echo "Starting development server with auto-reload..."
        echo "Press Ctrl+C to stop"
        exec "$APP_DIR/run-dev.sh"
        ;;
    uninstall)
        echo "Uninstalling crawler-api service..."
        sudo systemctl stop crawler-api
        sudo systemctl disable crawler-api
        sudo rm "$SYSTEMD_PATH"
        sudo systemctl daemon-reload
        echo "✓ Service uninstalled"
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|logs-api|logs-newsletter|logs-all|dev|uninstall}"
        echo ""
        echo "Log commands:"
        echo "  logs           - View systemd service logs (journalctl)"
        echo "  logs-api       - View crawler_api.py logs"
        echo "  logs-newsletter - View newsletter_crawl.py logs"
        echo "  logs-all       - View all application logs"
        exit 1
        ;;
esac
