// Windows source of window titles and (opt-in) typed keys for the guide.
//
// No native module: PowerShell compiles a tiny C# poller with Add-Type and streams
// one line per event on stdout, stamped with epoch ms (the same clock as `Date.now()`
// in the main process). Polling at 15 ms catches ordinary typing; it is not a keylogger
// and does nothing at all unless the user turned key capture on.
//
//   T <tab> epochMs <tab> window title        (foreground window changed)
//   K <tab> epochMs <tab> key                 (key went down)

import { type ChildProcess, spawn } from "node:child_process";
import type { GuideKeyEvent, GuideWindowEvent } from "../../src/lib/guide/types";

export type ProbeEvent =
	| { kind: "window"; epochMs: number; title: string }
	| { kind: "key"; epochMs: number; key: string };

export function parseProbeLine(line: string): ProbeEvent | null {
	const [tag, stamp, ...rest] = line.replace(/\r$/, "").split("\t");
	const epochMs = Number(stamp);
	if (!Number.isFinite(epochMs)) return null;
	const value = rest.join("\t");
	if (tag === "T") return { kind: "window", epochMs, title: value };
	if (tag === "K" && value) return { kind: "key", epochMs, key: value };
	return null;
}

export function toGuideEvent(
	event: ProbeEvent,
	startEpochMs: number,
): { window: GuideWindowEvent } | { key: GuideKeyEvent } {
	const timeMs = Math.max(0, event.epochMs - startEpochMs);
	return event.kind === "window"
		? { window: { timeMs, title: event.title } }
		: { key: { timeMs, key: event.key } };
}

const CSHARP = String.raw`
using System; using System.Runtime.InteropServices; using System.Text; using System.Threading;
public static class AutoDocProbe {
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern short GetAsyncKeyState(int vk);
  [DllImport("user32.dll")] static extern short GetKeyState(int vk);
  [DllImport("user32.dll")] static extern uint MapVirtualKey(uint code, uint type);
  [DllImport("user32.dll")] static extern int ToUnicode(uint vk, uint sc, byte[] ks, StringBuilder buf, int n, uint flags);
  static long Now() { return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(); }
  static bool Down(int vk) { return (GetAsyncKeyState(vk) & 0x8000) != 0; }
  static string Special(int vk) {
    switch (vk) {
      case 0x0D: return "[Enter]"; case 0x20: return "[Space]"; case 0x09: return "[Tab]";
      case 0x08: return "[Backspace]"; case 0x1B: return "[Esc]"; case 0x2E: return "[Delete]";
      case 0x25: return "[Left]"; case 0x26: return "[Up]"; case 0x27: return "[Right]"; case 0x28: return "[Down]";
    }
    return null;
  }
  public static void Run(bool keys) {
    var title = new StringBuilder(512); string last = null;
    var down = new bool[256]; var state = new byte[256]; var buf = new StringBuilder(8);
    while (true) {
      title.Clear(); GetWindowText(GetForegroundWindow(), title, title.Capacity);
      string t = title.ToString().Replace('\t', ' ').Replace('\r', ' ').Replace('\n', ' ');
      if (t != last) { last = t; Console.Out.WriteLine("T\t" + Now() + "\t" + t); Console.Out.Flush(); }
      if (keys) {
        bool ctrl = Down(0x11), alt = Down(0x12);
        for (int vk = 8; vk < 255; vk++) {
          if (vk < 7 || (vk >= 0x10 && vk <= 0x12) || vk == 0x5B || vk == 0x5C || (vk >= 0xA0 && vk <= 0xA5)) continue;
          if (vk == 0x77 || vk == 0x78) continue; // F8 / F9: recorder hotkeys, never logged
          bool d = Down(vk);
          if (d && !down[vk]) {
            string k = Special(vk);
            if (k == null && !ctrl && !alt) {
              Array.Clear(state, 0, 256);
              if (Down(0x10)) state[0x10] = 0x80;
              if ((GetKeyState(0x14) & 1) != 0) state[0x14] = 1;
              buf.Clear();
              if (ToUnicode((uint)vk, MapVirtualKey((uint)vk, 0), state, buf, buf.Capacity, 0) == 1) k = buf.ToString();
            }
            if (!string.IsNullOrEmpty(k)) { Console.Out.WriteLine("K\t" + Now() + "\t" + k); Console.Out.Flush(); }
          }
          down[vk] = d;
        }
      }
      Thread.Sleep(15);
    }
  }
}`;

export function buildProbeCommand(captureKeys: boolean): string {
	const script = [
		"[Console]::OutputEncoding = [Text.Encoding]::UTF8",
		`Add-Type -TypeDefinition @'${CSHARP}\n'@`,
		`[AutoDocProbe]::Run($${captureKeys ? "true" : "false"})`,
	].join("\n");
	return Buffer.from(script, "utf16le").toString("base64");
}

export function spawnWindowsProbe(
	captureKeys: boolean,
	onEvent: (event: ProbeEvent) => void,
): ChildProcess {
	const child = spawn(
		"powershell.exe",
		[
			"-NoProfile",
			"-NonInteractive",
			"-ExecutionPolicy",
			"Bypass",
			"-EncodedCommand",
			buildProbeCommand(captureKeys),
		],
		{ windowsHide: true, stdio: ["ignore", "pipe", "ignore"] },
	);
	let pending = "";
	child.stdout?.setEncoding("utf8");
	child.stdout?.on("data", (chunk: string) => {
		pending += chunk;
		let newline = pending.indexOf("\n");
		while (newline >= 0) {
			const event = parseProbeLine(pending.slice(0, newline));
			if (event) onEvent(event);
			pending = pending.slice(newline + 1);
			newline = pending.indexOf("\n");
		}
	});
	return child;
}
