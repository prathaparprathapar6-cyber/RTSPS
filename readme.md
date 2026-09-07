# Single-Phase Electrical Parameter Calculator

## 📌 Project Overview

The **Single-Phase Electrical Parameter Calculator** is a Python-based application designed to calculate important electrical parameters for a **single-phase AC electrical system**.

This project was originally designed with three-phase electrical parameters. It has now been modified to work with **single-phase parameters only**.

All three-phase-specific parameters, formulas, and inputs have been removed.

The application allows the user to enter single-phase electrical parameters and obtain the corresponding electrical calculations.

---

## 🎯 Project Objective

The main objective of this project is to develop a simple, accurate, and user-friendly application for calculating electrical parameters in a **single-phase AC circuit**.

The system focuses only on:

* Single-phase voltage
* Single-phase current
* Power factor
* Frequency
* Active power
* Apparent power
* Reactive power

---

## ⚡ Electrical System

The application is designed for a **single-phase AC supply**.

### Single-Phase System

```text
             AC SUPPLY
                │
                ▼
        ┌─────────────────┐
        │ Single-Phase    │
        │ Electrical Load │
        └─────────────────┘
                │
                ▼
          Electrical
          Parameters
```

---

# 🔌 Input Parameters

The user enters the following single-phase parameters.

| Parameter    | Symbol | Unit       | Description                             |
| ------------ | ------ | ---------- | --------------------------------------- |
| Voltage      | V      | Volt (V)   | Single-phase RMS voltage                |
| Current      | I      | Ampere (A) | Single-phase RMS current                |
| Power Factor | PF     | —          | Ratio between active and apparent power |
| Frequency    | f      | Hertz (Hz) | AC supply frequency                     |

### Example Input

```text
Voltage       = 230 V
Current       = 10 A
Power Factor  = 0.8
Frequency     = 50 Hz
```

---

# 🧮 Electrical Calculations

## 1. Active Power

Active power is the actual electrical power consumed by the load.

### Formula

```text
P = V × I × PF
```

Where:

```text
P  = Active Power in Watts (W)
V  = Voltage in Volts (V)
I  = Current in Amperes (A)
PF = Power Factor
```

### Example

```text
V  = 230 V
I  = 10 A
PF = 0.8

P = 230 × 10 × 0.8

P = 1840 W
```

Therefore:

```text
Active Power = 1840 W
```

---

# 2. Apparent Power

Apparent power is the product of RMS voltage and RMS current.

### Formula

```text
S = V × I
```

Where:

```text
S = Apparent Power in Volt-Amperes (VA)
V = Voltage in Volts (V)
I = Current in Amperes (A)
```

### Example

```text
V = 230 V
I = 10 A

S = 230 × 10

S = 2300 VA
```

Therefore:

```text
Apparent Power = 2300 VA
```

---

# 3. Reactive Power

Reactive power is the power associated with the reactive component of an AC load.

It can be calculated using:

### Formula

```text
Q = √(S² - P²)
```

Where:

```text
Q = Reactive Power in Volt-Amperes Reactive (VAR)
S = Apparent Power in VA
P = Active Power in W
```

### Example

```text
S = 2300 VA
P = 1840 W

Q = √(2300² - 1840²)

Q = √(5290000 - 3385600)

Q = √1904400

Q ≈ 1380 VAR
```

Therefore:

```text
Reactive Power ≈ 1380 VAR
```

---

# 4. Power Factor

Power factor represents the relationship between active power and apparent power.

### Formula

```text
PF = P / S
```

Where:

```text
PF = Power Factor
P  = Active Power in W
S  = Apparent Power in VA
```

### Example

```text
P = 1840 W
S = 2300 VA

PF = 1840 / 2300

PF = 0.8
```

Therefore:

```text
Power Factor = 0.8
```

---

# 📊 Output Parameters

After entering the required values, the application calculates and displays:

| Output         | Symbol | Unit |
| -------------- | ------ | ---- |
| Active Power   | P      | W    |
| Apparent Power | S      | VA   |
| Reactive Power | Q      | VAR  |
| Power Factor   | PF     | —    |

### Example Output

```text
========================================
       SINGLE-PHASE CALCULATION
========================================

Voltage        : 230 V
Current        : 10 A
Power Factor   : 0.8
Frequency      : 50 Hz

----------------------------------------

Active Power   : 1840 W
Apparent Power : 2300 VA
Reactive Power : 1380 VAR
Power Factor   : 0.8

========================================
```

---

# 🚫 Three-Phase Parameters Removed

This project is **not a three-phase calculator**.

All three-phase-specific parameters and calculations have been removed.

The following parameters are not used:

* Three-phase voltage
* Three-phase current
* Line voltage
* Phase voltage
* Line current
* Three-phase active power
* Three-phase apparent power
* Three-phase reactive power
* Three-phase power factor
* Three-phase energy calculations
* √3 multiplication factor
* Three-phase parameter input fields
* Three-phase calculation logic

The project now uses **single-phase parameters only**.

---

# 🔄 Calculation Flow

The calculation process follows this sequence:

```text
┌──────────────────────┐
│      User Input      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Single-Phase Voltage │
│ Single-Phase Current │
│ Power Factor         │
│ Frequency            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Electrical           │
│ Calculations         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Active Power         │
│ Apparent Power       │
│ Reactive Power       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Display Results      │
└──────────────────────┘
```

---

# 🛡️ Input Validation

The application should validate all user inputs before performing calculations.

## Voltage

Voltage must be greater than zero.

```text
V > 0
```

## Current

Current must be greater than or equal to zero.

```text
I >= 0
```

## Power Factor

Power factor must be within the valid range.

```text
0 <= PF <= 1
```

## Frequency

Frequency must be greater than zero.

```text
f > 0
```

## Empty Input

The application should not accept empty input fields.

If an input is missing or invalid, an appropriate error message should be displayed.

Example:

```text
Please enter a valid voltage.
```

---

# 🖥️ User Interface

The user interface should contain only the required single-phase parameters.

### Input Section

```text
----------------------------------------
        SINGLE-PHASE INPUT
----------------------------------------

Voltage (V)       : [             ]

Current (A)       : [             ]

Power Factor      : [             ]

Frequency (Hz)    : [             ]

              [ CALCULATE ]

----------------------------------------
```

### Result Section

```text
----------------------------------------
          CALCULATION RESULTS
----------------------------------------

Active Power      : 1840 W
Apparent Power    : 2300 VA
Reactive Power    : 1380 VAR
Power Factor      : 0.8

----------------------------------------
```

---

# 📁 Project Structure

The recommended project structure is:

```text
Single-Phase-Project/
│
├── main.py
│
├── README.md
│
├── requirements.txt
│
├── src/
│   │
│   ├── calculator.py
│   │
│   └── ui.py
│
└── assets/
    │
    └── images/
```

---

# 📄 File Description

## `main.py`

The main entry point of the application.

It starts the program and connects the user interface with the calculation module.

---

## `calculator.py`

Contains the electrical calculation logic.

It can contain functions such as:

```text
calculate_active_power()
calculate_apparent_power()
calculate_reactive_power()
calculate_power_factor()
```

---

## `ui.py`

Contains the user interface and input/output handling.

It manages:

* Input fields
* Buttons
* Validation messages
* Calculation results
* User interaction

---

## `requirements.txt`

Contains the Python packages required to run the application.

Example:

```text
# Add required Python packages here
```

---

# 💻 Technologies Used

The project can be developed using:

* **Python 3**
* **Visual Studio Code**
* **Git**
* **GitHub**

---

# ▶️ Installation

## Step 1: Install Python

Install Python 3.x on your computer.

Check the Python installation:

```bash
python --version
```

Example:

```text
Python 3.12.x
```

---

## Step 2: Open the Project

Open the project folder using Visual Studio Code.

```text
Single-Phase-Project
```

---

## Step 3: Create a Virtual Environment

It is recommended to create a Python virtual environment.

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## Step 4: Install Requirements

Run:

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Application

Run the following command:

```bash
python main.py
```

The application should start and display the single-phase calculation interface.

---

# 🧪 Test Example

Use the following values to test the application:

```text
Voltage       = 230 V
Current       = 10 A
Power Factor  = 0.8
Frequency     = 50 Hz
```

Expected results:

```text
Active Power   = 1840 W
Apparent Power = 2300 VA
Reactive Power ≈ 1380 VAR
```

---

# 📐 Mathematical Relationship

For a single-phase AC circuit:

```text
S² = P² + Q²
```

Therefore:

```text
Q = √(S² - P²)
```

And:

```text
P = S × PF
```

Since:

```text
S = V × I
```

The active power becomes:

```text
P = V × I × PF
```

---

# 🔧 Future Improvements

The project can be expanded in the future with:

* Electrical energy calculation
* Energy consumption in kWh
* Cost calculation
* Load analysis
* Power factor correction
* Capacitor calculation
* Graphical power analysis
* Data export
* Report generation
* Calculation history
* Dark mode
* Improved user interface

---

# ⚠️ Important Note

This calculator is intended for **educational, development, and estimation purposes**.

For actual electrical installation, equipment selection, protection design, or safety-critical applications, calculations should be verified by a qualified electrical professional and applicable electrical standards.

---

# 📌 Summary

The project has been converted from a three-phase electrical calculator to a **single-phase electrical parameter calculator**.

### The final project uses:

```text
Voltage
Current
Power Factor
Frequency
```

### And calculates:

```text
Active Power
Apparent Power
Reactive Power
Power Factor
```

### Single-Phase Formulas

```text
P = V × I × PF

S = V × I

Q = √(S² - P²)

PF = P / S
```

---

# 👨‍💻 Development

This project can be modified and maintained using Visual Studio Code.

Recommended workflow:

```text
Write Code
    ↓
Run Application
    ↓
Test Calculations
    ↓
Fix Errors
    ↓
Update README
    ↓
Commit Changes
    ↓
Push to GitHub
```

---

# 📜 License

This project is intended for educational and project-development purposes.

You may modify the source code according to your project requirements.

---

# ✅ Final Project Status

```text
╔══════════════════════════════════════╗
║       SINGLE-PHASE PROJECT           ║
╠══════════════════════════════════════╣
║                                      ║
║  ✓ Single-Phase Voltage              ║
║  ✓ Single-Phase Current              ║
║  ✓ Power Factor                      ║
║  ✓ Frequency                         ║
║  ✓ Active Power                      ║
║  ✓ Apparent Power                    ║
║  ✓ Reactive Power                    ║
║                                      ║
║  ✗ Three-Phase Parameters             ║
║  ✗ Line Voltage                      ║
║  ✗ Three-Phase Current               ║
║  ✗ √3 Three-Phase Formula            ║
║                                      ║
╚══════════════════════════════════════╝
```

## End of README
