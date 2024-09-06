import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler, FunctionTransformer
from sklearn.compose import ColumnTransformer

# ensemble
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# hypertuning
import dill
import pickle
import mlflow
from mlflow import MlflowClient
from mlflow.entities import ViewType
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from hyperopt.pyll import scope

# eval
from sklearn.metrics import (
    f1_score, 
    log_loss, 
    roc_auc_score, 
    precision_score, 
    recall_score, 
    matthews_corrcoef
)

class Preprocessor:
    """Preprocessor for cleaning and splitting data    
    """
    def __init__(self, dataset, train=True):
        self.dataset=dataset
        self.train=train
        
        self.cat=self.dataset.select_dtypes(include='object').columns.to_list()
        self.num=self.dataset.select_dtypes(exclude='object').columns.to_list()
        if self.train == True:
            self.cat.remove('class')
            self.num.remove('id')

    def clean(self):

        self.dataset=(
            self.dataset
            .assign(**{
                cat_col: lambda x, col=cat_col: np.where(
                    ~x[col].isna() & x[col].str.match('^[a-zA-Z]$'),
                    x[col],
                    "unknown") for cat_col in self.cat})
            .assign(**{
                num_col: self.dataset[num_col].fillna(0)
                for num_col in self.num})
           )
        
        X = self.dataset.drop(columns=['class', 'id'], errors='ignore')
        if self.train==True:
            self.dataset = self.dataset.assign(**{'class': self.dataset['class'].map({'e': 0, 'p': 1})})
            y = self.dataset['class']
            
            return X, y
        return X


    def preprocess_features(self, X, preprocessing_pipeline=None):
        if not preprocessing_pipeline:
            def label_encode(X):
                encoder = LabelEncoder()
                return X.apply(encoder.fit_transform)
                
            num_pipeline=make_pipeline(
                StandardScaler()
            )
            cat_pipeline=make_pipeline(
                FunctionTransformer(func=label_encode, validate=False, feature_names_out='one-to-one'),
            )
                
            preprocessing=ColumnTransformer([
                ("num", num_pipeline, self.num),
                ("cat", cat_pipeline, self.cat),
            ])

            preprocessing_pipeline=make_pipeline(preprocessing)

        X_transformed=preprocessing_pipeline.fit_transform(X)
        feature_names=list(preprocessing_pipeline[0].get_feature_names_out())
        X=pd.DataFrame(data=X_transformed, columns=feature_names)

        return X, preprocessing_pipeline
    
    def split(self, X, y, test_size):
        
        X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                            test_size=test_size,
                                                            random_state=42,
                                                            stratify=y)

        return X_train, X_test, y_train, y_test


class Modeller:
    """Modeller to execute hypertuning and registering of model
    """
    def __init__(self, X_train, y_train, X_test, y_test, preprocessing_pipeline, experiment_name, mlflow_tracking_uri):
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.preprocessing_pipeline = preprocessing_pipeline
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.experiment_name = experiment_name


    def hypertune(self):
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        print(self.mlflow_tracking_uri)
        mlflow.set_experiment(self.experiment_name)
        all_scores={}

        def search_fn(params):
            with mlflow.start_run() as run:
                mlflow.set_tag('person','rchll') # Change name
                mlflow.autolog()
                
                classifier_type = params["type"]
                mlflow.set_tag('model', classifier_type)
                
                del params["type"]
                
                if classifier_type == "xgb":
                    mlflow.log_params(params)
                    model = XGBClassifier(**params)
                elif classifier_type == "lgbm":
                    mlflow.log_params(params)
                    model = LGBMClassifier(**params)
                elif classifier_type == "catboost":
                    mlflow.log_params(params)
                    model = CatBoostClassifier(**params)

                model.fit(self.X_train, self.y_train)
                y_pred=model.predict(self.X_test)
                
                accuracy=model.score(self.X_test,self.y_test)
                precision=precision_score(self.y_test, y_pred)
                recall=recall_score(self.y_test,y_pred)
                f1=f1_score(self.y_test, y_pred)
                roc=roc_auc_score(self.y_test, y_pred)
                logloss=log_loss(self.y_test, y_pred)
                mcc=matthews_corrcoef(self.y_test,y_pred)
                
                metrics={
                    'accuracy':accuracy,
                    'precision':precision,
                    'recall':recall,
                    'f1':f1,
                    'roc_auc_score': roc,
                    'log_loss': logloss,
                    'mcc':mcc
                }
    
                mlflow.log_metrics(metrics)
                
                os.makedirs(run.info.run_id, exist_ok=True)
                
                # with open(f"{run.info.run_id}/preprocessing_pipeline.pkl", "wb") as f:
                #     pickle.dump(self.preprocessing_pipeline, f)

                with open(f"{run.info.run_id}/preprocessing_pipeline.pkl", "wb") as f:
                    dill.dump(self.preprocessing_pipeline, f)

                mlflow.log_artifact(f"{run.info.run_id}/preprocessing_pipeline.pkl", artifact_path="model/preprocessing_pipeline")
                # mlflow.sklearn.log_model(model, artifacts_path=f"{run.info.run_id}/models")
                return {"loss": -f1, "status": STATUS_OK}

        search_space =  hp.choice(
            "classifier_type",
            [
                {
                    'type': 'xgb',
                    'n_estimators': scope.int(hp.uniform('xgb.n_estimators', 100, 1000)),
                    'max_depth': scope.int(hp.quniform('xgb.max_depth', 10, 100, 1)),
                    'learning_rate': hp.loguniform('xgb.learning_rate', -7, -2),
                    'min_child_weight': hp.loguniform('xgb.min_child_weight', -1, 5),
                    'random_state': 42,
                },
                {
                    "type": "lgbm",
                    'n_estimators': scope.int(hp.uniform('lgbm.n_estimators', 100, 1000)),
                    'learning_rate': hp.loguniform('lgbm.learning_rate', -7, -2),
                    'num_leaves': hp.choice('lgbm.num_leaves', [31, 50, 70]),
                    'max_depth': scope.int(hp.quniform('lgbm.max_depth', 10, 100, 1)),
                    'min_child_samples': hp.choice('lgbm.min_child_samples', [20, 30, 40]),
                    'subsample': hp.uniform('lgbm.subsample', 0.7, 1.0),
                    'colsample_bytree': hp.uniform('lgbm.catboost.colsample_bytree', 0.7, 1.0)
                },
                {
                    "type": "catboost",
                    'iterations': hp.choice('catboost.iterations', [100, 200]),
                    'learning_rate': hp.loguniform('catboost.learning_rate', -7, -2),
                    'depth': hp.choice('catboost.depth', [6, 8, 10]),
                    'l2_leaf_reg': hp.choice('catboost.l2_leaf_reg', [1, 3, 5]),
                    'subsample': hp.uniform('catboost.subsample', 0.7, 1.0),
                    'colsample_bylevel': hp.uniform('catboost.colsample_bylevel', 0.7, 1.0)
                },
            ],
        )
        trials=Trials()
        best_result = fmin(
            fn=search_fn,
            space=search_space,
            algo=tpe.suggest,
            max_evals=2,
            trials=trials
        )

    def register_best_model(self):
        """Register the best model to MLFLOW
        
        Parameters
        ----------
            self.mflow_tracking_uri
            self.experiment_name
        """
        client = MlflowClient(tracking_uri=self.mlflow_tracking_uri)
        experiment = client.get_experiment_by_name(self.experiment_name)
        best_run = client.search_runs(
            experiment_ids=experiment.experiment_id,
            run_view_type=ViewType.ACTIVE_ONLY,
            max_results=1,
            order_by=["metrics.f1 DESC"],
        )[0]
        # register the best model
        run_id = best_run.info.run_id
        model_uri = f"runs:/{run_id}/model"
        mlflow.register_model(model_uri=model_uri, name=self.experiment_name)