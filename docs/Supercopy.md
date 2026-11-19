# 📋 Supercopy

By Giuseppe Salerno [rsztype.com](https://rsztype.com).

A script for the [Glyphs font editor](https://glyphsapp.com/). It copies the selected glyphs as real text instead of `/glyphnames`, so they paste into another Glyphs file, where that font shapes them again, or into any other app.

### What it does

When you copy letters in an Edit tab, Glyphs writes a `/name` for every glyph that has no Unicode value of its own. Ligatures, conjuncts, positional forms and alternates have none, so a line of Arabic comes out as `/veh_yehbarree.ar.fina/…`. Another app cannot read that, and another font may not have glyphs with the same names.

Supercopy takes each glyph back to the characters it stands for and puts that text on the clipboard. It reads, in this order:

1. the glyph's own Unicode value;
2. its production name, which spells out the sequence (`k_ssa-deva` is `uni0915094D0937`, ka + virama + ssa);
3. its name, split at `_` into the letters a ligature is made of, with suffixes such as `.fina`, `.comp` or `.ss01` left out.

That makes it work well for **complex scripts**, where most of what you see in an Edit tab has no Unicode value:

- **Arabic**: positional forms and ligatures (`beh-ar.init` → ب, `lam_alef-ar` → لا, `veh_yehbarree.ar.fina` → ڤے)
- **Hebrew**: letters, final forms and the precomposed letters with points (`shindagesh-hb` → שּ)
- **Devanagari**: half forms and conjuncts (`k-deva` → क्, `k_ssa-deva` → क्ष)
- **Bengali**: conjuncts (`k_ssa-beng` → ক্ষ)
- **Latin** ligatures and alternates (`f_f_i` → ffi, `s_t` → st, `a.ss01` → a, `one.tf` → 1)

Marks that only exist as components (`threedotsupabove.ar`, `dotbelow-ar`) add no text. A glyph that cannot be traced back, such as `.notdef` or a helper part, is skipped, and the notification names it.

It copies the selection in the Edit tab, or the selected glyphs in the Font View.

### Installation

1. Download `Supercopy.py`.
2. Drop it into your Glyphs scripts folder: *Glyphs > Settings… > Addons > Scripts*, or directly into `~/Library/Application Support/Glyphs 3/Scripts/` (or `Glyphs 4/Scripts/`).
3. In Glyphs, open the *Script* menu and choose *Reload Scripts* (⌘⌥⇧Y) if it doesn't show up right away.

### Usage

1. Select some letters in an Edit tab, or some glyphs in the Font View.
2. Run **📋 Supercopy** from the *Script* menu. A notification shows what was copied.
3. Paste with ⌘V in another Glyphs file or in any other app.

For a shortcut of your own, add one in *Glyphs > Settings… > Shortcuts*.

### Requirements

Glyphs 3 or Glyphs 4.

### License

Copyright 2026 Giuseppe Salerno / Resistenza Type [rsztype.com](https://rsztype.com).

You may use, modify, and distribute this script freely. It is provided as-is, without warranty of any kind.
