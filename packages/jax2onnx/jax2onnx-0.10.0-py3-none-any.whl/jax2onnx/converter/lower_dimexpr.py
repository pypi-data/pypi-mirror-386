# jax2onnx/converter/lower_dimexpr.py

from __future__ import annotations

from typing import TYPE_CHECKING

from jax._src.export.shape_poly import _DimExpr, _DimTerm, _DimFactor
from jax2onnx.plugins._ir_shapes import _ensure_value_metadata, _stamp_type_and_shape
from jax2onnx.plugins.jax.lax._index_utils import _const_i64
import onnx_ir as ir
import numpy as np

if TYPE_CHECKING:
    from jax2onnx.converter.ir_context import IRContext


class LowerDimExpr:
    def __init__(self, ctx: "IRContext"):
        self.ctx = ctx
        self.compute_cache = {}

    def _get_dim_value(self, name: str) -> ir.Value:
        if name in self.compute_cache:
            return self.compute_cache[name]

        src_val, dim_index = self.ctx.get_symbolic_dim_origin(name)
        shp = self.ctx.builder.Shape(
            src_val,
            start=dim_index,
            end=dim_index + 1,
            _outputs=[self.ctx.fresh_name("dimexpr_shape")],
        )
        _stamp_type_and_shape(shp, (1,))
        shp.type = ir.TensorType(
            ir.DataType.INT64
        )  # this is defined by ONNX specs to be INT64 for Shape
        _ensure_value_metadata(self.ctx, shp)

        self.compute_cache[name] = shp
        return shp

    def _get_scalar(self, scalar: int) -> ir.Value:
        if scalar in self.compute_cache:
            return self.compute_cache[scalar]

        val = _const_i64(
            self.ctx, np.asarray([scalar], dtype=np.int64), "dimexpr_scalar"
        )

        self.compute_cache[scalar] = val
        return val

    def _set_metadata(self, value: ir.Value) -> None:
        _stamp_type_and_shape(value, (1,))
        value.type = ir.TensorType(ir.DataType.INT64)
        _ensure_value_metadata(self.ctx, value)

    def _convert_op(self, name: str, operands: list[ir.Value]) -> ir.Value:
        if name == "floordiv":
            result = self.ctx.builder.Div(
                operands[0], operands[1], _outputs=[self.ctx.fresh_name("dimexpr_div")]
            )
        elif name == "max":
            result = self.ctx.builder.Max(
                *operands, _outputs=[self.ctx.fresh_name("dimexpr_max")]
            )
        elif name == "min":
            result = self.ctx.builder.Min(
                *operands, _outputs=[self.ctx.fresh_name("dimexpr_min")]
            )
        elif name == "mod":
            result = self.ctx.builder.Mod(
                *operands, _outputs=[self.ctx.fresh_name("dimexpr_mod")]
            )
        else:
            raise RuntimeError(f"Unhandled operation in LowerDimExpr: {name}")

        self._set_metadata(result)
        return result

    def _lower_op(self, name: str, operands: tuple) -> ir.Value:
        key = f"{name}#{operands}"
        if key in self.compute_cache:
            return self.compute_cache[key]

        operand_vals = [self._lower_expr(operand) for operand in operands]
        result_value = self._convert_op(name, operand_vals)

        self.compute_cache[key] = result_value
        return result_value

    def _lower_factor(self, factor: tuple[_DimFactor, int]) -> ir.Value:
        if str(factor) in self.compute_cache:
            return self.compute_cache[str(factor)]

        if factor[0].operation is None:
            result_value = self._get_dim_value(factor[0].var)
        else:
            result_value = self._lower_op(factor[0].operation, factor[0].operands)

        if factor[1] != 1:
            result_value = self.ctx.builder.Pow(
                result_value,
                self._get_scalar(factor[1]),
                _outputs=[self.ctx.fresh_name("dimexpr_pow")],
            )
            self._set_metadata(result_value)

        self.compute_cache[str(factor)] = result_value
        return result_value

    def _lower_term(self, term: _DimTerm) -> ir.Value:
        if str(term) in self.compute_cache:
            return self.compute_cache[str(term)]

        if len(term._factors) == 0:
            result_value = self._get_scalar(1)
        else:
            result_value = self._lower_factor(term._factors[0])

            for factor in term._factors[1:]:
                result_value = self.ctx.builder.Mul(
                    result_value,
                    self._lower_factor(factor),
                    _outputs=[self.ctx.fresh_name("dimexpr_mul")],
                )
                self._set_metadata(result_value)

        self.compute_cache[str(term)] = result_value
        return result_value

    def _lower_term_with_mult(self, term: tuple[_DimTerm, int]) -> ir.Value:
        if str(term) in self.compute_cache:
            return self.compute_cache[str(term)]

        if term[0].is_constant and str(term[0]) == "":
            result_value = self._get_scalar(term[1])
        else:
            result_value = self._lower_term(term[0])

            if term[1] != 1:
                result_value = self.ctx.builder.Mul(
                    result_value,
                    self._get_scalar(term[1]),
                    _outputs=[self.ctx.fresh_name("dimexpr_mul")],
                )
                self._set_metadata(result_value)

        self.compute_cache[str(term)] = result_value
        return result_value

    def _lower_expr(self, expr: _DimExpr | int) -> ir.Value:
        if isinstance(expr, int):
            return self._get_scalar(expr)

        if str(expr) in self.compute_cache:
            return self.compute_cache[str(expr)]

        terms = expr._sorted_terms
        result_value = self._lower_term_with_mult(terms[0])

        for term in terms[1:]:
            result_value = self.ctx.builder.Add(
                result_value,
                self._lower_term_with_mult(term),
                _outputs=[self.ctx.fresh_name("dimexpr_add")],
            )
            self._set_metadata(result_value)

        self.compute_cache[str(expr)] = result_value
        return result_value

    def __call__(self, exprs: list[_DimExpr | int]) -> ir.Value:
        values = [self._lower_expr(expr) for expr in exprs]
        if len(values) == 1:
            return values[0]
        else:
            result = self.ctx.builder.Concat(
                *values, axis=0, _outputs=[self.ctx.fresh_name("dimexpr_concat")]
            )
            self._set_metadata(result)
            return result
