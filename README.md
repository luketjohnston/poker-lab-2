# poker-lab
source env_vars.sh
redis-server
source myProcfile
then app is hosted on http://127.0.0.1:8000/

 not sure about this line... do we even need postgres?
open postgres, run \c postgresql://localhost/poker_lab_dev
