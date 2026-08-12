# MenuTitle: 📮 Postino
# -*- coding: utf-8 -*-
__version__ = "1.0"
__doc__ = """
Deliver the selected glyphs to any of the other open fonts.
Every master is matched by name, so Regular lands in Regular and Bold in
Bold; masters with no counterpart are reported rather than guessed at.
"""

import GlyphsApp
import vanilla
import vanilla.dialogs   # submodule isn't pulled in by `import vanilla` alone
from GlyphsApp import Glyphs, GSGlyph, GSComponent, UPDATEINTERFACE


def selected_glyphs(font):
	"""Every selected glyph, in order, without repeats — Edit tab or Font view."""
	glyphs = [layer.parent for layer in (font.selectedLayers or []) if layer is not None]
	if not glyphs:
		glyphs = list(font.selection or [])

	seen, unique = set(), []
	for glyph in glyphs:
		if glyph is not None and glyph.name not in seen:
			seen.add(glyph.name)
			unique.append(glyph)
	return unique


def font_label(font):
	"""Family plus file name: two open fonts often share a family."""
	family = font.familyName or "Untitled"
	try:
		filename = font.filepath.lastPathComponent() if font.filepath else None
	except Exception:
		filename = None
	return "%s — %s" % (family, filename) if filename else family


def master_map(source, target, fallbackId):
	"""
	For every master of the destination, which source master feeds it.

	Keyed by the destination so no master is left empty: names decide where
	they match, and anything unmatched falls back rather than being skipped.
	"""
	byName = {}
	for master in source.masters:
		byName.setdefault((master.name or "").strip().lower(), master.id)

	pairs, guessed = {}, []
	for master in target.masters:
		key = (master.name or "").strip().lower()
		if key in byName:
			pairs[master.id] = byName[key]
		else:
			pairs[master.id] = fallbackId
			guessed.append("%s → %s" % (master.name or "?", font_label(target)))
	return pairs, guessed


def clear(layer, attribute):
	"""Empty a layer's anchors or hints, whichever way this Glyphs build allows."""
	try:
		setattr(layer, attribute, [])
	except Exception:
		for item in list(getattr(layer, attribute)):
			try:
				getattr(layer, attribute).remove(item)
			except Exception:
				pass


def missing_components(layer, target):
	"""Component bases the destination font hasn't got."""
	names = set()
	for shape in layer.shapes:
		if isinstance(shape, GSComponent):
			base = shape.componentName
			if base and target.glyphs[base] is None:
				names.add(base)
	return names


class PostinoPanel:
	def __init__(self, font):
		self.source = font
		self.targets = [f for f in Glyphs.fonts if f is not font]

		items = [{"on": True, "font": font_label(f)} for f in self.targets]

		self.w = vanilla.FloatingWindow((420, 320), "📮 Postino", minSize=(360, 260))

		self.w.caption = vanilla.TextBox((14, 12, -14, 17), "", sizeStyle="small")
		self.w.list = vanilla.List(
			(14, 36, -14, -96), items,
			columnDescriptions=[
				{"title": "", "key": "on", "cell": vanilla.CheckBoxListCell(), "width": 22},
				{"title": "Deliver to", "key": "font", "editable": False},
			],
			drawFocusRing=False,
		)
		try:
			table = self.w.list.getNSTableView()
			table.enclosingScrollView().setHasHorizontalScroller_(False)
		except Exception:
			pass

		# 16 apart: at 8 the small bezels touch and read as one control
		self.w.all = vanilla.Button((14, -84, 60, 18), "All",
			callback=self.selectAll, sizeStyle="small")
		self.w.none = vanilla.Button((90, -84, 60, 18), "None",
			callback=self.selectNone, sizeStyle="small")
		self.w.replace = vanilla.CheckBox((166, -85, -14, 20),
			"Replace glyphs that are already there", value=True, sizeStyle="small")

		self.w.info = vanilla.TextBox((14, -56, -14, 17), "", sizeStyle="small")
		self.w.cancelButton = vanilla.Button((-206, -32, 90, 20), "Cancel",
			callback=self.cancel)
		self.w.deliverButton = vanilla.Button((-100, -32, 90, 20), "Deliver",
			callback=self.deliver)
		self.w.setDefaultButton(self.w.deliverButton)

		self.refresh()

		# the selection is read while the panel is open, not once at launch:
		# opening the window first and picking the glyph after is the normal
		# way round, and snapshotting here left it permanently empty
		self.w.bind("close", self.windowClosed)
		Glyphs.addCallback(self.interfaceUpdate_, UPDATEINTERFACE)

		self.w.open()
		self.w.makeKey()

	# ------------------------------------------------------------------
	def currentGlyphs(self):
		"""Whatever is selected in the sending font, right now."""
		return selected_glyphs(self.source)

	def fallbackId(self):
		"""
		The source layer a destination master gets when no name matches.

		The master in front is the right guess: it is the drawing you are
		looking at while you press Deliver.
		"""
		try:
			return self.source.selectedFontMaster.id
		except Exception:
			return self.source.masters[0].id

	def refresh(self, sender=None):
		try:
			glyphs = self.currentGlyphs()
			names = ", ".join(g.name for g in glyphs[:6])
			if len(glyphs) > 6:
				names += ", …"
			self.w.caption.set("Sending %d glyph%s from %s: %s" % (
				len(glyphs), "" if len(glyphs) == 1 else "s",
				self.source.familyName or "Untitled", names)
				if glyphs else "Select the glyphs in %s." % (
					self.source.familyName or "the font"))

			chosen = sum(1 for item in self.w.list if item["on"])
			self.w.info.set("%d of %d open fonts ticked." % (chosen, len(self.targets)))
		except Exception as e:
			self.w.info.set("Refresh: %s" % e)

	def interfaceUpdate_(self, sender):
		try:
			self.refresh()
		except Exception:
			pass

	def windowClosed(self, sender):
		# an orphaned callback keeps firing into a dead panel
		try:
			Glyphs.removeCallback(self.interfaceUpdate_, UPDATEINTERFACE)
		except Exception:
			pass

	def selectAll(self, sender):
		for item in self.w.list:
			item["on"] = True
		self.refresh()

	def selectNone(self, sender):
		for item in self.w.list:
			item["on"] = False
		self.refresh()

	def cancel(self, sender):
		self.closePanel()

	def closePanel(self):
		try:
			self.w.close()
		except TypeError:
			# PyObjC bridge bug in some Glyphs builds: NSWindow.close misbridged
			self.w._window.performClose_(None)

	# ------------------------------------------------------------------
	def copyGlyph(self, glyph, target, replace, report):
		existing = target.glyphs[glyph.name]
		if existing is not None and not replace:
			report["skipped"].append(glyph.name)
			return

		pairs, guessed = master_map(self.source, target, self.fallbackId())
		if not pairs:
			report["nomasters"].add(font_label(target))
			return
		report["guessed"].update(guessed)

		if existing is None:
			# GSGlyph() takes no positional arguments in Glyphs 4: the name
			# has to be set on the empty object, before it joins the font
			existing = GSGlyph()
			existing.name = glyph.name
			target.glyphs.append(existing)
			report["created"] += 1
		else:
			report["replaced"] += 1

		# the glyph's own identity, not just its drawing
		existing.unicodes = list(glyph.unicodes or [])
		for attribute in ("category", "subCategory", "script", "export",
				"leftMetricsKey", "rightMetricsKey", "widthMetricsKey"):
			try:
				setattr(existing, attribute, getattr(glyph, attribute))
			except Exception:
				pass

		for targetId, sourceId in pairs.items():
			sourceLayer = glyph.layers[sourceId]
			if sourceLayer is None:
				continue
			report["missing"].update(missing_components(sourceLayer, target))

			targetLayer = existing.layers[targetId]
			if targetLayer is None:
				report["nolayer"].add("%s in %s" % (glyph.name, font_label(target)))
				continue

			# Contents, not the layer object: handing a whole GSLayer from one
			# font to another leaves the shapes behind and the glyph lands empty.
			for shape in list(targetLayer.shapes):
				targetLayer.shapes.remove(shape)
			for shape in sourceLayer.shapes:
				targetLayer.shapes.append(shape.copy())

			clear(targetLayer, "anchors")
			for anchor in sourceLayer.anchors:
				targetLayer.anchors.append(anchor.copy())

			# after the shapes: a hint points at nodes by index
			clear(targetLayer, "hints")
			for hint in sourceLayer.hints:
				try:
					targetLayer.hints.append(hint.copy())
				except Exception:
					pass

			targetLayer.width = sourceLayer.width

	def deliver(self, sender):
		glyphs = self.currentGlyphs()
		if not glyphs:
			vanilla.dialogs.message("Postino", "Select the glyphs to send first.")
			return

		chosen = [f for f, item in zip(self.targets, self.w.list) if item["on"]]
		if not chosen:
			vanilla.dialogs.message("Postino", "Tick at least one font.")
			return

		replace = bool(self.w.replace.get())
		report = {"created": 0, "replaced": 0, "skipped": [],
			"guessed": set(), "missing": set(), "nomasters": set(),
			"nolayer": set()}

		for target in chosen:
			target.disableUpdateInterface()
			try:
				for glyph in glyphs:
					existing = target.glyphs[glyph.name]
					if existing is not None:
						existing.beginUndo()
					try:
						self.copyGlyph(glyph, target, replace, report)
					finally:
						if existing is not None:
							existing.endUndo()
			finally:
				target.enableUpdateInterface()

		self.announce(report, len(chosen))
		self.closePanel()

	def announce(self, report, fonts):
		lines = ["%d added, %d replaced, across %d font%s." % (
			report["created"], report["replaced"], fonts,
			"" if fonts == 1 else "s")]
		if report["skipped"]:
			lines.append("Left alone (already there): %s" % ", ".join(sorted(set(report["skipped"]))))
		if report["guessed"]:
			lines.append("No master of that name — filled from the master in front: %s"
				% ", ".join(sorted(report["guessed"])))
		if report["missing"]:
			lines.append("Components the destination hasn't got: %s" % ", ".join(sorted(report["missing"])))
		if report["nomasters"]:
			lines.append("No matching masters at all: %s" % ", ".join(sorted(report["nomasters"])))
		if report["nolayer"]:
			lines.append("Couldn't reach the master layer: %s" % ", ".join(sorted(report["nolayer"])))

		text = "\n".join(lines)
		print("📮 Postino\n%s" % text)
		Glyphs.showNotification("📮 Postino", lines[0])
		# anything beyond the headline is a warning, and a notification is too
		# small to carry it — put it where it can be read
		if len(lines) > 1:
			vanilla.dialogs.message("Postino", text)


font = Glyphs.font
if font is None:
	vanilla.dialogs.message("Postino", "No font open.")
elif len(Glyphs.fonts) < 2:
	vanilla.dialogs.message("Postino", "Open the fonts you want to deliver to as well.")
else:
	PostinoPanel(font)
