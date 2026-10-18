import type { GuideSidecar, GuideStep } from "./types";

interface Click {
	timeMs: number;
	cx: number;
	cy: number;
}

/**
 * One step per click. The window title is the last one reported at or before the click
 * (the click's own effect, such as a dialog opening, must not rename it); the keys are
 * everything typed after the previous click up to this one.
 *
 * Without a sidecar (capture off, or a platform with no provider) the steps still exist,
 * just without title and keys.
 */
export function buildSteps(
	clicks: Click[],
	sidecar: GuideSidecar | null,
	createId: (prefix: string) => string,
): GuideStep[] {
	const windows = [...(sidecar?.windows ?? [])].sort((a, b) => a.timeMs - b.timeMs);
	const keys = [...(sidecar?.keys ?? [])].sort((a, b) => a.timeMs - b.timeMs);
	const ordered = [...clicks].sort((a, b) => a.timeMs - b.timeMs);

	let previousClickMs = -Infinity;
	return ordered.map((click) => {
		let title: string | undefined;
		for (const event of windows) {
			if (event.timeMs > click.timeMs) break;
			title = event.title;
		}
		const typed = keys
			.filter((event) => event.timeMs > previousClickMs && event.timeMs <= click.timeMs)
			.map((event) => event.key);
		previousClickMs = click.timeMs;
		return {
			id: createId("step"),
			timeMs: click.timeMs,
			cx: click.cx,
			cy: click.cy,
			...(title ? { windowTitle: title } : {}),
			...(typed.length > 0 ? { keys: typed.join(" ") } : {}),
		};
	});
}

/** The sidecar is a file on disk: keep only well-formed events, drop anything else. */
export function parseGuideSidecar(raw: unknown): GuideSidecar | null {
	if (!raw || typeof raw !== "object") return null;
	const value = raw as Record<string, unknown>;
	if (value.version !== 1) return null;
	const list = (input: unknown) => (Array.isArray(input) ? input : []);
	const timed = (item: unknown): item is { timeMs: number } =>
		!!item && typeof item === "object" && Number.isFinite((item as { timeMs?: unknown }).timeMs);
	return {
		version: 1,
		keysCaptured: value.keysCaptured === true,
		windows: list(value.windows).filter(
			(item): item is GuideSidecar["windows"][number] =>
				timed(item) && typeof (item as { title?: unknown }).title === "string",
		),
		keys: list(value.keys).filter(
			(item): item is GuideSidecar["keys"][number] =>
				timed(item) && typeof (item as { key?: unknown }).key === "string",
		),
	};
}
