import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.interpolate import make_interp_spline

# Load dataset
df = pd.read_csv("results.csv")

# Filter valid and comparable entries
df = df[(df["is_broken"] == False) & (df["is_comparable_dft@dft_mlp@mlp"] == True)].copy()
df["formation_energy_abs_error"] = abs(df["interface_E_form_delta_dft@dft"] - df["interface_E_form_delta_dft@mlp"])

# Group by electron count and preprocess
summary = df.groupby("interface_electron_n")["formation_energy_abs_error"].mean().fillna(0).reset_index()
summary["formation_energy_abs_error"] = summary["formation_energy_abs_error"].apply(
    lambda x: x if np.isfinite(x) and x > 0 else 1e-6
)
summary = summary.sort_values("interface_electron_n").reset_index(drop=True)

# X and Y arrays
x_vals = summary["interface_electron_n"].to_numpy()
y_vals = summary["formation_energy_abs_error"].to_numpy()

# Linear regression (primary)
x_reshaped = x_vals.reshape(-1, 1)
linear_model = LinearRegression().fit(x_reshaped, y_vals)
y_linear = linear_model.predict(x_reshaped)

# Smoothed spline (primary)
x_smooth = np.linspace(x_vals.min(), x_vals.max(), 300)
spline = make_interp_spline(x_vals, y_vals, k=3)
y_smooth = spline(x_smooth)

# ±250 moving average (secondary)
rolling_avg_250 = [np.mean(y_vals[(x_vals >= x - 250) & (x_vals <= x + 250)]) for x in x_vals]
x_smooth_250 = np.linspace(x_vals.min(), x_vals.max(), 300)
spline_250 = make_interp_spline(x_vals, rolling_avg_250, k=3)
y_smooth_250 = spline_250(x_smooth_250)

# Linear regression (secondary)
linear_model_2 = LinearRegression().fit(x_reshaped, rolling_avg_250)
y_linear_2 = linear_model_2.predict(x_reshaped)

# Custom gradient fill function
def gradient_fill_under_curve(ax, x, y, base, color='blue', max_alpha=0.2, steps=10):
    for i in range(len(x) - 1):
        y0 = y[i]
        y1 = y[i + 1]
        for j in range(steps):
            alpha = max_alpha * (1 - j / steps)
            y0a = y0 - (y0 - base) * j / (2 * steps)
            y0b = y0 - (y0 - base) * (j + 1) / (2 * steps)
            y1a = y1 - (y1 - base) * j / (2 * steps)
            y1b = y1 - (y1 - base) * (j + 1) / (2 * steps)
            ax.fill([x[i], x[i + 1], x[i + 1], x[i]],
                    [y0a, y1a, y1b, y0b],
                    color=color, alpha=alpha)

# Plot figure
fig, ax1 = plt.subplots(figsize=(10, 6))

# Primary Y-axis
ax1.scatter(x_vals, y_vals, color="grey", alpha=0.6, label="Mean Absolute Error (Points)")
ax1.plot(x_vals, y_linear, color="red", linestyle="--", linewidth=2.0, label="Primary Linear Trend")
ax1.plot(x_smooth, y_smooth, color="red", linewidth=2.0, label="Smoothed Raw Means")
gradient_fill_under_curve(ax1, x_smooth, y_smooth, base=0, color="red", max_alpha=0.2)
ax1.set_xlabel("Number of Electrons", color="black")
ax1.set_ylabel("Mean Absolute Formation Energy Error [eV]", color="black")
ax1.tick_params(axis="x", colors="black")
ax1.tick_params(axis="y", colors="black")
ax1.grid(True, linestyle="--", linewidth=0.5)

# Secondary Y-axis
ax2 = ax1.twinx()
ax2.plot(x_smooth_250, y_smooth_250, color="violet", linewidth=2.0, label="±250 Smoothed Avg")
ax2.plot(x_vals, y_linear_2, color="violet", linestyle="--", linewidth=2.0, label="Secondary Linear Trend")
gradient_fill_under_curve(ax2, x_smooth_250, y_smooth_250, base=0, color="violet", max_alpha=0.2)
ax2.set_ylabel("±250 Moving Average Error [eV]", color="black")
ax2.tick_params(axis="y", colors="black")

# Title and layout
fig.suptitle("Formation Energy Error vs Number of Electrons", color="black")
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.legend(loc="upper left", bbox_to_anchor=(0.13, 0.88), labelcolor="black", edgecolor="black", frameon=False)

# Save plot
plt.savefig("./plots/error_vs_electron_count.png", dpi=300)
plt.show()
