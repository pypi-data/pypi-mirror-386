
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
