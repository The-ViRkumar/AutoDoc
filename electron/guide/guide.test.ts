import { describe, expect, it } from "vitest";
import { shiftSidecar } from "./session";
import { buildProbeCommand, parseProbeLine, toGuideEvent } from "./windowsProbe";

describe("parseProbeLine", () => {
	it("reads window and key lines, keeping tabs inside the value", () => {
		expect(parseProbeLine("T\t1000\tNotepad\r")).toEqual({
			kind: "window",
			epochMs: 1000,
			title: "Notepad",
		});
		expect(parseProbeLine("K\t1010\ta")).toEqual({ kind: "key", epochMs: 1010, key: "a" });
	});

	it("ignores noise such as PowerShell progress output", () => {
		expect(parseProbeLine("#< CLIXML")).toBeNull();
		expect(parseProbeLine("K\tnope\ta")).toBeNull();
		expect(parseProbeLine("K\t5\t")).toBeNull();
	});
});

describe("toGuideEvent", () => {
	it("is relative to the take start and never negative", () => {
		expect(toGuideEvent({ kind: "key", epochMs: 1500, key: "x" }, 1000)).toEqual({
			key: { timeMs: 500, key: "x" },
		});
		expect(toGuideEvent({ kind: "window", epochMs: 900, title: "t" }, 1000)).toEqual({
			window: { timeMs: 0, title: "t" },
		});
	});
});

describe("shiftSidecar", () => {
	it("moves every event by the video offset, like the cursor telemetry", () => {
		const shifted = shiftSidecar(
			{
				version: 1,
				keysCaptured: true,
				windows: [{ timeMs: 800, title: "a" }],
				keys: [{ timeMs: 300, key: "b" }],
			},
			325,
		);
		expect(shifted.windows[0].timeMs).toBe(475);
		expect(shifted.keys[0].timeMs).toBe(0);
	});
});

describe("buildProbeCommand", () => {
	it("encodes the key switch into the script", () => {
		const decode = (keys: boolean) =>
			Buffer.from(buildProbeCommand(keys), "base64").toString("utf16le");
		expect(decode(true)).toContain("[AutoDocProbe]::Run($true)");
		expect(decode(false)).toContain("[AutoDocProbe]::Run($false)");
	});
});
