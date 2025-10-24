"""Render-capable client for the Arm stream service.

This module provides :class:`RenderClient`, a subclass of
:class:`parnassus.clients.arm_stream.client.StreamClient` that renders the
returned arm states as a simple cylindrical inverted pendulum animation.

The rendering pipeline is intentionally lightweight and mirrors the logic in
``tests/test_stream/test_render.py`` so that interactive debugging works the
same way outside the test harness.
"""

from __future__ import annotations

import math
import time
from typing import Any, Callable, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from google.protobuf.json_format import MessageToDict
from matplotlib.patches import Circle

from .client import StreamClient as Client

StateExtractor = Callable[[np.ndarray, Optional[Dict[str, Any]]], Tuple[float, float]]


class RenderClient(Client):
    """Stream client with a Matplotlib based renderer.

    Parameters
    ----------
    server_address:
        Target gRPC endpoint passed to :class:`Client`.
    radius:
        Radius of the cylinder on which the cart moves.
    pendulum_len:
        Length of the pendulum segment used for visualization.
    cyl_half_height:
        Half height of the reference cylinder.
    auto_render:
        If ``True`` (default), render whenever :meth:`reset` or :meth:`step`
        returns a new observation.
    state_extractor:
        Optional callable taking ``(observation, info_dict)`` and returning a
        tuple ``(theta, phi)``. When omitted, the extractor falls back to the
        observation vector (first two components) or the ``info`` payload.
    """

    def __init__(
        self,
        server_address: str = "localhost:50051",
        *,
        radius: float = 1.0,
        pendulum_len: float = 1.0,
        cyl_half_height: float = 1.0,
        auto_render: bool = True,
        state_extractor: Optional[StateExtractor] = None,
    ) -> None:
        super().__init__(server_address=server_address)
        self.R = float(radius)
        self.L = float(pendulum_len)
        self.h = float(cyl_half_height)
        self.auto_render = bool(auto_render)
        self._state_extractor = state_extractor or self._default_state_extractor

        self.fig = plt.figure(figsize=(13, 7))
        gs = self.fig.add_gridspec(
            2,
            2,
            width_ratios=(2.2, 1.0),
            height_ratios=(1.0, 1.0),
            wspace=0.25,
            hspace=0.25,
        )
        self.ax3d = self.fig.add_subplot(gs[:, 0], projection="3d")
        self.ax_plan_arm = self.fig.add_subplot(gs[0, 1])
        self.ax_plan_pend = self.fig.add_subplot(gs[1, 1])
        self._init_scene()

        self.last_time = time.time()
        self.fps = 0.0

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _init_scene(self) -> None:
        ax3d = self.ax3d
        ax3d.set_box_aspect((1, 1, 0.8))
        margin = self.R + self.L + 0.5
        ax3d.set_xlim(-margin, margin)
        ax3d.set_ylim(-margin, margin)
        ax3d.set_zlim(-self.h, max(self.h, self.L) + 0.5)
        ax3d.set_xlabel("X")
        ax3d.set_ylabel("Y")
        ax3d.set_zlabel("Z")

        u = np.linspace(0, 2 * np.pi, 60)
        z = np.linspace(-self.h, self.h, 2)
        U, Z = np.meshgrid(u, z)
        X = self.R * np.cos(U)
        Y = self.R * np.sin(U)
        ax3d.plot_wireframe(X, Y, Z, rcount=6, ccount=6, alpha=0.15)

        arm_color = "#1f77b4"
        pendulum_color = "#ff7f0e"

        (self.rotor_axis,) = ax3d.plot(
            [0, 0], [0, 0], [-self.h, self.h], linewidth=2, alpha=0.3
        )
        (self.horizontal_arm,) = ax3d.plot(
            [0, 0], [0, 0], [0, 0], linewidth=3, color=arm_color
        )
        (self.pendulum_line,) = ax3d.plot(
            [0, 0], [0, 0], [0, 0], linewidth=3, color=pendulum_color
        )
        self.cart_point = ax3d.scatter([0], [0], [0], s=50, color=arm_color)

        ax_plan_arm = self.ax_plan_arm
        ax_plan_arm.set_aspect("equal", adjustable="box")
        arm_margin = self.R + 0.6
        ax_plan_arm.set_xlim(-arm_margin, arm_margin)
        ax_plan_arm.set_ylim(-arm_margin, arm_margin)
        ax_plan_arm.set_title("First arm (top view)", fontsize=12)
        ax_plan_arm.set_facecolor("white")
        ax_plan_arm.grid(False)
        ax_plan_arm.set_xticks([])
        ax_plan_arm.set_yticks([])
        ax_plan_arm.tick_params(which="both", length=0)

        circle = Circle(
            (0.0, 0.0),
            radius=self.R,
            edgecolor="0.5",
            facecolor="none",
            linewidth=1.2,
            alpha=0.2,
        )
        ax_plan_arm.add_patch(circle)
        self.arm_circle = circle

        self.arm_angle_lines = []
        self.arm_angle_labels = []
        label_radius = self.R + 0.25 * arm_margin
        for angle_deg in range(0, 360, 30):
            angle_rad = math.radians(angle_deg)
            x_end = self.R * math.cos(angle_rad)
            y_end = self.R * math.sin(angle_rad)
            (line,) = ax_plan_arm.plot(
                [0.0, x_end],
                [0.0, y_end],
                linestyle="--",
                linewidth=0.8,
                color="0.6",
                alpha=0.25,
            )
            self.arm_angle_lines.append(line)
            ha = "left" if math.cos(angle_rad) >= 0 else "right"
            va = "bottom" if math.sin(angle_rad) >= 0 else "top"
            label = ax_plan_arm.text(
                label_radius * math.cos(angle_rad),
                label_radius * math.sin(angle_rad),
                f"{angle_deg}\N{DEGREE SIGN}",
                fontsize=9,
                color="0.3",
                ha=ha,
                va=va,
            )
            self.arm_angle_labels.append(label)

        (self.horizontal_arm_plan,) = ax_plan_arm.plot(
            [0.0, 0.0], [0.0, 0.0], linewidth=3, color=arm_color
        )
        self.arm_tip_plan = ax_plan_arm.scatter([0.0], [0.0], s=40, color=arm_color)

        ax_plan_pend = self.ax_plan_pend
        ax_plan_pend.set_aspect("equal", adjustable="box")
        pend_margin = self.L + 0.4
        ax_plan_pend.set_xlim(-pend_margin, pend_margin)
        ax_plan_pend.set_ylim(-pend_margin, pend_margin)
        ax_plan_pend.set_title("Second arm plane", fontsize=12)
        ax_plan_pend.set_facecolor("white")
        ax_plan_pend.grid(False)
        ax_plan_pend.set_xticks([])
        ax_plan_pend.set_yticks([])
        ax_plan_pend.tick_params(which="both", length=0)

        pend_circle = Circle(
            (0.0, 0.0),
            radius=self.L,
            edgecolor="0.5",
            facecolor="none",
            linewidth=1.2,
            alpha=0.2,
        )
        ax_plan_pend.add_patch(pend_circle)
        self.pend_circle = pend_circle

        self.pend_angle_lines = []
        self.pend_angle_labels = []
        pend_label_radius = self.L + 0.25 * pend_margin
        for angle_deg in range(0, 360, 30):
            angle_rad = math.radians(angle_deg)
            x_end = self.L * math.sin(angle_rad)
            z_end = self.L * math.cos(angle_rad)
            (line,) = ax_plan_pend.plot(
                [0.0, x_end],
                [0.0, z_end],
                linestyle="--",
                linewidth=0.8,
                color="0.6",
                alpha=0.25,
            )
            self.pend_angle_lines.append(line)
            ha = "left" if math.sin(angle_rad) >= 0 else "right"
            va = "bottom" if math.cos(angle_rad) >= 0 else "top"
            label = ax_plan_pend.text(
                pend_label_radius * math.sin(angle_rad),
                pend_label_radius * math.cos(angle_rad),
                f"{angle_deg}\N{DEGREE SIGN}",
                fontsize=9,
                color="0.3",
                ha=ha,
                va=va,
            )
            self.pend_angle_labels.append(label)

        (self.pendulum_line_side,) = ax_plan_pend.plot(
            [0.0, 0.0], [0.0, 0.0], linewidth=3, color=pendulum_color
        )
        self.pendulum_origin_side = ax_plan_pend.scatter(
            [0.0], [0.0], s=40, color=arm_color
        )
        self.pendulum_tip_side = ax_plan_pend.scatter(
            [0.0], [0.0], s=40, color=pendulum_color
        )

        self.fps_text = self.fig.text(0.88, 0.96, "FPS: 0.0", fontsize=12, ha="right")

        self.fig.tight_layout()
        plt.ion()
        plt.show(block=False)

    def _default_state_extractor(
        self,
        observation: np.ndarray,
        info: Optional[Dict[str, Any]],
    ) -> Tuple[float, float]:
        if info:
            render_info = info
            if "render_state" in render_info and isinstance(
                render_info["render_state"], dict
            ):
                render_info = render_info["render_state"]  # type: ignore[assignment]
            if "theta" in render_info and "phi" in render_info:
                return float(render_info["theta"]), float(render_info["phi"])

        if observation is None:
            raise ValueError("No observation available to infer render state.")

        arr = np.asarray(observation, dtype=float).reshape(-1)
        if arr.size < 2:
            raise ValueError(
                "Observation must contain at least two elements for default rendering."
            )
        return float(arr[0]), float(arr[1])

    def render_state(self, theta: float, phi: float) -> None:
        R, L = self.R, self.L

        x = R * math.cos(theta)
        y = R * math.sin(theta)
        z = 0.0

        nx = -math.sin(theta)
        ny = math.cos(theta)

        tip_x = x + L * math.sin(phi) * nx
        tip_y = y + L * math.sin(phi) * ny
        tip_z = z + L * math.cos(phi)

        self.horizontal_arm.set_data([0.0, x], [0.0, y])
        self.horizontal_arm.set_3d_properties([0.0, 0.0])

        self.pendulum_line.set_data([x, tip_x], [y, tip_y])
        self.pendulum_line.set_3d_properties([z, tip_z])

        self.cart_point._offsets3d = ([x], [y], [z])

        self.horizontal_arm_plan.set_data([0.0, x], [0.0, y])
        self.arm_tip_plan.set_offsets(np.array([[x, y]]))

        local_x = L * math.sin(phi)
        local_z = L * math.cos(phi)
        self.pendulum_line_side.set_data([0.0, local_x], [0.0, local_z])
        self.pendulum_tip_side.set_offsets(np.array([[local_x, local_z]]))

        now = time.time()
        dt = now - self.last_time
        if dt > 0:
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
        self.last_time = now
        self.fps_text.set_text(f"FPS: {self.fps:.1f}")

        self.fig.canvas.draw_idle()
        plt.pause(0.001)

    def render_observation(
        self,
        observation: Optional[np.ndarray],
        info: Optional[Dict[str, Any]] = None,
    ) -> None:
        if observation is None:
            return
        theta, phi = self._state_extractor(np.asarray(observation), info)
        self.render_state(theta, phi)

    # ------------------------------------------------------------------
    # StreamClient overrides
    # ------------------------------------------------------------------
    def reset(self, seed: Optional[int] = None, render_mode: Optional[str] = None):
        obs = super().reset(seed=seed, render_mode=render_mode)
        self.record_state(obs, None)
        if self.auto_render:
            self.render_observation(obs)
        return obs

    def step(self, action: np.ndarray):
        reply = super().step(action)
        info_dict: Optional[Dict[str, Any]] = None
        raw = reply.get("raw")
        if raw is not None and hasattr(raw, "HasField") and raw.HasField("step"):
            info_dict = MessageToDict(raw.step.info, preserving_proto_field_name=True)
            if not info_dict:
                info_dict = None
        self.record_state(reply.get("observation"), info_dict)
        if self.auto_render:
            self.render_observation(reply.get("observation"), info_dict)
        reply["info"] = info_dict
        return reply

    # ------------------------------------------------------------------
    # Manual render loop (optional helper)
    # ------------------------------------------------------------------
    def run_render_loop(
        self,
        state_provider: Optional[Callable[[], Tuple[float, float]]] = None,
        fps: float = 50.0,
    ) -> None:
        if state_provider is None:

            def _provider() -> Tuple[float, float]:
                obs = getattr(self, "last_observation", None)
                info = getattr(self, "last_info", None)
                if obs is None:
                    raise RuntimeError("No observation available for rendering loop.")
                return self._state_extractor(np.asarray(obs), info)

            provider = _provider
        else:
            provider = state_provider

        dt = 1.0 / float(max(1.0, float(fps)))
        try:
            while plt.fignum_exists(self.fig.number):
                t0 = time.time()
                theta, phi = provider()
                self.render_state(float(theta), float(phi))
                elapsed = time.time() - t0
                time.sleep(max(0.0, dt - elapsed))
        except KeyboardInterrupt:
            print("用户中断，退出渲染循环。")
        finally:
            try:
                plt.close(self.fig)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Tracking helpers for the default state provider
    # ------------------------------------------------------------------
    @property
    def last_observation(self) -> Optional[np.ndarray]:
        return getattr(self, "_last_observation", None)

    @last_observation.setter
    def last_observation(self, value: Optional[np.ndarray]) -> None:
        self._last_observation = None if value is None else np.asarray(value)

    @property
    def last_info(self) -> Optional[Dict[str, Any]]:
        return getattr(self, "_last_info", None)

    @last_info.setter
    def last_info(self, value: Optional[Dict[str, Any]]) -> None:
        self._last_info = value

    def record_state(
        self,
        observation: Optional[np.ndarray],
        info: Optional[Dict[str, Any]],
    ) -> None:
        self.last_observation = observation
        self.last_info = info
