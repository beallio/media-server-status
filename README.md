Server status dashboard written in python 2.7, using flask on the backend, and bootstrap and jQuery for design.


Need to install the following dependencies for Pillow (assuming Pillow's installed in a Virtual Env) if they're not already install on the system:
*libjpeg-dev
*zlib1g-dev
*libpng12-dev


To run in Gunicorn on Apache:

sudo -u $USER gunicorn wsgi:application -b $INTERNAL_IP:$PORT --workers=5

$USER = user dedicated to running application (e.g. 'www', 'status', 'flask')
$INTERNAL_IP = Internal IP address of your server (e.g. '10.0.10.1')
$PORT = internal port Gunicorn will run on

In Apache config add:

ProxyPass /$SUBPATH http://$INTERNAL_IP:$PORT
ProxyPassReverse /$SUBPATH http://$INTERNAL_IP:$PORT

Ensure Apache module "mod_proxy" is installed http://httpd.apache.org/docs/2.2/mod/mod_proxy.html

For security it's recommended you move "config.py" from a web accessible directory to a protected directory, ensuring $USER has read privledges




Last, but not least, kudos to this person for the inspiration: http://d4rk.co/