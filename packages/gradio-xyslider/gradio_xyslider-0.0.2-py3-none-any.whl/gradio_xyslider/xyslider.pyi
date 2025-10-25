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

from gradio.events import Dependency

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
        # Include corner labels/colors; prefer dynamic values from 'value' dict if provided
        dyn_ul = value.get("upper_left_label") if isinstance(value, dict) else None
        dyn_ur = value.get("upper_right_label") if isinstance(value, dict) else None
        dyn_lr = value.get("lower_right_label") if isinstance(value, dict) else None
        dyn_ll = value.get("lower_left_label") if isinstance(value, dict) else None
        dyn_c_ul = value.get("color_upper_left") if isinstance(value, dict) else None
        dyn_c_ur = value.get("color_upper_right") if isinstance(value, dict) else None
        dyn_c_lr = value.get("color_lower_right") if isinstance(value, dict) else None
        dyn_c_ll = value.get("color_lower_left") if isinstance(value, dict) else None

        ul = dyn_ul if isinstance(dyn_ul, str) else self.upper_left_label
        ur = dyn_ur if isinstance(dyn_ur, str) else self.upper_right_label
        lr = dyn_lr if isinstance(dyn_lr, str) else self.lower_right_label
        ll = dyn_ll if isinstance(dyn_ll, str) else self.lower_left_label
        c_ul = dyn_c_ul if isinstance(dyn_c_ul, str) else self.color_upper_left
        c_ur = dyn_c_ur if isinstance(dyn_c_ur, str) else self.color_upper_right
        c_lr = dyn_c_lr if isinstance(dyn_c_lr, str) else self.color_lower_right
        c_ll = dyn_c_ll if isinstance(dyn_c_ll, str) else self.color_lower_left

        if ul is not None:
            payload["upper_left_label"] = ul
        if ur is not None:
            payload["upper_right_label"] = ur
        if lr is not None:
            payload["lower_right_label"] = lr
        if ll is not None:
            payload["lower_left_label"] = ll
        if c_ul is not None:
            payload["color_upper_left"] = c_ul
        if c_ur is not None:
            payload["color_upper_right"] = c_ur
        if c_lr is not None:
            payload["color_lower_right"] = c_lr
        if c_ll is not None:
            payload["color_lower_left"] = c_ll
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
    from typing import Callable, Literal, Sequence, Any, TYPE_CHECKING
    from gradio.blocks import Block
    if TYPE_CHECKING:
        from gradio.components import Timer
        from gradio.components.base import Component

    
    def change(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
        api_description: str | None | Literal[False] = None,
        validator: Callable[..., Any] | None = None,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
            key: A unique key for this event listener to be used in @gr.render(). If set, this value identifies an event as identical across re-renders when the key is identical.
            api_description: Description of the API endpoint. Can be a string, None, or False. If set to a string, the endpoint will be exposed in the API docs with the given description. If None, the function's docstring will be used as the API endpoint description. If False, then no description will be displayed in the API docs.
            validator: Optional validation function to run before the main function. If provided, this function will be executed first with queue=False, and only if it completes successfully will the main function be called. The validator receives the same inputs as the main function.
        
        """
        ...
    
    def input(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
        api_description: str | None | Literal[False] = None,
        validator: Callable[..., Any] | None = None,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
            key: A unique key for this event listener to be used in @gr.render(). If set, this value identifies an event as identical across re-renders when the key is identical.
            api_description: Description of the API endpoint. Can be a string, None, or False. If set to a string, the endpoint will be exposed in the API docs with the given description. If None, the function's docstring will be used as the API endpoint description. If False, then no description will be displayed in the API docs.
            validator: Optional validation function to run before the main function. If provided, this function will be executed first with queue=False, and only if it completes successfully will the main function be called. The validator receives the same inputs as the main function.
        
        """
        ...
    
    def release(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
        api_description: str | None | Literal[False] = None,
        validator: Callable[..., Any] | None = None,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
            key: A unique key for this event listener to be used in @gr.render(). If set, this value identifies an event as identical across re-renders when the key is identical.
            api_description: Description of the API endpoint. Can be a string, None, or False. If set to a string, the endpoint will be exposed in the API docs with the given description. If None, the function's docstring will be used as the API endpoint description. If False, then no description will be displayed in the API docs.
            validator: Optional validation function to run before the main function. If provided, this function will be executed first with queue=False, and only if it completes successfully will the main function be called. The validator receives the same inputs as the main function.
        
        """
        ...