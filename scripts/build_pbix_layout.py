import json, zipfile, random, copy

SRC = "/home/claude/pbix/financial.pbix"
OUT = "/mnt/user-data/outputs/financial_dashboard.pbix"
random.seed(11)

# ---------- palette ----------
NAVY, BLUE, TEAL, ORANGE, RED, GREY, INK = "#0B2545", "#1F6F8B", "#17A398", "#F29E4C", "#D1495B", "#6B7280", "#1F2937"
PAGE_BG, WHITE, BORDER = "#F3F5F9", "#FFFFFF", "#E1E6EF"

def hid(): return ''.join(random.choice('0123456789abcdef') for _ in range(20))
def lit(v): return {"expr": {"Literal": {"Value": v}}}
def S(s): return lit("'%s'" % s)
def N(n): return lit("%sD" % n)
def L(n): return lit("%sL" % n)
def B(b): return lit("true" if b else "false")
def color(c): return {"solid": {"color": S(c)}}
def J(o): return json.dumps(o, separators=(',', ':'), ensure_ascii=False)

ALIAS = {"vw_transactions": "v", "Date": "d", "_Measures": "m"}
class F:
    def __init__(self, entity, prop, kind, native=None):
        self.e, self.p, self.k, self.native = entity, prop, kind, native or prop
    @property
    def qref(self): return "%s.%s" % (self.e, self.p)
    def expr(self):
        key = "Column" if self.k == "c" else "Measure"
        return {key: {"Expression": {"SourceRef": {"Source": ALIAS[self.e]}}, "Property": self.p}}
    def select(self):
        d = self.expr(); d["Name"] = self.qref; d["NativeReferenceName"] = self.native; return d

def col(e, p, native=None): return F(e, p, "c", native)
def mea(p, native=None): return F("_Measures", p, "m", native)

def prototype(fields, order=None):
    ents = []
    for f in fields + ([order[0]] if order else []):
        if f.e not in ents: ents.append(f.e)
    q = {"Version": 2,
         "From": [{"Name": ALIAS[e], "Entity": e, "Type": 0} for e in ents],
         "Select": [f.select() for f in fields]}
    if order:
        q["OrderBy"] = [{"Direction": order[1], "Expression": order[0].expr()}]
    return q

def proj(**roles):
    out = {}
    for r, fl in roles.items():
        out[r] = [{"queryRef": f.qref, **({"active": True} if r in ("Category", "Rows", "Columns") else {})} for f in fl]
    return out

# ---------- container-level formatting ----------
def vcobj(title=None, bg=WHITE, border=True, show_bg=True):
    d = {"background": [{"properties": {"show": B(show_bg), "color": color(bg), "transparency": N(0)}}]}
    if border:
        d["border"] = [{"properties": {"show": B(True), "color": color(BORDER), "radius": N(8)}}]
    if title:
        d["title"] = [{"properties": {"show": B(True), "text": S(title), "fontColor": color(NAVY),
                                       "fontSize": N(12), "bold": B(True), "alignment": S("left")}}]
    return d

visuals_by_page = {}
class Page:
    def __init__(self, name):
        self.name, self.items, self.z = name, [], 0
    def add(self, x, y, w, h, single, filters="[]"):
        cfg = {"name": hid(),
               "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": self.z, "width": w, "height": h, "tabOrder": self.z}}],
               "singleVisual": single}
        self.items.append({"x": x, "y": y, "z": self.z, "width": w, "height": h, "config": J(cfg), "filters": filters})
        self.z += 1

def textbox(page, x, y, w, h, text="", size=12, bold=False, fcolor=WHITE, bg=None, align="left", font="Segoe UI"):
    run = {"value": text}
    if text:
        run["textStyle"] = {"fontFamily": font, "fontSize": "%dpt" % size, "color": fcolor, **({"fontWeight": "bold"} if bold else {})}
    para = {"textRuns": [run]}
    if align != "left": para["horizontalTextAlignment"] = align
    single = {"visualType": "textbox", "drillFilterOtherVisuals": True,
              "objects": {"general": [{"properties": {"paragraphs": [para]}}]},
              "vcObjects": {"background": [{"properties": {"show": B(bg is not None), **({"color": color(bg), "transparency": N(0)} if bg else {})}}]}}
    page.add(x, y, w, h, single)

def header(page, title):
    textbox(page, 0, 0, 1280, 64, bg=NAVY)
    textbox(page, 24, 12, 720, 40, title, size=22, bold=True, font="Segoe UI Semibold")
    textbox(page, 760, 20, 496, 26, "MySQL + Power BI  |  FY 2023-24  |  Synthetic dataset", size=10, fcolor="#C9D6EA", align="right")

def slicer(page, x, y, w, h, f, title):
    single = {"visualType": "slicer", "projections": {"Values": [{"queryRef": f.qref, "active": True}]},
              "prototypeQuery": prototype([f]), "drillFilterOtherVisuals": True,
              "objects": {"data": [{"properties": {"mode": S("Dropdown")}}],
                          "header": [{"properties": {"show": B(False)}}]},
              "vcObjects": vcobj(title)}
    page.add(x, y, w, h, single)

def card(page, x, y, w, h, f, accent, units=1000000, prec=2):
    textbox(page, x, y, w, 5, bg=accent)  # accent strip
    single = {"visualType": "card", "projections": {"Values": [{"queryRef": f.qref}]},
              "prototypeQuery": prototype([f]), "drillFilterOtherVisuals": True,
              "objects": {"labels": [{"properties": {"color": color(NAVY), "fontSize": N(28),
                                                      "labelDisplayUnits": N(units), "labelPrecision": L(prec)}}],
                          "categoryLabels": [{"properties": {"show": B(True), "color": color(GREY), "fontSize": N(11)}}]},
              "vcObjects": vcobj()}
    page.add(x, y + 5, w, h - 5, single)

AXIS = lambda: {"showAxisTitle": B(False), "fontSize": N(9), "labelColor": color(GREY)}

def line(page, x, y, w, h, cat, ys, colors, title, units=1000000):
    single = {"visualType": "lineChart", "projections": proj(Category=[cat], Y=ys),
              "prototypeQuery": prototype([cat] + ys, order=(cat, 1)), "drillFilterOtherVisuals": True,
              "objects": {"legend": [{"properties": {"show": B(True), "position": S("Top"), "fontSize": N(10)}}],
                          "categoryAxis": [{"properties": AXIS()}],
                          "valueAxis": [{"properties": {**AXIS(), "labelDisplayUnits": N(units), "gridlineColor": color("#E8ECF3")}}],
                          "dataPoint": [{"properties": {"fill": color(c)}, "selector": {"metadata": f.qref}} for f, c in zip(ys, colors)],
                          "lineStyles": [{"properties": {"strokeWidth": L(3), "showMarker": B(False)}}]},
              "vcObjects": vcobj(title)}
    page.add(x, y, w, h, single)

def bars(page, x, y, w, h, vt, cat, y_f, c, title, units=1000000, prec=1, sort_dir=2, sort_by=None):
    order = (sort_by, 1) if sort_by else (y_f, sort_dir)
    single = {"visualType": vt, "projections": proj(Category=[cat], Y=[y_f]),
              "prototypeQuery": prototype([cat, y_f], order=order), "drillFilterOtherVisuals": True,
              "objects": {"legend": [{"properties": {"show": B(False)}}],
                          "categoryAxis": [{"properties": AXIS()}],
                          "valueAxis": [{"properties": {"show": B(False), "showAxisTitle": B(False), "gridlineShow": B(False)}}],
                          "labels": [{"properties": {"show": B(True), "fontSize": N(9), "color": color(INK),
                                                       "labelDisplayUnits": N(units), "labelPrecision": L(prec)}}],
                          "dataPoint": [{"properties": {"fill": color(c)}}]},
              "vcObjects": vcobj(title)}
    page.add(x, y, w, h, single)

def donut(page, x, y, w, h, cat, y_f, title):
    single = {"visualType": "donutChart", "projections": proj(Category=[cat], Y=[y_f]),
              "prototypeQuery": prototype([cat, y_f], order=(y_f, 2)), "drillFilterOtherVisuals": True,
              "objects": {"legend": [{"properties": {"show": B(True), "position": S("Right"), "fontSize": N(10)}}],
                          "labels": [{"properties": {"show": B(True), "labelStyle": S("Percent of total"), "fontSize": N(9)}}]},
              "vcObjects": vcobj(title)}
    page.add(x, y, w, h, single)

def table_objs():
    return {"columnHeaders": [{"properties": {"fontColor": color(WHITE), "backColor": color(NAVY), "fontSize": N(10), "bold": B(True)}}],
            "values": [{"properties": {"fontSize": N(10), "fontColor": color(INK)}}],
            "grid": [{"properties": {"gridHorizontal": B(True), "gridHorizontalColor": color("#E8ECF3"), "gridVertical": B(False), "rowPadding": L(3)}}]}

def not_blank_filter(entity, prop):
    c = {"Column": {"Expression": {"SourceRef": {"Source": "v"}}, "Property": prop}}
    return J([{"name": hid(), "expression": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
               "type": "Advanced",
               "filter": {"Version": 2, "From": [{"Name": "v", "Entity": entity, "Type": 0}],
                          "Where": [{"Condition": {"Not": {"Expression": {"Comparison": {"ComparisonKind": 0, "Left": c, "Right": {"Literal": {"Value": "null"}}}}}}}]}}])

def table(page, x, y, w, h, fields, title, order=None, filters="[]"):
    single = {"visualType": "tableEx", "projections": {"Values": [{"queryRef": f.qref} for f in fields]},
              "prototypeQuery": prototype(fields, order=order), "drillFilterOtherVisuals": True,
              "objects": table_objs(), "vcObjects": vcobj(title)}
    page.add(x, y, w, h, single, filters)

def matrix(page, x, y, w, h, rows, cols, vals, title):
    fields = rows + cols + vals
    single = {"visualType": "pivotTable", "projections": proj(Rows=rows, Columns=cols, Values=vals),
              "prototypeQuery": prototype(fields), "drillFilterOtherVisuals": True,
              "objects": {"columnHeaders": table_objs()["columnHeaders"],
                          "rowHeaders": [{"properties": {"fontSize": N(10), "fontColor": color(INK)}}],
                          "values": table_objs()["values"],
                          "grid": table_objs()["grid"]},
              "vcObjects": vcobj(title)}
    page.add(x, y, w, h, single)

# ---------- fields ----------
V, D, M = "vw_transactions", "Date", "_Measures"
revenue   = mea("Total Revenue", "Total Revenue (₹ M)")
expenses  = mea("Total Expenses", "Total Expenses (₹ M)")
profit    = mea("Net Profit", "Net Profit (₹ M)")
margin    = mea("Profit Margin %", "Profit Margin %")
avgtxn    = mea("Avg Transaction Value", "Avg Transaction Value (₹)")
txncount  = mea("Transaction Count")
failrate  = mea("Failed Txn Rate %")
revly     = mea("Revenue LY")
revyoy    = mea("Revenue YoY %")
revytd    = mea("Revenue YTD", "Revenue YTD (₹ M)")
period    = col(D, "period", "Month")
year      = col(D, "year", "Year")
region    = col(V, "region", "Region")
segment   = col(V, "segment", "Segment")
paymode   = col(V, "payment_mode", "Payment Mode")
category  = col(V, "category_name", "Category")
custname  = col(V, "customer_name", "Customer")

M_ = 24; GAP = 16; FULL = 1232
def row_x(n, i, gap=GAP):
    w = (FULL - gap * (n - 1)) / n
    return M_ + i * (w + gap), w

pages = []

# ===== Page 1: Executive Overview =====
p = Page("Executive Overview"); pages.append(p)
header(p, "Financial Performance Dashboard")
slicer(p, 24, 76, 220, 46, year, "Year")
slicer(p, 260, 76, 220, 46, region, "Region")
specs = [(revenue, TEAL, 1000000, 2), (expenses, ORANGE, 1000000, 2), (profit, BLUE, 1000000, 2), (margin, "#8E7DBE", 1, 1), (avgtxn, RED, 1, 0)]
for i, (f, ac, u, pr) in enumerate(specs):
    x, w = row_x(5, i); card(p, x, 134, w, 92, f, ac, u, pr)
line(p, 24, 238, 744, 222, period, [revenue, expenses], [TEAL, ORANGE], "Revenue vs Expenses by Month (₹ M)")
donut(p, 784, 238, 472, 222, category, expenses, "Expense Breakdown by Category")
x, w = row_x(3, 0); bars(p, x, 472, w, 236, "clusteredBarChart", category, revenue, TEAL, "Revenue by Category (₹ M)")
x, w = row_x(3, 1); bars(p, x, 472, w, 236, "clusteredColumnChart", region, revenue, BLUE, "Revenue by Region (₹ M)")
x, w = row_x(3, 2); bars(p, x, 472, w, 236, "clusteredColumnChart", period, profit, "#8E7DBE", "Net Profit by Month (₹ M)", sort_by=period)

# ===== Page 2: Transaction Analysis =====
p = Page("Transaction Analysis"); pages.append(p)
header(p, "Transaction Analysis")
slicer(p, 24, 76, 220, 46, year, "Year")
slicer(p, 260, 76, 220, 46, segment, "Segment")
slicer(p, 496, 76, 220, 46, paymode, "Payment Mode")
specs = [(txncount, BLUE, 1, 0), (failrate, RED, 1, 1), (revyoy, TEAL, 1, 1), (revytd, ORANGE, 1000000, 2)]
for i, (f, ac, u, pr) in enumerate(specs):
    x, w = row_x(4, i); card(p, x, 134, w, 92, f, ac, u, pr)
line(p, 24, 238, 744, 222, period, [revenue, revly], [TEAL, "#9CA3AF"], "Revenue vs Last Year (₹ M)")
bars(p, 784, 238, 472, 222, "clusteredColumnChart", paymode, failrate, RED, "Failed Transaction Rate by Payment Mode", units=1, prec=1)
matrix(p, 24, 472, 600, 236, [category], [year], [revenue], "Revenue by Category and Year")
table(p, 640, 472, 616, 236, [custname, segment, revenue, txncount], "Top Customers by Revenue",
      order=(revenue, 2), filters=not_blank_filter(V, "customer_name"))

# ===== Page 3: Customer Drill-through =====
p = Page("Customer Drill-through"); pages.append(p)
header(p, "Customer Drill-through")
specs = [(revenue, TEAL, 0, 0), (txncount, BLUE, 1, 0), (avgtxn, ORANGE, 1, 0)]
for i, (f, ac, u, pr) in enumerate(specs):
    x, w = row_x(3, i); card(p, x, 76, w, 92, f, ac, u, pr)
line(p, 24, 180, 1232, 236, period, [revenue], [TEAL], "Revenue by Month", units=0)
table(p, 24, 428, 1232, 280, [custname, col(V, "full_date", "Date"), category, col(V, "amount", "Amount"), paymode, col(V, "status", "Status")],
      "Transaction Details", order=(col(V, "full_date"), 1), filters=not_blank_filter(V, "customer_name"))

# ---------- assemble layout ----------
zin = zipfile.ZipFile(SRC)
layout = json.loads(zin.read("Report/Layout").decode("utf-16-le"))
page_bg = J({"objects": {"background": [{"properties": {"color": color(PAGE_BG), "transparency": N(0)}}]}})
sections = []
for i, pg in enumerate(pages):
    sections.append({"id": i, "name": hid(), "displayName": pg.name, "filters": "[]", "ordinal": i,
                     "visualContainers": pg.items, "config": page_bg, "displayOption": 1, "width": 1280, "height": 720})
layout["sections"] = sections
layout_bytes = json.dumps(layout, separators=(',', ':'), ensure_ascii=False).encode("utf-16-le")

# ---------- rewrite zip (drop SecurityBindings, keep everything else byte-identical) ----------
with zipfile.ZipFile(OUT, "w") as zout:
    for info in zin.infolist():
        if info.filename == "SecurityBindings":
            continue
        data = zin.read(info.filename)
        if info.filename == "Report/Layout":
            data = layout_bytes
        if info.filename == "[Content_Types].xml":
            s = data.decode("utf-8-sig") if data[:3] == b"\xef\xbb\xbf" else data.decode("utf-8")
            s = s.replace('<Override PartName="/SecurityBindings" ContentType="" />', "")
            data = (b"\xef\xbb\xbf" if data[:3] == b"\xef\xbb\xbf" else b"") + s.encode("utf-8")
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zout.writestr(zi, data)

print("pages:", [(pg.name, len(pg.items)) for pg in pages])
