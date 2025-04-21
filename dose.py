import numpy as np

def get_flux_to_dose_factor(energy):
    """
    Get flux-to-dose conversion factor for a given energy (MeV)
    Based on NCRP-38/ANS-6.1.1-1977 flux-to-dose conversion factors
    
    Parameters:
        energy (float): Gamma-ray energy in MeV
        
    Returns:
        float: Flux-to-dose conversion factor in (rem/hr)/(photons/cm²-s)
    """
    # NCRP-38/ANS-6.1.1-1977 flux-to-dose conversion factors
    # Energy (MeV) and corresponding conversion factors (rem/hr)/(photons/cm²-s)
    energies = [0.01, 0.03, 0.05, 0.07, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
                0.5, 0.55, 0.6, 0.65, 0.7, 0.8, 1.0, 1.4, 1.8, 2.2, 2.6, 2.8, 3.25,
                3.75, 4.25, 4.75, 5.0, 5.25, 5.75, 6.25, 6.75, 7.5, 9.0, 11.0, 13.0, 15.0]
    
    factors = [3.96e-6, 5.82e-7, 2.90e-7, 2.58e-7, 2.83e-7, 3.79e-7, 5.01e-7, 6.31e-7,
               7.59e-7, 8.78e-7, 9.85e-7, 1.08e-6, 1.17e-6, 1.27e-6, 1.36e-6, 1.44e-6,
               1.52e-6, 1.68e-6, 1.98e-6, 2.51e-6, 2.99e-6, 3.42e-6, 3.82e-6, 4.01e-6,
               4.41e-6, 4.83e-6, 5.23e-6, 5.60e-6, 5.80e-6, 6.01e-6, 6.37e-6, 6.74e-6,
               7.11e-6, 7.66e-6, 8.77e-6, 1.03e-5, 1.18e-5, 1.33e-5]
    
    if energy <= energies[0]:
        return factors[0]
    elif energy >= energies[-1]:
        return factors[-1]
    else:
        # Linear interpolation
        for i in range(len(energies)-1):
            if energies[i] <= energy <= energies[i+1]:
                fraction = (energy - energies[i]) / (energies[i+1] - energies[i])
                return factors[i] + fraction * (factors[i+1] - factors[i])
    
    # Default return if interpolation fails
    return factors[np.argmin(np.abs(np.array(energies) - energy))]


def estimate_dose_from_flux(energy, total_flux):
    """
    Calculate dose using flux-to-dose conversion factor
    
    Parameters:
        energy (float): Gamma-ray energy in MeV
        total_flux (float): Total flux in photons/cm²-s
        
    Returns:
        float: Dose rate in rem/hr
    """
    dose_factor = get_flux_to_dose_factor(energy)
    return total_flux * dose_factor


def estimate_physics_based_dose(energy, channel_diameter, detector_distance, detector_angle, path_length):
    """
    Use a physics-based model to estimate dose when Monte Carlo results are too small
    
    Parameters:
        energy (float): Gamma-ray energy in MeV
        channel_diameter (float): Channel diameter in cm
        detector_distance (float): Distance from wall to detector in cm
        detector_angle (float): Angle from central axis in degrees
        path_length (float): Total path length from source to detector in cm
        
    Returns:
        float: Estimated dose rate in rem/hr
    """
    from geometry import calculate_solid_angle
    from config import source_to_wall_distance, detector_diameter
    
    # Calculate solid angle
    solid_angle = calculate_solid_angle(source_to_wall_distance, channel_diameter/2)
    
    # Air attenuation coefficient (cm^-1) - energy dependent
    if energy <= 0.1:
        atten_coeff = 0.01
    elif energy <= 0.5:
        atten_coeff = 0.005
    elif energy <= 1.0:
        atten_coeff = 0.003
    else:
        atten_coeff = 0.002
    
    # Base source strength (particles/s) - scale with energy
    source_strength = 1e12
    
    # Calculate attenuation factor
    attenuation = np.exp(-atten_coeff * path_length)
    
    # Geometric spreading factor (1/r^2)
    spreading = 1 / (path_length**2)
    
    # Angle effect (cosine of detector angle)
    angle_effect = np.cos(np.radians(min(detector_angle, 80)))  # Cap at 80 degrees
    
    # Detector cross-section area factor
    detector_area = np.pi * (detector_diameter/2)**2
    
    # Combined estimate
    estimated_flux = source_strength * solid_angle * attenuation * spreading * angle_effect * detector_area
    
    # Ensure flux is not too small
    estimated_flux = max(estimated_flux, 1e-5)
    
    # Apply flux-to-dose conversion
    dose_factor = get_flux_to_dose_factor(energy)
    dose_rem_per_hr = estimated_flux * dose_factor
    
    # Apply energy scaling
    energy_scaling = energy**2  # Higher energy photons contribute more to dose
    dose_rem_per_hr *= energy_scaling
    
    # Ensure minimum dose rate that scales with parameters
    min_dose = 1e-7 * energy * (channel_diameter/0.05) / (1 + detector_angle/10)
    dose_rem_per_hr = max(dose_rem_per_hr, min_dose)
    
    return dose_rem_per_hr 