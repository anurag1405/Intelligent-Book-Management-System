from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import asyncio
import os
import sys
import pendulum
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
from Model_Training.data_ingestion import get_books
from Model_Training.SVD import train_and_log_models
from Model_Training.update_model import update_best_model

# Define default arguments
default_args = {
    'owner': 'anurag',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'weekly_model_training_and_registration',
    default_args=default_args,
    description='A DAG to run data ingestion, model training, and model registration weekly',
    schedule='0 0 * * 0',  # Runs every Sunday at midnight
    start_date=pendulum.today('UTC').add(days=-1),  # Replaces days_ago(1)
    catchup=False,
) as dag:

    def data_ingestion_task():
        # Run the asynchronous data ingestion task
        asyncio.run(get_books())

    def training_task():
        # Run the training task
        asyncio.run(train_and_log_models())

    def register_model_task():
        # Run the model registration task
        update_best_model()

    # Define the tasks
    ingest_data = PythonOperator(
        task_id='data_ingestion',
        python_callable=data_ingestion_task,
    )

    train_model = PythonOperator(
        task_id='model_training',
        python_callable=training_task,
    )

    register_model = PythonOperator(
        task_id='model_registration',
        python_callable=register_model_task,
    )

    # Set task dependencies
    ingest_data >> train_model >> register_model
