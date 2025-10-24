#!/usr/bin/env python3
"""
按步交互的 ArmEnv 客户端（类封装版）

特性：
- 将按需发送/按步接收的逻辑封装为一个类 TestStreamClient，提供清晰的 API：connect(), reset(), step(), close(), shutdown()。
- 内部使用阻塞队列作为请求源，并通过同一线程的 next(responses) 保证“一步一收”的交互模型。
- 兼容不同实现中 reward/terminated/truncated 是 tensor 或标量的情况。
- 提供上下文管理器支持（with TestStreamClient(...) as c: ...）。

注意：该客户端仍假设服务器会在收到每个请求后返回对应 reply。如果服务器在某步不返回，next(responses) 将阻塞直到超时或服务端响应。
"""

from __future__ import annotations

import logging
import queue
from typing import Any, Optional, Sequence, Union

import grpc
import numpy as np

from parnassus_client.proto import arm_stream_pb2, arm_stream_pb2_grpc
from parnassus_client.utils.tensor import numpy_to_tensor, tensor_to_numpy

logger = logging.getLogger(__name__)


class StreamClient:
    """按步交互的 gRPC 测试客户端封装。

    用法示例：
        with StreamClient('localhost:50051') as client:
            client.connect()
            reset_obs = client.reset(seed=42)
            for i in range(5):
                action = np.array([np.sin(i * 0.5)], dtype=np.float32)
                step_reply = client.step(action)
            client.close()
    """

    def __init__(
        self,
        server_address: str = "localhost:50051",
    ):
        self.server_address = server_address
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[Any] = None
        self._req_q: "queue.Queue[Any]" = queue.Queue()
        self._sentinel = object()
        self._responses = None

    # ------------------------ 连接与流 ------------------------
    def connect(self) -> None:
        """建立 gRPC 通道并启动双向流（不会立即发送任何请求）。"""
        self._channel = grpc.insecure_channel(self.server_address)
        self._stub = arm_stream_pb2_grpc.ArmEnvStub(self._channel)
        self._responses = self._stub.StreamEnv(self._request_generator())
        logger.info("Connected to %s", self.server_address)

    def _request_generator(self):
        """生成器：从队列中阻塞取出请求并 yield；遇到哨兵结束。"""
        while True:
            req = self._req_q.get()
            if req is self._sentinel:
                return
            yield req

    def shutdown(self) -> None:
        """发送哨兵并关闭底层通道（用于清理）。"""
        try:
            self._req_q.put(self._sentinel)
        except Exception:
            pass
        if self._channel:
            try:
                self._channel.close()
            except Exception:
                pass
        logger.info("Client shutdown complete")

    # ------------------------ 高层 API: reset/step/close ------------------------
    def reset(
        self,
        seed: Optional[Union[int, Sequence[int]]] = None,
        render_mode: Optional[str] = None,
    ):
        """发送 Reset 请求并返回 Reset reply 的 observation（numpy array 或 None）。"""
        if seed is None:
            reset_msg = arm_stream_pb2.Reset()
        else:
            # 兼容原 proto 中 seed 可能为 repeated/单值的不同实现
            try:
                if isinstance(seed, Sequence) and not isinstance(
                    seed, (str, bytes, bytearray)
                ):
                    reset_msg = arm_stream_pb2.Reset(
                        seed=[int(s) for s in seed]  # type: ignore[arg-type]
                    )
                else:
                    reset_msg = arm_stream_pb2.Reset(seed=[int(seed)])  # type: ignore[arg-type]
            except Exception:
                reset_msg = arm_stream_pb2.Reset(seed=int(seed))

        if render_mode is not None:
            try:
                reset_msg.render_mode = render_mode
            except Exception:
                # 如果 proto 没有 render_mode 字段，忽略
                pass

        self._req_q.put(arm_stream_pb2.EnvRequest(reset=reset_msg))

        # 阻塞等待一次响应并解析
        try:
            resp = next(self._responses)
        except StopIteration:
            raise RuntimeError("Server closed stream unexpectedly after reset")

        if resp.HasField("reset"):
            try:
                return tensor_to_numpy(resp.reset.observation)
            except Exception:
                return None
        else:
            logger.warning("Reset request returned non-reset reply")
            return None

    def step(self, action: np.ndarray):
        """发送 Step 请求并返回一个字典：{'observation': np.ndarray|None, 'reward': float|None, 'terminated': bool|None, 'truncated': bool|None, 'raw': resp}

        注意：reward/terminated/truncated 的格式在不同实现中可能不同，方法会尝试兼容 tensor 与标量两种情形。
        """
        self._req_q.put(
            arm_stream_pb2.EnvRequest(
                step=arm_stream_pb2.Step(action=numpy_to_tensor(action))
            )
        )

        try:
            resp = next(self._responses)
        except StopIteration:
            raise RuntimeError("Server closed stream unexpectedly after step request")

        if not resp.HasField("step"):
            logger.warning("Expected step reply but got different reply")
            return {
                "observation": None,
                "reward": None,
                "terminated": None,
                "truncated": None,
                "raw": resp,
            }

        # 解析 observation
        obs = None
        try:
            obs = tensor_to_numpy(resp.step.observation)
        except Exception:
            obs = None

        def _decode_tensor_field(field_value, dtype):
            try:
                arr = tensor_to_numpy(field_value)
                arr = np.asarray(arr, dtype=dtype)
                if arr.ndim == 0 or arr.size == 1:
                    scalar = arr.reshape(-1)[0]
                    return bool(scalar) if dtype == np.bool_ else float(scalar)
                if dtype == np.bool_:
                    return arr.astype(bool)
                return arr
            except Exception:
                try:
                    return bool(field_value) if dtype == np.bool_ else float(field_value)
                except Exception:
                    return None

        reward = (
            _decode_tensor_field(resp.step.reward, np.float32)
            if hasattr(resp.step, "reward")
            else None
        )
        terminated = (
            _decode_tensor_field(resp.step.terminated, np.bool_)
            if hasattr(resp.step, "terminated")
            else None
        )
        truncated = (
            _decode_tensor_field(resp.step.truncated, np.bool_)
            if hasattr(resp.step, "truncated")
            else None
        )

        return {
            "observation": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "raw": resp,
        }

    def close(self):
        """发送 Close 请求并等待 Close reply。"""
        self._req_q.put(arm_stream_pb2.EnvRequest(close=arm_stream_pb2.Close()))
        try:
            resp = next(self._responses)
        except StopIteration:
            raise RuntimeError("Server closed stream unexpectedly after close request")

        if resp.HasField("close"):
            logger.info("Close reply received from server")
            return True
        else:
            logger.warning("Close request returned non-close reply")
            return False

    # ------------------------ 上下文管理 ------------------------
    def __enter__(self) -> "StreamClient":
        if self._channel is None:
            self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.shutdown()
        finally:
            # 不抑制异常
            return False
