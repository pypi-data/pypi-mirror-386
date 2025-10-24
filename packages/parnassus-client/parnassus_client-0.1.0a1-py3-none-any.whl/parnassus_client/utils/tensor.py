import logging

import numpy as np

from parnassus_client.proto import arm_stream_pb2 as pb2

logger = logging.getLogger(__name__)


def numpy_to_tensor(arr: np.ndarray) -> pb2.Tensor:
    """将numpy数组转换为protobuf Tensor"""
    return pb2.Tensor(data=arr.tobytes(), shape=list(arr.shape), dtype=str(arr.dtype))


def tensor_to_numpy(tensor: pb2.Tensor) -> np.ndarray:
    """将protobuf Tensor转换为numpy数组"""
    dtype = np.dtype(tensor.dtype)
    arr = np.frombuffer(tensor.data, dtype=dtype)
    return arr.reshape(tensor.shape)
