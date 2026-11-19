# 📋 Supercopy

By Giuseppe Salerno [rsztype.com](https://rsztype.com).

A script for the [Glyphs font editor](https://glyphsapp.com/). It copies the selected glyphs as real text instead of `/glyphnames`, so they paste into another Glyphs file, where that font shapes them again, or into any other app.

![What ⌘C copies from a Glyphs Edit tab, next to what Supercopy copies](SupercopyScreenshot.png)

### What it does

When you copy in an Edit tab, Glyphs writes a `/name` for every glyph without a Unicode value: ligatures, conjuncts, positional forms and alternates. Supercopy takes each of them back to the characters it is made of, reading the Unicode value, then the production name, then the glyph name.

That makes it work well for **complex scripts**:

- **Arabic**: positional forms and ligatures (`beh-ar.init` → ب, `lam_alef-ar` → لا, `veh_yehbarree.ar.fina` → ڤے)
- **Hebrew**: letters with points (`shindagesh-hb` → שּ)
- **Devanagari**: half forms and conjuncts (`k-deva` → क्, `k_ssa-deva` → क्ष)
- **Bengali**: conjuncts (`k_ssa-beng` → ক্ষ)
- **Latin**: ligatures, alternates, small caps and figures (`f_f_i` → ffi, `T_h` → Th, `a.ss01` → a, `a.sc` → a, `one.tf` → 1)

Marks that only exist as components add no text; a glyph that cannot be traced back, such as `.notdef`, is skipped and named in the notification.

### Installation

1. Download `Supercopy.py`.
2. Drop it into your Glyphs scripts folder: *Glyphs > Settings… > Addons > Scripts*, or `~/Library/Application Support/Glyphs 3/Scripts/` (or `Glyphs 4/Scripts/`).
3. Choose *Script > Reload Scripts* (⌘⌥⇧Y).

### Usage

1. Select letters in an Edit tab, or glyphs in the Font View.
2. Run **📋 Supercopy** from the *Script* menu.
3. Paste with ⌘V in another Glyphs file or any other app.

### Requirements

Glyphs 3 or Glyphs 4.

### License

Copyright 2026 Giuseppe Salerno / Resistenza Type [rsztype.com](https://rsztype.com). Free to use, modify, and distribute; provided as-is, without warranty of any kind.
