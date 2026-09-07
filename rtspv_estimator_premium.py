"""
RTSPV ESTIMATION APPLICATION
Based on the uploaded project/report material:
"Application Software Development for Design of Rooftop Solar PV System"

Features
--------
- Customer/project information
- Rooftop-area and energy-bill input modes
- Dynamic building inputs
- Technical estimation
- Inverter, isolator, AC cable, ACDB/MCCB/CT/busbar selection
- Monthly and 25-year generation tables/charts
- Economic/environmental estimates
- Professional PDF report generation
- Single-file desktop application

Install:
    pip install matplotlib reportlab

Run:
    python rtspv_estimator.py
"""

import math
import os
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# Heavy libraries are loaded only when charts/PDF are actually used.
# This keeps application startup fast.
plt = None
reportlab_available = None

def _load_matplotlib():
    global plt
    if plt is None:
        try:
            import matplotlib.pyplot as _plt
            plt = _plt
        except ImportError:
            return False
    return True

def _load_reportlab():
    global reportlab_available
    if reportlab_available is not None:
        return reportlab_available
    try:
        global colors, A4
        global TA_CENTER, TA_LEFT
        global getSampleStyleSheet, ParagraphStyle
        global mm
        global SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        global RLImage, PageBreak

        from reportlab.lib import colors as _colors
        from reportlab.lib.enums import TA_CENTER as _TA_CENTER, TA_LEFT as _TA_LEFT
        from reportlab.lib.pagesizes import A4 as _A4
        from reportlab.lib.styles import getSampleStyleSheet as _getSampleStyleSheet
        from reportlab.lib.styles import ParagraphStyle as _ParagraphStyle
        from reportlab.lib.units import mm as _mm
        from reportlab.platypus import (
            SimpleDocTemplate as _SimpleDocTemplate,
            Paragraph as _Paragraph,
            Spacer as _Spacer,
            Table as _Table,
            TableStyle as _TableStyle,
            Image as _RLImage,
            PageBreak as _PageBreak
        )

        colors = _colors
        A4 = _A4
        TA_CENTER = _TA_CENTER
        TA_LEFT = _TA_LEFT
        getSampleStyleSheet = _getSampleStyleSheet
        ParagraphStyle = _ParagraphStyle
        mm = _mm
        SimpleDocTemplate = _SimpleDocTemplate
        Paragraph = _Paragraph
        Spacer = _Spacer
        Table = _Table
        TableStyle = _TableStyle
        RLImage = _RLImage
        PageBreak = _PageBreak
        reportlab_available = True
    except ImportError:
        reportlab_available = False
    return reportlab_available


# ---------------------------------------------------------------------------
# SOURCE DATA FROM THE UPLOADED SENIOR PROJECT MATERIAL
# ---------------------------------------------------------------------------

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Appendix A: monthly solar insolation values
MONTHLY_INSOLATION = [
    5.15, 5.40, 5.35, 4.96, 4.37, 3.26,
    2.91, 3.26, 3.84, 4.30, 4.40, 5.00
]

# Appendix A: panel data
PANEL_DATA = {
    275: {"vmax": 32.90, "imax": 8.36, "eff": 16.8},
    300: {"vmax": 32.26, "imax": 9.31, "eff": 18.3},
    325: {"vmax": 37.45, "imax": 8.68, "eff": 17.25},
    350: {"vmax": 38.50, "imax": 9.09, "eff": 18.0},
    375: {"vmax": 40.20, "imax": 9.37, "eff": 19.23},
    400: {"vmax": 41.70, "imax": 9.60, "eff": 20.2},
}

# Appendix A: inverter ratings
INVERTERS = [
    {"kw": 20, "current": 30, "spec": "20 kW, 415V, 50Hz, MPPT"},
    {"kw": 25, "current": 37, "spec": "25 kW, 415V, 50Hz, MPPT"},
    {"kw": 50, "current": 80, "spec": "50 kW, 415V, 50Hz, MPPT"},
    {"kw": 100, "current": 167, "spec": "100 kW, 415V, 50Hz, MPPT"},
]

# Appendix A: solar AC cable ratings
CABLES = [
    (1.5, 22, 13.70, 0.107),
    (2.5, 30, 8.21, 0.0985),
    (4, 42, 5.09, 0.0927),
    (6, 52, 3.39, 0.0884),
    (10, 76, 1.95, 0.0837),
    (16, 95, 1.24, 0.0808),
    (25, 125, 0.80, 0.0805),
    (50, 185, 0.39, 0.075),
    (70, 239, 0.28, 0.074),
    (120, 335, 0.16, 0.0712),
    (150, 385, 0.13, 0.0716),
    (185, 440, 0.11, 0.0718),
    (240, 520, 0.08, 0.071),
    (300, 640, 0.07, 0.071),
    (400, 770, 0.06, 0.070),
    (500, 900, 0.04, 0.070),
    (630, 1030, 0.03, 0.069),
]

ISOLATORS = [
    15, 20, 25, 30, 35, 40, 50, 70, 100, 125, 150, 175,
    200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800,
    1000, 1200
]

MCCBS = {
    63: "63A, 415V, 4Pole, Breaking Capacity-25KA",
    100: "100A, 415V, 4Pole, Breaking Capacity-10KA",
    125: "125A, 415V, 4Pole, Breaking Capacity-36KA",
    150: "150A, 415V, 4Pole, Breaking Capacity-36KA",
    200: "200A, 415V, 4Pole, Breaking Capacity-25KA",
    250: "250A, 415V, 4Pole, Breaking Capacity-50KA",
    300: "300A, 415V, 4Pole, Breaking Capacity-36KA",
    400: "400A, 415V, 4Pole, Breaking Capacity-36KA",
    500: "500A, 415V, 4Pole, Breaking Capacity-36KA",
    800: "800A, 415V, 4Pole, Breaking Capacity-50KA",
    1000: "1000A, 415V, 4Pole, Breaking Capacity-50KA",
}

CT_RATINGS = [50, 100, 150, 200, 250, 400, 500, 800, 1000]
BUSBARS = [50, 100, 150, 200, 250, 400, 500, 1000]


# ---------------------------------------------------------------------------
# CONSTANTS FROM THE DOCUMENTED ALGORITHM
# ---------------------------------------------------------------------------

PLANT_LIFE = 25
SAFETY_FACTOR = 1.20
MAX_VOLTAGE_DROP = 2.0
DEFAULT_INSOLATION = 4.0
DEFAULT_COST_PER_KW = 50000.0
AMC_PER_KW = 600.0
INTEREST_RATE = 0.065
TARIFF = 8.05
POST_PAYBACK_TARIFF = 10.78
CARBON_KG_PER_KWH = 0.82
TREES_DIVISOR = 625.0


# ---------------------------------------------------------------------------
# CALCULATION HELPERS
# ---------------------------------------------------------------------------

def ceil_int(value):
    return max(1, math.ceil(value))


def nearest_rating(required, ratings):
    for value in sorted(ratings):
        if value >= required:
            return value
    return max(ratings)


def select_inverter_configuration(capacity_kw):
    """Select the smallest standard inverter combination using documented ratings."""
    remaining = capacity_kw
    selected = []

    # Prefer 100 kW units for large plants, then 50, 25, 20.
    for inv in sorted(INVERTERS, key=lambda x: x["kw"], reverse=True):
        count = int(remaining // inv["kw"])
        if count:
            for _ in range(count):
                selected.append(inv)
            remaining -= count * inv["kw"]

    if remaining > 1e-9:
        # Smallest inverter that covers the remaining capacity.
        inv = next(i for i in sorted(INVERTERS, key=lambda x: x["kw"])
                   if i["kw"] >= remaining)
        selected.append(inv)

    return selected


def cable_voltage_drop(current, cable_size, length_m, voltage=440.0):
    """Three-phase voltage-drop formula used in the project material."""
    row = next((r for r in CABLES if abs(r[0] - cable_size) < 1e-9), None)
    if row is None:
        raise ValueError("Cable size not found.")
    _, _, resistance, reactance = row

    # Formula as stated in the source:
    # sqrt(3)*I*(R*0.8 + X*0.6)*L*100/(440*1000)
    return (
        math.sqrt(3) * current *
        (resistance * 0.8 + reactance * 0.6) *
        length_m * 100 / (voltage * 1000)
    )


def select_cable(current, length_m):
    required_current = current * SAFETY_FACTOR
    for size, ampacity, resistance, reactance in CABLES:
        if ampacity >= required_current:
            vd = cable_voltage_drop(required_current, size, length_m)
            if vd <= MAX_VOLTAGE_DROP:
                return {
                    "size": size,
                    "ampacity": ampacity,
                    "required_current": required_current,
                    "voltage_drop": vd,
                    "length_m": length_m,
                }

    # If the final standard cable does not satisfy the voltage-drop criterion,
    # return the largest available standard cable with its calculated drop.
    size, ampacity, *_ = CABLES[-1]
    return {
        "size": size,
        "ampacity": ampacity,
        "required_current": required_current,
        "voltage_drop": cable_voltage_drop(required_current, size, length_m),
        "length_m": length_m,
    }


def select_inverter_details(capacity_kw):
    selected = select_inverter_configuration(capacity_kw)
    result = []

    for inv in selected:
        required_current = inv["current"] * SAFETY_FACTOR
        isolator = nearest_rating(required_current, ISOLATORS)
        result.append({
            "kw": inv["kw"],
            "current": inv["current"],
            "spec": inv["spec"],
            "isolator": isolator,
            "isolator_spec": f"{isolator} A, MCB Type, 4P 415V AC",
            "cable": select_cable(inv["current"], 100),
        })

    return result


def calculate_monthly_generation(capacity_kw):
    """Monthly estimate using each month's insolation and month length."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return [
        capacity_kw * insolation * day
        for insolation, day in zip(MONTHLY_INSOLATION, days)
    ]


def calculate_25_year_generation(capacity_kw):
    """
    Year-by-year generation using 1% degradation per year.
    The source report also presents a simplified 0.75 factor for 25 years;
    the application retains that documented lifetime approach in the summary
    while also showing the year-by-year model used for the chart.
    """
    base = capacity_kw * DEFAULT_INSOLATION * 365
    return [base * ((1 - 0.01) ** year) for year in range(PLANT_LIFE)]


def calculate_payback(capacity_kw, cost_per_kw, tariff=TARIFF):
    """
    Iterative payback calculation following the report's stated principle:
    investment + AMC, annual interest, annual savings, then repeat by year.
    """
    investment = capacity_kw * cost_per_kw
    amc = capacity_kw * AMC_PER_KW
    principal = investment + amc

    yearly = []
    cumulative_savings = 0.0

    for year in range(1, PLANT_LIFE + 1):
        principal_with_interest = principal * (1 + INTEREST_RATE)
        efficiency = (1 - 0.01) ** (year - 1)
        annual_savings = capacity_kw * DEFAULT_INSOLATION * 365 * tariff * efficiency
        remaining = principal_with_interest - annual_savings
        yearly.append({
            "year": year,
            "opening_principal": principal,
            "interest": principal * INTEREST_RATE,
            "annual_savings": annual_savings,
            "remaining": max(0.0, remaining),
        })
        cumulative_savings += annual_savings

        if remaining <= 0:
            previous_remaining = principal
            fraction = previous_remaining / annual_savings if annual_savings else 1
            fraction = min(1.0, max(0.0, fraction))
            payback_years = (year - 1) + fraction
            return payback_years, yearly

        principal = remaining

    return float(PLANT_LIFE), yearly


def calculate_project(capacity_kw, panel_wp, cost_per_kw, distance_grid_m,
                      building_rows=None, mode="Rooftop Area",
                      monthly_units=None):
    panel_kw = panel_wp / 1000.0
    total_panels = ceil_int(capacity_kw / panel_kw)

    # Preserve building-wise panel/capacity calculations where available.
    building_results = []
    if building_rows:
        for b in building_rows:
            raw_area = b["length"] * b["breadth"]
            usable_l = max(0.0, b["length"] - 2 * b["parapet"])
            usable_b = max(0.0, b["breadth"] - 2 * b["parapet"])
            utilized = usable_l * usable_b
            b_capacity = utilized / 100.0
            b_panels = ceil_int(b_capacity / panel_kw) if b_capacity > 0 else 0
            building_results.append({
                **b,
                "area": raw_area,
                "utilized_area": utilized,
                "capacity_kw": b_capacity,
                "panels": b_panels,
            })

    inverters = select_inverter_details(capacity_kw)
    total_current = sum(x["current"] * SAFETY_FACTOR for x in inverters)
    acdb_mccb = nearest_rating(total_current, sorted(MCCBS))
    acdb_ct = nearest_rating(total_current, CT_RATINGS)
    acdb_busbar = nearest_rating(total_current, BUSBARS)

    grid_cable = select_cable(total_current / SAFETY_FACTOR, distance_grid_m)

    annual_generation_simple = capacity_kw * DEFAULT_INSOLATION * 365
    generation_25_simple = annual_generation_simple * PLANT_LIFE * 0.75

    monthly_generation = calculate_monthly_generation(capacity_kw)
    yearly_generation = calculate_25_year_generation(capacity_kw)

    total_cost = capacity_kw * cost_per_kw
    payback_years, payback_table = calculate_payback(capacity_kw, cost_per_kw)

    post_payback = (
        capacity_kw * DEFAULT_INSOLATION * 365 * POST_PAYBACK_TARIFF *
        max(0.0, PLANT_LIFE - payback_years)
    )

    fd_amount = total_cost * ((1 + INTEREST_RATE) ** PLANT_LIFE)

    carbon_tonnes = (
        capacity_kw * DEFAULT_INSOLATION * 365 * PLANT_LIFE *
        CARBON_KG_PER_KWH / 1000.0
    )

    trees = (carbon_tonnes * 1000.0) / TREES_DIVISOR

    return {
        "mode": mode,
        "capacity_kw": capacity_kw,
        "panel_wp": panel_wp,
        "panel_data": PANEL_DATA[panel_wp],
        "total_panels": total_panels,
        "building_results": building_results,
        "distance_grid_m": distance_grid_m,
        "inverters": inverters,
        "total_inverter_current": total_current,
        "acdb_rating": acdb_mccb,
        "acdb_mccb_spec": MCCBS[acdb_mccb],
        "acdb_ct_rating": acdb_ct,
        "acdb_ct_spec": f"{acdb_ct}/5A Class-0.5",
        "acdb_busbar_rating": acdb_busbar,
        "acdb_busbar_spec": f"{acdb_busbar}A, 415V, 3PN, Aluminium",
        "grid_cable": grid_cable,
        "annual_generation_simple": annual_generation_simple,
        "generation_25_simple": generation_25_simple,
        "monthly_generation": monthly_generation,
        "yearly_generation": yearly_generation,
        "total_cost": total_cost,
        "amc": capacity_kw * AMC_PER_KW,
        "payback_years": payback_years,
        "payback_display": format_years_months(payback_years),
        "payback_table": payback_table,
        "post_payback": post_payback,
        "fd_amount": fd_amount,
        "carbon_tonnes": carbon_tonnes,
        "trees": trees,
        "monthly_units": monthly_units,
    }


def format_years_months(years):
    whole = int(years)
    months = round((years - whole) * 12)
    if months == 12:
        whole += 1
        months = 0
    return f"{whole} years and {months} months"


def money(value):
    return f"Rs. {value:,.2f}"



# ---------------------------------------------------------------------------
# UPGRADED UI + REPORT LAYER
# ---------------------------------------------------------------------------

class RTSPVApp(tk.Tk):
    """Modern single-window RTSPV estimator UI."""

    BG = "#F4F7FA"
    CARD = "#FFFFFF"
    NAVY = "#102A43"
    NAVY_2 = "#163B5C"
    TEAL = "#0F766E"
    TEAL_LIGHT = "#E6F6F3"
    TEXT = "#243B53"
    MUTED = "#627D98"
    BORDER = "#D9E2EC"
    SUCCESS = "#18794E"
    WARNING = "#B7791F"
    WHITE = "#FFFFFF"

    def __init__(self):
        super().__init__()
        self.title("SolarVision • RTSPV Design & Estimation")
        self.geometry("1280x820")
        self.minsize(1080, 720)
        self.configure(bg=self.BG)

        self.result = None
        self.building_rows = []
        self.chart_paths = []

        self.customer_vars = {
            "name": tk.StringVar(),
            "date": tk.StringVar(value=datetime.now().strftime("%d-%m-%Y")),
            "address": tk.StringVar(),
            "email": tk.StringVar(),
            "phone": tk.StringVar(),
            "site_type": tk.StringVar(value="Building rooftop"),
            "supply": tk.StringVar(value="LT"),
            "phase": tk.StringVar(value="3 phase"),
            "transformer": tk.StringVar(),
            "bi_meter": tk.StringVar(value="Yes"),
            "system": tk.StringVar(value="Grid connected"),
            "cost": tk.StringVar(value=str(int(DEFAULT_COST_PER_KW))),
            "panel": tk.StringVar(value="325"),
            "distance": tk.StringVar(value="100"),
            "mode": tk.StringVar(value="Rooftop Area"),
            "monthly_units": tk.StringVar(value="48000"),
            "num_buildings": tk.StringVar(value="1"),
        }

        self._configure_style()
        self._build_shell()
        self._build_input_page()
        self._build_results_page()
        self._show_page("input")

    # ------------------------------ Styling ------------------------------

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD)
        style.configure("TLabel", background=self.BG, foreground=self.TEXT,
                        font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.CARD, foreground=self.TEXT,
                        font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=self.BG, foreground=self.MUTED,
                        font=("Segoe UI", 9))
        style.configure("CardMuted.TLabel", background=self.CARD, foreground=self.MUTED,
                        font=("Segoe UI", 9))
        style.configure("H1.TLabel", background=self.BG, foreground=self.NAVY,
                        font=("Segoe UI", 24, "bold"))
        style.configure("H2.TLabel", background=self.BG, foreground=self.NAVY,
                        font=("Segoe UI", 15, "bold"))
        style.configure("CardH.TLabel", background=self.CARD, foreground=self.NAVY,
                        font=("Segoe UI", 11, "bold"))
        style.configure("CardValue.TLabel", background=self.CARD, foreground=self.NAVY,
                        font=("Segoe UI", 17, "bold"))
        style.configure("Sidebar.TButton", font=("Segoe UI", 10, "bold"),
                        padding=(12, 10))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"),
                        foreground=self.WHITE, background=self.TEAL,
                        padding=(18, 11), borderwidth=0)
        style.map("Primary.TButton",
                  background=[("active", "#0B5E58"), ("pressed", "#094E49")],
                  foreground=[("disabled", "#A7B8C8"), ("!disabled", self.WHITE)])
        style.configure("Secondary.TButton", font=("Segoe UI", 10, "bold"),
                        foreground=self.NAVY, background="#E8EEF3",
                        padding=(14, 10), borderwidth=0)
        style.map("Secondary.TButton",
                  background=[("active", "#DDE6ED")])
        style.configure("TEntry", fieldbackground=self.WHITE,
                        foreground=self.TEXT, bordercolor=self.BORDER,
                        padding=8)
        style.configure("TCombobox", fieldbackground=self.WHITE,
                        foreground=self.TEXT, padding=7)
        style.configure("Treeview", background=self.WHITE,
                        fieldbackground=self.WHITE, foreground=self.TEXT,
                        rowheight=30, bordercolor=self.BORDER)
        style.configure("Treeview.Heading", background=self.NAVY,
                        foreground=self.WHITE, font=("Segoe UI", 9, "bold"),
                        padding=7)
        style.map("Treeview", background=[("selected", "#D8F0EC")],
                  foreground=[("selected", self.NAVY)])

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=self.NAVY, width=245)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=self.NAVY)
        brand.pack(fill="x", padx=22, pady=(24, 25))

        logo = tk.Canvas(brand, width=42, height=42, bg=self.NAVY,
                         highlightthickness=0)
        logo.pack(side="left")
        logo.create_oval(3, 3, 39, 39, fill=self.TEAL, outline="")
        logo.create_arc(9, 8, 33, 32, start=20, extent=140,
                        outline=self.WHITE, width=2)
        logo.create_line(21, 10, 21, 33, fill=self.WHITE, width=2)

        brand_text = tk.Frame(brand, bg=self.NAVY)
        brand_text.pack(side="left", padx=10)
        tk.Label(brand_text, text="SolarVision", bg=self.NAVY,
                 fg=self.WHITE, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="RTSPV DESIGN SUITE", bg=self.NAVY,
                 fg="#9FB3C8", font=("Segoe UI", 7, "bold")).pack(anchor="w")

        tk.Label(self.sidebar, text="WORKSPACE", bg=self.NAVY,
                 fg="#829AB1", font=("Segoe UI", 8, "bold")).pack(
                     anchor="w", padx=24, pady=(0, 8))

        self.nav_buttons = {}
        self.nav_buttons["input"] = self._nav_button(
            "◈   Project Setup", "input", "Start a new estimate")
        self.nav_buttons["results"] = self._nav_button(
            "◉   Analysis Dashboard", "results", "View calculated results")

        spacer = tk.Frame(self.sidebar, bg=self.NAVY)
        spacer.pack(fill="both", expand=True)

        info = tk.Frame(self.sidebar, bg=self.NAVY_2)
        info.pack(fill="x", padx=14, pady=14)
        tk.Label(info, text="ENGINEERING ESTIMATION", bg=self.NAVY_2,
                 fg="#B8E6DF", font=("Segoe UI", 8, "bold")).pack(
                     anchor="w", padx=12, pady=(11, 4))
        tk.Label(info, text="Technical • Energy • Economic\nEnvironmental analysis",
                 bg=self.NAVY_2, fg="#D9E2EC", justify="left",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(0, 11))

        footer = tk.Frame(self.sidebar, bg=self.NAVY)
        footer.pack(fill="x", padx=22, pady=(0, 18))
        tk.Label(footer, text="25-year planning model", bg=self.NAVY,
                 fg="#829AB1", font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(footer, text="Grid-connected RTSPV", bg=self.NAVY,
                 fg="#9FB3C8", font=("Segoe UI", 8, "bold")).pack(anchor="w")

        self.content = tk.Frame(self, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {}

    def _nav_button(self, text, key, subtitle):
        holder = tk.Frame(self.sidebar, bg=self.NAVY)
        holder.pack(fill="x", padx=12, pady=3)

        button = tk.Button(
            holder, text=text, anchor="w", relief="flat", bd=0,
            bg=self.NAVY, fg="#D9E2EC", activebackground=self.NAVY_2,
            activeforeground=self.WHITE, font=("Segoe UI", 10, "bold"),
            padx=13, pady=10, cursor="hand2",
            command=lambda k=key: self._show_page(k)
        )
        button.pack(fill="x")

        tk.Label(holder, text=subtitle, bg=self.NAVY, fg="#829AB1",
                 font=("Segoe UI", 7)).pack(anchor="w", padx=38, pady=(0, 5))
        return button

    def _show_page(self, key):
        for page in self.pages.values():
            page.pack_forget()
        if key in self.pages:
            self.pages[key].pack(fill="both", expand=True)
        for name, btn in self.nav_buttons.items():
            if name == key:
                btn.configure(bg=self.TEAL, fg=self.WHITE)
            else:
                btn.configure(bg=self.NAVY, fg="#D9E2EC")

    # ------------------------------ Input page ------------------------------

    def _build_input_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["input"] = page

        header = tk.Frame(page, bg=self.BG)
        header.pack(fill="x", padx=28, pady=(25, 14))
        tk.Label(header, text="Project setup", bg=self.BG, fg=self.NAVY,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(
            header,
            text="Enter the site information and design assumptions. "
                 "The application will build the complete estimate automatically.",
            bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(3, 0))

        body = tk.Frame(page, bg=self.BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        canvas = tk.Canvas(body, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.BG)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=900)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Left/right cards
        top = tk.Frame(inner, bg=self.BG)
        top.pack(fill="x", pady=(0, 10))

        customer = self._card(top, "01  Customer & site")
        customer.pack(side="left", fill="both", expand=True, padx=(0, 6))

        technical = self._card(top, "02  Design assumptions")
        technical.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._customer_form(customer)
        self._technical_form(technical)

        mode_card = self._card(inner, "03  Estimation method")
        mode_card.pack(fill="x", pady=10)
        self._mode_form(mode_card)

        self.roof_card = self._card(inner, "04  Rooftop configuration")
        self.roof_card.pack(fill="x", pady=10)
        self._roof_form(self.roof_card)

        self.bill_card = self._card(inner, "04  Energy consumption")
        self.bill_card.pack(fill="x", pady=10)
        tk.Label(
            self.bill_card,
            text="Enter average monthly electricity consumption. "
                 "The documented project algorithm derives the plant capacity "
                 "from this demand.",
            bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(0, 12))

        row = tk.Frame(self.bill_card, bg=self.CARD)
        row.pack(fill="x", padx=18, pady=(0, 15))
        self._field(row, "Average monthly units (kWh)", "monthly_units", 0, 0, 28)

        action = tk.Frame(inner, bg=self.BG)
        action.pack(fill="x", pady=(8, 22))

        ttk.Button(action, text="Calculate complete design  →",
                   style="Primary.TButton", command=self.calculate).pack(
                       side="right", padx=(8, 0))
        ttk.Button(action, text="Reset", style="Secondary.TButton",
                   command=self.clear_all).pack(side="right")

        self._toggle_mode()

    def _card(self, parent, title):
        frame = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER,
                         highlightthickness=1)
        tk.Label(frame, text=title, bg=self.CARD, fg=self.NAVY,
                 font=("Segoe UI", 11, "bold")).pack(
                     anchor="w", padx=18, pady=(15, 12))
        return frame

    def _field(self, parent, label, key, row, col, width=26):
        box = tk.Frame(parent, bg=self.CARD)
        box.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
        tk.Label(box, text=label, bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Entry(box, textvariable=self.customer_vars[key],
                  width=width).pack(fill="x")
        return box

    def _combo(self, parent, label, key, values, row, col, width=24):
        box = tk.Frame(parent, bg=self.CARD)
        box.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
        tk.Label(box, text=label, bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Combobox(box, textvariable=self.customer_vars[key],
                     values=values, state="readonly",
                     width=width).pack(fill="x")
        return box

    def _customer_form(self, parent):
        grid = tk.Frame(parent, bg=self.CARD)
        grid.pack(fill="x", padx=10, pady=(0, 15))
        for c in range(2):
            grid.columnconfigure(c, weight=1)

        self._field(grid, "Customer / organization name", "name", 0, 0)
        self._field(grid, "Report date", "date", 0, 1)
        self._field(grid, "Address", "address", 1, 0)
        self._field(grid, "Email ID", "email", 1, 1)
        self._field(grid, "Phone number", "phone", 2, 0)
        self._field(grid, "Transformer rating", "transformer", 2, 1)

        self._combo(grid, "Area available", "site_type",
                    ["Vacant land", "Building rooftop"], 3, 0)
        self._combo(grid, "Existing installation", "supply",
                    ["HT", "LT"], 3, 1)
        self._combo(grid, "AC supply", "phase",
                    ["3 phase", "1 Phase"], 4, 0)
        self._combo(grid, "Bi-directional meter", "bi_meter",
                    ["Yes", "No"], 4, 1)
        self._combo(grid, "RTSPV system", "system",
                    ["Standalone", "Grid connected"], 5, 0)

    def _technical_form(self, parent):
        grid = tk.Frame(parent, bg=self.CARD)
        grid.pack(fill="x", padx=10, pady=(0, 15))
        for c in range(2):
            grid.columnconfigure(c, weight=1)

        self._combo(grid, "Solar panel rating (Wp)", "panel",
                    [str(x) for x in PANEL_DATA], 0, 0)
        self._field(grid, "ACDB → grid distance (m)", "distance", 0, 1)
        self._field(grid, "Installation cost per kW (Rs.)", "cost", 1, 0)
        self._field(grid, "Average monthly consumption (kWh)", "monthly_units", 1, 1)

        note = tk.Frame(grid, bg=self.TEAL_LIGHT)
        note.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        tk.Label(
            note,
            text="Design basis  •  4 kWh/kW/day  •  25-year life  •  1% annual degradation  •  "
                 "2% maximum voltage drop",
            bg=self.TEAL_LIGHT, fg=self.TEAL,
            font=("Segoe UI", 8, "bold"), padx=10, pady=9
        ).pack(anchor="w")

    def _mode_form(self, parent):
        row = tk.Frame(parent, bg=self.CARD)
        row.pack(fill="x", padx=18, pady=(0, 15))

        for text, value, description in [
            ("Rooftop Area", "Rooftop Area",
             "Size the plant from available roof dimensions."),
            ("Energy Bill", "Energy Bill",
             "Size the plant from average monthly consumption.")
        ]:
            box = tk.Frame(row, bg=self.CARD, highlightbackground=self.BORDER,
                           highlightthickness=1)
            box.pack(side="left", fill="x", expand=True, padx=(0 if value == "Rooftop Area" else 8, 8))
            rb = tk.Radiobutton(
                box, text=text, variable=self.customer_vars["mode"],
                value=value, command=self._toggle_mode,
                bg=self.CARD, fg=self.NAVY, activebackground=self.CARD,
                selectcolor=self.TEAL_LIGHT,
                font=("Segoe UI", 10, "bold"), padx=10, pady=7
            )
            rb.pack(anchor="w")
            tk.Label(box, text=description, bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w", padx=34, pady=(0, 9))

    def _roof_form(self, parent):
        top = tk.Frame(parent, bg=self.CARD)
        top.pack(fill="x", padx=18, pady=(0, 8))
        tk.Label(top, text="Number of buildings", bg=self.CARD, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Entry(top, textvariable=self.customer_vars["num_buildings"],
                  width=8).pack(side="left", padx=8)
        ttk.Button(top, text="Generate fields", style="Secondary.TButton",
                   command=self._create_building_fields).pack(side="left")

        self.building_container = tk.Frame(parent, bg=self.CARD)
        self.building_container.pack(fill="x", padx=10, pady=(0, 15))
        self._create_building_fields()

    def _create_building_fields(self):
        if not hasattr(self, "building_container"):
            return
        for child in self.building_container.winfo_children():
            child.destroy()
        self.building_rows.clear()

        try:
            n = max(1, min(10, int(self.customer_vars["num_buildings"].get())))
        except ValueError:
            n = 1
            self.customer_vars["num_buildings"].set("1")

        headers = ["Building", "Name", "Length (ft)", "Breadth (ft)", "Parapet (ft)"]
        for col, title in enumerate(headers):
            tk.Label(self.building_container, text=title, bg=self.CARD,
                     fg=self.MUTED, font=("Segoe UI", 8, "bold")).grid(
                         row=0, column=col, sticky="w", padx=8, pady=5)

        for i in range(n):
            defaults = ("111", "26") if i == 0 else ("79", "32")
            vars_ = {
                "name": tk.StringVar(value=f"Building {i+1}"),
                "length": tk.StringVar(value=defaults[0]),
                "breadth": tk.StringVar(value=defaults[1]),
                "parapet": tk.StringVar(value="3"),
            }
            self.building_rows.append(vars_)

            tk.Label(self.building_container, text=f"{i+1:02d}",
                     bg=self.CARD, fg=self.NAVY,
                     font=("Segoe UI", 9, "bold")).grid(
                         row=i+1, column=0, padx=8, pady=5, sticky="w")
            for col, key in enumerate(["name", "length", "breadth", "parapet"], 1):
                ttk.Entry(self.building_container, textvariable=vars_[key],
                          width=24 if key == "name" else 14).grid(
                              row=i+1, column=col, padx=8, pady=5, sticky="ew")

    def _toggle_mode(self):
        if not hasattr(self, "roof_card"):
            return
        if self.customer_vars["mode"].get() == "Rooftop Area":
            self.roof_card.pack(fill="x", pady=10)
            self.bill_card.pack_forget()
        else:
            self.roof_card.pack_forget()
            self.bill_card.pack(fill="x", pady=10)

    # ------------------------------ Results page ------------------------------

    def _build_results_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["results"] = page

        header = tk.Frame(page, bg=self.BG)
        header.pack(fill="x", padx=28, pady=(24, 12))
        left = tk.Frame(header, bg=self.BG)
        left.pack(side="left")
        tk.Label(left, text="Analysis dashboard", bg=self.BG, fg=self.NAVY,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        self.result_subtitle = tk.Label(
            left, text="Calculate a project to populate the dashboard.",
            bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)
        )
        self.result_subtitle.pack(anchor="w", pady=(3, 0))

        actions = tk.Frame(header, bg=self.BG)
        actions.pack(side="right", anchor="n")
        ttk.Button(actions, text="← Edit inputs", style="Secondary.TButton",
                   command=lambda: self._show_page("input")).pack(side="left", padx=4)
        ttk.Button(actions, text="Download PDF  ↓", style="Primary.TButton",
                   command=self.download_pdf).pack(side="left", padx=4)

        self.kpi_frame = tk.Frame(page, bg=self.BG)
        self.kpi_frame.pack(fill="x", padx=28, pady=(0, 12))

        self.kpis = {}
        kpi_specs = [
            ("Plant capacity", "capacity", "kW"),
            ("Solar modules", "panels", "modules"),
            ("Annual generation", "annual", "kWh"),
            ("Project investment", "cost", ""),
            ("Payback period", "payback", ""),
            ("25-year CO₂ reduction", "carbon", "tonnes"),
        ]
        for idx, (title, key, unit) in enumerate(kpi_specs):
            card = tk.Frame(self.kpi_frame, bg=self.CARD,
                            highlightbackground=self.BORDER, highlightthickness=1)
            card.grid(row=0, column=idx, sticky="nsew",
                      padx=(0 if idx == 0 else 5, 0))
            self.kpi_frame.columnconfigure(idx, weight=1)
            tk.Label(card, text=title.upper(), bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=12, pady=(12, 3))
            val = tk.Label(card, text="—", bg=self.CARD, fg=self.NAVY,
                           font=("Segoe UI", 15, "bold"))
            val.pack(anchor="w", padx=12)
            tk.Label(card, text=unit, bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(0, 11))
            self.kpis[key] = val

        area = tk.Frame(page, bg=self.BG)
        area.pack(fill="both", expand=True, padx=28, pady=(0, 22))

        self.result_tabs = ttk.Notebook(area)
        self.result_tabs.pack(fill="both", expand=True)

        self.overview_tab = tk.Frame(self.result_tabs, bg=self.BG)
        self.tech_tab = tk.Frame(self.result_tabs, bg=self.BG)
        self.energy_tab = tk.Frame(self.result_tabs, bg=self.BG)
        self.econ_tab = tk.Frame(self.result_tabs, bg=self.BG)
        self.env_tab = tk.Frame(self.result_tabs, bg=self.BG)

        self.result_tabs.add(self.overview_tab, text="Overview")
        self.result_tabs.add(self.tech_tab, text="Technical Design")
        self.result_tabs.add(self.energy_tab, text="Energy")
        self.result_tabs.add(self.econ_tab, text="Economics")
        self.result_tabs.add(self.env_tab, text="Environment")

        self._build_overview_tab()
        self._build_technical_tab()
        self._build_energy_tab()
        self._build_economic_tab()
        self._build_environment_tab()

    def _text_panel(self, parent):
        outer = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER,
                         highlightthickness=1)
        outer.pack(fill="both", expand=True)
        text = tk.Text(outer, wrap="word", bg=self.CARD, fg=self.TEXT,
                       relief="flat", bd=0, padx=18, pady=16,
                       font=("Consolas", 9), insertbackground=self.TEXT)
        text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(outer, command=text.yview)
        scroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=scroll.set)
        return text

    def _build_overview_tab(self):
        grid = tk.Frame(self.overview_tab, bg=self.BG)
        grid.pack(fill="both", expand=True, padx=8, pady=8)

        self.overview_summary = tk.Frame(grid, bg=self.CARD,
                                         highlightbackground=self.BORDER,
                                         highlightthickness=1)
        self.overview_summary.pack(side="left", fill="both", expand=True, padx=(0, 5))

        chart_card = tk.Frame(grid, bg=self.CARD,
                              highlightbackground=self.BORDER,
                              highlightthickness=1)
        chart_card.pack(side="left", fill="both", expand=True, padx=(5, 0))

        tk.Label(self.overview_summary, text="PROJECT SNAPSHOT",
                 bg=self.CARD, fg=self.NAVY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(17, 10))
        self.overview_text = tk.Text(
            self.overview_summary, wrap="word", bg=self.CARD, fg=self.TEXT,
            relief="flat", bd=0, padx=18, pady=8, font=("Segoe UI", 9)
        )
        self.overview_text.pack(fill="both", expand=True)

        tk.Label(chart_card, text="GENERATION PROFILE",
                 bg=self.CARD, fg=self.NAVY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(17, 10))
        self.chart_canvas = tk.Frame(chart_card, bg=self.CARD)
        self.chart_canvas.pack(fill="both", expand=True, padx=12, pady=8)
        self.chart_placeholder = tk.Label(
            self.chart_canvas,
            text="Run the calculation to preview the monthly generation chart.",
            bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)
        )
        self.chart_placeholder.pack(expand=True)

    def _build_technical_tab(self):
        self.technical_text = self._text_panel(self.tech_tab)

    def _build_energy_tab(self):
        toolbar = tk.Frame(self.energy_tab, bg=self.BG)
        toolbar.pack(fill="x", padx=8, pady=8)
        ttk.Button(toolbar, text="Open monthly chart",
                   style="Secondary.TButton",
                   command=self.monthly_chart).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Open 25-year chart",
                   style="Secondary.TButton",
                   command=self.yearly_chart).pack(side="left", padx=3)
        self.energy_text = self._text_panel(self.energy_tab)

    def _build_economic_tab(self):
        self.economic_text = self._text_panel(self.econ_tab)

    def _build_environment_tab(self):
        self.env_text = self._text_panel(self.env_tab)

    def _write(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _show_results(self):
        r = self.result
        self.result_subtitle.configure(
            text=f'{r["mode"]} estimate • {r["capacity_kw"]:.2f} kW system • '
                 f'Generated {datetime.now().strftime("%d %b %Y, %H:%M")}'
        )

        self.kpis["capacity"].configure(text=f'{r["capacity_kw"]:.2f}')
        self.kpis["panels"].configure(text=f'{r["total_panels"]:,}')
        self.kpis["annual"].configure(text=f'{r["annual_generation_simple"]:,.0f}')
        self.kpis["cost"].configure(text=money(r["total_cost"]).replace("Rs. ", "₹ "))
        self.kpis["payback"].configure(text=r["payback_display"])
        self.kpis["carbon"].configure(text=f'{r["carbon_tonnes"]:,.1f}')

        overview = [
            "DESIGN SUMMARY",
            "",
            f'Plant capacity              {r["capacity_kw"]:.2f} kW',
            f'Solar modules               {r["total_panels"]:,} × {r["panel_wp"]} Wp',
            f'Rooftop area                {r["total_roof_area"]:.2f} sq.ft',
            f'Utilized rooftop area       {r["total_utilized_area"]:.2f} sq.ft',
            f'Annual generation           {r["annual_generation_simple"]:,.2f} kWh',
            f'25-year documented estimate {r["generation_25_simple"]:,.2f} kWh',
            "",
            "COMMERCIAL SUMMARY",
            "",
            f'Investment                  {money(r["total_cost"])}',
            f'Payback                     {r["payback_display"]}',
            f'Post-payback profitability  {money(r["post_payback"])}',
            f'FD comparison (25 years)   {money(r["fd_amount"])}',
            "",
            "ENVIRONMENTAL SUMMARY",
            "",
            f'CO₂ reduction               {r["carbon_tonnes"]:,.2f} tonnes',
            f'Equivalent trees            {r["trees"]:,.0f}',
        ]
        self._write(self.overview_text, "\n".join(overview))

        technical = [
            "TECHNICAL DESIGN RESULTS",
            "=" * 82,
            f'Estimation mode                 : {r["mode"]}',
            f'Plant capacity                  : {r["capacity_kw"]:.2f} kW',
            f'Panel rating                    : {r["panel_wp"]} Wp',
            f'Total number of panels          : {r["total_panels"]}',
            f'Total rooftop area              : {r["total_roof_area"]:.2f} sq.ft',
            f'Utilized rooftop area           : {r["total_utilized_area"]:.2f} sq.ft',
            "",
            "INVERTER CONFIGURATION",
            "-" * 82,
        ]
        for i, inv in enumerate(r["inverters"], 1):
            technical.append(
                f'{i:02d}. {inv["spec"]} | output current {inv["current"]} A | '
                f'isolator {inv["isolator_spec"]}'
            )
            technical.append(
                f'    Inverter → ACDB: 3.5C × {inv["cable"]["size"]} sq.mm | '
                f'VD {inv["cable"]["voltage_drop"]:.2f}%'
            )
        technical += [
            "",
            "AC DISTRIBUTION BOARD",
            "-" * 82,
            f'Number of ACDBs                : 1 No.',
            f'Required current               : {r["total_inverter_current"]:.1f} A',
            f'MCCB                           : {r["acdb_mccb_spec"]}',
            f'CT                             : {r["acdb_ct_spec"]}',
            f'Busbar                         : {r["acdb_busbar_spec"]}',
            "",
            "ACDB → GRID",
            "-" * 82,
            f'Cable size                     : 3.5C × {r["grid_cable"]["size"]} sq.mm',
            f'Current capacity               : {r["grid_cable"]["ampacity"]} A',
            f'Voltage drop                   : {r["grid_cable"]["voltage_drop"]:.2f}%',
        ]
        self._write(self.technical_text, "\n".join(technical))

        energy = [
            "ENERGY GENERATION",
            "=" * 82,
            f'Annual generation (simple model) : {r["annual_generation_simple"]:,.2f} kWh',
            f'25-year documented model         : {r["generation_25_simple"]:,.2f} kWh',
            "",
            "MONTHLY GENERATION",
            "-" * 82,
            f'{"Month":<14}{"Insolation":>14}{"Generation (kWh)":>22}',
            "-" * 50,
        ]
        for m, ins, gen in zip(MONTHS, MONTHLY_INSOLATION, r["monthly_generation"]):
            energy.append(f'{m:<14}{ins:>14.2f}{gen:>22,.2f}')
        energy += ["", "25-YEAR GENERATION WITH 1% ANNUAL DEGRADATION",
                   "-" * 82]
        for y, value in enumerate(r["yearly_generation"], 1):
            energy.append(f'Year {y:02d}{"":>12}{value:>18,.2f} kWh')
        self._write(self.energy_text, "\n".join(energy))

        economic = [
            "ECONOMIC ANALYSIS",
            "=" * 82,
            f'Total plant cost               : {money(r["total_cost"])}',
            f'Annual maintenance charge      : {money(r["amc"])}',
            f'Annual interest                : {INTEREST_RATE*100:.1f}%',
            f'Tariff                         : Rs. {TARIFF:.2f}/kWh',
            f'Payback period                 : {r["payback_display"]}',
            f'Post-payback profitability     : {money(r["post_payback"])}',
            f'FD amount after 25 years       : {money(r["fd_amount"])}',
            "",
            "PAYBACK YEAR-BY-YEAR",
            "-" * 82,
            f'{"Year":<8}{"Opening":>18}{"Savings":>18}{"Remaining":>20}',
            "-" * 66,
        ]
        for row in r["payback_table"]:
            economic.append(
                f'{row["year"]:<8}{row["opening_principal"]:>18,.0f}'
                f'{row["annual_savings"]:>18,.0f}{row["remaining"]:>20,.0f}'
            )
        self._write(self.economic_text, "\n".join(economic))

        env = [
            "ENVIRONMENTAL BENEFITS",
            "=" * 82,
            "",
            f'CO₂ reduction over 25 years : {r["carbon_tonnes"]:,.2f} tonnes',
            f'Equivalent matured trees    : {r["trees"]:,.0f}',
            "",
            "Calculation basis",
            "-" * 82,
            f'Carbon factor               : {CARBON_KG_PER_KWH:.2f} kg CO₂/kWh',
            f'Plant life                  : {PLANT_LIFE} years',
            f'Annual degradation          : 1%',
        ]
        self._write(self.env_text, "\n".join(env))

        self._draw_preview_chart()

    def _draw_preview_chart(self):
        if not self.result or not _load_matplotlib():
            return
        for child in self.chart_canvas.winfo_children():
            child.destroy()

        # Embed a compact matplotlib chart into the Tkinter dashboard.
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            fig = Figure(figsize=(5.8, 3.5), dpi=90)
            ax = fig.add_subplot(111)
            ax.bar(MONTHS, self.result["monthly_generation"])
            ax.set_title("Monthly electricity generation", fontsize=10, pad=10)
            ax.set_ylabel("kWh", fontsize=8)
            ax.tick_params(axis="x", labelrotation=35, labelsize=7)
            ax.tick_params(axis="y", labelsize=7)
            ax.grid(axis="y", alpha=0.18)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.chart_canvas)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception:
            self.chart_placeholder = tk.Label(
                self.chart_canvas,
                text="Chart preview unavailable. Use the chart buttons below.",
                bg=self.CARD, fg=self.MUTED, font=("Segoe UI", 9)
            )
            self.chart_placeholder.pack(expand=True)

    # ------------------------------ Calculation ------------------------------

    def calculate(self):
        try:
            mode = self.customer_vars["mode"].get()
            panel_wp = int(self.customer_vars["panel"].get())
            cost = float(self.customer_vars["cost"].get())
            distance = float(self.customer_vars["distance"].get())

            if cost <= 0:
                raise ValueError("Installation cost must be greater than zero.")
            if distance < 0:
                raise ValueError("ACDB-to-grid distance cannot be negative.")

            building_results = None
            total_roof_area = 0.0
            total_utilized_area = 0.0

            if mode == "Rooftop Area":
                building_input = []
                for row in self.building_rows:
                    b = {
                        "name": row["name"].get().strip() or "Unnamed Building",
                        "length": float(row["length"].get()),
                        "breadth": float(row["breadth"].get()),
                        "parapet": float(row["parapet"].get()),
                    }
                    if b["length"] <= 0 or b["breadth"] <= 0 or b["parapet"] < 0:
                        raise ValueError("Check all building dimensions and parapet values.")
                    building_input.append(b)
                    total_roof_area += b["length"] * b["breadth"]
                    total_utilized_area += (
                        max(0, b["length"] - 2*b["parapet"]) *
                        max(0, b["breadth"] - 2*b["parapet"])
                    )
                capacity = total_utilized_area / 100.0
            else:
                monthly_units = float(self.customer_vars["monthly_units"].get())
                if monthly_units <= 0:
                    raise ValueError("Average monthly consumption must be greater than zero.")
                capacity = monthly_units / (DEFAULT_INSOLATION * 30)
                total_roof_area = capacity * 100.0
                total_utilized_area = total_roof_area
                building_input = None

            if capacity <= 0:
                raise ValueError("Calculated plant capacity is zero.")

            self.result = calculate_project(
                capacity_kw=capacity,
                panel_wp=panel_wp,
                cost_per_kw=cost,
                distance_grid_m=distance,
                building_rows=building_input,
                mode=mode,
                monthly_units=self.customer_vars["monthly_units"].get()
            )
            self.result["total_roof_area"] = total_roof_area
            self.result["total_utilized_area"] = total_utilized_area
            self.result["customer"] = {
                k: v.get() for k, v in self.customer_vars.items()
            }

            self._show_results()
            self._show_page("results")

        except Exception as exc:
            messagebox.showerror(
                "Please check the inputs",
                str(exc),
                parent=self
            )

    # ------------------------------ Charts ------------------------------

    def monthly_chart(self):
        if not self.result:
            messagebox.showwarning("No results", "Calculate the project first.", parent=self)
            return
        if not _load_matplotlib():
            messagebox.showerror("Missing package", "Install matplotlib:\npip install matplotlib", parent=self)
            return

        plt.figure(figsize=(10, 5))
        plt.bar(MONTHS, self.result["monthly_generation"])
        plt.xlabel("Month")
        plt.ylabel("Electricity generation (kWh)")
        plt.title("Monthly Average Electricity Generation")
        plt.xticks(rotation=35)
        plt.grid(axis="y", alpha=0.18)
        plt.tight_layout()
        plt.show()

    def yearly_chart(self):
        if not self.result:
            messagebox.showwarning("No results", "Calculate the project first.", parent=self)
            return
        if not _load_matplotlib():
            messagebox.showerror("Missing package", "Install matplotlib:\npip install matplotlib", parent=self)
            return

        plt.figure(figsize=(10, 5))
        plt.plot(range(1, PLANT_LIFE + 1),
                 self.result["yearly_generation"], marker="o")
        plt.xlabel("Year")
        plt.ylabel("Electricity generation (kWh)")
        plt.title("25-Year Electricity Generation with 1% Annual Degradation")
        plt.grid(True, alpha=0.18)
        plt.tight_layout()
        plt.show()

    # ------------------------------ PDF report ------------------------------

    def _pdf_styles(self):
        if not _load_reportlab():
            raise RuntimeError("ReportLab is not installed. Run: pip install reportlab")
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ReportTitleX", parent=styles["Title"], alignment=TA_CENTER,
            fontSize=20, leading=24, textColor=colors.HexColor("#102A43"),
            spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            name="ReportSubtitleX", parent=styles["Normal"], alignment=TA_CENTER,
            fontSize=9, leading=12, textColor=colors.HexColor("#627D98"),
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name="ReportHeadingX", parent=styles["Heading2"], fontSize=12,
            leading=15, textColor=colors.HexColor("#102A43"),
            spaceBefore=8, spaceAfter=7
        ))
        styles.add(ParagraphStyle(
            name="ReportBodyX", parent=styles["BodyText"], fontSize=8.5,
            leading=12, textColor=colors.HexColor("#243B53")
        ))
        styles.add(ParagraphStyle(
            name="ReportSmallX", parent=styles["BodyText"], fontSize=7,
            leading=9, textColor=colors.HexColor("#627D98")
        ))
        return styles

    def _pdf_table(self, data, widths=None):
        if not _load_reportlab():
            raise RuntimeError("ReportLab is not installed. Run: pip install reportlab")
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102A43")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.3),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E2EC")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F5F8FA")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def _make_report_charts(self, folder):
        if plt is None:
            return []

        r = self.result
        paths = []

        monthly_path = os.path.join(folder, "monthly_generation.png")
        plt.figure(figsize=(9, 4.2))
        plt.bar(MONTHS, r["monthly_generation"])
        plt.xlabel("Month")
        plt.ylabel("Generation (kWh)")
        plt.title("Monthly Electricity Generation")
        plt.xticks(rotation=35)
        plt.grid(axis="y", alpha=0.18)
        plt.tight_layout()
        plt.savefig(monthly_path, dpi=180, bbox_inches="tight")
        plt.close()
        paths.append(monthly_path)

        yearly_path = os.path.join(folder, "yearly_generation.png")
        plt.figure(figsize=(9, 4.2))
        plt.plot(range(1, PLANT_LIFE + 1), r["yearly_generation"], marker="o")
        plt.xlabel("Year")
        plt.ylabel("Generation (kWh)")
        plt.title("25-Year Electricity Generation with 1% Annual Degradation")
        plt.grid(True, alpha=0.18)
        plt.tight_layout()
        plt.savefig(yearly_path, dpi=180, bbox_inches="tight")
        plt.close()
        paths.append(yearly_path)

        economic_path = os.path.join(folder, "economic_summary.png")
        labels = ["Plant Cost", "Post-payback Profit", "25Y FD Amount"]
        values = [r["total_cost"], r["post_payback"], r["fd_amount"]]
        plt.figure(figsize=(9, 4.0))
        plt.bar(labels, values)
        plt.ylabel("Amount (Rs.)")
        plt.title("Economic Comparison")
        plt.grid(axis="y", alpha=0.18)
        plt.tight_layout()
        plt.savefig(economic_path, dpi=180, bbox_inches="tight")
        plt.close()
        paths.append(economic_path)

        return paths

    def download_pdf(self):
        if not self.result:
            messagebox.showwarning("No results", "Calculate the project first.", parent=self)
            return
        if not _load_reportlab():
            messagebox.showerror(
                "Missing package",
                "Install ReportLab first:\npip install reportlab",
                parent=self
            )
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save RTSPV Design Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="RTSPV_Design_Estimation_Report.pdf"
        )
        if not path:
            return

        try:
            self._generate_pdf(path)
            messagebox.showinfo(
                "Report ready",
                "Your professional RTSPV report has been generated successfully.",
                parent=self
            )
        except Exception as exc:
            messagebox.showerror("PDF generation failed", str(exc), parent=self)

    def _generate_pdf(self, path):
        if not _load_reportlab():
            raise RuntimeError("ReportLab is not installed. Run: pip install reportlab")
        r = self.result
        customer = r["customer"]
        styles = self._pdf_styles()

        doc = SimpleDocTemplate(
            path, pagesize=A4,
            rightMargin=14*mm, leftMargin=14*mm,
            topMargin=15*mm, bottomMargin=16*mm
        )

        story = []
        story.append(Spacer(1, 8))
        story.append(Paragraph("SOLARVISION", styles["ReportTitleX"]))
        story.append(Paragraph("ROOFTOP SOLAR PV DESIGN & ESTIMATION REPORT",
                               styles["ReportTitleX"]))
        story.append(Paragraph(
            "Technical • Energy • Economic • Environmental Assessment",
            styles["ReportSubtitleX"]
        ))

        # KPI band
        kpi = [
            ["PLANT CAPACITY", "SOLAR MODULES", "ANNUAL GENERATION", "PAYBACK"],
            [f'{r["capacity_kw"]:.2f} kW', f'{r["total_panels"]:,}',
             f'{r["annual_generation_simple"]:,.0f} kWh',
             r["payback_display"]]
        ]
        kt = Table(kpi, colWidths=[43*mm]*4)
        kt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6F6F3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#102A43")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, 0), 6.5),
            ("FONTSIZE", (0, 1), (-1, 1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7E4DD")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7E4DD")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(kt)
        story.append(Spacer(1, 13))

        story.append(Paragraph("1. Customer & Project Details", styles["ReportHeadingX"]))
        customer_data = [
            ["Parameter", "Value"],
            ["Name", customer.get("name", "")],
            ["Date", customer.get("date", "")],
            ["Address", customer.get("address", "")],
            ["Email ID", customer.get("email", "")],
            ["Phone No.", customer.get("phone", "")],
            ["Area type", customer.get("site_type", "")],
            ["Existing installation", customer.get("supply", "")],
            ["AC power supply", customer.get("phase", "")],
            ["Bi-directional meter", customer.get("bi_meter", "")],
            ["RTSPV system", customer.get("system", "")],
            ["Estimation method", r["mode"]],
        ]
        story.append(self._pdf_table(customer_data, [58*mm, 115*mm]))

        story.append(Paragraph("2. Design Inputs & Basis", styles["ReportHeadingX"]))
        inputs = [
            ["Parameter", "Value"],
            ["Solar panel rating", f'{r["panel_wp"]} Wp'],
            ["Installation cost", money(r["total_cost"] / r["capacity_kw"])],
            ["ACDB → grid distance", f'{r["distance_grid_m"]:.2f} m'],
            ["Average solar insolation", "4 kWh/kW/day"],
            ["Plant life", f"{PLANT_LIFE} years"],
            ["Annual degradation", "1%"],
            ["Maximum voltage drop", f"{MAX_VOLTAGE_DROP:.1f}%"],
        ]
        story.append(self._pdf_table(inputs, [75*mm, 98*mm]))

        story.append(Paragraph("3. Rooftop Assessment", styles["ReportHeadingX"]))
        roof = [
            ["Parameter", "Estimated result"],
            ["Total rooftop area", f'{r["total_roof_area"]:.2f} sq.ft'],
            ["Utilized rooftop area", f'{r["total_utilized_area"]:.2f} sq.ft'],
            ["Plant capacity", f'{r["capacity_kw"]:.2f} kW'],
            ["Number of solar panels", str(r["total_panels"])],
        ]
        story.append(self._pdf_table(roof, [75*mm, 98*mm]))

        if r["building_results"]:
            story.append(Spacer(1, 6))
            bdata = [["Building", "Area", "Utilized", "Capacity", "Panels"]]
            for b in r["building_results"]:
                bdata.append([
                    b["name"], f'{b["area"]:.1f} sq.ft',
                    f'{b["utilized_area"]:.1f} sq.ft',
                    f'{b["capacity_kw"]:.2f} kW',
                    str(b["panels"])
                ])
            story.append(self._pdf_table(bdata,
                                          [40*mm, 32*mm, 34*mm, 33*mm, 25*mm]))

        story.append(PageBreak())
        story.append(Paragraph("4. Inverter & Protection Design",
                               styles["ReportHeadingX"]))

        invdata = [["No.", "Inverter", "Current", "Isolator",
                    "Inverter → ACDB cable", "VD"]]
        for i, inv in enumerate(r["inverters"], 1):
            invdata.append([
                str(i), inv["spec"], f'{inv["current"]} A',
                f'{inv["isolator"]} A',
                f'3.5C × {inv["cable"]["size"]} sq.mm',
                f'{inv["cable"]["voltage_drop"]:.2f}%'
            ])
        story.append(self._pdf_table(invdata))

        story.append(Spacer(1, 8))
        acdb = [
            ["ACDB parameter", "Selected specification"],
            ["Number of ACDBs", "1 No."],
            ["Required current", f'{r["total_inverter_current"]:.1f} A'],
            ["MCCB", r["acdb_mccb_spec"]],
            ["Multi-function meter", "CL-0.5, 3PH, 4W, 415V"],
            ["CT", r["acdb_ct_spec"]],
            ["PT", "415/110V"],
            ["Busbar", r["acdb_busbar_spec"]],
            ["ACDB → grid cable", f'3.5C × {r["grid_cable"]["size"]} sq.mm'],
            ["Grid cable voltage drop", f'{r["grid_cable"]["voltage_drop"]:.2f}%'],
        ]
        story.append(self._pdf_table(acdb, [68*mm, 105*mm]))

        story.append(Paragraph("5. Energy Generation", styles["ReportHeadingX"]))
        story.append(Paragraph(
            f'Annual electricity generation: <b>{r["annual_generation_simple"]:,.2f} kWh</b>',
            styles["ReportBodyX"]))
        story.append(Paragraph(
            f'25-year documented estimate: <b>{r["generation_25_simple"]:,.2f} kWh</b>',
            styles["ReportBodyX"]))
        story.append(Spacer(1, 7))

        monthly = [["Month", "Solar insolation", "Generation (kWh)"]]
        for m, ins, gen in zip(MONTHS, MONTHLY_INSOLATION, r["monthly_generation"]):
            monthly.append([m, f"{ins:.2f}", f"{gen:,.2f}"])
        story.append(self._pdf_table(monthly, [58*mm, 52*mm, 63*mm]))

        # Keep chart files alive until after doc.build().
        with tempfile.TemporaryDirectory() as temp:
            chart_paths = self._make_report_charts(temp)

            if chart_paths:
                story.append(PageBreak())
                story.append(Paragraph("6. Visual Analysis",
                                       styles["ReportHeadingX"]))
                story.append(RLImage(chart_paths[0], width=176*mm, height=82*mm))
                story.append(Spacer(1, 8))
                story.append(RLImage(chart_paths[1], width=176*mm, height=82*mm))

                story.append(PageBreak())
                story.append(Paragraph("7. Economic Analysis",
                                       styles["ReportHeadingX"]))
                econ = [
                    ["Parameter", "Estimated result"],
                    ["Total plant cost", money(r["total_cost"])],
                    ["Annual maintenance charge", money(r["amc"])],
                    ["Annual interest", f"{INTEREST_RATE*100:.1f}%"],
                    ["Tariff", f"Rs. {TARIFF:.2f}/kWh"],
                    ["Payback period", r["payback_display"]],
                    ["Post-payback profitability", money(r["post_payback"])],
                    ["FD amount after 25 years", money(r["fd_amount"])],
                ]
                story.append(self._pdf_table(econ, [85*mm, 88*mm]))
                story.append(Spacer(1, 8))
                story.append(RLImage(chart_paths[2], width=176*mm, height=78*mm))
            else:
                story.append(PageBreak())
                story.append(Paragraph("6. Economic Analysis",
                                       styles["ReportHeadingX"]))

            story.append(Paragraph("8. Environmental Benefits",
                                   styles["ReportHeadingX"]))
            env = [
                ["Parameter", "Estimated result"],
                ["CO₂ reduction over 25 years",
                 f'{r["carbon_tonnes"]:,.2f} tonnes'],
                ["Equivalent matured trees",
                 f'{r["trees"]:,.0f}'],
            ]
            story.append(self._pdf_table(env, [85*mm, 88*mm]))

            story.append(Paragraph("9. Final Project Summary",
                                   styles["ReportHeadingX"]))
            final = [
                ["Parameter", "Final estimate"],
                ["Plant capacity", f'{r["capacity_kw"]:.2f} kW'],
                ["Solar modules", str(r["total_panels"])],
                ["Annual generation", f'{r["annual_generation_simple"]:,.2f} kWh'],
                ["Plant investment", money(r["total_cost"])],
                ["Payback period", r["payback_display"]],
                ["Post-payback profitability", money(r["post_payback"])],
                ["CO₂ reduction", f'{r["carbon_tonnes"]:,.2f} tonnes'],
                ["Equivalent trees", f'{r["trees"]:,.0f}'],
            ]
            story.append(self._pdf_table(final, [85*mm, 88*mm]))

            story.append(Spacer(1, 13))
            story.append(Paragraph(
                "<b>Engineering note:</b> This report is an estimation generated from "
                "the calculation method and reference data contained in the project "
                "material. Final installation design, protection coordination, "
                "structural verification, statutory approvals and site-specific "
                "engineering checks should be completed before implementation.",
                styles["ReportSmallX"]
            ))

            def footer(canvas, doc_obj):
                canvas.saveState()
                canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
                canvas.line(14*mm, 12*mm, A4[0]-14*mm, 12*mm)
                canvas.setFont("Helvetica", 7)
                canvas.setFillColor(colors.HexColor("#627D98"))
                canvas.drawString(14*mm, 7*mm, "SolarVision • RTSPV Design & Estimation")
                canvas.drawRightString(
                    A4[0]-14*mm, 7*mm, f"Page {doc_obj.page}"
                )
                canvas.restoreState()

            doc.build(story, onFirstPage=footer, onLaterPages=footer)

    def clear_all(self):
        self.result = None
        self.customer_vars["name"].set("")
        self.customer_vars["date"].set(datetime.now().strftime("%d-%m-%Y"))
        self.customer_vars["address"].set("")
        self.customer_vars["email"].set("")
        self.customer_vars["phone"].set("")
        self.customer_vars["transformer"].set("")
        self.customer_vars["monthly_units"].set("48000")
        self.customer_vars["distance"].set("100")
        self.customer_vars["cost"].set("50000")
        self.customer_vars["panel"].set("325")
        self.customer_vars["num_buildings"].set("1")
        self.customer_vars["mode"].set("Rooftop Area")
        self._create_building_fields()
        self._toggle_mode()
        for key in self.kpis:
            self.kpis[key].configure(text="—")
        self.result_subtitle.configure(
            text="Calculate a project to populate the dashboard."
        )
        self._write(self.overview_text, "")
        self._write(self.technical_text, "")
        self._write(self.energy_text, "")
        self._write(self.economic_text, "")
        self._write(self.env_text, "")
        self._show_page("input")


if __name__ == "__main__":
    app = RTSPVApp()
    app.mainloop()
