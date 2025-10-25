from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from ..losses import mse_grad, mse_loss
from .base import BaseTrainer


@dataclass
class HybridTrainer(BaseTrainer):
    """Original Jang (1993) hybrid training: LSM for consequents + GD for antecedents.

    Notes:
        This trainer assumes a single-output regression head. It is not compatible with
        :class:`~anfis_toolbox.model.TSKANFISClassifier` or the high-level
        :class:`~anfis_toolbox.classifier.ANFISClassifier` facade.
    """

    learning_rate: float = 0.01
    epochs: int = 100
    verbose: bool = False

    def _prepare_training_data(self, model, X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return self._prepare_data(X, y)

    def _prepare_validation_data(
        self,
        model,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        return self._prepare_data(X_val, y_val)

    def init_state(self, model, X: np.ndarray, y: np.ndarray):
        """Hybrid trainer doesn't maintain optimizer state; returns None."""
        return None

    def train_step(self, model, Xb: np.ndarray, yb: np.ndarray, state):
        """Perform one hybrid step on a batch and return (loss, state).

        Equivalent to one iteration of the hybrid algorithm on the given batch.
        """
        Xb, yb = self._prepare_data(Xb, yb)
        # Forward to get normalized weights
        membership_outputs = model.membership_layer.forward(Xb)
        rule_strengths = model.rule_layer.forward(membership_outputs)
        normalized_weights = model.normalization_layer.forward(rule_strengths)

        # Build LSM system for batch
        ones_col = np.ones((Xb.shape[0], 1), dtype=float)
        x_bar = np.concatenate([Xb, ones_col], axis=1)
        A_blocks = [normalized_weights[:, j : j + 1] * x_bar for j in range(model.n_rules)]
        A = np.concatenate(A_blocks, axis=1)
        try:
            regularization = 1e-6 * np.eye(A.shape[1])
            ATA_reg = A.T @ A + regularization
            theta = np.linalg.solve(ATA_reg, A.T @ yb.flatten())
        except np.linalg.LinAlgError:
            logging.getLogger(__name__).warning("Matrix singular in LSM, using pseudo-inverse")
            theta = np.linalg.pinv(A) @ yb.flatten()
        model.consequent_layer.parameters = theta.reshape(model.n_rules, model.n_inputs + 1)

        # Loss and backward for antecedents only
        y_pred = model.consequent_layer.forward(Xb, normalized_weights)
        loss = mse_loss(yb, y_pred)
        dL_dy = mse_grad(yb, y_pred)
        dL_dnorm_w, _ = model.consequent_layer.backward(dL_dy)
        dL_dw = model.normalization_layer.backward(dL_dnorm_w)
        gradients = model.rule_layer.backward(dL_dw)
        model.membership_layer.backward(gradients)
        model._apply_membership_gradients(self.learning_rate)
        return float(loss), state

    def compute_loss(self, model, X: np.ndarray, y: np.ndarray) -> float:
        """Compute the hybrid MSE loss on prepared data without side effects."""
        X_arr, y_arr = self._prepare_data(X, y)
        membership_outputs = model.membership_layer.forward(X_arr)
        rule_strengths = model.rule_layer.forward(membership_outputs)
        normalized_weights = model.normalization_layer.forward(rule_strengths)
        preds = model.consequent_layer.forward(X_arr, normalized_weights)
        return float(mse_loss(y_arr, preds))

    @staticmethod
    def _prepare_data(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Ensure X, y are float arrays and y is 2D (n, 1) if originally 1D."""
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        return X, y
