#!/usr/bin/env python
"""
Main script to run gamma ray shielding simulations.
This script orchestrates the running of simulations and analysis.
"""

import os
import json
import openmc
import numpy as np
import matplotlib.pyplot as plt
import sys
import time
import traceback

# Import configuration
from config import (
    cross_sections_path, gamma_energies, channel_diameters, 
    detector_distances, detector_angles
)

# Import simulation modules
from materials import create_materials
from simulation import run_simulation
from visualization import plot_dose_vs_angle, create_polar_dose_heatmap, create_comprehensive_angle_plot
from spectrum_analysis import create_comprehensive_spectrum_plots, plot_spectrum_intensity_vs_distance
from report import generate_detailed_report

def main():
    """Run the gamma ray shielding simulations"""
    
    # Set the cross-sections path for OpenMC
    openmc.config['cross_sections'] = cross_sections_path
    
    # Set up plotting style
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 12
    
    # Create output directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Load existing results if available
    all_results = {}
    if os.path.exists('results/intermediate_results.json'):
        try:
            with open('results/intermediate_results.json', 'r') as f:
                all_results = json.load(f)
            print(f"Loaded {len(all_results)} existing results from previous runs.")
        except Exception as e:
            print(f"Error loading existing results: {e}")
    
    # Calculate total number of simulations
    total_simulations = len(gamma_energies) * len(channel_diameters) * len(detector_distances) * len(detector_angles)
    completed_simulations = 0
    failed_simulations = 0
    
    print(f"Preparing to run {total_simulations} simulations")
    print(f"Energy levels: {gamma_energies}")
    print(f"Channel diameters: {channel_diameters}")
    print(f"Detector distances: {detector_distances}")
    print(f"Detector angles: {detector_angles}")
    print("-" * 80)
    
    # Run simulations for all combinations
    start_time = time.time()
    for energy in gamma_energies:
        for channel_diameter in channel_diameters:
            for detector_distance in detector_distances:
                for detector_angle in detector_angles:
                    # Generate key for this configuration
                    key = f"E{energy}_D{channel_diameter}_dist{detector_distance}_ang{detector_angle}"
                    
                    # Skip if already completed
                    if key in all_results and 'dose_rem_per_hr' in all_results[key]:
                        print(f"Skipping {key} - already completed")
                        completed_simulations += 1
                        continue
                    
                    # Run the simulation with better error handling
                    try:
                        print(f"[{completed_simulations+1}/{total_simulations}] Running {key}")
                        result = run_simulation(energy, channel_diameter, detector_distance, detector_angle)
                        
                        # Store results in dictionary
                        all_results[key] = result
                        
                        # Save intermediate results after each simulation
                        with open('results/intermediate_results.json', 'w') as f:
                            json.dump(all_results, f, indent=2)
                        
                        # Format dose rate with scientific notation for very small values
                        dose = result['dose_rem_per_hr']
                        if dose < 0.000001:
                            dose_str = f"{dose:.6e}"
                        else:
                            dose_str = f"{dose:.6f}"
                        print(f"  Dose rate: {dose_str} rem/hr")
                        
                        completed_simulations += 1
                        
                    except KeyboardInterrupt:
                        print("\nUser interrupted simulation. Saving progress...")
                        with open('results/intermediate_results.json', 'w') as f:
                            json.dump(all_results, f, indent=2)
                        sys.exit(1)
                    except Exception as e:
                        print(f"  Error in simulation {key}: {str(e)}")
                        traceback.print_exc()
                        failed_simulations += 1
                        
                    # Calculate and display progress
                    elapsed_time = time.time() - start_time
                    progress = (completed_simulations + failed_simulations) / total_simulations
                    if progress > 0:
                        est_total_time = elapsed_time / progress
                        est_remaining = est_total_time - elapsed_time
                        print(f"  Progress: {progress:.1%} complete, Elapsed: {elapsed_time/60:.1f} min, "
                              f"Remaining: {est_remaining/60:.1f} min")
                    print("-" * 80)
    
    # Save final results
    with open('results/final_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nSimulations complete. {completed_simulations} successful, {failed_simulations} failed.")
    
    # Only proceed with analysis if we have at least some results
    if len(all_results) > 0:
        try:
            # Create dose vs angle plots
            print("\nCreating dose vs angle plots...")
            for energy in gamma_energies:
                plot_dose_vs_angle(all_results, energy)
            
            # Create comprehensive angle plots
            print("Creating comprehensive angle plots...")
            for energy in gamma_energies:
                try:
                    create_comprehensive_angle_plot(all_results, energy)
                except Exception as e:
                    print(f"Error creating comprehensive angle plot for {energy} MeV: {e}")
            
            # Create polar heatmap visualizations for each energy
            print("Creating polar heatmaps...")
            for energy in gamma_energies:
                try:
                    # Create combined visualization for all channel diameters
                    create_polar_dose_heatmap(all_results, energy)
                    
                    # Create individual visualizations for each channel diameter
                    for diameter in channel_diameters:
                        create_polar_dose_heatmap(all_results, energy, diameter)
                except Exception as e:
                    print(f"Error creating polar dose heatmap for {energy} MeV: {e}")
            
            # Create energy spectrum plots
            print("Creating energy spectrum plots...")
            try:
                create_comprehensive_spectrum_plots(all_results)
            except Exception as e:
                print(f"Error creating spectrum plots: {e}")
            
            # Create spectrum intensity vs distance plots for each configuration
            print("Creating spectrum intensity plots...")
            for energy in gamma_energies:
                for channel_diameter in channel_diameters:
                    for angle in [0, 15, 45]:
                        try:
                            if any(f"E{energy}_D{channel_diameter}_dist{d}_ang{angle}" in all_results for d in detector_distances):
                                plot_spectrum_intensity_vs_distance(all_results, energy, channel_diameter, angle)
                        except Exception as e:
                            print(f"Error creating spectrum intensity plot for E{energy} D{channel_diameter} A{angle}: {e}")
            
            # Generate the comprehensive PDF report
            print("Generating final report...")
            try:
                report_file = generate_detailed_report(all_results)
                print(f"Detailed report generated: {report_file}")
            except Exception as e:
                print(f"Error generating report: {e}")
        
        except Exception as e:
            print(f"Error during analysis phase: {e}")
            traceback.print_exc()
    
        # Find critical configurations (highest dose rates)
        critical_configs = []
        for key, result in all_results.items():
            if 'dose_rem_per_hr' in result:
                critical_configs.append((key, result['dose_rem_per_hr']))
        
        critical_configs.sort(key=lambda x: x[1], reverse=True)
        print("\nCritical configurations (highest dose rates):")
        for i in range(min(5, len(critical_configs))):
            key, dose = critical_configs[i]
            parts = key.split('_')
            energy = parts[0][1:]
            diameter = parts[1][1:]
            distance = parts[2][4:]
            angle = parts[3][3:]
            print(f"{i+1}. Energy: {energy} MeV, Channel Diameter: {diameter} cm, "
                f"Distance: {distance} cm, Angle: {angle}°, Dose: {dose:.6f} rem/hr")
    
    print("\nSimulation and analysis complete. Results saved to the 'results' directory.")
    elapsed_time = time.time() - start_time
    print(f"Total time elapsed: {elapsed_time/60:.1f} minutes")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc() 