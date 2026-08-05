# MenuTitle: 👯 MasterTwins
# -*- coding: utf-8 -*-
__doc__ = """
Copy a whole master into another one — every glyph in the font.
Pick the two masters, see a glyph drawn on each side, choose what travels
(paths, components, anchors, metrics, hints), then Apply.
"""

import GlyphsApp
import vanilla
import vanilla.dialogs   # submodule isn't pulled in by `import vanilla` alone
from GlyphsApp import Glyphs, GSComponent, UPDATEINTERFACE
from AppKit import NSImage, NSColor, NSBezierPath, NSAffineTransform, NSMakeRect
from Foundation import NSMakeSize

PREVIEW = 70           # side of each preview box
PADDING = 6            # breathing room around the glyph inside it

INCLUDE = (
	# key, label, (x, y) inside the window — two columns, three rows: at this
	# width a third column would clip "Components"
	("paths", "Paths", (16, 189)),
	("components", "Components", (118, 189)),
	("anchors", "Anchors", (16, 209)),
	("metrics", "Metrics", (118, 209)),
	("hints", "Hints", (16, 229)),
)


def selected_glyphs(font):
	"""Every selected glyph, in order, without repeats — Edit tab or Font view."""
	glyphs = [layer.parent for layer in (font.selectedLayers or []) if layer is not None]
	if not glyphs:
		glyphs = list(font.selection or [])

	seen = set()
	unique = []
	for glyph in glyphs:
		if glyph is not None and glyph.name not in seen:
			seen.add(glyph.name)
			unique.append(glyph)
	return unique


def preview_glyph(font):
	"""The glyph the previews draw: the first selected one, else anything legible."""
	glyphs = selected_glyphs(font)
	if glyphs:
		return glyphs[0]
	for name in ("A", "a", "one"):
		if font.glyphs[name] is not None:
			return font.glyphs[name]
	return font.glyphs[0] if len(font.glyphs) else None


def layer_image(layer):
	"""
	The layer drawn into a square image.

	Both masters are scaled by the same rule — the ascender-to-descender span
	fills the box — so the two previews stay comparable: a Thin next to a Thin
	Italic differ because the drawings differ, not because one was fitted
	tighter than the other. The scale is uniform on both axes.
	"""
	image = NSImage.alloc().initWithSize_(NSMakeSize(PREVIEW, PREVIEW))
	image.lockFocus()
	try:
		NSColor.clearColor().set()
		NSBezierPath.fillRect_(NSMakeRect(0, 0, PREVIEW, PREVIEW))

		path = layer.completeBezierPath if layer is not None else None
		if path is not None and not path.isEmpty():
			master = layer.master
			bottom = master.descender
			span = master.ascender - bottom
			if span <= 0:
				span = layer.parent.parent.upm or 1000

			scale = (PREVIEW - 2 * PADDING) / float(span)
			transform = NSAffineTransform.transform()
			transform.translateXBy_yBy_(
				PREVIEW / 2.0 - scale * layer.width / 2.0,
				PADDING - scale * bottom)
			transform.scaleBy_(scale)

			drawn = path.copy()
			drawn.transformUsingAffineTransform_(transform)
			NSColor.textColor().set()
			drawn.fill()
	finally:
		image.unlockFocus()
	return image


def copy_layer(source, target, include):
	"""Replace the chosen parts of `target` with `source`'s."""
	if include["paths"] or include["components"]:
		for shape in list(target.shapes):
			if isinstance(shape, GSComponent):
				if include["components"]:
					target.shapes.remove(shape)
			elif include["paths"]:
				target.shapes.remove(shape)

		for shape in source.shapes:
			if isinstance(shape, GSComponent):
				if include["components"]:
					target.shapes.append(shape.copy())
			elif include["paths"]:
				target.shapes.append(shape.copy())

	if include["anchors"]:
		clear(target, "anchors")
		for anchor in source.anchors:
			target.anchors.append(anchor.copy())

	# after the paths: a hint points at nodes by index, so it only lands
	# correctly once the outline it belongs to is already there
	if include["hints"]:
		clear(target, "hints")
		for hint in source.hints:
			# not every Glyphs build gives GSHint a copy(), and a missing hint
			# is not worth losing the outline that was already copied over
			try:
				target.hints.append(hint.copy())
			except Exception:
				pass

	if include["metrics"]:
		target.width = source.width
		for key in ("leftMetricsKey", "rightMetricsKey", "widthMetricsKey"):
			try:
				setattr(target, key, getattr(source, key))
			except Exception:
				pass


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


class MasterTwinsPanel:
	def __init__(self, font):
		self.font = font
		self.masters = list(font.masters)
		names = [master.name or "Master %i" % (i + 1) for i, master in enumerate(self.masters)]

		self.w = vanilla.FloatingWindow((240, 312), "👯 MasterTwins")

		# each column reads top to bottom the way the sketch does:
		# what it is, the drawing, then which master it belongs to
		self.w.fromTitle = vanilla.TextBox((16, 10, 92, 14), "Copy From",
			alignment="center", sizeStyle="small")
		self.w.fromBox = vanilla.Box((27, 30, PREVIEW, PREVIEW))
		self.w.fromBox.preview = vanilla.ImageView((0, 0, -0, -0))
		self.w.fromPopup = vanilla.PopUpButton((16, 106, 92, 17), names,
			callback=self.refresh, sizeStyle="small")

		self.w.arrow = vanilla.TextBox((108, 54, 24, 22), "→", alignment="center")
		self.w.arrow.getNSTextField().setFont_(
			self.w.arrow.getNSTextField().font().fontWithSize_(17))

		self.w.toTitle = vanilla.TextBox((132, 10, 92, 14), "Paste Into",
			alignment="center", sizeStyle="small")
		self.w.toBox = vanilla.Box((143, 30, PREVIEW, PREVIEW))
		self.w.toBox.preview = vanilla.ImageView((0, 0, -0, -0))
		self.w.toPopup = vanilla.PopUpButton((132, 106, 92, 17), names,
			callback=self.refresh, sizeStyle="small")

		# start on the master in front, pasting into the next one along: the
		# pair you most often want, and never the same master twice
		current = self.masters.index(font.selectedFontMaster) if font.selectedFontMaster in self.masters else 0
		self.w.fromPopup.set(current)
		self.w.toPopup.set((current + 1) % len(self.masters))

		# scope first, then contents: which glyphs get written at all, and only
		# then which parts of them travel
		self.w.selectedOnly = vanilla.CheckBox((16, 138, -16, 18),
			"Selected glyphs only", value=False, sizeStyle="small",
			callback=self.refresh)

		self.w.divider = vanilla.HorizontalLine((16, 163, -16, 1))

		self.w.includeTitle = vanilla.TextBox((16, 171, 56, 14), "Include:",
			sizeStyle="small")
		for key, label, (x, y) in INCLUDE:
			setattr(self.w, key, vanilla.CheckBox((x, y, 100, 18), label,
				value=True, sizeStyle="small"))

		self.w.info = vanilla.TextBox((16, 258, -16, 14), "", sizeStyle="small")
		# 16 between the two and 16 to the window edge: at sizeStyle small the
		# bezel is drawn a little wider than the frame, so a narrow gap closes up
		self.w.cancelButton = vanilla.Button((-192, -30, 80, 18), "Cancel",
			callback=self.cancel, sizeStyle="small")
		self.w.applyButton = vanilla.Button((-96, -30, 80, 18), "Apply",
			callback=self.apply, sizeStyle="small")
		self.w.setDefaultButton(self.w.applyButton)

		self.refresh(None)

		# the previews and the count follow the selection while the panel is
		# open, so what you are about to overwrite is always on screen
		self.w.bind("close", self.windowClosed)
		Glyphs.addCallback(self.interfaceUpdate_, UPDATEINTERFACE)

		self.w.open()
		self.w.makeKey()

	# ------------------------------------------------------------------
	@property
	def sourceMaster(self):
		return self.masters[self.w.fromPopup.get()]

	@property
	def targetMaster(self):
		return self.masters[self.w.toPopup.get()]

	def include(self):
		return dict((key, bool(getattr(self.w, key).get())) for key, _, _ in INCLUDE)

	def targetGlyphs(self):
		"""What Apply will write into: the whole font, or just the selection."""
		if self.w.selectedOnly.get():
			return selected_glyphs(self.font)
		return list(self.font.glyphs)

	def refresh(self, sender=None):
		try:
			glyph = preview_glyph(self.font)
			if glyph is not None:
				self.w.fromBox.preview.setImage(
					imageObject=layer_image(glyph.layers[self.sourceMaster.id]))
				self.w.toBox.preview.setImage(
					imageObject=layer_image(glyph.layers[self.targetMaster.id]))

			count = len(self.targetGlyphs())
			if self.sourceMaster is self.targetMaster:
				self.w.info.set("Pick two different masters.")
			elif not count:
				self.w.info.set("No glyphs selected.")
			elif self.w.selectedOnly.get():
				self.w.info.set("Overwrites %i selected glyph%s in %s." % (
					count, "" if count == 1 else "s", self.targetMaster.name))
			else:
				self.w.info.set("Overwrites all %i glyph%s in %s." % (
					count, "" if count == 1 else "s", self.targetMaster.name))
		except Exception as e:
			self.w.info.set("Preview: %s" % e)

	def interfaceUpdate_(self, sender):
		try:
			self.refresh(None)
		except Exception:
			pass

	# ------------------------------------------------------------------
	def windowClosed(self, sender):
		# an orphaned callback keeps firing into a dead panel
		try:
			Glyphs.removeCallback(self.interfaceUpdate_, UPDATEINTERFACE)
		except Exception:
			pass

	def closePanel(self):
		try:
			self.w.close()
		except TypeError:
			# PyObjC bridge bug in some Glyphs builds: NSWindow.close misbridged
			self.w._window.performClose_(None)

	def cancel(self, sender):
		self.closePanel()

	def apply(self, sender):
		# vanilla swallows anything raised inside a callback: without this the
		# button would just look dead, with the reason hidden in the Macro Panel
		try:
			self.copyMasters()
		except Exception:
			import traceback
			report = traceback.format_exc()
			print("MasterTwins — apply:\n%s" % report)
			self.w.info.set("Error: %s" % report.strip().splitlines()[-1])

	def copyMasters(self):
		source, target = self.sourceMaster, self.targetMaster
		if source is target:
			vanilla.dialogs.message("MasterTwins", "Copy From and Paste Into are the same master.")
			return

		glyphs = self.targetGlyphs()
		if not glyphs:
			vanilla.dialogs.message("MasterTwins",
				"Select the glyphs to copy first." if self.w.selectedOnly.get()
				else "This font has no glyphs.")
			return

		include = self.include()
		if not any(include.values()):
			vanilla.dialogs.message("MasterTwins", "Nothing ticked under Include.")
			return

		# one undo for the whole clone: per-glyph undo would mean pressing
		# ⌘Z once for every glyph in the font to get the master back
		try:
			undo = self.font.undoManager()
		except Exception:
			undo = None

		count = 0
		self.font.disableUpdateInterface()
		if undo is not None:
			undo.beginUndoGrouping()
		try:
			for glyph in glyphs:
				sourceLayer = glyph.layers[source.id]
				targetLayer = glyph.layers[target.id]
				if sourceLayer is None or targetLayer is None:
					continue
				glyph.beginUndo()
				try:
					copy_layer(sourceLayer, targetLayer, include)
					count += 1
				finally:
					glyph.endUndo()
		finally:
			if undo is not None:
				undo.endUndoGrouping()
			self.font.enableUpdateInterface()

		Glyphs.showNotification("👯 MasterTwins", "%s → %s on %i glyph%s." % (
			source.name, target.name, count, "" if count == 1 else "s"))
		self.closePanel()


font = Glyphs.font
if font is None:
	vanilla.dialogs.message("MasterTwins", "No font open.")
elif len(font.masters) < 2:
	vanilla.dialogs.message("MasterTwins", "This font has only one master.")
else:
	MasterTwinsPanel(font)
