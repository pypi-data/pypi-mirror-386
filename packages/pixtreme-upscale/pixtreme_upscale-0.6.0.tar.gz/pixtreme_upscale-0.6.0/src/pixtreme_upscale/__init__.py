"""pixtreme-upscale: Multi-backend deep learning upscalers"""

__version__ = "0.6.0"

from .onnx_upscaler import OnnxUpscaler
from .torch_upscaler import TorchUpscaler
from .trt_upscaler import TrtUpscaler

__all__ = [
    "OnnxUpscaler",
    "TorchUpscaler",
    "TrtUpscaler",
]
