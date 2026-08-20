"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Mathematics Overlay Presets V1.0 - The Math Overlay options Separated
"""

import sys
import math
import random
import numpy as np

import camera_controls

from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor, QRadialGradient, QLinearGradient, QPen, QPolygon

from PySide6.QtGui import QLinearGradient
import camera_presets 

_filter_overlay_label = camera_controls._filter_overlay_label

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

    # Execute system update hooks
    if hasattr(camera, 'updateCameraPosition'): 
        camera.updateCameraPosition()
    elif hasattr(camera, 'update'): 
        camera.update()

    camera.updateViewMatrix()
    camera.calculateProjMatrix()

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
    """Class wrapper"""
    
    @staticmethod
    def draw_effect(painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio):

        log_w = log_w
        log_h = log_h
        pixel_ratio = pixel_ratio

        # =============================
        # CORE EFFECTS DISPATCH MATRIX 
        # =============================
        if selected_effect == "chromatic aberration":

            painter.fillRect(0, 0, w, h, QColor(0, 0, 0, 255))

            import numpy as np
            cyan_img = src.copy()
            cyan_arr = np.frombuffer(cyan_img.bits(), dtype=np.uint8).reshape((h, w, 4))
            cyan_arr[:, :, 2] = 0  
            
            red_img = src.copy()
            red_arr = np.frombuffer(red_img.bits(), dtype=np.uint8).reshape((h, w, 4))
            red_arr[:, :, 0] = 0  
            red_arr[:, :, 1] = 0  

            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(intensity, 0, cyan_img)
            
            painter.setCompositionMode(QPainter.CompositionMode_Plus)
            painter.drawImage(-intensity, 0, red_img)

        elif selected_effect == "vintage film noise":
            grain_mask = QImage(w, h, QImage.Format_ARGB32)
            grain_mask.fill(Qt.transparent)
            for _ in range(int(w * h * (intensity / 500.0))):
                rx = random.randint(0, w - 1)
                ry = random.randint(0, h - 1)
                n = random.randint(220, 255)
                grain_mask.setPixelColor(rx, ry, QColor(n, n, n, int(intensity * 6)))
            
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, grain_mask)

        elif selected_effect == "thermal mapping (flir)":
            thermal_grad = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.4)
            thermal_grad.setColorAt(0.0, QColor(255, 240, 0, int(intensity * 4.5))) 
            thermal_grad.setColorAt(0.6, QColor(235, 0, 115, int(intensity * 3.5))) 
            thermal_grad.setColorAt(1.0, QColor(15, 0, 90, int(intensity * 5.0)))   
            
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(Qt.NoPen)
            painter.setBrush(thermal_grad)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "security cam hud":
            log_w = log_w
            log_h = log_h
            
            painter.setPen(QPen(QColor(255, 255, 255, 12), 1, Qt.PenStyle.SolidLine))

            for y in range(0, log_h, 4):
                painter.drawLine(0, y, log_w, y)
            
            painter.setPen(QPen(QColor(255, 255, 255, int(intensity * 5)), 2, Qt.PenStyle.SolidLine))
            pad = 20
            painter.drawLine(pad, pad, pad + 30, pad)
            painter.drawLine(pad, pad, pad, pad + 30)
            painter.drawLine(log_w - pad, log_h - pad, log_w - pad - 30, log_h - pad)
            painter.drawLine(log_w - pad, log_h - pad, log_w - pad, log_h - pad - 30)

        elif selected_effect == "western":
            center_x, center_y = w / 2.0, h / 2.0
            radius = max(w, h) / 1.3
        
            golden_grad = QRadialGradient(center_x, center_y, radius)
            golden_grad.setColorAt(0.0, QColor(0, 0, 0, 0)) 
            golden_grad.setColorAt(0.6, QColor(230, 150, 50, int(intensity * 1.5))) 
            golden_grad.setColorAt(1.0, QColor(80, 40, 10, int(intensity * 6.0)))    
        
            painter.setPen(Qt.NoPen)
            painter.setBrush(golden_grad)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "cyberpunk terminal":
            painter.setPen(QPen(QColor(0, 255, 128, int(intensity * 1.2)), 1, Qt.PenStyle.SolidLine))
            grid_size = int(25 * pixel_ratio)
            for x in range(0, w, grid_size):
                painter.drawLine(x, 0, x, h)
            for y in range(0, h, grid_size):
                painter.drawLine(0, y, w, y)
                
            edge_grad = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.2)
            edge_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
            edge_grad.setColorAt(1.0, QColor(0, 40, 20, int(intensity * 4)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(edge_grad)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "hologram":
            painter.setPen(QPen(QColor(0, 180, 255, int(intensity * 1.5)), 1, Qt.PenStyle.SolidLine))
            for y in range(0, h, int(6 * pixel_ratio)):
                painter.drawLine(0, y, w, y)
            
            holo_ring = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 2.0)
            holo_ring.setColorAt(0.0, QColor(0, 0, 0, 0))
            holo_ring.setColorAt(0.7, QColor(0, 120, 255, int(intensity * 2)))
            holo_ring.setColorAt(1.0, QColor(0, 50, 150, int(intensity * 5)))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(holo_ring)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "90s camcorder":
            log_w = log_w
            log_h = log_h
            
            font = painter.font()

            font.setFamily("Courier New")
            font.setBold(True)
            font.setPointSize(13)
            painter.setFont(font)
            
            if intensity % 2 == 0:
                painter.setBrush(QColor(255, 30, 30, 240))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(30, 25, 12, 12)
            
            painter.setPen(QPen(QColor(255, 255, 255, 210)))
            painter.drawText(50, 36, "REC")
            
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 210), 2))
            painter.drawRect(log_w - 75, 24, 35, 16) 
            painter.fillRect(log_w - 40, 29, 3, 6, QColor(255, 255, 255, 210)) 
            
            bar_count = 3 if intensity > 10 else (2 if intensity > 4 else 1)
            for i in range(bar_count):
                painter.fillRect(log_w - 71 + (i * 9), 28, 7, 8, QColor(255, 255, 255, 210))
            
            painter.drawText(30, log_h - 30, "AUTO")
            painter.drawText(30, log_h - 55, "SP")
            painter.drawText(log_w - 150, log_h - 30, "12:04:15 PM")
            painter.drawText(log_w - 150, log_h - 55, "SEP. 19 1996")
            
            painter.setPen(QPen(QColor(255, 255, 255, 45), 1, Qt.PenStyle.SolidLine))
            for _ in range(int(intensity * 1.5)):
                noise_y = random.randint(0, log_h)
                painter.drawLine(0, noise_y, log_w, noise_y)
                
            painter.setPen(QPen(QColor(255, 255, 255, 140), 2, Qt.PenStyle.DashLine))
            for _ in range(max(1, int(intensity / 8))):
                thick_y = random.randint(0, log_h)
                for offset in range(-4, 5, 2):
                    painter.drawLine(random.randint(10, 50), thick_y + offset, log_w - random.randint(10, 50), thick_y + offset)

        elif selected_effect == "1920s movie":
            if not src.isNull():
                img_buffer = src.convertToFormat(QImage.Format_Grayscale8)
                img_buffer = img_buffer.convertToFormat(QImage.Format_ARGB32)

                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.drawImage(0, 0, img_buffer)

                painter.setCompositionMode(QPainter.CompositionMode_ColorBurn)
                sepia_grad = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.3)
                sepia_grad.setColorAt(0.0, QColor(160, 115, 65, int(intensity * 1.5)))  
                sepia_grad.setColorAt(0.7, QColor(100, 70, 35, int(intensity * 3.5)))   
                sepia_grad.setColorAt(1.0, QColor(30, 20, 10, int(160 + intensity * 3.0))) 
                
                painter.setPen(Qt.NoPen)
                painter.setBrush(sepia_grad)
                painter.drawRect(0, 0, w, h)

                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(QPen(QColor(15, 10, 5, 130), 1, Qt.PenStyle.SolidLine))
                
                lane_width = max(5, int(w / max(1, int(intensity / 3))))
                for l in range(max(1, int(intensity / 3))):
                    scratch_x = (l * lane_width) + random.randint(0, max(1, lane_width - 5))
                    if 0 < scratch_x < w:
                        painter.drawLine(scratch_x + random.randint(-1, 1), 0, scratch_x, h)

                painter.setBrush(QColor(10, 5, 0, 180))
                for _ in range(int(intensity * 1.5)):
                    painter.drawEllipse(random.randint(5, w - 5), random.randint(5, h - 5), random.randint(1, 3), random.randint(1, 4))
                    
                painter.setBrush(QColor(255, 250, 220, 100))
                for _ in range(int(intensity / 2)):
                    painter.drawEllipse(random.randint(5, w - 5), random.randint(5, h - 5), random.randint(2, 4), random.randint(2, 3))

                painter.setPen(QPen(QColor(5, 5, 5, 200), 2, Qt.PenStyle.SolidLine))
                for _ in range(max(1, int(intensity / 10))):
                    hx = random.randint(20, w - 20)
                    hy = random.randint(10, h - 50)
                    painter.drawLine(hx, hy, hx + random.randint(-12, 12), hy + random.randint(15, 35))

        elif selected_effect == "8-bit arcade":
            log_w = log_w
            log_h = log_h
            
            font = painter.font()

            font.setFamily("Lucida Console")
            font.setBold(True)
            font.setPointSize(11)
            painter.setFont(font)
            
            painter.setPen(QPen(QColor(255, 255, 0, 230)))
            painter.drawText(30, 35, "1UP")
            painter.drawText(30, 55, "024800")
            painter.drawText(log_w - 140, 35, "HIGH SCORE")
            painter.drawText(log_w - 140, 55, "999990")
            
            painter.setBrush(QColor(255, 0, 64, 240))
            painter.setPen(Qt.NoPen)
            
            for i in range(3):
                hx = 30 + (i * 28)
                hy = 70
                painter.drawRect(hx + 4, hy, 4, 4)       
                painter.drawRect(hx + 12, hy, 4, 4)      
                painter.fillRect(hx, hy + 4, 20, 4, QColor(255, 0, 64, 240))    
                painter.fillRect(hx + 2, hy + 8, 16, 4, QColor(255, 0, 64, 240))   
                painter.fillRect(hx + 4, hy + 12, 12, 4, QColor(255, 0, 64, 240))  
                painter.fillRect(hx + 8, hy + 16, 4, 4, QColor(255, 0, 64, 240))   
            
            painter.setPen(QPen(QColor(0, 0, 0, int(35 + intensity * 2.5)), 1, Qt.PenStyle.SolidLine))
            grid_gap = 3  
            
            for y in range(0, log_h, grid_gap):
                painter.drawLine(0, y, log_w, y)
            for x in range(0, log_w, grid_gap):
                painter.drawLine(x, 0, x, log_h)


        elif selected_effect == "80s pc monitor":
            painter.setPen(QPen(QColor(20, 255, 50, 15), 1, Qt.PenStyle.SolidLine))
            for y in range(0, h, 3):
                painter.drawLine(0, y, w, y)
            
            glare = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.1)
            glare.setColorAt(0.0, QColor(0, 40, 10, 0))
            glare.setColorAt(1.0, QColor(0, 20, 5, int(intensity * 4)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glare)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "postcard":
            log_w = log_w
            log_h = log_h
            
            thick = int(12 + intensity / 3)
            pad = int(thick + 10)
            
            painter.setPen(QPen(QColor(240, 230, 200, 220), thick, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            
            # Formatted explicitly to integers to stop PySide6 drawing crashes
            painter.drawRect(int(thick // 2), int(thick / 2), int(log_w - thick), int(log_h - thick))
            
            painter.setPen(QPen(QColor(180, 150, 100, 140), 1, Qt.SolidLine))
            painter.drawRect(int(pad), int(pad), int(log_w - (pad * 2)), int(log_h - (pad * 2)))

        elif selected_effect == "instant photo border":
            log_w = log_w
            log_h = log_h
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(245, 245, 240, 255))
            pad = int(20 + intensity)
            
            # All parameters cast safely to integers for rendering tracking stability
            painter.drawRect(0, 0, int(log_w), int(pad)) 
            painter.drawRect(0, 0, int(pad), int(log_h)) 
            painter.drawRect(int(log_w - pad), 0, int(pad), int(log_h)) 
            painter.drawRect(0, int(log_h - int(pad * 2.8)), int(log_w), int(pad * 2.8))

        elif selected_effect == "oil painting":
            #This one needs work if its to be viable
            painter.setPen(QPen(QColor(255, 255, 255, int(intensity * 1.5)), 1))
            stroke_count = int(intensity * 150)
            for _ in range(stroke_count):
                rx = random.randint(0, w)
                ry = random.randint(0, h)
                length = random.randint(5, 15)
                painter.drawLine(rx, ry, rx + length, ry + random.randint(-2, 2))
                painter.drawLine(rx, ry, rx + random.randint(-2, 2), ry + length)

        elif selected_effect == "comic book style":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, int(intensity * 4.5)))
            dot_spacing = 8
            for x in range(0, w, dot_spacing):
                for y in range(0, h, dot_spacing):
                    if (x + y) % 3 == 0:
                        painter.drawEllipse(x, y, 2, 2)

        elif selected_effect == "true black and white":
            grayscale_img = src.convertToFormat(QImage.Format_Grayscale8)
            monochrome_img = grayscale_img.convertToFormat(QImage.Format_ARGB32)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, monochrome_img)

        elif selected_effect == "prism light leaks":
            
            int_w = int(w)
            int_h = int(h)
            
            leak_grad = QLinearGradient(0, 0, int_w, int(int_h / 3))
            leak_grad.setColorAt(0.0, QColor(255, 50, 50, int(intensity * 4)))
            leak_grad.setColorAt(0.4, QColor(255, 200, 0, int(intensity * 2)))
            leak_grad.setColorAt(0.7, QColor(50, 255, 100, int(intensity * 3)))
            leak_grad.setColorAt(1.0, QColor(50, 100, 255, int(intensity * 4)))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(leak_grad)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "raindrops":
            log_w = log_w
            log_h = log_h
            
            painter.fillRect(0, 0, int(log_w), int(log_h), QColor(15, 25, 35, int(intensity * 1.5)))
            
            for _ in range(int(intensity * 2.5)):
                rx = random.randint(15, int(log_w - 15))
                ry = random.randint(15, int(log_h - 40))
                
                drop_w = random.randint(8, 16)
                drop_h = random.randint(12, 24)
                trail_length = random.randint(30, 90)
                
                trail_thickness = max(1, int(1 + intensity / 15))
                trail_grad = QLinearGradient(rx + int(drop_w / 2), ry, rx + int(drop_w / 2), ry + trail_length)
                trail_grad.setColorAt(0.0, QColor(220, 230, 245, 10))  
                trail_grad.setColorAt(0.8, QColor(240, 245, 255, 65))  
                trail_grad.setColorAt(1.0, QColor(240, 245, 255, 0))   
                
                painter.setPen(Qt.NoPen)
                painter.setBrush(trail_grad)
                painter.drawRect(int(rx + (drop_w // 2) - (trail_thickness // 2)), int(ry), int(trail_thickness), int(trail_length))
                
                drop_y_base = int(ry + trail_length - int(drop_h * 0.4))
                
                painter.setBrush(QColor(0, 5, 15, 110))
                painter.drawEllipse(int(rx + 1), int(drop_y_base + 1), int(drop_w), int(drop_h))
                
                painter.setBrush(QColor(235, 242, 255, 175))
                painter.drawEllipse(int(rx), int(drop_y_base), int(drop_w - 1), int(drop_h - 2))
                
                painter.setBrush(QColor(255, 255, 255, 225))
                painter.drawEllipse(int(rx + (drop_w // 3)), int(drop_y_base + 2), int(drop_w // 3), int(drop_h // 4))
                
                painter.setBrush(Qt.NoBrush)


        elif selected_effect == "mirror border":
            log_w = log_w
            log_h = log_h
            
            thick = int(4 + intensity / 4)

            offset = 8
            
            painter.setPen(QPen(QColor(200, 200, 220, 180), thick, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(offset, offset, log_w - (offset * 2), log_h - (offset * 2))
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1, Qt.PenStyle.SolidLine))
            painter.drawLine(0, 0, offset, offset)
            painter.drawLine(log_w, 0, log_w - offset, offset)
            painter.drawLine(0, log_h, offset, log_h - offset)
            painter.drawLine(log_w, log_h, log_w - offset, log_h - offset)

        elif selected_effect == "stickers overlay":
            log_w = log_w
            log_h = log_h
            
            painter.setPen(Qt.NoPen)

            
            # Setup clean pixel/arcade style fonts for sticker texts
            font = painter.font()
            font.setFamily("Impact" if sys.platform == "win32" else "Helvetica")
            font.setBold(True)
            
            # ==========================================
            # STICKER 1: Top-Left Neon "HELLO" Name Tag
            # ==========================================
            painter.setBrush(QColor(255, 92, 0, 255)) #Orange Accents
            painter.drawRoundedRect(25, 25, 110, 75, 8, 8) 
            painter.setBrush(QColor(255, 255, 255, 255)) # White Center Box
            painter.drawRect(25, 48, 110, 36)
            
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(42, 40, "HELLO")
            
            font.setPointSize(11)
            painter.setFont(font)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(38, 72, "MH2_Creator")
            
            # ==========================================
            # STICKER 2: Bottom-Left Industrial Barcode
            # ==========================================
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(245, 245, 240, 245)) # Cream Paper Body
            painter.drawRect(30, log_h - 85, 130, 55)
            
            # Draw individual random barcode lines natively
            painter.setBrush(QColor(20, 20, 20, 240))
            bx = 40
            while bx < 150:
                line_w = random.choice([2, 4, 6])
                painter.drawRect(bx, log_h - 75, line_w, 30)
                bx += line_w + random.choice([2, 4])
                
            font.setFamily("Courier New")
            font.setPointSize(7)
            painter.setFont(font)
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(50, log_h - 36, "*VER 2.0*")

            # ==========================================
            # STICKER 3: Top-Right Danger Warning Triangle
            # ==========================================
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 180, 0, 235)) # Yellow Warning Body
            from PySide6.QtGui import QPolygon
            from PySide6.QtCore import QPoint
            
            tx = log_w - 120
            ty = 30
            # Build a crisp vector warning triangle shape
            triangle = QPolygon([
                QPoint(tx + 45, ty),
                QPoint(tx, ty + 70),
                QPoint(tx + 90, ty + 70)
            ])
            painter.drawPolygon(triangle)
            
            # Draw the internal black exclamation mark symbol
            painter.setBrush(QColor(15, 15, 15, 255))
            painter.drawRect(tx + 42, ty + 25, 6, 25)
            painter.drawEllipse(tx + 42, ty + 56, 6, 6)

            # ==========================================
            # STICKER 4: Bottom-Right Round Pass Stamp
            # ==========================================
            # Base outer circle
            painter.setPen(QPen(QColor(0, 180, 210, 230), 3, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(20, 40, 50, 220)) # Dark translucent vinyl backing
            cx = log_w - 95
            cy = log_h - 95
            painter.drawEllipse(cx, cy, 70, 70)
            
            # Inner circle core text layout
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 210, 255, 240)) # Cyan center punch
            painter.drawEllipse(cx + 8, cy + 8, 54, 54)
            
            font.setFamily("Arial")
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(cx + 11, cy + 40, "PASSED")
            
            painter.setBrush(Qt.NoBrush)
            painter.setPen(Qt.NoPen)

        elif selected_effect == "found footage":
            painter.setPen(QPen(QColor(255, 255, 255, int(intensity * 3)), 1, Qt.PenStyle.DashLine))
            for _ in range(max(1, int(intensity / 6))):
                my = random.randint(0, h)
                painter.drawLine(random.randint(5, 30), my, w - random.randint(5, 30), my)
            
            tape_tint = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.2)
            tape_tint.setColorAt(0.0, QColor(0, 0, 0, 0))
            tape_tint.setColorAt(1.0, QColor(20, 35, 15, int(100 + intensity * 4)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(tape_tint)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "smoke curls":
            log_w = log_w
            log_h = log_h
            
            painter.setPen(Qt.NoPen)

            
            # Determine how many plumes rise from the floor based on slider intensity
            plume_count = max(2, int(intensity / 4))
            
            for i in range(plume_count):
                # 1. Anchor the starting origin point firmly to the bottom floor line
                floor_x = int((log_w / (plume_count + 1)) * (i + 1)) + random.randint(-30, 30)
                
                # Randomized wave values so each plume curls uniquely
                wave_speed = random.uniform(0.03, 0.06)
                wave_amplitude = random.uniform(25.0, 50.0)
                wave_phase = random.uniform(0.0, 10.0)
                
                # 2. CLIMB FROM FLOOR UPWARD (Step sequentially from log_h down to 0)
                # Climb in increments of 6 pixels to create a fluid, continuous trail of rounded curls
                for y in range(log_h, 0, -6):
                    # Standard vertical dissipation math: calculate height fraction (0.0 at floor, 1.0 at top)
                    height_pct = (log_h - y) / float(log_h)
                    
                    # 3. MATHEMATICAL SINE-WAVE CURLING
                    # As y climbs upward, this forces the horizontal position to swing smoothly left and right
                    curl_offset = math.sin(y * wave_speed + wave_phase) * wave_amplitude
                    
                    # Add a gradual wind drift to the side as the plume gets higher
                    drift_offset = height_pct * 40.0 * (1.0 if i % 2 == 0 else -1.0)
                    
                    current_x = floor_x + curl_offset + drift_offset
                    
                    # 4. VOLUMETRIC PUFF SCALING
                    # Smoke starts narrow at the floor source, swells in the mid-air heat currents, and thins out at the top
                    if height_pct < 0.2:
                        puff_size = int(12 + (height_pct * 5.0) * 15) # Expanding out from the floor
                    else:
                        puff_size = int(42 * (1.0 - height_pct * 0.7)) # Gradually shrinking/dissipating as it vanishes
                        
                    if puff_size <= 2:
                        continue
                        
                    # 5. DISSIPATING VERTICAL ALPHA FADE
                    # Smoke is thickest near the floor and completely dissolves to 0 alpha before exiting the upper window frame
                    base_alpha = int(intensity * 3.5)
                    current_alpha = int(base_alpha * (1.0 - height_pct))
                    current_alpha = max(0, min(current_alpha, 255))
                    
                    # Soft, misty white/grey color tone
                    painter.setBrush(QColor(235, 238, 245, current_alpha))
                    
                    # Stamp the rounded curl element onto the graphics thread
                    painter.drawEllipse(int(current_x - puff_size / 2), y, puff_size, puff_size)
                    
            painter.setBrush(Qt.NoBrush)

        elif selected_effect == "halo godlight":

            god_light = QLinearGradient(w / 2.0, 0, w / 2.0, h)
            god_light.setColorAt(0.0, QColor(255, 255, 240, int(intensity * 7))) 
            god_light.setColorAt(0.5, QColor(255, 250, 220, int(intensity * 3))) 
            god_light.setColorAt(1.0, QColor(255, 255, 255, 0))               
            painter.setPen(Qt.NoPen)
            painter.setBrush(god_light)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "x-ray view":
            log_w = log_w
            log_h = log_h
            
            painter.fillRect(0, 0, log_w, log_h, QColor(10, 20, 30, 200))

            
            # Radiant inverted medical skeletal neon outline overlay
            painter.setPen(QPen(QColor(0, 210, 255, 140), 2, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(20, 20, log_w - 40, log_h - 40)
            
            # Subtle medical scanning grid mesh matrix
            painter.setPen(QPen(QColor(0, 210, 255, 15), 1, Qt.PenStyle.SolidLine))
            for y in range(0, log_h, 30):
                painter.drawLine(0, y, log_w, y)

        elif selected_effect == "80s tube television":
            log_w = log_w
            log_h = log_h
            
            painter.fillRect(0, 0, log_w, log_h, QColor(25, 30, 35, int(30 + intensity * 1.5)))
            
            # 2. DRAW COARSE HORIZONTAL PHOSPHOR RASTER SCAN LINES
            painter.setPen(QPen(QColor(0, 0, 0, int(60 + intensity * 3.5)), 2, Qt.PenStyle.SolidLine))
            for y in range(0, log_h, 6):
                painter.drawLine(0, y, log_w, y)
                
            # 3. CREATE SOLID OUTER HOUSING BLOCKMASK (Fills absolute corners completely with solid black)
            # Create a dedicated local pixel buffer layer to compute the inverse window punch
            mask_layer = QImage(log_w, log_h, QImage.Format_ARGB32)
            mask_layer.fill(QColor(12, 10, 8, 255)) # Pure solid retro plastic bezel chassis black
            
            mask_painter = QPainter(mask_layer)
            mask_painter.setRenderHint(QPainter.Antialiasing)
            
            # Use hardware slicing to punch the viewing window out of the solid black block
            mask_painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            mask_painter.setBrush(QColor(0, 0, 0, 255))
            mask_painter.setPen(Qt.NoPen)
            
            # INCREASED RADIUS & THICKNESS: Generates heavy 85px curved glass viewport frame
            frame_margin = int(8 + intensity / 2)
            mask_painter.drawRoundedRect(
                frame_margin, frame_margin, 
                log_w - (frame_margin * 2), log_h - (frame_margin * 2), 
                85, 85 # Maximized corner curvature radius to completely replicate 80s bubble glass tubes
            )
            mask_painter.end()
            
            # 4. Project the completed corner-filled bezel mask onto our active rendering thread
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, mask_layer)
            
            # 5. RETRO SCREEN EDGE SHADOW (Gives deep 3D curved tube simulation around margins)
            glare_grad = QRadialGradient(log_w / 2.0, log_h / 2.0, max(log_w, log_h) / 1.3)
            glare_grad.setColorAt(0.0, QColor(0, 0, 0, 0)) # Clean view on center character
            glare_grad.setColorAt(0.7, QColor(0, 0, 0, int(intensity * 1.5))) # Soft screen vignette
            glare_grad.setColorAt(1.0, QColor(0, 0, 0, int(150 + intensity * 3.0))) # Heavy tube frame shadows
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(glare_grad)
            painter.drawRect(0, 0, log_w, log_h)
            painter.setBrush(Qt.NoBrush)

        elif selected_effect == "crime scene":
            log_w = log_w
            log_h = log_h
            
            thick = int(32 + intensity / 2)

            pad = thick + 12
            
            # 1. Draw solid forensic warning yellow caution ribbon base frame
            painter.setPen(QPen(QColor(245, 210, 0, 255), thick, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(thick / 2), int(thick / 2), log_w - thick, log_h - thick)
            
            # 2. DRAW TEXTBOOK HAZARD LINES WRAPPING ALL 4 SIDES
            painter.setPen(QPen(QColor(15, 15, 15, 180), 3, Qt.PenStyle.SolidLine))
            
            # Top and Bottom tape lines hash markings loop
            for x in range(0, log_w, 35):
                painter.drawLine(x, 0, x + 15, thick) # Top edge hashes
                painter.drawLine(x, log_h - thick, x + 15, log_h) # Bottom edge hashes
                
            # Left and Right tape lines hash markings loop
            for y in range(0, log_h, 35):
                painter.drawLine(0, y, thick, y + 15) # Left edge hashes
                painter.drawLine(log_w - thick, y, log_w, y + 15) # Right edge hashes

            # 3. DRAW "CRIME SCENE" WARNING STRINGS REPETITIVELY AROUND THE RECTANGLE
            font = painter.font()
            font.setFamily("Arial Black" if sys.platform == "win32" else "sans-serif")
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(QColor(15, 15, 15, 240)) # Clear black text stamping
            
            # Horizontal Text tracks (Top & Bottom Tape paths)
            text_spacing = 220
            for tx in range(40, log_w - 100, text_spacing):
                painter.drawText(tx, int(thick * 0.65), "CRIME SCENE - DO NOT CROSS")
                painter.drawText(tx, log_h - int(thick * 0.35), "CRIME SCENE - DO NOT CROSS")
                
            # Vertical Text tracks (Left & Right Tape paths using painter rotation tracking)
            for ty in range(60, log_h - 100, text_spacing):
                # Left tape vertical text
                painter.save()
                painter.translate(int(thick * 0.65), ty)
                painter.rotate(90)
                painter.drawText(0, 0, "CRIME SCENE")
                painter.restore()
                
                # Right tape vertical text
                painter.save()
                painter.translate(log_w - int(thick * 0.35), ty)
                painter.rotate(90)
                painter.drawText(0, 0, "CRIME SCENE")
                painter.restore()

            # 4. CUSTOM DATA MARKER BOX ("custom words")
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(245, 210, 0, 240))
            painter.drawRect(pad, log_h - pad - 30, 200, 30)
            
            font.setFamily("Arial")
            font.setPointSize(12)
            painter.setFont(font)
            painter.setPen(QColor(15, 15, 15, 230))
            painter.drawText(pad + 8, log_h - pad - 10, " Detective MH2 Creator")
            
            painter.setBrush(Qt.NoBrush)
            painter.setPen(Qt.NoPen)

        elif selected_effect == "mugshot":
            log_w = log_w
            log_h = log_h
            
            font = painter.font()

            font.setFamily("monospace")
            font.setBold(True)
            font.setPointSize(10)
            painter.setFont(font)
            
            # This counts your absolute increments starting from a base line of 5 feet
            total_inches = 0
            
            # Step up sequentially from near the floor bounds up toward the ceiling layout
            for y in range(int(log_h * 0.85), int(log_h * 0.15), -20):
                painter.setPen(QPen(QColor(40, 40, 40, int(70 + intensity * 4.0)), 1, Qt.PenStyle.SolidLine))
                painter.drawLine(0, y, log_w, y)
                
                # --- TRUE PROPER ROLLOVER MATH CONVERSION ---
                # floor division: figures out how many additional feet are in our inches pile
                calculated_feet = 5 + (total_inches // 12)
                # modulo: extracts the remainder left over for the inches reading
                remaining_inches = total_inches % 12
                
                # Formats the string cleanly so it reads like a real booking lineup wall
                height_str = f"{calculated_feet}' {remaining_inches}\""
                
                painter.setPen(QPen(QColor(30, 30, 30, 220)))
                # Print symmetrically on both outer margins
                painter.drawText(15, y - 4, height_str)
                painter.drawText(log_w - 60, y - 4, height_str)
                
                total_inches += 1

        elif selected_effect == "model portfolio":
            log_w = log_w
            log_h = log_h
            
            thick = int(12 + intensity / 2)

            painter.setPen(QPen(QColor(255, 255, 255, 255), thick, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(thick / 2), int(thick / 2), log_w - thick, log_h - thick)
            
            # Print elegant editorial typography overlay strings over the view boundaries
            font = painter.font()
            font.setFamily("serif")
            font.setBold(True)
            font.setPointSize(26)
            painter.setFont(font)
            painter.setPen(QColor(20, 20, 20, 240))
            painter.drawText(thick + 15, thick + 35, "Fashion Magazine")
            
            font.setFamily("sans-serif")
            font.setPointSize(9)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(thick + 17, thick + 55, "SPRING / SUMMER 2026")

        elif selected_effect == "lighting energy":
            log_w = log_w
            log_h = log_h
            
            energy = QRadialGradient(log_w / 2.0, log_h / 2.0, max(log_w, log_h) / 1.3)

            energy.setColorAt(0.0, QColor(0, 255, 200, 0)) 
            energy.setColorAt(0.6, QColor(0, 180, 255, int(intensity * 3.0)))  
            energy.setColorAt(0.9, QColor(140, 0, 255, int(intensity * 4.5))) 
            energy.setColorAt(1.0, QColor(255, 0, 100, int(intensity * 5.0))) 
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(energy)
            painter.drawRect(0, 0, log_w, log_h)

        elif selected_effect == "hearts valentine":
            log_w = log_w
            log_h = log_h
            
            pink_glow = QRadialGradient(log_w / 2.0, log_h / 2.0, max(log_w, log_h) / 1.2)

            pink_glow.setColorAt(0.0, QColor(0, 0, 0, 0))
            pink_glow.setColorAt(1.0, QColor(255, 100, 150, int(80 + intensity * 4.0))) 
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(pink_glow)
            painter.drawRect(0, 0, log_w, log_h)
            
            # Scatter high-fidelity geometric 3D pop hearts around margins
            for i in range(int(intensity * 1.5)):
                hx = random.choice([random.randint(30, 140), random.randint(max(40, log_w - 160), max(50, log_w - 40))])
                hy = random.randint(30, max(40, log_h - 50))
                
                size = 18
                
                # ==========================================
                # PASS 1: DRAW DEEP 3D SOFT DROP SHADOWS
                # ==========================================
                painter.save()
                # Shift shadow tracking matrix slightly down and right (+3px)
                painter.translate(hx + int(size / 2) + 3, hy + int(size / 2) + 3)
                painter.rotate(45)
                
                painter.setBrush(QColor(15, 5, 10, 110)) # Translucent dark silhouette shadow
                painter.drawRect(int(-size / 2), int(-size / 2), size, size)
                painter.drawEllipse(int(-size / 2), -size, size, size)
                painter.drawEllipse(-size, int(-size / 2), size, size)
                painter.restore()

                # ==========================================
                # PASS 2: DRAW MAIN VOLUMETRIC HEART BODY
                # ==========================================
                painter.save()
                painter.translate(hx + int(size / 2), hy + int(size / 2))
                painter.rotate(45)
                
                painter.setBrush(QColor(255, 35, 85, 230)) # Vivid Valentine Red Core
                painter.drawRect(int(-size / 2), int(-size / 2), size, size)
                painter.drawEllipse(int(-size / 2), -size, size, size)
                painter.drawEllipse(-size, int(-size / 2), size, size)
                painter.restore()

                # ==========================================
                # PASS 3: LAYER SPEGULAR GLOSS HIGHLIGHTS (POP EFFECT)
                # ==========================================
                # Add tiny pure-white reflection circles onto the upper left rounding lobe areas
                painter.setBrush(QColor(255, 255, 255, 210))
                # Left lobe spec point
                painter.drawEllipse(hx + int(size * 0.15), hy - int(size * 0.2), 4, 4)
                # Right lobe spec point
                painter.drawEllipse(hx + int(size * 0.65), hy - int(size * 0.2), 4, 4)
                
            painter.setBrush(Qt.NoBrush)


        elif selected_effect == "clouds layer":
            # REPAIRED: Reads dimensions from parameters instead of None label
            log_w = log_w
            log_h = log_h
            
            painter.setPen(Qt.NoPen)
           
            # --- CLOUD STAMP INNER FUNCTION ---
            def draw_fluffy_cloud(px, py, base_size):
                """Draws an organic, layered pictorial cloud puff with soft light modeling."""
                # Layer 1: Soft deep atmospheric mist drop shadow base
                painter.setBrush(QColor(180, 195, 210, int(intensity * 2.5)))
                painter.drawEllipse(px - 10, py + 10, int(base_size * 1.4), int(base_size * 0.9))
                
                # Layer 2: Main dense cloud body
                painter.setBrush(QColor(240, 245, 250, int(intensity * 4.5)))
                painter.drawEllipse(px, py, int(base_size * 1.2), int(base_size * 0.8))
                
                # Layer 3: Overlapping fluffy center puffs for organic texture
                painter.drawEllipse(px + int(base_size * 0.3), py - int(base_size * 0.2), int(base_size * 0.7), int(base_size * 0.7))
                painter.drawEllipse(px + int(base_size * 0.6), py + int(base_size * 0.1), int(base_size * 0.6), int(base_size * 0.6))
                
                # Layer 4: Pure white illuminated silver-lining highlight rim
                painter.setBrush(QColor(255, 255, 255, int(intensity * 6.0)))
                painter.drawEllipse(px + int(base_size * 0.1), py - int(base_size * 0.1), int(base_size * 0.5), int(base_size * 0.5))

            # --- CORNER DEPLOYMENT ENGINE ---
            # Distribute thick cloud banks around the frame edges, keeping the center clear
            cloud_intensity_count = int(intensity * 1.2)
            
            for _ in range(cloud_intensity_count):
                size = random.randint(120, 260) # Large, thick pictorial puffs
                
                # Randomly assign clouds to the outer margins of the 4 quadrants
                quadrant = random.choice(["top_left", "top_right", "bottom_left", "bottom_right", "bottom_rim"])
                
                if quadrant == "top_left":
                    draw_fluffy_cloud(random.randint(-50, 120), random.randint(-50, 80), size)
                elif quadrant == "top_right":
                    draw_fluffy_cloud(random.randint(log_w - 280, log_w), random.randint(-50, 80), size)
                elif quadrant == "bottom_left":
                    draw_fluffy_cloud(random.randint(-50, 120), random.randint(log_h - 220, log_h), size)
                elif quadrant == "bottom_right":
                    draw_fluffy_cloud(random.randint(log_w - 280, log_w), random.randint(log_h - 220, log_h), size)
                elif quadrant == "bottom_rim":
                    # Spreads thick sweeping ground fog puffs across the lower viewport canvas
                    draw_fluffy_cloud(random.randint(50, log_w - 200), random.randint(log_h - 130, log_h), size)

            # --- SOFT ATMOSPHERIC SKY VIGNETTE TINT ---
            # Softly blends the background to make the pictorial framing look natural
            sky_glow = QRadialGradient(log_w / 2.0, log_h / 2.0, max(log_w, log_h) / 1.2)
            sky_glow.setColorAt(0.0, QColor(0, 0, 0, 0)) # Clear focus zone
            sky_glow.setColorAt(0.75, QColor(225, 235, 245, int(intensity * 1.2))) # Soft sky wash
            sky_glow.setColorAt(1.0, QColor(190, 210, 230, int(intensity * 3.5)))  # Overcast vignette edges
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(sky_glow)
            painter.drawRect(0, 0, log_w, log_h)
            
            painter.setBrush(Qt.NoBrush)

        elif selected_effect == "psychedelic":
            psy_grad = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.5)
            psy_grad.setColorAt(0.0, QColor(255, 0, 240, int(intensity * 6)))  
            psy_grad.setColorAt(0.3, QColor(0, 255, 255, int(intensity * 4)))  
            psy_grad.setColorAt(0.6, QColor(255, 255, 0, int(intensity * 5)))  
            psy_grad.setColorAt(1.0, QColor(120, 0, 255, int(intensity * 6)))  
            painter.setPen(Qt.NoPen)
            painter.setBrush(psy_grad)
            painter.drawRect(0, 0, w, h)

