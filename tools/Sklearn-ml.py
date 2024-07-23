import os
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.decomposition import PCA
from langchain_core.tools import tool
import pandas as pd
from typing import Annotated
from dotenv import load_dotenv
from logger import setup_logger

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = setup_logger()

# Get storage path from environment variable
storage_path = os.getenv('STORAGE_PATH', './data_storage/')

@tool
def train_linear_regression(
    input_csv: Annotated[str, "Path to the input CSV file"],
    target_column: Annotated[str, "Name of the target column"]
):
    """
    Train a linear regression model.

    This function reads data from a CSV file, trains a linear regression model,
    and returns the model coefficients, intercept, and feature names.

    Args:
    input_csv (str): Path to the input CSV file.
    target_column (str): Name of the target column.

    Returns:
    dict: A dictionary containing the modified data (model parameters) and the input file path.
    """
    try:
        logger.info(f"Training linear regression model with data from {input_csv}")
        data = pd.read_csv(input_csv)
        X = data.drop(columns=[target_column])
        y = data[target_column]
        model = LinearRegression()
        model.fit(X, y)
        
        output = {
            'coefficients': model.coef_.tolist(),
            'intercept': model.intercept_,
            'feature_names': X.columns.tolist()
        }
        
        logger.info("Linear regression model trained successfully")
        return {"modified_data": pd.DataFrame([output]).to_json(), "new_file_path": input_csv}
    except Exception as e:
        logger.error(f"Error training linear regression model: {str(e)}")
        return {"error": str(e)}

@tool
def train_decision_tree(
    input_csv: Annotated[str, "Path to the input CSV file"],
    target_column: Annotated[str, "Name of the target column"]
):
    """
    Train a decision tree classifier.

    This function reads data from a CSV file and trains a decision tree classifier.

    Args:
    input_csv (str): Path to the input CSV file.
    target_column (str): Name of the target column.

    Returns:
    dict: A dictionary indicating the model was trained and the input file path.
    """
    try:
        logger.info(f"Training decision tree classifier with data from {input_csv}")
        data = pd.read_csv(input_csv)
        X = data.drop(columns=[target_column])
        y = data[target_column]
        model = DecisionTreeClassifier()
        model.fit(X, y)
        
        logger.info("Decision tree classifier trained successfully")
        return {"modified_data": "Decision Tree trained", "new_file_path": input_csv}
    except Exception as e:
        logger.error(f"Error training decision tree classifier: {str(e)}")
        return {"error": str(e)}

@tool
def train_random_forest(
    input_csv: Annotated[str, "Path to the input CSV file"],
    target_column: Annotated[str, "Name of the target column"]
):
    """
    Train a random forest classifier.

    This function reads data from a CSV file and trains a random forest classifier.

    Args:
    input_csv (str): Path to the input CSV file.
    target_column (str): Name of the target column.

    Returns:
    dict: A dictionary indicating the model was trained and the input file path.
    """
    try:
        logger.info(f"Training random forest classifier with data from {input_csv}")
        data = pd.read_csv(input_csv)
        X = data.drop(columns=[target_column])
        y = data[target_column]
        model = RandomForestClassifier()
        model.fit(X, y)
        
        logger.info("Random forest classifier trained successfully")
        return {"modified_data": "Random Forest trained", "new_file_path": input_csv}
    except Exception as e:
        logger.error(f"Error training random forest classifier: {str(e)}")
        return {"error": str(e)}

@tool
def train_svc(
    input_csv: Annotated[str, "Path to the input CSV file"],
    target_column: Annotated[str, "Name of the target column"]
):
    """
    Train a support vector classifier.

    This function reads data from a CSV file and trains a support vector classifier.

    Args:
    input_csv (str): Path to the input CSV file.
    target_column (str): Name of the target column.

    Returns:
    dict: A dictionary indicating the model was trained and the input file path.
    """
    try:
        logger.info(f"Training support vector classifier with data from {input_csv}")
        data = pd.read_csv(input_csv)
        X = data.drop(columns=[target_column])
        y = data[target_column]
        model = SVC()
        model.fit(X, y)
        
        logger.info("Support vector classifier trained successfully")
        return {"modified_data": "SVC trained", "new_file_path": input_csv}
    except Exception as e:
        logger.error(f"Error training support vector classifier: {str(e)}")
        return {"error": str(e)}

@tool
def train_knn(
    input_csv: Annotated[str, "Path to the input CSV file"],
    target_column: Annotated[str, "Name of the target column"]
):
    """
    Train a k-nearest neighbors classifier.

    This function reads data from a CSV file and trains a k-nearest neighbors classifier.

    Args:
    input_csv (str): Path to the input CSV file.
    target_column (str): Name of the target column.

    Returns:
    dict: A dictionary indicating the model was trained and the input file path.
    """
    try:
        logger.info(f"Training k-nearest neighbors classifier with data from {input_csv}")
        data = pd.read_csv(input_csv)
        X = data.drop(columns=[target_column])
        y = data[target_column]
        model = KNeighborsClassifier()
        model.fit(X, y)
        
        logger.info("K-nearest neighbors classifier trained successfully")
        return {"modified_data": "KNN trained", "new_file_path": input_csv}
    except Exception as e:
        logger.error(f"Error training k-nearest neighbors classifier: {str(e)}")
        return {"error": str(e)}

@tool
def apply_pca(
    input_csv: Annotated[str, "Path to the input CSV file"],
    n_components: Annotated[int, "Number of components for PCA"]
):
    """
    Apply PCA to reduce dimensionality.

    This function reads data from a CSV file, applies PCA, and saves the transformed data.

    Args:
    input_csv (str): Path to the input CSV file.
    n_components (int): Number of components for PCA.

    Returns:
    dict: A dictionary containing the first few rows of PCA-transformed data and the path to the new CSV file.
    """
    try:
        logger.info(f"Applying PCA to data from {input_csv} with {n_components} components")
        data = pd.read_csv(input_csv)
        pca = PCA(n_components=n_components)
        data_pca = pca.fit_transform(data)
        
        output_csv = os.path.join(storage_path, 'pca_data.csv')
        pd.DataFrame(data_pca).to_csv(output_csv, index=False)
        
        logger.info(f"PCA applied successfully. Output saved to {output_csv}")
        return {"modified_data": pd.DataFrame(data_pca).head().to_json(), "new_file_path": output_csv}
    except Exception as e:
        logger.error(f"Error applying PCA: {str(e)}")
        return {"error": str(e)}

logger.info("Machine learning tools initialized")