// One guide capture per take. It starts, stops, shifts and is written beside the
// video exactly where the cursor telemetry is (see the wrappers in ipc/handlers.ts),
// so the two sidecars share a time axis.

import type { ChildProcess } from "node:child_process";
import fs from "node:fs/promises";
import type { GuideSidecar } from "../../src/lib/guide/types";
import { spawnWindowsProbe, toGuideEvent } from "./windowsProbe";

export interface GuideCapturePrefs {
	enabled: boolean;
	captureKeys: boolean;
}

let readPrefs: () => GuideCapturePrefs = () => ({ enabled: false, captureKeys: false });
let probe: ChildProcess | null = null;
let live: GuideSidecar | null = null;
let pending: GuideSidecar | null = null;

export function setGuideCapturePrefsReader(reader: () => GuideCapturePrefs): void {
	readPrefs = reader;
}

export function startGuideCapture(startEpochMs: number = Date.now()): void {
	stopGuideCapture();
	pending = null;
	const prefs = readPrefs();
	// ponytail: Windows only. macOS and Linux get no sidecar, so their steps carry no
	// title or keys; add a provider here when those platforms are taken on.
	if (process.platform !== "win32" || !prefs.enabled) return;
	const sidecar: GuideSidecar = {
		version: 1,
		keysCaptured: prefs.captureKeys,
		windows: [],
		keys: [],
	};
	live = sidecar;
	try {
		probe = spawnWindowsProbe(prefs.captureKeys, (event) => {
			const mapped = toGuideEvent(event, startEpochMs);
			if ("window" in mapped) sidecar.windows.push(mapped.window);
			else sidecar.keys.push(mapped.key);
		});
		probe.on("error", (error) => console.warn("[guide] probe failed:", error));
	} catch (error) {
		console.warn("[guide] could not start the window probe:", error);
		probe = null;
		live = null;
	}
}

export function stopGuideCapture(): void {
	if (probe) {
		probe.kill();
		probe = null;
	}
	if (live) {
		pending = live;
		live = null;
	}
}

/** Mirrors `shiftPendingCursorTelemetry`: the video starts `offsetMs` after the capture clock. */
export function shiftSidecar(sidecar: GuideSidecar, offsetMs: number): GuideSidecar {
	const shift = <T extends { timeMs: number }>(items: T[]) =>
		items.map((item) => ({ ...item, timeMs: Math.max(0, item.timeMs - offsetMs) }));
	return { ...sidecar, windows: shift(sidecar.windows), keys: shift(sidecar.keys) };
}

export function shiftGuideCapture(offsetMs: number): void {
	if (!pending || !Number.isFinite(offsetMs) || offsetMs <= 0) return;
	pending = shiftSidecar(pending, offsetMs);
}

export async function writeGuideSidecar(videoPath: string): Promise<void> {
	const sidecar = pending;
	pending = null;
	if (!sidecar || sidecar.windows.length === 0) return;
	await fs.writeFile(`${videoPath}.guide.json`, JSON.stringify(sidecar), "utf-8");
}
