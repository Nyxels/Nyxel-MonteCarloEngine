# NyxQuant :: Monte Carlo Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange)]()

> A Python-based Monte Carlo simulation engine for robustness testing of algorithmic trading strategies. Built for production-grade quantitative finance workflows.

---

## Overview

**NyxQuant** is a desktop application designed to answer the most critical question in quantitative trading:

> *"How robust is my strategy, really?"*

Historical backtests show **one** possible past. This engine simulates **thousands** of possible futures by resampling trade sequences, revealing tail risk, drawdown distributions, and strategy fragility before capital is deployed.

### Why Monte Carlo?

| Backtest | Monte Carlo |
|----------|-------------|
| One historical realization | Distribution of all possible futures |
| Point estimate (Sharpe, CAGR) | Confidence intervals for every metric |
| Ignores path dependency | Explicitly models path dependency |
| Hidden tail risk | Exposes tail risk via percentile analysis |

---

## Architecture

┌─────────────────────────────────────────────────────────────┐
│                        GUI Layer                            │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   Control    │  │   Chart Area     │  │    Metrics     │ │
│  │   Panel      │  │  (Matplotlib)    │  │    & Logs      │ │
│  └──────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────┐
│                      Engine Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐     │
│  │   Data       │  │  Bootstrap   │  │   Analytics    │     │
│  │   Ingestion  │→ │  (i.i.d. /   │→ │   (CAGR, DD,   │     │
│  │   (CSV)      │  │   Block)     │  │   Sharpe, etc.)│     │
│  └──────────────┘  └──────────────┘  └────────────────┘     │
└─────────────────────────────────────────────────────────────┘

---

## Features

### Current
- **Professional Dark-Mode GUI** built with Tkinter + embedded Matplotlib
- **CSV Trade Data Import** with automatic validation
- **Non-Parametric Bootstrap** on trade level (preserves skewness & kurtosis)
- **Real-time Metric Dashboard**:
  - Total Return & CAGR
  - Sharpe Ratio
  - Maximum Drawdown (Peak-to-Trough)
  - Profit Factor
  - Probability of Ruin
- **Interactive Charts**:
  - Equity Curve Envelope (5th / 50th / 95th percentile)
  - End-Equity Distribution Histogram
  - Drawdown Distribution Analysis

### Planned
- [ ] Block-Bootstrap & Stationary Bootstrap (serial correlation handling)
- [ ] Parametric simulation (GBM, GARCH) for stress testing
- [ ] Kelly Criterion & Fractional Kelly position sizing integration
- [ ] Walk-forward analysis module
- [ ] DeFi / On-chain data connector (Uniswap, Aave)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Nyxels/Nyxel-MonteCarloEngine.git
cd Nyxel-MonteCarloEngine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

Requirements
plain

numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
scipy>=1.10.0

Usage
1. Generate Dummy Trade Data
bash

python src/generate_dummy_data.py

Creates data/dummy_trades.csv with realistic, logically consistent futures trades (ES, NQ, GC, CL, NG).
2. Launch the Engine
bash

python src/gui.py

3. Run Simulation

    Click "Load CSV" and select your trade data
    Set parameters (Start Capital, # Simulations, Position Size)
    Click "▶ RUN SIMULATION"
    Analyze equity curves, distributions, and metrics in real-time

Methodology
Trade-Level Bootstrap
The engine treats each trade as an atomic unit of strategy behavior. Unlike return-level bootstrapping (which destroys setup logic), trade-level resampling preserves:

    Win rate & profit factor
    Trade duration & path dependency
    Symbol-specific characteristics

Consistent P&L Calculation
P&L is never randomized independently. It is derived deterministically from:
plain

P&L = (Exit - Entry) × Direction × Lots × PointValue

This prevents the "equity explosion" problem common in naive Monte Carlo implementations.
Metrics Computed Per Simulation
Tabellen
Metric	Definition
CAGR	Compound Annual Growth Rate from start to end equity
Max Drawdown	Largest peak-to-trough decline in equity curve
Sharpe Ratio	Excess return per unit of volatility
Profit Factor	Gross profit / Gross loss
Probability of Ruin	% of simulations where equity falls below threshold
Project Structure
plain

nyxquant-monte-carlo/
├── data/                   # Trade data (CSV)
├── outputs/                # Simulation results & exports
├── src/
│   ├── gui.py              # Main application (Tkinter + Matplotlib)
│   ├── engine.py           # Monte Carlo core logic (bootstrap, metrics)
│   ├── generate_dummy_data.py  # Realistic futures trade generator
│   └── utils.py            # Helper functions (drawdown calc, etc.)
├── tests/                  # Unit tests
├── requirements.txt
└── README.md

Background
This project is part of a focused transition into quantitative finance and algorithmic trading. It combines:

    4 years of enterprise software engineering (Java, Python, Docker, Linux) at Volkswagen Group
    Self-directed study in stochastic processes, risk management, and derivatives
    Hands-on trading experience with futures and prop-firm capital

Goal: Build production-grade quantitative tools and contribute to systematic trading teams in Switzerland (Zürich / Zug).
Connect

    LinkedIn: linkedin.com/in/marcel-rohr-60202a357
    GitHub: github.com/Nyxels
    Location: Germany → Switzerland (Zürich/Zug) — ready to relocate

License
MIT License — feel free to use, modify, and contribute.
plain
