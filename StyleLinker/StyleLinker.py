# MenuTitle: 🔗 Style Linker
# -*- coding: utf-8 -*-
__doc__ = """
Panel that previews automatic style linking for all exportable instances:
Bold/Italic/Bold Italic link to their base style, also inside width groups
(Condensed Bold Italic → Condensed, Extended Italic → Extended, etc.).
Only whole words count: ExtraBold/SemiBold are NOT linked as Bold.
"""

import GlyphsApp
import vanilla
import vanilla.dialogs   # submodule isn't pulled in by `import vanilla` alone

ITALIC_WORDS = ("Italic", "Oblique")


def link_for(style_name, all_styles):
	"""Returns (linkStyle, isBold, isItalic) for a style name, or None if no link applies."""
	words = style_name.split()
	is_italic = any(w in ITALIC_WORDS for w in words)
	remainder = [w for w in words if w not in ITALIC_WORDS]

	is_bold = "Bold" in remainder
	if is_bold:
		base_words = [w for w in remainder if w != "Bold"]
	else:
		base_words = remainder

	if not (is_bold or is_italic):
		return None

	base = " ".join(base_words) or "Regular"
	if base == style_name:
		return None
	if base not in all_styles:
		# e.g. "Bold Italic" with no "Bold"? fall back to bold-only base, then give up
		if is_bold and is_italic and " ".join(remainder) in all_styles:
			return (" ".join(remainder), False, True)
		return None

	return (base, is_bold, is_italic)


class StyleLinkerPanel:
	def __init__(self, font):
		self.font = font
		variable_type = getattr(GlyphsApp, "INSTANCETYPEVARIABLE", 1)
		self.instances = [
			i for i in font.instances
			if i.active and getattr(i, "type", 0) != variable_type
		]
		all_styles = set(i.name for i in self.instances)

		self.links = []  # parallel to self.instances: None or (base, isBold, isItalic)
		items = []
		for instance in self.instances:
			link = link_for(instance.name or "", all_styles)
			self.links.append(link)
			if link:
				base, is_bold, is_italic = link
				items.append({
					"Instance": instance.name,
					"Links to": base,
					"Bold": "✓" if is_bold else "",
					"Italic": "✓" if is_italic else "",
				})
			else:
				items.append({
					"Instance": instance.name,
					"Links to": "—",
					"Bold": "",
					"Italic": "",
				})

		linked = sum(1 for l in self.links if l)
		self.w = vanilla.FloatingWindow((520, 400), "🔗 Style Linker", minSize=(420, 260))
		self.w.list = vanilla.List(
			(10, 10, -10, -70),
			items,
			columnDescriptions=[
				{"title": "Instance", "editable": False, "width": 180},
				{"title": "Links to", "editable": False, "width": 160},
				{"title": "Bold", "editable": False, "width": 50},
				{"title": "Italic", "editable": False, "width": 50},
			],
		)
		self.w.info = vanilla.TextBox((12, -56, -10, 17), f"{linked} of {len(items)} instances will be linked. '—' rows stay untouched.", sizeStyle="small")
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
		count = 0
		for instance, link in zip(self.instances, self.links):
			if not link:
				continue
			base, is_bold, is_italic = link
			instance.isBold = is_bold
			instance.isItalic = is_italic
			# empty linkStyle means "linked to Regular" in Glyphs
			instance.linkStyle = "" if base == "Regular" else base
			count += 1

		Glyphs.showNotification("🔗 Style Linker", f"{count} instances linked in {self.font.familyName}.")
		self.closePanel()


font = Glyphs.font
if font is None:
	vanilla.dialogs.message("Style Linker", "No font open.")
elif not font.instances:
	vanilla.dialogs.message("Style Linker", "No instances in Font Info → Exports.")
else:
	StyleLinkerPanel(font)
