#!/bin/bash

# Initialize the database
flask init-db

# Initialize default moderator (using environment variables for security)
flask init-moderator "${ADMIN_USERNAME:-admin}" "${ADMIN_EMAIL:-admin@example.com}"

# Execute the CMD from Dockerfile
exec "$@" 
