"""XYSlider lane component."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal

from gradio_client.documentation import document

from gradio.components.base import Component, FormComponent
from gradio.components.number import Number
from gradio.events import Events
from gradio.i18n import I18nData

if TYPE_CHECKING:
    from gradio.components import Timer


class XYSlider(FormComponent):
    """
    Kaoss-pad style 2D XY controller with a single draggable point.

    The component renders a 2D canvas spanning [x_min, x_max] × [y_min, y_max].
    Users drag a single point to set the coordinates. The component's OUTPUT is a
    dictionary with keys:
      - "x": float — X coordinate in component domain
      - "y": float — Y coordinate in component domain
      - "bilinear": dict — weights for the four corners suitable for blending
        {"top_left", "top_right", "bottom_left", "bottom_right"}
        that sum to 1, computed from the normalized position.
    """

    EVENTS = [Events.change, Events.input, Events.release]

    def __init__(
        self,
        value: list[list[float]] | dict[str, Any] | Callable | None = None,
        *,
        x_min: float = 0.0,
        x_max: float = 1.0,
        y_min: float = 0.0,
        y_max: float = 1.0,
        precision: int | None = 3,
        audio_url: str | None = None,
        shade_enabled: bool = True,
        shade_above_color: str | None = "rgba(250, 204, 21, 0.25)",
        shade_below_color: str | None = "rgba(34, 197, 94, 0.25)",
        top_label: str | None = None,
        bottom_label: str | None = None,
        upper_left_label: str | None = None,
        upper_right_label: str | None = None,
        lower_right_label: str | None = None,
        lower_left_label: str | None = None,
        color_upper_left: str | None = "rgba(239, 68, 68, 0.9)",
        color_upper_right: str | None = "rgba(59, 130, 246, 0.9)",
        color_lower_right: str | None = "rgba(16, 185, 129, 0.9)",
        color_lower_left: str | None = "rgba(234, 179, 8, 0.9)",
        label: str | I18nData | None = None,
        info: str | I18nData | None = None,
        every: Timer | float | None = None,
        inputs: Component | Sequence[Component] | set[Component] | None = None,
        show_label: bool | None = None,
        container: bool = True,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = None,
        visible: bool | Literal["hidden"] = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
        preserved_by_key: list[str] | str | None = "value",
        show_reset_button: bool = True,
    ):
        """
        Parameters:
            value: Initial points list ([[x, y], ...]) or an object {"points": [[x,y],...], "audio_url": str}.
            x_min: Minimum x value of the canvas domain.
            x_max: Maximum x value of the canvas domain.
            y_min: Minimum y value of the canvas range.
            y_max: Maximum y value of the canvas range.
            precision: Number of decimal places to round values to when serializing.
            audio_url: Optional URL or path to an audio file to render waveform background.
            label, info, every, inputs, show_label, container, scale, min_width, interactive, visible, elem_id, elem_classes, render, key, preserved_by_key, show_reset_button: Standard component options.
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.precision = precision
        self.audio_url = audio_url
        self.shade_enabled = shade_enabled
        self.shade_above_color = shade_above_color
        self.shade_below_color = shade_below_color
        self.top_label = top_label
        self.bottom_label = bottom_label
        self.show_reset_button = show_reset_button
        # Corner labels for XY pad
        self.upper_left_label = upper_left_label
        self.upper_right_label = upper_right_label
        self.lower_right_label = lower_right_label
        self.lower_left_label = lower_left_label
        # Corner colors for bilinear background visualization
        self.color_upper_left = color_upper_left
        self.color_upper_right = color_upper_right
        self.color_lower_right = color_lower_right
        self.color_lower_left = color_lower_left
        super().__init__(
            label=label,
            info=info,
            every=every,
            inputs=inputs,
            show_label=show_label,
            container=container,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            render=render,
            key=key,
            preserved_by_key=preserved_by_key,
            value=value,
        )

    def api_info(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "X coordinate"},
                "y": {"type": "number", "description": "Y coordinate"},
                "bilinear": {
                    "type": "object",
                    "properties": {
                        "top_left": {"type": "number"},
                        "top_right": {"type": "number"},
                        "bottom_left": {"type": "number"},
                        "bottom_right": {"type": "number"},
                    },
                    "required": [
                        "top_left",
                        "top_right",
                        "bottom_left",
                        "bottom_right",
                    ],
                },
            },
            "required": ["x", "y", "bilinear"],
            "description": "XY pad output with bilinear corner weights that sum to 1.",
        }

    def example_payload(self) -> Any:
        return {
            "x": 0.5,
            "y": 0.5,
            "bilinear": {
                "top_left": 0.25,
                "top_right": 0.25,
                "bottom_left": 0.25,
                "bottom_right": 0.25,
            },
        }

    def example_value(self) -> Any:
        return self.example_payload()

    @staticmethod
    def _round(value: float | None, precision: int | None) -> float:
        if value is None:
            return 0.0
        if precision is None:
            return float(value)
        return round(float(value), precision)

    def postprocess(self, value: Any) -> dict[str, Any] | list[list[float]]:
        """
        Accepts either a dict {x, y, bilinear?} or any value with x/y.
        Returns a dict with rounded x/y and computed bilinear weights, plus
        rendering props for the frontend.
        """
        if value is None:
            # Default to center
            cx = self._round((self.x_min + self.x_max) / 2.0, self.precision)
            cy = self._round((self.y_min + self.y_max) / 2.0, self.precision)
        elif isinstance(value, dict) and "x" in value and "y" in value:
            cx = self._round(float(value.get("x", 0.0)), self.precision)
            cy = self._round(float(value.get("y", 0.0)), self.precision)
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            # Support [x, y]
            cx = self._round(float(value[0]), self.precision)
            cy = self._round(float(value[1]), self.precision)
        else:
            cx = self._round((self.x_min + self.x_max) / 2.0, self.precision)
            cy = self._round((self.y_min + self.y_max) / 2.0, self.precision)

        # Clamp
        cx = max(self.x_min, min(self.x_max, cx))
        cy = max(self.y_min, min(self.y_max, cy))

        bilinear = self._compute_bilinear(cx, cy)

        payload: dict[str, Any] = {
            "x": cx,
            "y": cy,
            "bilinear": bilinear,
            # Include axis/bounds so frontend can render consistently
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "shade_enabled": self.shade_enabled,
        }
        # Include corner labels/colors if available
        if self.upper_left_label is not None:
            payload["upper_left_label"] = self.upper_left_label
        if self.upper_right_label is not None:
            payload["upper_right_label"] = self.upper_right_label
        if self.lower_right_label is not None:
            payload["lower_right_label"] = self.lower_right_label
        if self.lower_left_label is not None:
            payload["lower_left_label"] = self.lower_left_label
        if self.color_upper_left is not None:
            payload["color_upper_left"] = self.color_upper_left
        if self.color_upper_right is not None:
            payload["color_upper_right"] = self.color_upper_right
        if self.color_lower_right is not None:
            payload["color_lower_right"] = self.color_lower_right
        if self.color_lower_left is not None:
            payload["color_lower_left"] = self.color_lower_left
        if self.shade_above_color is not None:
            payload["shade_above_color"] = self.shade_above_color
        if self.shade_below_color is not None:
            payload["shade_below_color"] = self.shade_below_color
        if self.top_label is not None:
            payload["top_label"] = self.top_label
        if self.bottom_label is not None:
            payload["bottom_label"] = self.bottom_label
        return payload

    def preprocess(self, payload: Any) -> dict[str, Any]:
        """
        Parameters:
            payload: dict with keys {x, y}. Optionally includes a client-computed
                     "bilinear" field which will be ignored and recomputed.
        Returns:
            Dict with rounded {x, y, bilinear} to pass to the user's function.
        """
        if not isinstance(payload, dict):
            return {
                "x": Number.round_to_precision((self.x_min + self.x_max) / 2.0, self.precision),
                "y": Number.round_to_precision((self.y_min + self.y_max) / 2.0, self.precision),
                "bilinear": self._compute_bilinear(
                    Number.round_to_precision((self.x_min + self.x_max) / 2.0, self.precision),
                    Number.round_to_precision((self.y_min + self.y_max) / 2.0, self.precision),
                ),
            }

        x_raw = float(payload.get("x", (self.x_min + self.x_max) / 2.0))
        y_raw = float(payload.get("y", (self.y_min + self.y_max) / 2.0))

        # Clamp to bounds
        x = max(self.x_min, min(self.x_max, x_raw))
        y = max(self.y_min, min(self.y_max, y_raw))

        x_rounded = Number.round_to_precision(x, self.precision)
        y_rounded = Number.round_to_precision(y, self.precision)
        return {
            "x": x_rounded,
            "y": y_rounded,
            "bilinear": self._compute_bilinear(x_rounded, y_rounded),
        }

    def read_from_flag(self, payload: Any):
        """Points arrays are stored as strings in the flagging file; parse as JSON."""
        return json.loads(payload)

    def _compute_bilinear(self, x: float, y: float) -> dict[str, float]:
        """Compute bilinear weights for the four corners based on x, y in bounds.

        Returns a dict with keys: top_left, top_right, bottom_left, bottom_right.
        Weights sum to 1.0.
        """
        x_span = (self.x_max - self.x_min) or 1.0
        y_span = (self.y_max - self.y_min) or 1.0
        u = (x - self.x_min) / x_span
        v = (y - self.y_min) / y_span
        # v: 0 bottom, 1 top, consistent with drawing logic
        top_left = (1.0 - u) * v
        top_right = u * v
        bottom_left = (1.0 - u) * (1.0 - v)
        bottom_right = u * (1.0 - v)
        return {
            "top_left": float(self._round(top_left, self.precision)),
            "top_right": float(self._round(top_right, self.precision)),
            "bottom_left": float(self._round(bottom_left, self.precision)),
            "bottom_right": float(self._round(bottom_right, self.precision)),
        }
