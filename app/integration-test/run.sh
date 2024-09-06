#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# skip export

echo "Creating test docker containers"
docker compose up -d

sleep 10

echo "Testing the docker containers for the MLOps pipeline"
docker exec -it test-prefect-server python train.py

ERROR_CODE=$?

if [${ERROR_CODE} != 0]; then
    docker compose logs
    docker compose down
    exit ${ERROR_CODE}
fi

sleep 10

echo "Restarting mushroom web service"
docker restart test-mushroom-web-service

sleep 10

echo "Testing the web service"
python test_predict.py

ERROR_CODE=$?

if [${ERROR_CODE} != 0]; then
    docker compose logs
    docker compose down
    exit ${ERROR_CODE}
fi

echo "Cleaning up resources
docker compose down