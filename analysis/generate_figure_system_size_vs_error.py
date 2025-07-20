import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Load dataset
df = pd.read_csv("results.csv")

# Filter valid and comparable entries
df = df[(df["is_broken"] == False) & (df["is_comparable_dft@dft_mlp@mlp"] == True)].copy()

# Compute absolute error between MLP and DFT
df["formation_energy_abs_error"] = abs(
    df["interface_E_form_delta_dft@dft"] - df["interface_E_form_delta_dft@mlp"]
)

# Group by number of electrons
summary = (
    df.groupby("interface_electron_n")["formation_energy_abs_error"]
    .mean()
    .fillna(0)
    .reset_index()
)
summary["formation_energy_abs_error"] = summary["formation_energy_abs_error"].apply(
    lambda x: x if np.isfinite(x) and x > 0 else 1e-6
)
summary = summary.sort_values("interface_electron_n").reset_index(drop=True)

# Extract arrays
x_vals = summary["interface_electron_n"].to_numpy()
y_vals = summary["formation_energy_abs_error"].to_numpy()

# Rolling ±250 average
rolling_avg_250 = [
    np.mean(y_vals[(x_vals >= x - 250) & (x_vals <= x + 250)]) for x in x_vals
]

# Linear regression on rolling average
x_reshaped = x_vals.reshape(-1, 1)
trend_model = LinearRegression().fit(x_reshaped, rolling_avg_250)
y_trend = trend_model.predict(x_reshaped)

# Extract trendline equation
slope = trend_model.coef_[0]
intercept = trend_model.intercept_
equation = f"y = {slope:.2e}x + {intercept:.2f}"

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x_vals, y_vals, width=4.0, color="red", alpha=0.8, label="MLP vs DFT Error")
ax.plot(
    x_vals,
    y_trend,
    color="red",
    linestyle="--",
    linewidth=2.5,
    label=f"±250 Rolling Avg Trend\n({equation})"
)

# Formatting
ax.set_xlabel("Number of Electrons", color="black")
ax.set_ylabel("Mean Absolute Formation Energy Error [eV]", color="black")
ax.set_title("Formation Energy Error vs Number of Electrons", color="black")
ax.tick_params(axis="x", colors="black")
ax.tick_params(axis="y", colors="black")
ax.grid(True, linestyle="--", linewidth=0.5)
ax.legend(loc="upper left", frameon=False, labelcolor="black", edgecolor="black")

# Save output
plt.tight_layout()
plt.savefig("./plots/error_vs_electron_trend_equation.png", dpi=300)
plt.show()
