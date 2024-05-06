import numpy as np
from scipy.fft import fft, ifft
import dataclasses
from typing import Union
import pandas as pd


@dataclasses.dataclass
class HSTransform:
    """
    A class used to represent the S-transform with a hyperbolic Gaussian window.

    ...

    Attributes
    ----------
    L : int
        length of the signal
    forwardtaper : float
        forward taper value
    backwardtaper : float
        backward taper value
    curvature : float
        curvature value
    """

    forwardtaper: float = 0.2
    backwardtaper: float = 0.1
    curvature: float = 312.5

    def _input_validation(self, input_signal):
        """
        Validates the input signal.

        Parameters
        ----------
            input_signal : np.ndarray, pd.Series, or list

        Raises
        ------
            TypeError: If input_signal is not a numpy array, pandas Series, or list.
            ValueError: If input_signal contains non-numerical values.
        """
        valid_types = (np.ndarray, pd.Series, list)
        if not isinstance(input_signal, valid_types):
            raise TypeError(f"input_signal must be one of the following types: {valid_types}, not {type(input_signal)}.")

        input_array = np.array(input_signal)
        if np.isnan(input_array).any():
            raise ValueError("input_signal contains null values.")

        if not np.issubdtype(input_array.dtype, np.number):
            raise ValueError("input_signal should only contain numerical values.")

    def _compute_hyperbolic_gaussian(self, L: int, n: int, time: np.ndarray) -> np.ndarray:
        """
        Computes the hyperbolic Gaussian window.

        Parameters
        ----------
            L : int
                length of the signal
            n : int
                frequency point
            time : np.ndarray
                time values of the signal

        Returns
        -------
            G : np.ndarray
                hyperbolic Gaussian window
        """
        vectorf = np.arange(0, L)
        vectorf1 = vectorf**2
        lambdaf = self.forwardtaper
        lambdab = self.backwardtaper
        lambda_val = self.curvature
        X = (lambdaf + lambdab) * time / (2 * lambdaf * lambdab) + (lambdaf - lambdab) * np.sqrt(time**2 + lambda_val) / (2 * lambdaf * lambdab)
        X = np.tile(X, (1, 2)).T
        vectorf2 = -vectorf1 * X**2 / (2 * n**2)
        G = 2 * np.abs(vectorf) * np.exp(vectorf2) / ((lambdaf + lambdab) * np.sqrt(2 * np.pi))
        return np.sum(G)

    def fit_transform(self,
                      time_values: Union[pd.Series, np.ndarray, list],
                      input_signal: Union[pd.Series, np.ndarray, list],
                      minf: int = 0,
                      fsamplingrate: int = 1) -> np.ndarray:
        """
        Computes the S-transform of the input signal.

        Parameters
        ----------
            time_values : np.ndarray
                time values of the signal
            input_signal : np.ndarray
                input signal
            minf : int
                minimum frequency point
            fsamplingrate : int
                frequency sampling rate

        Returns
        -------
            S : np.ndarray
                S-transform of the input signal
        """
        # Validate the input
        self._input_validation(input_signal)

        # Convert to numpy arrays if they are not array types
        if not isinstance(time_values, np.ndarray):
            time_values = np.array(time_values)
        if not isinstance(input_signal, np.ndarray):
            input_signal = np.array(input_signal)

        N = len(input_signal)
        # Make sure the max frequency to be optimized (Cover the 6th, 12th, or 18th harmonic respectively)
        maxf = min(900, N // 2)

        # Compute the fft of input
        H = fft(input_signal)
        H = np.concatenate((H, H))

        # S output
        S = np.zeros(((maxf - minf + 1) // fsamplingrate, N), dtype='complex')
        S[0, :] = np.mean(input_signal) * (1 & np.arange(1, N + 1))

        k_values = np.arange(fsamplingrate, maxf - minf + 1, fsamplingrate)

        # Increment the frequency point
        for k in range(fsamplingrate, maxf - minf + 1, fsamplingrate):
            W_hy = self._compute_hyperbolic_gaussian(N, minf + k, time_values)
            S[k // fsamplingrate, :] = ifft(H[minf + k + 1:minf + k + N+1] * W_hy)

        return S