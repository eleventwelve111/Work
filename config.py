import os
import numpy as np

# Avoid file locking issues with HDF5
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

# Set OpenMC cross section path
# This path should be updated to your local cross section data location
cross_sections_path = '/Users/fantadiaby/Desktop/endfb-vii.1-hdf5/cross_sections.xml'

# Create output directory if it doesn't exist
os.makedirs('results', exist_ok=True)

# Define parameters (all dimensions in cm)
ft_to_cm = 30.48  # 1 foot = 30.48 cm
wall_thickness = 2 * ft_to_cm            # 2 ft in cm
source_to_wall_distance = 6 * ft_to_cm    # 6 ft in cm
detector_diameter = 30.0                 # ICRU phantom sphere diameter in cm

# Channel diameters (in cm)
channel_diameters = [0.05, 0.1, 0.5, 1.0]  # from 0.5 mm to 1 cm

# Gamma-ray energies (in MeV)
gamma_energies = [0.1, 0.5, 1.0, 2.0, 5.0]  # from 100 keV to 5 MeV

# Detector positions (distance from back of wall in cm)
detector_distances = [30, 40, 60, 80, 100, 150]

# Detector angles (in degrees)
detector_angles = [0, 5, 10, 15, 30, 45]

# Test mode parameters (for faster testing)
test_mode = True
if test_mode:
    gamma_energies = [0.1, 1.0, 5.0]         # Test with 100 keV, 1 MeV, 5 MeV
    channel_diameters = [0.05, 0.5]          # Test with 0.5 mm and 5 mm
    detector_distances = [30, 100]           # Test with 30 cm and 100 cm
    detector_angles = [0, 15, 45]            # Test with 0°, 15°, 45° 