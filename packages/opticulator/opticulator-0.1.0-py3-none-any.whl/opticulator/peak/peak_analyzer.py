
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

@dataclass
class Peak:
    x: float                 # peak position (bin center, in data units)
    index: int               # peak index in the counts array
    height: float            # smoothed histogram height at the peak
    count: float             # raw histogram count at the peak bin
    prominence: float        # estimated prominence (same units as counts)
    left_base: float         # x-position of left base (approx)
    right_base: float        # x-position of right base (approx)

def _gaussian_kernel1d(sigma: float, radius: Optional[int] = None) -> np.ndarray:
    if sigma <= 0:
        return np.array([1.0], dtype=float)
    if radius is None:
        radius = int(max(1, round(3 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=float)
    k = np.exp(-0.5 * (x / sigma) **2)
    k /= k.sum()
    return k

def _smooth(y: np.ndarray, sigma: float) -> np.ndarray:
    k = _gaussian_kernel1d(sigma)
    if k.size == 1:
        return y.astype(float, copy=True)
    return np.convolve(y.astype(float), k, mode="same")

def _local_maxima(y: np.ndarray) -> np.ndarray:
    y = y.astype(float)
    left = y[1:-1] > y[:-2]
    right = y[1:-1] >= y[2:]
    peaks = np.nonzero(left & right)[0] + 1
    return peaks

def _estimate_prominence(y: np.ndarray, peak_idx: int) -> Tuple[float, int, int]:
    # Approximate prominence for peak at peak_idx by walking to nearest basins.
    n = y.size
    yp = y[peak_idx]

    # Walk left
    i = peak_idx
    left_min = yp
    left_i = peak_idx
    while i > 0 and (y[i-1] <= y[i] or y[i-1] < yp):
        i -= 1
        if y[i] < left_min:
            left_min = y[i]
            left_i = i
        if y[i] > yp:
            break

    # Walk right
    j = peak_idx
    right_min = yp
    right_j = peak_idx
    while j < n - 1 and (y[j+1] <= y[j] or y[j+1] < yp):
        j += 1
        if y[j] < right_min:
            right_min = y[j]
            right_j = j
        if y[j] > yp:
            break

    base_level = max(left_min, right_min)
    prominence = max(0.0, yp - base_level)
    return float(prominence), int(left_i), int(right_j)

def _suppress_close(peaks: np.ndarray, y: np.ndarray, min_distance: int) -> np.ndarray:
    if min_distance <= 0 or peaks.size == 0:
        return peaks
    order = np.argsort(y[peaks])[::-1]
    selected = []
    taken = np.zeros(y.size, dtype=bool)
    for p in peaks[order]:
        lo = max(0, p - min_distance)
        hi = min(y.size, p + min_distance + 1)
        if taken[lo:hi].any():
            continue
        selected.append(p)
        taken[lo:hi] = True
    return np.array(sorted(selected))

def histogram_peaks(
    values,
    bins: int = 128,
    value_range: Optional[Tuple[float, float]] = None,
    weights: Optional[np.ndarray] = None,
    smooth_sigma: float = 1.0,
    min_prominence: float = 0.0,
    min_distance_bins: int = 3,
    max_peaks: Optional[int] = None,
    density: bool = False,
) -> Tuple[List[Peak], np.ndarray, np.ndarray]:
    # Detect peaks in a value distribution via a histogram.
    vals = np.asarray(values, dtype=float).ravel()
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return [], np.array([]), np.array([0.0, 1.0])

    if value_range is None:
        vmin, vmax = float(np.min(vals)), float(np.max(vals))
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
            return [], np.array([]), np.array([0.0, 1.0])
    else:
        vmin, vmax = value_range

    counts, edges = np.histogram(vals, bins=bins, range=(vmin, vmax), weights=weights, density=density)
    if counts.size == 0 or np.all(counts == 0):
        return [], counts, edges

    y = _smooth(counts, smooth_sigma)
    cand = _local_maxima(y)
    cand = _suppress_close(cand, y, min_distance_bins)

    peaks: List[Peak] = []
    centers = 0.5 * (edges[:-1] + edges[1:])
    for idx in cand:
        prom, li, rj = _estimate_prominence(y, idx)
        if prom >= min_prominence:
            p = Peak(
                x=float(centers[idx]),
                index=int(idx),
                height=float(y[idx]),
                count=float(counts[idx]),
                prominence=float(prom),
                left_base=float(centers[max(li, 0)]),
                right_base=float(centers[min(rj, centers.size - 1)]),
            )
            peaks.append(p)

    if max_peaks is not None and len(peaks) > max_peaks:
        peaks = sorted(peaks, key=lambda p: p.height, reverse=True)[:max_peaks]
        peaks = sorted(peaks, key=lambda p: p.x)

    return peaks, y, edges

def peak_positions(values, **kwargs) -> np.ndarray:
    peaks, _, _ = histogram_peaks(values, **kwargs)
    return np.array([p.x for p in peaks], dtype=float)

def highest_peak_value(values, **kwargs):
    peaks, _, _ = histogram_peaks(values, **kwargs)
    return max(peaks, key=lambda p: p.height).x if peaks else float("nan")