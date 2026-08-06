# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this repository is

A small collection of standalone scripts for the [Glyphs font editor](https://glyphsapp.com/)
(Glyphs 3 and Glyphs 4), by Giuseppe Salerno / Resistenza Type. Each script is a
single `.py` file at the top level; a user installs one by dropping it into
`~/Library/Application Support/Glyphs 3/Scripts/` (or `Glyphs 4/Scripts/`).

There is no build system, no package, no dependency manifest, no test suite, and
nothing to install. The repository *is* the deliverable.

## Layout

```
MasterTwins.py     👯  clone one master into another (whole font or selection)
Postino.py         📮  send selected glyphs to other open fonts
ShortNames.py      ✂️  short PostScript names + fileName for exportable instances
StyleLinker.py     🔗  style linking (Bold/Italic/Bold Italic) for instances
README.md              index of the scripts, one bullet each
docs/<Name>.md         per-script documentation, one file per script
docs/*Screenshot.png   panel screenshots referenced from docs/
LICENSE.txt            Apache 2.0
```

The flat top level is deliberate — see commit `e2877df` "Flatten the repo so the
Script menu has no submenus". **Do not move scripts into subfolders**: Glyphs
mirrors the folder structure in its *Script* menu, and subfolders would nest them.

## Running and testing

These scripts only run inside Glyphs. `import GlyphsApp`, `import vanilla` and
`from AppKit import …` all resolve against the macOS app's embedded Python, so
nothing here is importable or executable in this environment, and there is no way
to run it in CI.

Practically this means:

- Verify changes by **reading** them. Check syntax with `python3 -m py_compile
  <file>.py` — that works because the imports are at module level but compilation
  does not execute them.
- Never add a dependency that isn't already available in Glyphs (`GlyphsApp`,
  `vanilla`, `AppKit`/`Foundation` via PyObjC, and the standard library).
- Do not add test files, `requirements.txt`, `setup.py`, CI config, or linters
  unless explicitly asked. None of it fits how these scripts ship.

## Script anatomy

Every script follows the same shape. Copy it when adding a new one.

1. **`# MenuTitle: <emoji> <Name>`** on line 1 — this is what Glyphs shows in the
   *Script* menu. The emoji is part of the title.
2. **`# -*- coding: utf-8 -*-`** on line 2.
3. **`__doc__ = """…"""`** — a few lines describing what the script does; Glyphs
   shows it as the menu item's tooltip.
4. Imports: `GlyphsApp`, `vanilla`, then **`import vanilla.dialogs`** explicitly
   (the submodule is *not* pulled in by `import vanilla` alone — commit `1ba5202`),
   then AppKit/Foundation.
5. Module-level helper functions (`selected_glyphs`, `clear`, `fit_columns`, …).
6. A single `…Panel` class that builds a `vanilla.FloatingWindow`, previews the
   change, and applies it on a button press.
7. A guard block at the bottom of the file, at module level, that checks
   preconditions and either shows a `vanilla.dialogs.message` or constructs the
   panel:

   ```python
   font = Glyphs.font
   if font is None:
       vanilla.dialogs.message("MasterTwins", "No font open.")
   elif len(font.masters) < 2:
       vanilla.dialogs.message("MasterTwins", "This font has only one master.")
   else:
       MasterTwinsPanel(font)
   ```

`Glyphs` is available as a global inside Glyphs without importing it; some scripts
also `from GlyphsApp import Glyphs, …` for the other symbols. Both are fine.

### Panel conventions

- **Preview, then apply.** Every panel shows what it will do before doing it, with
  a **Cancel** and an **Apply**/**Deliver** pair; Apply is the default button
  (`self.w.setDefaultButton(...)`). Cancel must change nothing.
- **Button spacing is load-bearing.** Buttons sit 16pt apart, not 10 or 8 — at the
  smaller gap the default button's wider bezel closes the gap and the two read as
  one control. The existing inline comments say so; keep them and keep the spacing.
- **`closePanel()`**, not `self.w.close()`:

  ```python
  def closePanel(self):
      try:
          self.w.close()
      except TypeError:
          # PyObjC bridge bug in some Glyphs builds: NSWindow.close misbridged
          self.w._window.performClose_(None)
  ```
- **Live selection**, not a snapshot. Panels that depend on the glyph selection
  register `Glyphs.addCallback(self.interfaceUpdate_, UPDATEINTERFACE)` and refresh
  from it, because opening the window first and selecting after is the normal way
  round. Always pair it with `self.w.bind("close", self.windowClosed)` and
  `Glyphs.removeCallback(...)` there — an orphaned callback keeps firing into a
  dead panel.
- **Report, don't guess silently.** Results go out as
  `Glyphs.showNotification(title, headline)`; anything longer than a headline
  (warnings, per-glyph problems) goes to `vanilla.dialogs.message` and `print()`,
  because a notification is too small to carry it.
- **Wrap `apply` in try/except** where a failure is plausible: vanilla swallows
  exceptions raised inside a callback, so an unguarded error makes the button look
  dead with the traceback hidden in the Macro Panel.

### Working with the Glyphs object model

- **Glyphs 3 / Glyphs 4 differences are handled defensively at the call site** —
  `getattr(GlyphsApp, "INSTANCETYPEVARIABLE", 1)`, the multi-attribute fallbacks in
  `ShortNames.set_ps_name` and `typographic_family`, the `clear()` helper that
  empties `anchors`/`hints` "whichever way this Glyphs build allows". Follow the
  same pattern rather than branching on a version number.
- **Copy contents, never objects across fonts.** Handing a whole `GSLayer` from one
  font to another leaves the shapes behind and the glyph lands empty. Append
  `shape.copy()`, `anchor.copy()`, `hint.copy()` into the destination layer.
- **Order matters: shapes before hints.** A hint points at nodes by index, so it
  only lands correctly once its outline is already there.
- `GSGlyph()` takes no positional arguments in Glyphs 4 — create it empty, set
  `.name`, then append it to the font.
- **One undo per operation.** Bulk changes wrap the whole run in
  `font.undoManager().beginUndoGrouping()` / `endUndoGrouping()` plus per-glyph
  `glyph.beginUndo()` / `endUndo()`, so ⌘Z restores everything in one press instead
  of once per glyph. Bracket bulk work with `font.disableUpdateInterface()` /
  `enableUpdateInterface()` in a `try/finally`.
- **Nothing is saved by a script.** Changes sit in the open font for the user to
  look at and save themselves.
- Filter instances the same way everywhere: active and non-variable —
  `[i for i in font.instances if i.active and getattr(i, "type", 0) != variable_type]`.

## Code style

- **Tabs for indentation.** All four scripts are tab-indented; there are no
  space-indented lines. Match it exactly — mixing breaks Python.
- Module-level helpers are `snake_case`; methods on panel classes are `camelCase`
  (`closePanel`, `targetGlyphs`, `copyMasters`). This is intentional — it follows
  vanilla/PyObjC on the class side. Keep both conventions where they already are.
- Docstrings on helpers are one line, or a short paragraph explaining *why*.
- **Comments explain reasoning, not mechanics.** The existing ones record why a
  value or an ordering was chosen ("at this width a third column would clip
  'Components'", "a hint points at nodes by index"). Write that kind of comment;
  don't narrate what the next line obviously does.
- Prose in UI strings and docs uses en dashes (—), curly quotes and the author's
  plain, unhurried voice. Match it.

## Documentation conventions

Every script has a `docs/<ScriptName>.md` with this exact structure:

```markdown
# <emoji> <Name>

By Giuseppe Salerno ([Resistenza Type](https://rsztype.com)).

A script for the [Glyphs font editor](https://glyphsapp.com/). <one-sentence summary>

<optional <img> screenshot, width="450">

### What it does
### Installation      (download → drop into Scripts folder → Reload Scripts ⌘⌥⇧Y)
### Usage             (numbered steps)
### Requirements      (Glyphs 3 or Glyphs 4, plus anything else)
### License           (Copyright 2026 Giuseppe Salerno / Resistenza Type…)
```

When adding or changing a script:

1. Update its `docs/<Name>.md`.
2. Update the bullet in `README.md` — scripts are listed **alphabetically**, each
   as `[**<emoji> Name**](docs/Name.md) — <lowercase summary>`.
3. Screenshots go in `docs/`, named `<Name>Screenshot.png`, compressed
   (700px wide, pngquant) and displayed at `width="450"`.

## Git

- Work on the branch you were assigned; do not push to `main`.
- Commit messages: imperative mood, sentence case, no prefix or scope, one line,
  and they say *why* where it isn't obvious — "Build the short name from the
  typographic family when there is one", "Flatten the repo so the Script menu has
  no submenus", "Import vanilla.dialogs explicitly".
- Push with `git push -u origin <branch>`.
