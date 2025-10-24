"""
speed.py

This module generates polar plots representing track speed vectors from TrackMate data.
"""

import matplotlib.pyplot as plt
import os 
import pandas as pd
import numpy as np
import statistics
from matplotlib import cm
from .utils import circular_variance_from_angles, mean_angle, percent_densest_90, check_conversion_value
from .constants import ALL_TRACK_COLUMNS, ALL_SPOTS_COLUMNS, Track_columns_for_conversion, Spots_columns_for_conversion

def speed(Tracks, Spots, Conversion=None):
    """
    Generates a polar plot of track speed vectors from TrackMate data.

    Each track is represented as an arrow in a polar plot where the arrow's length
    corresponds to the track's mean straight-line speed. The top 150 tracks (sorted
    by quality) are processed and centered around 0 degrees for visualization.
    The plot is annotated with statistics (Percent in Densest 90 and Circular Variance).

    Parameters:
    -----------
    Tracks : str
        Path to the track_statistics CSV file exported from TrackMate.
    
    Spots : str
        Path to the spots_statistics CSV file exported from TrackMate.
    
    Conversion : float, optional
        A unit conversion factor (e.g., pixels to micrometers) to apply to distance values.
        If None, no conversion is applied.
    
    Returns:
    --------
    fig : matplotlib.figure.Figure
        The figure object for the generated polar speed vector plot.
    """

    ## -- Checks --
    # File existence
    if not os.path.isfile(Tracks):
        raise FileNotFoundError(f"Tracks file not found: {Tracks}")
    if not os.path.isfile(Spots):
        raise FileNotFoundError(f"Spots file not found: {Spots}")
    
    # Conversion argument validity
    check_conversion_value(Conversion)

    # Load TrackMate data
    track_stats = pd.read_csv(Tracks, skiprows=[1, 2, 3]) 
    spots_stats = pd.read_csv(Spots, skiprows=[1, 2, 3]) 

    ## -- Checks --
    # Missing required columns
    missing_track_cols = [col for col in ALL_TRACK_COLUMNS if col not in track_stats.columns]
    missing_spots_cols = [col for col in ALL_SPOTS_COLUMNS if col not in spots_stats.columns]
    if missing_track_cols:
        raise ValueError(f"Missing required columns in Tracks CSV: {missing_track_cols}")
    if missing_spots_cols:
        raise ValueError(f"Missing required columns in Spots CSV: {missing_spots_cols}")
    
    ## -- Spots Processing -- 

    # Normalize to first 445 frames
    spots_stats = spots_stats[spots_stats["FRAME"] <= 445] 

    # Convert units if needed
    if isinstance(Conversion, (int, float)): 
        spots_stats[Spots_columns_for_conversion] = spots_stats[Spots_columns_for_conversion] * Conversion

    # Keep only first and last Frame for every TRACK_ID in the spots_statistics table
    spots_stats = spots_stats.sort_values(by=['TRACK_ID', 'FRAME'])
    spots_stats = spots_stats.groupby('TRACK_ID', group_keys=False).apply(lambda x: x.iloc[[0, -1]])
    spots_stats = spots_stats.reset_index(drop=True)

    # Split into two new tables: First Frame, Last Frame
    First_FRAME = spots_stats.drop_duplicates(subset='TRACK_ID', keep='first')
    Last_FRAME = spots_stats.drop_duplicates(subset='TRACK_ID', keep='last')

    ## -- Track Processing --

    # Normalize to first 445 frames
    track_stats = track_stats[track_stats["TRACK_START"] <= 445] 
    
    # Convert units if needed 
    if isinstance(Conversion, (int, float)):
        track_stats[Track_columns_for_conversion] = track_stats[Track_columns_for_conversion] * Conversion

    # Sort by track quality
    track_stats = track_stats.sort_values(by='TRACK_MEAN_QUALITY', ascending=False)

    # Take only the top 150 of tracks 
    track_stats = track_stats[0:150]

    ## -- General Engineering

    # Merge the First and Last FRAME tables to the track statistics table
    track_stats = track_stats.merge(First_FRAME[['TRACK_ID', 'POSITION_X','POSITION_Y']], on='TRACK_ID')
    track_stats = track_stats.rename(columns={'POSITION_X': 'First_POSITION_X', 'POSITION_Y': 'First_POSITION_Y'})
    track_stats = track_stats.merge(Last_FRAME[['TRACK_ID', 'POSITION_X','POSITION_Y']], on='TRACK_ID')
    track_stats = track_stats.rename(columns={'POSITION_X': 'Last_POSITION_X', 'POSITION_Y': 'Last_POSITION_Y'})
    track_stats = track_stats.set_index('TRACK_ID')

    # Calculate the change in positions (delta_x and delta_y)
    track_stats['delta_x'] = track_stats['Last_POSITION_X'] - track_stats['First_POSITION_X']
    track_stats['delta_y'] = track_stats['Last_POSITION_Y'] - track_stats['First_POSITION_Y']

    # Calculate the angle in radians using atan2
    track_stats['angle_radians'] = np.arctan2(track_stats['delta_y'], track_stats['delta_x'])

    # Convert to degrees
    track_stats['ANGLE_DEGREES'] = np.degrees(track_stats['angle_radians'])

    # Calculate mean displacement
    displacement = np.array(track_stats['TRACK_DISPLACEMENT'])
    d_mean = displacement.mean()

    # Convert angles to radians and keep only angles for tracks with larger than mean displacement
    angles = np.array(track_stats['ANGLE_DEGREES'][displacement >= d_mean])
    angles_rad = np.deg2rad(angles)

    # Add Percent in Densest 90 Window
    percent_within_90 = percent_densest_90(angles)

    # Add circular variance 
    circular_variance = circular_variance_from_angles(angles_rad)

    # Calulate mean angle for circular data
    rad_mean = mean_angle(angles_rad)

    ## -- Visualization --
    
    # Number of tracks
    n_tracks = len(track_stats)

    # Create color map with a unique color for each vector
    colors = cm.rainbow(np.linspace(0, 1, n_tracks))

    # Set up polar plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

    # Set background color 
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    for idx, (i, row) in enumerate(track_stats.iterrows()):
        angle = row['angle_radians'] 
        speed = row['MEAN_STRAIGHT_LINE_SPEED'] 

        # Plot the vector as an arrow
        ax.arrow(
            angle - rad_mean, 0, 
            0, speed, 
            width=0.005,                
            head_width=0.04,            
            head_length=0.08 * speed,   
            length_includes_head=True,  
            fc=colors[idx], 
            ec=colors[idx]
        )

    # Annotate  plot with the Percent in Densest 90 Window   
    ax.text(
        1.1,  
        -0.025,  
        f"Percent in Densest 90: {percent_within_90:.1f}%", 
        color='white',            
        fontsize=16,
        ha='right', va='bottom',    
        transform=ax.transAxes    
    )

    # Annotate plot with Circular Variance  
    ax.text(
        1.1, 
        -0.075,  
        f"Circular Variance: {circular_variance:.2f}",  
        color='white',            
        fontsize=16,
        ha='right', va='bottom',   
        transform=ax.transAxes    
    )

    # Set the maximum radius to fit all data
    ax.set_rmax(track_stats['MEAN_STRAIGHT_LINE_SPEED'].max() + 5)  
    ax.set_rlabel_position(80)

    # Set the title and labels for the polar plot
    ax.set_title("Track Speed Vectors", color='white', fontsize = 20, pad = 30)

    # Set  grid and axis labels to white
    ax.grid(color='white', linestyle='--', linewidth=0.5)
    ax.tick_params(axis='both', labelcolor='white')
    plt.close(fig)
    return fig