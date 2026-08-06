# 📮 Postino

By Giuseppe Salerno [rsztype.com](https://rsztype.com).

A script for the [Glyphs font editor](https://glyphsapp.com/). It delivers the selected glyphs to any of the other open fonts, filling every master of the destination.

### What it does

Open the fonts you want to send to, select the glyphs in the font you are sending from, and run the script. It lists the other open fonts with a tick each; tick the ones you want and press **Deliver**.

Masters are paired by name, so Regular lands in Regular and Bold in Bold. A destination master whose name matches nothing takes the master you have in front instead — no master is left empty, and the summary tells you exactly which ones were filled that way, so you know where to go back and draw.

What travels is the glyph, not just its outline: paths, components, anchors, hints, the advance width, plus unicodes, category and the metrics keys.

The summary also warns about **components the destination hasn't got** — a glyph made of parts that aren't there arrives broken, so send the base letters first.

Nothing is saved: the changes sit in the destination fonts for you to look at, and you save them yourself.

### Installation

1. Download `Postino.py`.
2. Drop it into your Glyphs scripts folder: *Glyphs > Settings… > Addons > Scripts*, or directly into `~/Library/Application Support/Glyphs 3/Scripts/` (or `Glyphs 4/Scripts/`).
3. In Glyphs, open the *Script* menu and choose *Reload Scripts* (⌘⌥⇧Y) if it doesn't show up right away.

### Usage

1. Open the source font and the destination fonts.
2. Select the glyphs to send.
3. Run **📮 Postino** from the *Script* menu.
4. Tick the destination fonts and click **Deliver**.

### Requirements

Glyphs 3 or Glyphs 4, and at least two fonts open.

### License

Copyright 2026 Giuseppe Salerno / Resistenza Type [rsztype.com](https://rsztype.com).

You may use, modify, and distribute this script freely. It is provided as-is, without warranty of any kind.
