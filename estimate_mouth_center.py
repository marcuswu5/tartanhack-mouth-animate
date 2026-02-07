#!/usr/bin/env python3
"""
Estimate mouth center from OpenFace facial landmarks (excluding mouth landmarks 48-65).
Uses nose tip, chin, and jaw landmarks to calculate mouth center position.
"""

import pandas as pd
import numpy as np
import sys


def estimate_mouth_center(row):
    """
    Estimate the center of the mouth using non-mouth facial landmarks.
    
    Args:
        row: A pandas Series containing OpenFace landmark data
        
    Returns:
        tuple: (x_center, y_center) pixel coordinates of estimated mouth center
    """
    # Key landmarks:
    # 30 = nose tip
    # 8 = chin
    # 3-5 = left jaw
    # 11-13 = right jaw
    
    # Extract nose tip coordinates
    nose_tip_x = row['x_30']
    nose_tip_y = row['y_30']
    
    # Extract chin coordinates
    chin_x = row['x_8']
    chin_y = row['y_8']
    
    # Extract left jaw points (3, 4, 5)
    left_jaw_x = np.mean([row['x_3'], row['x_4'], row['x_5']])
    left_jaw_y = np.mean([row['y_3'], row['y_4'], row['y_5']])
    
    # Extract right jaw points (11, 12, 13)
    right_jaw_x = np.mean([row['x_11'], row['x_12'], row['x_13']])
    right_jaw_y = np.mean([row['y_11'], row['y_12'], row['y_13']])
    
    # Horizontal position: average of nose tip and jaw midpoints
    # This handles face rotation naturally
    x_center = np.mean([nose_tip_x, left_jaw_x, right_jaw_x])
    
    # Vertical position: interpolate between nose tip and chin
    # Mouth center is typically about 45% of the way from nose to chin
    interpolation_factor = 0.45
    y_center = nose_tip_y + interpolation_factor * (chin_y - nose_tip_y)
    
    return x_center, y_center


def process_csv(input_csv, output_csv=None):
    """
    Process OpenFace CSV file and add mouth center estimates.
    
    Args:
        input_csv: Path to input CSV file with OpenFace landmarks
        output_csv: Optional path to output CSV (if None, prints to stdout)
    """
    # Read the CSV file
    df = pd.read_csv(input_csv)
    
    # Strip whitespace from column names (OpenFace CSVs have spaces after commas)
    df.columns = df.columns.str.strip()
    
    # Calculate mouth center for each frame
    mouth_centers = df.apply(estimate_mouth_center, axis=1)
    
    # Add mouth center columns to dataframe
    df['mouth_center_x'] = mouth_centers.apply(lambda x: x[0])
    df['mouth_center_y'] = mouth_centers.apply(lambda x: x[1])
    
    # Output results
    if output_csv:
        df.to_csv(output_csv, index=False)
        print(f"Results saved to {output_csv}")
    else:
        # Print just the mouth center coordinates
        print("frame, mouth_center_x, mouth_center_y")
        for idx, row in df.iterrows():
            frame = row.get('frame', idx)
            print(f"{frame}, {row['mouth_center_x']:.2f}, {row['mouth_center_y']:.2f}")
    
    return df


def estimate_single_frame(csv_file, frame_num=0):
    """
    Estimate mouth center for a single frame.
    
    Args:
        csv_file: Path to OpenFace CSV file
        frame_num: Frame number to process (default: 0)
        
    Returns:
        tuple: (x_center, y_center) coordinates
    """
    df = pd.read_csv(csv_file)
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    if frame_num >= len(df):
        raise ValueError(f"Frame {frame_num} not found in CSV (only {len(df)} frames)")
    
    row = df.iloc[frame_num]
    x_center, y_center = estimate_mouth_center(row)
    
    print(f"Frame {frame_num}: Mouth center at ({x_center:.2f}, {y_center:.2f})")
    return x_center, y_center


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python estimate_mouth_center.py <input_csv> [output_csv]")
        print("   Or: python estimate_mouth_center.py <input_csv> --frame <frame_num>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Check if processing single frame
    if len(sys.argv) > 2 and sys.argv[2] == '--frame':
        frame_num = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        estimate_single_frame(input_file, frame_num)
    else:
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        process_csv(input_file, output_file)
