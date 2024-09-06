SHELL:=/bin/bash
Build the bucket
1. terraform init, terraform plan -var="bucket_name=${AWS_BUCKET_NAME}", terraform apply -var="bucket_name=${AWS_BUCKET_NAME}"

Run the docker daemon
2. docker compose up -d
3. docker exec -it prefect-server prefect block register --file create_s3_block.py

docker exec -it prefect-server prefect block register -m prefect_aws

4. docker exec -it prefect-server prefect deployment build ./train.py:train --name train_mushroom --tag dev -sb s3-bucket/${AWS_BUCKET_NAME}
4. docker exec -it prefect-server prefect deployment apply train-deployment.yaml
docker exec -it prefect-server prefect deployment run mushroom-flow/train_mushroom --params '{"EXPERIMENT_NAME":"'"$EXPERIMENT_NAME"'","MLFLOW_TRACKING_URI":"'"$MLFLOW_TRACKING_URI"'"}'
5. docker exec -it prefect-server prefect agent start --pool "default-agent-pool"
docker exec -it prefect-server prefect worker start
5. docker exec -it prefect-server prefect deployment run mushroom-flow/train_mushroom
6. docker exec -it ml-web-server python generate_traffic.py