import os

import numpy as np
import openml
import pandas as pd


def _ensure_openml_configured():
    """Ensure OpenML is configured with required environment variables.

    Raises:
        ValueError: If required environment variables are not set.
    """
    # Only configure if not already set
    if not openml.config.apikey:
        openml_api_key = os.environ.get("OPENML_API_KEY")
        if openml_api_key is None:
            raise ValueError(
                "OPENML_API_KEY not found in environment variables. "
                "This is required to use OpenML datasets. "
                "Set the environment variable or use a different data source."
            )
        openml.config.apikey = openml_api_key

    if not openml.config.cache_directory:
        openml_cache_dir = os.environ.get("OPENML_CACHE_DIR")
        if openml_cache_dir is None:
            raise ValueError(
                "OPENML_CACHE_DIR not found in environment variables. "
                "This is required to use OpenML datasets. "
                "Set the environment variable or use a different data source."
            )
        openml.config.set_root_cache_directory(openml_cache_dir)


def load_openml_dataset(
    task_id: int | None = None,
    dataset_id: int | None = None,
    fold_idx: int = 0,
    random_state: int = 0,
) -> tuple[pd.DataFrame, pd.Series, np.ndarray, np.ndarray]:
    """Load and preprocess an OpenML dataset.

    This function retrieves a dataset from OpenML, processes it, and prepares it for machine learning tasks.
    It can load a dataset either by task_id or dataset_id, with task_id taking precedence if both are provided.

    Args:
        task_id: The ID of the OpenML task. If provided, it overrides the dataset_id.
        dataset_id: The ID of the OpenML dataset to load.
        fold_idx: The index of the test split to use. Used for reproducible train/test splits.
        random_state: The random seed to use for reproducible train/test splits.

    Raises:
        ValueError: If required environment variables (OPENML_API_KEY, OPENML_CACHE_DIR) are not set.

    Returns:
        A tuple containing:
        - pd.DataFrame: The processed dataset with cleaned column names and encoded categorical variables.
        - pd.Series: The target column.
        - np.ndarray: Indices for the training set.
        - np.ndarray: Indices for the test set.
    """
    # Configure OpenML only when this function is actually called
    _ensure_openml_configured()

    # if we have the task id, override dataset_id
    if task_id is not None:
        task = openml.tasks.get_task(task_id)
        dataset_id = task.dataset_id

    dset = openml.datasets.get_dataset(
        dataset_id=dataset_id,
        download_data=True,
        download_qualities=False,
        download_features_meta_data=False,
    )
    X, y, is_col_cat, col_names = dset.get_data(
        dataset_format="dataframe",
        target=(
            task.target_name if task_id is not None else dset.default_target_attribute
        ),
    )
    # The is_col_cat flag is unreliable. We will use our own heuristic for this in tableprocessor.
    # openml dataframe load can be weird. If y is category, just turn it back
    # to str.
    if y.dtype.name == "category":
        y = y.astype(str)
    for col in X.columns:
        if X[col].dtype.name == "category":
            X[col] = X[col].astype(str)

    # re-use the split if we have a task_id.
    # if not, let the processor handle it and just return None
    if task_id is not None:
        tr_idxs, te_idxs = task.get_train_test_split_indices(fold=fold_idx)
    else:
        tr_idxs, te_idxs = None, None
    is_col_cat = np.array(is_col_cat)

    return X, y, tr_idxs, te_idxs
