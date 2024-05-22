#!/bin/bash
# Script to stop uWSGI by sending the SIGINT signal
UWSGI_PID=$(pgrep -f 'uwsgi')
if [ -z "$UWSGI_PID" ]; then
    echo "No uWSGI process found."
else
    echo "Stopping uWSGI process with PID $UWSGI_PID..."
    sudo kill -2 $UWSGI_PID  # Send SIGINT signal
    sleep 2
    if ps -p $UWSGI_PID > /dev/null; then
        echo "uWSGI process did not stop. Sending SIGTERM signal..."
        sudo kill -15 $UWSGI_PID  # Send SIGTERM signal
        sleep 2
        if ps -p $UWSGI_PID > /dev/null; then
            echo "uWSGI process did not stop. Sending SIGKILL signal..."
            sudo kill -9 $UWSGI_PID  # Send SIGKILL signal
        else
            echo "uWSGI process stopped."
        fi
    else
        echo "uWSGI process stopped."
    fi
fi

