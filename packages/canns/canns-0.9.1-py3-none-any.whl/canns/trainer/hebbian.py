from __future__ import annotations

from collections.abc import Callable, Iterable

import brainstate
import jax.numpy as jnp
from tqdm import tqdm  # type: ignore

from ..models.brain_inspired import BrainInspiredModel
from ._base import Trainer

__all__ = ["HebbianTrainer"]


class HebbianTrainer(Trainer):
    """
    Generic Hebbian trainer with progress reporting.

    Overview
    - Uses a model-exposed weight parameter (default attribute name: ``W``) to apply a
      standard Hebbian update. If unavailable, falls back to the model's
      ``apply_hebbian_learning``.
    - Works with models that expose a parameter object with a ``.value`` ndarray of shape
      (N, N) (e.g., ``brainstate.ParamState``).

    Generic rule
    - For patterns ``x`` (shape: (N,)), compute optional mean activity ``rho`` and update
      ``W <- W + sum_i (x_i - rho)(x_i - rho)^T``.
    - Options allow zeroing the diagonal and normalizing by number of patterns.

    Key options
    - ``weight_attr``: Name of the weight attribute on the model (default: "W").
    - ``subtract_mean``: Whether to center patterns by mean activity ``rho``.
    - ``zero_diagonal``: Whether to set diagonal of ``W`` to zero after update.
    - ``normalize_by_patterns``: Divide accumulated outer-products by number of patterns.
    - ``prefer_generic``: Prefer the generic Hebbian rule over model-specific method.
    - ``state_attr``: Name of the state vector attribute for prediction (default: ``s``; or
      model-provided ``predict_state_attr``).
    - ``prefer_generic_predict``: Prefer the trainer's generic predict loop over the
      model's ``predict`` implementation (falls back automatically when unsupported).
    """

    def __init__(
        self,
        model: BrainInspiredModel,
        show_iteration_progress: bool = False,  # Default to False for cleaner display
        compiled_prediction: bool = True,
        *,
        # Generic Hebbian options
        weight_attr: str | None = "W",
        subtract_mean: bool = True,
        zero_diagonal: bool = True,
        normalize_by_patterns: bool = True,
        prefer_generic: bool = True,
        # Generic predict options
        state_attr: str | None = None,
        prefer_generic_predict: bool = True,
        preserve_on_resize: bool = True,
    ):
        """
        Initialize Hebbian trainer.

        Args:
            model: The model to train
            show_iteration_progress: Whether to show progress for individual pattern convergence
            compiled_prediction: Whether to use compiled prediction by default (faster but no iteration progress)
            weight_attr: Name of model attribute holding the connection weights (default: "W").
            subtract_mean: Subtract dataset mean activity (rho) before outer-product.
            zero_diagonal: Force zero self-connections after update.
            normalize_by_patterns: Divide accumulated outer-products by number of patterns.
            prefer_generic: If True, use trainer's generic Hebbian rule when possible; otherwise
                call the model's own implementation if available.
        """
        super().__init__(
            model=model,
            show_iteration_progress=show_iteration_progress,
            compiled_prediction=compiled_prediction,
        )
        # Generic Hebbian config
        self.weight_attr = weight_attr
        self.subtract_mean = subtract_mean
        self.zero_diagonal = zero_diagonal
        self.normalize_by_patterns = normalize_by_patterns
        self.prefer_generic = prefer_generic
        # Generic predict config
        self.state_attr = state_attr
        self.prefer_generic_predict = prefer_generic_predict
        self.preserve_on_resize = preserve_on_resize

    def train(self, train_data: Iterable):
        """
        Train the model using Hebbian learning.

        Behavior
        - Preferred path: apply a generic Hebbian update directly to ``model.<weight_attr>``.
        - Fallback path: call ``model.apply_hebbian_learning(train_data)`` if generic path
          is unavailable.

        Requirements for generic path
        - Model must expose ``model.<weight_attr>`` with a ``.value`` array of shape (N, N).
        - Optionally, models can declare ``weight_attr`` property to specify the
          attribute name, allowing ``HebbianTrainer(..., weight_attr=None)``.
        """
        used_generic = False

        # Materialize training data (avoid consuming generators twice)
        patterns = [jnp.asarray(p) for p in train_data]
        if len(patterns) == 0:
            return

        # Determine the weight attribute to use (allow model override via `weight_attr`)
        weight_attr = self.weight_attr
        if weight_attr is None and hasattr(self.model, "weight_attr"):
            try:
                weight_attr = self.model.weight_attr  # could be property/str
                if callable(weight_attr):
                    weight_attr = weight_attr()
            except Exception:
                weight_attr = None

        # Ensure model dimensionality matches training patterns (use first pattern)
        n = int(jnp.asarray(patterns[0]).shape[0])
        self._ensure_model_dim(n, weight_attr)

        # Try generic path if preferred
        if self.prefer_generic and weight_attr is not None:
            param = getattr(self.model, weight_attr, None)
            if param is not None and hasattr(param, "value"):
                W = param.value
                if (
                    W is not None
                    and hasattr(W, "shape")
                    and len(W.shape) == 2
                    and W.shape[0] == W.shape[1]
                ):
                    self._apply_generic_hebbian(patterns, param)
                    used_generic = True

        # Fallback to model-specific implementation if generic path wasn't used
        if not used_generic:
            if hasattr(self.model, "apply_hebbian_learning"):
                self.model.apply_hebbian_learning(patterns)
            else:
                raise AttributeError(
                    "Model does not expose a suitable weight attribute for generic Hebbian "
                    "learning and has no `apply_hebbian_learning` method."
                )

    def _apply_generic_hebbian(self, train_data: Iterable, weight_param) -> None:
        """
        Apply generic Hebbian learning.

        Rule
        - ``W <- W + Σ (t t^T)`` where ``t = x - rho`` if centering enabled, otherwise ``t = x``.
        - If ``normalize_by_patterns`` is True, divide by number of patterns.
        - If ``zero_diagonal`` is True, set diagonal to zero after update.

        Args
        - train_data: Iterable of 1D patterns (numpy/jax arrays) of shape (N,).
        - weight_param: Parameter object with ``.value`` as ndarray (N, N).
        """
        # Gather patterns as jax arrays
        patterns = [jnp.asarray(p, dtype=jnp.float32) for p in train_data]
        if len(patterns) == 0:
            return
        num_patterns = len(patterns)

        # Infer size and basic checks
        n = patterns[0].shape[0]
        for p in patterns:
            if p.ndim != 1 or p.shape[0] != n:
                raise ValueError("All patterns must be 1D with consistent length.")

        # Create training progress bar via tqdm
        total_steps = num_patterns * (2 if self.subtract_mean else 1)
        pbar = tqdm(total=total_steps, desc="Learning patterns", ncols=80, leave=False)

        try:
            # Compute mean activity (rho) across dataset if requested
            rho = jnp.float32(0.0)
            if self.subtract_mean:
                total_sum = jnp.float32(0.0)
                for p in patterns:
                    total_sum = total_sum + jnp.sum(p)
                    pbar.update(1)
                rho = total_sum / (num_patterns * n)

            # Accumulate outer products
            W_accum = jnp.zeros((n, n), dtype=jnp.float32)
            for p in patterns:
                t = p - rho if self.subtract_mean else p
                W_accum = W_accum + jnp.outer(t, t)
                pbar.update(1)

            if self.normalize_by_patterns:
                W_accum = W_accum / num_patterns

            # Update with existing weights
            W_new = jnp.asarray(weight_param.value, dtype=jnp.float32) + W_accum

            # Force zero diagonal if required
            if self.zero_diagonal:
                W_new = W_new - jnp.diag(jnp.diag(W_new))

            weight_param.value = W_new
        finally:
            pbar.close()

    def predict(
        self,
        pattern,
        num_iter: int = 20,
        compiled: bool | None = None,
        show_progress: bool | None = None,
        convergence_threshold: float = 1e-10,
        progress_callback: Callable[[int, float, bool, float], None] | None = None,
    ):
        """
        Predict a single pattern.

        Args:
            pattern: Input pattern to predict
            num_iter: Maximum number of iterations
            compiled: Override default compiled setting
            show_progress: Override default progress setting
            convergence_threshold: Energy change threshold for convergence

        Returns:
            Predicted pattern
        """
        # Always use compiled path; ignore `compiled` and iteration progress flags.
        # Keep parameters for backward compatibility.
        compiled = True
        if show_progress is None:
            show_progress = False

        # Create progress bar callback if needed
        bar_callback = None
        pbar = None

        if show_progress and not compiled:
            pbar = tqdm(total=num_iter, desc="Converging", ncols=80, leave=False)

            def bar_callback(iteration, energy, converged, energy_change):
                # Update with simpler format to avoid clutter
                status_icon = "✓" if converged else "→"
                energy_str = f"{energy:.0f}" if abs(energy) > 1000 else f"{energy:.3f}"

                pbar.set_postfix(E=energy_str, st=status_icon)
                pbar.update(1)
                if converged:
                    # Fill remaining iterations to show completion
                    remaining = num_iter - iteration
                    if remaining > 0:
                        pbar.update(remaining)

        # Always use generic predict (no backward-compat call to model.predict)
        # Check capability: model must have update, energy, and a vector state attr
        state_attr = self._resolve_state_attr()
        state_param = getattr(self.model, state_attr, None)
        if not (
            hasattr(self.model, "update")
            and hasattr(self.model, "energy")
            and state_param is not None
            and hasattr(state_param, "value")
        ):
            raise AttributeError(
                "Generic prediction requires model.update, model.energy, and a state vector "
                f"attribute '{state_attr}' with a '.value' array."
            )

        # Initialize state
        # Ensure dimensionality matches pattern
        n = int(jnp.asarray(pattern).shape[0])
        self._ensure_model_dim(
            n,
            self.weight_attr
            if self.weight_attr is not None
            else getattr(self.model, "weight_attr", None),
        )
        # Refresh state_param after potential resize
        state_attr = self._resolve_state_attr()
        state_param = getattr(self.model, state_attr, None)
        self._set_state_vector(pattern, state_param)

        # Prepare combined callback
        def combined_callback(iteration, energy, converged, energy_change):
            if progress_callback is not None:
                try:
                    progress_callback(iteration, energy, converged, energy_change)
                except Exception:
                    pass
            if bar_callback is not None:
                bar_callback(iteration, energy, converged, energy_change)

        # Run (always compiled path)
        try:
            result = self._predict_generic_compiled(num_iter, state_param)
        finally:
            if pbar is not None:
                pbar.close()

        return result

    def _ensure_model_dim(self, n: int, weight_attr: str | None):
        """Ensure model parameter/state dimensionality equals n.

        Tries model.resize if available; otherwise, adjusts weight/state arrays directly.
        """
        # Prefer model-provided resize
        if hasattr(self.model, "resize"):
            try:
                self.model.resize(n, preserve_submatrix=self.preserve_on_resize)
                return
            except Exception:
                pass

        # Fallback: attempt to resize arrays
        if weight_attr is not None:
            param = getattr(self.model, weight_attr, None)
            if param is not None and hasattr(param, "value"):
                W = jnp.asarray(param.value)
                if W.ndim != 2 or W.shape[0] != n or W.shape[1] != n:
                    new_W = jnp.zeros((n, n), dtype=jnp.float32)
                    if self.preserve_on_resize and W.ndim == 2:
                        m0 = min(W.shape[0], n)
                        m1 = min(W.shape[1], n)
                        new_W = new_W.at[:m0, :m1].set(W[:m0, :m1])
                    param.value = new_W - jnp.diag(jnp.diag(new_W))

        # State vector
        state_attr = self._resolve_state_attr()
        state_param = getattr(self.model, state_attr, None)
        if state_param is not None and hasattr(state_param, "value"):
            s = jnp.asarray(state_param.value)
            if s.ndim != 1 or s.shape[0] != n:
                state_param.value = jnp.ones((n,), dtype=jnp.float32)

    def _resolve_state_attr(self) -> str:
        """
        Resolve the name of the state attribute to use for predictions.

        Checks in order:
        1. Explicit state_attr parameter from constructor
        2. Model's predict_state_attr hint (method or property)
        3. Default "s"

        Returns:
            str: Name of the state attribute (e.g., "s", "u", "r")
        """
        # Explicit override takes precedence
        if self.state_attr is not None:
            return self.state_attr
        # Model-provided hint
        if hasattr(self.model, "predict_state_attr"):
            try:
                attr = self.model.predict_state_attr
                if callable(attr):
                    attr = attr()
                if isinstance(attr, str):
                    return attr
            except Exception:
                pass
        # Default
        return "s"

    def _set_state_vector(self, pattern, state_param) -> None:
        """
        Set model state vector from a pattern array.

        Args:
            pattern: Input pattern to set as state
            state_param: State parameter object with .value attribute
        """
        vec = jnp.asarray(pattern, dtype=jnp.float32)
        state_param.value = vec

    def _get_state_vector(self, state_param):
        """
        Get current model state as a JAX array.

        Args:
            state_param: State parameter object with .value attribute

        Returns:
            jnp.ndarray: Current state vector
        """
        return jnp.asarray(state_param.value, dtype=jnp.float32)

    def _predict_generic_compiled(self, num_iter: int, state_param):
        """
        Run prediction with JAX-compiled while loop for maximum performance.

        Uses jax.lax.while_loop for efficient execution on GPU/TPU.
        No early stopping or progress tracking for compilation compatibility.

        Args:
            num_iter: Fixed number of iterations to run
            state_param: State parameter to update

        Returns:
            Final state vector after num_iter iterations
        """
        # Initial energy
        initial_energy = jnp.float32(self.model.energy)

        def cond_fn(carry):
            _, _, iteration = carry
            return iteration < num_iter

        def body_fn(carry):
            s, prev_energy, iteration = carry
            # Set current state
            state_param.value = s
            # Single update step
            self.model.update(prev_energy)
            # New state and energy
            new_s = jnp.array(state_param.value, dtype=jnp.float32)
            new_energy = jnp.float32(self.model.energy)
            return new_s, new_energy, iteration + 1

        initial_carry = (self._get_state_vector(state_param), initial_energy, 0)
        final_s, _, _ = brainstate.compile.while_loop(
            cond_fn,
            body_fn,
            initial_carry,
        )
        return final_s

    def _predict_generic_uncompiled(
        self,
        num_iter: int,
        progress_callback,
        convergence_threshold: float,
        state_param,
    ):
        """
        Run prediction with Python loop allowing early stopping and progress tracking.

        Uses standard Python for loop enabling convergence checks and callbacks.
        Less efficient than compiled version but provides more control and feedback.

        Args:
            num_iter: Maximum number of iterations
            progress_callback: Optional callback(iter, energy, converged, delta)
            convergence_threshold: Energy change threshold for early stopping
            state_param: State parameter to update

        Returns:
            Final state vector (may stop early if converged)
        """
        prev_energy = float(self.model.energy)
        for iteration in range(num_iter):
            self.model.update(prev_energy)
            current_energy = float(self.model.energy)
            energy_change = abs(current_energy - prev_energy)
            converged = energy_change < convergence_threshold
            if progress_callback is not None:
                progress_callback(iteration + 1, current_energy, converged, energy_change)
            if converged:
                break
            prev_energy = current_energy
        return self._get_state_vector(state_param)

    def predict_batch(
        self,
        patterns: list,
        num_iter: int = 20,
        compiled: bool | None = None,
        show_sample_progress: bool = True,
        show_iteration_progress: bool | None = None,
        convergence_threshold: float = 1e-10,
    ) -> list:
        """
        Predict multiple patterns with progress reporting.

        Args:
            patterns: List of input patterns to predict
            num_iter: Maximum number of iterations per pattern
            compiled: Override default compiled setting
            show_sample_progress: Whether to show progress across samples
            show_iteration_progress: Override default iteration progress setting
            convergence_threshold: Energy change threshold for convergence

        Returns:
            List of predicted patterns
        """
        # Always use compiled path (ignore flags)
        compiled = True
        show_iteration_progress = False

        results = []

        # Create sample-level progress bar
        sample_pbar = None
        if show_sample_progress:
            sample_pbar = tqdm(total=len(patterns), desc="Processing samples", ncols=80, leave=True)

        try:
            for i, pattern in enumerate(patterns):
                # Predict single pattern
                result = self.predict(
                    pattern,
                    num_iter=num_iter,
                    compiled=compiled,
                    show_progress=show_iteration_progress,
                    convergence_threshold=convergence_threshold,
                )
                results.append(result)

                # Update sample progress
                if sample_pbar is not None:
                    sample_pbar.set_postfix(sample=f"{i + 1}/{len(patterns)}")
                    sample_pbar.update(1)

        finally:
            if sample_pbar is not None:
                sample_pbar.close()

        return results
