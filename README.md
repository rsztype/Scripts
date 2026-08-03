# 🔗 Style Linker

A script for the [Glyphs font editor](https://glyphsapp.com/). It previews and applies **style linking** for every exportable instance in a family: Bold, Italic, and Bold Italic instances get linked to their base style, including inside width groups (`Condensed Bold Italic` → `Condensed`, `Extended Italic` → `Extended`, etc.).

Style linking is what lets apps that don't understand OpenType family relationships trigger the correct weight/style when the user presses the Bold or Italic button, instead of applying a synthetic (faux) bold/italic.

Only whole words count when matching: `ExtraBold` and `SemiBold` are never linked as `Bold`.

### What it does

Run the script with a font open. It scans every active, non-variable instance and shows a preview table: for each instance, whether it links, to which base style, and whether it will be marked Bold/Italic. Nothing changes until you click **Apply** — click **Cancel** and nothing happens.

On Apply, it sets `isBold`, `isItalic`, and `linkStyle` on the linked instances (an empty `linkStyle` means "linked to Regular", which is how Glyphs expects it) and shows a notification with how many instances were linked.

### Installation

1. Download `StyleLinker.py`.
2. Drop it into your Glyphs scripts folder: *Glyphs > Settings… > Addons > Scripts*, or directly into `~/Library/Application Support/Glyphs 3/Scripts/` (or `Glyphs 4/Scripts/`).
3. In Glyphs, open the *Script* menu and choose *Reload Scripts* (⌘⌥⇧Y) if the panel doesn't show up right away.

### Usage

1. Open a font with instances set up in *Font Info > Exports*.
2. Run **🔗 Style Linker** from the *Script* menu.
3. Check the preview table — rows with `—` in "Links to" are left untouched.
4. Click **Apply**.

### Requirements

Glyphs 3 or Glyphs 4.

### License

Copyright 2026 Resistenza Type (rsztype.com).

You may use, modify, and distribute this script freely. It is provided as-is, without warranty of any kind.
