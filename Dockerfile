FROM python:3.9-slim

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies and project in development mode
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV FLASK_APP=flaskr
ENV FLASK_ENV=development
ENV FLASK_RUN_PORT=3000
ENV ADMIN_EMAIL=admin@example.com
ENV ADMIN_USERNAME=admin

# Create instance folder
RUN mkdir -p instance

# Expose configurable port
EXPOSE 3000

# Create an entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Command to run the development server
CMD ["flask", "run", "--host=0.0.0.0"]
