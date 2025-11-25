#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tally data class for MCNP output processing
"""

from typing import List, Tuple, Optional
import math


class Tally:
    """
    Class representing a single MCNP tally with associated data and metadata.
    
    Attributes:
        tally_num (int): Tally number from MCNP output
        tally_type (int): Type of tally (e.g., 1, 2, 4, 5, 6, 8)
        particle (str): Particle type (e.g., 'neutron', 'photon')
        energy (List[float]): Energy bins (MeV)
        flux (List[float]): Flux values
        error (List[float]): Relative error values
        cutoff_energy (float): Energy cutoff value (MeV)
        flux_normalized (List[float]): Flux normalized per MeV
        comment (str): Comment from MCNP input file
        legend_name (str): Name to use in plot legends
        checks_passed (str): Statistical checks passed (e.g., '8/10' or 'N/A')
        relative_error (str): Relative error from statistical check (e.g., '0.00' or 'N/A')
        variance_of_variance (str): Variance of the variance (e.g., '0.00' or 'N/A')
        figure_of_merit (str): Figure of merit (e.g., '3.356E+00' or 'N/A')
        slope (str): PDF slope from statistical check (e.g., '10.00' or 'N/A')
    """
    
    def __init__(self, 
                 tally_num: int,
                 tally_type: int,
                 particle: str,
                 energy: List[float],
                 flux: List[float],
                 error: List[float],
                 cutoff_energy: float,
                 flux_normalized: List[float],
                 comment: str = "---",
                 legend_name: Optional[str] = None,
                 checks_passed: str = "N/A",
                 relative_error: str = "N/A",
                 variance_of_variance: str = "N/A",
                 figure_of_merit: str = "N/A",
                 slope: str = "N/A"):
        """
        Initialize a Tally object.
        
        Args:
            tally_num: Tally number from MCNP output
            tally_type: Type of tally
            particle: Particle type
            energy: Energy bins (MeV)
            flux: Flux values
            error: Relative error values
            cutoff_energy: Energy cutoff value (MeV)
            flux_normalized: Flux normalized per MeV
            comment: Comment from MCNP input file
            legend_name: Name to use in plot legends (defaults to tally_num if None)
            checks_passed: Statistical checks passed (e.g., '8/10')
            relative_error: Relative error from statistical check
            variance_of_variance: Variance of the variance
            figure_of_merit: Figure of merit
            slope: PDF slope from statistical check
        """
        self.tally_num = tally_num
        self.tally_type = tally_type
        self.particle = particle
        self.energy = energy
        self.flux = flux
        self.error = error
        self.cutoff_energy = cutoff_energy
        self.flux_normalized = flux_normalized
        self.comment = comment
        self.legend_name = legend_name if legend_name is not None else str(tally_num)
        self.checks_passed = checks_passed
        self.relative_error = relative_error
        self.variance_of_variance = variance_of_variance
        self.figure_of_merit = figure_of_merit
        self.slope = slope
    
    @property
    def num_bins(self) -> int:
        """Get number of energy bins (excluding first cutoff bin)."""
        return len(self.energy) - 1
    
    @property
    def energy_min(self) -> float:
        """Get minimum energy value (first non-cutoff bin)."""
        return self.energy[1] if len(self.energy) > 1 else 0.0
    
    @property
    def energy_max(self) -> float:
        """Get maximum energy value."""
        return self.energy[-1] if self.energy else 0.0
    
    def get_data(self, 
                 normalized: bool = True, 
                 include_first_bin: bool = True) -> Tuple[List[float], List[float], List[float]]:
        """
        Get energy, flux, and error data with specified options.
        
        Args:
            normalized: If True, return normalized flux (per MeV), otherwise original flux
            include_first_bin: If True, include the first (cutoff) bin, otherwise skip it
        
        Returns:
            Tuple of (energy, flux, error) lists
        """
        if normalized:
            flux_data = self.flux_normalized[:]
        else:
            flux_data = self.flux[:]
        
        if include_first_bin:
            return self.energy[:], flux_data, self.error[:]
        else:
            return self.energy[1:], flux_data[1:], self.error[1:]
    
    def calculate_interval_centers(self, include_first_bin: bool = True) -> List[float]:
        """
        Calculate the center points of energy intervals.
        
        Args:
            include_first_bin: If True, include the first (cutoff) bin, otherwise skip it
        
        Returns:
            List of interval center points
        """
        energy_data = self.energy if include_first_bin else self.energy[1:]
        centers = []
        for i in range(len(energy_data) - 1):
            centers.append((energy_data[i] + energy_data[i + 1]) / 2)
        return centers
    
    def apply_multiplier(self, 
                        multiplier: float, 
                        normalized: bool = True, 
                        include_first_bin: bool = True) -> Tuple[List[float], List[float], List[float]]:
        """
        Get data with a multiplier applied to flux values.
        
        Args:
            multiplier: Factor to multiply flux values by
            normalized: If True, use normalized flux, otherwise original flux
            include_first_bin: If True, include the first (cutoff) bin, otherwise skip it
        
        Returns:
            Tuple of (energy, flux*multiplier, error) lists
        """
        energy, flux, error = self.get_data(normalized, include_first_bin)
        flux_multiplied = [f * multiplier for f in flux]
        return energy, flux_multiplied, error
    
    def calculate_ratio(self, 
                       reference_tally: 'Tally', 
                       normalized: bool = True,
                       include_first_bin: bool = True) -> Tuple[List[float], List[float], List[float], bool]:
        """
        Calculate ratio of this tally to a reference tally.
        
        Args:
            reference_tally: Tally to use as denominator
            normalized: If True, use normalized flux, otherwise original flux
            include_first_bin: If True, include the first (cutoff) bin, otherwise skip it
        
        Returns:
            Tuple of (energy, ratio, error, success_flag)
            success_flag is False if energy bins don't match
        """
        energy_this, flux_this, error_this = self.get_data(normalized, include_first_bin)
        energy_ref, flux_ref, error_ref = reference_tally.get_data(normalized, include_first_bin)
        
        # Check if energy bins match
        if energy_this != energy_ref:
            return energy_this, [], [], False
        
        ratio_flux = []
        ratio_error = []
        
        for i in range(len(flux_this)):
            if flux_this[i] != 0 and flux_ref[i] != 0:
                # Calculate ratio
                ratio_flux.append(flux_this[i] / flux_ref[i])
                # Propagate error
                ratio_error.append(math.sqrt(error_this[i]**2 + error_ref[i]**2))
            else:
                ratio_flux.append(0)
                ratio_error.append(0)
        
        return energy_this, ratio_flux, ratio_error, True
    
    def to_legacy_list(self) -> List:
        """
        Convert Tally object back to legacy list format for backward compatibility.
        
        Returns:
            List in the old format [tally_num, tally_type, particle, energy, flux, 
                                   error, cutoff_energy, flux_normalized, comment, None, legend_name]
        """
        return [
            self.tally_num,
            self.tally_type,
            self.particle,
            self.energy,
            self.flux,
            self.error,
            self.cutoff_energy,
            self.flux_normalized,
            self.comment,
            None,  # unused field
            self.legend_name
        ]
    
    @classmethod
    def from_legacy_list(cls, data: List) -> 'Tally':
        """
        Create a Tally object from legacy list format.
        
        Args:
            data: List in old format [tally_num, tally_type, particle, energy, flux,
                                     error, cutoff_energy, flux_normalized, comment, None, legend_name]
        
        Returns:
            Tally object
        """
        return cls(
            tally_num=data[0],
            tally_type=data[1],
            particle=data[2],
            energy=data[3],
            flux=data[4],
            error=data[5],
            cutoff_energy=data[6],
            flux_normalized=data[7],
            comment=data[8] if len(data) > 8 else "---",
            legend_name=data[10] if len(data) > 10 and data[10] is not None else None
        )
    
    def __repr__(self) -> str:
        """String representation of the Tally object."""
        return (f"Tally(num={self.tally_num}, type={self.tally_type}, "
                f"particle='{self.particle}', bins={self.num_bins}, "
                f"E_range=[{self.energy_min:.2e}, {self.energy_max:.2e}] MeV)")
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return (f"Tally {self.tally_num} ({self.particle}): "
                f"{self.num_bins} bins, "
                f"E ∈ [{self.energy_min:.2e}, {self.energy_max:.2e}] MeV")
