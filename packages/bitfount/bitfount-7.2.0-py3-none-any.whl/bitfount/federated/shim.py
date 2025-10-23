"""Backend-agnostisc shims."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Union

import numpy as np

from bitfount.config import _PYTORCH_ENGINE, BITFOUNT_ENGINE
from bitfount.exceptions import BitfountEngineError

if TYPE_CHECKING:
    from bitfount.types import _TensorLike


class BackendTensorShim(ABC):
    """A shim for handling tensors of a particular type.

    An abstract class representing a shim/bridge for tensor handling in a particular
    backend.
    """

    @staticmethod
    @abstractmethod
    def to_numpy(t: Union[_TensorLike, list[float]]) -> np.ndarray:
        """Converts a tensor into a numpy array and returns it.

        Args:
            t: The tensor or list to convert.

        Returns:
            A numpy array.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_tensor(p: Any, **kwargs: Any) -> _TensorLike:
        """Converts the supplied argument to a tensor (if possible) and returns it.

        Args:
            p: The argument to convert to a tensor.
            **kwargs: Additional keyword arguments to pass to the tensor constructor.

        Returns:
            A tensor.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_list(p: Union[np.ndarray, _TensorLike]) -> list[float]:
        """Converts the supplied tensor or numpy array to a list and returns it.

        Args:
            p: The tensor or numpy array to convert to a list.

        Returns:
            A list.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def is_tensor(p: Any) -> bool:
        """Checks if the argument is a tensor.

        Args:
            p: The argument to check.

        Returns:
            True if the supplied argument is a tensor according to this model's
                backend, False otherwise.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def clamp_params(
        p: _TensorLike, prime_q: int, precision: int, num_workers: int
    ) -> _TensorLike:
        """Clamps the parameter of a given tensor.

        Constrains the parameters for secure sharing to be within the
        required range for secure sharing. Used only when
        `steps_between_parameter_updates is 1.`

        Args:
            p: The tensor to be constrained.
            prime_q: The prime use for secret aggregation.
            precision: The precision used for secret aggregation.
            num_workers: The number of workers taking part in the secure aggregation.

        Returns:
            The clamped parameters.
        """
        raise NotImplementedError


def _load_default_tensor_shim() -> BackendTensorShim:
    """Helper function for loading the BackendTensorShim.

    Currently only supports the PyTorchBackendTensorShim.
    """
    if BITFOUNT_ENGINE == _PYTORCH_ENGINE:
        try:
            from bitfount.backends.pytorch.federated.shim import (
                PyTorchBackendTensorShim,
            )

            return PyTorchBackendTensorShim()
        except ImportError as e:
            raise BitfountEngineError(
                "An error was encountered trying to load the pytorch engine; "
                "check pytorch is installed."
            ) from e
    else:
        # Raise the same error due to only supporting shim for pytorch.
        raise BitfountEngineError(
            "An error was encountered trying to load the pytorch engine; "
            "check pytorch is installed."
        )
