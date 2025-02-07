Master of Jokes (MoJ) - Version 2.0
==================================

A Flask web application for sharing and rating jokes with moderation capabilities.

Setup Instructions
----------------

1. Create and activate a Python virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

2. Install the application:
   pip install -e .

3. Initialize the database:
   flask --app flaskr init-db

4. Create a moderator account:
   flask --app flaskr init-moderator admin@example.com yourpassword

5. Run the application:
   flask --app flaskr run

User Features
------------
- Register/Login
- Create jokes
- Take jokes from others
- Rate jokes you've taken
- View your joke balance

Moderator Features
-----------------
- Access moderator dashboard
- Manage all jokes (edit/delete)
- Edit user balances
- Add/remove moderators
- Control logging levels

Logging
-------
- Log file location: instance/logs/master_of_jokes.log
- Console logging: WARN level and above
- File logging: INFO level by default
- Moderators can change logging level via UI

Testing
-------
Run the test suite:
python -m pytest

Project Structure
---------------
flaskr/
  ├── __init__.py          # Application factory
  ├── auth.py              # Authentication views
  ├── db.py               # Database functions
  ├── jokes.py            # Joke management
  ├── moderator.py        # Moderator features
  ├── logging_routes.py   # Logging controls
  ├── schema.sql         # Database schema
  ├── static/            # CSS and other static files
  └── templates/         # HTML templates

Requirements
-----------
- Python 3.7+
- Flask
- Click
- Werkzeug

License
-------
This project is licensed under the MIT License. 

Docker Setup
-----------
1. Build the Docker image:
   docker build -t master-of-jokes .

2. Run the container:
   # With default admin credentials:
   docker run -p 3000:3000 -it master-of-jokes

   # With custom admin credentials:
   docker run -p 3000:3000 \
     -e ADMIN_EMAIL=your.email@example.com \
     -e ADMIN_USERNAME=your_username \
     -it master-of-jokes

3. Access the application:
   The application will be available at http://localhost:3000

Notes:
- The database will be initialized automatically on container start
- A moderator account will be created using the provided credentials
- Data is stored in the container's instance folder and will be lost when the container is removed
- For persistence, you can mount a volume:
  docker run -p 3000:3000 -v $(pwd)/instance:/app/instance master-of-jokes
  
