import cupy as cp
import onnxruntime


class OnnxUpscaler:
    """ONNX-based image upscaler with CUDA and CPU provider support.

    This class provides optimized inference for ONNX upscaling models with automatic
    fallback handling for type inconsistencies and efficient memory management.
    """

    def __init__(
        self,
        model_path: str | None = None,
        model_bytes: bytes | None = None,
        device_id: int = 0,
        provider_options: list | None = None,
    ) -> None:
        """Initialize the ONNX upscaler.

        Args:
            model_path: Path to the ONNX model file. Either this or model_bytes must be provided.
            model_bytes: Raw bytes of the ONNX model. Either this or model_path must be provided.
            device_id: CUDA device ID to use for inference.
            provider_options: Custom provider options for ONNX Runtime.

        Raises:
            ValueError: If neither model_path nor model_bytes is provided.
            RuntimeError: If ONNX model cannot be loaded due to type inconsistencies.
        """
        # Setting device and provider options
        self.device_id = device_id
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if provider_options is None:
            self.provider_options = [{"device_id": str(device_id)}, {}]
        else:
            self.provider_options = provider_options

        # Create ONNX Runtime session options
        sess_options = onnxruntime.SessionOptions()
        sess_options.log_severity_level = 4
        sess_options.enable_mem_pattern = True
        sess_options.enable_cpu_mem_arena = True
        sess_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Configuration to handle type mismatch errors
        sess_options.add_session_config_entry("session.disable_prepacking", "1")

        # Load model from bytes or file
        if model_bytes is None:
            if model_path is None:
                raise ValueError("model_path or model_bytes is required")
            with open(model_path, "rb") as f:
                model_bytes = f.read()

        # Type error handling during model loading
        try:
            self.session = onnxruntime.InferenceSession(
                model_bytes,
                sess_options=sess_options,
                providers=providers,
                provider_options=self.provider_options,
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "type error" in error_msg and ("layernormalization" in error_msg or "bound to different types" in error_msg):
                print(f"⚠️ Type inconsistency detected in ONNX model: {e}")
                print("🔧 Attempting to fix with CPU provider and relaxed settings...")

                # Retry with CPU provider
                cpu_providers = ["CPUExecutionProvider"]
                cpu_provider_options = [{}]

                # More tolerant settings
                relaxed_sess_options = onnxruntime.SessionOptions()
                relaxed_sess_options.log_severity_level = 4
                relaxed_sess_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_DISABLE_ALL
                relaxed_sess_options.add_session_config_entry("session.disable_prepacking", "1")

                try:
                    self.session = onnxruntime.InferenceSession(
                        model_bytes,
                        sess_options=relaxed_sess_options,
                        providers=cpu_providers,
                        provider_options=cpu_provider_options,
                    )
                    print("✅ Successfully loaded model with CPU provider")
                    # Update provider information
                    self.providers = cpu_providers
                    self.provider_options = cpu_provider_options
                except Exception as retry_e:
                    print(f"❌ CPU provider also failed: {retry_e}")
                    print("💡 Suggestions:")
                    print("   1. Re-export ONNX model with consistent precision (all fp32 or all fp16)")
                    print("   2. Use PyTorch inference instead")
                    print("   3. Try ONNX simplifier: python -m onnxsim model.onnx model_simplified.onnx")
                    raise RuntimeError(f"ONNX model type inconsistency cannot be resolved. Original error: {e}")
            else:
                raise

        # Get input and output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        # Initialize IO binding
        self.io = self.session.io_binding()

        # Data type mapping
        self.dtype_map = {
            "tensor(float)": cp.float32,
            "tensor(float16)": cp.float16,
            "tensor(double)": cp.float64,
            "tensor(int32)": cp.int32,
            "tensor(int64)": cp.int64,
            "tensor(uint8)": cp.uint8,
        }

        # Buffer pool
        self.input_buffer = None
        self.output_buffer = None
        self.last_input_shape = None
        self.binding_configured = False

    def _ensure_buffers(self, input_shape):
        """Ensure necessary buffers are allocated for the given input shape.

        Args:
            input_shape: Shape of the input image as (height, width, channels).
        """
        channels = 3 if input_shape[-1] >= 3 else input_shape[-1]
        processed_shape = (1, channels, input_shape[0], input_shape[1])

        if self.input_buffer is None or self.input_buffer.shape != processed_shape:
            # Process with single buffer (removed temp_buffer)
            self.input_buffer = cp.empty(processed_shape, dtype=cp.float32)
            self.binding_configured = False

    def pre_process(self, input_frame: cp.ndarray) -> cp.ndarray:
        """Preprocess input frame for ONNX inference.

        Converts BGR to RGB, handles different channel configurations,
        and transforms from HWC to NCHW format.

        Args:
            input_frame: Input image array in HWC format.

        Returns:
            Preprocessed image array in NCHW format ready for inference.
        """
        self._ensure_buffers(input_frame.shape)

        assert self.input_buffer is not None, "Input buffer must be initialized before preprocessing."

        # Check the most common case (RGB) first
        if input_frame.shape[-1] == 3:
            # Process BGR → RGB + HWC → NCHW at once
            self.input_buffer[0, 0] = input_frame[:, :, 2]  # B → R
            self.input_buffer[0, 1] = input_frame[:, :, 1]  # G → G
            self.input_buffer[0, 2] = input_frame[:, :, 0]  # R → B
        elif input_frame.shape[-1] == 4:
            # RGBA → RGB + BGR → RGB + HWC → NCHW
            self.input_buffer[0, 0] = input_frame[:, :, 2]  # B → R
            self.input_buffer[0, 1] = input_frame[:, :, 1]  # G → G
            self.input_buffer[0, 2] = input_frame[:, :, 0]  # R → B
        elif input_frame.ndim == 2:
            # Grayscale → RGB
            self.input_buffer[0, 0] = input_frame
            self.input_buffer[0, 1] = input_frame
            self.input_buffer[0, 2] = input_frame

        return self.input_buffer

    def post_process(self, output_frame: cp.ndarray) -> cp.ndarray:
        """Post-process ONNX inference output.

        Converts from NCHW to HWC format and RGB back to BGR.

        Args:
            output_frame: Model output in NCHW format.

        Returns:
            Post-processed image array in HWC BGR format.
        """
        if self.output_buffer is None or self.output_buffer.shape != output_frame[0].shape:
            # Pre-allocate output buffer
            self.output_buffer = cp.empty(
                (output_frame.shape[2], output_frame.shape[3], output_frame.shape[1]), dtype=output_frame.dtype
            )

        # NCHW → HWC + RGB → BGR (in-place)
        self.output_buffer[:, :, 0] = output_frame[0, 2]  # R → B
        self.output_buffer[:, :, 1] = output_frame[0, 1]  # G → G
        self.output_buffer[:, :, 2] = output_frame[0, 0]  # B → R

        return self.output_buffer

    def get(self, image: cp.ndarray) -> cp.ndarray:
        """Internal method to perform upscaling on a single image.

        Args:
            image: Single image array to upscale.

        Returns:
            Upscaled image array.
        """
        input_frame = self.pre_process(image)

        # Set binding only if not configured or shape has changed
        if not self.binding_configured or self.last_input_shape != input_frame.shape:
            self.io.clear_binding_inputs()
            self.io.clear_binding_outputs()

            self.io.bind_input(
                name=self.input_name,
                device_type="cuda",
                device_id=self.device_id,
                element_type=input_frame.dtype,
                shape=input_frame.shape,
                buffer_ptr=input_frame.data.ptr,
            )

            self.io.bind_output(
                name=self.output_name,
                device_type="cuda",
                device_id=self.device_id,
            )

            self.last_input_shape = input_frame.shape
            self.binding_configured = True

        # Execute inference
        self.session.run_with_iobinding(self.io)

        # Get output (zero-copy)
        output_ortvalue = self.io.get_outputs()[0]
        shape = output_ortvalue.shape()
        dtype = output_ortvalue.data_type()
        gpu_ptr = output_ortvalue.data_ptr()

        cupy_dtype = self.dtype_map.get(dtype, cp.float32)
        output_array = cp.ndarray(
            shape=shape, dtype=cupy_dtype, memptr=cp.cuda.MemoryPointer(cp.cuda.UnownedMemory(gpu_ptr, 0, None), 0)
        )

        return self.post_process(output_array)
