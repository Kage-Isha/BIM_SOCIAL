# Daphne configuration for WebSocket support in production

import os

# Server settings
bind = "0.0.0.0"
port = 8001
unix_socket = None

# Application
application = "bim_social.asgi:application"

# Process settings
verbosity = 1
access_log = "/var/log/daphne/access.log"
access_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# WebSocket settings
websocket_timeout = 86400  # 24 hours
websocket_connect_timeout = 5

# SSL settings (if using HTTPS)
ssl_keyfile = os.getenv('SSL_KEYFILE')
ssl_certfile = os.getenv('SSL_CERTFILE')

# Security
proxy_headers = True
force_color = False

# Performance
server_name = "BIM Social WebSocket Server"
