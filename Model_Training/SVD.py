# model_training.py
import mlflow
import mlflow.pyfunc
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import train_test_split
import itertools
from Model_Training.data_ingestion import get_books
from mlflow.types import Schema, ColSpec
from mlflow.models import ModelSignature
import pandas as pd
import os
import mlflow

# Get the base directory of the current file
base_dir = "/home/kapiushon05/airflow/dags/Book/Model_Training"

# Set the MLflow tracking URI to a specific directory
#mlflow.set_tracking_uri(f"file://{base_dir}")
  # Adjust the path as needed
mlflow.set_tracking_uri("/home/kapiushon05/airflow/dags/Book/mlruns")

experiment_name = "books"

mlflow.set_experiment(experiment_name)

class SVDWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, svd_model):
        self.svd_model = svd_model
    
    def predict(self, context, model_input):
        # Extract user_id and item_id from the input DataFrame
        user_id = int(model_input["user_id"].iloc[0])
        item_id = int(model_input["item_id"].iloc[0])
        
        # Make the prediction using SVD's predict method
        prediction = self.svd_model.predict(uid=user_id, iid=item_id)
        return prediction.est  # Return only the estimated rating

async def train_and_log_models():
    #df = await get_books()
    df = pd.read_csv(os.path.join(base_dir,"training.csv"))
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df[['id', 'book_id', 'rating']], reader)
    trainset, testset = train_test_split(data, test_size=0.2)

    # Hyperparameter grid
    param_combinations = list(itertools.product(
        [60],  # n_factors
        [80],  # n_epochs
        [0.002],  # lr_all
        [0.01]  # reg_all
    ))

    signature = ModelSignature(
        inputs=Schema([
            ColSpec("integer", "user_id"),
            ColSpec("integer", "item_id"),
        ]),
        outputs=Schema([ColSpec("float", "prediction")])
    )

    for params in param_combinations:
        n_factors, n_epochs, lr_all, reg_all = params
        with mlflow.start_run():
            svd = SVD(n_factors=n_factors, n_epochs=n_epochs, lr_all=lr_all, reg_all=reg_all)
            svd.fit(trainset)
            predictions = svd.test(testset)
            rmse = accuracy.rmse(predictions, verbose=False)
            mlflow.log_params({
                "n_factors": n_factors,
                "n_epochs": n_epochs,
                "lr_all": lr_all,
                "reg_all": reg_all
            })
            mlflow.log_metric("rmse", rmse)

            # Log the model using the SVDWrapper
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=SVDWrapper(svd),
                signature=signature
            )
            mlflow.set_tag("model_name", "Best_SVD_Model")

            print(f"Logged model with RMSE: {rmse}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(train_and_log_models())
