# jax2onnx/plugins/jax/nn/elu.py

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Final

import jax
from jax.extend.core import Primitive

from jax2onnx.plugins._post_check_onnx_graph import expect_graph as EG
from jax2onnx.plugins._patching import AssignSpec, MonkeyPatchSpec
from jax2onnx.plugins.plugin_system import PrimitiveLeafPlugin, register_primitive
from jax2onnx.plugins.jax.nn._builder_utils import (
    lower_unary_elementwise,
    register_unary_elementwise_batch_rule,
)

if TYPE_CHECKING:  # pragma: no cover
    from jax2onnx.converter.ir_context import IRContext


_ELU_PRIM: Final[Primitive] = Primitive("jax.nn.elu")
_ELU_PRIM.multiple_results = False


@register_primitive(
    jaxpr_primitive=_ELU_PRIM.name,
    jax_doc="https://docs.jax.dev/en/latest/_autosummary/jax.nn.elu.html",
    onnx=[{"component": "Elu", "doc": "https://onnx.ai/onnx/operators/onnx__Elu.html"}],
    since="v0.7.1",
    context="primitives.nn",
    component="elu",
    testcases=[
        {
            "testcase": "jaxnn_elu",
            "callable": lambda x: jax.nn.elu(x, alpha=0.1),
            "input_shapes": [(1,)],
            "run_only_f32_variant": True,
            "post_check_onnx_graph": EG(
                ["Elu:1"],
                no_unused_inputs=True,
            ),
        },
        {
            "testcase": "jaxnn_elu_1",
            "callable": lambda x: jax.nn.elu(x, alpha=0.2),
            "input_shapes": [(2, 5)],
            "run_only_f32_variant": True,
            "post_check_onnx_graph": EG(
                ["Elu:2x5"],
                no_unused_inputs=True,
            ),
        },
        {
            "testcase": "jaxnn_elu_default",
            "callable": lambda x: jax.nn.elu(x),
            "input_shapes": [(5, 5)],
            "run_only_f32_variant": True,
            "post_check_onnx_graph": EG(
                ["Elu:5x5"],
                no_unused_inputs=True,
            ),
        },
        {
            "testcase": "jaxnn_elu_custom_alpha",
            "callable": lambda x: jax.nn.elu(x, alpha=0.2),
            "input_shapes": [("B", 4)],
            "run_only_f32_variant": True,
            "post_check_onnx_graph": EG(
                ["Elu:Bx4"],
                symbols={"B": None},
                no_unused_inputs=True,
            ),
        },
    ],
)
class EluPlugin(PrimitiveLeafPlugin):
    """Lower ``jax.nn.elu`` to ONNX ``Elu``."""

    _PRIM: ClassVar[Primitive] = _ELU_PRIM
    _ABSTRACT_EVAL_BOUND: ClassVar[bool] = False

    @staticmethod
    def abstract_eval(x, alpha: float = 1.0):
        del alpha
        return jax.core.ShapedArray(x.shape, x.dtype)

    def lower(self, ctx: "IRContext", eqn):  # type: ignore[name-defined]
        alpha = float(eqn.params.get("alpha", 1.0))

        lower_unary_elementwise(
            ctx,
            eqn,
            op_name="Elu",
            input_hint="elu_in",
            output_hint="elu_out",
            attrs={"alpha": alpha},
        )

    @classmethod
    def ensure_abstract_eval_bound(cls):
        if not cls._ABSTRACT_EVAL_BOUND:
            cls._PRIM.def_abstract_eval(cls.abstract_eval)
            cls._ABSTRACT_EVAL_BOUND = True

    @classmethod
    def binding_specs(cls):
        return [
            AssignSpec("jax.nn", "elu_p", cls._PRIM, delete_if_missing=True),
            MonkeyPatchSpec(
                target="jax.nn",
                attr="elu",
                make_value=lambda orig: (
                    lambda *args, **kwargs: cls._PRIM.bind(*args, **kwargs)
                ),
                delete_if_missing=False,
            ),
        ]


@EluPlugin._PRIM.def_impl
def _elu_impl(*args, **kwargs):
    return jax.nn.elu(*args, **kwargs)


register_unary_elementwise_batch_rule(EluPlugin._PRIM)
