// What the About box says, kept out of the dialog that shows it. Every fact is passed in
// rather than read from `app`/`process`, so the string can be pinned in a test from any
// platform — the same reason install-channel.ts takes an `InstallProbe`.
//
// The install channel is in there deliberately: it is the single fact that explains why a
// copy does or does not offer "Check for Updates" (see install-channel.ts), and the first
// thing worth knowing about a bug report from a build we did not install ourselves.

import type { InstallChannel } from "./install-channel";

export const WEBSITE_URL = "https://github.com/The-ViRkumar/AutoDoc";
/** The brand spelling, for the surfaces we render ourselves. NOT `app.name`: that resolves to
 *  electron-builder's `productName` ("AutoDoc") when packaged and to package.json's `name`
 *  in dev, so the About box could disagree with its own title bar. */
export const PRODUCT_NAME = "AutoDoc";
/** The one-line credit every user sees: who made AutoDoc, and the project it is built on.
 *  The full legal notices — LICENSE carries Siddharth Vaddem, the OpenScreen contributors and
 *  The.ViRkumar — ship with the app (see `extraResources` in electron-builder.json5); this line
 *  is the short, human-readable form of them, not a replacement.
 *
 *  Must stay byte-identical to `copyright` in electron-builder.json5, which feeds Info.plist's
 *  NSHumanReadableCopyright and the Windows LegalCopyright. That key is declared explicitly
 *  BECAUSE electron-builder otherwise derives those from package.json's `author`. */
export const COPYRIGHT = "© 2026 The.ViRkumar — Built on OpenScreen (MIT License)";

/** macOS opens its own About panel (the app menu's `role: "about"`), so it is the one platform
 *  that must not be shown the message box we build, and the only one whose panel needs
 *  populating up front. Pure so both branches can be pinned from a Linux-only CI. */
export function usesNativeAboutPanel(platform: NodeJS.Platform): boolean {
	return platform === "darwin";
}

export interface AboutFacts {
	version: string;
	channel: InstallChannel;
	platform: NodeJS.Platform;
	arch: string;
	electron: string;
	chrome: string;
	node: string;
}

/** The block under "Openscreen <version>". Untranslated on purpose: every line is a version
 *  number, a platform identifier or a URL, and a pasted bug report reads the same whatever
 *  locale the reporter runs.
 *
 *  `COPYRIGHT` is deliberately NOT part of it: the macOS About panel has its own field for
 *  that line, and putting it here too would print it twice on the one platform that asked
 *  for it separately. The surface that shows the box adds it. */
export function formatAboutDetail(facts: AboutFacts): string {
	return [
		`Electron ${facts.electron} · Chromium ${facts.chrome} · Node ${facts.node}`,
		`${facts.platform} ${facts.arch} · ${facts.channel}`,
		WEBSITE_URL,
	].join("\n");
}
