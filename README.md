# Server Status #

## Screenshots ##

#### Now Playing ####
![nowplaying](https://bytebucket.org/beallio/media-server-dashboard/raw/3ddb5482ea252ef402eb5d65f90514fac8cb94fa/serverstatus/docs/now_playing_screenshot.png)


#### Recently Added ####
![nowplaying](https://bytebucket.org/beallio/media-server-dashboard/raw/3ddb5482ea252ef402eb5d65f90514fac8cb94fa/serverstatus/docs/recently_added_screenshot.png)


## Introduction ##
Server status dashboard written in python 2.7, using flask on the backend, and bootstrap and jQuery for design.


## Setup ##

Installation instructions are for a Debian-based distro.  You will need to adjust accordingly to your linux-based setup.

Run the following commands (assuming the following is not installed on your system)

    sudo apt-get update && sudo apt-get -y upgrade
    sudo apt-get install python-dev libjpeg-dev zlib1g-dev libpng12-dev pip virtualenv virtualenvwrapper git

Note the image libraries are in support of Pillow

Now to setup the folder to contain the app and virtual environment

    cd mkdir /var/www/serverstatus
    mkvirtualenv venv
    
Clone the repository to your system

    sudo git clone https://bitbucket.org/beallio/media-server-dashboard.git


Install additional python requirements in virtual environment

    pip install -r requirements.txt

Setup config file
    
    vim config.py
    
Move setup file outside of root app directory (by default the app assumes the location is "/var".  
You'll need to adjust the import in serverstatus/__init__.py if you place it elsewhere).

    sudo mv config.py /var/config.py
    
Change permissions the user that will run gunicorn and the WSGI (e.g. $APPUSER/$APPGROUP)

    sudo chown $APPUSER:$APPGROUP /var/config.py

Run test server to ensure repository and python requirements installed correctly

    ./__init__.py


### Gunicorn on Apache ### 

    sudo -u $USER gunicorn wsgi:application -b $INTERNAL_IP:$PORT --workers=5

$USER = user dedicated to running application (e.g. 'www', 'status', 'flask')

$INTERNAL_IP = Internal IP address of your server (e.g. '10.0.10.1')

$PORT = internal port Gunicorn will run on


### Apache Configuration Edits for Proxying ###

    ProxyPass /$SUBPATH http://$INTERNAL_IP:$PORT

    ProxyPassReverse /$SUBPATH http://$INTERNAL_IP:$PORT

Ensure Apache module ["mod_proxy"](http://httpd.apache.org/docs/2.2/mod/mod_proxy.html) is installed 

For security it's recommended you move "config.py" from a web accessible directory 
to a protected directory, ensuring $USER has read privileges



### Acknowledgement ###
Last, but not least, kudos to this [person](http://d4rk.co/) for the inspiration.