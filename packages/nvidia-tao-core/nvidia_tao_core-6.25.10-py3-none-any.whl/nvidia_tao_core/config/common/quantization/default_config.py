# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
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

"""Configuration classes for quantization framework.

This module defines dataclasses for specifying quantization configuration at various levels of
granularity, including model, layer, weight, and activation. These configuration classes are used to
control quantization behavior in the TAO Toolkit.

The configuration hierarchy is as follows:

- ``ModelQuantizationConfig``: Top-level configuration that orchestrates the entire quantization process
- ``LayerQuantizationConfig``: Configuration for individual layers or groups of layers
- ``WeightQuantizationConfig``: Configuration specifically for weight quantization
- ``ActivationQuantizationConfig``: Configuration specifically for activation quantization
- ``BaseQuantizationConfig``: Base class providing common quantization parameters

Supported backends include "torchao", "modelopt", and "modelopt_onnx", with quantization modes
including "static_ptq" and "weight_only_ptq". The framework supports various data types including
"int8", "fp8_e4m3fn", "fp8_e5m2", and "native" precision.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from nvidia_tao_core.config.utils.types import (
    DICT_FIELD,
    DATACLASS_FIELD,
    INT_FIELD,
    LIST_FIELD,
    STR_FIELD,
)


@dataclass
class BaseQuantizationConfig:
    """Base configuration for quantization.

    Parameters
    ----------
    dtype : str
        Data type to use for quantization. Valid values include "int8", "fp8_e4m3fn",
        "fp8_e5m2", and "native". Defaults to an empty string.
    observer_or_fake_quant : str
        Name of the observer (PTQ) or fake quant (QAT) to use for collecting statistics (must be
        registered). Defaults to an empty string.
    quant_axis : int or None, optional
        Axis along which to apply per-channel quantization. If ``None``, per-tensor quantization is
        used. Defaults to None.
    observer_or_fake_quant_kwargs : dict or None, optional
        Additional keyword arguments to pass to the observer or fake quant constructor. Defaults to
        an empty dictionary.

    Notes
    -----
    This is the base class for all quantization configurations. It provides the common parameters
    needed for both weight and activation quantization.
    """

    dtype: str = STR_FIELD(  # type: ignore
        "",
        description="Data type to use for quantization (e.g., 'int8', 'fp8_e4m3fn', 'fp8_e5m2')",
        display_name="Quantization data type",
        required="yes",
    )
    observer_or_fake_quant: str = STR_FIELD(  # type: ignore
        "",
        description="Name of the observer (PTQ) or fake quant (QAT) to use for collecting statistics",
        display_name="Observer or fake quant",
    )
    quant_axis: Optional[int] = INT_FIELD(  # type: ignore
        None,
        description="Axis along which to apply per-channel quantization. If None, per-tensor quantization is used",
        display_name="Quantization axis",
    )
    observer_or_fake_quant_kwargs: Optional[Dict[str, Any]] = DICT_FIELD(
        {},
        description="Additional keyword arguments to pass to the observer or fake quant constructor",
        display_name="Observer kwargs",
    )


@dataclass
class WeightQuantizationConfig(BaseQuantizationConfig):
    """Configuration for weight quantization.

    Inherits all parameters from ``BaseQuantizationConfig``. This configuration is specifically for
    quantizing model weights.

    Parameters
    ----------
    dtype : str
        Data type to use for weight quantization. Valid values include "int8", "fp8_e4m3fn",
        "fp8_e5m2", and "native". Defaults to an empty string.
    observer_or_fake_quant : str
        Name of the observer (PTQ) or fake quant (QAT) to use for collecting weight statistics.
        Must be registered. Defaults to an empty string.
    quant_axis : int or None, optional
        Axis along which to apply per-channel quantization for weights. If ``None``, per-tensor
        quantization is used. Defaults to None.
    observer_or_fake_quant_kwargs : dict or None, optional
        Additional keyword arguments to pass to the weight observer or fake quant constructor.
        Defaults to an empty dictionary.

    Notes
    -----
    Weight quantization typically uses per-channel quantization (quant_axis=0 for most layers)
    to preserve accuracy while reducing model size and improving inference speed.

    See Also
    --------
    BaseQuantizationConfig
        Base class for quantization configurations.
    ActivationQuantizationConfig
        Configuration for activation quantization.
    """
    # No additional parameters for now; all inherited from BaseQuantizationConfig.


@dataclass
class ActivationQuantizationConfig(BaseQuantizationConfig):
    """Configuration for activation quantization.

    Inherits all parameters from ``BaseQuantizationConfig``. This configuration is specifically for
    quantizing model activations.

    Parameters
    ----------
    dtype : str
        Data type to use for activation quantization. Valid values include "int8", "fp8_e4m3fn",
        "fp8_e5m2", and "native". Defaults to an empty string.
    observer_or_fake_quant : str
        Name of the observer (PTQ) or fake quant (QAT) to use for collecting activation statistics.
        Must be registered. Defaults to an empty string.
    quant_axis : int or None, optional
        Axis along which to apply per-channel quantization for activations. If ``None``, per-tensor
        quantization is used. Defaults to None.
    observer_or_fake_quant_kwargs : dict or None, optional
        Additional keyword arguments to pass to the activation observer or fake quant constructor.
        Defaults to an empty dictionary.

    Notes
    -----
    Activation quantization typically uses per-tensor quantization (quant_axis=None) as activations
    are more sensitive to quantization errors and per-channel quantization may not provide
    significant benefits.

    See Also
    --------
    BaseQuantizationConfig
        Base class for quantization configurations.
    WeightQuantizationConfig
        Configuration for weight quantization.
    """
    # No additional parameters for now; all inherited from BaseQuantizationConfig.


@dataclass
class LayerQuantizationConfig:
    """Configuration for quantizing a single module or set of modules.

    Parameters
    ----------
    module_name : str
        Name or pattern specifying the module(s) to quantize. Can be:

        - Exact module name (e.g., "layers.0.conv1")
        - Layer type (e.g., "Linear", "Conv2d")
        - Wildcard pattern (e.g., "conv*", "*.linear")

        The pattern matching is case-sensitive and uses Python's ``fnmatch.fnmatch``.
    weights : WeightQuantizationConfig or None, optional
        Weight quantization configuration. If ``None``, weights are not quantized and left in the
        original precision. Defaults to None.
    activations : ActivationQuantizationConfig or None, optional
        Activation quantization configuration. If ``None``, activations are not quantized and left in
        the original precision. Defaults to None.

    Notes
    -----
    This configuration allows fine-grained control over quantization at the layer level. You can
    specify different quantization strategies for weights and activations of the same layer.

    When both weights and activations are None, the layer will not be quantized and will retain
    its original precision. This is useful for excluding specific layers from quantization.

    The module_name pattern matching is applied first to the module's qualified graph name,
    then to the module's class name if no match is found.

    Examples
    --------
    Quantize all convolutional layers with int8 weights and activations::

        LayerQuantizationConfig(
            module_name="Conv*",
            weights=WeightQuantizationConfig(dtype="int8", observer_or_fake_quant="minmax"),
            activations=ActivationQuantizationConfig(dtype="int8", observer_or_fake_quant="minmax")
        )

    Quantize only weights of linear layers::

        LayerQuantizationConfig(
            module_name="Linear",
            weights=WeightQuantizationConfig(dtype="fp8_e4m3fn", observer_or_fake_quant="entropy")
        )

    Exclude a specific layer from quantization::

        LayerQuantizationConfig(
            module_name="final_layer",
            weights=None,
            activations=None
        )
    """

    module_name: str = STR_FIELD(  # type: ignore
        "",
        description="Name or pattern specifying the module(s) to quantize",
        display_name="Module name",
        required="yes",
    )
    weights: Optional[WeightQuantizationConfig] = DATACLASS_FIELD(
        None,
        description="Weight quantization configuration. If None, weights are not quantized",
        display_name="Weight quantization",
    )
    activations: Optional[ActivationQuantizationConfig] = DATACLASS_FIELD(
        None,
        description="Activation quantization configuration. If None, activations are not quantized",
        display_name="Activation quantization",
    )


@dataclass
class ModelQuantizationConfig:
    """Top-level configuration for model quantization.

    Parameters
    ----------
    backend : str or None, optional
        The quantization backend to use. Valid options are "modelopt", "torchao", and "modelopt_onnx".
        Defaults to "torchao".
    mode : str or None, optional
        The quantization mode to use. Valid options are "static_ptq" and "weight_only_ptq".
        Defaults to "weight_only_ptq".
    algorithm : str or None, optional
        Calibration/optimisation algorithm name for the backend configuration.
        Valid options are "minmax" and "entropy". When using the ``modelopt`` backend, this value
        is propagated to the top-level ``"algorithm"`` field of the ModelOpt config.
        Defaults to "minmax".
    default_layer_dtype : str, optional
        Default data type for layers. Valid options are "int8", "fp8_e4m3fn", "fp8_e5m2", and "native".
        Defaults to "native".
    default_activation_dtype : str, optional
        Default data type for activations. Valid options are "int8", "fp8_e4m3fn", "fp8_e5m2", and "native".
        Defaults to "native".
    layers : list of LayerQuantizationConfig, optional
        List of per-module quantization configurations. Each entry specifies how a particular module
        or set of modules should be quantized. Defaults to an empty list. If empty, no specific layer
        quantization is applied.
    skip_names : list of str, optional
        List of module names or patterns to exclude from quantization. Each entry can be:

        - An exact module name (e.g., "layers.0.conv1")
        - A layer type (e.g., "Linear", "Conv2d")
        - A wildcard pattern (e.g., "conv*", "*.linear")

        Any module whose name matches any pattern in this list will be excluded from quantization.
        Defaults to an empty list. If empty, no modules are excluded.
    model_path : str, optional
        Path to the model to be quantized. Defaults to an empty string.
    results_dir : str, optional
        Path to where all the assets generated from a quantization task are stored. Defaults to an
        empty string.

    Notes
    -----
    This is the main configuration class that orchestrates the entire quantization process. It
    combines global settings with layer-specific configurations to provide a comprehensive
    quantization strategy.

    Pattern syntax
    --------------
    The ``module_name`` and ``skip_names`` fields accept wildcard patterns interpreted using
    Python's ``fnmatch.fnmatch``. Wildcards ``*`` and ``?`` are supported and matching is
    case-sensitive. A pattern is first applied to the module's qualified graph name (e.g.,
    ``backbone.layer1.0.conv1``). If that does not match, the module's class name (e.g., ``Conv2d``)
    is checked. See ``nvidia_tao_pytorch.core.quantization.utils.match_layer`` for implementation
    details.

    Examples
    --------
    Basic weight-only PTQ configuration::

        config = ModelQuantizationConfig(
            backend="torchao",
            mode="weight_only_ptq",
            algorithm="minmax",
            default_layer_dtype="int8",
            default_activation_dtype="native",
            layers=[
                LayerQuantizationConfig(
                    module_name="conv*",
                    weights=WeightQuantizationConfig(
                        dtype="int8",
                        observer_or_fake_quant="my_observer"
                    )
                )
            ],
            skip_names=["final_layer"]
        )

    Static PTQ configuration with mixed precision::

        config = ModelQuantizationConfig(
            backend="modelopt",
            mode="static_ptq",
            algorithm="entropy",
            default_layer_dtype="fp8_e4m3fn",
            default_activation_dtype="fp8_e4m3fn",
            layers=[
                LayerQuantizationConfig(
                    module_name="Linear",
                    weights=WeightQuantizationConfig(
                        dtype="fp8_e4m3fn",
                        observer_or_fake_quant="my_observer"
                    ),
                    activations=ActivationQuantizationConfig(
                        dtype="fp8_e4m3fn",
                        observer_or_fake_quant="my_observer"
                    )
                )
            ]
        )

    See Also
    --------
    LayerQuantizationConfig
        Configuration for individual layer quantization.
    WeightQuantizationConfig
        Configuration for weight quantization.
    ActivationQuantizationConfig
        Configuration for activation quantization.
    """

    backend: Optional[str] = STR_FIELD(  # type: ignore
        "torchao",
        valid_options="modelopt,torchao,modelopt_onnx",
        description="The quantization backend to use",
        display_name="Quantization backend",
    )
    mode: Optional[str] = STR_FIELD(
        "weight_only_ptq",
        valid_options="static_ptq,weight_only_ptq",
        description="The quantization mode to use",
        display_name="Quantization mode",
    )
    algorithm: Optional[str] = STR_FIELD(  # type: ignore
        "minmax",
        valid_options="minmax,entropy",
        description=(
            "Calibration/optimisation algorithm name to pass to the backend configuration. "
            "For the 'modelopt' backend, this becomes the top-level 'algorithm' field."
        ),
        display_name="Calibration/optimisation algorithm",
    )
    default_layer_dtype: str = STR_FIELD(
        "native",
        valid_options="int8,fp8_e4m3fn,fp8_e5m2,native",
        description="Default data type for layers",
        display_name="Default layer dtype",
        required="yes",
    )
    default_activation_dtype: str = STR_FIELD(
        "native",
        valid_options="int8,fp8_e4m3fn,fp8_e5m2,native",
        description="Default data type for activations",
        display_name="Default activation dtype",
        required="yes",
    )
    layers: Optional[List[LayerQuantizationConfig]] = LIST_FIELD(
        [],
        description="List of per-module quantization configurations",
        display_name="Layer quantization configs",
    )
    skip_names: Optional[List[str]] = LIST_FIELD(
        [],
        description="List of module/layer names or patterns to exclude from quantization",
        display_name="Skip names",
    )
    model_path: Optional[str] = STR_FIELD(
        "",
        display_name="Model path",
        description="Path to the model to be quantized.",
        required="yes",
    )
    results_dir: Optional[str] = STR_FIELD(
        "",
        display_name="Results directory",
        description="Path to where all the assets generated from a task are stored.",
        required="yes",
    )
