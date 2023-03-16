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
pip install -e ".[prefect,dev,ner]" --use-pep517
prefect block register --file=./jobs/blocks/hoodie_configuration.py
prefect block register --file=./jobs/blocks/snowflake.py
prefect block register --file=./jobs/blocks/airtable.py
prefect block register --file=./jobs/blocks/postgres.py
prefect block register --file=./jobs/blocks/organization_accounts.py
