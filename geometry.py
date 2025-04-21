import numpy as np
import openmc
import math
from config import wall_thickness, source_to_wall_distance, detector_diameter

def calculate_solid_angle(source_to_wall_distance, channel_radius):
    """
    Calculate the solid angle from source to channel entrance
    
    Parameters:
        source_to_wall_distance (float): Distance from source to wall front, in cm
        channel_radius (float): Radius of the channel, in cm
        
    Returns:
        float: Solid angle in steradians
    """
    # Calculate the half-angle of the cone that encompasses the channel
    theta = math.atan(channel_radius / source_to_wall_distance)
    # Calculate solid angle using the formula for a cone
    return 2 * math.pi * (1 - math.cos(theta))


def create_geometry(channel_diameter, detector_distance, detector_angle, materials):
    """
    Create geometry with concrete wall, air channel, and phantom detector
    All particles must go through the channel without interaction with concrete
    
    Parameters:
        channel_diameter (float): Diameter of the channel in cm
        detector_distance (float): Distance from back of wall to detector center in cm
        detector_angle (float): Angle of detector from central axis in degrees
        materials (openmc.Materials): Materials for the simulation
        
    Returns:
        tuple: (geometry, detector_cell, detector_x, detector_y, cone_angle)
            geometry (openmc.Geometry): The OpenMC geometry
            detector_cell (openmc.Cell): The detector cell
            detector_x (float): X-coordinate of detector center
            detector_y (float): Y-coordinate of detector center
            cone_angle (float): Angle of cone that encompasses the channel
    """
    # Calculate channel radius
    channel_radius = channel_diameter / 2.0
    
    # Calculate the half-angle of the cone that encompasses the channel
    theta = math.atan(channel_radius / source_to_wall_distance)
    
    # Define surfaces
    # World boundaries
    xmin = openmc.XPlane(-200, boundary_type='vacuum')
    xmax = openmc.XPlane(source_to_wall_distance + wall_thickness + 300, boundary_type='vacuum')
    ymin = openmc.YPlane(-200, boundary_type='vacuum')
    ymax = openmc.YPlane(200, boundary_type='vacuum')
    zmin = openmc.ZPlane(-200, boundary_type='vacuum')
    zmax = openmc.ZPlane(200, boundary_type='vacuum')
    
    # Source is at the origin (0,0,0)
    
    # Wall surfaces
    wall_front = openmc.XPlane(source_to_wall_distance)
    wall_back = openmc.XPlane(source_to_wall_distance + wall_thickness)
    
    # Channel - cylindrical hole through the wall
    channel = openmc.ZCylinder(x0=0, y0=0, r=channel_radius)
    
    # Detector position based on distance and angle from the back of the wall
    detector_angle_rad = np.radians(detector_angle)
    detector_x = source_to_wall_distance + wall_thickness + detector_distance * np.cos(detector_angle_rad)
    detector_y = detector_distance * np.sin(detector_angle_rad)
    detector_sphere = openmc.Sphere(x0=detector_x, y0=detector_y, z0=0, r=detector_diameter/2)
    
    # Define cell regions
    world_region = +xmin & -xmax & +ymin & -ymax & +zmin & -zmax
    
    # Wall cell with channel cutout
    wall_region = +wall_front & -wall_back & ~-channel
    
    # Air channel through wall
    channel_region = -channel & +wall_front & -wall_back
    
    # Detector cell
    detector_region = -detector_sphere
    
    # Void region (everything else)
    void_region = world_region & ~(wall_region | channel_region | detector_region)
    
    # Create cells
    concrete = materials[0]
    air = materials[1]
    void = materials[2]
    tissue = materials[3]
    
    wall_cell = openmc.Cell(name='wall')
    wall_cell.fill = concrete
    wall_cell.region = wall_region
    
    channel_cell = openmc.Cell(name='channel')
    channel_cell.fill = air
    channel_cell.region = channel_region
    
    detector_cell = openmc.Cell(name='detector')
    detector_cell.fill = tissue
    detector_cell.region = detector_region
    
    void_cell = openmc.Cell(name='void')
    void_cell.fill = void
    void_cell.region = void_region
    
    # Create universe and geometry
    universe = openmc.Universe(cells=[wall_cell, channel_cell, detector_cell, void_cell])
    geometry = openmc.Geometry(universe)
    
    return geometry, detector_cell, detector_x, detector_y, theta 