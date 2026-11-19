# MenuTitle: 📋 Supercopy
# -*- coding: utf-8 -*-
__doc__ = """
Copies the selected glyphs as real text, not /glyphnames, so they paste into another Glyphs file or any other app. Ligatures, conjuncts and positional forms go back to the characters they are made of, which makes it work well for complex scripts: Arabic (veh_yehbarree.ar.fina becomes ڤے, lam_alef-ar لا), Hebrew, Devanagari and Bengali conjuncts (k_ssa-deva becomes क्ष), and Latin ligatures (f_f_i becomes ffi).
"""
__version__ = "1.04"

import re

VERSIONE = __version__
SEGNI_SENZA_TESTO = ("Mark",)  # components such as threedotsupabove.ar have no character


def carattere_da_unicode(glifo):
	codici = glifo.unicodes or ([glifo.unicode] if glifo.unicode else [])
	if not codici:
		return None
	return chr(int(codici[0], 16))


def carattere_da_nome(nome, font, suffissi):
	"""Il carattere di una parte del nome (es. 'veh', 'yehbarree')."""
	candidati = [nome] + [nome + "." + s for s in suffissi] + [nome + "-ar", nome + ".ar"]
	for candidato in candidati:
		glifo = font.glyphs[candidato]
		if glifo is not None:
			c = carattere_da_unicode(glifo)
			if c:
				return c
	try:
		from GlyphsApp import Glyphs
		for candidato in candidati:
			info = Glyphs.glyphInfoForName(candidato)
			if info is not None and info.unicode:
				return chr(int(info.unicode, 16))
	except Exception:
		pass
	return None


def testo_da_produzione(glifo, font):
	"""Dal nome di produzione, che scrive la sequenza vera: k_ssa-deva = uni0915094D0937,
	lam_alef-ar = uni06440627, f_f_i = f_f_i. None se non c e o non si legge."""
	try:
		produzione = glifo.productionName
	except Exception:
		produzione = None
	if not produzione:
		return None
	pezzi = []
	for parte in str(produzione).split(".")[0].split("_"):
		if re.fullmatch(r"uni(?:[0-9A-F]{4})+", parte):
			pezzi += [chr(int(parte[i:i + 4], 16)) for i in range(3, len(parte), 4)]
		elif re.fullmatch(r"u[0-9A-F]{4,6}", parte):
			pezzi.append(chr(int(parte[1:], 16)))
		else:
			c = carattere_da_nome(parte, font, [])
			if c is None:
				return None
			pezzi.append(c)
	return "".join(pezzi)


def testo_del_glifo(glifo, font):
	"""Testo del glifo; None se non si sa ricostruire."""
	c = carattere_da_unicode(glifo)
	if c:
		return c
	t = testo_da_produzione(glifo, font)
	if t:
		return t
	base, _, coda = glifo.name.partition(".")
	suffissi = [s for s in coda.split(".") if s]
	pezzi = []
	for parte in base.split("_"):
		c = carattere_da_nome(parte, font, suffissi)
		if c is None:
			if glifo.category in SEGNI_SENZA_TESTO:
				return ""
			return None
		pezzi.append(c)
	return "".join(pezzi)


def layer_scelti(font):
	tab = font.currentTab
	if tab is not None:
		try:
			inizio, lunghezza = int(tab.textCursor), int(tab.textRange)
			if lunghezza > 0:
				return list(tab.layers)[inizio:inizio + lunghezza]
		except Exception:
			pass
	return list(font.selectedLayers or [])


def testo_dei_layer(layers, font):
	testo, saltati = [], []
	for layer in layers:
		if layer is None:
			continue
		if layer.__class__.__name__ == "GSControlLayer":
			testo.append("\n")
			continue
		glifo = layer.parent
		if glifo is None:
			continue
		t = testo_del_glifo(glifo, font)
		if t is None:
			saltati.append(glifo.name)
		else:
			testo.append(t)
	return "".join(testo), saltati


def metti_negli_appunti(testo):
	from AppKit import NSPasteboard, NSPasteboardTypeString
	appunti = NSPasteboard.generalPasteboard()
	appunti.clearContents()
	appunti.setString_forType_(testo, NSPasteboardTypeString)


def main():
	from GlyphsApp import Glyphs
	font = Glyphs.font
	titolo = "Supercopy " + VERSIONE
	if font is None:
		Glyphs.showNotification(titolo, "No font open.")
		return
	testo, saltati = testo_dei_layer(layer_scelti(font), font)
	if not testo:
		Glyphs.showNotification(titolo, "Nothing to copy: select some glyphs.")
		return
	metti_negli_appunti(testo)
	messaggio = "Copied: " + testo
	if saltati:
		messaggio += "  (skipped: " + ", ".join(saltati[:5]) + ")"
	Glyphs.showNotification(titolo, messaggio)
	print(titolo, "→", testo, ("| skipped: " + ", ".join(saltati)) if saltati else "")


if __name__ == "__main__":
	main()
