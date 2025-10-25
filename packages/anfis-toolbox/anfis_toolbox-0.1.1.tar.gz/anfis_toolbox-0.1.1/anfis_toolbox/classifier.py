"""High-level classification estimator facade for ANFIS.

``ANFISClassifier`` exposes a scikit-learn style API that bundles membership
function management, model construction, and trainer selection so downstream
code can focus on providing data and retrieving predictions.
"""

from __future__ import annotations

import inspect
import logging
import pickle  # nosec B403
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any, TypeAlias, cast

import numpy as np
import numpy.typing as npt

from .builders import ANFISBuilder
from .estimator_utils import (
    BaseEstimatorLike,
    ClassifierMixinLike,
    FittedMixin,
    check_is_fitted,
    ensure_2d_array,
    format_estimator_repr,
)
from .logging_config import enable_training_logs
from .losses import LossFunction
from .membership import MembershipFunction
from .metrics import ANFISMetrics, MetricValue
from .model import TSKANFISClassifier
from .optim import (
    AdamTrainer,
    BaseTrainer,
    PSOTrainer,
    RMSPropTrainer,
    SGDTrainer,
)
from .optim import (
    HybridAdamTrainer as _HybridAdamTrainer,
)
from .optim import (
    HybridTrainer as _HybridTrainer,
)
from .optim.base import TrainingHistory

InputConfigValue: TypeAlias = Mapping[str, Any] | Sequence[Any] | MembershipFunction | str | int | None
NormalizedInputSpec: TypeAlias = dict[str, Any]

TRAINER_REGISTRY: dict[str, type[BaseTrainer]] = {
    "sgd": SGDTrainer,
    "adam": AdamTrainer,
    "rmsprop": RMSPropTrainer,
    "pso": PSOTrainer,
}

_UNSUPPORTED_TRAINERS: tuple[type[BaseTrainer], ...] = (_HybridTrainer, _HybridAdamTrainer)


def _ensure_training_logging(verbose: bool) -> None:
    if not verbose:
        return
    logger = logging.getLogger("anfis_toolbox")
    if logger.handlers:
        return
    enable_training_logs()


class ANFISClassifier(BaseEstimatorLike, FittedMixin, ClassifierMixinLike):
    """Adaptive Neuro-Fuzzy classifier with a scikit-learn style API.

    The estimator manages membership-function synthesis, rule construction, and
    trainer selection so you can focus on calling :meth:`fit`,
    :meth:`predict`, :meth:`predict_proba`, and :meth:`evaluate` with familiar
    NumPy-like data structures.

    Examples:
    --------
    >>> clf = ANFISClassifier()
    >>> clf.fit(X, y)
    ANFISClassifier(...)
    >>> clf.predict([[0.1, -0.2]])
    array([...])

    Parameters
    ----------
    n_classes : int, optional
        Number of target classes. Must be >= 2 when provided. If omitted, the
        classifier infers the class count during the first call to ``fit``.
    n_mfs : int, default=3
        Default number of membership functions per input.
    mf_type : str, default="gaussian"
        Default membership function family applied when membership functions are
        inferred from data.
    init : {"grid", "fcm", "random", None}, default="grid"
        Strategy used when inferring membership functions from data. ``None``
        falls back to ``"grid"``.
    overlap : float, default=0.5
        Controls overlap when generating membership functions automatically.
    margin : float, default=0.10
        Margin added around observed data ranges during grid initialization.
    inputs_config : Mapping, optional
        Per-input overrides. Keys may be feature names (when ``X`` is a
        :class:`pandas.DataFrame`) or integer indices. Values may be:

        * ``dict`` with keys among ``{"n_mfs", "mf_type", "init", "overlap",
          "margin", "range", "membership_functions", "mfs"}``.
        * A list or tuple of membership function objects for full control.
        * ``None`` for defaults.
    random_state : int, optional
        Random state forwarded to initialization routines and stochastic
        optimizers.
    optimizer : str, BaseTrainer, type[BaseTrainer], or None, default="adam"
        Trainer identifier or instance used for fitting. Strings map to entries
        in :data:`TRAINER_REGISTRY`. ``None`` defaults to "adam".
    optimizer_params : Mapping, optional
        Additional keyword arguments forwarded to the trainer constructor.
    learning_rate, epochs, batch_size, shuffle, verbose : optional scalars
        Common trainer hyper-parameters provided for convenience. When the
        selected trainer supports the parameter it is included automatically.
    loss : str or LossFunction, optional
        Custom loss forwarded to trainers that expose a ``loss`` parameter.
    rules : Sequence[Sequence[int]] | None, optional
        Explicit fuzzy rule indices to use instead of the full Cartesian product. Each
        rule lists the membership-function index per input. ``None`` keeps the default
        exhaustive rule set.
    """

    def __init__(
        self,
        *,
        n_classes: int | None = None,
        n_mfs: int = 3,
        mf_type: str = "gaussian",
        init: str | None = "grid",
        overlap: float = 0.5,
        margin: float = 0.10,
        inputs_config: Mapping[Any, Any] | None = None,
        random_state: int | None = None,
        optimizer: str | BaseTrainer | type[BaseTrainer] | None = "adam",
        optimizer_params: Mapping[str, Any] | None = None,
        learning_rate: float | None = None,
        epochs: int | None = None,
        batch_size: int | None = None,
        shuffle: bool | None = None,
        verbose: bool = False,
        loss: LossFunction | str | None = None,
        rules: Sequence[Sequence[int]] | None = None,
    ) -> None:
        """Configure an :class:`ANFISClassifier` with the supplied hyper-parameters.

        Parameters
        ----------
        n_classes : int, optional
            Number of output classes. Must be at least two when provided. If
            omitted, the value is inferred from the training targets during
            the first ``fit`` call.
        n_mfs : int, default=3
            Default number of membership functions to allocate per input when
            inferred from data.
        mf_type : str, default="gaussian"
            Membership function family used for automatically generated
            membership functions.
        init : {"grid", "fcm", "random", None}, default="grid"
            Initialization strategy applied when synthesizing membership
            functions from the training data. ``None`` falls back to ``"grid"``.
        overlap : float, default=0.5
            Desired overlap between adjacent membership functions during
            automatic generation.
        margin : float, default=0.10
            Additional range padding applied around observed feature minima
            and maxima for grid initialization.
        inputs_config : Mapping, optional
            Per-feature overrides for the generated membership functions.
            Keys may be feature names (when ``X`` is a :class:`pandas.DataFrame`),
            integer indices, or ``"x{i}"`` aliases. Values may include dictionaries
            with membership-generation arguments, explicit membership function
            sequences, or ``None`` to retain defaults.
        random_state : int, optional
            Seed forwarded to stochastic initializers and optimizers.
        optimizer : str | BaseTrainer | type[BaseTrainer] | None, default="adam"
            Training algorithm identifier or instance. String aliases are looked
            up in :data:`TRAINER_REGISTRY`. ``None`` defaults to ``"adam"``.
            Hybrid variants that depend on least-squares refinements are limited
            to regression and raise ``ValueError`` when supplied here.
        optimizer_params : Mapping, optional
            Additional keyword arguments provided to the trainer constructor
            when a string alias or trainer class is supplied.
        learning_rate, epochs, batch_size, shuffle, verbose : optional
            Convenience hyper-parameters injected into the trainer whenever the
            chosen implementation accepts them. ``shuffle`` supports ``False``
            to disable random shuffling.
        loss : str | LossFunction, optional
            Custom loss specification forwarded to trainers that expose a
            ``loss`` parameter. ``None`` resolves to cross-entropy.
        rules : Sequence[Sequence[int]] | None, optional
            Optional explicit fuzzy rule definitions. Each rule lists the
            membership-function index for each input. ``None`` uses the full
            Cartesian product of configured membership functions.
        """
        if n_classes is not None and int(n_classes) < 2:
            raise ValueError("n_classes must be >= 2")
        self.n_classes: int | None = int(n_classes) if n_classes is not None else None
        self.n_mfs = int(n_mfs)
        self.mf_type = str(mf_type)
        self.init = None if init is None else str(init)
        self.overlap = float(overlap)
        self.margin = float(margin)
        self.inputs_config: dict[Any, InputConfigValue] | None = (
            dict(inputs_config) if inputs_config is not None else None
        )
        self.random_state = random_state
        self.optimizer = optimizer
        self.optimizer_params = dict(optimizer_params) if optimizer_params is not None else None
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.verbose = verbose
        self.loss = loss
        self.rules = None if rules is None else tuple(tuple(int(idx) for idx in rule) for rule in rules)

        # Fitted attributes (initialised during fit)
        self.model_: TSKANFISClassifier | None = None
        self.optimizer_: BaseTrainer | None = None
        self.feature_names_in_: list[str] | None = None
        self.n_features_in_: int | None = None
        self.training_history_: TrainingHistory | None = None
        self.input_specs_: list[NormalizedInputSpec] | None = None
        self.classes_: np.ndarray | None = None
        self._class_to_index_: dict[Any, int] | None = None
        self.rules_: list[tuple[int, ...]] | None = None

        # ------------------------------------------------------------------
        # Public API
        # ------------------------------------------------------------------

    def fit(
        self,
        X: npt.ArrayLike,
        y: npt.ArrayLike,
        *,
        validation_data: tuple[np.ndarray, np.ndarray] | None = None,
        validation_frequency: int = 1,
        verbose: bool | None = None,
        **fit_params: Any,
    ) -> ANFISClassifier:
        """Fit the classifier on labelled data.

        Parameters
        ----------
        X : array-like
            Training inputs with shape ``(n_samples, n_features)``.
        y : array-like
            Target labels. Accepts integer or string labels as well as one-hot
            matrices with shape ``(n_samples, n_classes)``.
        validation_data : tuple[np.ndarray, np.ndarray], optional
            Optional validation split supplied to the underlying trainer.
            Inputs and targets must already be numeric and share the same row
            count.
        validation_frequency : int, default=1
            Frequency (in epochs) at which validation metrics are computed when
            ``validation_data`` is provided.
        verbose : bool, optional
            Override the estimator's ``verbose`` flag for this fit call. When
            provided, the value is stored on the estimator and forwarded to the
            trainer configuration.
        **fit_params : Any
            Additional keyword arguments forwarded directly to the trainer
            ``fit`` method.

        Returns:
        -------
        ANFISClassifier
            Reference to ``self`` to enable fluent-style chaining.

        Raises:
        ------
        ValueError
            If the input arrays disagree on the number of samples or the label
            encoding is incompatible with the configured ``n_classes``.
        TypeError
            If the trainer ``fit`` implementation does not return a
            dictionary-style training history.
        """
        X_arr, feature_names = ensure_2d_array(X)
        n_samples = X_arr.shape[0]
        y_encoded, classes = self._encode_targets(y, n_samples)

        self.classes_ = classes
        self._class_to_index_ = {self._normalize_class_key(cls): idx for idx, cls in enumerate(classes.tolist())}

        self.feature_names_in_ = feature_names
        self.n_features_in_ = X_arr.shape[1]
        self.input_specs_ = self._resolve_input_specs(feature_names)

        if verbose is not None:
            self.verbose = bool(verbose)

        _ensure_training_logging(self.verbose)
        if self.n_classes is None:
            raise RuntimeError("n_classes could not be inferred from the provided targets")
        self.model_ = self._build_model(X_arr, feature_names)
        trainer = self._instantiate_trainer()
        self.optimizer_ = trainer
        trainer_kwargs: dict[str, Any] = dict(fit_params)
        if validation_data is not None:
            trainer_kwargs.setdefault("validation_data", validation_data)
        if validation_data is not None or validation_frequency != 1:
            trainer_kwargs.setdefault("validation_frequency", validation_frequency)

        history = trainer.fit(self.model_, X_arr, y_encoded, **trainer_kwargs)
        if not isinstance(history, dict):
            raise TypeError("Trainer.fit must return a TrainingHistory dictionary")
        self.training_history_ = history
        self.rules_ = self.model_.rules

        self._mark_fitted()
        return self

    def predict(self, X: npt.ArrayLike) -> np.ndarray:
        """Predict class labels for the provided samples.

        Parameters
        ----------
        X : array-like
            Samples to classify. One-dimensional arrays are treated as a single
            sample; two-dimensional arrays must have shape ``(n_samples, n_features)``.

        Returns:
        -------
        np.ndarray
            Predicted class labels with shape ``(n_samples,)``.

        Raises:
        ------
        RuntimeError
            If invoked before the estimator is fitted.
        ValueError
            When the supplied samples do not match the fitted feature count.
        """
        check_is_fitted(self, attributes=["model_", "classes_"])
        X_arr = np.asarray(X, dtype=float)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        else:
            X_arr, _ = ensure_2d_array(X)

        if self.n_features_in_ is None:
            raise RuntimeError("Model must be fitted before calling predict.")
        if X_arr.shape[1] != self.n_features_in_:
            raise ValueError(f"Feature mismatch: expected {self.n_features_in_}, got {X_arr.shape[1]}.")
        model = self.model_
        classes = self.classes_
        if model is None or classes is None:
            raise RuntimeError("Model must be fitted before calling predict.")
        encoded = np.asarray(model.predict(X_arr), dtype=int)
        return np.asarray(classes)[encoded]

    def predict_proba(self, X: npt.ArrayLike) -> np.ndarray:
        """Predict class probabilities for the provided samples.

        Parameters
        ----------
        X : array-like
            Samples for which to estimate class probabilities.

        Returns:
        -------
        np.ndarray
            Matrix of shape ``(n_samples, n_classes)`` containing class
            probability estimates.

        Raises:
        ------
        RuntimeError
            If the estimator has not been fitted.
        ValueError
            If sample dimensionality does not match the fitted feature count.
        """
        check_is_fitted(self, attributes=["model_"])
        X_arr = np.asarray(X, dtype=float)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        else:
            X_arr, _ = ensure_2d_array(X)

        if self.n_features_in_ is None:
            raise RuntimeError("Model must be fitted before calling predict_proba.")
        if X_arr.shape[1] != self.n_features_in_:
            raise ValueError(f"Feature mismatch: expected {self.n_features_in_}, got {X_arr.shape[1]}.")
        model = self.model_
        if model is None:
            raise RuntimeError("Model must be fitted before calling predict_proba.")
        return np.asarray(model.predict_proba(X_arr), dtype=float)

    def evaluate(
        self,
        X: npt.ArrayLike,
        y: npt.ArrayLike,
        *,
        return_dict: bool = True,
        print_results: bool = True,
    ) -> Mapping[str, MetricValue] | None:
        """Evaluate predictive performance on a labelled dataset.

        Parameters
        ----------
        X : array-like
            Evaluation inputs.
        y : array-like
            Ground-truth labels. Accepts integer labels or one-hot encodings.
        return_dict : bool, default=True
            When ``True`` return the computed metric dictionary; when ``False``
            return ``None`` after optional printing.
        print_results : bool, default=True
            Emit a formatted summary to stdout. Set to ``False`` to suppress
            printing.

        Returns:
        -------
        Mapping[str, MetricValue] | None
            Dictionary containing accuracy, balanced accuracy, macro/micro
            precision/recall/F1 scores, and the confusion matrix when
            ``return_dict`` is ``True``; otherwise ``None``.

        Raises:
        ------
        RuntimeError
            If called before the estimator has been fitted.
        ValueError
            When ``X`` and ``y`` disagree on sample count or labels are
            incompatible with the configured class count.
        """
        check_is_fitted(self, attributes=["model_"])
        X_arr, _ = ensure_2d_array(X)
        encoded_targets, _ = self._encode_targets(y, X_arr.shape[0], allow_partial_classes=True)
        proba = self.predict_proba(X_arr)
        metrics: dict[str, MetricValue] = ANFISMetrics.classification_metrics(encoded_targets, proba)
        metrics.pop("log_loss", None)
        if print_results:

            def _is_effectively_nan(value: Any) -> bool:
                if value is None:
                    return True
                if isinstance(value, (float, np.floating)):
                    return bool(np.isnan(value))
                if isinstance(value, (int, np.integer)):
                    return False
                if isinstance(value, np.ndarray):
                    if value.size == 0:
                        return False
                    if np.issubdtype(value.dtype, np.number):
                        return bool(np.isnan(value.astype(float)).all())
                    return False
                return False

            print("ANFISClassifier evaluation:")  # noqa: T201
            for key, value in metrics.items():
                if _is_effectively_nan(value):
                    continue
                if isinstance(value, (float, np.floating)):
                    display_value = f"{float(value):.6f}"
                    print(f"  {key}: {display_value}")  # noqa: T201
                elif isinstance(value, (int, np.integer)):
                    print(f"  {key}: {int(value)}")  # noqa: T201
                elif isinstance(value, np.ndarray):
                    array_repr = np.array2string(value, precision=6, suppress_small=True)
                    if "\n" in array_repr:
                        indented = "\n    ".join(array_repr.splitlines())
                        print(f"  {key}:\n    {indented}")  # noqa: T201
                    else:
                        print(f"  {key}: {array_repr}")  # noqa: T201
                else:
                    print(f"  {key}: {value}")  # noqa: T201
        return metrics if return_dict else None

    def get_rules(self) -> tuple[tuple[int, ...], ...]:
        """Return the fuzzy rule index combinations used by the fitted model.

        Returns:
        -------
        tuple[tuple[int, ...], ...]
            Immutable tuple describing each fuzzy rule as a per-input
            membership index.

        Raises:
        ------
        RuntimeError
            If invoked before ``fit`` completes.
        """
        check_is_fitted(self, attributes=["rules_"])
        if not self.rules_:
            return ()
        return tuple(tuple(rule) for rule in self.rules_)

    def save(self, filepath: str | Path) -> None:
        """Serialize this estimator (including fitted artefacts) to ``filepath``."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            pickle.dump(self, stream)  # nosec B301

    @classmethod
    def load(cls, filepath: str | Path) -> ANFISClassifier:
        """Load a pickled ``ANFISClassifier`` from ``filepath`` and validate its type."""
        path = Path(filepath)
        with path.open("rb") as stream:
            estimator = pickle.load(stream)  # nosec B301
        if not isinstance(estimator, cls):
            raise TypeError(f"Expected pickled {cls.__name__} instance, got {type(estimator).__name__}.")
        return estimator

    def __repr__(self) -> str:
        """Return a formatted representation summarising configuration and fitted artefacts."""
        return format_estimator_repr(
            type(self).__name__,
            self._repr_config_pairs(),
            self._repr_children_entries(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_input_specs(self, feature_names: list[str]) -> list[NormalizedInputSpec]:
        resolved: list[NormalizedInputSpec] = []
        for idx, name in enumerate(feature_names):
            spec = self._fetch_input_config(name, idx)
            resolved.append(self._normalize_input_spec(spec))
        return resolved

    def _fetch_input_config(self, name: str, index: int) -> InputConfigValue:
        if self.inputs_config is None:
            return None
        spec = self.inputs_config.get(name)
        if spec is not None:
            return spec
        spec = self.inputs_config.get(index)
        if spec is not None:
            return spec
        alt_key = f"x{index + 1}"
        return self.inputs_config.get(alt_key)

    def _normalize_input_spec(self, spec: InputConfigValue) -> NormalizedInputSpec:
        config: NormalizedInputSpec = {
            "n_mfs": self.n_mfs,
            "mf_type": self.mf_type,
            "init": self.init,
            "overlap": self.overlap,
            "margin": self.margin,
            "range": None,
            "membership_functions": None,
        }
        if spec is None:
            return config
        if isinstance(spec, (list, tuple)) and all(isinstance(mf, MembershipFunction) for mf in spec):
            config["membership_functions"] = list(spec)
            return config
        if isinstance(spec, MembershipFunction):
            config["membership_functions"] = [spec]
            return config
        if isinstance(spec, Mapping):
            mapping = dict(spec)
            if "mfs" in mapping and "membership_functions" not in mapping:
                mapping = {**mapping, "membership_functions": mapping["mfs"]}
            for key in ("n_mfs", "mf_type", "init", "overlap", "margin", "range", "membership_functions"):
                if key in mapping and (mapping[key] is not None or key == "init"):
                    config[key] = mapping[key]
            return config
        if isinstance(spec, str):
            config["mf_type"] = spec
            return config
        if isinstance(spec, int):
            config["n_mfs"] = int(spec)
            return config
        raise TypeError(f"Unsupported input configuration type: {type(spec)!r}")

    def _build_model(self, X: np.ndarray, feature_names: list[str]) -> TSKANFISClassifier:
        builder = ANFISBuilder()
        if self.input_specs_ is None:
            raise RuntimeError("Input specifications must be resolved before building the model.")
        if self.n_classes is None:
            raise RuntimeError("Number of classes must be known before constructing the low-level model.")
        for idx, name in enumerate(feature_names):
            column = X[:, idx]
            spec = self.input_specs_[idx]
            mf_list = spec.get("membership_functions")
            range_override = spec.get("range")
            if mf_list is not None:
                builder.input_mfs[name] = [cast(MembershipFunction, mf) for mf in mf_list]
                if range_override is not None:
                    range_tuple = tuple(float(v) for v in range_override)
                    if len(range_tuple) != 2:
                        raise ValueError("range overrides must contain exactly two values")
                    builder.input_ranges[name] = (range_tuple[0], range_tuple[1])
                else:
                    builder.input_ranges[name] = (float(np.min(column)), float(np.max(column)))
                continue
            if range_override is not None:
                range_tuple = tuple(float(v) for v in range_override)
                if len(range_tuple) != 2:
                    raise ValueError("range overrides must contain exactly two values")
                rmin, rmax = range_tuple
                builder.add_input(
                    name,
                    float(rmin),
                    float(rmax),
                    int(spec["n_mfs"]),
                    str(spec["mf_type"]),
                    overlap=float(spec["overlap"]),
                )
            else:
                init_strategy = spec.get("init")
                init_arg = None if init_strategy is None else str(init_strategy)
                builder.add_input_from_data(
                    name,
                    column,
                    n_mfs=int(spec["n_mfs"]),
                    mf_type=str(spec["mf_type"]),
                    overlap=float(spec["overlap"]),
                    margin=float(spec["margin"]),
                    init=init_arg,
                    random_state=self.random_state,
                )
        return TSKANFISClassifier(
            builder.input_mfs,
            n_classes=self.n_classes,
            random_state=self.random_state,
            rules=self.rules,
        )

    # ------------------------------------------------------------------
    # Representation helpers
    # ------------------------------------------------------------------
    def _repr_config_pairs(self) -> list[tuple[str, Any]]:
        optimizer_label = self._describe_optimizer_config(self.optimizer)
        pairs: list[tuple[str, Any]] = [
            ("n_classes", self.n_classes),
            ("n_mfs", self.n_mfs),
            ("mf_type", self.mf_type),
            ("init", self.init),
            ("overlap", self.overlap),
            ("margin", self.margin),
            ("random_state", self.random_state),
            ("optimizer", optimizer_label),
            ("learning_rate", self.learning_rate),
            ("epochs", self.epochs),
            ("batch_size", self.batch_size),
            ("shuffle", self.shuffle),
            ("loss", self.loss),
        ]
        if self.rules is not None:
            pairs.append(("rules", f"preset:{len(self.rules)}"))
        if self.optimizer_params:
            pairs.append(("optimizer_params", self.optimizer_params))
        return pairs

    def _repr_children_entries(self) -> list[tuple[str, str]]:
        if not getattr(self, "is_fitted_", False):
            return []

        children: list[tuple[str, str]] = []
        model = getattr(self, "model_", None)
        if model is not None:
            children.append(("model_", self._summarize_model(model)))

        optimizer = getattr(self, "optimizer_", None)
        if optimizer is not None:
            children.append(("optimizer_", self._summarize_optimizer(optimizer)))

        history = getattr(self, "training_history_", None)
        if isinstance(history, Mapping) and history:
            children.append(("training_history_", self._summarize_history(history)))

        class_labels = getattr(self, "classes_", None)
        if class_labels is not None:
            labels = list(map(str, class_labels))
            preview = labels if len(labels) <= 6 else labels[:5] + ["..."]
            children.append(("classes_", ", ".join(preview)))

        learned_rules = getattr(self, "rules_", None)
        if learned_rules is not None:
            children.append(("rules_", f"{len(learned_rules)} learned"))

        feature_names = getattr(self, "feature_names_in_", None)
        if feature_names is not None:
            children.append(("feature_names_in_", ", ".join(feature_names)))

        return children

    @staticmethod
    def _describe_optimizer_config(optimizer: Any) -> Any:
        if optimizer is None:
            return None
        if isinstance(optimizer, str):
            return optimizer
        if inspect.isclass(optimizer):
            return optimizer.__name__
        if isinstance(optimizer, BaseTrainer):
            return type(optimizer).__name__
        return repr(optimizer)

    def _summarize_model(self, model: Any) -> str:
        name = type(model).__name__
        parts = [name]
        n_inputs = getattr(model, "n_inputs", None)
        n_rules = getattr(model, "n_rules", None)
        n_classes = getattr(model, "n_classes", None)
        if n_inputs is not None:
            parts.append(f"n_inputs={n_inputs}")
        if n_rules is not None:
            parts.append(f"n_rules={n_rules}")
        if n_classes is not None:
            parts.append(f"n_classes={n_classes}")
        input_names = getattr(model, "input_names", None)
        if input_names:
            parts.append(f"inputs={list(input_names)}")
        mf_map = getattr(model, "membership_functions", None)
        if isinstance(mf_map, Mapping) and mf_map:
            counts = [len(mf_map[name]) for name in getattr(model, "input_names", mf_map.keys())]
            parts.append(f"mfs_per_input={counts}")
        return ", ".join(parts)

    def _summarize_optimizer(self, optimizer: BaseTrainer) -> str:
        name = type(optimizer).__name__
        fields: list[str] = []
        for attr in ("learning_rate", "epochs", "batch_size", "shuffle", "verbose", "loss"):
            if hasattr(optimizer, attr):
                value = getattr(optimizer, attr)
                if value is not None:
                    fields.append(f"{attr}={value!r}")
        if hasattr(optimizer, "__dict__") and not fields:
            return repr(optimizer)
        return f"{name}({', '.join(fields)})" if fields else name

    @staticmethod
    def _summarize_history(history: Mapping[str, Any]) -> str:
        segments: list[str] = []
        for key in ("train", "val", "validation", "metrics"):
            if key in history and isinstance(history[key], Sequence):
                series = history[key]
                length = len(series)
                if length == 0:
                    segments.append(f"{key}=0")
                else:
                    tail = series[-1]
                    if isinstance(tail, (float, np.floating)):
                        segments.append(f"{key}={length} (last={float(tail):.4f})")
                    else:
                        segments.append(f"{key}={length}")
        return ", ".join(segments) if segments else "{}"

    def _instantiate_trainer(self) -> BaseTrainer:
        optimizer = self.optimizer if self.optimizer is not None else "adam"
        if isinstance(optimizer, BaseTrainer):
            if isinstance(optimizer, _UNSUPPORTED_TRAINERS):
                raise ValueError(
                    "Hybrid-style trainers that rely on least-squares updates are not supported by ANFISClassifier. "
                    "Choose among: "
                    f"{', '.join(sorted(TRAINER_REGISTRY.keys()))}."
                )
            trainer = deepcopy(optimizer)
            self._apply_runtime_overrides(trainer)
            return trainer
        if inspect.isclass(optimizer) and issubclass(optimizer, BaseTrainer):
            if issubclass(optimizer, _UNSUPPORTED_TRAINERS):
                raise ValueError(
                    "Hybrid-style trainers that rely on least-squares updates are not supported by ANFISClassifier. "
                    "Choose among: "
                    f"{', '.join(sorted(TRAINER_REGISTRY.keys()))}."
                )
            params = self._collect_trainer_params(optimizer)
            return optimizer(**params)
        if isinstance(optimizer, str):
            key = optimizer.lower()
            if key in {"hybrid", "hybrid_adam"}:
                raise ValueError(
                    "Hybrid-style optimizers that combine least-squares with gradient descent are only available "
                    "for regression. Supported classifier optimizers: "
                    f"{', '.join(sorted(TRAINER_REGISTRY.keys()))}."
                )
            if key not in TRAINER_REGISTRY:
                supported = ", ".join(sorted(TRAINER_REGISTRY.keys()))
                raise ValueError(f"Unknown optimizer '{optimizer}'. Supported: {supported}")
            trainer_cls = TRAINER_REGISTRY[key]
            params = self._collect_trainer_params(trainer_cls)
            return trainer_cls(**params)
        raise TypeError("optimizer must be a string identifier, BaseTrainer instance, or BaseTrainer subclass")

    def _collect_trainer_params(self, trainer_cls: type[BaseTrainer]) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if self.optimizer_params is not None:
            params.update(self.optimizer_params)

        overrides: dict[str, Any] = {
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "shuffle": self.shuffle,
            "verbose": self.verbose,
            "loss": self._resolved_loss_spec(),
        }
        for key, value in overrides.items():
            if value is not None and key not in params:
                params[key] = value
        if self.shuffle is not None:
            params.setdefault("shuffle", self.shuffle)
        params.setdefault("verbose", self.verbose)

        sig = inspect.signature(trainer_cls)
        filtered: dict[str, Any] = {}
        for name in sig.parameters:
            if name == "self":
                continue
            if name in params:
                filtered[name] = params[name]
        return filtered

    def _apply_runtime_overrides(self, trainer: BaseTrainer) -> None:
        resolved_loss = self._resolved_loss_spec()
        for attr, value in (
            ("learning_rate", self.learning_rate),
            ("epochs", self.epochs),
            ("batch_size", self.batch_size),
            ("shuffle", self.shuffle),
            ("verbose", self.verbose),
        ):
            if value is not None and hasattr(trainer, attr):
                setattr(trainer, attr, value)
        if hasattr(trainer, "loss") and resolved_loss is not None:
            trainer.loss = resolved_loss

    def _encode_targets(
        self,
        y,
        n_samples: int,
        *,
        allow_partial_classes: bool = False,
    ) -> tuple[np.ndarray, np.ndarray]:
        y_arr: np.ndarray = np.asarray(y)
        if y_arr.ndim == 2:
            if y_arr.shape[0] != n_samples:
                raise ValueError("y must contain the same number of samples as X")
            n_classes = self.n_classes
            if n_classes is None:
                inferred = y_arr.shape[1]
                if inferred < 2:
                    raise ValueError("One-hot targets must encode at least two classes for classification.")
                self.n_classes = inferred
                n_classes = inferred
            if y_arr.shape[1] != n_classes:
                raise ValueError(f"One-hot targets must have shape (n_samples, n_classes={n_classes}).")
            encoded = np.argmax(y_arr, axis=1).astype(int)
            classes = np.arange(n_classes)
            return encoded, classes
        if y_arr.ndim == 1:
            if y_arr.shape[0] != n_samples:
                raise ValueError("y must contain the same number of samples as X")
            classes = np.unique(y_arr)
            n_unique = classes.size
            if n_unique < 2 and not allow_partial_classes:
                raise ValueError("Classification targets must include at least two distinct classes.")
            n_classes = self.n_classes
            if n_classes is None:
                if n_unique < 2:
                    raise ValueError("Classification targets must include at least two distinct classes.")
                self.n_classes = n_unique
                n_classes = n_unique
            if not allow_partial_classes and n_unique != n_classes:
                raise ValueError(f"y contains {n_unique} unique classes but estimator was configured for {n_classes}.")
            if n_unique > n_classes:
                raise ValueError(
                    f"y contains {n_unique} unique classes which exceeds configured n_classes={n_classes}."
                )
            normalized_classes = [self._normalize_class_key(cls) for cls in classes.tolist()]
            mapping = {cls: idx for idx, cls in enumerate(normalized_classes)}
            encoded = np.array([mapping[self._normalize_class_key(val)] for val in y_arr], dtype=int)
            return encoded, np.asarray(normalized_classes)
        raise ValueError("Target array must be 1-dimensional or a one-hot encoded 2D array.")

    def _resolved_loss_spec(self) -> LossFunction | str:
        if self.loss is None:
            return "cross_entropy"
        return self.loss

    def _more_tags(self) -> dict[str, Any]:  # pragma: no cover - informational hook
        return {
            "estimator_type": "classifier",
            "requires_y": True,
        }

    @staticmethod
    def _normalize_class_key(value: Any) -> Any:
        return value.item() if isinstance(value, np.generic) else value
