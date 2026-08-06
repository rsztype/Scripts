# 👯 MasterTwins

By Giuseppe Salerno ([Resistenza Type](https://rsztype.com)).

A script for the [Glyphs font editor](https://glyphsapp.com/). It clones one master into another — every glyph in the font, or just the selected ones — and lets you choose what travels: paths, components, anchors, metrics, hints.

### What it does

Run the script with a font of two or more masters open. Pick the master to copy from and the one to paste into; a glyph is drawn on each side so you can see which pair you picked. Untick anything under **Include** that should stay as it is in the destination — copying only the components, for instance, leaves hand-drawn paths there alone.

On **Apply** the whole master is overwritten, as one single undo. Tick **Selected glyphs only** to limit it to the current selection instead.

### Installation

1. Download `MasterTwins.py`.
2. Drop it into your Glyphs scripts folder: *Glyphs > Settings… > Addons > Scripts*, or directly into `~/Library/Application Support/Glyphs 3/Scripts/` (or `Glyphs 4/Scripts/`).
3. In Glyphs, open the *Script* menu and choose *Reload Scripts* (⌘⌥⇧Y) if it doesn't show up right away.

### Usage

1. Open a font with at least two masters.
2. Run **👯 MasterTwins** from the *Script* menu.
3. Choose the two masters, and what to include.
4. Click **Apply**. ⌘Z puts the master back.

### Requirements

Glyphs 3 or Glyphs 4.

### License

Copyright 2026 Giuseppe Salerno / Resistenza Type ([rsztype.com](https://rsztype.com)).

You may use, modify, and distribute this script freely. It is provided as-is, without warranty of any kind.
