import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
import pandas as pd
from scipy.stats import multivariate_normal, weibull_min, lognorm, expon, uniform, gamma, norm

@dataclass
class SimulationConfig:
    """Configuration for data simulation."""
    n_samples: int = 200
    n_features: int = 15
    censoring_rate: float = 0.4
    random_state: Optional[int] = None

class DataGenerator:
    """Class for generating simulated survival data."""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.rng = np.random.RandomState(self.config.random_state)
        self.supported_types = ['weibull', 'lognormal', 'SDGM1', 'SDGM2', 'SDGM3', 'SDGM4']
    
    def _generate_cov_matrix(self, p: int, rho: float = 0.6) -> np.ndarray:
        """Generate covariance matrix with AR(1) structure."""
        cov = np.zeros((p, p))
        for i in range(p):
            for j in range(p):
                cov[i, j] = rho ** abs(i - j)
        return cov
    
    def _generate_aft_data(self, sim_type: str) -> pd.DataFrame:
        """Generate AFT model data (weibull or lognormal)."""
        n = self.config.n_samples
        p = self.config.n_features
        
        # Generate covariates
        cov = self._generate_cov_matrix(p)
        X = self.rng.multivariate_normal(np.zeros(p), cov, size=n)
        
        # Generate survival times
        if sim_type == 'weibull':
            # Weibull AFT model
            beta = np.zeros(p)
            beta[p//2:] = 0.1  # Only second half of features are relevant
            log_time = np.dot(X, beta) + self.rng.normal(0, 1, n)
            time = np.exp(log_time)
        else:  # lognormal
            # Lognormal AFT model
            beta = np.zeros(p)
            beta[:p//5] = 0.1  # First 20% of features are relevant
            beta[-p//5:] = 0.1  # Last 20% of features are relevant
            log_time = np.dot(X, beta) + self.rng.normal(0, 1, n)
            time = np.exp(log_time)
        
        # Generate censoring times
        c_time = self.rng.exponential(1/self.config.censoring_rate, n)
        
        # Determine status and observed time
        status = (time < c_time).astype(int)
        observed_time = np.minimum(time, c_time)
        
        # Create DataFrame
        data = pd.DataFrame(X, columns=[f'x{i+1}' for i in range(p)])
        data['time'] = observed_time
        data['status'] = status
        
        return data
    
    def _generate_sdgm1(self) -> pd.DataFrame:
        """Generate SDGM1 data (proportional hazards model)."""
        n = self.config.n_samples
        p = self.config.n_features
        
        # Generate covariates with AR(1) covariance
        cov = self._generate_cov_matrix(p)
        X = self.rng.multivariate_normal(np.zeros(p), cov, size=n)
        
        # Generate survival times
        time = np.zeros(n)
        for i in range(n):
            t_mu = np.exp(0.1 * np.sum(X[i, p//2:]))
            time[i] = self.rng.exponential(t_mu)
        
        # Generate censoring times
        c_time = self.rng.exponential(1/self.config.censoring_rate, n)
        
        # Determine status and observed time
        status = (time < c_time).astype(int)
        observed_time = np.minimum(time, c_time)
        
        # Create DataFrame
        data = pd.DataFrame(X, columns=[f'x{i+1}' for i in range(p)])
        data['time'] = observed_time
        data['status'] = status
        
        return data
    
    def _generate_sdgm2(self) -> pd.DataFrame:
        """Generate SDGM2 data (mild violations of proportional hazards)."""
        n = self.config.n_samples
        p = self.config.n_features
        
        # Generate covariates from uniform distribution
        X = self.rng.uniform(0, 1, size=(n, p))
        
        # Generate survival times
        time = np.zeros(n)
        for i in range(n):
            t_mu = np.sin(X[i, 0] * np.pi) + 2 * np.abs(X[i, 1] - 0.5) + X[i, 2]**3
            time[i] = self.rng.exponential(t_mu)
        
        # Generate censoring times
        c_time = self.rng.uniform(0, 4, n)  # u_max = 4
        
        # Determine status and observed time
        status = (time < c_time).astype(int)
        observed_time = np.minimum(time, c_time)
        
        # Create DataFrame
        data = pd.DataFrame(X, columns=[f'x{i+1}' for i in range(p)])
        data['time'] = observed_time
        data['status'] = status
        
        return data
    
    def _generate_sdgm3(self) -> pd.DataFrame:
        """Generate SDGM3 data (strong violations of proportional hazards)."""
        n = self.config.n_samples
        p = self.config.n_features
        
        # Generate covariates with AR(1) covariance
        cov = self._generate_cov_matrix(p, rho=0.75)
        X = self.rng.multivariate_normal(np.zeros(p), cov, size=n)
        
        # Generate survival times
        time = np.zeros(n)
        q = np.floor(np.quantile(np.arange(p), [2/5, 3/5])).astype(int)
        for i in range(n):
            shape = 0.5 + 0.25 * np.abs(np.sum(X[i, q[0]:q[1]]))
            scale = 2
            time[i] = self.rng.gamma(shape, scale)
        
        # Generate censoring times
        c_time = self.rng.uniform(0, 7, n)  # u_max = 7
        
        # Determine status and observed time
        status = (time < c_time).astype(int)
        observed_time = np.minimum(time, c_time)
        
        # Create DataFrame
        data = pd.DataFrame(X, columns=[f'x{i+1}' for i in range(p)])
        data['time'] = observed_time
        data['status'] = status
        
        return data
    
    def _generate_sdgm4(self) -> pd.DataFrame:
        """Generate SDGM4 data (proportional hazards with log-normal errors)."""
        n = self.config.n_samples
        p = self.config.n_features
        
        # Generate covariates with AR(1) covariance
        cov = self._generate_cov_matrix(p, rho=0.75)
        X = self.rng.multivariate_normal(np.zeros(p), cov, size=n)
        
        # Generate survival times
        time = np.zeros(n)
        c_time = np.zeros(n)
        for i in range(n):
            t_mu = 0.1 * np.abs(np.sum(X[i, :p//5])) + 0.1 * np.abs(np.sum(X[i, -p//5:]))
            log_time = self.rng.normal(t_mu, 1)
            time[i] = np.exp(log_time)
            
            # Generate censoring times with dependency on covariates
            c_mu = t_mu + self.config.censoring_rate
            log_c_time = self.rng.normal(c_mu, 1)
            c_time[i] = np.exp(log_c_time)
        
        # Determine status and observed time
        status = (time < c_time).astype(int)
        observed_time = np.minimum(time, c_time)
        
        # Create DataFrame
        data = pd.DataFrame(X, columns=[f'x{i+1}' for i in range(p)])
        data['time'] = observed_time
        data['status'] = status
        
        return data
    
    def generate(self, sim_type: str) -> pd.DataFrame:
        """Generate simulated survival data.
        
        Args:
            sim_type: Type of simulation to generate. One of:
                - 'weibull': Weibull AFT model
                - 'lognormal': Lognormal AFT model
                - 'SDGM1': SDGM1 (proportional hazards)
                - 'SDGM2': SDGM2 (mild violations of PH)
                - 'SDGM3': SDGM3 (strong violations of PH)
                - 'SDGM4': SDGM4 (proportional hazards with log-normal errors)
        
        Returns:
            DataFrame containing the simulated data with columns:
                - x1, x2, ..., xp: Features
                - time: Observed time
                - status: Event indicator (1 = event, 0 = censored)
        """
        if sim_type in ['weibull', 'lognormal']:
            return self._generate_aft_data(sim_type)
        elif sim_type == 'SDGM1':
            return self._generate_sdgm1()
        elif sim_type == 'SDGM2':
            return self._generate_sdgm2()
        elif sim_type == 'SDGM3':
            return self._generate_sdgm3()
        elif sim_type == 'SDGM4':
            return self._generate_sdgm4()
        else:
            raise ValueError(f"Unknown simulation type: {sim_type}") 