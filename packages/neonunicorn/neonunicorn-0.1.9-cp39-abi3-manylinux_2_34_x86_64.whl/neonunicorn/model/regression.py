import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from typing import Tuple, Optional
import polars
import sklearn.model_selection


class LinearRegression:
    """
    A PyTorch-based Linear Regression implementation for one variable.

    Model: y = w_1 * x + w_0
    Loss: Mean Squared Error

    Features:
    - Gradient-based optimization using PyTorch
    - Confidence intervals for parameters w_1 and w_0
    - Visualization with confidence bands
    """

    def __init__(self, learning_rate: float = 0.01, max_epochs: int = 1000, tolerance: float = 1e-6):
        """
        Initialize the Linear Regression model.
        """
        self.learning_rate = learning_rate
        self.max_epochs = max_epochs
        self.tolerance = tolerance

        # Model parameters
        self.w_1 = nn.Parameter(torch.randn(1, requires_grad=True))  # slope
        self.w_0 = nn.Parameter(torch.randn(1, requires_grad=True))  # intercept

        # Training state
        self.X_train = None
        self.y_train = None
        self.fitted = False

        # Statistics for inference
        self.n_samples = None
        self.residual_sum_squares = None
        self.X_mean = None
        self.X_var = None

        # Training setup
        self.criterion = nn.MSELoss()
        self.optimizer = optim.SGD([self.w_1, self.w_0], lr=self.learning_rate)

        # Logs
        self.loss_history = []
        self.w0_history = []
        self.w1_history = []

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        return self.w_1 * X + self.w_0

    def fit(self, X: np.ndarray, y: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> 'LinearRegression':
        """Fit model and compute R² on test set."""
        self.X_train = torch.tensor(X, dtype=torch.float32)
        self.y_train = torch.tensor(y, dtype=torch.float32)
        self.n_samples = len(X)

        self.X_mean = float(np.mean(X))
        self.X_var = float(np.var(X, ddof=1))

        prev_loss = float('inf')

        for epoch in range(self.max_epochs):
            self.optimizer.zero_grad()
            y_pred = self.forward(self.X_train)
            loss = self.criterion(y_pred, self.y_train)
            loss.backward()
            self.optimizer.step()

            curr_loss = loss.item()
            self.loss_history.append(curr_loss)
            self.w0_history.append(float(self.w_0.item()))
            self.w1_history.append(float(self.w_1.item()))

            if abs(prev_loss - curr_loss) < self.tolerance:
                print(f"Converged after {epoch + 1} epochs")
                break
            prev_loss = curr_loss

        with torch.no_grad():
            y_pred = self.forward(self.X_train)
            residuals = self.y_train - y_pred
            self.residual_sum_squares = float(torch.sum(residuals ** 2))

        self.fitted = True

        y_test_pred = self.predict(X_test)
        ss_res = np.sum((y_test - y_test_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        print(f"R2 on test data: {r2:.4f}")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if not self.fitted:
            raise ValueError("Model must be fitted before making predictions.")
        X_tensor = torch.tensor(X, dtype=torch.float32)
        with torch.no_grad():
            preds = self.forward(X_tensor)
        return preds.numpy()

    def get_parameters(self) -> Tuple[float, float]:
        """Return fitted parameters."""
        if not self.fitted:
            raise ValueError("Model must be fitted before accessing parameters.")
        return float(self.w_1.item()), float(self.w_0.item())

    def parameter_confidence_intervals(self, confidence_level: float = 0.95) -> dict:
        """Compute 95% CI for parameters."""
        if not self.fitted:
            raise ValueError("Model must be fitted before computing confidence intervals.")
        df = self.n_samples - 2
        alpha = 1 - confidence_level
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        mse = self.residual_sum_squares / df
        se_reg = np.sqrt(mse)
        se_w1 = se_reg / np.sqrt(self.n_samples * self.X_var)
        se_w0 = se_reg * np.sqrt(1 / self.n_samples + self.X_mean**2 / (self.n_samples * self.X_var))
        w1, w0 = self.get_parameters()
        return {
            "w_1_confidence_interval": (w1 - t_crit * se_w1, w1 + t_crit * se_w1),
            "w_0_confidence_interval": (w0 - t_crit * se_w0, w0 + t_crit * se_w0),
            "confidence_level": confidence_level
        }

    def plot_regression_with_confidence_band(self, confidence_level: float = 0.95,
                                             figsize: Tuple[int, int] = (10, 6),
                                             title: Optional[str] = None) -> plt.Figure:
        """Plot regression line with confidence interval."""
        if not self.fitted:
            raise ValueError("Model must be fitted before plotting.")
        X_np = self.X_train.numpy()
        y_np = self.y_train.numpy()
        X_range = np.linspace(X_np.min(), X_np.max(), 100)
        y_pred = self.predict(X_range)
        df = self.n_samples - 2
        alpha = 1 - confidence_level
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        mse = self.residual_sum_squares / df
        se_reg = np.sqrt(mse)
        X_centered = X_range - self.X_mean
        se_pred = se_reg * np.sqrt(1 / self.n_samples + X_centered**2 / (self.n_samples * self.X_var))
        margin = t_crit * se_pred
        y_upper = y_pred + margin
        y_lower = y_pred - margin

        fig, ax = plt.subplots(figsize=figsize)
        ax.scatter(X_np, y_np, alpha=0.6, color="blue", label="Data")
        ax.plot(X_range, y_pred, "r-", linewidth=2, label="Fitted line")
        ax.fill_between(X_range, y_lower, y_upper, color="red", alpha=0.3,
                        label=f"{int(confidence_level*100)}% CI")
        w1, w0 = self.get_parameters()
        ax.set_title(title or f"y = {w1:.3f}x + {w0:.3f}")
        ax.set_xlabel("X")
        ax.set_ylabel("y")
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_training_history(self) -> plt.Figure:
        """Plot loss and parameter trajectories."""
        if not self.fitted:
            raise ValueError("Model must be fitted before plotting history.")
        epochs = range(len(self.loss_history))
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(epochs, self.loss_history, color="tab:blue", label="Loss")
        ax1.set_xlabel("Epochs")
        ax1.set_ylabel("Loss", color="tab:blue")
        ax2 = ax1.twinx()
        ax2.plot(epochs, self.w0_history, color="tab:green", label="w0")
        ax2.plot(epochs, self.w1_history, color="tab:orange", label="w1")
        ax2.set_ylabel("Parameters", color="tab:red")
        fig.tight_layout()
        ax1.legend(loc="upper right")
        plt.title("Training History")
        return fig

    def summary(self) -> dict:
        """Return model summary stats."""
        if not self.fitted:
            raise ValueError("Model must be fitted before summary.")
        w1, w0 = self.get_parameters()
        y_mean = float(torch.mean(self.y_train))
        ss_tot = float(torch.sum((self.y_train - y_mean) ** 2))
        r2 = 1 - self.residual_sum_squares / ss_tot
        adj_r2 = 1 - ((1 - r2) * (self.n_samples - 1) / (self.n_samples - 2))
        rmse = np.sqrt(self.residual_sum_squares / self.n_samples)
        return {
            "parameters": {"w_1 (slope)": w1, "w_0 (intercept)": w0},
            "model_fit": {"r_squared": r2, "adjusted_r_squared": adj_r2, "rmse": rmse},
            "training_info": {"epochs": len(self.loss_history), "final_loss": self.loss_history[-1]}
        }


class CauchyRegression:
    """
    Robust regression using Cauchy loss (heavy-tailed, resistant to outliers).
    """

    def __init__(self, n_features=4, c=1.0, lr=0.0001, epochs=2000):
        self.n_features = n_features
        self.c = c
        self.lr = lr
        self.epochs = epochs
        torch.manual_seed(0)
        self.w = torch.randn((n_features, 1), requires_grad=True)
        self.b = torch.randn(1, requires_grad=True)

    def forward(self, X):
        return X @ self.w + self.b

    def cauchy_loss(self, y_pred, y_true):
        r = (y_true - y_pred) / self.c
        return 0.5 * (self.c**2) * torch.log1p(r**2).mean()

    def fit(self, X, y):
        for _ in range(self.epochs):
            y_pred = self.forward(X)
            loss = self.cauchy_loss(y_pred, y)
            loss.backward()
            with torch.no_grad():
                self.w -= self.lr * self.w.grad
                self.b -= self.lr * self.b.grad
                self.w.grad.zero_()
                self.b.grad.zero_()
        return loss.item()

    def predict(self, X):
        with torch.no_grad():
            return self.forward(X)


if __name__ == "__main__":
    # Local demo for quick verification
    np.random.seed(42)
    torch.manual_seed(42)

    data = polars.read_csv("/mnt/c/Users/fm0032/Downloads/Hydropower.csv")
    X = data["BCR"].to_numpy()
    y = data["AnnualProduction"].to_numpy()
    X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y, test_size=0.2)

    model = LinearRegression(learning_rate=0.01, max_epochs=250)
    model.fit(X_train, y_train, X_test, y_test)

    print("\nModel Summary:")
    import pprint
    pprint.pprint(model.summary())

    model.plot_regression_with_confidence_band()
    plt.show()
    model.plot_training_history()
    plt.show()
