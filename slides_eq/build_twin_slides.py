"""Native twin slides (deck slides 20-24, objectIds tw1_slide..tw5_slide). Generate batchUpdate requests for the five native twin slides. Usage: python twin_gen.py <revisionId> <out.json>"""
import json, sys
from PIL import Image

E = 914400
SHA = "a4338b1f4b51e5cc74629e3bd362dbb0ace5f09e"
EQD = "/home/user/CFO_estimation/slides_eq/twin_eq/"
URL = f"https://raw.githubusercontent.com/eitank123/CFO_estimation/{SHA}/slides_eq/twin_eq/"
NAVY = {"red": 0, "green": 0.2, "blue": 0.4}
DARK = {"red": 0.12156863, "green": 0.16078432, "blue": 0.21568628}
GREY = {"red": 0.357, "green": 0.396, "blue": 0.451}
CARD = {"red": 0.9098039, "green": 0.93333334, "blue": 0.9607843}
WHITE = {"red": 1, "green": 1, "blue": 1}
RED = {"red": 0.784, "green": 0.259, "blue": 0.231}
R = []
INS = 19


def ep(page, x, y, w, h, sx=1, sy=1):
    return {"pageObjectId": page, "size": {"width": {"magnitude": int(w * E), "unit": "EMU"}, "height": {"magnitude": int(h * E), "unit": "EMU"}},
            "transform": {"scaleX": sx, "scaleY": sy, "translateX": int(x * E), "translateY": int(y * E), "unit": "EMU"}}


def no_outline(oid, fill=None):
    p = {"outline": {"propertyState": "NOT_RENDERED"}}
    f = "outline"
    if fill is not None:
        p["shapeBackgroundFill"] = {"solidFill": {"color": {"rgbColor": fill}}}
        f += ",shapeBackgroundFill.solidFill.color"
    R.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": p, "fields": f}})


def text(page, oid, x, y, w, h, t, size=15, color=DARK, bold=False, font="Calibri", bullets=False, align=None, space=None,
         shape="TEXT_BOX", fill=None, valign=None):
    R.append({"createShape": {"objectId": oid, "shapeType": shape, "elementProperties": ep(page, x, y, w, h)}})
    if shape != "TEXT_BOX" or fill:
        no_outline(oid, fill)
    if t:
        R.append({"insertText": {"objectId": oid, "text": t}})
        R.append({"updateTextStyle": {"objectId": oid, "textRange": {"type": "ALL"}, "style": {
            "fontFamily": font, "fontSize": {"magnitude": size, "unit": "PT"}, "bold": bold,
            "foregroundColor": {"opaqueColor": {"rgbColor": color}}}, "fields": "fontFamily,fontSize,bold,foregroundColor"}})
        ps, fl = {}, []
        if align:
            ps["alignment"] = align; fl.append("alignment")
        if space:
            ps["spaceBelow"] = {"magnitude": space, "unit": "PT"}; fl.append("spaceBelow")
        if ps:
            R.append({"updateParagraphStyle": {"objectId": oid, "textRange": {"type": "ALL"}, "style": ps, "fields": ",".join(fl)}})
        if bullets:
            R.append({"createParagraphBullets": {"objectId": oid, "textRange": {"type": "ALL"}, "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})
    if valign:
        R.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": {"contentAlignment": valign}, "fields": "contentAlignment"}})


def bold_words(oid, full, words):
    for wd in words:
        i = full.index(wd)
        R.append({"updateTextStyle": {"objectId": oid, "textRange": {"type": "FIXED_RANGE", "startIndex": i, "endIndex": i + len(wd)},
                                      "style": {"bold": True}, "fields": "bold"}})


def img(page, oid, name, x, y, scale=1.0):
    w, h = Image.open(EQD + name + ".png").size
    R.append({"createImage": {"objectId": oid, "url": URL + name + ".png", "elementProperties": ep(page, x, y, w / 300 * scale, h / 300 * scale)}})
    return w / 300 * scale, h / 300 * scale


def line(page, oid, x1, y1, x2, y2, color=NAVY, wt=1.75, arrow=False, dash="SOLID"):
    sx = 1 if x2 >= x1 else -1
    sy = 1 if y2 >= y1 else -1
    w, h = max(abs(x2 - x1), 0.0001), max(abs(y2 - y1), 0.0001)
    R.append({"createLine": {"objectId": oid, "category": "STRAIGHT", "elementProperties": ep(page, x1, y1, w, h, sx, sy)}})
    p = {"lineFill": {"solidFill": {"color": {"rgbColor": color}}}, "weight": {"magnitude": wt, "unit": "PT"}, "dashStyle": dash}
    f = "lineFill.solidFill.color,weight,dashStyle"
    if arrow:
        p["endArrow"] = "FILL_ARROW"; f += ",endArrow"
    R.append({"updateLineProperties": {"objectId": oid, "lineProperties": p, "fields": f}})


def slide(sid, n, title):
    R.append({"createSlide": {"objectId": sid, "insertionIndex": INS + n - 1, "slideLayoutReference": {"predefinedLayout": "BLANK"}}})
    R.append({"createShape": {"objectId": sid + "_rule", "shapeType": "RECTANGLE", "elementProperties": ep(sid, 0.83, 1.23, 11.67, 0.03)}})
    no_outline(sid + "_rule", NAVY)
    text(sid, sid + "_title", 0.73, 0.5, 12.0, 0.7, title, size=31.5, color=NAVY, bold=True, font="Arial")
    text(sid, sid + "_pg", 12.25, 7.0, 0.85, 0.3, f"{INS + n}/34", size=10, color=GREY)


# ---- slide 1: twin idea
s = "tw1_slide"
slide(s, 1, "Twin symbols: a pilot that costs no energy")
t1 = ("A twin is a QPSK symbol whose two coded bits are always equal\n"
      "Its square is then known: j, times the known scrambler sign\n"
      "Squaring the twins gives a CFO line at 2f, coherent over all twins\n"
      "2nd power instead of the 4th power blind QPSK needs: much smaller squaring loss\n"
      "No pilot symbol is sent and no energy is spent: the twins only constrain the code\n"
      "The twins also give the carrier phase (twin phase)")
text(s, "tw1_b", 0.83, 1.5, 7.4, 2.85, t1, size=15, bullets=True, space=6)
bold_words("tw1_b", t1, ["always equal", "CFO line at 2f", "no energy is spent"])
img(s, "tw1_eq_s", "s", 0.83, 4.5)
img(s, "tw1_eq_r", "r", 0.83, 5.15)
img(s, "tw1_eq_w", "w", 0.83, 5.75)
text(s, "tw1_an", 4.3, 5.7, 4.1, 0.55, "ω: known scrambler term. FFT over the twins: line at 2f (blind QPSK uses the 4th power, line at 4f)",
     size=13)
# constellation
cx, cy, d, rr = 10.55, 3.55, 1.05, 0.2
line(s, "tw1_ax_i", 8.75, cy, 12.35, cy, GREY, 1)
line(s, "tw1_ax_q", cx, 1.75, cx, 5.35, GREY, 1)
text(s, "tw1_lab_i", 12.3, cy - 0.2, 0.3, 0.4, "I", size=14, color=GREY)
text(s, "tw1_lab_q", cx + 0.05, 1.5, 0.3, 0.4, "Q", size=14, color=GREY)
line(s, "tw1_diag", cx + 1.45 * d, cy - 1.45 * d, cx - 1.45 * d, cy + 1.45 * d, NAVY, 1.25, dash="DOT")
for oid, sx, sy, filled in (("tw1_p1", 1, -1, True), ("tw1_p2", -1, 1, True), ("tw1_p3", -1, -1, False), ("tw1_p4", 1, 1, False)):
    R.append({"createShape": {"objectId": oid, "shapeType": "ELLIPSE", "elementProperties": ep(s, cx + sx * d - rr, cy + sy * d - rr, 2 * rr, 2 * rr)}})
    R.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": {
        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": NAVY if filled else WHITE}}},
        "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": NAVY}}}, "weight": {"magnitude": 2, "unit": "PT"}}},
        "fields": "shapeBackgroundFill.solidFill.color,outline.outlineFill.solidFill.color,outline.weight"}})
img(s, "tw1_biq1", "biq", cx + d + 0.2, cy - d - 0.65)
img(s, "tw1_biq2", "biq", cx - d - 1.05, cy + d + 0.25)
text(s, "tw1_cap", 8.75, 5.55, 3.75, 0.55, "Filled: twin (diagonal) symbols. Hollow: never a twin before scrambling.", size=13, color=GREY)

# ---- slide 2: moved bits
s = "tw2_slide"
slide(s, 2, "Moved bits: the polar code's own structure makes twins")
img(s, "tw2_eq_x", "x", 0.83, 1.45)
img(s, "tw2_eq_p", "pair", 0.83, 2.15)
t2 = ("The pair is equal in every codeword iff no first-half info bit covers k\n"
      "Each first-half info bit i breaks 2^wt(i) twins\n"
      "Moving m of them (highest weight first, greedy and swap search) to the most reliable frozen second-half positions frees those twins\n"
      "Same payload, same frame, same E: zero extra bits\n"
      "Cost: info bits sit on less reliable bit-channels, a small coding loss")
text(s, "tw2_b", 0.83, 3.0, 7.0, 2.75, t2, size=15, bullets=True, space=6)
bold_words("tw2_b", t2, ["equal in every codeword", "zero extra bits", "Cost:"])
img(s, "tw2_eq_ub", "ub", 0.83, 5.85)
text(s, "tw2_ubl", 3.8, 6.0, 3.0, 0.4, "GA union bound on the loss", size=13, color=GREY)
# codeword
x0, cw = 8.3, 0.5
text(s, "tw2_cwl", x0, 1.45, 4.0, 0.35, "Polar codeword x (length N)", size=13, color=GREY)
for i in range(8):
    oid = f"tw2_c{i}"
    R.append({"createShape": {"objectId": oid, "shapeType": "RECTANGLE", "elementProperties": ep(s, x0 + i * cw, 1.85, cw, 0.45)}})
    R.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": {
        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": NAVY if i in (2, 6) else CARD}}},
        "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": NAVY}}}, "weight": {"magnitude": 1, "unit": "PT"}}},
        "fields": "shapeBackgroundFill.solidFill.color,outline.outlineFill.solidFill.color,outline.weight"}})
line(s, "tw2_half", x0 + 4 * cw, 1.75, x0 + 4 * cw, 2.4, RED, 2)
text(s, "tw2_h1", x0, 2.35, 2.0, 0.3, "first half", size=12, color=GREY, align="CENTER")
text(s, "tw2_h2", x0 + 2.0, 2.35, 2.0, 0.3, "second half", size=12, color=GREY, align="CENTER")
xa, xb = x0 + 2.5 * cw, x0 + 6.5 * cw
img(s, "tw2_xk", "xk", xa + 0.08, 2.95)
img(s, "tw2_xkn", "xkn", xb - 1.0, 2.95)
line(s, "tw2_a1", xa, 2.7, xa, 3.95, NAVY, 2, arrow=True)
line(s, "tw2_a2", xb, 2.7, xb, 3.95, NAVY, 2, arrow=True)
text(s, "tw2_sym", xa - 0.55, 4.0, xb - xa + 1.1, 1.0, "", shape="ROUND_RECTANGLE", fill=CARD)
text(s, "tw2_si", xa - 0.3, 4.05, 0.6, 0.45, "I", size=18, color=NAVY, bold=True, align="CENTER")
text(s, "tw2_sq", xb - 0.3, 4.05, 0.6, 0.45, "Q", size=18, color=NAVY, bold=True, align="CENTER")
text(s, "tw2_sl", xa - 0.4, 4.5, xb - xa + 0.8, 0.4, "one QPSK symbol", size=13, color=GREY, align="CENTER")
text(s, "tw2_res", 8.3, 5.15, 4.2, 0.4, "Equal pair: a diagonal (twin) symbol", size=15, color=NAVY, bold=True, align="CENTER")
text(s, "tw2_n", 8.3, 5.55, 4.2, 1.4, "Twin count is set by the code: 73 on ID 13 (N 4096, 1476 symbols), 100 on ID 3 (N 1024, 456 symbols); "
     "about 6 on the shortened ID 14, too few to use; ID 2 can move only 12 bits. Combined receiver: 18 moved bits + CRC-24 "
     "(frees 8 bits) + list 16 + twin phase", size=13)

# ---- slide 3: repeated bits
s = "tw3_slide"
slide(s, 3, "Repeated bits: repetition makes any number of twins")
t3 = ("Encode the rate-matched (E − t, K) polar code: same K, optimal info set kept\n"
      "Send t of its coded bits twice: the copy goes on the Q bit of the symbol whose I bit carries the original\n"
      "Receiver adds the two LLRs (MRC), so the copy's energy is not wasted\n"
      "Which bits: greedy on the union bound (largest −dUB/dm per round)\n"
      "Placement: arcsine (ends-weighted) stratified jitter over the burst, for a better CFO estimate and no grating lobes\n"
      "Cost: t fewer parity bits (rate up), partly paid back by the MRC\n"
      "ID 13 and ID 3: t = 96 twins; ID 5 and ID 2: t = 32")
text(s, "tw3_b", 0.83, 1.5, 7.4, 4.1, t3, size=15, bullets=True, space=6)
bold_words("tw3_b", t3, ["Send t of its coded bits twice", "adds the two LLRs (MRC)", "Cost:"])
img(s, "tw3_eq_e", "e", 0.83, 5.75)
img(s, "tw3_eq_m", "mrc", 0.83, 6.3)
steps = [("tw3_k0", "Polar encode (E − t, K)", None), ("tw3_k1", "Repeat t coded bits", None),
         ("tw3_k2", "Copy on Q, original on I", None), ("tw3_k3", "Channel", NAVY),
         ("tw3_k4", "MRC: add the two LLRs", None), ("tw3_k5", "CA-SCL decode", None)]
X, W, H, G = 8.85, 3.65, 0.55, 0.3
for i, (oid, t, fc) in enumerate(steps):
    y = 1.5 + i * (H + G)
    text(s, oid, X, y, W, H, t, size=15, color=WHITE if fc else NAVY, bold=False, align="CENTER", shape="ROUND_RECTANGLE",
         fill=fc or CARD, valign="MIDDLE")
    if i:
        line(s, oid + "_a", X + W / 2, y - G, X + W / 2, y, NAVY, 1.75, arrow=True)

# ---- slide 4: difference table
s = "tw4_slide"
slide(s, 4, "Moved vs repeated: the same twins, made two ways")
rows = [["", "Moved bits (18)", "Repeated bits (t = 96)"],
        ["Where twins come from", "The code's own structure: Plotkin pairs freed by moving info bits", "Explicit repetition of coded bits"],
        ["What it costs", "Info set moved to worse bit-channels", "Fewer parity bits (rate up), with MRC gain on the repeated bits"],
        ["Number of twins", "Limited by the code: 73 on ID 13, about 6 on ID 14", "Any t"],
        ["Placement over the burst", "Fixed by the code", "Free (ends-weighted)"],
        ["Extra receiver work", "None", "t LLR additions (MRC)"],
        ["Shortened codes", "Does not work", "Works"]]
R.append({"createTable": {"objectId": "tw4_tab", "rows": len(rows), "columns": 3, "elementProperties": ep(s, 0.83, 1.5, 11.67, 4.6)}})
for r, row in enumerate(rows):
    for c, v in enumerate(row):
        if not v:
            continue
        R.append({"insertText": {"objectId": "tw4_tab", "cellLocation": {"rowIndex": r, "columnIndex": c}, "text": v}})
        R.append({"updateTextStyle": {"objectId": "tw4_tab", "cellLocation": {"rowIndex": r, "columnIndex": c}, "textRange": {"type": "ALL"},
                                      "style": {"fontFamily": "Calibri", "fontSize": {"magnitude": 15, "unit": "PT"}, "bold": r == 0 or c == 0,
                                                "foregroundColor": {"opaqueColor": {"rgbColor": NAVY if (r == 0 or c == 0) else DARK}}},
                                      "fields": "fontFamily,fontSize,bold,foregroundColor"}})
for c, w in enumerate((3.0, 4.335, 4.335)):
    R.append({"updateTableColumnProperties": {"objectId": "tw4_tab", "columnIndices": [c],
                                              "tableColumnProperties": {"columnWidth": {"magnitude": int(w * E), "unit": "EMU"}}, "fields": "columnWidth"}})
R.append({"updateTableCellProperties": {"objectId": "tw4_tab", "tableRange": {"location": {"rowIndex": 0, "columnIndex": 0}, "rowSpan": 7, "columnSpan": 3},
                                        "tableCellProperties": {"contentAlignment": "MIDDLE"}, "fields": "contentAlignment"}})
text(s, "tw4_note", 0.83, 6.3, 11.67, 0.45, "Both send zero pilots and keep the same payload and frame length.", size=15, color=NAVY, bold=True)

# ---- slide 5: data
s = "tw5_slide"
slide(s, 5, "Repeated twins beat moved bits on ID 13 and ID 3")
rows = [["", "ID 13 (QPSK 1/3, 1476 symbols)", "ID 3 (QPSK 1/3, 456 symbols)"],
        ["Repeated 96 vs moved (combined receiver)", "−0.026 dB, MACs per core ×0.88", "−0.153 dB"],
        ["Repeated 96 vs other moved arrangement", "−0.046 dB (moved + 2 extra frozen)", "−0.062 dB vs z0 (p = 0.014)"],
        ["Repeated 96 vs DVB-RCS2", "+0.02 dB Es/N0, −0.38 dB Eb/N0; MACs about ×3.8", "−0.21 dB Es/N0, −0.92 dB Eb/N0; MACs about ×3.6"],
        ["Other", "Twin-phase fallbacks 4-8× fewer with repeated twins", "Repeated 128 no better than z0 (dropped)"]]
R.append({"createTable": {"objectId": "tw5_tab", "rows": len(rows), "columns": 3, "elementProperties": ep(s, 0.83, 1.5, 11.67, 3.4)}})
for r, row in enumerate(rows):
    for c, v in enumerate(row):
        if not v:
            continue
        R.append({"insertText": {"objectId": "tw5_tab", "cellLocation": {"rowIndex": r, "columnIndex": c}, "text": v}})
        R.append({"updateTextStyle": {"objectId": "tw5_tab", "cellLocation": {"rowIndex": r, "columnIndex": c}, "textRange": {"type": "ALL"},
                                      "style": {"fontFamily": "Calibri", "fontSize": {"magnitude": 15, "unit": "PT"}, "bold": r == 0 or c == 0,
                                                "foregroundColor": {"opaqueColor": {"rgbColor": NAVY if (r == 0 or c == 0) else DARK}}},
                                      "fields": "fontFamily,fontSize,bold,foregroundColor"}})
for c, w in enumerate((3.4, 4.135, 4.135)):
    R.append({"updateTableColumnProperties": {"objectId": "tw5_tab", "columnIndices": [c],
                                              "tableColumnProperties": {"columnWidth": {"magnitude": int(w * E), "unit": "EMU"}}, "fields": "columnWidth"}})
R.append({"updateTableCellProperties": {"objectId": "tw5_tab", "tableRange": {"location": {"rowIndex": 0, "columnIndex": 0}, "rowSpan": 5, "columnSpan": 3},
                                        "tableCellProperties": {"contentAlignment": "MIDDLE"}, "fields": "contentAlignment"}})
t5 = ("All twin receivers vs blind without twins (ID 13): MACs per core about 3-4× lower (about 0.2-0.3 M vs 0.8-1.8 M)\n"
      "Undetected errors: 0 in all twin runs\n"
      "In progress: NN retrain and joint threshold retune (ID 13, ID 3); twins on ID 14 (repeated only), ID 5 and ID 2\n"
      "VDE-SAT and ID 42 (BPSK) cannot use twins: every BPSK symbol already has I = Q")
text(s, "tw5_b", 0.83, 5.1, 11.67, 1.65, t5, size=15, bullets=True, space=4)
text(s, "tw5_fn", 0.83, 6.85, 11.2, 0.3, "Before the retune: known timing, BLER 1e-3, base NN. Negative dB: the repeated-twin receiver needs less SNR; "
     "Eb/N0 charges the DVB-RCS2 known symbols. MACs: per core, 32-core model, relative to DVB-RCS2.", size=10, color=GREY)

out = {"requests": R, "writeControl": {"requiredRevisionId": sys.argv[1]}}
json.dump(out, open(sys.argv[2], "w"))
print(len(R), "requests")
