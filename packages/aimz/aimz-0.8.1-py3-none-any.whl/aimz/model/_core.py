# Copyright 2025 Eli Lilly and Company
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base class for impact model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

from aimz.utils._validation import _validate_kernel_signature

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseModel(ABC):
    """Abstract base class for the impact model.

    Attributes:
        kernel (Callable): A probabilistic model with NumPyro primitives.
    """

    def __init__(
        self,
        kernel: Callable,
        param_input: str = "X",
        param_output: str = "y",
    ) -> None:
        """Initialize the BaseModel with a callable model.

        Args:
            kernel: A probabilistic model with NumPyro primitives.
            param_input: Name of the parameter in the ``kernel`` for the main input
                data.
            param_output: Name of the parameter in the ``kernel`` for the output data.
        """
        self._kernel = kernel
        self._param_input = param_input
        self._param_output = param_output
        _validate_kernel_signature(self._kernel, self._param_input, self._param_output)

    @abstractmethod
    def fit(self, X, y, **kwargs) -> Self:
        """Fit the model to the input data ``X`` and output data ``y``."""
        return self

    @abstractmethod
    def predict(self, X, **kwargs) -> object:
        """Predict the output based on the fitted model."""
