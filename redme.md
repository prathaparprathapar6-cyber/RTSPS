# RTSPV Solar Estimator — Single Phase

## 1. Project Overview

**RTSPV Solar Estimator** is a desktop-based solar photovoltaic (PV) design and estimation application developed using Python.

The application helps users estimate the technical, energy, economic, and environmental performance of a rooftop solar PV system based on project inputs.

The current version is designed specifically for **Single-Phase electrical systems**. Three-phase selection and active three-phase design parameters have been removed from the user interface and calculation workflow.

## 2. Main Objectives

The application is intended to:

- Estimate the required rooftop solar PV system size.
- Calculate the number of solar panels required.
- Estimate inverter requirements.
- Perform single-phase electrical design calculations.
- Select suitable cable and protection parameters.
- Calculate voltage drop for the single-phase circuit.
- Estimate monthly and annual solar generation.
- Estimate long-term 25-year energy generation with degradation.
- Calculate project cost and financial performance.
- Estimate payback period and profitability.
- Compare solar investment with a fixed-deposit (FD) style alternative.
- Estimate CO₂ emission reduction.
- Estimate equivalent trees associated with the environmental benefit.
- Generate a professional PDF project report with tables and charts.

## 3. Technology Used

### Programming Language
- Python 3.x

### GUI
- Tkinter
- ttk

### Report Generation
- ReportLab

### Charts
- Matplotlib

### Main Application Type
- Desktop GUI application

The application uses lazy loading for heavier libraries such as Matplotlib and ReportLab so that the main GUI can start faster.

## 4. System Requirements

### Minimum Software Requirements

- Windows 10 or later
- Python 3.x
- VS Code or another Python-compatible IDE (optional)

### Python Libraries

The application uses:

- `tkinter` — normally included with Python
- `reportlab`
- `matplotlib`

Install the external libraries using:

```bash
pip install reportlab matplotlib
```

## 5. How to Run the Application

Open Command Prompt or PowerShell and run:

```bash
python rtspv_estimator_single_phase.py
```

Example for a specific Python installation:

```powershell
& C:\Users\test\AppData\Local\Programs\Python\Python313\python.exe C:\Users\test\Downloads\rtspv_estimator_single_phase.py
```

## 6. User Input Parameters

The current application provides Single-Phase electrical input parameters.

### Solar / Project Inputs

- Solar panel rating (Wp)
- Installation cost per kW
- Average monthly consumption (kWh)

### Single-Phase Electrical Inputs

- Single-phase voltage (V)
- Inverter rating (kW)
- Inverter rated current (A)
- Number of single-phase inverters
- Inverter-to-DB cable size (sq.mm)
- Main MCB rating (A)
- Single-phase cable length (m)

### Installation Information

- AC supply: Single Phase
- Existing installation: LT

## 7. Single-Phase Electrical Design

The active electrical design is based on a single-phase system.

The application uses a **2-wire single-phase voltage-drop model**.

The voltage-drop calculation follows:

```text
Voltage Drop % =
2 × I × (R × 0.8 + X × 0.6) × L × 100
------------------------------------------------
                    V × 1000
```

Where:

- `I` = current in amperes
- `R` = cable resistance
- `X` = cable reactance
- `L` = cable length in metres
- `V` = single-phase system voltage

The application uses a maximum voltage-drop criterion of approximately:

```text
2%
```

The cable selection also considers the calculated design current and available cable sizes.

## 8. Solar PV Calculations

The application estimates the PV system requirement using the project energy requirement and solar design assumptions included in the program.

The calculation workflow includes:

1. Energy requirement estimation.
2. Required PV capacity estimation.
3. Panel quantity calculation.
4. Installed PV capacity calculation.
5. Inverter requirement.
6. Electrical cable and protection design.
7. Generation estimation.

The number of panels is calculated from the required PV capacity and the selected panel rating.

## 9. Energy Analysis

The application provides:

- Monthly solar generation estimate.
- Annual generation estimate.
- Monthly energy analysis.
- 25-year generation analysis.
- Panel/system degradation over the project life.

The report includes graphical representation of the energy-generation data.

## 10. Economic Analysis

The application estimates the financial performance of the proposed solar PV system.

The economic section includes:

- Total project cost.
- Estimated annual savings/benefit.
- Payback period.
- Long-term project benefit.
- Profitability indicators.
- Fixed Deposit (FD) comparison.

These calculations are intended for project estimation and academic analysis.

Actual financial results can vary depending on electricity tariffs, solar irradiation, installation cost, maintenance, financing, and other real-world conditions.

## 11. Environmental Analysis

The application estimates environmental benefits from solar generation.

The environmental section includes:

- Estimated CO₂ emission reduction.
- Equivalent tree calculation.

These values are calculated using the environmental assumptions implemented in the program.

## 12. Dashboard

After entering the project information and running the calculation, the application provides an analysis dashboard.

The dashboard contains sections such as:

### Overview
- Project summary
- PV capacity
- Panel count
- Generation
- Cost
- Payback

### Single-Phase Design
- Inverter information
- Current
- Cable size
- Main MCB
- Voltage drop
- Electrical design information

### Energy
- Monthly generation
- Annual generation
- Long-term generation

### Economics
- Project cost
- Savings
- Payback
- Financial comparison

### Environment
- CO₂ reduction
- Equivalent trees

## 13. PDF Report

The application can generate a professional PDF report.

The report includes:

- Project title
- Project summary
- Key performance indicators
- Technical design
- Single-phase electrical parameters
- Energy analysis
- Economic analysis
- Environmental analysis
- Tables
- Monthly generation chart
- 25-year generation chart
- Economic comparison chart

The generated report is intended to be suitable for project presentation, documentation, and academic submission.

## 14. Application Workflow

```text
Start Application
       |
       v
Enter Project Inputs
       |
       v
Enter Solar Parameters
       |
       v
Enter Single-Phase Electrical Parameters
       |
       v
Run Calculation
       |
       v
Solar PV Size Estimation
       |
       v
Panel & Inverter Design
       |
       v
Single-Phase Cable & Protection Design
       |
       v
Voltage Drop Calculation
       |
       v
Energy Generation Analysis
       |
       v
Economic Analysis
       |
       v
Environmental Analysis
       |
       v
Dashboard Results
       |
       v
Generate PDF Report
```

## 15. Important Notes

- This version is specifically configured for **Single Phase** operation.
- Three-phase selection is not provided in the current user interface.
- Three-phase electrical design is not part of the active calculation workflow.
- Single-phase voltage, inverter rating, inverter current, inverter count, cable size, MCB rating, and cable length are user-entered parameters.
- The application is intended for estimation and academic/project purposes.
- Electrical installation should be verified by a qualified electrical engineer before practical implementation.
- Actual solar generation depends on location, irradiation, shading, orientation, tilt, temperature, system losses, and other site conditions.

## 16. Project File

Main application file:

```text
rtspv_estimator_single_phase.py
```

## 17. Future Improvements

Possible future improvements include:

- Location-based solar irradiation data.
- Automatic tariff selection.
- More detailed string and MPPT design.
- Detailed DC-side protection.
- Detailed earthing and lightning protection.
- Automatic component datasheet integration.
- More advanced financial analysis.
- Export to Excel.
- User login/project database.
- Company logo and customized report templates.
- Additional report customization options.

## 18. Author / Project Information

**Project:** RTSPV Solar Estimator  
**System Type:** Rooftop Solar PV  
**Electrical Configuration:** Single Phase  
**Application:** Solar PV Design, Estimation & Analysis  
**Platform:** Python Desktop Application

## 19. License

This project is intended for educational, academic, and project-development purposes.

Before using the calculated electrical design for an actual installation, all values and component selections should be reviewed and approved by a qualified professional.
