# flaskserver.py is the application python file
# The flaskserver.py must be located in same folder with this file
# This 'wsgi.py' will be used by both Gunicon WSGI server and uWSGI server

from flaskserver import app

if __name__ == "__main__":
    app.run()

