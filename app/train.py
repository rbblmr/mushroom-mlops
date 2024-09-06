# general
import os
import zipfile
import pickle
import pandas as pd
import logging
# mlflow
from train_utils import Preprocessor, Modeller
from mlflow import MlflowClient
from mlflow.entities import ViewType

# prefect
from prefect import flow, task

# kaggle
from kaggle.api.kaggle_api_extended import KaggleApi


# AWS_REGION=os.getenv('AWS_REGION')
KAGGLE_USERNAME=os.getenv('KAGGLE_USERNAME')
KAGGLE_KEY=os.getenv('KAGGLE_KEY')
EXPERIMENT_NAME=os.getenv('EXPERIMENT_NAME')
MLFLOW_TRACKING_URI=os.getenv('MLFLOW_TRACKING_URI')
print(MLFLOW_TRACKING_URI)
os.makedirs("logs", exist_ok=True)
log_file = "logs/train_logs"

logging.basicConfig(
    format="%(asctime)s|%(name)s|%(levelname)s|%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler().setLevel(logging.INFO),
        logging.FileHandler(log_file, mode='a').setLevel(logging.ERROR)
    ]
)

logger = logging.getLogger(__name__)

@task(log_prints=True)
def get_kaggle_data():
    """
    Download kaggle data
    """
    logger.info("Downloading kaggle data...")
    api = KaggleApi()
    api.authenticate()
    api.competition_download_files(
        competition="playground-series-s4e8",
        path='/app/data',
    )
    logger.debug("Unzipping kaggle data...")
    with zipfile.ZipFile('/app/data/playground-series-s4e8.zip', 'r') as zip_ref:
        zip_ref.extractall('/app/data/')
    logger.info("Successfully downloaded!")
    
@task(log_prints=True)
def preprocess(kaggle_data, test_size):
    logger.info("Preprocessing kaggle data...")
    dataset=pd.read_csv(kaggle_data)
    preprocessor = Preprocessor(dataset)
    X, y = preprocessor.clean()
    X_preprocess, preprocessing_pipeline = preprocessor.preprocess_features(X)
    X_train, X_test, y_train, y_test = preprocessor.split(X_preprocess, y, test_size)
    logger.info("Producing X and y data...")
    return X_train, X_test, y_train, y_test, preprocessing_pipeline
    
@task(log_prints=True)
def model(X_train, y_train, X_test, y_test, preprocessing_pipeline, EXPERIMENT_NAME, MLFLOW_TRACKING_URI):
    logger.info("Modelling started...")
    modeller = Modeller(X_train, y_train, X_test, y_test, preprocessing_pipeline, EXPERIMENT_NAME, MLFLOW_TRACKING_URI)
    logger.info("Hypertuning started...")
    modeller.hypertune()
    logger.info("Registering best model...")
    modeller.register_best_model()

@flow(name='mushroom-flow', log_prints=True)
def train(EXPERIMENT_NAME, MLFLOW_TRACKING_URI, test_size=0.2):
    get_kaggle_data()
    kaggle_data = "/app/data/train.csv"
    X_train, X_test, y_train, y_test, preprocessing_pipeline = preprocess(kaggle_data, test_size)
    model(X_train, y_train, X_test, y_test, preprocessing_pipeline, EXPERIMENT_NAME, MLFLOW_TRACKING_URI)

if __name__ == "__main__":
    EXPERIMENT_NAME=os.getenv('EXPERIMENT_NAME')
    MLFLOW_TRACKING_URI=os.getenv('MLFLOW_TRACKING_URI')
    train(EXPERIMENT_NAME, MLFLOW_TRACKING_URI, test_size=0.2)
    logger.info("Successfully trained model...")