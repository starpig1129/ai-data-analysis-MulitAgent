import os
from typing import Annotated
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.feature_selection import SelectKBest, f_regression
from langchain_core.tools import tool
from dotenv import load_dotenv
from logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = setup_logger()

# Get storage path from environment variable
storage_path = os.getenv('STORAGE_PATH', './data_storage/')

# Ensure the storage directory exists
if not os.path.exists(storage_path):
    os.makedirs(storage_path)
    logger.info(f"Created storage directory: {storage_path}")

@tool
def handle_missing_values(input_csv: Annotated[str, "Path to the input CSV file"]):
    """
    Handle missing values in the data.

    This function reads a CSV file, imputes missing values using the mean strategy,
    and saves the imputed data to a new CSV file.

    Args:
    input_csv (str): Path to the input CSV file.

    Returns:
    dict: A dictionary containing the modified data (first 5 rows) and the path to the new file.
    """
    try:
        logger.info(f"Handling missing values for file: {input_csv}")
        data = pd.read_csv(input_csv)
        imputer = SimpleImputer(strategy='mean')
        data_imputed = pd.DataFrame(imputer.fit_transform(data), columns=data.columns)
        
        output_csv = os.path.join(storage_path, 'imputed_data.csv')
        data_imputed.to_csv(output_csv, index=False)
        
        logger.info(f"Missing values handled. Output saved to: {output_csv}")
        return {"modified_data": data_imputed.head().to_json(), "new_file_path": output_csv}
    except Exception as e:
        logger.error(f"Error handling missing values: {str(e)}")
        return {"error": str(e)}

@tool
def standardize_data(input_csv: Annotated[str, "Path to the input CSV file"]):
    """
    Standardize the data.

    This function reads a CSV file, standardizes the data using StandardScaler,
    and saves the standardized data to a new CSV file.

    Args:
    input_csv (str): Path to the input CSV file.

    Returns:
    dict: A dictionary containing the modified data (first 5 rows) and the path to the new file.
    """
    try:
        logger.info(f"Standardizing data for file: {input_csv}")
        data = pd.read_csv(input_csv)
        scaler = StandardScaler()
        data_scaled = pd.DataFrame(scaler.fit_transform(data), columns=data.columns)
        
        output_csv = os.path.join(storage_path, 'standardized_data.csv')
        data_scaled.to_csv(output_csv, index=False)
        
        logger.info(f"Data standardized. Output saved to: {output_csv}")
        return {"modified_data": data_scaled.head().to_json(), "new_file_path": output_csv}
    except Exception as e:
        logger.error(f"Error standardizing data: {str(e)}")
        return {"error": str(e)}

@tool
def select_features(
    input_csv: Annotated[str, "Path to the input CSV file"],
    target_column: Annotated[str, "Name of the target column"],
    k: Annotated[int, "Number of top features to select"]
):
    """
    Select top k features based on their relationship with the target.

    This function reads a CSV file, selects the top k features using f_regression,
    and saves the selected features along with the target column to a new CSV file.

    Args:
    input_csv (str): Path to the input CSV file.
    target_column (str): Name of the target column.
    k (int): Number of top features to select.

    Returns:
    dict: A dictionary containing the modified data (first 5 rows) and the path to the new file.
    """
    try:
        logger.info(f"Selecting top {k} features for file: {input_csv}")
        data = pd.read_csv(input_csv)
        X = data.drop(columns=[target_column])
        y = data[target_column]
        selector = SelectKBest(score_func=f_regression, k=k)
        X_new = selector.fit_transform(X, y)
        selected_features = X.columns[selector.get_support()]
        
        selected_data = pd.DataFrame(X_new, columns=selected_features)
        selected_data[target_column] = y.values
        
        output_csv = os.path.join(storage_path, 'selected_features_data.csv')
        selected_data.to_csv(output_csv, index=False)
        
        logger.info(f"Feature selection complete. Output saved to: {output_csv}")
        return {"modified_data": selected_data.head().to_json(), "new_file_path": output_csv}
    except Exception as e:
        logger.error(f"Error selecting features: {str(e)}")
        return {"error": str(e)}

@tool
def encode_categorical_data(input_csv: Annotated[str, "Path to the input CSV file"]):
    """
    Encode categorical data using one-hot encoding.

    This function reads a CSV file, applies one-hot encoding to categorical columns,
    and saves the encoded data to a new CSV file.

    Args:
    input_csv (str): Path to the input CSV file.

    Returns:
    dict: A dictionary containing the modified data (first 5 rows) and the path to the new file.
    """
    try:
        logger.info(f"Encoding categorical data for file: {input_csv}")
        data = pd.read_csv(input_csv)
        categorical_columns = data.select_dtypes(include=['object']).columns
        encoder = OneHotEncoder(sparse=False, drop='first')
        encoded_data = pd.DataFrame(encoder.fit_transform(data[categorical_columns]), 
                                    columns=encoder.get_feature_names_out(categorical_columns))
        data = data.drop(columns=categorical_columns).reset_index(drop=True)
        encoded_data = pd.concat([data, encoded_data], axis=1)
        
        output_csv = os.path.join(storage_path, 'encoded_data.csv')
        encoded_data.to_csv(output_csv, index=False)
        
        logger.info(f"Categorical data encoded. Output saved to: {output_csv}")
        return {"modified_data": encoded_data.head().to_json(), "new_file_path": output_csv}
    except Exception as e:
        logger.error(f"Error encoding categorical data: {str(e)}")
        return {"error": str(e)}

logger.info("Data processing tools initialized")