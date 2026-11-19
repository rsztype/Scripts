# MenuTitle: ◣ 45°
# -*- coding: utf-8 -*-
__version__ = "0.01"
__doc__ = """
Adds a node wherever a curve leans at 45°, the way Glyphs adds one wherever it
reaches its furthest in x or in y. An extreme is the place the tangent turns
flat or upright; this is the same question asked of the diagonal, and a circle
that had four nodes comes out with eight.

Nothing moves. Each curve is cut at the parameter where the tangent takes the
angle, and the two halves are refitted by de Casteljau, so the outline through
the new node is the one that was already there, to the last decimal.

The angle is a field: 45 with its perpendicular gives the four diagonals, 0
gives the plain extremes, and anything else gives whatever slant you are after.
"""

import math
import vanilla
import vanilla.dialogs   # submodule isn't pulled in by `import vanilla` alone
from Foundation import NSPoint
from GlyphsApp import Glyphs, GSNode, GSPath, CURVE, LINE, OFFCURVE

try:
	from GlyphsApp import MOVE
except ImportError:
	MOVE = "move"   # an open path starts on one, whatever the constant is called

PREF_ANGLE = "com.rsztype.45.angle"
PREF_BOTH = "com.rsztype.45.both"
PREF_SCOPE = "com.rsztype.45.scope"
PREF_REACH = "com.rsztype.45.reach"

SCOPES = ("Selected glyphs", "Whole font")
SELECTED, WHOLE = 0, 1
REACH = ("All masters", "Current master only")
EVERY, THIS = 0, 1

EDGE = 1e-4        # a root this close to either end is the node already there
NEARBY = 0.35      # units: a cut this near an existing node is not worth making


# ----------------------------------------------------------------------
# Where a cubic leans at a given angle
# ----------------------------------------------------------------------
def leanRoots(p0, p1, p2, p3, degrees):
	"""The parameters where the tangent of this cubic runs at `degrees`.

	The derivative is a quadratic, and asking for a direction is asking where
	dx·sin - dy·cos vanishes — one quadratic to solve, whose two roots are the
	two places the curve can lean that way. The angle and the angle plus 180°
	are the same line, so both are caught at once.
	"""
	angle = math.radians(degrees)
	sine, cosine = math.sin(angle), math.cos(angle)
	ax, ay = p1[0] - p0[0], p1[1] - p0[1]
	bx, by = p2[0] - p1[0], p2[1] - p1[1]
	cx, cy = p3[0] - p2[0], p3[1] - p2[1]

	quad = sine * (ax - 2 * bx + cx) - cosine * (ay - 2 * by + cy)
	lin = sine * (-2 * ax + 2 * bx) - cosine * (-2 * ay + 2 * by)
	const = sine * ax - cosine * ay

	found = []
	if abs(quad) < 1e-12:
		if abs(lin) > 1e-12:
			found.append(-const / lin)
	else:
		under = lin * lin - 4 * quad * const
		if under < 0:
			return []
		root = math.sqrt(under)
		found.append((-lin + root) / (2 * quad))
		found.append((-lin - root) / (2 * quad))
	return [t for t in found if EDGE < t < 1 - EDGE]


def at(p0, p1, p2, p3, t):
	"""The point on the cubic."""
	u = 1.0 - t
	return (u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
		u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1])


def lerp(a, b, t):
	return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def cutCubic(p0, p1, p2, p3, t):
	"""de Casteljau: the same curve, written as two."""
	a = lerp(p0, p1, t)
	b = lerp(p1, p2, t)
	c = lerp(p2, p3, t)
	d = lerp(a, b, t)
	e = lerp(b, c, t)
	f = lerp(d, e, t)
	return (p0, a, d, f), (f, e, c, p3)


def cutAll(p0, p1, p2, p3, times):
	"""One cubic cut at several parameters at once. Each cut shortens what is
	left, so every later parameter is restated against the piece it lands in."""
	pieces = []
	current = (p0, p1, p2, p3)
	eaten = 0.0
	for t in sorted(times):
		local = (t - eaten) / (1.0 - eaten)
		if not (EDGE < local < 1 - EDGE):
			continue
		first, current = cutCubic(current[0], current[1], current[2], current[3], local)
		pieces.append(first)
		eaten = t
	pieces.append(current)
	return pieces


# ----------------------------------------------------------------------
# Reading and rewriting a path
# ----------------------------------------------------------------------
def kindOf(node):
	try:
		return str(node.type).lower()
	except Exception:
		return "line"


def spot(node):
	return (float(node.position.x), float(node.position.y))


def segmentsOf(path):
	"""(start, [handles], end, isCurve) for every stretch of the path, in order.
	A closed path starts at its last on-curve node, which is where Glyphs keeps
	the beginning; an open one starts at its first."""
	nodes = list(path.nodes)
	if len(nodes) < 2:
		return None
	kinds = [kindOf(node) for node in nodes]
	closed = bool(path.closed)
	if closed:
		begin = None
		for index in range(len(nodes) - 1, -1, -1):
			if kinds[index] != "offcurve":
				begin = index
				break
		if begin is None:
			return None
		order = [(begin + 1 + step) % len(nodes) for step in range(len(nodes))]
		here = spot(nodes[begin])
	else:
		order = list(range(1, len(nodes)))
		here = spot(nodes[0])

	start = here          # where the walk sets off, not where it ends up: the
	out, waiting = [], [] # open path is laid out again from this one
	for index in order:
		node = nodes[index]
		point = spot(node)
		if kinds[index] == "offcurve":
			waiting.append(point)
			continue
		out.append((here, list(waiting), point, len(waiting) == 2, node))
		here = point
		waiting = []
	return (out, closed, start)


def rewrite(path, segments, closed, first):
	"""Lay the path out again from its segments. Built as a fresh list and set
	in one go: dropping and inserting nodes one at a time on a live path is
	where an off-curve ends up orphaned."""
	made = []
	if not closed:
		made.append(GSNode(NSPoint(first[0], first[1]), MOVE))
	for handles, end, curved, smooth in segments:
		for handle in handles:
			made.append(GSNode(NSPoint(handle[0], handle[1]), OFFCURVE))
		node = GSNode(NSPoint(end[0], end[1]), CURVE if curved else LINE)
		if smooth:
			try:
				node.smooth = True
			except Exception:
				pass
		made.append(node)
	# A closed path needs no node of its own to start from: the last segment
	# comes back to where the first set off, and that node closing the list is
	# exactly where Glyphs keeps the beginning. Writing it out again as well is
	# how a path ends up with two nodes in the same spot.
	try:
		path.setNodes_(made)
	except Exception:
		try:
			path.nodes = made
		except Exception:
			return False
	try:
		path.closed = closed
	except Exception:
		pass
	return True


def far(a, b):
	return math.hypot(a[0] - b[0], a[1] - b[1]) > NEARBY


def workPath(path, angles):
	"""Cut every curve of this path where it leans. Returns how many nodes the
	path gained."""
	read = segmentsOf(path)
	if read is None:
		return 0
	segments, closed, first = read

	rebuilt, added = [], 0
	for here, handles, end, curved, node in segments:
		wasSmooth = False
		try:
			wasSmooth = bool(node.smooth)
		except Exception:
			pass
		if not curved:
			rebuilt.append((handles, end, False, wasSmooth))
			continue
		p0, p1, p2, p3 = here, handles[0], handles[1], end
		times = []
		for angle in angles:
			times.extend(leanRoots(p0, p1, p2, p3, angle))
		# A cut that would land on a node already there is dropped here and not
		# later: skipping the piece instead of the cut would throw away the
		# stretch of curve that piece was carrying.
		times = sorted(set(round(t, 9) for t in times
			if far(at(p0, p1, p2, p3, t), p0) and far(at(p0, p1, p2, p3, t), p3)))
		if not times:
			rebuilt.append((handles, end, True, wasSmooth))
			continue
		pieces = cutAll(p0, p1, p2, p3, times)
		for index, piece in enumerate(pieces):
			last = index == len(pieces) - 1
			# a cut lands where the curve carries straight on through it, so the
			# node put there is smooth; the segment's own end keeps what it had
			rebuilt.append(([piece[1], piece[2]], piece[3], True,
				wasSmooth if last else True))
			if not last:
				added += 1
	if not added:
		return 0
	return added if rewrite(path, rebuilt, closed, first) else 0


def workingLayers(glyph, font, reach):
	only = font.selectedFontMaster.id if reach == THIS else None
	for layer in glyph.layers:
		if not (layer.isMasterLayer or layer.isSpecialLayer):
			continue
		if only is not None and layer.associatedMasterId != only:
			continue
		yield layer


# ----------------------------------------------------------------------
# The window
# ----------------------------------------------------------------------
class FortyFivePanel(object):
	def __init__(self, font):
		self.font = font
		angle = Glyphs.defaults[PREF_ANGLE]
		if angle is None:
			angle = 45.0
		both = Glyphs.defaults[PREF_BOTH]
		if both is None:
			both = 1

		self.w = vanilla.FloatingWindow((330, 190), "◣ 45°", minSize=(310, 190))

		self.w.angleLabel = vanilla.TextBox((15, 18, 90, 18), "Angle", sizeStyle="small")
		self.w.angle = vanilla.EditText((110, 15, 60, 21), "%g" % float(angle),
			callback=self.somethingChanged, sizeStyle="small")
		self.w.angleUnit = vanilla.TextBox((175, 18, 20, 18), "°", sizeStyle="small")

		self.w.both = vanilla.CheckBox((110, 43, -15, 18), "And the perpendicular",
			value=bool(both), callback=self.somethingChanged, sizeStyle="small")

		self.w.scopeLabel = vanilla.TextBox((15, 73, 90, 18), "Scope", sizeStyle="small")
		self.w.scope = vanilla.PopUpButton((110, 70, -15, 21), SCOPES,
			sizeStyle="small")
		self.w.scope.set(int(Glyphs.defaults[PREF_SCOPE] or 0))

		self.w.reachLabel = vanilla.TextBox((15, 103, 90, 18), "Masters", sizeStyle="small")
		self.w.reach = vanilla.PopUpButton((110, 100, -15, 21), REACH,
			sizeStyle="small")
		self.w.reach.set(int(Glyphs.defaults[PREF_REACH] or 0))

		self.w.info = vanilla.TextBox((15, 130, -15, 26), "", sizeStyle="small")

		self.w.cancelButton = vanilla.Button((-190, -32, 80, 20), "Cancel", callback=self.cancel)
		self.w.applyButton = vanilla.Button((-95, -32, 80, 20), "Add", callback=self.apply)
		self.w.setDefaultButton(self.w.applyButton)
		self.somethingChanged(None)
		self.w.open()
		self.w.makeKey()

	def closePanel(self):
		try:
			self.w.close()
		except TypeError:
			# PyObjC bridge bug in some Glyphs builds: NSWindow.close misbridged
			self.w._window.performClose_(None)

	def angles(self):
		try:
			angle = float(str(self.w.angle.get()).strip().replace(",", ".").rstrip("°"))
		except ValueError:
			return None
		return [angle, angle + 90.0] if self.w.both.get() else [angle]

	def somethingChanged(self, sender):
		angles = self.angles()
		if angles is None:
			self.w.info.set("An angle in degrees, please.")
			return
		self.w.info.set("A node wherever a curve leans at %s." % " or ".join(
			"%g°" % (a % 180.0) for a in angles))

	def cancel(self, sender):
		self.closePanel()

	def apply(self, sender):
		angles = self.angles()
		if angles is None:
			vanilla.dialogs.message("45°", "An angle in degrees, please.")
			return
		Glyphs.defaults[PREF_ANGLE] = float(str(self.w.angle.get()).strip().replace(",", "."))
		Glyphs.defaults[PREF_BOTH] = self.w.both.get()
		Glyphs.defaults[PREF_SCOPE] = self.w.scope.get()
		Glyphs.defaults[PREF_REACH] = self.w.reach.get()

		if self.w.scope.get() == WHOLE:
			glyphs = list(self.font.glyphs)
		else:
			glyphs = [layer.parent for layer in self.font.selectedLayers or []]
			if not glyphs:
				glyphs = list(self.font.selection or [])
		if not glyphs:
			vanilla.dialogs.message("45°", "Select a glyph first, or ask for the whole font.")
			return

		reach = self.w.reach.get()
		added, touched = 0, 0
		self.font.disableUpdateInterface()
		try:
			for glyph in glyphs:
				gained = 0
				glyph.beginUndo()
				for layer in workingLayers(glyph, self.font, reach):
					for path in list(layer.paths):
						gained += workPath(path, angles)
				glyph.endUndo()
				if gained:
					added += gained
					touched += 1
		finally:
			self.font.enableUpdateInterface()

		if not added:
			vanilla.dialogs.message("45°",
				"Nothing leans that way — no curve in there reaches %s."
				% " or ".join("%g°" % (a % 180.0) for a in angles))
			return
		Glyphs.showNotification("45°", "%d node%s in %d glyph%s." % (
			added, "" if added == 1 else "s", touched, "" if touched == 1 else "s"))
		self.closePanel()


font = Glyphs.font
if font is None:
	vanilla.dialogs.message("45°", "No font open.")
else:
	FortyFivePanel(font)
