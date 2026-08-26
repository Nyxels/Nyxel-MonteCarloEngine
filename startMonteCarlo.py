## NyxQuant Monte Carlo Engine GUI
## Auther: Marcel Rohr
## License: MIT

from sys import path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use("TkAgg")  # Wichtig: Backend BEVOR pyplot importiert wird
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import csv
import random


#Theme-Farben

COLORS = {
    "bg": "#1e1e2e",           # Haupt-Hintergrund (dunkel)
    "bg_secondary": "#252537",  # Panel-Hintergrund
    "bg_tertiary": "#2d2d44",  # Eingabefelder, Hover
    "accent": "#7aa2f7",       # Primär-Akzent (Blau)
    "accent_secondary": "#bb9af7",  # Sekundär (Lila)
    "text": "#c0caf5",         # Haupt-Text
    "text_muted": "#565f89",   # Sekundärer Text
    "success": "#9ece6a",      # Grün für Gewinne/OK
    "danger": "#f7768e",       # Rot für Verluste/Fehler
    "warning": "#e0af68",      # Orange für Warnungen
}


class StyledFrame(tk.Frame):
    #Rahmen mit Theme-Hintergrundfarbe
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_secondary"], **kwargs)


class StyledLabel(tk.Label):
    #Label mit Theme-Farben.
    def __init__(self, parent, text="", muted=False, bold=False, **kwargs):
        fg = COLORS["text_muted"] if muted else COLORS["text"]
        font = ("Segoe UI", 10, "bold" if bold else "normal")
        super().__init__(
            parent, text=text, bg=parent["bg"], fg=fg, font=font, **kwargs
        )


class StyledButton(tk.Button):
    #Moderner Button mit Hover-Effekt.
    def __init__(self, parent, text, command=None, accent=False, **kwargs):
        self.bg_color = COLORS["accent"] if accent else COLORS["bg_tertiary"]
        self.fg_color = "#1e1e2e" if accent else COLORS["text"]
        self.hover_bg = "#89b4fa" if accent else "#3d3d5c"
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self.bg_color,
            fg=self.fg_color,
            activebackground=self.hover_bg,
            activeforeground=self.fg_color,
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            font=("Segoe UI", 9, "bold" if accent else "normal"),
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))


class StyledEntry(tk.Entry):
    #Eingabefeld im Dark Mode.
    def __init__(self, parent, default="", width=12, **kwargs):
        super().__init__(
            parent,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            bd=0,
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            highlightbackground=COLORS["bg"],
            width=width,
            font=("Consolas", 10),
            **kwargs
        )
        self.insert(0, default)



# MAIN APPLICATION


class MonteCarloApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NyxQuant :: Monte Carlo Engine")
        self.root.geometry("1400x850")
        self.root.minsize(1000, 600)
        self.root.configure(bg=COLORS["bg"])
        
        # Daten-Storage (wird von Engine befüllt)
        self.trades = []           # Roh-Trade-Daten
        self.simulations = []      # Ergebnisse der MC-Runs
        self.current_file = None   # Pfad zur geladenen CSV
        
        self._setup_styles()
        self._build_ui()
        self._init_charts()
        
    def _setup_styles(self):
        """ttk Styles überschreiben für Dark Mode."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Notebook (Tabs)
        style.configure(
            "CustomNotebook.TNotebook",
            background=COLORS["bg"],
            tabmargins=[0, 0, 0, 0],
        )
        style.configure(
            "CustomNotebook.TNotebook.Tab",
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_muted"],
            padding=[12, 4],
            font=("Segoe UI", 9),
        )
        style.map(
            "CustomNotebook.TNotebook.Tab",
            background=[("selected", COLORS["bg"]), ("active", COLORS["bg_tertiary"])],
            foreground=[("selected", COLORS["accent"]), ("active", COLORS["text"])],
            expand=[("selected", [2, 2, 2, 0])],
        )
        
        # Scrollbar
        style.configure(
            "Vertical.TScrollbar",
            background=COLORS["bg_tertiary"],
            troughcolor=COLORS["bg"],
            bordercolor=COLORS["bg"],
            arrowcolor=COLORS["text_muted"],
        )
        
    def _build_ui(self):
        """Haupt-Layout: Sidebar | Center | RightPanel."""
        
        # ═══ TOP MENU BAR ═══
        menubar = tk.Menu(self.root, bg=COLORS["bg"], fg=COLORS["text"], bd=0)
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"], 
                           fg=COLORS["text"], activebackground=COLORS["bg_tertiary"])
        file_menu.add_command(label="Load Trade Data (CSV)", command=self._load_data)
        file_menu.add_command(label="Export Results", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"],
                           fg=COLORS["text"], activebackground=COLORS["bg_tertiary"])
        view_menu.add_command(label="Reset Layout", command=self._reset_layout)
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menubar)
        
        # ═══ MAIN CONTAINER ═══
        main_container = StyledFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=8, pady=8)
        main_container.grid_columnconfigure(1, weight=1)  # Center expandiert
        main_container.grid_rowconfigure(0, weight=1)
        
        # ═══ LEFT SIDEBAR (Control Panel) ═══
        self.sidebar = self._build_sidebar(main_container)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # ═══ CENTER (Chart Area) ═══
        self.center_frame = self._build_center(main_container)
        self.center_frame.grid(row=0, column=1, sticky="nsew")
        
        # ═══ RIGHT PANEL (Metrics) ═══
        self.right_panel = self._build_right_panel(main_container)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        
        # ═══ BOTTOM STATUS BAR ═══
        self.status_bar = tk.Label(
            self.root,
            text="Ready  |  No data loaded",
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_muted"],
            font=("Consolas", 9),
            anchor="w",
            padx=10,
            pady=4,
        )
        self.status_bar.pack(fill="x", side="bottom")
        
    def _build_sidebar(self, parent):
        #Linker Bereich: Parameter & Kontrollen.
        frame = StyledFrame(parent, width=260)
        frame.pack_propagate(False)
        frame.grid_propagate(False)
        
        # Header
        StyledLabel(frame, text="SIMULATION CONTROL", bold=True, muted=True).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        tk.Frame(frame, bg=COLORS["accent"], height=2).pack(fill="x", padx=12)
        
        #  Data Section
        StyledLabel(frame, text="Data Source", bold=True).pack(anchor="w", padx=12, pady=(16, 6))
        
        self.lbl_file = StyledLabel(frame, text="No file loaded", muted=True)
        self.lbl_file.pack(anchor="w", padx=12, pady=(0, 8))
        
        StyledButton(frame, text="Load CSV", command=self._load_data).pack(
            fill="x", padx=12, pady=2
        )
        
        # Parameters Section 
        StyledLabel(frame, text="Parameters", bold=True).pack(
            anchor="w", padx=12, pady=(20, 6)
        )
        
        params = StyledFrame(frame)
        params.pack(fill="x", padx=12, pady=4)
        
        # Grid für Parameter
        param_defs = [
            ("Start Capital ($):", "100000"),
            ("# Simulations:", "1000"),
            ("Bootstrap Type:", "i.i.d."),  # später: Block-Bootstrap
            ("Position Size (%):", "1.0"),
        ]
        self.param_entries = {}
        
        for i, (label, default) in enumerate(param_defs):
            StyledLabel(params, text=label, muted=True).grid(
                row=i, column=0, sticky="w", pady=4
            )
            entry = StyledEntry(params, default=default, width=14)
            entry.grid(row=i, column=1, sticky="e", pady=4, padx=(8, 0))
            self.param_entries[label] = entry
        
        #  Action Buttons 
        StyledLabel(frame, text="Actions", bold=True).pack(
            anchor="w", padx=12, pady=(24, 6)
        )
        
        StyledButton(
            frame, text="▶  RUN SIMULATION", command=self._run_simulation, accent=True
        ).pack(fill="x", padx=12, pady=6)
        
        StyledButton(
            frame, text="↻  Reset", command=self._reset
        ).pack(fill="x", padx=12, pady=2)
        
        # footer Info 
        tk.Frame(frame, bg=COLORS["bg_secondary"]).pack(expand=True, fill="both")
        StyledLabel(
            frame, 
            text="NyxQuant Engine v0.1\nBuilt for Swiss Quant Interviews",
            muted=True
        ).pack(anchor="center", pady=12)
        
        return frame
        
    def _build_center(self, parent):
        """Mittlerer Bereich: Tabs mit Matplotlib-Charts."""
        frame = StyledFrame(parent)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(frame, style="CustomNotebook.TNotebook")
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Equity Curves
        self.tab_equity = StyledFrame(self.notebook)
        self.notebook.add(self.tab_equity, text=" Equity Curves ")
        
        # Tab 2: Distribution
        self.tab_dist = StyledFrame(self.notebook)
        self.notebook.add(self.tab_dist, text=" Distribution ")
        
        # Tab 3: Drawdown Analysis
        self.tab_dd = StyledFrame(self.notebook)
        self.notebook.add(self.tab_dd, text=" Drawdown ")
        
        # Tab 4: Raw Data
        self.tab_raw = StyledFrame(self.notebook)
        self.notebook.add(self.tab_raw, text=" Trade Log ")
        
        return frame
        
    def _build_right_panel(self, parent):
        # Rechter Bereich: Metriken & Logs.
        frame = StyledFrame(parent, width=240)
        frame.pack_propagate(False)
        frame.grid_propagate(False)
        
        # Header
        StyledLabel(frame, text="METRICS", bold=True, muted=True).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        tk.Frame(frame, bg=COLORS["accent_secondary"], height=2).pack(fill="x", padx=12)
        
        # Key Metrics 
        self.metrics_frame = StyledFrame(frame)
        self.metrics_frame.pack(fill="x", padx=12, pady=(12, 0))
        
        self.metric_labels = {}
        metrics = [
            ("Total Return", "0.00%", COLORS["text"]),
            ("CAGR", "0.00%", COLORS["text"]),
            ("Sharpe Ratio", "0.00", COLORS["text"]),
            ("Max Drawdown", "0.00%", COLORS["danger"]),
            ("Profit Factor", "0.00", COLORS["text"]),
            ("Win Rate", "0.00%", COLORS["success"]),
            ("Probability of Ruin", "0.00%", COLORS["warning"]),
            ("VaR (95%)", "0.00 €", COLORS["danger"]),
            ("CVaR (95%)", "0.00 €", COLORS["danger"]),
        ]
        
        for name, default, color in metrics:
            row = StyledFrame(self.metrics_frame)
            row.pack(fill="x", pady=3)
            
            StyledLabel(row, text=name, muted=True).pack(side="left")
            lbl = StyledLabel(row, text=default, bold=True)
            lbl.configure(fg=color)
            lbl.pack(side="right")
            self.metric_labels[name] = lbl
        
        # Simulation Stats 
        StyledLabel(frame, text="Simulation Stats", bold=True).pack(
            anchor="w", padx=12, pady=(20, 6)
        )
        
        self.sim_stats = StyledLabel(frame, text="Runs: 0\nTrades: 0\nTime: 0ms", muted=True)
        self.sim_stats.pack(anchor="w", padx=12)
        
        # Log Console
        StyledLabel(frame, text="Event Log", bold=True).pack(
            anchor="w", padx=12, pady=(20, 6)
        )
        
        log_container = StyledFrame(frame)
        log_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        self.log_text = tk.Text(
            log_container,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_muted"],
            font=("Consolas", 9),
            bd=0,
            highlightthickness=0,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(
            log_container, orient="vertical", command=self.log_text.yview,
            style="Vertical.TScrollbar"
        )
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        return frame
        
    def _init_charts(self):
        """Matplotlib-Figuren in die Tabs einbetten."""
        plt.style.use("dark_background")
        
        # --- Tab 1: Equity Curves ---
        self.fig_equity = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS["bg"])
        self.ax_equity = self.fig_equity.add_subplot(111)
        self.ax_equity.set_facecolor(COLORS["bg_secondary"])
        self.ax_equity.set_title("Monte Carlo Equity Curves", color=COLORS["text"], fontsize=11)
        self.ax_equity.set_xlabel("Trade #", color=COLORS["text_muted"])
        self.ax_equity.set_ylabel("Equity ($)", color=COLORS["text_muted"])
        self.ax_equity.tick_params(colors=COLORS["text_muted"])
        self.ax_equity.grid(True, alpha=0.2, color=COLORS["text_muted"])
        
        self.canvas_equity = FigureCanvasTkAgg(self.fig_equity, master=self.tab_equity)
        self.canvas_equity.draw()
        self.canvas_equity.get_tk_widget().pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas_equity, self.tab_equity)
        toolbar.configure(bg=COLORS["bg_secondary"])
        toolbar.update()
        
        # --- Tab 2: Distribution (Histogram) ---
        self.fig_dist = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS["bg"])
        self.ax_dist = self.fig_dist.add_subplot(111)
        self.ax_dist.set_facecolor(COLORS["bg_secondary"])
        self.ax_dist.set_title("End Equity Distribution", color=COLORS["text"], fontsize=11)
        self.ax_dist.set_xlabel("Final Equity ($)", color=COLORS["text_muted"])
        self.ax_dist.set_ylabel("Frequency", color=COLORS["text_muted"])
        self.ax_dist.tick_params(colors=COLORS["text_muted"])
        self.ax_dist.grid(True, alpha=0.2, color=COLORS["text_muted"])
        
        self.canvas_dist = FigureCanvasTkAgg(self.fig_dist, master=self.tab_dist)
        self.canvas_dist.draw()
        self.canvas_dist.get_tk_widget().pack(fill="both", expand=True)
        
        # --- Tab 3: Drawdown ---
        self.fig_dd = Figure(figsize=(8, 5), dpi=100, facecolor=COLORS["bg"])
        self.ax_dd = self.fig_dd.add_subplot(111)
        self.ax_dd.set_facecolor(COLORS["bg_secondary"])
        self.ax_dd.set_title("Drawdown Distribution", color=COLORS["text"], fontsize=11)
        self.ax_dd.set_xlabel("Max Drawdown (%)", color=COLORS["text_muted"])
        self.ax_dd.set_ylabel("Frequency", color=COLORS["text_muted"])
        self.ax_dd.tick_params(colors=COLORS["text_muted"])
        self.ax_dd.grid(True, alpha=0.2, color=COLORS["text_muted"])
        
        self.canvas_dd = FigureCanvasTkAgg(self.fig_dd, master=self.tab_dd)
        self.canvas_dd.draw()
        self.canvas_dd.get_tk_widget().pack(fill="both", expand=True)
        
        # --- Tab 4: Raw Data (Treeview) ---
        columns = ("#", "Symbol", "P&L", "Reason", "Duration")
        self.tree = ttk.Treeview(
            self.tab_raw, columns=columns, show="headings", height=20
        )
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Scrollbar für Tree
        tree_scroll = ttk.Scrollbar(self.tab_raw, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
    #Logik-Funktionen
    
    def _log(self, message, level="info"):
        """Schreibt in die Log-Console."""
        self.log_text.configure(state="normal")
        color = COLORS["text_muted"]
        if level == "success":
            color = COLORS["success"]
        elif level == "error":
            color = COLORS["danger"]
        elif level == "warning":
            color = COLORS["warning"]
            
        self.log_text.insert("end", f"{message}\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        
    def _load_data(self):
        """CSV-Datei laden und über TradeLoader parsen."""
        path = filedialog.askopenfilename(
            title="Select Trade Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
            
        self.current_file = path
        
        try:
            from src.engine import TradeLoader
            self.trades = TradeLoader.from_csv(Path(path))
            
            # UI Updates
            filename = Path(path).name
            self.lbl_file.configure(text=filename, fg=COLORS["success"])
            self.status_bar.configure(text=f"Loaded: {filename}  |  Trades: {len(self.trades)}")
            self._log(f"Loaded {len(self.trades)} trades from {filename}", "success")
            
            # Raw Data Tab befüllen
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for i, trade in enumerate(self.trades[:100]):  # max 100 anzeigen
                self.tree.insert("", "end", values=(
                    i+1,
                    trade.get("symbol", "N/A"),
                    trade.get("profit_loss", 0.0),
                    trade.get("exit_reason", "N/A"),
                    trade.get("duration", "0"),
                ))
                
        except Exception as e:
            self._log(f"Error loading file: {e}", "error")
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")
            
    def _run_simulation(self):
        """Startet die Monte-Carlo-Simulation mit den geladenen Daten."""
        if not self.trades:
            messagebox.showwarning("No Data", "Bitte zuerst eine CSV-Datei laden!")
            return

        from src.engine import MonteCarloEngine

        try:
            start_cap = float(self.param_entries["Start Capital ($):"].get())
            n_sims = int(self.param_entries["# Simulations:"].get())

            engine = MonteCarloEngine(
                trades=self.trades,
                start_capital=start_cap,
                n_simulations=n_sims,
                sampler_type="iid",
            )
            
            # 1. Engine ausführen und Ergebnis in self.simulations speichern
            self.simulations = engine.run()
            
            # 2. Charts und Metriken in der UI aktualisieren
            self._update_charts()
            self._update_metrics()
            
            self._log(f"Simulation fertig! Median Return: {self.simulations.p50_cagr:.2%}", "success")
            
        except Exception as e:
            self._log(f"Simulation Error: {e}", "error")
            messagebox.showerror("Simulation Error", f"Fehler bei der Berechnung:\n{e}")

    def _update_charts(self):
        """Zeichnet die Matplotlib-Charts mit den Simulationsdaten neu."""
        if not hasattr(self, 'simulations') or self.simulations is None:
            return

        summary = self.simulations

        # --- 1. Tab: Equity Curves ---
        self.ax_equity.clear()
        self.ax_equity.set_facecolor(COLORS["bg_secondary"])
        self.ax_equity.set_title("Monte Carlo Equity Curves", color=COLORS["text"], fontsize=11)
        self.ax_equity.set_xlabel("Trade #", color=COLORS["text_muted"])
        self.ax_equity.set_ylabel("Equity ($)", color=COLORS["text_muted"])
        self.ax_equity.tick_params(colors=COLORS["text_muted"])
        self.ax_equity.grid(True, alpha=0.2, color=COLORS["text_muted"])

        # Bis zu 100 Pfade zeichnen, damit die Performance flüssig bleibt
        max_lines = min(100, len(summary.equity_curves))
        for i in range(max_lines):
            self.ax_equity.plot(summary.equity_curves[i], color=COLORS["accent"], alpha=0.15, linewidth=0.8)

        # Perzentil-Pfade (Median / 5% / 95%) als hervorgehobene Linien
        p50 = np.median(summary.equity_curves, axis=0)
        self.ax_equity.plot(p50, color="#f7768e", linewidth=2, label="Median Path")
        self.ax_equity.legend(facecolor=COLORS["bg_tertiary"], edgecolor="none", labelcolor=COLORS["text"])
        
        self.canvas_equity.draw()

        # --- 2. Tab: Distribution Histogram ---
        self.ax_dist.clear()
        self.ax_dist.set_facecolor(COLORS["bg_secondary"])
        self.ax_dist.set_title("End Equity Distribution", color=COLORS["text"], fontsize=11)
        self.ax_dist.set_xlabel("Final Equity ($)", color=COLORS["text_muted"])
        self.ax_dist.set_ylabel("Frequency", color=COLORS["text_muted"])
        self.ax_dist.tick_params(colors=COLORS["text_muted"])
        self.ax_dist.grid(True, alpha=0.2, color=COLORS["text_muted"])

        self.ax_dist.hist(summary.final_equities, bins=40, color=COLORS["accent"], edgecolor=COLORS["bg"], alpha=0.7)
        self.canvas_dist.draw()

        # --- 3. Tab: Drawdown Histogram ---
        self.ax_dd.clear()
        self.ax_dd.set_facecolor(COLORS["bg_secondary"])
        self.ax_dd.set_title("Drawdown Distribution", color=COLORS["text"], fontsize=11)
        self.ax_dd.set_xlabel("Max Drawdown (%)", color=COLORS["text_muted"])
        self.ax_dd.set_ylabel("Frequency", color=COLORS["text_muted"])
        self.ax_dd.tick_params(colors=COLORS["text_muted"])
        self.ax_dd.grid(True, alpha=0.2, color=COLORS["text_muted"])

        self.ax_dd.hist(summary.max_drawdowns_pct, bins=40, color=COLORS["danger"], edgecolor=COLORS["bg"], alpha=0.7)
        self.canvas_dd.draw()

    def _update_metrics(self):
            """Aktualisiert die Kennzahlen auf der rechten Seite."""
            if not hasattr(self, 'simulations') or self.simulations is None:
                return

            s = self.simulations

            # Metriken berechnen & formatieren
            self.metric_labels["Total Return"].configure(text=f"{s.p50_cagr:.2%}")
            self.metric_labels["CAGR"].configure(text=f"{s.p50_cagr:.2%}")
            self.metric_labels["Max Drawdown"].configure(text=f"{s.p95_max_dd:.2f}%")
            self.metric_labels["Probability of Ruin"].configure(text=f"{s.probability_of_ruin:.2%}")
            self.metric_labels["VaR (95%)"].configure(text=f"{s.var_95:.2f} €")
            self.metric_labels["CVaR (95%)"].configure(text=f"{s.cvar_95:.2f} €")

            # Stats-Label unten rechts
            self.sim_stats.configure(
                text=f"Runs: {len(s.final_equities)}\nTrades: {len(self.trades)}\nConv. SE: {s.convergence_score:.2f}"
        )
    def _reset(self):
        #reset alle Daten und UI-Elemente
        self.trades = []
        self.simulations = []
        self.current_file = None
        self.lbl_file.configure(text="No file loaded", fg=COLORS["text_muted"])
        self.status_bar.configure(text="Ready  |  No data loaded")
        self._log("Reset complete.")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.ax_equity.clear()
        self.ax_equity.set_facecolor(COLORS["bg_secondary"])
        self.canvas_equity.draw()
        
    def _export_results(self):
        # Export-Funktion (noch nicht implementiert)
        if not self.simulations:
            messagebox.showwarning("No Data", "Run a simulation first.")
            return
        self._log("Export not yet implemented.", "warning")
        
    def _reset_layout(self):
        # GUI-Layout zurücksetzen (falls verschoben/angepasst)
        self.root.geometry("1400x850")



if __name__ == "__main__":
    root = tk.Tk()
    app = MonteCarloApp(root)
    root.mainloop()