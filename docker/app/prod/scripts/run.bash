#!/bin/bash

export PATH="/venv/bin:${PATH}"

CMD="$1"

if [ -z $CMD ]; then
  echo "No command specified"
  exit 1
fi

exec_server() {
  exec uwsgi --ini /etc/uwsgi/papermerge.ini
}

exec_worker() {
  exec celery --app=papermerge worker --loglevel=INFO
}

case $CMD in
  server)
    exec_server
    ;;
  worker)
    exec_worker
    ;;
  *)
    echo "Unkown command: '$CMD'. Exiting..."
    exit 1
    ;;
esac