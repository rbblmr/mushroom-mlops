Docker
1. EXPOSE: just for documentation
2. Use the container name as http://container-name/port --> Can only be used and referred to within docker compose
    - You need to use localhost to access it in your browser
3. PROBLEM:failed to solve: rpc error: code = Unknown desc = failed to solve with frontend dockerfile.v0: failed to read dockerfile: open /var/lib/docker/tmp/buildkit-mount3869447793/Dockerfile: no such file or directory
    SOLUTION: docker compose pull, docker compose build problematic containers
4. PROBLEM: COPY is not working
SOLUTION: Move copy before RUN or include it in volumes
5. REALIZATION: if the container is built on the same dockerfile, it's image must refer to the same as every ccontainer built on that dockerfile
6. PROBLEM: docker container out of memory
    SOLUTION: https://docs.docker.com/reference/compose-file/deploy/

7. PROBLEM: interact with bash within docker
    SOLUTION: docker exec -it name bash
8. Overwrite image: docker-compose up --build 
9. PROBLEM: Web app can't access mlflow server
    SOLUTION: They must be in the same network, if you already assigned network to web app, it must include the network for mlflow
    - example. networks: back-tier, front-tier --> this restricts access outside of this network, add the mlflow-net (create one)
10. PROBLEM: Web app can't access AWS
    SOLUTION: Keys must be configure manually?? Why did it work for mlflow server. Might have to fix the authentication on pipenv level

11. PROBLEM: Request doesnt accept a properly formatted dict
    SOLUTION: .post(url, json=data), dont convert it to json or specify header and
Airflow
1. Use amazon package
2. Run it managed in cloud
3. Treat each task as a transaction in a db:
    Do not use INSERT during a task re-run, an INSERT statement might lead to duplicate rows in your database. Replace it with UPSERT.

MLFLOW
1. Hyperopt DuplicateLabels for learning_rate:
    - for the space, create unique names for hp.choice('learning_rate')
2. PROBLEM: TypeError: log_params() got an unexpected keyword argument 'learning_rate'")
    SOLUTION: mlflow.log_params(params) not **params
3. PROBLEM: prefect deployment run does not accept --params formatting:
    SOLUTION: docker exec -it prefect-server prefect deployment run mushroom-flow/train_mushroom --params '{"EXPERIMENT_NAME":"'"$EXPERIMENT_NAME"'","MLFLOW_TRACKING_URI":"'"$MLFLOW_TRACKING_URI"'"}'
4. PROBLEM: mflow server is not showing in localhost


PREFECT
prefect deployment build path/to/flow.py:flow_name --name deployment_name --tag dev -sb s3/dev
prefect deployment build path/to/flow.py:flow_name --name deployment_name --tag dev -sb s3/dev
1. PROBLEM: Credentials problem when attaching an S3 Block
    SOLUTION: You dont need this s3 block for mlflow server, remove -sb during deploymeny
2. PROBLEM: I can't see the ui
    SOLUTION: PREFECT_API_SERVICES_FLOW_RUN_NOTIFICATIONS_ENABLED: false to remove the error on databse locked
    stop the container and docker compose up -d again
3. PROBLEM: prefect.exceptions.ScriptError: Script at 'train.py' encountered an exception: OSError('libgomp.so.1: cannot open shared object file: No such file or directory')
    SOLUTION: 
        RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
        RUN apt-get -y install curl
        RUN apt-get install libgomp1

4. PROBLEM: Prefect deployment has required Parameters
    SOLUTION: edit the yaml file and add the parameters or identify it during deployment run --params
5. PROBLEM: Can't connect to mlflow tracking uri
    SOLUTION: BRO YOU GOT THE URI WRONG (face palm): http://mlflow-server:5000 NOT http://mlflow-server/5000
6. How do you log artifacts and access them?
    PROBLEM: If you log a single artifact while autologging is activated, that single afrtifact will overwrite the autologged model artifacts
    SOLUTION: artifact_path must not just be "model" bc thats the default path, add a subdir
    PROBLEM: No definite way to access registered model's s3 path
    SOLUTION: Download all artifacts as you mlflow.pyfunc.load_model(dst_path=)
7. PROBLEM: Cant connect to AWS bucket even while setting AWS env vars
    SOLUTION: Make sure youre connected to internet
8. PROBLEM: bson.errors.InvalidDocument: cannot encode object: array([0]), of type: <class 'numpy.ndarray'>
    SOLUTION: Convert y_pred to int 
9. PROBLEM: Cant connect to evidently
    SOLUTION: Make sure its within the network!!
10. PROBLEM: Web app encounters 2014-02-16 14:29:53 [1267] [CRITICAL] WORKER TIMEOUT (pid:4994) memory exceeded
    SOLUTION: Increase --timeout on gunicorn command
11. PROBLEM: Evidently
2024-08-22 19:34:01   File "/app/app.py", line 142, in iterate
2024-08-22 19:34:01     self.monitoring[dataset_name].execute(
2024-08-22 19:34:01 KeyError: 'mushroom'
    SOLUTION: Fix the config.yaml datasets path, it will search for the mushroom folder 
12. PROBLEM: Evidently server shuts down after loading reference data
    SOLUTION: `restart: always` in docker compose
13. PROBLEM: Evidently 
2024-08-22 19:43:54   File "/usr/local/lib/python3.9/site-packages/evidently/pipeline/pipeline.py", line 46, in execute
2024-08-22 19:43:54     self.analyzers_results[analyzer] = instance.calculate(rdata, cdata, column_mapping)
2024-08-22 19:43:54   File "/usr/local/lib/python3.9/site-packages/evidently/analyzers/data_drift_analyzer.py", line 103, in calculate
2024-08-22 19:43:54     test = get_stattest(reference_data[feature_name],
2024-08-22 19:43:54   File "/usr/local/lib/python3.9/site-packages/evidently/analyzers/stattests/registry.py", line 69, in get_stattest
2024-08-22 19:43:54     return _get_default_stattest(reference_data, current_data, feature_type)
2024-08-22 19:43:54   File "/usr/local/lib/python3.9/site-packages/evidently/analyzers/stattests/registry.py", line 43, in _get_default_stattest
2024-08-22 19:43:54     n_values = reference_data.append(current_data).nunique()
2024-08-22 19:43:54   File "/usr/local/lib/python3.9/site-packages/pandas/core/generic.py", line 6299, in __getattr__
2024-08-22 19:43:54     return object.__getattribute__(self, name)
2024-08-22 19:43:54 AttributeError: 'Series' object has no attribute 'append'
    SOLUTION: restart evidently to start the monitoring from scratch
14. PROBLEM: I cant see dashboard

INTEGRATION TEST
1. Must build from the image used during development
2. Dont need to specify ports, only expose for docu
3. You need to specify port for app to test it using the test_predict.py
4. You need to print eacch step
    1. Run the docker
    2. Test the docker
    3. Do IF error code is not an error, docker compose logs docker compose down exit

    Common Exit Codes
    0: Success – The command or script completed successfully.
    1: General error – An unspecified error occurred.
    2: Misuse of shell builtins – For example, syntax errors in shell commands.
    126: Command invoked cannot execute – Permission issues or the command is not executable.
    127: Command not found – The command does not exist or is not in the PATH.
    130: Script terminated by Ctrl+C – The script was interrupted by the user.
5. Save you secrets to github secrets
    - Create a script to update it
    - URL when pasted from curl works, but when typed returns 404 "https://api.github.com/repos/rbblmr/mushroom-mlops/actions/secrets/public-key"

RANDOM:
1. Type hinting imports
2. When to use *args and **kwargs
3. VSCode shortcuts
4. grep matches pattern -v means invert pattern
5. If a function requires a dict, no need to **params 
6. Pandas dataframe:
    - PROBLEM: Convert dict to df, columns are they keys
    - SOLUTION: Enclose the dict inside [] --> pd.DataFrame([data])
7. Tabulate won't print df in stdout:
    - SOLUTION: print(), for the headers, they must be in list() not just df.columns
8. Jinja2 is needed to run flask
9. Try to make logging universal --> logging.py