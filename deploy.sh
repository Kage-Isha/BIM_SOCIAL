#!/bin/bash

# BIM Social Production Deployment Script
# This script automates the deployment process for production environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="bim_social"
DEPLOY_USER="deploy"
BACKUP_DIR="/var/backups/bim_social"
LOG_FILE="/var/log/deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}✗${NC} $1" | tee -a $LOG_FILE
    exit 1
}

# Check if running as correct user
check_user() {
    if [ "$USER" != "$DEPLOY_USER" ]; then
        error "This script must be run as $DEPLOY_USER user"
    fi
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    mkdir -p $BACKUP_PATH
    
    # Backup database
    if command -v pg_dump &> /dev/null; then
        log "Backing up PostgreSQL database..."
        pg_dump $DATABASE_URL > "$BACKUP_PATH/database.sql"
        success "Database backup created"
    fi
    
    # Backup media files
    if [ -d "media" ]; then
        log "Backing up media files..."
        cp -r media "$BACKUP_PATH/"
        success "Media files backup created"
    fi
    
    # Backup current code
    log "Backing up current code..."
    tar -czf "$BACKUP_PATH/code.tar.gz" --exclude='*.pyc' --exclude='__pycache__' .
    success "Code backup created at $BACKUP_PATH"
}

# Update code
update_code() {
    log "Updating code from repository..."
    
    if [ -d ".git" ]; then
        git fetch origin
        git reset --hard origin/main
        success "Code updated from Git"
    else
        warning "Not a Git repository, skipping code update"
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    pip install -r requirements.txt
    success "Dependencies installed"
}

# Run migrations
run_migrations() {
    log "Running database migrations..."
    
    python manage.py migrate --noinput
    success "Migrations completed"
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    
    python manage.py collectstatic --noinput --clear
    success "Static files collected"
}

# Restart services
restart_services() {
    log "Restarting services..."
    
    # Restart Gunicorn
    if systemctl is-active --quiet gunicorn-bim-social; then
        sudo systemctl restart gunicorn-bim-social
        success "Gunicorn restarted"
    fi
    
    # Restart Daphne
    if systemctl is-active --quiet daphne-bim-social; then
        sudo systemctl restart daphne-bim-social
        success "Daphne restarted"
    fi
    
    # Restart Nginx
    if systemctl is-active --quiet nginx; then
        sudo systemctl reload nginx
        success "Nginx reloaded"
    fi
    
    # Restart Redis (if managed by systemd)
    if systemctl is-active --quiet redis; then
        sudo systemctl restart redis
        success "Redis restarted"
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for services to start
    sleep 10
    
    # Check web server
    if curl -f -s http://localhost:8000/health/ > /dev/null; then
        success "Web server is healthy"
    else
        error "Web server health check failed"
    fi
    
    # Check WebSocket server
    if nc -z localhost 8001; then
        success "WebSocket server is running"
    else
        warning "WebSocket server check failed"
    fi
    
    # Check database connection
    if python manage.py check --database default; then
        success "Database connection is healthy"
    else
        error "Database connection check failed"
    fi
    
    # Check Redis connection
    if redis-cli ping | grep -q PONG; then
        success "Redis connection is healthy"
    else
        warning "Redis connection check failed"
    fi
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 10 backups
    find $BACKUP_DIR -name "backup_*" -type d | sort -r | tail -n +11 | xargs rm -rf
    success "Old backups cleaned up"
}

# Send deployment notification
send_notification() {
    log "Sending deployment notification..."
    
    # This can be extended to send Slack, email, or other notifications
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 BIM Social deployed successfully at $(date)\"}" \
            $SLACK_WEBHOOK_URL
        success "Slack notification sent"
    fi
}

# Main deployment function
deploy() {
    log "Starting BIM Social deployment..."
    
    # Pre-deployment checks
    check_user
    
    # Create backup
    create_backup
    
    # Update code
    update_code
    
    # Install dependencies
    install_dependencies
    
    # Run migrations
    run_migrations
    
    # Collect static files
    collect_static
    
    # Restart services
    restart_services
    
    # Health check
    health_check
    
    # Cleanup
    cleanup_backups
    
    # Send notification
    send_notification
    
    success "Deployment completed successfully!"
}

# Rollback function
rollback() {
    log "Starting rollback process..."
    
    # Find latest backup
    LATEST_BACKUP=$(find $BACKUP_DIR -name "backup_*" -type d | sort -r | head -n 1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        error "No backup found for rollback"
    fi
    
    log "Rolling back to $LATEST_BACKUP"
    
    # Restore database
    if [ -f "$LATEST_BACKUP/database.sql" ]; then
        log "Restoring database..."
        psql $DATABASE_URL < "$LATEST_BACKUP/database.sql"
        success "Database restored"
    fi
    
    # Restore media files
    if [ -d "$LATEST_BACKUP/media" ]; then
        log "Restoring media files..."
        rm -rf media
        cp -r "$LATEST_BACKUP/media" .
        success "Media files restored"
    fi
    
    # Restore code
    if [ -f "$LATEST_BACKUP/code.tar.gz" ]; then
        log "Restoring code..."
        tar -xzf "$LATEST_BACKUP/code.tar.gz"
        success "Code restored"
    fi
    
    # Restart services
    restart_services
    
    # Health check
    health_check
    
    success "Rollback completed successfully!"
}

# Script usage
usage() {
    echo "Usage: $0 {deploy|rollback|health-check}"
    echo ""
    echo "Commands:"
    echo "  deploy      - Deploy the application"
    echo "  rollback    - Rollback to previous version"
    echo "  health-check - Check application health"
    exit 1
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    health-check)
        health_check
        ;;
    *)
        usage
        ;;
esac
