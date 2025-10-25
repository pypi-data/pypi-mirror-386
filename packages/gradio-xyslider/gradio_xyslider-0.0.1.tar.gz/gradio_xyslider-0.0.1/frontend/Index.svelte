<script context="module">
	let _id = 0;
</script>

<script lang="ts">
	import type { Gradio } from "@gradio/utils";
	import { Block, BlockTitle } from "@gradio/atoms";
	import { StatusTracker } from "@gradio/statustracker";
	import type { LoadingStatus } from "@gradio/statustracker";
    import { afterUpdate, onMount } from "svelte";

    type Point = [number, number];

	export let gradio: Gradio<{
		change: never;
		input: never;
        release: any;
		clear_status: LoadingStatus;
	}>;
	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let visible: boolean | "hidden" = true;
    export let value: any = [];
	let initial_value = value;

    export let label = "XYSlider";
	export let info: string | undefined = undefined;
	export let container = true;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;

    // Axis bounds
    export let x_min: number = 0;
    export let x_max: number = 1;
    export let y_min: number = 0;
    export let y_max: number = 1;
    export let shade_enabled: boolean = true;
    export let shade_above_color: string = "rgba(250, 204, 21, 0.25)"; // yellow-400 @ 25%
    export let shade_below_color: string = "rgba(34, 197, 94, 0.25)"; // green-500 @ 25%
    export let top_label: string | null = null;
    export let bottom_label: string | null = null;
    // Corner labels/colors for XY pad
    let upper_left_label: string | null = null;
    let upper_right_label: string | null = null;
    let lower_right_label: string | null = null;
    let lower_left_label: string | null = null;
    let color_upper_left: string = "rgba(239, 68, 68, 0.9)"; // red
    let color_upper_right: string = "rgba(59, 130, 246, 0.9)"; // blue
    let color_lower_right: string = "rgba(16, 185, 129, 0.9)"; // emerald
    let color_lower_left: string = "rgba(234, 179, 8, 0.9)"; // yellow
	export let show_label: boolean;
	export let interactive: boolean;
	export let loading_status: LoadingStatus;
	export let value_is_output = false;
	export let show_reset_button: boolean;

    const id = `xyslider_${_id++}`;
    const yMinId = `${id}_ymin`;
    const yMaxId = `${id}_ymax`;

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null = null;
    let width = 0;
    let height = 0;
    let devicePixelRatio = 1;
    let window_width: number = 0;

    let points: Point[] = [];
    let initial_points: Point[] = [];

    // Track props normalization (we now normalize once on mount)

    // Drag state for Command-drag to shift all points vertically
    let isDraggingAll = false;
    let dragStartPy = 0;
    let dragStartPoints: Point[] = [];

    // Hover/selection and single-point dragging
    let hoveredIndex: number | null = null;
    let selectedIndex: number | null = null;
    let isDraggingPoint = false;
    let dragPointIndex: number | null = null;
    const hoverRadiusPx = 6;

    function enforceYBounds(): void {
        if (y_min >= y_max) {
            // maintain a minimal range
            y_max = y_min + 1e-6;
        }
    }

    function clampPointsToY(): void {
        points = points.map(([x, y]) => [x, Math.max(y_min, Math.min(y_max, y))] as Point);
    }

    function normalizeIncomingValue(): void {
        // Accept {x, y, ...} from backend or legacy {points}
        if (value && typeof value === "object" && !Array.isArray(value)) {
            if (typeof value.x === "number" && typeof value.y === "number") {
                points = [[value.x, value.y]];
            } else if (Array.isArray(value.points) && value.points.length > 0) {
                const p = value.points[0];
                if (Array.isArray(p) && p.length === 2) points = [[p[0], p[1]]];
            }
            if (typeof value.x_min === "number") x_min = value.x_min;
            if (typeof value.x_max === "number") x_max = value.x_max;
            if (typeof value.y_min === "number") y_min = value.y_min;
            if (typeof value.y_max === "number") y_max = value.y_max;
            if (typeof value.shade_enabled === "boolean") shade_enabled = value.shade_enabled;
            if (typeof value.shade_above_color === "string") shade_above_color = value.shade_above_color;
            if (typeof value.shade_below_color === "string") shade_below_color = value.shade_below_color;
            if (typeof value.top_label === "string") top_label = value.top_label;
            if (typeof value.bottom_label === "string") bottom_label = value.bottom_label;
            if (typeof value.upper_left_label === "string") upper_left_label = value.upper_left_label;
            if (typeof value.upper_right_label === "string") upper_right_label = value.upper_right_label;
            if (typeof value.lower_right_label === "string") lower_right_label = value.lower_right_label;
            if (typeof value.lower_left_label === "string") lower_left_label = value.lower_left_label;
            if (typeof value.color_upper_left === "string") color_upper_left = value.color_upper_left;
            if (typeof value.color_upper_right === "string") color_upper_right = value.color_upper_right;
            if (typeof value.color_lower_right === "string") color_lower_right = value.color_lower_right;
            if (typeof value.color_lower_left === "string") color_lower_left = value.color_lower_left;
        } else if (Array.isArray(value) && value.length === 2) {
            const [vx, vy] = value as [number, number];
            points = [[vx, vy]];
        }
        ensureBaseline();
        initial_points = points.map((p) => [p[0], p[1]] as Point);
    }

    function sortUniqueByX(arr: Point[]): Point[] {
        const map = new Map<number, number>();
        for (const [x, y] of arr) map.set(x, y);
        return Array.from(map.entries())
            .sort((a, b) => a[0] - b[0])
            .map(([x, y]) => [x, y]);
    }

	function handle_change(): void {
		gradio.dispatch("change");
		if (!value_is_output) {
			gradio.dispatch("input");
		}
	}

    function handle_release(): void {
        value_is_output = true;
        const payload = currentPayload();
        value = payload;
        gradio.dispatch("release", payload);
    }

	function handle_resize(): void {
		window_width = window.innerWidth;
        resizeCanvas();
        draw();
	}

	function reset_value(): void {
		points = [];
		ensureBaseline();
		draw();
		gradio.dispatch("change");
		handle_release();
	}

    function resizeCanvas(): void {
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        devicePixelRatio = window.devicePixelRatio || 1;
        width = Math.max(1, Math.floor(rect.width));
        height = Math.max(120, Math.floor(rect.height));
        canvas.width = Math.floor(width * devicePixelRatio);
        canvas.height = Math.floor(height * devicePixelRatio);
        if (!ctx) ctx = canvas.getContext("2d");
        if (ctx) ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    }

    function toPxX(x: number): number {
        const span = x_max - x_min || 1;
        return ((x - x_min) / span) * width;
    }
    function toPxY(y: number): number {
        const span = y_max - y_min || 1;
        return height - ((y - y_min) / span) * height;
    }
    function fromPxX(px: number): number {
        const span = x_max - x_min || 1;
        return x_min + (px / width) * span;
    }
    function fromPxY(py: number): number {
        const span = y_max - y_min || 1;
        return y_min + ((height - py) / height) * span;
    }

    function computeBilinear(x: number, y: number) {
        const xspan = (x_max - x_min) || 1;
        const yspan = (y_max - y_min) || 1;
        const u = (x - x_min) / xspan;
        const v = (y - y_min) / yspan; // 0 bottom, 1 top
        const top_left = (1 - u) * v;
        const top_right = u * v;
        const bottom_left = (1 - u) * (1 - v);
        const bottom_right = u * (1 - v);
        return { top_left, top_right, bottom_left, bottom_right };
    }

    function currentPayload() {
        if (points.length === 0) {
            const cx = x_min + (x_max - x_min) * 0.5;
            const cy = y_min + (y_max - y_min) * 0.5;
            return { x: cx, y: cy, bilinear: computeBilinear(cx, cy) };
        }
        const [x, y] = points[0];
        return { x, y, bilinear: computeBilinear(x, y) };
    }

    function drawGrid(): void {
        if (!ctx) return;
        ctx.clearRect(0, 0, width, height);
        // Draw bilinear gradient background using a coarse grid
        drawBilinearBackground();

        ctx.strokeStyle = "#e5e7eb"; // neutral-200
        ctx.lineWidth = 1;
        const numLines = 8;
        for (let i = 1; i < numLines; i++) {
            const y = (i / numLines) * height;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Corner labels
        ctx.fillStyle = "#111827"; // neutral-900
        ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial";
        ctx.textBaseline = "top";
        if (upper_left_label) ctx.fillText(upper_left_label, 8, 6);
        if (upper_right_label) {
            const tw = ctx.measureText(upper_right_label).width;
            ctx.fillText(upper_right_label, width - tw - 8, 6);
        }
        if (lower_left_label) {
            ctx.textBaseline = "bottom";
            ctx.fillText(lower_left_label, 8, height - 6);
        }
        if (lower_right_label) {
            const tw = ctx.measureText(lower_right_label).width;
            ctx.textBaseline = "bottom";
            ctx.fillText(lower_right_label, width - tw - 8, height - 6);
        }
    }

    // Waveform removed for now

    function drawShading(): void { return; }

    function lerpColor(a: [number, number, number], b: [number, number, number], t: number): [number, number, number] {
        return [
            Math.round(a[0] + (b[0] - a[0]) * t),
            Math.round(a[1] + (b[1] - a[1]) * t),
            Math.round(a[2] + (b[2] - a[2]) * t),
        ];
    }

    function parseRgb(color: string): [number, number, number] {
        // Supports rgba(r,g,b,a) or rgb(r,g,b)
        const m = color.match(/rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
        if (!m) return [200, 200, 200];
        return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3])];
    }

    function drawBilinearBackground(): void {
        if (!ctx) return;
        const tl = parseRgb(color_upper_left);
        const tr = parseRgb(color_upper_right);
        const br = parseRgb(color_lower_right);
        const bl = parseRgb(color_lower_left);
        const cells = 32; // coarse resolution
        const cellW = width / cells;
        const cellH = height / cells;
        for (let j = 0; j < cells; j++) {
            for (let i = 0; i < cells; i++) {
                const u = i / (cells - 1);
                const v = 1 - j / (cells - 1); // canvas y is inverted
                const top = lerpColor(tl, tr, u);
                const bottom = lerpColor(bl, br, u);
                const rgb = lerpColor(bottom, top, v);
                ctx.fillStyle = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
                ctx.fillRect(i * cellW, j * cellH, Math.ceil(cellW) + 1, Math.ceil(cellH) + 1);
            }
        }
        // Grid lines overlay for reference
        ctx.strokeStyle = "#e5e7eb";
        ctx.lineWidth = 1;
        const numLines = 8;
        for (let i = 1; i < numLines; i++) {
            const y = (i / numLines) * height;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        for (let i = 1; i < numLines; i++) {
            const x = (i / numLines) * width;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
    }

    function drawPoints(): void {
        if (!ctx) return;
        if (points.length === 0) return;
        const [x, y] = points[0];
        const px = toPxX(x);
        const py = toPxY(y);

        // Crosshair
        ctx.strokeStyle = "#111827";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(px, 0);
        ctx.lineTo(px, height);
        ctx.moveTo(0, py);
        ctx.lineTo(width, py);
        ctx.stroke();
        ctx.setLineDash([]);

        // Point
        ctx.fillStyle = "#111827";
        ctx.beginPath();
        ctx.arc(px, py, 5, 0, Math.PI * 2);
        ctx.fill();

        // Outline on hover/selected
        if (selectedIndex === 0 || hoveredIndex === 0) {
            ctx.beginPath();
            ctx.arc(px, py, 9, 0, Math.PI * 2);
            ctx.lineWidth = 2;
            ctx.strokeStyle = selectedIndex === 0 ? "#ffffff" : "#9ca3af";
            ctx.stroke();
        }

        // Label
        ctx.font = "11px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial";
        ctx.fillStyle = "#111827";
        ctx.textBaseline = "bottom";
        const label = `${x.toFixed(2)}, ${y.toFixed(2)}`;
        ctx.fillText(label, px + 8, Math.max(0, py - 8));
    }

    function draw(): void {
        if (!canvas) return;
        drawGrid();
        // Draw shading only
        drawShading();
        drawPoints();
    }

    function ensureBaseline(): void {
        if (!Array.isArray(points) || points.length === 0) {
            const midY = y_min + (y_max - y_min) * 0.5;
            const midX = x_min + (x_max - x_min) * 0.5;
            points = [[midX, midY]];
        } else if (points.length > 1) {
            points = [[points[0][0], points[0][1]]];
        }
    }

    function onPointerDown(e: PointerEvent): void {
        if (interactive === false) return;
        const rect = canvas.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        const x = Math.max(x_min, Math.min(x_max, fromPxX(px)));
        const y = Math.max(y_min, Math.min(y_max, fromPxY(py)));
        points = [[x, y]];
        selectedIndex = 0;
        hoveredIndex = 0;
        isDraggingPoint = true;
        dragPointIndex = 0;
        try { canvas.setPointerCapture(e.pointerId); } catch {}
        draw();
    }

    function onPointerMove(e: PointerEvent): void {
        if (interactive === false) return;
        const rect = canvas.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        if (isDraggingPoint && dragPointIndex !== null && selectedIndex !== null) {
            const x = Math.max(x_min, Math.min(x_max, fromPxX(px)));
            const y = Math.max(y_min, Math.min(y_max, fromPxY(py)));
            points[selectedIndex] = [x, y];
            draw();
            return;
        }
        // Hover detection when not dragging
        hoveredIndex = findPointNear(px, py, hoverRadiusPx);
        draw();
    }

    function onPointerUp(e: PointerEvent): void {
        if (isDraggingPoint) {
            isDraggingPoint = false;
            dragPointIndex = null;
        }
        handle_release();
        try { canvas.releasePointerCapture(e.pointerId); } catch {}
    }

    function findPointNear(px: number, py: number, radius: number): number | null {
        const r2 = radius * radius;
        let hit: number | null = null;
        for (let i = 0; i < points.length; i++) {
            const [x, y] = points[i];
            const dx = toPxX(x) - px;
            const dy = toPxY(y) - py;
            if (dx * dx + dy * dy <= r2) {
                hit = i;
                break;
            }
        }
        return hit;
    }

    // Reactivity
    $: disabled = interactive === false;
    // When y bounds change, enforce validity, clamp points, and redraw
    $: {
        enforceYBounds();
        clampPointsToY();
        ensureBaseline();
        draw();
    }
    // Keep component's value in sync with points so events carry the latest data
    // Avoid forcing value on every change; we only send points via release/input events
    // $: value = points;
    $: points, handle_change();

    // Waveform reactive logic removed

    onMount(() => {
        normalizeIncomingValue();
        resizeCanvas();
        draw();
        const ro = new ResizeObserver(() => {
            resizeCanvas();
            draw();
        });
        ro.observe(canvas);
        window.addEventListener("resize", handle_resize);
        return () => {
            ro.disconnect();
            window.removeEventListener("resize", handle_resize);
        };
    });

    afterUpdate(() => {
        value_is_output = false;
        draw();
    });
</script>

<svelte:window on:resize={handle_resize} />

<Block {visible} {elem_id} {elem_classes} {container} {scale} {min_width}>
	<StatusTracker
		autoscroll={gradio.autoscroll}
		i18n={gradio.i18n}
		{...loading_status}
		on:clear_status={() => gradio.dispatch("clear_status", loading_status)}
	/>

	<div class="wrap">
		<div class="head">
			<label for={id}>
				<BlockTitle {show_label} {info}>{label}</BlockTitle>
			</label>
			<div class="tab-like-container">
				{#if show_reset_button}
					<button
						class="reset-button"
						on:click={reset_value}
						{disabled}
						aria-label="Reset to default value"
						data-testid="reset-button"
					>
						↺
					</button>
				{/if}
			</div>
		</div>

        <!-- XY pad has fixed bounds UI removed for simplicity -->

        <div class="lane_container">
            <canvas
                bind:this={canvas}
                class="lane"
                on:pointerdown={onPointerDown}
                on:pointermove={onPointerMove}
                on:pointerup={onPointerUp}
                on:mouseleave={() => { if (!isDraggingPoint) { hoveredIndex = null; draw(); } }}
            ></canvas>
		</div>
	</div>
</Block>

<style>
	.wrap {
		display: flex;
		flex-direction: column;
		width: 100%;
	}

	.head {
		margin-bottom: var(--size-2);
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		flex-wrap: wrap;
		width: 100%;
	}

	.head > label {
		flex: 1;
	}

	.head > .tab-like-container {
		margin-left: auto;
		order: 1;
	}

    .lane_container {
        display: block;
		width: 100%;
        max-width: 300px; /* default max size */
        aspect-ratio: 1 / 1; /* keep square */
        height: auto;
        margin: 0 auto; /* center when not full width */
    }

    /* removed bounds inputs */

    .lane {
		width: 100%;
        height: 100%;
        display: block;
		background: transparent;
        border-radius: var(--radius-md);
        box-shadow: inset 0 0 0 1px var(--input-border-color);
        cursor: crosshair;
	}

	@media (max-width: 520px) {
		.head {
			gap: var(--size-3);
		}
	}

	@media (max-width: 420px) {
		.head .tab-like-container {
			margin-bottom: var(--size-4);
		}
	}

	.tab-like-container {
		display: flex;
		align-items: stretch;
		border: 1px solid var(--input-border-color);
		border-radius: var(--radius-sm);
		overflow: hidden;
		height: var(--size-6);
	}

	.reset-button {
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		border-left: 1px solid var(--input-border-color);
		cursor: pointer;
		font-size: var(--text-sm);
		color: var(--body-text-color);
		padding: 0 var(--size-2);
		min-width: var(--size-6);
		transition: background-color 0.15s ease-in-out;
	}

	.reset-button:hover:not(:disabled) {
		background-color: var(--background-fill-secondary);
	}

	.reset-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
