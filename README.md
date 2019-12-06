# poker-lab

make a python3 virtualenv, activate it, then
pip install -r requirements.txt



source env_vars.sh
redis-server
source Procfile
then app is hosted on http://0.0.0.0:8000/


some warning messages about sql will display, seems to still work fine for me though.

To host the app publicly, you'll have to port forward 8000 on your router settings.
To actually deploy it on a wider scale we'd need a better web server than whatever flask
is doing by default (nginx or something), and host on port 80 instead of 8000, but for now this is fine.

I may have forgotten a installation step somewhere here, 
just install whatever is necessary to get those commands working.

