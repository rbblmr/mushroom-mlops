import os
import s3fs
import json
import pickle
import mlflow
import logging
import requests
import pandas as pd
from tabulate import tabulate

from flask import (
    Flask,
    request,
    jsonify
)

from pymongo import MongoClient
from typing import Union, Dict
from train_utils import Preprocessor

log_file = 'logs/app_logs'
logging.basicConfig(
    format="%(asctime)s|%(levelname)s|%(message)s",
    datefmt="%Y-%M-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode='a'),
    ]
)

logging.getLogger().handlers[0].setLevel(logging.INFO)
logging.getLogger().handlers[0].setLevel(logging.ERROR)

logging.getLogger().handlers[1]
logger=logging.getLogger(__name__)


AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
EVIDENTLY_SERVICE_ADDRESS = os.getenv('EVIDENTLY_SERVICE')
MONGODB_ADDRESS = os.getenv("MONGODB_ADDRESS")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
EXPERIMENT_NAME = os.getenv("EXPERIMENT_NAME")

app = Flask(__name__)
db = MongoClient(MONGODB_ADDRESS).get_database("mushroom-web-service")
collection = db.get_collection("data")
fs = s3fs.S3FileSystem()

def load_model_artifacts_from_mlflow(MLFLOW_TRACKING_URI, EXPERIMENT_NAME):
    logger.info("Downloading artifacts..")
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model_name = EXPERIMENT_NAME
    model_alias = 'champion'
    os.makedirs('./model', exist_ok=True)
    model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}@{model_alias}", dst_path = "./model")
    
    with open('./model/preprocessing_pipeline/preprocessing_pipeline.pkl', 'rb') as f:
        preprocessing_pipeline=pickle.load(f)
    
    logger.info("Downloaded artifacts..")
    
    return model, preprocessing_pipeline

def handle_input(input_data):
    input_df = pd.DataFrame([input_data])
    print(tabulate(input_df, headers=list(input_df.columns), tablefmt='psql'))
    return input_df

def handle_output(output_data):
    if output_data == 1:
        return "poisonous"
    else:
        return "not poisonous"

def save_to_db(record, prediction):
    rec = record.copy()
    rec['class'] = prediction
    collection.insert_one(rec)

def send_to_evidently_service(record, prediction):
    rec = record.copy()
    rec['class'] = prediction
    requests.post(f"{EVIDENTLY_SERVICE_ADDRESS}/iterate/mushroom", json=[rec])

@app.route('/predict', methods=['POST'])
def predict():
    
    record = request.get_json()
    input_df = handle_input(record)
    
    model, preprocessing_pipeline = load_model_artifacts_from_mlflow(MLFLOW_TRACKING_URI, EXPERIMENT_NAME)
    preprocessor = Preprocessor(input_df, train=False)
    
    logger.info("Cleaning data..")
    X = preprocessor.clean()
    
    logger.info("Cleaning features..")
    X_preprocessed, preprocessing_pipeline = preprocessor.preprocess_features(X, preprocessing_pipeline=preprocessing_pipeline)
    
    logger.info("Predicting for mushroom..")
    y_pred = model.predict(X_preprocessed)
    output = handle_output(y_pred)
    result = {'MushroomClass': output}

    logger.info("Saving to mongodb and evidently..")
    save_to_db(record, int(y_pred))
    send_to_evidently_service(record, int(y_pred))
    
    logger.info(f"{result}")
    
    return jsonify(result)

if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0", port=9696)
