"""
Direct memory conversion functions for OpenHCS.

This module provides direct conversion functions between different memory types,
enforcing Clause 65 (Fail Loudly), Clause 88 (No Inferred Capabilities),
and Clause 251 (Declarative Memory Conversion).
"""

from typing import Any, Optional

from openhcs.constants.constants import MemoryType

from .exceptions import MemoryConversionError
from .utils import (_ensure_module, _supports_cuda_array_interface,
                    _supports_dlpack)

# NumPy conversion functions

def _numpy_to_numpy(data: Any) -> Any:
    """Convert numpy array to numpy array (identity operation)."""
    return data.copy()


def _numpy_to_cupy(data: Any, gpu_id: int) -> Any:
    """
    Convert numpy array to cupy array.

    Args:
        data: The numpy array to convert
        gpu_id: The target GPU device ID

    Returns:
        The converted cupy array

    Raises:
        ImportError: If cupy is not installed
        ValueError: If gpu_id is negative
    """
    cupy = _ensure_module("cupy")

    # Validate gpu_id
    if gpu_id < 0:
        raise ValueError(f"Invalid GPU ID: {gpu_id}. Must be a non-negative integer.")

    # Always use the specified GPU device
    with cupy.cuda.Device(gpu_id):
        return cupy.array(data)


def _numpy_to_torch(data: Any, gpu_id: int) -> Any:
    """
    Convert numpy array to torch tensor.

    Args:
        data: The numpy array to convert
        gpu_id: The target GPU device ID

    Returns:
        The converted torch tensor

    Raises:
        ImportError: If torch is not installed
        ValueError: If gpu_id is negative
    """
    torch = _ensure_module("torch")

    # Validate gpu_id
    if gpu_id is None:
        raise ValueError("🔥 GPU ID IS NONE! The compiler failed to assign a GPU to this torch function. This is a GPU registry/compiler bug!")
    if gpu_id < 0:
        raise ValueError(f"Invalid GPU ID: {gpu_id}. Must be a non-negative integer.")

    # Always use the specified GPU device
    device = torch.device(f"cuda:{gpu_id}")
    return torch.tensor(data, device=device)


def _numpy_to_pyclesperanto(data: Any, gpu_id: int) -> Any:
    """
    Convert numpy array to pyclesperanto array.

    Args:
        data: The numpy array to convert
        gpu_id: The target GPU device ID

    Returns:
        The converted pyclesperanto array

    Raises:
        ImportError: If pyclesperanto is not installed
        ValueError: If gpu_id is negative
    """
    cle = _ensure_module("pyclesperanto")

    # Validate gpu_id
    if gpu_id < 0:
        raise ValueError(f"Invalid GPU ID: {gpu_id}. Must be a non-negative integer.")

    # Select the appropriate device
    devices = cle.list_available_devices()
    if gpu_id >= len(devices):
        raise ValueError(f"GPU ID {gpu_id} not available. Available devices: {len(devices)}")

    # Select device and push data
    cle.select_device(gpu_id)
    return cle.push(data)


def _numpy_to_tensorflow(data: Any, gpu_id: int) -> Any:
    """
    Convert numpy array to tensorflow tensor.

    Args:
        data: The numpy array to convert
        gpu_id: The target GPU device ID

    Returns:
        The converted tensorflow tensor

    Raises:
        ImportError: If tensorflow is not installed
        ValueError: If gpu_id is negative
    """
    tf = _ensure_module("tensorflow")

    # Validate gpu_id
    if gpu_id is None:
        raise ValueError("🔥 GPU ID IS NONE! The compiler failed to assign a GPU to this tensorflow function. This is a GPU registry/compiler bug!")
    if gpu_id < 0:
        raise ValueError(f"Invalid GPU ID: {gpu_id}. Must be a non-negative integer.")

    # Always use the specified GPU device
    with tf.device(f"/device:GPU:{gpu_id}"):
        return tf.convert_to_tensor(data)


# pyclesperanto conversion functions

def _pyclesperanto_to_numpy(data: Any) -> Any:
    """
    Convert pyclesperanto array to numpy array.

    Args:
        data: The pyclesperanto array to convert

    Returns:
        The converted numpy array
    """
    cle = _ensure_module("pyclesperanto")
    return cle.pull(data)


def _pyclesperanto_to_pyclesperanto(data: Any) -> Any:
    """Convert pyclesperanto array to pyclesperanto array (identity operation)."""
    cle = _ensure_module("pyclesperanto")
    return data


def _pyclesperanto_to_torch(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert pyclesperanto array to torch tensor, staying on GPU.

    Args:
        data: The pyclesperanto array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted torch tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If torch is not installed
    """
    torch = _ensure_module("torch")
    cle = _ensure_module("pyclesperanto")

    # Try GPU-to-GPU conversion first
    try:
        # Use CUDA array interface for zero-copy conversion
        if _supports_cuda_array_interface(data):
            # Convert via CUDA array interface
            tensor = torch.as_tensor(data, device=f"cuda:{device_id if device_id is not None else 0}")

            # Move to specified device if needed
            if device_id is not None and tensor.device.index != device_id:
                tensor = tensor.to(f"cuda:{device_id}")

            return tensor
    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.PYCLESPERANTO.value,
                target_type=MemoryType.TORCH.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

    # Fallback: CPU roundtrip
    numpy_data = cle.pull(data)
    if device_id is not None:
        return torch.tensor(numpy_data, device=f"cuda:{device_id}")
    return torch.tensor(numpy_data)


def _pyclesperanto_to_tensorflow(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert pyclesperanto array to tensorflow tensor, staying on GPU.

    Args:
        data: The pyclesperanto array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted tensorflow tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If tensorflow is not installed
    """
    tf = _ensure_module("tensorflow")
    cle = _ensure_module("pyclesperanto")

    # Try GPU-to-GPU conversion first
    try:
        # Use CUDA array interface for zero-copy conversion
        if _supports_cuda_array_interface(data):
            # Convert via CUDA array interface
            with tf.device(f"/device:GPU:{device_id if device_id is not None else 0}"):
                return tf.experimental.dlpack.from_dlpack(data.__dlpack__())
    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.PYCLESPERANTO.value,
                target_type=MemoryType.TENSORFLOW.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

    # Fallback: CPU roundtrip
    numpy_data = cle.pull(data)
    if device_id is not None:
        with tf.device(f"/device:GPU:{device_id}"):
            return tf.convert_to_tensor(numpy_data)
    return tf.convert_to_tensor(numpy_data)


def _pyclesperanto_to_jax(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert pyclesperanto array to JAX array, staying on GPU.

    Args:
        data: The pyclesperanto array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted JAX array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If jax is not installed
    """
    jax = _ensure_module("jax")
    cle = _ensure_module("pyclesperanto")

    # Try GPU-to-GPU conversion first
    try:
        # Use DLPack for zero-copy conversion
        if hasattr(data, '__dlpack__'):
            dlpack = data.__dlpack__()
            result = jax.dlpack.from_dlpack(dlpack)

            # Move to specified device if needed
            if device_id is not None:
                result = jax.device_put(result, jax.devices("gpu")[device_id])

            return result
    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.PYCLESPERANTO.value,
                target_type=MemoryType.JAX.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

    # Fallback: CPU roundtrip
    numpy_data = cle.pull(data)
    result = jax.numpy.array(numpy_data)

    if device_id is not None:
        result = jax.device_put(result, jax.devices("gpu")[device_id])

    return result


# CuPy conversion functions

def _cupy_to_numpy(data: Any) -> Any:
    """
    Convert cupy array to numpy array.

    Args:
        data: The cupy array to convert

    Returns:
        The converted numpy array
    """
    return data.get()


def _cupy_to_cupy(data: Any) -> Any:
    """Convert cupy array to cupy array (identity operation)."""
    return data.copy()


def _cupy_to_torch(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert cupy array to torch tensor, staying on GPU.

    Args:
        data: The cupy array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted torch tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If torch is not installed
    """
    torch = _ensure_module("torch")

    # Use DLPack for zero-copy GPU-to-GPU conversion
    if _supports_dlpack(data):
        try:
            dlpack = data.toDlpack()
            result = torch.from_dlpack(dlpack)

            # Move to specified device if needed
            if device_id is not None:
                target_device = f"cuda:{device_id}"
                if str(result.device) != target_device:
                    result = result.to(target_device)

            return result
        except Exception as e:
            if not allow_cpu_roundtrip:
                raise MemoryConversionError(
                    source_type=MemoryType.CUPY.value,
                    target_type=MemoryType.TORCH.value,
                    method="DLPack",
                    reason=str(e)
                ) from e

    # Fallback to CUDA Array Interface
    elif _supports_cuda_array_interface(data):
        print(f"🔥 CONVERSION DEBUG: CUDA Array Interface supported, data shape: {data.shape}")
        try:
            print("🔥 CONVERSION DEBUG: About to call torch.as_tensor...")
            if device_id is not None:
                result = torch.as_tensor(data, device=f"cuda:{device_id}")
            else:
                result = torch.as_tensor(data, device="cuda")
            print("🔥 CONVERSION DEBUG: torch.as_tensor completed successfully")
            return result
        except Exception as e:
            print(f"🔥 CONVERSION DEBUG: torch.as_tensor failed with error: {e}")
            if not allow_cpu_roundtrip:
                raise MemoryConversionError(
                    source_type=MemoryType.CUPY.value,
                    target_type=MemoryType.TORCH.value,
                    method="CUDA Array Interface",
                    reason=str(e)
                ) from e
    else:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.CUPY.value,
                target_type=MemoryType.TORCH.value,
                method="CUDA Array Interface",
                reason="CuPy array does not support CUDA Array Interface"
            )

    # Only reach here if allow_cpu_roundtrip=True
    tensor = torch.from_numpy(data.get())

    # Move to specified device if needed
    if device_id is not None:
        tensor = tensor.to(f"cuda:{device_id}")

    return tensor


def _cupy_to_tensorflow(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert cupy array to tensorflow tensor, staying on GPU.

    Args:
        data: The cupy array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted tensorflow tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If tensorflow is not installed
        RuntimeError: If TensorFlow version is < 2.12 (unstable DLPack support)
    """
    tf = _ensure_module("tensorflow")

    # Try using DLPack if supported
    # _supports_dlpack will raise RuntimeError if TF version < 2.12 or tensor is on CPU
    # This enforces Clause 88 (No Inferred Capabilities)
    if _supports_dlpack(data):
        try:
            dlpack = data.toDlpack()
            tensor = tf.experimental.dlpack.from_dlpack(dlpack)

            # Move to specified device if needed
            if device_id is not None:
                with tf.device(f"/device:GPU:{device_id}"):
                    return tf.identity(tensor)

            return tensor
        except Exception as e:
            if not allow_cpu_roundtrip:
                raise MemoryConversionError(
                    source_type=MemoryType.CUPY.value,
                    target_type=MemoryType.TENSORFLOW.value,
                    method="DLPack",
                    reason=str(e)
                ) from e
    elif not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.CUPY.value,
            target_type=MemoryType.TENSORFLOW.value,
            method="DLPack",
            reason="DLPack conversion not supported"
        )

    # Only reach here if allow_cpu_roundtrip=True
    if device_id is not None:
        with tf.device(f"/device:GPU:{device_id}"):
            return tf.convert_to_tensor(data.get())

    return tf.convert_to_tensor(data.get())


def _cupy_to_pyclesperanto(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert cupy array to pyclesperanto array, staying on GPU.

    Args:
        data: The cupy array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted pyclesperanto array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If pyclesperanto is not installed
    """
    cle = _ensure_module("pyclesperanto")

    # Try direct GPU conversion first
    try:
        # Get current CuPy device
        current_device = data.device.id

        # Select appropriate pyclesperanto device
        if device_id is not None:
            target_device = device_id
        else:
            target_device = current_device

        devices = cle.list_available_devices()
        if target_device >= len(devices):
            if not allow_cpu_roundtrip:
                raise MemoryConversionError(
                    source_type=MemoryType.CUPY.value,
                    target_type=MemoryType.PYCLESPERANTO.value,
                    method="device_selection",
                    reason=f"GPU ID {target_device} not available in pyclesperanto"
                )
        else:
            cle.select_device(target_device)

        # Convert via numpy (pyclesperanto doesn't have direct CuPy interop)
        numpy_data = data.get()  # CuPy to NumPy
        return cle.push(numpy_data)  # NumPy to pyclesperanto

    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.CUPY.value,
                target_type=MemoryType.PYCLESPERANTO.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

        # Fallback: CPU roundtrip
        numpy_data = data.get()
        cle.select_device(device_id if device_id is not None else 0)
        return cle.push(numpy_data)


def _pyclesperanto_to_cupy(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert pyclesperanto array to cupy array, staying on GPU.

    Args:
        data: The pyclesperanto array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted cupy array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If cupy is not installed
    """
    cupy = _ensure_module("cupy")
    cle = _ensure_module("pyclesperanto")

    try:
        # Convert via numpy (pyclesperanto doesn't have direct CuPy interop)
        numpy_data = cle.pull(data)  # pyclesperanto to NumPy

        # Convert to CuPy on specified device
        if device_id is not None:
            with cupy.cuda.Device(device_id):
                return cupy.array(numpy_data)
        else:
            return cupy.array(numpy_data)

    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.PYCLESPERANTO.value,
                target_type=MemoryType.CUPY.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

        # Fallback: CPU roundtrip (same as above)
        numpy_data = cle.pull(data)
        if device_id is not None:
            with cupy.cuda.Device(device_id):
                return cupy.array(numpy_data)
        else:
            return cupy.array(numpy_data)


def _cupy_to_jax(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert cupy array to JAX array, staying on GPU with zero-copy DLPack transfer.

    Args:
        data: The cupy array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip (ignored, always False)
        device_id: The target GPU device ID (optional)

    Returns:
        The converted JAX array

    Raises:
        MemoryConversionError: If conversion fails
        ImportError: If JAX is not installed
    """
    jax = _ensure_module("jax")

    # Check if CuPy array is on GPU (should always be true for CuPy)
    if not hasattr(data, 'device'):
        raise MemoryConversionError(
            source_type=MemoryType.CUPY.value,
            target_type=MemoryType.JAX.value,
            method="device_detection",
            reason="CuPy array does not have a device attribute"
        )

    # Try using DLPack for direct GPU-to-GPU transfer
    if _supports_dlpack(data):
        try:
            dlpack = data.toDlpack()
            result = jax.dlpack.from_dlpack(dlpack)

            # Move to specified device if needed
            if device_id is not None:
                current_device = None
                try:
                    # Extract device ID from JAX array
                    device_str = str(result.device)
                    if "gpu:" in device_str:
                        current_device = int(device_str.split("gpu:")[-1].split(")")[0])
                except Exception:
                    pass

                # Only move if needed
                if current_device != device_id:
                    result = jax.device_put(result, jax.devices("gpu")[device_id])

            return result
        except Exception as e:
            # No CPU roundtrip allowed, so fail loudly
            raise MemoryConversionError(
                source_type=MemoryType.CUPY.value,
                target_type=MemoryType.JAX.value,
                method="DLPack",
                reason=str(e)
            ) from e
    else:
        # No CPU roundtrip allowed, so fail loudly
        raise MemoryConversionError(
            source_type=MemoryType.CUPY.value,
            target_type=MemoryType.JAX.value,
            method="DLPack",
            reason="CuPy array does not support DLPack"
        )


# PyTorch conversion functions

def _torch_to_numpy(data: Any) -> Any:
    """
    Convert torch tensor to numpy array.

    Args:
        data: The torch tensor to convert

    Returns:
        The converted numpy array
    """
    return data.detach().cpu().numpy()


def _torch_to_cupy(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert torch tensor to cupy array, staying on GPU.

    Args:
        data: The torch tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted cupy array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If cupy is not installed
    """
    cupy = _ensure_module("cupy")

    # Only attempt direct conversion if tensor is on CUDA
    if data.is_cuda:
        # Try using CUDA Array Interface
        if _supports_cuda_array_interface(data):
            try:
                result = cupy.asarray(data)

                # Move to specified device if needed
                if device_id is not None and result.device.id != device_id:
                    with cupy.cuda.Device(device_id):
                        return result.copy()

                return result
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.TORCH.value,
                        target_type=MemoryType.CUPY.value,
                        method="CUDA Array Interface",
                        reason=str(e)
                    ) from e

        # Try using DLPack
        if _supports_dlpack(data):
            try:
                dlpack = data.to_dlpack()
                result = cupy.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None and result.device.id != device_id:
                    with cupy.cuda.Device(device_id):
                        return result.copy()

                return result
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.TORCH.value,
                        target_type=MemoryType.CUPY.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
    elif not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.TORCH.value,
            target_type=MemoryType.CUPY.value,
            method="GPU-native",
            reason="PyTorch tensor is not on CUDA"
        )

    # Only reach here if allow_cpu_roundtrip=True
    if device_id is not None:
        with cupy.cuda.Device(device_id):
            return cupy.array(data.detach().cpu().numpy())

    return cupy.array(data.detach().cpu().numpy())


def _torch_to_torch(data: Any, device_id: Optional[int] = None) -> Any:
    """
    Convert torch tensor to torch tensor (identity operation).

    Args:
        data: The torch tensor to convert
        device_id: The target GPU device ID (optional)

    Returns:
        The cloned torch tensor, possibly on a different device
    """
    result = data.clone()

    # Move to specified device if needed
    if device_id is not None:
        if data.is_cuda and data.device.index != device_id:
            result = result.to(f"cuda:{device_id}")
        elif not data.is_cuda:
            result = result.to(f"cuda:{device_id}")

    return result


def _torch_to_tensorflow(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert torch tensor to tensorflow tensor, staying on GPU.

    Args:
        data: The torch tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted tensorflow tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If tensorflow is not installed
        RuntimeError: If TensorFlow version is < 2.12 (unstable DLPack support)
    """
    tf = _ensure_module("tensorflow")

    # Only attempt direct conversion if tensor is on CUDA
    if data.is_cuda:
        # Check TensorFlow version for DLPack compatibility
        try:
            # This will check TF version and raise RuntimeError if < 2.12
            # Enforces Clause 88 (No Inferred Capabilities)
            tf_version = tf.__version__
            major, minor = map(int, tf_version.split('.')[:2])

            if major < 2 or (major == 2 and minor < 12):
                raise RuntimeError(
                    f"TensorFlow version {tf_version} does not support stable DLPack operations. "
                    f"Version 2.12.0 or higher is required. "
                    f"Clause 88 violation: Cannot infer DLPack capability."
                )

            # Check if experimental.dlpack module exists
            if not hasattr(tf.experimental, "dlpack"):
                raise RuntimeError(
                    "TensorFlow installation missing experimental.dlpack module. "
                    "Clause 88 violation: Cannot infer DLPack capability."
                )

            # Now try the conversion
            try:
                dlpack = data.to_dlpack()
                tensor = tf.experimental.dlpack.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None:
                    with tf.device(f"/device:GPU:{device_id}"):
                        return tf.identity(tensor)

                return tensor
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.TORCH.value,
                        target_type=MemoryType.TENSORFLOW.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
        except RuntimeError as e:
            if not allow_cpu_roundtrip:
                raise MemoryConversionError(
                    source_type=MemoryType.TORCH.value,
                    target_type=MemoryType.TENSORFLOW.value,
                    method="DLPack",
                    reason=str(e)
                ) from e

    # If we get here, either the tensor is not on CUDA or there was a DLPack issue
    if not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.TORCH.value,
            target_type=MemoryType.TENSORFLOW.value,
            method="GPU-native",
            reason="PyTorch tensor is not on CUDA or TensorFlow DLPack support issue"
        )

    # Only reach here if allow_cpu_roundtrip=True
    # This is an explicit CPU roundtrip, which is only allowed if explicitly requested
    numpy_data = data.detach().cpu().numpy()

    if device_id is not None:
        with tf.device(f"/device:GPU:{device_id}"):
            return tf.convert_to_tensor(numpy_data)

    return tf.convert_to_tensor(numpy_data)


# TensorFlow conversion functions

def _tensorflow_to_numpy(data: Any) -> Any:
    """
    Convert tensorflow tensor to numpy array.

    Args:
        data: The tensorflow tensor to convert

    Returns:
        The converted numpy array
    """
    return data.numpy()


def _torch_to_pyclesperanto(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert torch tensor to pyclesperanto array, staying on GPU.

    Args:
        data: The torch tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted pyclesperanto array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If pyclesperanto is not installed
    """
    cle = _ensure_module("pyclesperanto")

    # Try GPU-to-GPU conversion first
    if data.is_cuda:
        try:
            # Use CUDA array interface for zero-copy conversion
            if _supports_cuda_array_interface(data):
                # Select target device
                target_device = device_id if device_id is not None else data.device.index
                cle.select_device(target_device)

                # Convert via CUDA array interface
                return cle.asarray(data.detach())
        except Exception as e:
            if not allow_cpu_roundtrip:
                raise MemoryConversionError(
                    source_type=MemoryType.TORCH.value,
                    target_type=MemoryType.PYCLESPERANTO.value,
                    method="GPU_conversion",
                    reason=str(e)
                ) from e

    # Fallback: CPU roundtrip
    if not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.TORCH.value,
            target_type=MemoryType.PYCLESPERANTO.value,
            method="GPU-native",
            reason="PyTorch tensor is not on CUDA"
        )

    # CPU roundtrip conversion
    numpy_data = data.detach().cpu().numpy()
    cle.select_device(device_id if device_id is not None else 0)
    return cle.push(numpy_data)


def _torch_to_jax(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert PyTorch tensor to JAX array, staying on GPU with zero-copy DLPack transfer.

    Args:
        data: The PyTorch tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip (ignored, always False)
        device_id: The target GPU device ID (optional)

    Returns:
        The converted JAX array

    Raises:
        MemoryConversionError: If conversion fails
        ImportError: If JAX is not installed
    """
    jax = _ensure_module("jax")
    torch = _ensure_module("torch")

    # If tensor is on CPU, move it to GPU first (similar to _numpy_to_jax behavior)
    if not data.is_cuda:
        if device_id is not None:
            # Move CPU tensor to specified GPU device
            data = data.to(f"cuda:{device_id}")
        else:
            # Move to default GPU device
            data = data.cuda()

    # Now attempt direct conversion with tensor on CUDA
    if data.is_cuda:
        # Try using DLPack for direct GPU-to-GPU transfer
        if _supports_dlpack(data):
            try:
                dlpack = torch.to_dlpack(data)
                result = jax.dlpack.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None:
                    current_device = None
                    try:
                        # Extract device ID from JAX array
                        device_str = str(result.device)
                        if "gpu:" in device_str or "cuda:" in device_str:
                            current_device = int(device_str.split("gpu:")[-1].split(")")[0])
                    except Exception:
                        pass

                    # Only move if needed
                    if current_device != device_id:
                        result = jax.device_put(result, jax.devices("gpu")[device_id])

                return result
            except Exception as e:
                # No CPU roundtrip allowed, so fail loudly
                raise MemoryConversionError(
                    source_type=MemoryType.TORCH.value,
                    target_type=MemoryType.JAX.value,
                    method="DLPack",
                    reason=str(e)
                ) from e

    # If we get here, there was a DLPack issue (tensor should be on CUDA at this point)
    raise MemoryConversionError(
        source_type=MemoryType.TORCH.value,
        target_type=MemoryType.JAX.value,
        method="GPU-native",
        reason="DLPack conversion failed after moving tensor to CUDA"
    )


# JAX conversion functions

def _numpy_to_jax(data: Any, gpu_id: int) -> Any:
    """
    Convert numpy array to JAX array.

    Args:
        data: The numpy array to convert
        gpu_id: The target GPU device ID

    Returns:
        The converted JAX array

    Raises:
        ImportError: If JAX is not installed
        ValueError: If gpu_id is negative
    """
    jax = _ensure_module("jax")

    # Validate gpu_id
    if gpu_id < 0:
        raise ValueError(f"Invalid GPU ID: {gpu_id}. Must be a non-negative integer.")

    # Create JAX array on CPU
    result = jax.numpy.array(data)

    # Always move to the specified GPU device
    # JAX uses different device notation
    result = jax.device_put(result, jax.devices("gpu")[gpu_id])

    return result


def _jax_to_numpy(data: Any) -> Any:
    """
    Convert JAX array to numpy array.

    Args:
        data: The JAX array to convert

    Returns:
        The converted numpy array
    """
    # JAX arrays can be converted to numpy with .copy()
    return data.copy()


def _jax_to_cupy(
    data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None
) -> Any:
    """
    Convert JAX array to cupy array, staying on GPU if possible.

    Args:
        data: The JAX array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted cupy array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If cupy is not installed
    """
    jax = _ensure_module("jax")
    cupy = _ensure_module("cupy")

    # Check if JAX array is on GPU
    device_str = str(data.device).lower()
    is_on_gpu = device_str.startswith("gpu") or device_str.startswith("cuda")

    if is_on_gpu:
        # Try using DLPack for direct GPU-to-GPU transfer
        if _supports_dlpack(data):
            try:
                dlpack = jax.dlpack.to_dlpack(data)
                result = cupy.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None and result.device.id != device_id:
                    with cupy.cuda.Device(device_id):
                        return result.copy()

                return result
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.JAX.value,
                        target_type=MemoryType.CUPY.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
    elif not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.JAX.value,
            target_type=MemoryType.CUPY.value,
            method="GPU-native",
            reason="JAX array is not on GPU"
        )

    # Only reach here if allow_cpu_roundtrip=True or DLPack failed
    numpy_data = _jax_to_numpy(data)

    if device_id is not None:
        with cupy.cuda.Device(device_id):
            return cupy.array(numpy_data)

    return cupy.array(numpy_data)


def _jax_to_torch(
    data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None
) -> Any:
    """
    Convert JAX array to torch tensor, staying on GPU if possible.

    Args:
        data: The JAX array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted torch tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If torch is not installed
    """
    jax = _ensure_module("jax")
    torch = _ensure_module("torch")

    # Check if JAX array is on GPU
    device_str = str(data.device).lower()
    is_on_gpu = device_str.startswith("gpu") or device_str.startswith("cuda")

    if is_on_gpu:
        # Try using DLPack for direct GPU-to-GPU transfer
        if _supports_dlpack(data):
            try:
                dlpack = jax.dlpack.to_dlpack(data)
                tensor = torch.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None and tensor.device.index != device_id:
                    tensor = tensor.to(f"cuda:{device_id}")

                return tensor
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.JAX.value,
                        target_type=MemoryType.TORCH.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
    elif not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.JAX.value,
            target_type=MemoryType.TORCH.value,
            method="GPU-native",
            reason="JAX array is not on GPU"
        )

    # Only reach here if allow_cpu_roundtrip=True or DLPack failed
    numpy_data = _jax_to_numpy(data)

    if device_id is not None:
        return torch.tensor(numpy_data, device=f"cuda:{device_id}")

    return torch.tensor(numpy_data)


def _jax_to_tensorflow(
    data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None
) -> Any:
    """
    Convert JAX array to tensorflow tensor, staying on GPU if possible.

    Args:
        data: The JAX array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted tensorflow tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If tensorflow is not installed
    """
    jax = _ensure_module("jax")
    tf = _ensure_module("tensorflow")

    # Check if JAX array is on GPU
    device_str = str(data.device).lower()
    is_on_gpu = device_str.startswith("gpu") or device_str.startswith("cuda")

    if is_on_gpu:
        # Try using DLPack for direct GPU-to-GPU transfer
        if _supports_dlpack(data):
            try:
                dlpack = jax.dlpack.to_dlpack(data)
                tensor = tf.experimental.dlpack.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None:
                    with tf.device(f"/device:GPU:{device_id}"):
                        return tf.identity(tensor)

                return tensor
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.JAX.value,
                        target_type=MemoryType.TENSORFLOW.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
    elif not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.JAX.value,
            target_type=MemoryType.TENSORFLOW.value,
            method="GPU-native",
            reason="JAX array is not on GPU"
        )

    # Only reach here if allow_cpu_roundtrip=True or DLPack failed
    numpy_data = _jax_to_numpy(data)

    if device_id is not None:
        with tf.device(f"/device:GPU:{device_id}"):
            return tf.convert_to_tensor(numpy_data)

    return tf.convert_to_tensor(numpy_data)


def _tensorflow_to_cupy(
    data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None
) -> Any:
    """
    Convert tensorflow tensor to cupy array, staying on GPU.

    Args:
        data: The tensorflow tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted cupy array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If cupy is not installed
        RuntimeError: If TensorFlow version is < 2.12 (unstable DLPack support)
    """
    cupy = _ensure_module("cupy")
    tf = _ensure_module("tensorflow")

    # _supports_dlpack will raise RuntimeError if TF version < 2.12 or tensor is on CPU
    # This enforces Clause 88 (No Inferred Capabilities)
    try:
        if _supports_dlpack(data):
            try:
                dlpack = tf.experimental.dlpack.to_dlpack(data)
                result = cupy.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None and result.device.id != device_id:
                    with cupy.cuda.Device(device_id):
                        return result.copy()

                return result
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.TENSORFLOW.value,
                        target_type=MemoryType.CUPY.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
    except RuntimeError as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.TENSORFLOW.value,
                target_type=MemoryType.CUPY.value,
                method="DLPack",
                reason=str(e)
            ) from e

    # Only reach here if allow_cpu_roundtrip=True or _supports_dlpack raised an exception
    if not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.TENSORFLOW.value,
            target_type=MemoryType.CUPY.value,
            method="GPU-native",
            reason="TensorFlow tensor is not on GPU or DLPack not supported"
        )

    # Only reach here if allow_cpu_roundtrip=True
    if device_id is not None:
        with cupy.cuda.Device(device_id):
            return cupy.array(data.numpy())

    return cupy.array(data.numpy())


def _tensorflow_to_torch(
    data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None
) -> Any:
    """
    Convert tensorflow tensor to torch tensor, staying on GPU.

    Args:
        data: The tensorflow tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted torch tensor

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If torch is not installed
        RuntimeError: If TensorFlow version is < 2.12 (unstable DLPack support)
    """
    torch = _ensure_module("torch")
    tf = _ensure_module("tensorflow")

    # _supports_dlpack will raise RuntimeError if TF version < 2.12 or tensor is on CPU
    # This enforces Clause 88 (No Inferred Capabilities)
    try:
        if _supports_dlpack(data):
            try:
                dlpack = tf.experimental.dlpack.to_dlpack(data)
                tensor = torch.from_dlpack(dlpack)

                # Move to specified device if needed
                if device_id is not None and tensor.device.index != device_id:
                    tensor = tensor.to(f"cuda:{device_id}")

                return tensor
            except Exception as e:
                if not allow_cpu_roundtrip:
                    raise MemoryConversionError(
                        source_type=MemoryType.TENSORFLOW.value,
                        target_type=MemoryType.TORCH.value,
                        method="DLPack",
                        reason=str(e)
                    ) from e
    except RuntimeError as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.TENSORFLOW.value,
                target_type=MemoryType.TORCH.value,
                method="DLPack",
                reason=str(e)
            ) from e

    # Only reach here if allow_cpu_roundtrip=True or _supports_dlpack raised an exception
    if not allow_cpu_roundtrip:
        raise MemoryConversionError(
            source_type=MemoryType.TENSORFLOW.value,
            target_type=MemoryType.TORCH.value,
            method="GPU-native",
            reason="TensorFlow tensor is not on GPU or DLPack not supported"
        )

    # Only reach here if allow_cpu_roundtrip=True
    tensor = torch.from_numpy(data.numpy())

    # Move to specified device if needed
    if device_id is not None:
        tensor = tensor.to(f"cuda:{device_id}")

    return tensor


def _tensorflow_to_jax(
    data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None
) -> Any:
    """
    Convert TensorFlow tensor to JAX array, staying on GPU with zero-copy DLPack transfer.

    Args:
        data: The TensorFlow tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip (ignored, always False)
        device_id: The target GPU device ID (optional)

    Returns:
        The converted JAX array

    Raises:
        MemoryConversionError: If conversion fails
        ImportError: If JAX is not installed
        RuntimeError: If TensorFlow version is < 2.12 (unstable DLPack support)
    """
    jax = _ensure_module("jax")
    tf = _ensure_module("tensorflow")

    # Check TensorFlow version for DLPack compatibility
    tf_version = tf.__version__
    major, minor = map(int, tf_version.split('.')[:2])

    if major < 2 or (major == 2 and minor < 12):
        raise RuntimeError(
            f"TensorFlow version {tf_version} does not support stable DLPack operations. "
            f"Version 2.12.0 or higher is required. "
            f"Clause 88 violation: Cannot infer DLPack capability."
        )

    # Check if experimental.dlpack module exists
    if not hasattr(tf.experimental, "dlpack"):
        raise RuntimeError(
            "TensorFlow installation missing experimental.dlpack module. "
            "Clause 88 violation: Cannot infer DLPack capability."
        )

    # Check if tensor is on GPU
    device_str = data.device.lower()
    is_on_gpu = "gpu" in device_str

    if is_on_gpu:
        # Try using DLPack for direct GPU-to-GPU transfer
        try:
            dlpack = tf.experimental.dlpack.to_dlpack(data)
            result = jax.dlpack.from_dlpack(dlpack)

            # Move to specified device if needed
            if device_id is not None:
                current_device = None
                try:
                    # Extract device ID from JAX array
                    device_str = str(result.device)
                    if "gpu:" in device_str:
                        current_device = int(device_str.rsplit('gpu:', maxsplit=1)[-1].split(")")[0])
                except (ValueError, IndexError):
                    pass

                # Only move if needed
                if current_device != device_id:
                    result = jax.device_put(result, jax.devices("gpu")[device_id])

            return result
        except Exception as e:
            # No CPU roundtrip allowed, so fail loudly
            raise MemoryConversionError(
                source_type=MemoryType.TENSORFLOW.value,
                target_type=MemoryType.JAX.value,
                method="DLPack",
                reason=str(e)
            ) from e

    # If we get here, the tensor is not on GPU
    # No CPU roundtrip allowed, so fail loudly
    raise MemoryConversionError(
        source_type=MemoryType.TENSORFLOW.value,
        target_type=MemoryType.JAX.value,
        method="GPU-native",
        reason="TensorFlow tensor is not on GPU"
    )


def _tensorflow_to_tensorflow(data: Any, device_id: Optional[int] = None) -> Any:
    """
    Convert tensorflow tensor to tensorflow tensor (identity operation).

    Args:
        data: The tensorflow tensor to convert
        device_id: The target GPU device ID (optional)

    Returns:
        The copied tensorflow tensor, possibly on a different device
    """
    tf = _ensure_module("tensorflow")

    if device_id is not None:
        with tf.device(f"/device:GPU:{device_id}"):
            return tf.identity(data)

    return tf.identity(data)


def _tensorflow_to_pyclesperanto(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert tensorflow tensor to pyclesperanto array, staying on GPU.

    Args:
        data: The tensorflow tensor to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted pyclesperanto array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If pyclesperanto is not installed
    """
    tf = _ensure_module("tensorflow")
    cle = _ensure_module("pyclesperanto")

    # Try GPU-to-GPU conversion first
    try:
        # Use DLPack for zero-copy conversion
        if hasattr(tf.experimental, 'dlpack') and hasattr(tf.experimental.dlpack, 'to_dlpack'):
            dlpack = tf.experimental.dlpack.to_dlpack(data)

            # Select target device
            target_device = device_id if device_id is not None else 0
            cle.select_device(target_device)

            # Convert from DLPack
            return cle.from_dlpack(dlpack)
    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.TENSORFLOW.value,
                target_type=MemoryType.PYCLESPERANTO.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

    # Fallback: CPU roundtrip
    numpy_data = data.numpy()
    cle.select_device(device_id if device_id is not None else 0)
    return cle.push(numpy_data)


def _jax_to_jax(data: Any, device_id: Optional[int] = None) -> Any:
    """
    Convert JAX array to JAX array (identity operation).

    Args:
        data: The JAX array to convert
        device_id: The target GPU device ID (optional)

    Returns:
        The cloned JAX array, possibly on a different device
    """
    jax = _ensure_module("jax")

    result = data.copy()

    # Move to specified device if needed
    if device_id is not None:
        result = jax.device_put(result, jax.devices("gpu")[device_id])

    return result


def _jax_to_pyclesperanto(data: Any, allow_cpu_roundtrip: bool = False, device_id: Optional[int] = None) -> Any:
    """
    Convert JAX array to pyclesperanto array, staying on GPU.

    Args:
        data: The JAX array to convert
        allow_cpu_roundtrip: Whether to allow fallback to CPU roundtrip
        device_id: The target GPU device ID (optional)

    Returns:
        The converted pyclesperanto array

    Raises:
        MemoryConversionError: If conversion fails and CPU fallback is not authorized
        ImportError: If pyclesperanto is not installed
    """
    jax = _ensure_module("jax")
    cle = _ensure_module("pyclesperanto")

    # Try GPU-to-GPU conversion first
    try:
        # Use DLPack for zero-copy conversion
        if hasattr(data, '__dlpack__'):
            dlpack = data.__dlpack__()

            # Select target device
            target_device = device_id if device_id is not None else 0
            cle.select_device(target_device)

            # Convert from DLPack
            return cle.from_dlpack(dlpack)
    except Exception as e:
        if not allow_cpu_roundtrip:
            raise MemoryConversionError(
                source_type=MemoryType.JAX.value,
                target_type=MemoryType.PYCLESPERANTO.value,
                method="GPU_conversion",
                reason=str(e)
            ) from e

    # Fallback: CPU roundtrip
    numpy_data = _jax_to_numpy(data)
    cle.select_device(device_id if device_id is not None else 0)
    return cle.push(numpy_data)
