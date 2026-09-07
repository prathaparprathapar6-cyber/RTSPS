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

# Optional third-party libraries used for charts and PDF.
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage, PageBreak
    )
except ImportError:
    colors = None
    A4 = None
    reportlab_available = False
else:
    reportlab_available = True


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
# GUI
# ---------------------------------------------------------------------------

class RTSPVApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RTSPV Design & Estimation Application")
        self.geometry("1180x780")
        self.minsize(1000, 700)

        self.result = None
        self.building_rows = []

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
        self._build_ui()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Big.TLabel", font=("Segoe UI", 15, "bold"))

    def _build_ui(self):
        header = ttk.Frame(self, padding=(18, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Rooftop Solar PV Design & Estimation",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Application software for technical, energy, economic and environmental estimation",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.input_tab = ttk.Frame(self.notebook, padding=10)
        self.result_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.input_tab, text="1. Project Input")
        self.notebook.add(self.result_tab, text="2. Results")

        self._build_input_tab()
        self._build_result_tab()

    def _build_input_tab(self):
        canvas = tk.Canvas(self.input_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.input_tab, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas)

        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        customer = ttk.LabelFrame(body, text="A. Customer / Project Details",
                                  padding=12, style="Section.TLabelframe")
        customer.pack(fill="x", pady=(0, 10))

        fields = [
            ("Name", "name"), ("Date", "date"), ("Address", "address"),
            ("Email ID", "email"), ("Phone No.", "phone"),
            ("Transformer Rating", "transformer")
        ]
        for row, (label, key) in enumerate(fields):
            ttk.Label(customer, text=label + ":").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            ttk.Entry(customer, textvariable=self.customer_vars[key], width=42).grid(
                row=row, column=1, sticky="ew", padx=5, pady=5
            )

        customer.columnconfigure(1, weight=1)

        ttk.Label(customer, text="Area Type:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Combobox(customer, textvariable=self.customer_vars["site_type"],
                     values=["Vacant land", "Building rooftop"], state="readonly",
                     width=20).grid(row=0, column=3, padx=5)

        ttk.Label(customer, text="Existing Installation:").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Combobox(customer, textvariable=self.customer_vars["supply"],
                     values=["HT", "LT"], state="readonly", width=20).grid(row=1, column=3, padx=5)

        ttk.Label(customer, text="AC Supply:").grid(row=2, column=2, sticky="w", padx=5)
        ttk.Combobox(customer, textvariable=self.customer_vars["phase"],
                     values=["3 phase", "1 Phase"], state="readonly", width=20).grid(row=2, column=3, padx=5)

        ttk.Label(customer, text="Bi-directional Meter:").grid(row=3, column=2, sticky="w", padx=5)
        ttk.Combobox(customer, textvariable=self.customer_vars["bi_meter"],
                     values=["Yes", "No"], state="readonly", width=20).grid(row=3, column=3, padx=5)

        ttk.Label(customer, text="RTSPV System:").grid(row=4, column=2, sticky="w", padx=5)
        ttk.Combobox(customer, textvariable=self.customer_vars["system"],
                     values=["Standalone", "Grid connected"], state="readonly", width=20).grid(row=4, column=3, padx=5)

        mode_frame = ttk.LabelFrame(body, text="B. Estimation Method", padding=12,
                                    style="Section.TLabelframe")
        mode_frame.pack(fill="x", pady=(0, 10))

        ttk.Radiobutton(
            mode_frame, text="Rooftop Area Input",
            variable=self.customer_vars["mode"], value="Rooftop Area",
            command=self._toggle_mode
        ).pack(side="left", padx=10)
        ttk.Radiobutton(
            mode_frame, text="Energy Bill Input",
            variable=self.customer_vars["mode"], value="Energy Bill",
            command=self._toggle_mode
        ).pack(side="left", padx=10)

        common = ttk.LabelFrame(body, text="C. Common Technical / Economic Inputs",
                                padding=12, style="Section.TLabelframe")
        common.pack(fill="x", pady=(0, 10))

        ttk.Label(common, text="Solar Panel Rating (Wp):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(common, textvariable=self.customer_vars["panel"],
                     values=[str(x) for x in PANEL_DATA], state="readonly", width=15).grid(row=0, column=1, padx=5)

        ttk.Label(common, text="ACDB to Grid Distance (m):").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(common, textvariable=self.customer_vars["distance"], width=15).grid(row=0, column=3, padx=5)

        ttk.Label(common, text="Cost per kW (Rs.):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(common, textvariable=self.customer_vars["cost"], width=15).grid(row=1, column=1, padx=5)

        ttk.Label(common, text="Average Monthly Consumption (kWh):").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Entry(common, textvariable=self.customer_vars["monthly_units"], width=15).grid(row=1, column=3, padx=5)

        self.roof_frame = ttk.LabelFrame(body, text="D. Building / Rooftop Information",
                                         padding=12, style="Section.TLabelframe")
        self.roof_frame.pack(fill="x", pady=(0, 10))

        top = ttk.Frame(self.roof_frame)
        top.pack(fill="x")
        ttk.Label(top, text="Number of Buildings:").pack(side="left")
        building_count = ttk.Entry(top, textvariable=self.customer_vars["num_buildings"], width=8)
        building_count.pack(side="left", padx=8)
        ttk.Button(top, text="Create Building Fields",
                   command=self._create_building_fields).pack(side="left")

        self.building_container = ttk.Frame(self.roof_frame)
        self.building_container.pack(fill="x", pady=10)
        self._create_building_fields()

        self.bill_frame = ttk.LabelFrame(body, text="D. Energy Bill Information",
                                        padding=12, style="Section.TLabelframe")
        self.bill_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(
            self.bill_frame,
            text="The application derives plant capacity as Monthly Consumption / (4 × 30),\n"
                 "following the algorithm documented in the uploaded project report."
        ).pack(anchor="w")

        action = ttk.Frame(body, padding=(0, 8))
        action.pack(fill="x")
        ttk.Button(action, text="CALCULATE", command=self.calculate).pack(side="left", padx=(0, 8))
        ttk.Button(action, text="Clear", command=self.clear_all).pack(side="left")
        self._toggle_mode()

    def _create_building_fields(self):
        for child in self.building_container.winfo_children():
            child.destroy()
        self.building_rows.clear()

        try:
            n = int(self.customer_vars["num_buildings"].get())
        except ValueError:
            n = 1
        n = max(1, min(10, n))

        headers = ["Building", "Name", "Length (ft)", "Breadth (ft)", "Parapet (ft)"]
        for col, h in enumerate(headers):
            ttk.Label(self.building_container, text=h, font=("Segoe UI", 9, "bold")).grid(
                row=0, column=col, padx=5, pady=4
            )

        for i in range(n):
            vars_ = {
                "name": tk.StringVar(value=f"Building {i+1}"),
                "length": tk.StringVar(value="111" if i == 0 else "79"),
                "breadth": tk.StringVar(value="26" if i == 0 else "32"),
                "parapet": tk.StringVar(value="3"),
            }
            self.building_rows.append(vars_)

            ttk.Label(self.building_container, text=str(i + 1)).grid(row=i+1, column=0, padx=5)
            ttk.Entry(self.building_container, textvariable=vars_["name"], width=22).grid(row=i+1, column=1, padx=5)
            ttk.Entry(self.building_container, textvariable=vars_["length"], width=14).grid(row=i+1, column=2, padx=5)
            ttk.Entry(self.building_container, textvariable=vars_["breadth"], width=14).grid(row=i+1, column=3, padx=5)
            ttk.Entry(self.building_container, textvariable=vars_["parapet"], width=14).grid(row=i+1, column=4, padx=5)

    def _toggle_mode(self):
        mode = self.customer_vars["mode"].get()
        if mode == "Rooftop Area":
            self.roof_frame.pack(fill="x", pady=(0, 10))
            self.bill_frame.pack_forget()
        else:
            self.roof_frame.pack_forget()
            self.bill_frame.pack(fill="x", pady=(0, 10))

    def _get_float(self, key, positive=True):
        value = float(self.customer_vars[key].get())
        if positive and value <= 0:
            raise ValueError(f"{key} must be greater than zero.")
        return value

    def calculate(self):
        try:
            mode = self.customer_vars["mode"].get()
            panel_wp = int(self.customer_vars["panel"].get())
            cost = float(self.customer_vars["cost"].get())
            distance = float(self.customer_vars["distance"].get())

            if cost <= 0 or distance < 0:
                raise ValueError("Cost must be positive and distance cannot be negative.")

            building_results = None
            total_roof_area = None
            total_utilized_area = None

            if mode == "Rooftop Area":
                building_input = []
                total_roof_area = 0.0
                total_utilized_area = 0.0

                for row in self.building_rows:
                    b = {
                        "name": row["name"].get().strip() or "Unnamed Building",
                        "length": float(row["length"].get()),
                        "breadth": float(row["breadth"].get()),
                        "parapet": float(row["parapet"].get()),
                    }
                    if b["length"] <= 0 or b["breadth"] <= 0 or b["parapet"] < 0:
                        raise ValueError("Building dimensions are invalid.")
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
                    raise ValueError("Monthly consumption must be greater than zero.")
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
            self.notebook.select(self.result_tab)

        except Exception as exc:
            messagebox.showerror("Input Error", str(exc))

    def _build_result_tab(self):
        top = ttk.Frame(self.result_tab)
        top.pack(fill="x")

        self.summary_labels = {}
        summary_specs = [
            ("Plant Capacity", "capacity"),
            ("Solar Panels", "panels"),
            ("Annual Generation", "annual"),
            ("Plant Cost", "cost"),
            ("Payback Period", "payback"),
            ("CO₂ Reduction", "carbon"),
        ]

        for col, (title, key) in enumerate(summary_specs):
            box = ttk.LabelFrame(top, text=title, padding=10)
            box.grid(row=0, column=col, padx=4, sticky="nsew")
            label = ttk.Label(box, text="—", style="Big.TLabel", anchor="center")
            label.pack(fill="x")
            self.summary_labels[key] = label
            top.columnconfigure(col, weight=1)

        notebook = ttk.Notebook(self.result_tab)
        notebook.pack(fill="both", expand=True, pady=12)

        self.technical_tab = ttk.Frame(notebook, padding=8)
        self.energy_tab = ttk.Frame(notebook, padding=8)
        self.economic_tab = ttk.Frame(notebook, padding=8)
        self.env_tab = ttk.Frame(notebook, padding=8)

        notebook.add(self.technical_tab, text="Technical")
        notebook.add(self.energy_tab, text="Energy & Graphs")
        notebook.add(self.economic_tab, text="Economic")
        notebook.add(self.env_tab, text="Environmental")

        self.technical_text = tk.Text(self.technical_tab, wrap="word", font=("Consolas", 10))
        self.technical_text.pack(fill="both", expand=True)

        self.energy_text = tk.Text(self.energy_tab, wrap="word", font=("Consolas", 10))
        self.energy_text.pack(fill="both", expand=True)

        self.economic_text = tk.Text(self.economic_tab, wrap="word", font=("Consolas", 10))
        self.economic_text.pack(fill="both", expand=True)

        self.env_text = tk.Text(self.env_tab, wrap="word", font=("Consolas", 10))
        self.env_text.pack(fill="both", expand=True)

        buttons = ttk.Frame(self.result_tab)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Monthly Generation Chart",
                   command=self.monthly_chart).pack(side="left", padx=4)
        ttk.Button(buttons, text="25-Year Generation Chart",
                   command=self.yearly_chart).pack(side="left", padx=4)
        ttk.Button(buttons, text="Download PDF Report",
                   command=self.download_pdf).pack(side="right", padx=4)

    def _set_text(self, widget, text):
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _show_results(self):
        r = self.result

        self.summary_labels["capacity"].configure(text=f'{r["capacity_kw"]:.2f} kW')
        self.summary_labels["panels"].configure(text=f'{r["total_panels"]:,}')
        self.summary_labels["annual"].configure(text=f'{r["annual_generation_simple"]:,.0f} kWh')
        self.summary_labels["cost"].configure(text=money(r["total_cost"]))
        self.summary_labels["payback"].configure(text=r["payback_display"])
        self.summary_labels["carbon"].configure(text=f'{r["carbon_tonnes"]:,.1f} t')

        technical = []
        technical.append("TECHNICAL DESIGN RESULTS")
        technical.append("=" * 72)
        technical.append(f'Estimation mode                 : {r["mode"]}')
        technical.append(f'Plant capacity                  : {r["capacity_kw"]:.2f} kW')
        technical.append(f'Panel rating                    : {r["panel_wp"]} Wp')
        technical.append(f'Total number of panels          : {r["total_panels"]}')
        technical.append(f'Total rooftop area              : {r["total_roof_area"]:.2f} sq.ft')
        technical.append(f'Utilized rooftop area           : {r["total_utilized_area"]:.2f} sq.ft')
        technical.append("")
        technical.append("INVERTERS")
        for i, inv in enumerate(r["inverters"], 1):
            technical.append(
                f'  {i}. {inv["spec"]} | Current={inv["current"]} A | '
                f'Isolator={inv["isolator_spec"]}'
            )
            technical.append(
                f'     Inverter-to-ACDB cable: 3.5C x {inv["cable"]["size"]} sq.mm | '
                f'VD={inv["cable"]["voltage_drop"]:.2f}%'
            )
        technical.append("")
        technical.append("ACDB")
        technical.append(f'  Number of ACDBs                 : 1')
        technical.append(f'  Required current               : {r["total_inverter_current"]:.1f} A')
        technical.append(f'  MCCB                            : {r["acdb_mccb_spec"]}')
        technical.append(f'  CT                              : {r["acdb_ct_spec"]}')
        technical.append(f'  Busbar                          : {r["acdb_busbar_spec"]}')
        technical.append("")
        technical.append("ACDB TO GRID CABLE")
        technical.append(f'  Cable size                      : 3.5C x {r["grid_cable"]["size"]} sq.mm')
        technical.append(f'  Current capacity                : {r["grid_cable"]["ampacity"]} A')
        technical.append(f'  Calculated voltage drop         : {r["grid_cable"]["voltage_drop"]:.2f}%')
        self._set_text(self.technical_text, "\n".join(technical))

        energy = []
        energy.append("ENERGY GENERATION")
        energy.append("=" * 72)
        energy.append(f'Annual generation (simple model) : {r["annual_generation_simple"]:,.2f} kWh')
        energy.append(f'25-year generation (0.75 factor) : {r["generation_25_simple"]:,.2f} kWh')
        energy.append("")
        energy.append("MONTHLY ESTIMATE")
        energy.append("-" * 72)
        for m, value in zip(MONTHS, r["monthly_generation"]):
            energy.append(f'{m:<12} {value:>14,.2f} kWh')
        energy.append("")
        energy.append("YEAR-BY-YEAR GENERATION WITH 1% DEGRADATION")
        energy.append("-" * 72)
        for y, value in enumerate(r["yearly_generation"], 1):
            energy.append(f'Year {y:02d}      {value:>14,.2f} kWh')
        self._set_text(self.energy_text, "\n".join(energy))

        economic = []
        economic.append("ECONOMIC ANALYSIS")
        economic.append("=" * 72)
        economic.append(f'Plant cost                       : {money(r["total_cost"])}')
        economic.append(f'Annual maintenance charge       : {money(r["amc"])}')
        economic.append(f'Interest rate                    : {INTEREST_RATE*100:.1f}%')
        economic.append(f'Tariff                            : Rs. {TARIFF:.2f}/kWh')
        economic.append(f'Payback period                   : {r["payback_display"]}')
        economic.append(f'Post-payback profitability       : {money(r["post_payback"])}')
        economic.append(f'FD amount after 25 years         : {money(r["fd_amount"])}')
        economic.append("")
        economic.append("PAYBACK TABLE")
        economic.append("-" * 72)
        for row in r["payback_table"]:
            economic.append(
                f'Year {row["year"]:02d} | Opening={money(row["opening_principal"])} | '
                f'Savings={money(row["annual_savings"])} | '
                f'Remaining={money(row["remaining"])}'
            )
        self._set_text(self.economic_text, "\n".join(economic))

        env = []
        env.append("ENVIRONMENTAL BENEFITS")
        env.append("=" * 72)
        env.append(f'Carbon emission reduction over 25 years : {r["carbon_tonnes"]:,.2f} tonnes')
        env.append(f'Equivalent matured trees                : {r["trees"]:,.0f}')
        env.append("")
        env.append("The carbon calculation follows the documented project factor")
        env.append(f'of {CARBON_KG_PER_KWH:.2f} kg CO2 per kWh.')
        self._set_text(self.env_text, "\n".join(env))

    def monthly_chart(self):
        if not self.result:
            messagebox.showwarning("No Results", "Calculate the project first.")
            return
        if plt is None:
            messagebox.showerror("Missing Package", "Install matplotlib: pip install matplotlib")
            return

        plt.figure(figsize=(10, 5))
        plt.bar(MONTHS, self.result["monthly_generation"])
        plt.xlabel("Month")
        plt.ylabel("Electricity Generation (kWh)")
        plt.title("Monthly Average Electricity Generation")
        plt.xticks(rotation=35)
        plt.tight_layout()
        plt.show()

    def yearly_chart(self):
        if not self.result:
            messagebox.showwarning("No Results", "Calculate the project first.")
            return
        if plt is None:
            messagebox.showerror("Missing Package", "Install matplotlib: pip install matplotlib")
            return

        years = list(range(1, PLANT_LIFE + 1))
        plt.figure(figsize=(10, 5))
        plt.plot(years, self.result["yearly_generation"], marker="o")
        plt.xlabel("Year")
        plt.ylabel("Electricity Generation (kWh)")
        plt.title("25-Year Electricity Generation with 1% Annual Degradation")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    # -----------------------------------------------------------------------
    # PDF REPORT
    # -----------------------------------------------------------------------

    def _pdf_styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ReportTitle", parent=styles["Title"], alignment=TA_CENTER,
            fontSize=17, leading=21, spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name="ReportHeading", parent=styles["Heading2"], fontSize=12,
            leading=15, spaceBefore=8, spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name="Small", parent=styles["BodyText"], fontSize=8, leading=10
        ))
        return styles

    def _table(self, data, widths=None):
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f2f6fa")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def _make_chart_files(self, folder):
        r = self.result
        paths = []

        if plt is None:
            return paths

        monthly_path = os.path.join(folder, "monthly_generation.png")
        plt.figure(figsize=(8.5, 4.0))
        plt.bar(MONTHS, r["monthly_generation"])
        plt.xlabel("Month")
        plt.ylabel("Generation (kWh)")
        plt.title("Monthly Electricity Generation")
        plt.xticks(rotation=35)
        plt.tight_layout()
        plt.savefig(monthly_path, dpi=180)
        plt.close()
        paths.append(monthly_path)

        yearly_path = os.path.join(folder, "yearly_generation.png")
        plt.figure(figsize=(8.5, 4.0))
        plt.plot(range(1, PLANT_LIFE + 1), r["yearly_generation"], marker="o")
        plt.xlabel("Year")
        plt.ylabel("Generation (kWh)")
        plt.title("25-Year Electricity Generation")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(yearly_path, dpi=180)
        plt.close()
        paths.append(yearly_path)

        return paths

    def download_pdf(self):
        if not self.result:
            messagebox.showwarning("No Results", "Calculate the project first.")
            return

        if not reportlab_available:
            messagebox.showerror(
                "Missing Package",
                "Install ReportLab first:\npip install reportlab"
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save RTSPV Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="RTSPV_Estimation_Report.pdf"
        )
        if not path:
            return

        try:
            self._generate_pdf(path)
            messagebox.showinfo("Report Generated", f"PDF report saved successfully:\n{path}")
        except Exception as exc:
            messagebox.showerror("PDF Error", str(exc))

    def _generate_pdf(self, path):
        r = self.result
        customer = r["customer"]
        styles = self._pdf_styles()

        doc = SimpleDocTemplate(
            path, pagesize=A4,
            rightMargin=15*mm, leftMargin=15*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )

        story = []

        story.append(Paragraph("ROOFTOP SOLAR PV SYSTEM", styles["ReportTitle"]))
        story.append(Paragraph("DESIGN & ESTIMATION REPORT", styles["ReportTitle"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "Application Software Development for Design of Rooftop Solar PV System",
            styles["Small"]
        ))
        story.append(Spacer(1, 12))

        story.append(Paragraph("1. Customer / Project Details", styles["ReportHeading"]))
        customer_data = [
            ["Parameter", "Value"],
            ["Name", customer.get("name", "")],
            ["Date", customer.get("date", "")],
            ["Address", customer.get("address", "")],
            ["Email ID", customer.get("email", "")],
            ["Phone No.", customer.get("phone", "")],
            ["Existing Installation", customer.get("supply", "")],
            ["AC Power Supply", customer.get("phase", "")],
            ["Bi-directional Meter", customer.get("bi_meter", "")],
            ["RTSPV System", customer.get("system", "")],
            ["Estimation Method", r["mode"]],
        ]
        story.append(self._table(customer_data, [55*mm, 120*mm]))
        story.append(Spacer(1, 10))

        story.append(Paragraph("2. Input Parameters", styles["ReportHeading"]))
        input_data = [
            ["Parameter", "Value"],
            ["Solar panel rating", f'{r["panel_wp"]} Wp'],
            ["Cost per kW", money(r["total_cost"] / r["capacity_kw"])],
            ["ACDB to grid distance", f'{r["distance_grid_m"]:.2f} m'],
            ["Average solar insolation", "4 kWh/kW/day"],
            ["Plant life", f"{PLANT_LIFE} years"],
            ["Safety factor", f"{SAFETY_FACTOR:.2f}"],
            ["Maximum voltage drop", f"{MAX_VOLTAGE_DROP:.1f}%"],
        ]
        story.append(self._table(input_data, [75*mm, 100*mm]))
        story.append(Spacer(1, 10))

        story.append(Paragraph("3. Rooftop Assessment", styles["ReportHeading"]))
        roof_data = [
            ["Parameter", "Result"],
            ["Total rooftop area", f'{r["total_roof_area"]:.2f} sq.ft'],
            ["Utilized rooftop area", f'{r["total_utilized_area"]:.2f} sq.ft'],
            ["Plant capacity", f'{r["capacity_kw"]:.2f} kW'],
            ["Number of solar panels", str(r["total_panels"])],
        ]
        story.append(self._table(roof_data, [75*mm, 100*mm]))

        if r["building_results"]:
            story.append(Spacer(1, 7))
            bdata = [["Building", "Area (sq.ft)", "Utilized (sq.ft)", "Capacity (kW)", "Panels"]]
            for b in r["building_results"]:
                bdata.append([
                    b["name"], f'{b["area"]:.2f}', f'{b["utilized_area"]:.2f}',
                    f'{b["capacity_kw"]:.2f}', str(b["panels"])
                ])
            story.append(self._table(bdata, [42*mm, 32*mm, 35*mm, 32*mm, 25*mm]))

        story.append(Spacer(1, 10))
        story.append(Paragraph("4. Inverter and Protection Selection", styles["ReportHeading"]))

        inv_data = [["No.", "Inverter", "Output Current", "Isolator", "Inverter-ACDB Cable", "VD"]]
        for i, inv in enumerate(r["inverters"], 1):
            inv_data.append([
                str(i), inv["spec"], f'{inv["current"]} A',
                f'{inv["isolator"]} A',
                f'3.5C x {inv["cable"]["size"]} sq.mm',
                f'{inv["cable"]["voltage_drop"]:.2f}%'
            ])
        story.append(self._table(inv_data))

        story.append(Spacer(1, 7))
        acdb_data = [
            ["ACDB Parameter", "Selected Specification"],
            ["Number of ACDBs", "1 No."],
            ["MCCB", r["acdb_mccb_spec"]],
            ["Multi-function meter", "CL-0.5, 3PH, 4W, 415V"],
            ["CT", r["acdb_ct_spec"]],
            ["PT", "415/110V"],
            ["Busbar", r["acdb_busbar_spec"]],
            ["ACDB-to-grid cable", f'3.5C x {r["grid_cable"]["size"]} sq.mm'],
            ["Grid cable voltage drop", f'{r["grid_cable"]["voltage_drop"]:.2f}%'],
        ]
        story.append(self._table(acdb_data, [75*mm, 100*mm]))

        story.append(PageBreak())
        story.append(Paragraph("5. Energy Generation", styles["ReportHeading"]))

        story.append(Paragraph(
            f'Annual electricity generation = {r["annual_generation_simple"]:,.2f} kWh',
            styles["BodyText"]
        ))
        story.append(Paragraph(
            f'25-year generation using the documented 0.75 factor = '
            f'{r["generation_25_simple"]:,.2f} kWh',
            styles["BodyText"]
        ))
        story.append(Spacer(1, 8))

        monthly_data = [["Month", "Solar Insolation", "Generation (kWh)"]]
        for m, ins, gen in zip(MONTHS, MONTHLY_INSOLATION, r["monthly_generation"]):
            monthly_data.append([m, f"{ins:.2f}", f"{gen:,.2f}"])
        story.append(self._table(monthly_data, [55*mm, 55*mm, 65*mm]))

        with tempfile.TemporaryDirectory() as temp:
            chart_paths = self._make_chart_files(temp)
            if chart_paths:
                story.append(PageBreak())
                story.append(Paragraph("6. Generation Graphs", styles["ReportHeading"]))
                story.append(RLImage(chart_paths[0], width=175*mm, height=82*mm))
                story.append(Spacer(1, 7))
                story.append(RLImage(chart_paths[1], width=175*mm, height=82*mm))

                story.append(PageBreak())

        story.append(Paragraph("7. Economic Analysis", styles["ReportHeading"]))
        economic_data = [
            ["Parameter", "Estimated Result"],
            ["Total plant cost", money(r["total_cost"])],
            ["Annual maintenance charge", money(r["amc"])],
            ["Annual interest", f"{INTEREST_RATE*100:.1f}%"],
            ["Tariff", f"Rs. {TARIFF:.2f}/kWh"],
            ["Payback period", r["payback_display"]],
            ["Post-payback profitability", money(r["post_payback"])],
            ["FD amount after 25 years", money(r["fd_amount"])],
        ]
        story.append(self._table(economic_data, [85*mm, 90*mm]))

        story.append(Spacer(1, 10))
        story.append(Paragraph("8. Environmental Benefits", styles["ReportHeading"]))
        env_data = [
            ["Parameter", "Result"],
            ["CO2 reduction over 25 years", f'{r["carbon_tonnes"]:,.2f} tonnes'],
            ["Equivalent matured trees", f'{r["trees"]:,.0f}'],
        ]
        story.append(self._table(env_data, [85*mm, 90*mm]))

        story.append(Spacer(1, 10))
        story.append(Paragraph("9. Final Summary", styles["ReportHeading"]))
        summary_data = [
            ["Parameter", "Final Estimate"],
            ["Plant capacity", f'{r["capacity_kw"]:.2f} kW'],
            ["Solar panels", str(r["total_panels"])],
            ["Annual generation", f'{r["annual_generation_simple"]:,.2f} kWh'],
            ["Plant cost", money(r["total_cost"])],
            ["Payback period", r["payback_display"]],
            ["Post-payback profitability", money(r["post_payback"])],
            ["CO2 reduction", f'{r["carbon_tonnes"]:,.2f} tonnes'],
            ["Equivalent trees", f'{r["trees"]:,.0f}'],
        ]
        story.append(self._table(summary_data, [85*mm, 90*mm]))

        story.append(Spacer(1, 16))
        story.append(Paragraph(
            "Note: This report is an engineering estimation generated from the "
            "calculation method and reference data contained in the project material. "
            "Final installation design, protection coordination, statutory approvals, "
            "structural verification and site-specific engineering should be checked "
            "before implementation.",
            styles["Small"]
        ))

        def footer(canvas, doc_obj):
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.drawCentredString(
                A4[0] / 2, 8*mm,
                f"RTSPV Design & Estimation Report  |  Page {doc_obj.page}"
            )
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)

    def clear_all(self):
        for var in self.customer_vars.values():
            if var == self.customer_vars["date"]:
                continue
        self.result = None
        self.customer_vars["name"].set("")
        self.customer_vars["address"].set("")
        self.customer_vars["email"].set("")
        self.customer_vars["phone"].set("")
        self.customer_vars["transformer"].set("")
        self.customer_vars["monthly_units"].set("48000")
        self.customer_vars["distance"].set("100")
        self.customer_vars["cost"].set("50000")
        self.customer_vars["panel"].set("325")
        self.customer_vars["num_buildings"].set("1")
        self._create_building_fields()

        for widget in [self.technical_text, self.energy_text, self.economic_text, self.env_text]:
            self._set_text(widget, "")

        for label in self.summary_labels.values():
            label.configure(text="—")


if __name__ == "__main__":
    app = RTSPVApp()
    app.mainloop()
