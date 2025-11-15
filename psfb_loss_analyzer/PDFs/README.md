# Reference PDF Library

This directory contains the reference materials used for developing and validating the PSFB Loss Analyzer.

## 📂 Expected Files

### Core Methodology
- `! MOSFET Power Losses Calculation Using the DataSheet Parameters 2006.pdf` - Infineon Application Note (PRIMARY REFERENCE)

### Power Electronics Textbooks
- `Fundamentals of Power Electronics 3ed 2020 - Part 1.pdf`
- `Fundamentals of Power Electronics 3ed 2020 - Part 2.pdf`
- `Fundamentals of Power Electronics 3ed 2020 - Magnetics Chapters.pdf`

### PSFB Topology References
- `! UCC28950, UCC28951 - Phase-Shifted Full-Bridge Controller.pdf` - Texas Instruments
- `Implementation of a PSFB DC-DC ZVS converter with Peak Current Mode Control - Assel Zhaksvlvk 2019.pdf`
- `Phase-Shifted Full-Bridge (PSFB) Quarter Brick DC-DC Converter Reference Design.pdf` - Microchip

### Magnetics Design
- `Transformer and Inductor Design Handbook 4ed 2011 - Colonel Wm. T. McLyman.pdf`
- `Large PQ series TDK PQ60x42 to PQ107x87x70.pdf`

### Component Datasheets
- `infineon-imza65r020m2h-datasheet-en.pdf` (650V, 20mΩ SiC MOSFET)
- `infineon-imza65r040m2h-datasheet-en.pdf` (650V, 40mΩ SiC MOSFET)

## 🚫 Git Ignore

PDF files are typically large and should not be committed to git repositories. This directory is included in `.gitignore`.

Users should obtain these reference materials from:
- Manufacturer websites (Infineon, TI, TDK, Microchip)
- Academic databases (for thesis)
- Publisher websites (for textbooks)

## 📖 Usage

See `../docs/REFERENCES.md` for detailed information on:
- How each reference is used in the tool
- Which sections/pages are relevant
- Parameter extraction procedures
- Implementation mapping to code modules

## ⚠️ Copyright Notice

All referenced materials are copyrighted by their respective authors and publishers. Users must obtain these materials through legitimate channels and comply with applicable copyright laws.
