"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Mathematics Overlay Presets V1.2 - The Math Overlay options Separated for use with .py drop ins
"""

import sys
import math
import random
import numpy as np

from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor, QRadialGradient, QLinearGradient, QPen, QPolygon

from PySide6.QtGui import QLinearGradient
from . import camera_presets 

def trigger_cinematic_preset(camera, preset_name):
    """Applies camera positioning matrices and transforms projection fields."""
    if not camera:
        return

    name = preset_name.lower().strip()
    
    # Retrieve configuration profile
    preset = camera_presets.PRESETS.get(name)
    if not preset:
        return

    # Handle Perspective vs Orthographic flags
    camera.cameraPers = name not in ["ortho", "isometric"]

    # Assign fallback lookAt defaults, override if explicit target profile demands it
    camera.lookAt.setX(preset.get("look_at_x", 0.0))
    camera.lookAt.setY(preset["look_at_y"])
    camera.lookAt.setZ(preset.get("look_at_z", 0.0))

    # Apply magnification settings for orthographic lenses
    if "ortho_mag" in preset:
        camera.ortho_magnification = preset["ortho_mag"]

    # Unpack targets safely
    target_fov = preset["fov"]
    target_dist = preset["dist"]
    target_rh = preset["rh"]
    target_rv = preset["rv"]

    # Assign matrix fields dynamically
    camera.verticalAngle = target_fov
    camera.cameraDist = target_dist
    
    if hasattr(camera, 'rh_angle'): 
        camera.rh_angle = target_rh
    if hasattr(camera, 'rv_angle'): 
        camera.rv_angle = target_rv

    # Calculate final translation offsets using target coordinates
    rad_h = math.radians(target_rh)
    rad_v = math.radians(target_rv)
    cx = target_dist * math.sin(rad_h) * math.cos(rad_v)
    cy = target_dist * math.sin(rad_v)
    cz = target_dist * math.cos(rad_h) * math.cos(rad_v)
    
    camera.cameraPos.setX(camera.lookAt.x() + cx)
    camera.cameraPos.setY(camera.lookAt.y() + cy)
    camera.cameraPos.setZ(camera.lookAt.z() + cz)
    
    camera.updateViewMatrix()
    camera.calculateProjMatrix()

class CameraFXProcessor:
    """Universal graphic processor parsing dropped JSON configuration structures."""
    
    @staticmethod
    def draw_effect(painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio, config=None):
        if not config:
            return

        fx_type = config.get("type")

        # Dynamically map composition text strings back to native PySide6 objects
        comp_str = config.get("composition_mode", "SourceOver")
        if hasattr(QPainter.CompositionMode, f"CompositionMode_{comp_str}"):
            painter.setCompositionMode(getattr(QPainter.CompositionMode, f"CompositionMode_{comp_str}"))
        elif hasattr(QPainter, f"CompositionMode_{comp_str}"):
            painter.setCompositionMode(getattr(QPainter, f"CompositionMode_{comp_str}"))

        # =========================
        # TYPE 1: RADIAL GRADIENTS
        # =========================
        if fx_type == "radial_gradient":
            center_x, center_y = w / 2.0, h / 2.0
            radius = max(w, h) / config.get("radius_factor", 1.2)
            gradient = QRadialGradient(center_x, center_y, radius)
            
            for stop in config.get("color_stops", []):
                # Safely split string numbers apart, fallback to pure red if error occurs
                color_str = stop.get("color_str", "255,0,0")
                r, g, b = map(int, color_str.split(","))
                alpha = max(0, min(int(intensity * stop.get("alpha_multiplier", 1.0)), 255))
                gradient.setColorAt(stop["position"], QColor(r, g, b, alpha))
            
            painter.setPen(Qt.PenStyle.NoPen if hasattr(Qt.PenStyle, "NoPen") else Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawRect(0, 0, w, h)

        # =========================
        # TYPE 2: LINEAR GRADIENTS
        # =========================
        elif fx_type == "linear_gradient":
            start_x, start_y = config.get("start", 0), config.get("start", 0)
            end_factors = config.get("end_factor", [1.0, 1.0])
            
            end_x = int(w * end_factors[0])
            end_y = int(h * end_factors[1])
            
            gradient = QLinearGradient(start_x, start_y, end_x, end_y)
            for stop in config.get("color_stops", []):
                color_str = stop.get("color_str", "255,255,255")
                r, g, b = map(int, color_str.split(","))
                alpha = max(0, min(int(intensity * stop.get("alpha_multiplier", 1.0)), 255))
                gradient.setColorAt(stop["position"], QColor(r, g, b, alpha))
                
            painter.setPen(Qt.PenStyle.NoPen if hasattr(Qt.PenStyle, "NoPen") else Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawRect(0, 0, w, h)

        # ================================
        # TYPE 3.5: LINES & SCANNER GRIDS
        # ================================
        elif fx_type == "lines_grid":
            grid_gap = int(config.get("grid_gap", 4))
            
            # Unpack color string profiles safely
            color_str = config.get("grid_color_str", "255,255,255")
            r, g, b = map(int, color_str.split(","))
            
            alpha_mult = config.get("grid_alpha_multiplier", 1.0)
            alpha = int(intensity * alpha_mult) if alpha_mult > 0 else 12
            alpha = max(0, min(alpha, 255))
            
            painter.setPen(QPen(QColor(r, g, b, alpha), 1, Qt.PenStyle.SolidLine))
            
            for y in range(0, log_h if config.get("horizontal_only") else h, grid_gap):
                painter.drawLine(0, y, log_w if config.get("horizontal_only") else w, y)
            
            if not config.get("horizontal_only", False):
                for x in range(0, w, grid_gap):
                    painter.drawLine(x, 0, x, h)
            
            if config.get("draw_corners", False):
                corner_str = config.get("corner_color_str", "255,255,255")
                cr, cg, cb = map(int, corner_str.split(","))
                c_alpha = max(0, min(int(intensity * config.get("corner_alpha_multiplier", 5.0)), 255))
                painter.setPen(QPen(QColor(cr, cg, cb, c_alpha), 2, Qt.PenStyle.SolidLine))
                pad = 20
                painter.drawLine(pad, pad, pad + 30, pad)
                painter.drawLine(pad, pad, pad, pad + 30)
                painter.drawLine(log_w - pad, log_h - pad, log_w - pad - 30, log_h - pad)
                painter.drawLine(log_w - pad, log_h - pad, log_w - pad, log_h - pad - 30)

            if "vignette" in config:
                v = config["vignette"]
                radius = max(w, h) / v.get("radius_factor", 1.2)
                grad = QRadialGradient(w / 2.0, h / 2.0, radius)
                for s in v.get("stops", []):
                    v_str = s.get("color_str", "0,0,0")
                    vr, vg, vb = map(int, v_str.split(","))
                    valpha = max(0, min(int(intensity * s.get("alpha_mult", 1.0)), 255))
                    grad.setColorAt(s["pos"], QColor(vr, vg, vb, valpha))
                painter.setPen(Qt.NoPen)
                painter.setBrush(grad)
                painter.drawRect(0, 0, w, h)

        # ================================================================================
        # TYPE 4: BITMAP & MULTI-PASS CHANNELS (example Chromatic Aberration, 1920s Movie)
        # ================================================================================
        elif fx_type == "multi_pass_bitmap":

            # Sub-type: Channel Splitting (Chromatic Aberration)
            if config.get("pass_mode") == "chromatic_aberration":
                painter.fillRect(0, 0, w, h, QColor(0, 0, 0, 255))
                
                cyan_img = src.copy()
                cyan_arr = np.frombuffer(cyan_img.bits(), dtype=np.uint8).reshape((h, w, 4))
                cyan_arr[:, :, 2] = 0  # Drop red
                
                red_img = src.copy()
                red_arr = np.frombuffer(red_img.bits(), dtype=np.uint8).reshape((h, w, 4))
                red_arr[:, :, 0] = 0  # Drop blue
                red_arr[:, :, 1] = 0  # Drop green

                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.drawImage(intensity, 0, cyan_img)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
                painter.drawImage(-intensity, 0, red_img)
                
            # Sub-type: Vintage Sepia Grayscale + Procedural Film Scratches
            elif config.get("pass_mode") == "vintage_film":
                grayscale_img = src.convertToFormat(QImage.Format.Format_Grayscale8)
                monochrome_img = grayscale_img.convertToFormat(QImage.Format.Format_ARGB32)
                painter.drawImage(0, 0, monochrome_img)

                # Overlay sepia burn vignette
                sepia_grad = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.3)
                sepia_grad.setColorAt(0.0, QColor(160, 115, 65, int(intensity * 1.5)))  
                sepia_grad.setColorAt(1.0, QColor(30, 20, 10, int(160 + intensity * 3.0))) 
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorBurn)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(sepia_grad)
                painter.drawRect(0, 0, w, h)

                # Reset to draw random scratches cleanly
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.setPen(QPen(QColor(15, 10, 5, 130), 1, Qt.PenStyle.SolidLine))
                for _ in range(max(1, int(intensity / 3))):
                    sx = random.randint(0, w)
                    painter.drawLine(sx, 0, sx + random.randint(-1, 1), h)

        # ===============================================================================
        # TYPE 5: PROCEDURAL MATH PARTICLES (example Raindrops, Grain Noise, Smoke Curls)
        # ===============================================================================
        elif fx_type == "procedural_particles":
            
            p_mode = config.get("particle_mode")
            
            # Sub-type: Film Grain static noise loop
            if p_mode == "grain":
                grain_mask = QImage(w, h, QImage.Format.Format_ARGB32)
                grain_mask.fill(Qt.GlobalColor.transparent if hasattr(Qt.GlobalColor, "transparent") else Qt.transparent)
                for _ in range(int(w * h * (intensity / 500.0))):
                    rx = random.randint(0, w - 1)
                    ry = random.randint(0, h - 1)
                    n = random.randint(220, 255)
                    grain_mask.setPixelColor(rx, ry, QColor(n, n, n, int(intensity * 6)))
                painter.drawImage(0, 0, grain_mask)
                
            # Sub-type: Volumetric rising sine-wave trails (Smoke Curls)
            elif p_mode == "sine_smoke":
                plumes = max(2, int(intensity / 4))
                for i in range(plumes):
                    floor_x = int((log_w / (plumes + 1)) * (i + 1)) + random.randint(-30, 30)
                    for y in range(log_h, 0, -6):
                        pct = (log_h - y) / float(log_h)
                        curl = math.sin(y * 0.04 + i) * 35.0
                        cx = floor_x + curl + (pct * 40.0 * (1.0 if i % 2 == 0 else -1.0))
                        size = int(12 + (pct * 5.0) * 15) if pct < 0.2 else int(42 * (1.0 - pct * 0.7))
                        if size <= 2: continue
                        alpha = max(0, min(int(int(intensity * 3.5) * (1.0 - pct)), 255))
                        painter.setBrush(QColor(235, 238, 245, alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(int(cx - size / 2), y, size, size)

        # ====================================================================================
        # TYPE 5.5: PROCEDURAL SHAPE MATRIX SCATTER (example Hearts Valentine, Custom Vectors)
        # ====================================================================================
        elif fx_type == "procedural_shape_scatter":
            shape_mode = config.get("shape_mode")
            
            # Sub-type: Layered Specular Valentine Heart Loop
            if shape_mode == "pop_hearts":
                # Soft environmental ambient wash
                glow_str = config.get("glow_color_str", "255,100,150")
                gr, gg, gb = map(int, glow_str.split(","))
                
                pink_glow = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.2)
                pink_glow.setColorAt(0.0, QColor(0, 0, 0, 0))
                pink_glow.setColorAt(1.0, QColor(gr, gg, gb, max(0, min(int(80 + intensity * 4.0), 255))))
                
                painter.setPen(Qt.PenStyle.NoPen if hasattr(Qt.PenStyle, "NoPen") else Qt.NoPen)
                painter.setBrush(pink_glow)
                painter.drawRect(0, 0, w, h)
                
                # Execute original scattered geometry engine logic
                for i in range(int(intensity * 1.5)):
                    hx = random.choice([random.randint(30, 140), random.randint(max(40, log_w - 160), max(50, log_w - 40))])
                    hy = random.randint(30, max(40, log_h - 50))
                    size = 18
                    
                    # Pass 1: Draw Soft Drop Shadow
                    painter.save()
                    painter.translate(hx + int(size / 2) + 3, hy + int(size / 2) + 3)
                    painter.rotate(45)
                    painter.setBrush(QColor(15, 5, 10, 110))
                    painter.drawRect(int(-size / 2), int(-size / 2), size, size)
                    painter.drawEllipse(int(-size / 2), -size, size, size)
                    painter.drawEllipse(-size, int(-size / 2), size, size)
                    painter.restore()

                    # Pass 2: Draw Main Volumetric Heart Core
                    painter.save()
                    painter.translate(hx + int(size / 2), hy + int(size / 2))
                    painter.rotate(45)
                    hr, hg, hb = map(int, config.get("shape_color_str", "255,35,85").split(","))
                    painter.setBrush(QColor(hr, hg, hb, 230))
                    painter.drawRect(int(-size / 2), int(-size / 2), size, size)
                    painter.drawEllipse(int(-size / 2), -size, size, size)
                    painter.drawEllipse(-size, int(-size / 2), size, size)
                    painter.restore()

                    # Pass 3: Specular High-Gloss Highlights
                    painter.setBrush(QColor(255, 255, 255, 210))
                    painter.drawEllipse(hx + int(size * 0.15), hy - int(size * 0.2), 4, 4)
                    painter.drawEllipse(hx + int(size * 0.65), hy - int(size * 0.2), 4, 4)
                    
                painter.setBrush(Qt.BrushStyle.NoBrush if hasattr(Qt.BrushStyle, "NoBrush") else Qt.NoBrush)

        # ====================================================================================
        # TYPE 6: DYNAMIC TEXT & FONTS LAYOUTS (example Camcorder overlays, Lineups, Magazine)
        # ====================================================================================
        elif fx_type == "typography_hud":
            font = painter.font()
            font.setFamily(config.get("font_family", "Arial"))
            font.setBold(config.get("font_bold", True))
            font.setPointSize(config.get("font_size", 12))
            painter.setFont(font)
            painter.setPen(QPen(QColor(*config.get("text_color", ))))
            
            t_mode = config.get("text_mode")
            
            # Sub-type: Symmetric step counters (MugshotBooking Height Lines)
            if t_mode == "booking_lineup":
                total_inches = 0
                for y in range(int(log_h * 0.85), int(log_h * 0.15), -20):
                    painter.setPen(QPen(QColor(40, 40, 40, int(70 + intensity * 4.0)), 1, Qt.PenStyle.SolidLine))
                    painter.drawLine(0, y, log_w, y)
                    
                    feet = 5 + (total_inches // 12)
                    inches = total_inches % 12
                    height_str = f"{feet}' {inches}\""
                    
                    painter.setPen(QPen(QColor(30, 30, 30, 220)))
                    painter.drawText(15, y - 4, height_str)
                    painter.drawText(log_w - 60, y - 4, height_str)
                    total_inches += 1
