
import gradio as gr
from app import demo as app
import os

_docs = {'XYSlider': {'description': 'Kaoss-pad style 2D XY controller with a single draggable point.\n\nThe component renders a 2D canvas spanning [x_min, x_max] × [y_min, y_max].\nUsers drag a single point to set the coordinates. The component\'s OUTPUT is a\ndictionary with keys:\n  - "x": float — X coordinate in component domain\n  - "y": float — Y coordinate in component domain\n  - "bilinear": dict — weights for the four corners suitable for blending\n    {"top_left", "top_right", "bottom_left", "bottom_right"}\n    that sum to 1, computed from the normalized position.', 'members': {'__init__': {'value': {'type': 'list[list[float]] | dict[str, Any] | Callable | None', 'default': 'None', 'description': 'Initial points list ([[x, y], ...]) or an object {"points": [[x,y],...], "audio_url": str}.'}, 'x_min': {'type': 'float', 'default': '0.0', 'description': 'Minimum x value of the canvas domain.'}, 'x_max': {'type': 'float', 'default': '1.0', 'description': 'Maximum x value of the canvas domain.'}, 'y_min': {'type': 'float', 'default': '0.0', 'description': 'Minimum y value of the canvas range.'}, 'y_max': {'type': 'float', 'default': '1.0', 'description': 'Maximum y value of the canvas range.'}, 'precision': {'type': 'int | None', 'default': '3', 'description': 'Number of decimal places to round values to when serializing.'}, 'audio_url': {'type': 'str | None', 'default': 'None', 'description': 'Optional URL or path to an audio file to render waveform background.'}, 'shade_enabled': {'type': 'bool', 'default': 'True', 'description': None}, 'shade_above_color': {'type': 'str | None', 'default': '"rgba(250, 204, 21, 0.25)"', 'description': None}, 'shade_below_color': {'type': 'str | None', 'default': '"rgba(34, 197, 94, 0.25)"', 'description': None}, 'top_label': {'type': 'str | None', 'default': 'None', 'description': None}, 'bottom_label': {'type': 'str | None', 'default': 'None', 'description': None}, 'upper_left_label': {'type': 'str | None', 'default': 'None', 'description': None}, 'upper_right_label': {'type': 'str | None', 'default': 'None', 'description': None}, 'lower_right_label': {'type': 'str | None', 'default': 'None', 'description': None}, 'lower_left_label': {'type': 'str | None', 'default': 'None', 'description': None}, 'color_upper_left': {'type': 'str | None', 'default': '"rgba(239, 68, 68, 0.9)"', 'description': None}, 'color_upper_right': {'type': 'str | None', 'default': '"rgba(59, 130, 246, 0.9)"', 'description': None}, 'color_lower_right': {'type': 'str | None', 'default': '"rgba(16, 185, 129, 0.9)"', 'description': None}, 'color_lower_left': {'type': 'str | None', 'default': '"rgba(234, 179, 8, 0.9)"', 'description': None}, 'label': {'type': 'str | I18nData | None', 'default': 'None', 'description': None}, 'info': {'type': 'str | I18nData | None', 'default': 'None', 'description': None}, 'every': {'type': 'Timer | float | None', 'default': 'None', 'description': None}, 'inputs': {'type': 'Component | Sequence[Component] | set[Component] | None', 'default': 'None', 'description': None}, 'show_label': {'type': 'bool | None', 'default': 'None', 'description': None}, 'container': {'type': 'bool', 'default': 'True', 'description': None}, 'scale': {'type': 'int | None', 'default': 'None', 'description': None}, 'min_width': {'type': 'int', 'default': '160', 'description': None}, 'interactive': {'type': 'bool | None', 'default': 'None', 'description': None}, 'visible': {'type': 'bool | Literal["hidden"]', 'default': 'True', 'description': None}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': None}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': None}, 'render': {'type': 'bool', 'default': 'True', 'description': None}, 'key': {'type': 'int | str | tuple[int | str, ...] | None', 'default': 'None', 'description': None}, 'preserved_by_key': {'type': 'list[str] | str | None', 'default': '"value"', 'description': None}, 'show_reset_button': {'type': 'bool', 'default': 'True', 'description': 'Standard component options.'}}, 'postprocess': {'value': {'type': 'typing.Any', 'description': None}}, 'preprocess': {'return': {'type': 'dict[str, typing.Any]', 'description': "Dict with rounded {x, y, bilinear} to pass to the user's function."}, 'value': None}}, 'events': {'change': {'type': None, 'default': None, 'description': 'Triggered when the value of the XYSlider changes either because of user input (e.g. a user types in a textbox) OR because of a function update (e.g. an image receives a value from the output of an event trigger). See `.input()` for a listener that is only triggered by user input.'}, 'input': {'type': None, 'default': None, 'description': 'This listener is triggered when the user changes the value of the XYSlider.'}, 'release': {'type': None, 'default': None, 'description': 'This listener is triggered when the user releases the mouse on this XYSlider.'}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'XYSlider': []}}}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
"""
# `gradio_xyslider`

<div style="display: flex; gap: 7px;">
<img alt="Static Badge" src="https://img.shields.io/badge/version%20-%200.0.1%20-%20orange">  
</div>

Python library for easily interacting with trained machine learning models
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_xyslider
```

## Usage

```python

import os
import sys
import gradio as gr


from gradio_xyslider import XYSlider


def passthrough(payload):
    # Just echo the xy + bilinear dict
    return payload


with gr.Blocks() as demo:
    gr.Markdown("## XY Pad Demo")
    with gr.Row():
        audio = gr.Audio(label="Audio", sources=["upload", "microphone"], type="filepath")
    with gr.Row():
        lane = XYSlider(
            label="XY Pad",
            x_min=0.0,
            x_max=1.0,
            y_min=0.0,
            y_max=1.0,
            upper_left_label="Upper Left",
            upper_right_label="Upper Right",
            lower_right_label="Lower Right",
            lower_left_label="Lower Left",
            color_upper_left="rgba(239, 68, 68, 0.9)",  # red
            color_upper_right="rgba(59, 130, 246, 0.9)",  # blue
            color_lower_right="rgba(16, 185, 129, 0.9)",  # emerald
            color_lower_left="rgba(234, 179, 8, 0.9)",  # yellow
        )

    # Remove waveform linkage for now

    # Echo xy + bilinear on release
    out = gr.JSON(label="Current XY + Bilinear")
    lane.release(fn=passthrough, inputs=lane, outputs=out)


if __name__ == "__main__":
    demo.launch(share=True)

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `XYSlider`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["XYSlider"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["XYSlider"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, dict with rounded {x, y, bilinear} to pass to the user's function.


 ```python
def predict(
    value: dict[str, typing.Any]
) -> typing.Any:
    return value
```
""", elem_classes=["md-custom", "XYSlider-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          XYSlider: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""")

demo.launch()
