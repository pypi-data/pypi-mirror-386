import importlib
import warnings
from typing import List, Tuple, Any

import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.pipeline import Pipeline

from benson import ImputationConfig
from benson.gallery import GridGallery, MagicGallery, ProcessingGallery
from benson.magic import Magic
import benson.magic as METHODS


class Phil:
    """
    PHIL: a Progressive High-Dimensional Imputation Lab.

    Phil is an advanced data imputation tool that combines scikit-learn's IterativeImputer
    with topological methods to generate and analyze multiple versions of a dataset.

    This class allows users to impute missing data using various imputation techniques,
    generate representations of imputed datasets, and democratically select a representative version.

    Key Features:
    ------------
    - Automatic handling of mixed data types (numerical and categorical)
    - Multiple imputation strategies with parameter grid search
    - Topological analysis for quality assessment
    - Democratic selection of representative imputed dataset
    - Configurable preprocessing pipeline

    Parameters
    ----------
    samples : int, default=30
        Number of imputations to sample from the parameter grid.
    param_grid : str or ImputationConfig, default="default"
        Imputation parameter grid identifier or configuration. Can be:
        - "default": Uses default imputation strategies
        - ImputationConfig object: Custom imputation configuration
        - str: Predefined grid from GridGallery (e.g., "finance", "healthcare")
    magic : str, default="ECT"
        Representation learning method to use for quality assessment.
    config : dict or None, default=None
        Configuration for the chosen magic method.
    random_state : int or None, default=None
        Seed for reproducibility.

    Attributes
    ----------
    config : BaseModel
        Configuration for the chosen magic method.
    magic : Magic
        Instantiated representation learning method.
    samples : int
        Number of imputations to sample from the parameter grid.
    param_grid : ImputationConfig
        Configured imputation parameter grid.
    random_state : int or None
        Random state for reproducibility.
    representations : list
        List of generated imputed datasets.
    magic_descriptors : list
        Topological descriptors for imputed datasets.
    selected_imputers : list
        Selected imputation pipelines.
    closest_index : int
        Index of the representative imputation.

    Examples
    --------
    >>> import pandas as pd
    >>> from benson import Phil
    >>>
    >>> # Create a dataframe with missing values
    >>> df = pd.DataFrame({
    ...     'num': [1.0, None, 3.0, None],
    ...     'cat': ['a', 'b', None, 'd']
    ... })
    >>>
    >>> # Initialize Phil with default settings
    >>> phil = Phil()
    >>>
    >>> # Fit and transform the data
    >>> imputed_df = phil.fit_transform(df)

    Notes
    -----
    The imputation process follows these steps:
    1. Identifies categorical and numerical columns
    2. Configures preprocessing pipeline
    3. Creates multiple imputation strategies
    4. Applies imputation and generates representations
    5. Uses topological analysis to select representative imputation
    """

    def __init__(
        self,
        samples: int = 30,
        param_grid: str = "default",
        magic: str = "ECT",
        config=None,
        random_state=None,
    ):
        """
        Parameters
        ----------
        samples : int, optional
            Number of imputations to sample from the parameter grid. Default is 30.
        param_grid : str, optional
            Imputation parameter grid identifier or configuration. Default is "default".
        magic : str, optional
            Representation learning method to use. Default is "ECT".
        config : dict or None, optional
            Configuration for the chosen magic method. Default is None.
        random_state : int or None, optional
            Seed for reproducibility. Default is None.

        Attributes
        ----------
        config : dict
            Configuration for the chosen magic method.
        magic : str
            Topological data analysis method to use.
        samples : int
            Number of imputations to sample from the parameter grid.
        param_grid : str
            Imputation parameter grid identifier or configuration.
        random_state : int or None
            Seed for reproducibility.
        representations : list
            List to store representations generated during imputation.
        magic_descriptors : list
            List to store descriptors for the chosen magic method.
        """
        self.config, self.magic = self._configure_magic_method(
            magic=magic, config=config
        )
        self.samples = samples
        self.param_grid = self._configure_param_grid(param_grid)
        self.random_state = random_state
        self.representations = []
        self.magic_descriptors = []

    def impute(self, df: pd.DataFrame, max_iter: int = 10) -> List[np.ndarray]:
        """
        Generate multiple imputed versions of a dataset with missing values.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing missing values to be imputed.
        max_iter : int, optional
            Maximum number of iterations for the IterativeImputer, default is 10.

        Returns
        -------
        List[np.ndarray]
            A list of numpy arrays with imputed values.

        Raises
        ------
        ValueError
            If the input DataFrame has no missing values.

        Notes
        -----
        This method identifies categorical and numerical columns, configures a preprocessing
        pipeline, creates multiple imputers with different parameter settings, selects the
        most appropriate imputations, and applies them to the input DataFrame.
        """
        if df.isnull().sum().sum() == 0:
            raise ValueError("No missing values found in the input DataFrame.")
        categorical_columns, numerical_columns = self._identify_column_types(df)
        preprocessor = self._configure_preprocessor(
            "default", categorical_columns, numerical_columns
        )
        imputers = self._create_imputers(preprocessor, max_iter)
        self.selected_imputers = self._select_imputations(imputers)
        return self._apply_imputations(df, self.selected_imputers)

    @staticmethod
    def _identify_column_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Identify categorical and numerical columns in a DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame containing the data to analyze.

        Returns
        -------
        Tuple[List[str], List[str]]
            A tuple containing two lists:
            - The first list contains the names of categorical columns.
            - The second list contains the names of numerical columns.

        Examples
        --------
        >>> import pandas as pd
        >>> data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c'], 'col3': [1.1, 2.2, 3.3]}
        >>> df = pd.DataFrame(data)
        >>> Phil._identify_column_types(df)
        (['col2'], ['col1', 'col3'])
        """
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()
        numerical_columns = df.select_dtypes(
            include=["number", "bool"]
        ).columns.tolist()

        return categorical_columns, numerical_columns

    def _create_imputers(
        self, preprocessor: ColumnTransformer, max_iter: int
    ) -> List[Pipeline]:
        """
        Constructs a list of imputation pipelines with various parameter configurations.
        Parameters
        ----------
        preprocessor : ColumnTransformer
            A scikit-learn ColumnTransformer object used for data preprocessing.
        max_iter : int
            The maximum number of iterations for the IterativeImputer.
        Returns
        -------
        List[Pipeline]
            A list of scikit-learn Pipeline objects, each containing a preprocessing
            step and an imputation model configured with different parameter settings.
        Notes
        -----
        - The method dynamically imports and initializes models based on the parameter
          grid defined in `self.param_grid`.
        - Only parameters compatible with the model's constructor are passed during
          initialization.
        """
        imputers = []
        for method, module, params in zip(
            self.param_grid.methods,
            self.param_grid.modules,
            self.param_grid.grids,
        ):
            model = self._import_model(module, method)
            for param_vals in params:
                compatible_params = {
                    k: v
                    for k, v in param_vals.items()
                    if k in model.__init__.__code__.co_varnames
                }
                estimator = model(**compatible_params)
                imputers.append(self._build_pipeline(preprocessor, estimator, max_iter))
        return imputers

    @staticmethod
    def _import_model(module: str, method: str):
        """
        Dynamically imports a model from a specified module.

        Parameters
        ----------
        module : str
            The name of the module to import from.
        method : str
            The name of the class or function to import from the module.

        Returns
        -------
        object
            The imported class or function.

        Raises
        ------
        ImportError
            If the module cannot be imported.
        AttributeError
            If the method cannot be found in the module.
        """
        imported_module = importlib.import_module(module)
        return getattr(imported_module, method)

    def _build_pipeline(
        self, preprocessor: ColumnTransformer, estimator, max_iter: int
    ) -> Pipeline:
        """
        Builds an imputation pipeline with a given estimator.

        Parameters
        ----------
        preprocessor : ColumnTransformer
            Data preprocessing transformer to handle different column types.
        estimator : object
            The estimator to use in the IterativeImputer.
        max_iter : int
            Maximum number of iterations for the IterativeImputer.

        Returns
        -------
        Pipeline
            A scikit-learn Pipeline containing the preprocessor and IterativeImputer.
        """
        return Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "imputer",
                    IterativeImputer(
                        estimator=estimator,
                        random_state=self.random_state,
                        max_iter=max_iter,
                    ),
                ),
            ]
        )

    def _select_imputations(self, imputers: List[Pipeline]) -> List[Pipeline]:
        """
        Randomly selects a subset of imputers to run.

        Parameters
        ----------
        imputers : List[Pipeline]
            A list of scikit-learn Pipeline objects, each containing preprocessing
            and imputation steps.

        Returns
        -------
        List[Pipeline]
            A randomly selected subset of imputation pipelines, with size determined
            by self.samples attribute.

        Notes
        -----
        Uses the random_state attribute for reproducible sampling.
        """
        np.random.seed(self.random_state)
        selected_idxs = np.random.choice(
            range(len(imputers)),
            min(self.samples, len(imputers)),
            replace=False,
        )
        return [imputers[idx] for idx in selected_idxs]

    def _apply_imputations(
        self, df: pd.DataFrame, imputers: List[Pipeline]
    ) -> List[np.ndarray]:
        """
        Applies multiple imputation pipelines to the dataset.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing missing values to be imputed.
        imputers : List[Pipeline]
            List of scikit-learn Pipeline objects to apply to the data.

        Returns
        -------
        List[np.ndarray]
            List of numpy arrays containing imputed datasets.

        Notes
        -----
        Suppresses convergence warnings during the imputation process.
        """
        imputations = []
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            for imputer in imputers:
                imputer.fit(df)
                imputations.append(imputer.transform(df))
            return imputations

    def generate_descriptors(self) -> List[np.ndarray]:
        """
        Generates topological descriptors for imputed datasets.

        Returns
        -------
        List[np.ndarray]
            List of topological descriptors, one for each imputed dataset

        Notes
        -----
        Processes all imputed datasets in a single batch for efficiency,
        particularly useful when using GPU acceleration.
        """
        return self.magic.generate(self.representations)

    def fit(self, df: pd.DataFrame, max_iter: int = 5) -> pd.DataFrame:
        """
        Fit the imputation model to the data and return the best imputed dataset.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing missing values to be imputed.
        max_iter : int, optional
            Maximum number of iterations for the IterativeImputer, default is 5.

        Returns
        -------
        pandas.DataFrame
            The best representative imputed dataset selected using topological analysis.

        Notes
        -----
        This method performs the complete imputation workflow:
        1. Generates multiple imputed versions of the dataset
        2. Creates topological descriptors for each imputation
        3. Selects the most representative imputation
        4. Stores the corresponding pipeline for later use with transform()
        """
        self.representations = self.impute(df, max_iter)
        self.magic_descriptors = self.generate_descriptors()

        assert len(self.representations) == len(self.magic_descriptors)
        self.closest_index = self._select_representative(self.magic_descriptors)
        X = self.representations[self.closest_index]
        # get imputed column labels from Pipeline
        self.pipeline = self.selected_imputers[self.closest_index]
        imputed_columns = self._get_imputed_columns(
            transformer=self.pipeline["preprocessor"]
        )
        return pd.DataFrame(X, columns=imputed_columns)

    def transform(self, df: pd.DataFrame, max_iter: int = 5) -> pd.DataFrame:
        """
        Imputes missing values in the input DataFrame using the fitted pipeline.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing missing values to be imputed.
        max_iter : int, optional
            Maximum number of iterations for the imputer, default is 5.

        Returns
        -------
        pandas.DataFrame
            DataFrame with imputed values.

        Raises
        ------
        RuntimeError
            If the method is called before fitting the model.

        Notes
        -----
        Uses the pipeline selected during the fit method to transform new data.
        """
        if not hasattr(self, "pipeline"):
            raise RuntimeError("Pipeline not fitted. Call `fit` first.")

        imputed_columns = self._get_imputed_columns(
            transformer=self.pipeline["preprocessor"]
        )
        return pd.DataFrame(self.pipeline.transform(df), columns=imputed_columns)

    @staticmethod
    def _get_imputed_columns(transformer: ColumnTransformer) -> List[str]:
        """
        Retrieves the imputed column labels from the pipeline.

        Parameters
        ----------
        transformer : ColumnTransformer
            The column transformer from the pipeline's preprocessor.

        Returns
        -------
        List[str]
            List of column names after preprocessing transformations.
        """
        return transformer.get_feature_names_out()

    @staticmethod
    def _select_representative(descriptors: List[np.ndarray]) -> int:
        """
        Finds the descriptor closest to the mean representation.

        Parameters
        ----------
        descriptors : List[np.ndarray]
            List of topological descriptors for each imputed dataset.

        Returns
        -------
        int
            Index of the descriptor that is closest to the mean of all descriptors,
            representing the most central imputation.

        Notes
        -----
        Uses Euclidean distance to determine proximity to the mean descriptor.
        """
        avg_descriptor = np.mean(descriptors, axis=0)
        return int(
            np.argmin(
                [
                    np.linalg.norm(descriptor - avg_descriptor)
                    for descriptor in descriptors
                ]
            )
        )

    @staticmethod
    def _configure_magic_method(magic: str, config) -> Tuple[BaseModel, Magic]:
        """
        Configures the topological method for representation learning.

        Parameters
        ----------
        magic : str
            Name of the magic method to use for topological analysis.
        config : BaseModel or None
            Configuration for the chosen magic method. If None, a default
            configuration will be retrieved from MagicGallery.

        Returns
        -------
        Tuple[BaseModel, Magic]
            A tuple containing:
            - The configuration object for the magic method
            - The instantiated magic method object

        Raises
        ------
        ValueError
            If the specified magic method is not found.
        """
        magic_method = getattr(METHODS, magic, None)
        if magic_method is None:
            raise ValueError(f"Magic method '{magic}' not found.")
        if not isinstance(config, BaseModel):
            config = MagicGallery.get(magic)
        return config, magic_method(config=config)

    @staticmethod
    def _configure_param_grid(param_grid) -> ImputationConfig:
        """
        Retrieves the imputation parameter grid.

        Parameters
        ----------
        param_grid : str, ImputationConfig, BaseModel, or dict
            The parameter grid specification. Can be:
            - str: A string identifier for a predefined grid in GridGallery
            - ImputationConfig: An already configured imputation configuration
            - BaseModel: A Pydantic model containing methods, modules, and grids
            - dict: A dictionary with keys 'methods', 'modules', and 'grids'

        Returns
        -------
        ImputationConfig
            The configured imputation parameter grid.

        Raises
        ------
        ValueError
            If the parameter grid specification is invalid or missing required fields.
        """
        if isinstance(param_grid, str):
            return GridGallery.get(param_grid)
        if isinstance(param_grid, ImputationConfig):
            return param_grid
        if isinstance(param_grid, BaseModel):
            if (
                not hasattr(param_grid, "methods")
                or not hasattr(param_grid, "modules")
                or not hasattr(param_grid, "grids")
            ):
                raise ValueError("Invalid parameter grid configuration.")
            return ImputationConfig(
                methods=param_grid.methods,
                modules=param_grid.modules,
                grids=param_grid.grids,
            )
        if isinstance(param_grid, dict):
            if not all(key in param_grid for key in ["methods", "modules", "grids"]):
                raise ValueError("Invalid parameter grid configuration.")
            data = {
                k: v
                for k, v in param_grid.items()
                if k in ["methods", "modules", "grids"]
            }
            return ImputationConfig(**data)
        raise ValueError("Invalid parameter grid type.")

    @staticmethod
    def _configure_preprocessor(
        strategy: str,
        categorical_columns: List[str],
        numerical_columns: List[str],
    ) -> ColumnTransformer:
        """
        Configures the preprocessing pipeline for different column types.

        Parameters
        ----------
        strategy : str
            Identifier for the preprocessing strategy to use from ProcessingGallery.
        categorical_columns : List[str]
            List of categorical column names in the dataset.
        numerical_columns : List[str]
            List of numerical column names in the dataset.

        Returns
        -------
        ColumnTransformer
            A scikit-learn ColumnTransformer configured with appropriate transformers
            for both categorical and numerical columns.

        Raises
        ------
        RuntimeError
            If there's an error importing or initializing a model from the
            preprocessing configuration.
        """
        strategy = ProcessingGallery.get(strategy)
        transformers: List[Tuple[str, Any, List[str]]] = []

        for key, preprocessing_config in strategy.items():
            try:
                model = Phil._import_model(
                    preprocessing_config.module, preprocessing_config.method
                )
            except (ImportError, AttributeError) as e:
                raise RuntimeError(
                    f"Failed to import model {preprocessing_config.method} from module {preprocessing_config.module}: {e}"
                )

            transformer = model(**preprocessing_config.params)

            # Determine column type and only add transformer if columns are not empty
            if key == "num" and len(numerical_columns) > 0:
                transformers.append((key, transformer, numerical_columns))
            elif key == "cat" and len(categorical_columns) > 0:
                transformers.append((key, transformer, categorical_columns))

        return ColumnTransformer(transformers, verbose_feature_names_out=True)
