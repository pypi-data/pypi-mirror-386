# jax2onnx/plugins/jax/lax/exp.py

from typing import TYPE_CHECKING

import jax

from jax2onnx.plugins._post_check_onnx_graph import expect_graph as EG
from jax2onnx.plugins.plugin_system import PrimitiveLeafPlugin, register_primitive

if TYPE_CHECKING:
    pass


@register_primitive(
    jaxpr_primitive=jax.lax.exp_p.name,
    jax_doc="https://docs.jax.dev/en/latest/_autosummary/jax.lax.exp.html",
    onnx=[
        {
            "component": "Exp",
            "doc": "https://onnx.ai/onnx/operators/onnx__Exp.html",
        }
    ],
    since="v0.2.0",
    context="primitives.lax",
    component="exp",
    testcases=[
        {
            "testcase": "exp",
            "callable": lambda x: jax.lax.exp(x),
            "input_shapes": [(3,)],
            "post_check_onnx_graph": EG(
                ["Exp:3"],
                no_unused_inputs=True,
            ),
        }
    ],
)
class ExpPlugin(PrimitiveLeafPlugin):
    def lower(self, ctx, eqn):
        x_var = eqn.invars[0]
        out_var = eqn.outvars[0]

        x_val = ctx.get_value_for_var(x_var, name_hint=ctx.fresh_name("exp_in"))
        out_spec = ctx.get_value_for_var(out_var, name_hint=ctx.fresh_name("exp_out"))

        desired_name = getattr(out_spec, "name", None) or ctx.fresh_name("exp_out")
        producer = getattr(out_spec, "producer", lambda: None)
        if callable(producer) and producer() is not None:
            desired_name = ctx.fresh_name("exp_out")

        result = ctx.builder.Exp(x_val, _outputs=[desired_name])
        if getattr(out_spec, "type", None) is not None:
            result.type = out_spec.type
        if getattr(out_spec, "shape", None) is not None:
            result.shape = out_spec.shape
        ctx.bind_value_for_var(out_var, result)
