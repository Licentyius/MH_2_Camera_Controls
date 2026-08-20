"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Camera Presets V1.0 - The controls for Camera now Seperated
"""

# camera_presets.py
import math

# Centralized camera preset profiles
PRESETS = {
    "selfie_left":        {"look_at_y": 5.8, "fov": 55.0,  "dist": 30.0,  "rh": -38.0,  "rv": -4.0},
    "selfie_right":       {"look_at_y": 5.8, "fov": 55.0,  "dist": 30.0,  "rh": 38.0,   "rv": -4.0},
    "security_cam_right": {"look_at_y": 4.8, "fov": 45.0,  "dist": 110.0, "rh": 35.0,   "rv": 50.0},
    "security_cam_left":  {"look_at_y": 4.8, "fov": 45.0,  "dist": 110.0, "rh": -35.0,  "rv": 50.0},
    "wormsview":          {"look_at_y": 1.5, "fov": 45.0,  "dist": 45.0,  "rh": 0.0,    "rv": -40.0},
    "fish eye":           {"look_at_y": 6.95,"fov": 120.0, "dist": 4.6,   "rh": 0.0,    "rv": 0.0},
    "godview":            {"look_at_y": 4.5, "fov": 45.0,  "dist": 110.0, "rh": 0.0,    "rv": 89.9},
    "birdview":           {"look_at_y": 4.5, "fov": 45.0,  "dist": 110.0, "rh": 0.0,    "rv": 89.9},
    "ortho":              {"look_at_y": 3.5, "fov": 45.0,  "dist": 38.0,  "rh": 0.0,    "rv": 0.0,    "ortho_mag": 2.8},
    "pov":                {"look_at_y": 7.2, "fov": 65.0,  "dist": 0.1,   "rh": 180.0,  "rv": 0.0,    "look_at_x": 0.0, "look_at_z": 1.5},
    "panoramic":          {"look_at_y": 4.5, "fov": 75.0,  "dist": 160.0, "rh": 0.0,    "rv": 0.0,    "look_at_x": 0.0, "look_at_z": 0.0},
    "isometric":          {"look_at_y": 3.8, "fov": 45.0,  "dist": 45.0,  "rh": 45.0,   "rv": -35.264,"ortho_mag": 6.2},
    "wideshot":           {"look_at_y": 2.5, "fov": 50.0,  "dist": 90.0,  "rh": 0.0,    "rv": -12.0,  "look_at_x": 0.0, "look_at_z": 0.0},
    "closeup":            {"look_at_y": 6.8, "fov": 22.0,  "dist": 12.0,  "rh": 0.0,    "rv": 0.0},
    "high angle":         {"look_at_y": 4.5, "fov": 46.0,  "dist": 25.0,  "rh": 0.0,    "rv": 32.0},
    "low angle":          {"look_at_y": 6.5, "fov": 46.0,  "dist": 30.0,  "rh": 0.0,    "rv": -32.0},
    "eye level":          {"look_at_y": 5.2, "fov": 38.0,  "dist": 30.0,  "rh": 0.0,    "rv": 0.0},
    "ots_left":           {"look_at_y": 8.0, "fov": 50.0,  "dist": 3.0,   "rh": -165.0, "rv": 8.0,    "look_at_z": -4.9},
    "ots_right":          {"look_at_y": 8.0, "fov": 50.0,  "dist": 3.0,   "rh": 165.0,  "rv": 8.0,    "look_at_z": -4.9},
    "mediumshot":         {"look_at_y": 4.5, "fov": 40.0,  "dist": 48.0,  "rh": 0.0,    "rv": 0.0},
    "fullshot":           {"look_at_y": 1.5, "fov": 35.0,  "dist": 75.0,  "rh": 0.0,    "rv": 0.0},
    "reset":              {"look_at_y": 1.5, "fov": 45.0,  "dist": 65.0,  "rh": 0.0,    "rv": 0.0}
}
