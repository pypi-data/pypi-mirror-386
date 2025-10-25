"""
Solver comparison module for coastal wave transport models

Provides tools to compare different numerical methods (RK4, RK45, DOP853)
in terms of accuracy, computational efficiency, and stability.

This module helps users select the most appropriate solver for their specific
application based on quantitative metrics.

Metrics Computed:
-----------------
1. Computational cost (CPU time, function evaluations)
2. Accuracy (compared to reference solution or Richardson extrapolation)
3. Stability (maximum stable step size)
4. Memory usage
5. Convergence behavior

References:
-----------
- Hairer, E., Nørsett, S.P., and Wanner, G. (1993). Solving Ordinary 
  Differential Equations I: Nonstiff Problems. Springer.
- Press, W.H., et al. (2007). Numerical Recipes: The Art of Scientific 
  Computing, 3rd ed. Cambridge University Press.
"""
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class SolverPerformance:
    """
    Container for solver performance metrics.
    
    Attributes:
    -----------
    solver_name : str
        Name of the numerical method
    cpu_time : float
        Total wall-clock time (seconds)
    num_function_evaluations : int
        Number of RHS function calls
    num_jacobian_evaluations : int
        Number of Jacobian evaluations (for implicit methods)
    max_error : float
        Maximum absolute error (if reference available)
    mean_error : float
        Mean absolute error
    rms_error : float
        Root-mean-square error
    num_steps : int
        Number of integration steps taken
    success : bool
        Whether integration completed successfully
    convergence_history : Optional[np.ndarray]
        Error vs. step size for convergence analysis
    """
    solver_name: str
    cpu_time: float
    num_function_evaluations: int
    num_jacobian_evaluations: int = 0
    max_error: float = np.nan
    mean_error: float = np.nan
    rms_error: float = np.nan
    num_steps: int = 0
    success: bool = True
    convergence_history: Optional[np.ndarray] = None
    memory_usage_mb: float = 0.0
    
    def efficiency_metric(self) -> float:
        """
        Calculate efficiency as accuracy per function evaluation.
        
        Returns:
        --------
        efficiency : float
            Inverse of (error * num_evaluations), higher is better
        """
        if np.isnan(self.rms_error) or self.rms_error == 0:
            return 0.0
        return 1.0 / (self.rms_error * self.num_function_evaluations)
    
    def __str__(self) -> str:
        """String representation with formatted metrics."""
        return (
            f"Solver: {self.solver_name}\n"
            f"  CPU Time: {self.cpu_time:.4f} s\n"
            f"  Function Evaluations: {self.num_function_evaluations}\n"
            f"  RMS Error: {self.rms_error:.2e}\n"
            f"  Max Error: {self.max_error:.2e}\n"
            f"  Efficiency: {self.efficiency_metric():.2e}\n"
            f"  Success: {self.success}"
        )


class SolverBenchmark:
    """
    Benchmark suite for comparing wave propagation solvers.
    
    Provides systematic comparison of different numerical methods
    on standard test problems with known solutions or high-accuracy
    reference results.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize benchmark suite.
        
        Parameters:
        -----------
        verbose : bool
            If True, print progress and results
        """
        self.verbose = verbose
        self.results: List[SolverPerformance] = []
        
    def run_single_solver(
        self,
        solver_function: Callable,
        solver_name: str,
        problem_params: Dict,
        reference_solution: Optional[np.ndarray] = None,
        reference_positions: Optional[np.ndarray] = None
    ) -> SolverPerformance:
        """
        Benchmark a single solver on a test problem.
        
        Parameters:
        -----------
        solver_function : Callable
            Function to solve ODE system, signature:
            solution = solver_function(**problem_params)
        solver_name : str
            Descriptive name for the solver
        problem_params : Dict
            Parameters to pass to solver_function
        reference_solution : np.ndarray, optional
            High-accuracy reference solution for error calculation
        reference_positions : np.ndarray, optional
            Spatial positions corresponding to reference solution
            
        Returns:
        --------
        performance : SolverPerformance
            Performance metrics for this solver
        """
        if self.verbose:
            print(f"\nBenchmarking {solver_name}...")
        
        # Time the solver
        start_time = time.time()
        
        try:
            # Run solver
            solution = solver_function(**problem_params)
            cpu_time = time.time() - start_time
            success = solution.get('success', True)
            
            # Extract results
            num_function_evals = solution.get('num_function_evals', 0)
            num_jacobian_evals = solution.get('num_jacobian_evals', 0)
            num_steps = len(solution.get('x', []))
            
            # Calculate errors if reference available
            max_error = np.nan
            mean_error = np.nan
            rms_error = np.nan
            
            if reference_solution is not None and reference_positions is not None:
                # Interpolate solution to reference positions
                solution_interp = np.interp(
                    reference_positions,
                    solution['x'],
                    solution['height_squared']
                )
                
                # Calculate error metrics
                errors = np.abs(solution_interp - reference_solution)
                max_error = np.max(errors)
                mean_error = np.mean(errors)
                rms_error = np.sqrt(np.mean(errors ** 2))
            
            # Create performance record
            performance = SolverPerformance(
                solver_name=solver_name,
                cpu_time=cpu_time,
                num_function_evaluations=num_function_evals,
                num_jacobian_evaluations=num_jacobian_evals,
                max_error=max_error,
                mean_error=mean_error,
                rms_error=rms_error,
                num_steps=num_steps,
                success=success
            )
            
        except Exception as e:
            if self.verbose:
                print(f"  ERROR: {str(e)}")
            
            performance = SolverPerformance(
                solver_name=solver_name,
                cpu_time=time.time() - start_time,
                num_function_evaluations=0,
                success=False
            )
        
        if self.verbose:
            print(performance)
        
        self.results.append(performance)
        return performance
    
    def compare_solvers(
        self,
        solver_configs: List[Tuple[Callable, str, Dict]],
        reference_solution: Optional[np.ndarray] = None,
        reference_positions: Optional[np.ndarray] = None
    ) -> List[SolverPerformance]:
        """
        Compare multiple solvers on the same problem.
        
        Parameters:
        -----------
        solver_configs : List[Tuple[Callable, str, Dict]]
            List of (solver_function, solver_name, problem_params) tuples
        reference_solution : np.ndarray, optional
            Reference solution for error calculation
        reference_positions : np.ndarray, optional
            Positions for reference solution
            
        Returns:
        --------
        results : List[SolverPerformance]
            Performance metrics for all solvers
        """
        self.results = []
        
        for solver_func, solver_name, params in solver_configs:
            self.run_single_solver(
                solver_func,
                solver_name,
                params,
                reference_solution,
                reference_positions
            )
        
        return self.results
    
    def generate_comparison_table(self) -> str:
        """
        Generate formatted comparison table.
        
        Returns:
        --------
        table : str
            Formatted table of results
        """
        if not self.results:
            return "No results available"
        
        # Header
        header = (
            f"{'Solver':<20} {'CPU Time (s)':<15} {'Func Evals':<12} "
            f"{'RMS Error':<12} {'Efficiency':<12} {'Success':<10}\n"
        )
        separator = "-" * 90 + "\n"
        
        # Rows
        rows = []
        for perf in self.results:
            row = (
                f"{perf.solver_name:<20} "
                f"{perf.cpu_time:<15.4f} "
                f"{perf.num_function_evaluations:<12d} "
                f"{perf.rms_error:<12.2e} "
                f"{perf.efficiency_metric():<12.2e} "
                f"{'Yes' if perf.success else 'No':<10}\n"
            )
            rows.append(row)
        
        return header + separator + "".join(rows)
    
    def plot_comparison(
        self,
        metrics: List[str] = ['cpu_time', 'num_function_evaluations', 'rms_error'],
        save_path: Optional[str] = None
    ):
        """
        Create visualization comparing solver performance.
        
        Parameters:
        -----------
        metrics : List[str]
            Metrics to plot (must be attributes of SolverPerformance)
        save_path : str, optional
            Path to save figure, if None displays interactively
        """
        if not self.results:
            print("No results to plot")
            return
        
        n_metrics = len(metrics)
        fig, axes = plt.subplots(1, n_metrics, figsize=(5*n_metrics, 4))
        
        if n_metrics == 1:
            axes = [axes]
        
        solver_names = [r.solver_name for r in self.results]
        x_pos = np.arange(len(solver_names))
        
        for ax, metric in zip(axes, metrics):
            values = [getattr(r, metric) for r in self.results]
            
            # Use log scale for large ranges
            if metric == 'num_function_evaluations' or max(values) / min(values) > 100:
                ax.set_yscale('log')
            
            bars = ax.bar(x_pos, values, alpha=0.7)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(solver_names, rotation=45, ha='right')
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.grid(axis='y', alpha=0.3)
            
            # Color code by success
            for bar, result in zip(bars, self.results):
                bar.set_color('green' if result.success else 'red')
                bar.set_alpha(0.7 if result.success else 0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            if self.verbose:
                print(f"Figure saved to {save_path}")
        else:
            plt.show()
    
    def find_best_solver(
        self,
        criterion: str = 'efficiency'
    ) -> Optional[SolverPerformance]:
        """
        Identify best solver based on specified criterion.
        
        Parameters:
        -----------
        criterion : str
            Selection criterion: 'efficiency', 'speed', 'accuracy'
            
        Returns:
        --------
        best : SolverPerformance
            Best performing solver
        """
        if not self.results:
            return None
        
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            return None
        
        if criterion == 'efficiency':
            return max(successful_results, key=lambda r: r.efficiency_metric())
        elif criterion == 'speed':
            return min(successful_results, key=lambda r: r.cpu_time)
        elif criterion == 'accuracy':
            return min(successful_results, key=lambda r: r.rms_error)
        else:
            raise ValueError(f"Unknown criterion: {criterion}")


def richardson_extrapolation(
    solver_function: Callable,
    problem_params: Dict,
    step_sizes: List[float],
    order: int = 4
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Use Richardson extrapolation to estimate high-accuracy reference solution.
    
    Richardson extrapolation combines solutions at multiple step sizes to
    eliminate leading error terms and achieve higher-order accuracy.
    
    For a method of order p, the Richardson extrapolation formula is:
    y_exact ≈ (2^p · y_h/2 - y_h) / (2^p - 1)
    
    Parameters:
    -----------
    solver_function : Callable
        Solver to use for reference solution
    problem_params : Dict
        Problem parameters
    step_sizes : List[float]
        Multiple step sizes (should include progressively smaller values)
    order : int
        Order of the numerical method (e.g., 4 for RK4)
        
    Returns:
    --------
    reference_solution : np.ndarray
        Extrapolated high-accuracy solution
    reference_positions : np.ndarray
        Corresponding spatial positions
        
    Notes:
    ------
    - Requires at least 2 step sizes
    - More step sizes give better extrapolation but cost more computation
    - Assumes error scales as h^p where p is method order
    
    References:
    -----------
    - Press, W.H., et al. (2007). Numerical Recipes, 3rd ed., Section 17.3.
    """
    if len(step_sizes) < 2:
        raise ValueError("Richardson extrapolation requires at least 2 step sizes")
    
    # Solve with different step sizes
    solutions = []
    for step in sorted(step_sizes):
        params = problem_params.copy()
        params['spatial_step'] = step
        solution = solver_function(**params)
        solutions.append(solution)
    
    # Use finest grid as reference positions
    reference_positions = solutions[-1]['x']
    
    # Richardson extrapolation using two finest solutions
    # y_exact ≈ (2^p · y_fine - y_coarse) / (2^p - 1)
    y_fine = solutions[-1]['height_squared']
    y_coarse = np.interp(reference_positions, solutions[-2]['x'], 
                         solutions[-2]['height_squared'])
    
    factor = 2 ** order
    reference_solution = (factor * y_fine - y_coarse) / (factor - 1)
    
    return reference_solution, reference_positions


def analyze_convergence_rate(
    solver_function: Callable,
    problem_params: Dict,
    step_sizes: np.ndarray,
    reference_solution: Optional[np.ndarray] = None
) -> Tuple[float, np.ndarray]:
    """
    Analyze convergence rate of a numerical method.
    
    Computes error as a function of step size to determine empirical
    convergence order. For a method of order p, error should scale as h^p.
    
    Parameters:
    -----------
    solver_function : Callable
        Solver to analyze
    problem_params : Dict
        Problem parameters
    step_sizes : np.ndarray
        Array of step sizes to test
    reference_solution : np.ndarray, optional
        High-accuracy reference (if None, uses finest grid)
        
    Returns:
    --------
    convergence_order : float
        Empirical convergence rate p (error ∝ h^p)
    errors : np.ndarray
        RMS errors for each step size
    """
    errors = []
    
    # Get reference solution if not provided
    if reference_solution is None:
        params = problem_params.copy()
        params['spatial_step'] = np.min(step_sizes) / 2
        ref_sol = solver_function(**params)
        reference_solution = ref_sol['height_squared']
        reference_positions = ref_sol['x']
    else:
        # Assume using finest grid for reference
        params = problem_params.copy()
        params['spatial_step'] = np.min(step_sizes)
        ref_sol = solver_function(**params)
        reference_positions = ref_sol['x']
    
    # Compute errors for each step size
    for step in step_sizes:
        params = problem_params.copy()
        params['spatial_step'] = step
        solution = solver_function(**params)
        
        # Interpolate to reference grid
        sol_interp = np.interp(reference_positions, solution['x'],
                              solution['height_squared'])
        
        # Calculate RMS error
        error = np.sqrt(np.mean((sol_interp - reference_solution) ** 2))
        errors.append(error)
    
    errors = np.array(errors)
    
    # Estimate convergence order using log-log fit
    # log(error) ≈ p * log(h) + const
    # So slope of log(error) vs log(h) gives order p
    valid_idx = errors > 0
    if np.sum(valid_idx) >= 2:
        log_h = np.log(step_sizes[valid_idx])
        log_err = np.log(errors[valid_idx])
        convergence_order = np.polyfit(log_h, log_err, 1)[0]
    else:
        convergence_order = np.nan
    
    return convergence_order, errors

