# MenuTitle:✂️ ShortNames
# -*- coding: utf-8 -*-
__doc__ = """
Make Short PS Names + File Names.
Panel that previews abbreviated postscriptFontName / fileName for every exportable instance
(Condensed→Cn, ExtraBold→XBd, etc.). Edit any name in the list, then Apply.
Family name and style name stay untouched.
"""

import re
import GlyphsApp
import vanilla
import vanilla.dialogs   # submodule isn't pulled in by `import vanilla` alone

ABBREVIATIONS = {
	"Regular": "Rg",
	"Italic": "It",
	"Oblique": "Obl",
	"Slanted": "Sl",
	"Bold": "Bd",
	"Light": "Lt",
	"Medium": "Md",
	"Black": "Blk",
	"Thin": "Th",
	"Book": "Bk",
	"Heavy": "Hv",
	"Hairline": "Hair",
	"Extra": "X",
	"Semi": "Sm",
	"Demi": "Dm",
	"Ultra": "Ult",
	"Super": "Sup",
	"Condensed": "Cn",
	"Compressed": "Cm",
	"Compact": "Cp",
	"Narrow": "Nr",
	"Extended": "Ex",
	"Expanded": "Exp",
	"Wide": "Wd",
	"Display": "Ds",
	"Text": "Tx",
	"Caption": "Ca",
	"Poster": "Po",
	"Variable": "VF",
}


def split_words(name):
	# "SemiCondensed Bold Italic" -> ["Semi", "Condensed", "Bold", "Italic"]
	words = []
	for chunk in name.split():
		words += re.findall(r"[A-Z][a-z]*|[a-z]+|\d+", chunk) or [chunk]
	return words


def shorten_style(style_name):
	short = "".join(ABBREVIATIONS.get(w, w) for w in split_words(style_name))
	return short or "Rg"


def get_ps_name(instance):
	return (
		getattr(instance, "postscriptFontName", None)
		or getattr(instance, "fontName", None)
		or ""
	)


def set_ps_name(instance, name):
	# Glyphs 4 stores it as the instance key `postscriptFontName`
	for attr in ("postscriptFontName", "fontName"):
		try:
			setattr(instance, attr, name)
			if get_ps_name(instance) == name:
				return True
		except Exception:
			pass
	try:
		instance.setValue_forKey_(name, "postscriptFontName")
		return get_ps_name(instance) == name
	except Exception:
		return False


class ShortNamesPanel:
	def __init__(self, font):
		self.font = font
		variable_type = getattr(GlyphsApp, "INSTANCETYPEVARIABLE", 1)
		self.instances = [
			i for i in font.instances
			if i.active and getattr(i, "type", 0) != variable_type
		]

		items = []
		for instance in self.instances:
			family = (instance.familyName or font.familyName or "").replace(" ", "")
			style = instance.name or getattr(instance, "styleName", None) or "Regular"
			current = get_ps_name(instance) or instance.customParameters["postscriptFontName"] or ""
			items.append({
				"Instance": style,
				"Current": current,
				"New": f"{family}-{shorten_style(style)}",
			})

		self.w = vanilla.FloatingWindow((560, 380), "✂️ Short PS Names + File Names", minSize=(420, 260))
		self.w.list = vanilla.List(
			(10, 10, -10, -70),
			items,
			columnDescriptions=[
				{"title": "Instance", "editable": False, "width": 150},
				{"title": "Current", "editable": False, "width": 170},
				{"title": "New", "editable": True},
			],
		)
		self.w.info = vanilla.TextBox((12, -56, -10, 17), f"{len(items)} instances — edit the New column if needed.", sizeStyle="small")
		self.w.cancelButton = vanilla.Button((-200, -32, 90, 20), "Cancel", callback=self.cancel)
		self.w.applyButton = vanilla.Button((-100, -32, 90, 20), "Apply", callback=self.apply)
		self.w.setDefaultButton(self.w.applyButton)
		self.w.open()
		self.w.makeKey()

	def closePanel(self):
		try:
			self.w.close()
		except TypeError:
			# PyObjC bridge bug in some Glyphs builds: NSWindow.close misbridged
			self.w._window.performClose_(None)

	def cancel(self, sender):
		self.closePanel()

	def apply(self, sender):
		items = self.w.list.get()
		seen = set()
		problems = []
		for item in items:
			name = str(item["New"]).strip()
			if not name or "-" not in name:
				problems.append(f"'{name}' is not a valid PS name")
			if name in seen:
				problems.append(f"duplicate: {name}")
			if len(name) > 29:
				problems.append(f"{name} is {len(name)} chars (>29)")
			seen.add(name)
		if problems:
			if not vanilla.dialogs.askYesNo("Problems found", "\n".join(problems) + "\n\nApply anyway?"):
				return

		failed = []
		for instance, item in zip(self.instances, items):
			name = str(item["New"]).strip()
			if not set_ps_name(instance, name):
				failed.append(item["Instance"])
			# drop the old custom parameter, ignored at export in Glyphs 4
			if instance.customParameters["postscriptFontName"]:
				del instance.customParameters["postscriptFontName"]
			instance.customParameters["fileName"] = name

		if failed:
			vanilla.dialogs.message("Short PS Names", "Could not set postscriptFontName on: " + ", ".join(failed))

		Glyphs.showNotification("Short PS Names", f"{len(items)} instances updated in {self.font.familyName}.")
		self.closePanel()


font = Glyphs.font
if font is None:
	vanilla.dialogs.message("Short PS Names", "No font open.")
elif not font.instances:
	vanilla.dialogs.message("Short PS Names", "No instances in Font Info → Exports.")
else:
	ShortNamesPanel(font)
