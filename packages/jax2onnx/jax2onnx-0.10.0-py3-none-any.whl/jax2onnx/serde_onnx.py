# jax2onnx/serde_onnx.py

from __future__ import annotations


import onnx
import onnx_ir as ir
import tempfile
import os


def ir_to_onnx(ir_model: ir.Model) -> onnx.ModelProto:
    """
    Convert an onnx-ir Model to an ONNX ModelProto by saving to a temp file.
    This module is the only place where 'onnx' is imported for converter.
    """
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
            tmp = f.name
        ir.save(ir_model, tmp)
        model = onnx.load_model(tmp)
        return model
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
