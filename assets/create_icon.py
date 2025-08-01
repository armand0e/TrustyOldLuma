#!/usr/bin/env python3
"""
Simple script to create a basic icon for the setup application.
This creates a minimal ICO file that can be used with PyInstaller.
"""

import os
from pathlib import Path

def create_simple_icon():
    """Create a simple 16x16 ICO file for the setup application."""
    # This is a minimal ICO file header + 16x16 1-bit bitmap
    # Creates a simple black square icon
    ico_data = bytes([
        # ICO header
        0x00, 0x00,  # Reserved (must be 0)
        0x01, 0x00,  # Type (1 = ICO)
        0x01, 0x00,  # Number of images
        
        # Image directory entry
        0x10,        # Width (16)
        0x10,        # Height (16)
        0x00,        # Color count (0 = no palette)
        0x00,        # Reserved
        0x01, 0x00,  # Color planes
        0x01, 0x00,  # Bits per pixel
        0x30, 0x00, 0x00, 0x00,  # Size of image data (48 bytes)
        0x16, 0x00, 0x00, 0x00,  # Offset to image data
        
        # Bitmap header (40 bytes)
        0x28, 0x00, 0x00, 0x00,  # Header size
        0x10, 0x00, 0x00, 0x00,  # Width
        0x20, 0x00, 0x00, 0x00,  # Height (32 = 16*2 for AND mask)
        0x01, 0x00,              # Planes
        0x01, 0x00,              # Bits per pixel
        0x00, 0x00, 0x00, 0x00,  # Compression
        0x00, 0x00, 0x00, 0x00,  # Image size
        0x00, 0x00, 0x00, 0x00,  # X pixels per meter
        0x00, 0x00, 0x00, 0x00,  # Y pixels per meter
        0x00, 0x00, 0x00, 0x00,  # Colors used
        0x00, 0x00, 0x00, 0x00,  # Important colors
        
        # Color palette (2 colors for 1-bit)
        0x00, 0x00, 0x00, 0x00,  # Black
        0xFF, 0xFF, 0xFF, 0x00,  # White
        
        # XOR mask (16x16, 1 bit per pixel, padded to 4-byte boundary)
        # Creates a simple pattern
        0xFF, 0xFF,  # Row 1
        0x81, 0x81,  # Row 2
        0x81, 0x81,  # Row 3
        0x81, 0x81,  # Row 4
        0x81, 0x81,  # Row 5
        0x81, 0x81,  # Row 6
        0x81, 0x81,  # Row 7
        0x81, 0x81,  # Row 8
        0x81, 0x81,  # Row 9
        0x81, 0x81,  # Row 10
        0x81, 0x81,  # Row 11
        0x81, 0x81,  # Row 12
        0x81, 0x81,  # Row 13
        0x81, 0x81,  # Row 14
        0x81, 0x81,  # Row 15
        0xFF, 0xFF,  # Row 16
        
        # AND mask (16x16, 1 bit per pixel, all transparent)
        0x00, 0x00,  # Row 1
        0x00, 0x00,  # Row 2
        0x00, 0x00,  # Row 3
        0x00, 0x00,  # Row 4
        0x00, 0x00,  # Row 5
        0x00, 0x00,  # Row 6
        0x00, 0x00,  # Row 7
        0x00, 0x00,  # Row 8
        0x00, 0x00,  # Row 9
        0x00, 0x00,  # Row 10
        0x00, 0x00,  # Row 11
        0x00, 0x00,  # Row 12
        0x00, 0x00,  # Row 13
        0x00, 0x00,  # Row 14
        0x00, 0x00,  # Row 15
        0x00, 0x00,  # Row 16
    ])
    
    icon_path = Path("assets/icon.ico")
    with open(icon_path, "wb") as f:
        f.write(ico_data)
    
    print(f"Created simple icon at {icon_path}")

if __name__ == "__main__":
    create_simple_icon()