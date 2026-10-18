// Guide capture data shared by the main process (writes the sidecar) and the
// renderer (turns it into steps). Times are ms from the start of the take, the
// same axis as the `.cursor.json` sidecar, so the two line up without conversion.

export interface GuideWindowEvent {
	timeMs: number;
	/** Title of the foreground window from this moment until the next event. */
	title: string;
}

export interface GuideKeyEvent {
	timeMs: number;
	/** Printable character as typed, or a bracketed name such as `[Enter]`. */
	key: string;
}

/** `${video}.guide.json` */
export interface GuideSidecar {
	version: 1;
	/** False when the user left key capture off; `keys` is then always empty. */
	keysCaptured: boolean;
	windows: GuideWindowEvent[];
	keys: GuideKeyEvent[];
}

export interface GuideStep {
	id: string;
	/** Click time on the recording, ms. */
	timeMs: number;
	/** Click position, 0..1 across the recorded display. */
	cx: number;
	cy: number;
	windowTitle?: string;
	/** Keys typed since the previous click, space-separated. */
	keys?: string;
	/** Manual caption; empty means "generate at export" (Phase 6). */
	caption?: string;
}
