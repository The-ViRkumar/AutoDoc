// Regenerates every AutoDoc app icon from logo.svg using Electron's own Chromium, so no image
// library is needed. Run from the repo root:
//   node_modules/electron/dist/electron.exe autodoc-project/brand/generate-icons.cjs
// Writes: icons/icons/png/*.png, icons/icons/win/icon.ico, icons/icons/mac/icon.icns and
// public/autodoc.png (tray + empty-state art) and src/assets/autodoc-mark.png (editor top bar).
const { app, BrowserWindow } = require("electron");
const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const SVG = fs.readFileSync(path.join(__dirname, "logo.svg"), "utf8");

const PNG_SIZES = [16, 24, 32, 48, 64, 128, 256, 512, 1024];
const ICO_SIZES = [16, 24, 32, 48, 64, 128, 256];
const ICNS_TYPES = { 128: "ic07", 256: "ic08", 512: "ic09", 1024: "ic10" };
// macOS draws app icons inside a transparent margin (about 10% per side).
const MAC_MARGIN = 0.0977;

/** Rasterises the SVG inside a hidden window; returns { key: base64 PNG }. */
async function render(jobs) {
	const win = new BrowserWindow({ show: false });
	await win.loadURL("about:blank");
	const script = `(async () => {
		const img = new Image();
		img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(${JSON.stringify(SVG)});
		await img.decode();
		const out = {};
		for (const [key, size, pad] of ${JSON.stringify(jobs)}) {
			const canvas = document.createElement("canvas");
			canvas.width = size;
			canvas.height = size;
			canvas.getContext("2d").drawImage(img, pad, pad, size - 2 * pad, size - 2 * pad);
			out[key] = canvas.toDataURL("image/png").split(",")[1];
		}
		return out;
	})()`;
	const result = await win.webContents.executeJavaScript(script);
	win.destroy();
	return result;
}

function buildIco(pngs) {
	const header = Buffer.alloc(6);
	header.writeUInt16LE(1, 2);
	header.writeUInt16LE(pngs.length, 4);
	let offset = 6 + 16 * pngs.length;
	const entries = pngs.map(({ size, data }) => {
		const entry = Buffer.alloc(16);
		entry.writeUInt8(size >= 256 ? 0 : size, 0);
		entry.writeUInt8(size >= 256 ? 0 : size, 1);
		entry.writeUInt16LE(1, 4);
		entry.writeUInt16LE(32, 6);
		entry.writeUInt32LE(data.length, 8);
		entry.writeUInt32LE(offset, 12);
		offset += data.length;
		return entry;
	});
	return Buffer.concat([header, ...entries, ...pngs.map((p) => p.data)]);
}

function buildIcns(pngsBySize) {
	const parts = Object.entries(ICNS_TYPES).map(([size, type]) => {
		const data = pngsBySize[size];
		const head = Buffer.alloc(8);
		head.write(type, 0, "ascii");
		head.writeUInt32BE(data.length + 8, 4);
		return Buffer.concat([head, data]);
	});
	const body = Buffer.concat(parts);
	const top = Buffer.alloc(8);
	top.write("icns", 0, "ascii");
	top.writeUInt32BE(body.length + 8, 4);
	return Buffer.concat([top, body]);
}

app.disableHardwareAcceleration();
app.whenReady().then(async () => {
	const jobs = [
		...PNG_SIZES.map((n) => [`full${n}`, n, 0]),
		["mark", 144, 0],
		...Object.keys(ICNS_TYPES).map((n) => [`mac${n}`, Number(n), Math.round(n * MAC_MARGIN)]),
	];
	const rendered = await render(jobs);
	const buf = (key) => Buffer.from(rendered[key], "base64");

	for (const n of PNG_SIZES) {
		fs.writeFileSync(path.join(ROOT, "icons", "icons", "png", `${n}x${n}.png`), buf(`full${n}`));
	}
	fs.writeFileSync(path.join(ROOT, "public", "autodoc.png"), buf("full512"));
	fs.writeFileSync(path.join(ROOT, "src", "assets", "autodoc-mark.png"), buf("mark"));
	fs.writeFileSync(
		path.join(ROOT, "icons", "icons", "win", "icon.ico"),
		buildIco(ICO_SIZES.map((size) => ({ size, data: buf(`full${size}`) }))),
	);
	const macPngs = Object.fromEntries(Object.keys(ICNS_TYPES).map((n) => [n, buf(`mac${n}`)]));
	fs.writeFileSync(path.join(ROOT, "icons", "icons", "mac", "icon.icns"), buildIcns(macPngs));

	console.log("icons written");
	app.quit();
});
