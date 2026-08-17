import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple, Union
import numpy as np


class TradeLoader:
    """Lädt und parst Trade-Daten aus CSV-Dateien."""

    @staticmethod
    def from_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")

        trades = []
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Automatische Erkennung gängiger PnL-Spaltennamen
                pnl_key = next(
                    (k for k in row.keys() if k.lower() in ["profit_loss", "p&l", "pnl", "profit"]), 
                    None
                )
                if pnl_key and row[pnl_key] != "":
                    try:
                        row["profit_loss"] = float(row[pnl_key])
                    except ValueError:
                        row["profit_loss"] = 0.0
                else:
                    row["profit_loss"] = 0.0
                trades.append(row)
        return trades


class MetricsCalculator:
    """Berechnet Risiko- und Performance-Kennzahlen."""

    @staticmethod
    def max_drawdown(equity_curve: np.ndarray) -> Tuple[float, float]:
        """
        Berechnet den maximalen absoluten ($) und prozentualen (%) Drawdown.
        Rückgabe: (max_dd_abs, max_dd_pct)
        """
        if len(equity_curve) == 0:
            return 0.0, 0.0

        peak = np.maximum.accumulate(equity_curve)
        drawdown_abs = peak - equity_curve
        
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdown_pct = np.where(peak > 0, (drawdown_abs / peak) * 100.0, 0.0)

        max_dd_abs = float(np.max(drawdown_abs)) if len(drawdown_abs) > 0 else 0.0
        max_dd_pct = float(np.max(drawdown_pct)) if len(drawdown_pct) > 0 else 0.0
        return max_dd_abs, max_dd_pct


@dataclass
class SimulationSummary:
    """Ergebnis-Container einer Monte-Carlo-Simulation."""
    equity_curves: np.ndarray        # Shape: (n_simulations, n_trades + 1)
    final_equities: np.ndarray       # Shape: (n_simulations,)
    max_drawdowns_pct: np.ndarray    # Shape: (n_simulations,)
    p50_cagr: float = 0.0
    p95_max_dd: float = 0.0
    probability_of_ruin: float = 0.0
    convergence_score: float = 0.0


class MonteCarloEngine:
    """Performante, vektorisierte Monte-Carlo-Engine."""

    def __init__(
        self,
        trades: List[Dict[str, Any]],
        start_capital: float = 100000.0,
        n_simulations: int = 1000,
        sampler_type: str = "iid",
        ruin_threshold: float = 0.5,  # Ruin z. B. bei 50% Drawdown/Kapitalverlust
    ):
        self.trades = trades
        self.start_capital = start_capital
        self.n_simulations = n_simulations
        self.sampler_type = sampler_type
        self.ruin_threshold = ruin_threshold

        # PnLs als NumPy-Array isolieren
        if self.trades and isinstance(self.trades[0], dict):
            self.pnls = np.array([float(t.get("profit_loss", 0.0)) for t in self.trades])
        elif isinstance(self.trades, (list, np.ndarray)):
            self.pnls = np.array(self.trades, dtype=float)
        else:
            self.pnls = np.array([0.0])

    def run(self) -> SimulationSummary:
        n_trades = len(self.pnls)
        if n_trades == 0:
            empty_curve = np.full((self.n_simulations, 1), self.start_capital)
            return SimulationSummary(empty_curve, np.full(self.n_simulations, self.start_capital), np.zeros(self.n_simulations))

        # 1. Bootstrap-Resampling (I.I.D.)
        # Shape: (n_simulations, n_trades)
        indices = np.random.choice(n_trades, size=(self.n_simulations, n_trades), replace=True)
        simulated_pnls = self.pnls[indices]

        # 2. Equity Curves berechnen (Startkapital + kumulierte PnLs)
        cum_pnls = np.cumsum(simulated_pnls, axis=1)
        equity_curves = np.hstack([
            np.full((self.n_simulations, 1), self.start_capital),
            self.start_capital + cum_pnls
        ])

        # 3. Metriken berechnen
        final_equities = equity_curves[:, -1]

        # Vektorisierte Max Drawdowns pro Pfad
        peaks = np.maximum.accumulate(equity_curves, axis=1)
        dds_abs = peaks - equity_curves
        dds_pct = np.where(peaks > 0, (dds_abs / peaks) * 100.0, 0.0)
        max_dds_pct = np.max(dds_pct, axis=1)

        # Ruin-Wahrscheinlichkeit
        min_equities = np.min(equity_curves, axis=1)
        ruin_level = self.start_capital * (1.0 - self.ruin_threshold)
        prob_ruin = float(np.mean(min_equities <= ruin_level))

        # Ertrag & Perzentile
        years = (n_trades / 252)  # Annahme: 252 Handelstage pro Jahr
        years = max(years, 1e-6)  # Vermeidung von Division durch Null
        cagr = (final_equities / self.start_capital) ** (1.0 / years) - 1.0
        p50_cagr = float(np.percentile(cagr, 50))
        p95_max_dd = float(np.percentile(max_dds_pct, 95))
        
        # Konvergenz-Standardfehler
        convergence_score = float(np.std(cagr) / np.sqrt(self.n_simulations))

        return SimulationSummary(
            equity_curves=equity_curves,
            final_equities=final_equities,
            max_drawdowns_pct=max_dds_pct,
            p50_cagr=p50_cagr,
            p95_max_dd=p95_max_dd,
            probability_of_ruin=prob_ruin,
            convergence_score=convergence_score,
        )


# --- STANDALONE TEST CODE ---
if __name__ == "__main__":
    # Test 1: Max Drawdown
    eq = np.array([100, 110, 105, 120, 115, 90, 95])
    dd, dd_pct = MetricsCalculator.max_drawdown(eq)
    assert dd == 30
    assert abs(dd_pct - 25.0) < 0.01

    # Test 2: Monte Carlo Engine Run
    dummy_trades = [{"profit_loss": x} for x in [100, -50, 200, -30, 80, -120]]
    engine = MonteCarloEngine(dummy_trades, start_capital=10000, n_simulations=100)
    summary = engine.run()

    print("Engine Test erfolgreich!")
    print(f"Median Return: {summary.p50_cagr:.2%}")
    print(f"95% Max DD:    {summary.p95_max_dd:.2f}%")
    print(f"Prob of Ruin:  {summary.probability_of_ruin:.2%}")