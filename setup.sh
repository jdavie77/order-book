#!/usr/bin/env bash

python3 -m venv env

case "$(uname -s)" in

   Darwin*)
     echo 'Mac OS X'
     source env/bin/activate
     ;;

   Linux*)
     echo 'Linux'
     source env/bin/activate
     ;;

   CYGWIN*|MINGW32*|MSYS*|MINGW*)
     echo 'MS Windows'
     env/Scripts/activate
     ;;

   *)
     echo 'Other OS detected.'
     ;;
esac

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt