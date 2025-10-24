import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from typing import Tuple, Optional
import warnings
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
    
    def __init__(self, learning_rate: float = 0.01, max_epochs: int = 1000, 
                 tolerance: float = 1e-6):
        """
        Initialize the Linear Regression model.
        
        Args:
            learning_rate: Learning rate for gradient descent
            max_epochs: Maximum number of training epochs
            tolerance: Convergence tolerance for early stopping
        """
        self.learning_rate = learning_rate
        self.max_epochs = max_epochs
        self.tolerance = tolerance
        
        # Model parameters
        self.w_1 = nn.Parameter(torch.randn(1, requires_grad=True))  # slope
        self.w_0 = nn.Parameter(torch.randn(1, requires_grad=True))  # intercept
        
        # Training data storage
        self.X_train = None
        self.y_train = None
        
        # Model statistics for confidence intervals
        self.n_samples = None
        self.residual_sum_squares = None
        self.X_mean = None
        self.X_var = None
        self.fitted = False
        
        # Loss function and optimizer
        self.criterion = nn.MSELoss()
        self.optimizer = optim.SGD([self.w_1, self.w_0], lr=self.learning_rate)
        
        # Training history
        self.loss_history = []
        self.w0_history = []
        self.w1_history = []
    
    def forward(self, X: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the linear model.
        
        Args:
            X: Input tensor of shape (n_samples,)
            
        Returns:
            Predictions tensor of shape (n_samples,)
        """
        return self.w_1 * X + self.w_0
    
    def fit(self, X: np.ndarray, y: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> 'LinearRegression':
        """
        Fit the linear regression model to the training data and compute R2 on test data.
        
        Args:
            X: Input features of shape (n_samples,)
            y: Target values of shape (n_samples,)
            X_test: Test input features of shape (n_samples,)
            y_test: Test target values of shape (n_samples,)
            
        Returns:
            self: Returns the fitted model instance
        """
        # Convert to PyTorch tensors
        self.X_train = torch.tensor(X, dtype=torch.float32)
        self.y_train = torch.tensor(y, dtype=torch.float32)
        self.n_samples = len(X)
        
        # Store statistics for confidence intervals
        self.X_mean = float(np.mean(X))
        self.X_var = float(np.var(X, ddof=1))  # Sample variance
        
        # Training loop
        prev_loss = float('inf')
        
        for epoch in range(self.max_epochs):
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            y_pred = self.forward(self.X_train)
            
            # Compute loss
            loss = self.criterion(y_pred, self.y_train)
            
            # Backward pass
            loss.backward()
            
            # Update parameters
            self.optimizer.step()
            
            # Store loss history
            current_loss = loss.item()
            self.loss_history.append(current_loss)
            self.w0_history.append(float(self.w_0.item()))
            self.w1_history.append(float(self.w_1.item()))
            
            # Check for convergence
            if abs(prev_loss - current_loss) < self.tolerance:
                print(f"Converged after {epoch + 1} epochs")
                break
            
            prev_loss = current_loss
        
        # Compute residual sum of squares for confidence intervals
        with torch.no_grad():
            y_pred = self.forward(self.X_train)
            residuals = self.y_train - y_pred
            self.residual_sum_squares = float(torch.sum(residuals ** 2))
        
        self.fitted = True

        # Compute R2 on test data
        y_test_pred = self.predict(X_test)
        ss_res_test = np.sum((y_test - y_test_pred) ** 2)
        ss_tot_test = np.sum((y_test - np.mean(y_test)) ** 2)
        r2_test = 1 - (ss_res_test / ss_tot_test)
        print(f"R2 on test data: {r2_test:.4f}")

        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Input features of shape (n_samples,)
            
        Returns:
            Predictions as numpy array
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        X_tensor = torch.tensor(X, dtype=torch.float32)
        
        with torch.no_grad():
            predictions = self.forward(X_tensor)
        
        return predictions.numpy()
    
    def get_parameters(self) -> Tuple[float, float]:
        """
        Get the fitted parameters.
        
        Returns:
            Tuple of (w_1, w_0) - slope and intercept
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before accessing parameters")
        
        return float(self.w_1.item()), float(self.w_0.item())
    
    def parameter_confidence_intervals(self, confidence_level: float = 0.95) -> dict:
        """
        Compute confidence intervals for parameters w_1 and w_0.
        
        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Dictionary containing confidence intervals for both parameters
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before computing confidence intervals")
        
        # Degrees of freedom
        df = self.n_samples - 2
        
        # Critical t-value
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, df)
        
        # Standard error of regression
        mse = self.residual_sum_squares / df
        se_regression = np.sqrt(mse)
        
        # Standard error for w_1 (slope)
        se_w1 = se_regression / np.sqrt(self.n_samples * self.X_var)
        
        # Standard error for w_0 (intercept)
        se_w0 = se_regression * np.sqrt(1/self.n_samples + self.X_mean**2 / (self.n_samples * self.X_var))
        
        # Get current parameter values
        w_1_val, w_0_val = self.get_parameters()
        
        # Compute confidence intervals
        w_1_ci = (
            w_1_val - t_critical * se_w1,
            w_1_val + t_critical * se_w1
        )
        
        w_0_ci = (
            w_0_val - t_critical * se_w0,
            w_0_val + t_critical * se_w0
        )
        
        return {
            'w_1_confidence_interval': w_1_ci,
            'w_0_confidence_interval': w_0_ci,
            'confidence_level': confidence_level,
            'standard_errors': {
                'se_w1': se_w1,
                'se_w0': se_w0,
                'se_regression': se_regression
            }
        }
    
    def plot_regression_with_confidence_band(self, confidence_level: float = 0.95, 
                                           figsize: Tuple[int, int] = (10, 6),
                                           title: Optional[str] = None) -> plt.Figure:
        """
        Plot the fitted regression line with confidence band.
        
        Args:
            confidence_level: Confidence level for the band
            figsize: Figure size tuple
            title: Optional plot title
            
        Returns:
            matplotlib Figure object
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before plotting")
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Convert training data to numpy for plotting
        X_np = self.X_train.numpy()
        y_np = self.y_train.numpy()
        
        # Create prediction range
        X_range = np.linspace(X_np.min(), X_np.max(), 100)
        y_pred_range = self.predict(X_range)
        
        # Compute confidence band
        df = self.n_samples - 2
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, df)
        
        mse = self.residual_sum_squares / df
        se_regression = np.sqrt(mse)
        
        # Standard error for predictions (confidence band)
        X_centered = X_range - self.X_mean
        se_pred = se_regression * np.sqrt(1/self.n_samples + X_centered**2 / (self.n_samples * self.X_var))
        
        # Confidence band bounds
        margin_of_error = t_critical * se_pred
        y_upper = y_pred_range + margin_of_error
        y_lower = y_pred_range - margin_of_error
        
        # Plot data points
        ax.scatter(X_np, y_np, alpha=0.6, color='blue', label='Data points')
        
        # Plot regression line
        ax.plot(X_range, y_pred_range, 'r-', linewidth=2, label='Fitted line')
        
        # Plot confidence band
        ax.fill_between(X_range, y_lower, y_upper, alpha=0.3, color='red', 
                       label=f'{int(confidence_level*100)}% Confidence band')
        
        # Get parameter values for display
        w_1_val, w_0_val = self.get_parameters()
        
        # Labels and title
        ax.set_xlabel('X')
        ax.set_ylabel('y')
        if title is None:
            title = f'Linear Regression: y = {w_1_val:.3f}x + {w_0_val:.3f}'
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_training_history(self) -> plt.Figure:
        """
        Plot the training history: loss and parameter values over epochs.
        
        Returns:
            matplotlib Figure object
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before plotting history")

        epochs = range(len(self.loss_history))

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.set_xlabel('Epochs')
        ax1.set_ylabel('Loss', color='tab:blue')
        ax1.plot(epochs, self.loss_history, color='tab:blue', label='Loss')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Parameters', color='tab:red')
        ax2.plot(epochs, self.w0_history, color='tab:green', label='w0')
        ax2.plot(epochs, self.w1_history, color='tab:orange', label='w1')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        fig.tight_layout()
        plt.title('Training History: Loss and Parameters')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        return fig
    
    def summary(self) -> dict:
        """
        Provide a summary of the fitted model.
        
        Returns:
            Dictionary containing model summary statistics
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before generating summary")
        
        w_1_val, w_0_val = self.get_parameters()
        
        # R-squared calculation
        y_mean = float(torch.mean(self.y_train))
        ss_tot = float(torch.sum((self.y_train - y_mean) ** 2))
        r_squared = 1 - (self.residual_sum_squares / ss_tot)
        
        # Adjusted R-squared
        adj_r_squared = 1 - ((1 - r_squared) * (self.n_samples - 1) / (self.n_samples - 2))
        
        # RMSE
        rmse = np.sqrt(self.residual_sum_squares / self.n_samples)
        
        return {
            'parameters': {
                'w_1 (slope)': w_1_val,
                'w_0 (intercept)': w_0_val
            },
            'model_fit': {
                'r_squared': r_squared,
                'adjusted_r_squared': adj_r_squared,
                'rmse': rmse,
                'residual_sum_squares': self.residual_sum_squares
            },
            'training_info': {
                'n_samples': self.n_samples,
                'epochs_trained': len(self.loss_history),
                'final_loss': self.loss_history[-1] if self.loss_history else None
            }
        }

if __name__ == "__main__":
    np.random.seed(42)
    torch.manual_seed(42)

    # Load data (local demo)
    data = polars.read_csv("/mnt/c/Users/fm0032/Downloads/Hydropower.csv")
    X = data["BCR"].to_numpy()
    y = data["AnnualProduction"].to_numpy()

    X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
        X, y, test_size=0.2
    )

    # Create and fit model
    model = LinearRegression(learning_rate=0.01, max_epochs=250)
    model.fit(X_train, y_train, X_test, y_test)

    # Make predictions
    y_pred = model.predict(X_test)
    test_mse = float(np.mean((y_pred - y_test) ** 2))
    print(f"Test MSE: {test_mse:.4f}")

    # Print model summary
    import pprint
    pprint.pprint(model.summary())

    # Plot regression with confidence band
    model.plot_regression_with_confidence_band()
    plt.show()

    # Plot training history
    model.plot_training_history()
    plt.show()

# Plot training history
model.plot_training_history()
plt.show()
class CauchyRegression:
    def __init__(self, n_features=4, c=1.0, lr=0.0001, epochs=2000):
        self.n_features = n_features
        self.c = c
        self.lr = lr
        self.epochs = epochs

        import torch
        torch.manual_seed(0)
        self.w = torch.randn((n_features, 1), requires_grad=True)
        self.b = torch.randn(1, requires_grad=True)

    def forward(self, X):
        return X @ self.w + self.b

    def cauchy_loss(self, y_pred, y_true):
        import torch
        r = (y_true - y_pred) / self.c
        return 0.5 * (self.c**2) * torch.log1p(r**2).mean()

    def fit(self, X, y):
        import torch
        for epoch in range(1, self.epochs + 1):
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
