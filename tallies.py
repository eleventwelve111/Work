import numpy as np
import openmc
from config import source_to_wall_distance, wall_thickness

def create_tallies(detector_cell):
    """
    Create tallies for the simulation
    
    Parameters:
        detector_cell (openmc.Cell): The detector cell
        
    Returns:
        tuple: (tallies, mesh)
            tallies (openmc.Tallies): Collection of tallies
            mesh (openmc.RegularMesh): Mesh for 2D visualization
    """
    tallies = openmc.Tallies()
    
    # Energy filter with a fine energy grid for spectrum analysis
    energy_filter = openmc.EnergyFilter(np.logspace(-2, 1, 100))  # 10 keV to 10 MeV
    
    # Cell filter for detector
    cell_filter = openmc.CellFilter(detector_cell)
    
    # Particle filter for photons
    particle_filter = openmc.ParticleFilter('photon')
    
    # Cell tally for detector
    detector_tally = openmc.Tally(name='detector_tally')
    detector_tally.filters = [cell_filter, energy_filter, particle_filter]
    detector_tally.scores = ['flux']
    tallies.append(detector_tally)
    
    # Mesh for 2D visualization
    mesh = openmc.RegularMesh()
    mesh.dimension = [100, 100, 1]
    mesh.lower_left = [-10, -50, -1]
    mesh.upper_right = [source_to_wall_distance + wall_thickness + 200, 50, 1]
    
    # Mesh filter
    mesh_filter = openmc.MeshFilter(mesh)
    
    # Mesh tally for 2D flux distribution
    mesh_tally = openmc.Tally(name='mesh_tally')
    mesh_tally.filters = [mesh_filter, particle_filter]
    mesh_tally.scores = ['flux']
    tallies.append(mesh_tally)
    
    return tallies, mesh 