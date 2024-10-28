# update_model.py
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.exceptions import RestException

def update_best_model():
    client = MlflowClient()
    model_name = "Best_SVD_Model"

    # Ensure the model exists in the registry
    try:
        client.get_registered_model(model_name)
    except RestException:
        print(f"Model '{model_name}' not found. Run `initial_register.py` first.")
        return

    # Fetch all runs associated with the model and get the one with the lowest RMSE
    runs = mlflow.search_runs(filter_string=f"tags.model_name='{model_name}'", order_by=["metrics.rmse ASC"])
    if runs.empty:
        print("No runs found for the specified model.")
        return
    
    best_run = runs.iloc[0]
    best_rmse = best_run["metrics.rmse"]
    best_run_id = best_run["run_id"]

    try:
        # Get the latest production version for comparison
        latest_version_info = client.search_model_versions(f"name='{model_name}'")
        production_versions = [v for v in latest_version_info if v.current_stage == "Production"]

        if production_versions:
            current_model_rmse = float(production_versions[0].description.split("RMSE: ")[-1])

            # Register the new model if it has a better RMSE
            if best_rmse < current_model_rmse:
                new_model_version = client.create_model_version(
                    name=model_name,
                    source=f"runs:/{best_run_id}/model",
                    run_id=best_run_id,
                    description=f"RMSE: {best_rmse}"
                )
                client.transition_model_version_stage(
                    name=model_name,
                    version=new_model_version.version,
                    stage="Production",
                    archive_existing_versions=True
                )
                print(f"Updated to new best model with RMSE: {best_rmse}")
            else:
                print("Alert: The new model did not improve RMSE. No update.")
        else:
            # If no production version exists, just create the new version
            new_model_version = client.create_model_version(
                name=model_name,
                source=f"runs:/{best_run_id}/model",
                run_id=best_run_id,
                description=f"RMSE: {best_rmse}"
            )
            client.transition_model_version_stage(
                name=model_name,
                version=new_model_version.version,
                stage="Production"
            )
            print(f"No production version found. Registered the first model version with RMSE: {best_rmse}")

    except RestException as e:
        print("An error occurred while accessing the model registry:", e)

if __name__ == "__main__":
    update_best_model()
