import { describe, expect, it } from "vitest";
import { buildSteps, parseGuideSidecar } from "./buildSteps";
import type { GuideSidecar } from "./types";

let n = 0;
const id = (prefix: string) => `${prefix}_${++n}`;

const sidecar: GuideSidecar = {
	version: 1,
	keysCaptured: true,
	windows: [
		{ timeMs: 0, title: "Desktop" },
		{ timeMs: 1000, title: "Settings" },
		{ timeMs: 2600, title: "Save As" },
	],
	keys: [
		{ timeMs: 1200, key: "a" },
		{ timeMs: 1300, key: "b" },
		{ timeMs: 2500, key: "[Enter]" },
	],
};

describe("buildSteps", () => {
	it("uses the window active at the click, not the one the click opened", () => {
		const steps = buildSteps([{ timeMs: 2550, cx: 0.5, cy: 0.5 }], sidecar, id);
		expect(steps[0].windowTitle).toBe("Settings");
	});

	it("attaches keys typed since the previous click, space-separated", () => {
		const steps = buildSteps(
			[
				{ timeMs: 1100, cx: 0.1, cy: 0.1 },
				{ timeMs: 2550, cx: 0.2, cy: 0.2 },
			],
			sidecar,
			id,
		);
		expect(steps[0].keys).toBeUndefined();
		expect(steps[1].keys).toBe("a b [Enter]");
	});

	it("sorts clicks by time", () => {
		const steps = buildSteps(
			[
				{ timeMs: 3000, cx: 0, cy: 0 },
				{ timeMs: 500, cx: 0, cy: 0 },
			],
			null,
			id,
		);
		expect(steps.map((s) => s.timeMs)).toEqual([500, 3000]);
	});

	it("still makes steps with no sidecar", () => {
		const [step] = buildSteps([{ timeMs: 10, cx: 0.3, cy: 0.4 }], null, id);
		expect(step).toMatchObject({ timeMs: 10, cx: 0.3, cy: 0.4 });
		expect(step.windowTitle).toBeUndefined();
		expect(step.keys).toBeUndefined();
	});
});

describe("parseGuideSidecar", () => {
	it("keeps good events and drops malformed ones", () => {
		const parsed = parseGuideSidecar({
			version: 1,
			keysCaptured: true,
			windows: [{ timeMs: 1, title: "ok" }, { timeMs: "x", title: "bad" }, null],
			keys: [{ timeMs: 2, key: "a" }, { timeMs: 3 }],
		});
		expect(parsed?.windows).toEqual([{ timeMs: 1, title: "ok" }]);
		expect(parsed?.keys).toEqual([{ timeMs: 2, key: "a" }]);
	});

	it("rejects other versions and non-objects", () => {
		expect(parseGuideSidecar({ version: 2 })).toBeNull();
		expect(parseGuideSidecar("nope")).toBeNull();
	});
});
