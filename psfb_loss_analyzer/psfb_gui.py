#!/usr/bin/env python3
"""
PSFB Loss Analyzer - Graphical User Interface

A comprehensive GUI for Phase-Shifted Full-Bridge converter design and analysis,
including UCC28951 controller integration, loss analysis, and optimization.

Features:
- UCC28951 controller design tab
- Real-time component calculation
- Bode plot visualization
- BOM generation and export
- Configuration management

Author: PSFB Loss Analysis Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import csv
from typing import Dict, Optional

from ucc28951_controller import (
    UCC28951PowerStage,
    UCC28951Designer,
    ControlMode,
    format_component_value
)


class UCC28951Tab(ttk.Frame):
    """UCC28951 Controller Design Tab"""

    def __init__(self, parent):
        super().__init__(parent)
        self.designer: Optional[UCC28951Designer] = None
        self.create_widgets()

    def create_widgets(self):
        """Create all widgets for UCC28951 tab"""
        # Main container with scrollbar
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Input parameters
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))

        # Right panel: Results and plots
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === LEFT PANEL: INPUT PARAMETERS ===
        self.create_input_section(left_panel)

        # === RIGHT PANEL: RESULTS ===
        self.create_results_section(right_panel)

    def create_input_section(self, parent):
        """Create input parameter section"""
        # Title
        title = ttk.Label(parent, text="UCC28951 Controller Design",
                         font=('Arial', 12, 'bold'))
        title.pack(pady=(0, 10))

        # Input/Output Specifications
        io_frame = ttk.LabelFrame(parent, text="Power Stage Specifications", padding=10)
        io_frame.pack(fill=tk.X, pady=5)

        self.inputs = {}

        # Input voltage
        row = 0
        ttk.Label(io_frame, text="Input Voltage Min (V):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['v_in_min'] = ttk.Entry(io_frame, width=15)
        self.inputs['v_in_min'].insert(0, "360")
        self.inputs['v_in_min'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(io_frame, text="Input Voltage Nom (V):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['v_in_nom'] = ttk.Entry(io_frame, width=15)
        self.inputs['v_in_nom'].insert(0, "400")
        self.inputs['v_in_nom'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(io_frame, text="Input Voltage Max (V):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['v_in_max'] = ttk.Entry(io_frame, width=15)
        self.inputs['v_in_max'].insert(0, "440")
        self.inputs['v_in_max'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(io_frame, text="Output Voltage (V):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['v_out'] = ttk.Entry(io_frame, width=15)
        self.inputs['v_out'].insert(0, "250")
        self.inputs['v_out'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(io_frame, text="Output Power (W):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['p_out'] = ttk.Entry(io_frame, width=15)
        self.inputs['p_out'].insert(0, "2200")
        self.inputs['p_out'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(io_frame, text="Max Output Current (A):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['i_out_max'] = ttk.Entry(io_frame, width=15)
        self.inputs['i_out_max'].insert(0, "8.8")
        self.inputs['i_out_max'].grid(row=row, column=1, pady=2)

        # Switching Specifications
        sw_frame = ttk.LabelFrame(parent, text="Switching Parameters", padding=10)
        sw_frame.pack(fill=tk.X, pady=5)

        row = 0
        ttk.Label(sw_frame, text="Switching Freq (kHz):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['f_sw'] = ttk.Entry(sw_frame, width=15)
        self.inputs['f_sw'].insert(0, "100")
        self.inputs['f_sw'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(sw_frame, text="Dead Time (ns):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['dead_time'] = ttk.Entry(sw_frame, width=15)
        self.inputs['dead_time'].insert(0, "200")
        self.inputs['dead_time'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(sw_frame, text="Max Duty Cycle:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['max_duty'] = ttk.Entry(sw_frame, width=15)
        self.inputs['max_duty'].insert(0, "0.45")
        self.inputs['max_duty'].grid(row=row, column=1, pady=2)

        # Transformer Parameters
        xfmr_frame = ttk.LabelFrame(parent, text="Transformer Parameters", padding=10)
        xfmr_frame.pack(fill=tk.X, pady=5)

        row = 0
        ttk.Label(xfmr_frame, text="Primary Turns:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['n_primary'] = ttk.Entry(xfmr_frame, width=15)
        self.inputs['n_primary'].insert(0, "16")
        self.inputs['n_primary'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(xfmr_frame, text="Secondary Turns:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['n_secondary'] = ttk.Entry(xfmr_frame, width=15)
        self.inputs['n_secondary'].insert(0, "10")
        self.inputs['n_secondary'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(xfmr_frame, text="Leakage L (µH):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['l_leak'] = ttk.Entry(xfmr_frame, width=15)
        self.inputs['l_leak'].insert(0, "3.5")
        self.inputs['l_leak'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(xfmr_frame, text="Magnetizing L (µH):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['l_mag'] = ttk.Entry(xfmr_frame, width=15)
        self.inputs['l_mag'].insert(0, "350")
        self.inputs['l_mag'].grid(row=row, column=1, pady=2)

        # Control Mode
        ctrl_frame = ttk.LabelFrame(parent, text="Control Mode", padding=10)
        ctrl_frame.pack(fill=tk.X, pady=5)

        self.control_mode_var = tk.StringVar(value="voltage_mode")
        ttk.Radiobutton(ctrl_frame, text="Voltage Mode",
                       variable=self.control_mode_var,
                       value="voltage_mode").pack(anchor=tk.W)
        ttk.Radiobutton(ctrl_frame, text="Peak Current Mode",
                       variable=self.control_mode_var,
                       value="peak_current_mode").pack(anchor=tk.W)

        # Design Parameters
        design_frame = ttk.LabelFrame(parent, text="Design Parameters", padding=10)
        design_frame.pack(fill=tk.X, pady=5)

        row = 0
        ttk.Label(design_frame, text="Soft-Start Time (ms):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['t_ss'] = ttk.Entry(design_frame, width=15)
        self.inputs['t_ss'].insert(0, "10")
        self.inputs['t_ss'].grid(row=row, column=1, pady=2)

        row += 1
        ttk.Label(design_frame, text="Crossover Freq (kHz):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.inputs['f_cross'] = ttk.Entry(design_frame, width=15)
        self.inputs['f_cross'].insert(0, "10")
        self.inputs['f_cross'].grid(row=row, column=1, pady=2)

        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Calculate Components",
                  command=self.calculate_components).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Generate Bode Plot",
                  command=self.generate_bode_plot).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Export BOM",
                  command=self.export_bom).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Clear All",
                  command=self.clear_all).pack(fill=tk.X, pady=2)

    def create_results_section(self, parent):
        """Create results display section"""
        # Notebook for results tabs
        results_notebook = ttk.Notebook(parent)
        results_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Component Values
        components_tab = ttk.Frame(results_notebook)
        results_notebook.add(components_tab, text="Component Values")

        # Component results text area
        self.components_text = scrolledtext.ScrolledText(components_tab,
                                                         height=20,
                                                         font=('Courier', 10))
        self.components_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 2: Bode Plot
        bode_tab = ttk.Frame(results_notebook)
        results_notebook.add(bode_tab, text="Bode Plot")

        # Create matplotlib figure for Bode plot
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax_gain = self.fig.add_subplot(211)
        self.ax_phase = self.fig.add_subplot(212)

        self.canvas = FigureCanvasTkAgg(self.fig, master=bode_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Navigation toolbar
        toolbar_frame = ttk.Frame(bode_tab)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # Tab 3: BOM
        bom_tab = ttk.Frame(results_notebook)
        results_notebook.add(bom_tab, text="Bill of Materials")

        # BOM treeview
        self.bom_tree = ttk.Treeview(bom_tab,
                                     columns=('designator', 'value', 'description', 'package'),
                                     show='headings',
                                     height=15)
        self.bom_tree.heading('designator', text='Designator')
        self.bom_tree.heading('value', text='Value')
        self.bom_tree.heading('description', text='Description')
        self.bom_tree.heading('package', text='Package')

        self.bom_tree.column('designator', width=100)
        self.bom_tree.column('value', width=100)
        self.bom_tree.column('description', width=250)
        self.bom_tree.column('package', width=80)

        scrollbar = ttk.Scrollbar(bom_tab, orient=tk.VERTICAL, command=self.bom_tree.yview)
        self.bom_tree.configure(yscrollcommand=scrollbar.set)

        self.bom_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(0, 5))

    def get_power_stage_params(self) -> UCC28951PowerStage:
        """Extract power stage parameters from input fields"""
        try:
            control_mode = ControlMode.VOLTAGE_MODE if self.control_mode_var.get() == "voltage_mode" else ControlMode.PEAK_CURRENT_MODE

            params = UCC28951PowerStage(
                v_in_min=float(self.inputs['v_in_min'].get()),
                v_in_nom=float(self.inputs['v_in_nom'].get()),
                v_in_max=float(self.inputs['v_in_max'].get()),
                v_out=float(self.inputs['v_out'].get()),
                i_out_max=float(self.inputs['i_out_max'].get()),
                p_out=float(self.inputs['p_out'].get()),
                f_sw=float(self.inputs['f_sw'].get()) * 1e3,  # Convert kHz to Hz
                dead_time=float(self.inputs['dead_time'].get()) * 1e-9,  # Convert ns to s
                max_duty_cycle=float(self.inputs['max_duty'].get()),
                n_primary=int(self.inputs['n_primary'].get()),
                n_secondary=int(self.inputs['n_secondary'].get()),
                leakage_inductance=float(self.inputs['l_leak'].get()) * 1e-6,  # Convert µH to H
                magnetizing_inductance=float(self.inputs['l_mag'].get()) * 1e-6,  # Convert µH to H
                control_mode=control_mode
            )
            return params
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return None

    def calculate_components(self):
        """Calculate all component values"""
        params = self.get_power_stage_params()
        if params is None:
            return

        # Create designer
        self.designer = UCC28951Designer(params)

        # Calculate all components
        try:
            t_ss = float(self.inputs['t_ss'].get()) * 1e-3  # Convert ms to s
            f_cross = float(self.inputs['f_cross'].get()) * 1e3  # Convert kHz to Hz
            components = self.designer.calculate_all_components(t_ss, f_cross)

            # Display results
            self.display_component_results(params, components)

            # Update BOM
            self.update_bom()

            messagebox.showinfo("Success", "Component values calculated successfully!")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {e}")

    def display_component_results(self, params: UCC28951PowerStage, components):
        """Display calculated component values"""
        self.components_text.delete('1.0', tk.END)

        output = []
        output.append("="*70)
        output.append("UCC28951 CONTROLLER DESIGN RESULTS")
        output.append("="*70)
        output.append("")

        # Power stage summary
        output.append("POWER STAGE SPECIFICATIONS")
        output.append("-"*70)
        output.append(f"Input Voltage:        {params.v_in_min}V - {params.v_in_max}V (nom: {params.v_in_nom}V)")
        output.append(f"Output Voltage:       {params.v_out}V")
        output.append(f"Output Power:         {params.p_out}W")
        output.append(f"Output Current:       {params.i_out_max}A")
        output.append(f"Switching Frequency:  {params.f_sw/1e3:.1f}kHz")
        output.append(f"Transformer Ratio:    {params.n_primary}:{params.n_secondary} (n = {params.n_ratio:.2f})")
        output.append(f"Control Mode:         {params.control_mode.value.replace('_', ' ').title()}")
        output.append("")

        # Timing components
        output.append("TIMING COMPONENTS")
        output.append("-"*70)
        output.append(f"RT (Oscillator):      {format_component_value(components.r_t, 'Ω')}")
        output.append(f"CT (Oscillator):      {format_component_value(components.c_t, 'F')}")
        output.append(f"Actual Frequency:     {1/(1.4*components.r_t*components.c_t)/1e3:.2f}kHz")
        output.append("")

        # Soft-start
        output.append("SOFT-START")
        output.append("-"*70)
        output.append(f"CSS:                  {format_component_value(components.c_ss, 'F')}")
        output.append(f"Soft-Start Time:      {components.t_ss*1e3:.1f}ms")
        output.append("")

        # Adaptive delay
        output.append("ADAPTIVE DELAY")
        output.append("-"*70)
        output.append(f"RADS:                 {format_component_value(components.r_ads, 'Ω')}")
        output.append(f"Delay Time:           {components.t_delay*1e9:.1f}ns")
        output.append("")

        # Output voltage feedback
        output.append("OUTPUT VOLTAGE FEEDBACK")
        output.append("-"*70)
        output.append(f"R_FB_UPPER:           {format_component_value(components.r_upper, 'Ω')}")
        output.append(f"R_FB_LOWER:           {format_component_value(components.r_lower, 'Ω')}")
        output.append(f"Feedback Voltage:     {2.5}V @ {params.v_out}V output")
        output.append("")

        # Compensation
        output.append("LOOP COMPENSATION (Type II)")
        output.append("-"*70)
        output.append(f"RCOMP:                {format_component_value(components.r_comp, 'Ω')}")
        output.append(f"CCOMP1:               {format_component_value(components.c_comp1, 'F')}")
        output.append(f"CCOMP2:               {format_component_value(components.c_comp2, 'F')}")
        output.append("")

        # UVLO
        output.append("INPUT UVLO")
        output.append("-"*70)
        output.append(f"R_UVLO_UPPER:         {format_component_value(components.r_uvlo_upper, 'Ω')}")
        output.append(f"R_UVLO_LOWER:         {format_component_value(components.r_uvlo_lower, 'Ω')}")
        output.append("")

        # Current sense (if applicable)
        if params.control_mode == ControlMode.PEAK_CURRENT_MODE:
            output.append("CURRENT SENSE")
            output.append("-"*70)
            output.append(f"RCS:                  {format_component_value(components.r_cs, 'Ω')}")
            output.append(f"Max CS Voltage:       {components.v_cs_max}V")
            output.append("")

        output.append("="*70)
        output.append("Design complete! See BOM tab for component list.")
        output.append("="*70)

        self.components_text.insert('1.0', '\n'.join(output))

    def generate_bode_plot(self):
        """Generate and display Bode plot"""
        if self.designer is None:
            messagebox.showwarning("Warning", "Please calculate components first!")
            return

        try:
            # Generate frequency response
            response = self.designer.generate_bode_plot()

            # Clear previous plots
            self.ax_gain.clear()
            self.ax_phase.clear()

            # Plot gain
            self.ax_gain.semilogx(response.frequencies, response.gain_db, 'b-', linewidth=2)
            self.ax_gain.axhline(0, color='r', linestyle='--', linewidth=1)
            self.ax_gain.axvline(response.f_crossover, color='g', linestyle='--', linewidth=1, label=f'fc = {response.f_crossover:.1f}Hz')
            self.ax_gain.grid(True, which='both', alpha=0.3)
            self.ax_gain.set_ylabel('Gain (dB)', fontsize=10)
            self.ax_gain.set_title('Loop Gain Bode Plot', fontsize=11, fontweight='bold')
            self.ax_gain.legend(loc='upper right')

            # Plot phase
            self.ax_phase.semilogx(response.frequencies, response.phase_deg, 'b-', linewidth=2)
            self.ax_phase.axhline(-180, color='r', linestyle='--', linewidth=1)
            self.ax_phase.axvline(response.f_crossover, color='g', linestyle='--', linewidth=1)
            self.ax_phase.grid(True, which='both', alpha=0.3)
            self.ax_phase.set_xlabel('Frequency (Hz)', fontsize=10)
            self.ax_phase.set_ylabel('Phase (degrees)', fontsize=10)

            # Add margins text
            margin_text = f'Phase Margin: {response.phase_margin:.1f}°\nGain Margin: {response.gain_margin:.1f}dB'
            self.ax_phase.text(0.02, 0.98, margin_text,
                              transform=self.ax_phase.transAxes,
                              verticalalignment='top',
                              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                              fontsize=9)

            self.fig.tight_layout()
            self.canvas.draw()

            messagebox.showinfo("Success", f"Bode plot generated!\n\nPhase Margin: {response.phase_margin:.1f}°\nGain Margin: {response.gain_margin:.1f}dB")

        except Exception as e:
            messagebox.showerror("Plot Error", f"Error generating Bode plot: {e}")

    def update_bom(self):
        """Update BOM treeview"""
        # Clear existing items
        for item in self.bom_tree.get_children():
            self.bom_tree.delete(item)

        if self.designer is None:
            return

        # Get BOM
        bom = self.designer.generate_bom()

        # Populate treeview
        for item in bom:
            self.bom_tree.insert('', tk.END,
                                values=(item['Designator'],
                                       item['Value'],
                                       item['Description'],
                                       item['Package']))

    def export_bom(self):
        """Export BOM to CSV file"""
        if self.designer is None:
            messagebox.showwarning("Warning", "Please calculate components first!")
            return

        try:
            # Ask for file location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export BOM"
            )

            if not filename:
                return

            # Get BOM
            bom = self.designer.generate_bom()

            # Write to CSV
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['Designator', 'Part Number', 'Description', 'Manufacturer', 'Value', 'Package', 'Quantity']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for item in bom:
                    writer.writerow(item)

            messagebox.showinfo("Success", f"BOM exported to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting BOM: {e}")

    def clear_all(self):
        """Clear all results"""
        self.components_text.delete('1.0', tk.END)
        self.ax_gain.clear()
        self.ax_phase.clear()
        self.canvas.draw()
        for item in self.bom_tree.get_children():
            self.bom_tree.delete(item)
        self.designer = None


class PSFBLossAnalyzerGUI:
    """Main application window"""

    def __init__(self, root):
        self.root = root
        self.root.title("PSFB Loss Analyzer & Design Suite")
        self.root.geometry("1200x800")

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Create main menu
        self.create_menu()

        # Create main notebook with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add tabs
        self.add_tabs()

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Configuration...", command=self.open_config)
        file_menu.add_command(label="Save Configuration...", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Report...", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Component Database...", command=self.open_component_db)
        tools_menu.add_command(label="Preferences...", command=self.open_preferences)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)

    def add_tabs(self):
        """Add all application tabs"""
        # Tab 1: UCC28951 Controller Design
        self.ucc28951_tab = UCC28951Tab(self.notebook)
        self.notebook.add(self.ucc28951_tab, text="UCC28951 Controller")

        # Tab 2: Loss Analysis (placeholder)
        loss_tab = ttk.Frame(self.notebook)
        self.notebook.add(loss_tab, text="Loss Analysis")
        ttk.Label(loss_tab, text="Loss Analysis Module\n(Coming Soon)",
                 font=('Arial', 14)).pack(expand=True)

        # Tab 3: Thermal Analysis (placeholder)
        thermal_tab = ttk.Frame(self.notebook)
        self.notebook.add(thermal_tab, text="Thermal Analysis")
        ttk.Label(thermal_tab, text="Thermal Analysis Module\n(Coming Soon)",
                 font=('Arial', 14)).pack(expand=True)

        # Tab 4: Optimization (placeholder)
        opt_tab = ttk.Frame(self.notebook)
        self.notebook.add(opt_tab, text="Optimization")
        ttk.Label(opt_tab, text="Optimization Module\n(Coming Soon)",
                 font=('Arial', 14)).pack(expand=True)

    # Menu callbacks (placeholders)
    def open_config(self):
        messagebox.showinfo("Info", "Open configuration - Coming soon!")

    def save_config(self):
        messagebox.showinfo("Info", "Save configuration - Coming soon!")

    def export_report(self):
        messagebox.showinfo("Info", "Export report - Coming soon!")

    def open_component_db(self):
        messagebox.showinfo("Info", "Component database - Coming soon!")

    def open_preferences(self):
        messagebox.showinfo("Info", "Preferences - Coming soon!")

    def show_help(self):
        help_text = """
PSFB Loss Analyzer & Design Suite

UCC28951 Controller Tab:
1. Enter power stage specifications
2. Click 'Calculate Components' to design controller
3. View component values in 'Component Values' tab
4. Generate Bode plot to analyze loop stability
5. Export BOM to CSV file

For more information, see the project README.md
"""
        messagebox.showinfo("Help", help_text)

    def show_about(self):
        about_text = """
PSFB Loss Analyzer & Design Suite
Version 1.0

A comprehensive tool for Phase-Shifted
Full-Bridge converter design and analysis.

Features:
• UCC28951 controller design
• Loss analysis and optimization
• Thermal modeling
• Component selection

Author: PSFB Loss Analysis Tool
"""
        messagebox.showinfo("About", about_text)


def main():
    """Main entry point for GUI application"""
    root = tk.Tk()
    app = PSFBLossAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
