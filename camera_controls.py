"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Camera Controls V3.0 - Formerly Zoom Patch- Cinematic Filters, Overlay dropdown, & Camera Presets Plus Box/marqee zoom
"""
import sys
import os
import math
import random
from math import pi as M_PI

from PySide6.QtCore import Qt, QPoint, QObject, QEvent, QRect, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QRubberBand, QComboBox, QDockWidget, QSlider)
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor, QRadialGradient, QPen

_active_filter_instance = None
_ui_panel_instance = None
_dock_container_instance = None  
_filter_overlay_label = None  
_filter_png_label = None  
_saved_app_context = None
_saved_glob_context = None


class CameraFXProcessor:
    """Core graphic processor interface."""
    
    @staticmethod
    def draw_effect(label, effect_type="chromatic aberration", intensity=8):
        pass


def apply_box_zoom(camera, x1, y1, x2, y2):
    """Calculates marquee box zoom vectors utilizing physical display boundaries."""
    box_w = abs(x2 - x1)
    box_h = abs(y2 - y1)
    if box_w < 10 or box_h < 10:
        return

    box_center_x = (x1 + x2) / 2.0
    box_center_y = (y1 + y2) / 2.0
    screen_center_x = camera.view_width / 2.0
    screen_center_y = camera.view_height / 2.0

    if not camera.cameraPers:
        factor = camera.o_height * camera.ortho_magnification
        world_w = (float(camera.view_width) / factor) * 2.0
        world_h = (float(camera.view_height) / factor) * 2.0
    else:
        cam_dist = camera.getCameraDistance()
        v_angle_rad = (camera.verticalAngle * M_PI) / 180.0
        world_h = 2.0 * cam_dist * (v_angle_rad / 2.0)
        world_w = world_h * (float(camera.view_width) / float(camera.view_height))

    dx = ((box_center_x - screen_center_x) / float(camera.view_width)) * world_w
    dy = -((box_center_y - screen_center_y) / float(camera.view_height)) * world_h

    up_vec = camera.view_matrix.transposed().row(1).toVector3D()
    right_vec = camera.getRightVector().normalized()
    translation = (right_vec * dx) + (up_vec.normalized() * dy)
    
    camera.lookAt += translation
    camera.cameraPos += translation

    zoom_factor = min(float(camera.view_width) / box_w, float(camera.view_height) / box_h)

    if not camera.cameraPers:
        new_ortho = camera.ortho_magnification * zoom_factor
        camera.ortho_magnification = max(camera.minOrthoMag, min(new_ortho, camera.maxOrthoMag))
    else:
        cam_dist = camera.getCameraDistance()
        new_dist = max(camera.minDist, min(cam_dist / zoom_factor, camera.maxDist))
        camera.cameraPos = camera.lookAt + (camera.getViewDirection().normalized() * -new_dist)
        camera.cameraDist = new_dist

    camera.updateViewMatrix()
    camera.calculateProjMatrix()

def trigger_cinematic_preset(camera, preset_name):
    """Applies camera positioning matrices and transforms projection fields."""
    if not camera:
        return

    name = preset_name.lower().strip()

    if name in ["ortho", "isometric"]:
        camera.cameraPers = False
    else:
        camera.cameraPers = True

    camera.lookAt.setX(0.0)
    camera.lookAt.setZ(0.0)

    target_rh = 0.0
    target_rv = 0.0
    target_dist = 32.0    
    target_fov = 45.0

    if name == "selfie_left":
        camera.lookAt.setY(5.8); target_fov = 55.0; target_dist = 30.0; target_rh = -38.0; target_rv = -4.0
    elif name == "selfie_right":
        camera.lookAt.setY(5.8); target_fov = 55.0; target_dist = 30.0; target_rh = 38.0; target_rv = -4.0
    elif name == "security_cam_right":
        camera.lookAt.setY(4.8); target_fov = 45.0; target_dist = 110.0; target_rh = 35.0; target_rv = 50.0
    elif name == "security_cam_left":
        camera.lookAt.setY(4.8); target_fov = 45.0; target_dist = 110.0; target_rh = -35.0; target_rv = 50.0
    elif name == "wormsview":
        camera.lookAt.setY(1.5); target_fov = 45.0; target_dist = 45.0; target_rh = 0.0; target_rv = -40.0  
    elif name == "fish eye":
        camera.lookAt.setY(6.95); target_fov = 120.0; target_dist = 4.6; target_rh = 0.0; target_rv = 0.0
    elif name in ["godview", "birdview"]:
        camera.lookAt.setY(4.5); target_fov = 45.0; target_dist = 110.0; target_rh = 0.0; target_rv = 89.9         
    elif name == "ortho":
        camera.lookAt.setY(3.5); camera.ortho_magnification = 2.8; target_dist = 38.0; target_rh = 0.0; target_rv = 0.0
    elif name == "pov":
        camera.lookAt.setY(7.2); camera.lookAt.setZ(1.5); camera.lookAt.setX(0.0); target_fov = 65.0; target_dist = 0.1; target_rh = 180.0; target_rv = 0.0
    elif name == "panoramic":
        camera.lookAt.setZ(0.0); camera.lookAt.setX(0.0); camera.lookAt.setY(4.5); target_fov = 75.0; target_dist = 160.0; target_rh = 0.0; target_rv = 0.0
    elif name == "isometric":
        camera.lookAt.setY(3.8); camera.ortho_magnification = 6.2; target_dist = 45.0; target_rh = 45.0; target_rv = -35.264   
    elif name == "wideshot":
        camera.lookAt.setY(2.5); camera.lookAt.setX(0.0); camera.lookAt.setZ(0.0); target_fov = 50.0; target_dist = 90.0; target_rh = 0.0; target_rv = -12.0
    elif name == "closeup":
        camera.lookAt.setY(6.8); target_fov = 22.0; target_dist = 12.0; target_rh = 0.0; target_rv = 0.0
    elif name == "high angle":
        camera.lookAt.setY(4.5); target_fov = 46.0; target_dist = 25.0; target_rh = 0.0; target_rv = 32.0   
    elif name == "low angle":
        camera.lookAt.setY(6.5); target_fov = 46.0; target_dist = 30.0; target_rh = 0.0; target_rv = -32.0    
    elif name == "eye level":
        camera.lookAt.setY(5.2); target_fov = 38.0; target_dist = 30.0; target_rh = 0.0; target_rv = 0.0
    elif name == "ots_left":
        camera.lookAt.setY(8.0); camera.lookAt.setZ(-4.9); target_fov = 50.0; target_dist = 3.0; target_rh = -165.0; target_rv = 8.0
    elif name == "ots_right":
        camera.lookAt.setY(8.0); camera.lookAt.setZ(-4.9); target_fov = 50.0; target_dist = 3.0; target_rh = 165.0; target_rv = 8.0
    elif name == "mediumshot":
        camera.lookAt.setY(4.5); target_fov = 40.0; target_dist = 48.0; target_rh = 0.0; target_rv = 0.0
    elif name == "fullshot":
        camera.lookAt.setY(1.5); target_fov = 35.0; target_dist = 75.0; target_rh = 0.0; target_rv = 0.0
    elif name == "reset":
        camera.lookAt.setY(1.5); target_fov = 45.0; target_dist = 65.0; target_rh = 0.0; target_rv = 0.0

    if 'target_fov' in locals(): 
        camera.verticalAngle = target_fov
    if 'target_dist' in locals(): 
        camera.cameraDist = target_dist
    if 'target_rh' in locals():
        if hasattr(camera, 'rh_angle'): 
            camera.rh_angle = target_rh
    if 'target_rv' in locals():
        if hasattr(camera, 'rv_angle'): 
            camera.rv_angle = target_rv

    if hasattr(camera, 'updateCameraPosition'): 
        camera.updateCameraPosition()
    elif hasattr(camera, 'update'): 
        camera.update()

    camera.updateViewMatrix()
    camera.calculateProjMatrix()

    if 'target_dist' in locals() and 'target_rh' in locals() and 'target_rv' in locals():
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


class DynamicInputInterceptor(QObject):
    """Monitors layout boundaries, handles marquee marquee zoom transformations, and manages overlay geometry scaling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = False
        self.start_pos = QPoint()
        self.rubber_band = None

    def eventFilter(self, obj, event):
        if not obj or not hasattr(obj, 'metaObject') or not obj.metaObject():
            return False

        class_name = obj.metaObject().className() if obj.metaObject() else ""
        is_canvas = "View3D" in class_name or "Canvas" in class_name or "GL" in class_name or hasattr(obj, 'view_matrix')
        if not is_canvas:
            return super().eventFilter(obj, event)

        global _saved_glob_context, _filter_overlay_label, _ui_panel_instance
        camera = None
        if _saved_glob_context and hasattr(_saved_glob_context, 'openGLWindow'):
            view = _saved_glob_context.openGLWindow
            if view and hasattr(view, 'camera'): 
                camera = view.camera

        if not camera:
            return super().eventFilter(obj, event)

        if event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.Wheel]:
            if _filter_overlay_label and not _filter_overlay_label.isHidden():
                _filter_overlay_label.clear()
                if _ui_panel_instance and hasattr(_ui_panel_instance, 'fx_dropdown'):
                    _ui_panel_instance.fx_dropdown.setCurrentText("None")

        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
                self.active = True
                self.start_pos = event.position().toPoint()
                if not self.rubber_band:
                    self.rubber_band = QRubberBand(QRubberBand.Rectangle, obj)
                self.rubber_band.setGeometry(QRect(self.start_pos, self.start_pos))
                self.rubber_band.show()
                return True

        elif event.type() == QEvent.MouseMove:
            if self.active and self.rubber_band:
                current_point = event.position().toPoint()
                self.rubber_band.setGeometry(QRect(self.start_pos, current_point).normalized())
                return True

        elif event.type() == QEvent.MouseButtonRelease:
            if self.active and event.button() == Qt.LeftButton:
                self.active = False
                if self.rubber_band: 
                    self.rubber_band.hide()
                end_point = event.position().toPoint()
                apply_box_zoom(camera, self.start_pos.x(), self.start_pos.y(), end_point.x(), end_point.y())
                obj.update()
                return True

        elif event.type() == QEvent.Paint:
            result = super().eventFilter(obj, event)
            
            # Dynamically force both transparent sheets to stretch to 100% of the active window space
            if _filter_overlay_label and _filter_overlay_label.isVisible():
                # Force alignment map to match obj.width() and obj.height() live!
                _filter_overlay_label.setGeometry(0, 0, obj.width(), obj.height())
                _filter_overlay_label.raise_()
                
            global _filter_png_label
            if _filter_png_label and _filter_png_label.isVisible():
                _filter_png_label.setGeometry(0, 0, obj.width(), obj.height())
                _filter_png_label.raise_()
                
            return result


        return super().eventFilter(obj, event)

# ======================================================
# CONTROL PANEL WITH IMAGE DROPDOWN AND EFFECT SLIDERS
# ======================================================
class CinematicPresetsUI(QWidget):
    def __init__(self, target_interceptor, parent=None):
        super().__init__(parent)
        self.interceptor = target_interceptor
        self.setObjectName("CinematicPresetsUI")
        global _ui_panel_instance
        _ui_panel_instance = self
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)
        
        title = QLabel("Cinematic Lenses & Framing")
        title.setStyleSheet("font-weight: bold; font-size: 13px; margin: 10px 0px 5px 0px; color: #E0E0E0;")
        layout.addWidget(title)
        
        # 1. Your original Working PNG Dropdown
        filter_label = QLabel("Camera Post-Process Filter (.png):")
        filter_label.setStyleSheet("font-size: 11px; color: #A0A0A0; margin-top: 5px;")
        layout.addWidget(filter_label)
        
        self.filter_dropdown = QComboBox()
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        filters_dir = os.path.join(plugin_dir, "filters")
        
        dynamic_filters = ["None"]
        if os.path.exists(filters_dir):
            dynamic_filters += sorted([f for f in os.listdir(filters_dir) if f.lower().endswith('.png')])
            
        self.filter_dropdown.addItems(dynamic_filters)
        self.filter_dropdown.currentTextChanged.connect(self.execute_render_filter_change)
        layout.addWidget(self.filter_dropdown)
        layout.addSpacing(4)

        # 2. Dynamic Shader Engine Options
        fx_section_title = QLabel("Dynamic Lens Shader Engine:")
        fx_section_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #E0E0E0; margin-top: 5px;")
        layout.addWidget(fx_section_title)

        self.fx_dropdown = QComboBox()
        self.fx_dropdown.addItems([
            "None",
            "1920s Movie",
            "8-Bit Arcade",
            "80s PC Monitor",
            "90s Camcorder",
            "Chromatic Aberration", 
            "Clouds Layer",
            "Comic Book Style",
            "Cyberpunk Terminal",
            "Found Footage",
            "Halo Godlight",
            "Hologram",
            "Instant Photo Border",
            "Mirror Border",
            "Oil Painting",
            "Postcard",
            "Prism Light Leaks",
            "Psychedelic",
            "Rain Drops",
            "Security Cam HUD",
            "Smoke Curls",
            "Stickers Overlay",
            "Thermal Mapping (FLIR)",
            "True Black and White",
            "Vintage Film Noise",
            "Western"
        ])

        layout.addWidget(self.fx_dropdown)

        # Intensity tuning slider element
        slider_row = QVBoxLayout()
        self.slider_title = QLabel("Effect Intensity Scale: 8")
        self.slider_title.setStyleSheet("font-size: 10px; color: #A0A0A0;")
        
        self.fx_slider = QSlider(Qt.Horizontal)
        self.fx_slider.setMinimum(0)
        self.fx_slider.setMaximum(30)
        self.fx_slider.setValue(8)
        self.fx_slider.valueChanged.connect(self.update_slider_label_text)
        
        slider_row.addWidget(self.slider_title)
        slider_row.addWidget(self.fx_slider)
        layout.addLayout(slider_row)

        # Action execution button
        apply_fx_btn = QPushButton("Generate Lens Shader Overlay")
        apply_fx_btn.setStyleSheet("font-weight: bold; padding: 4px;")

        apply_fx_btn.clicked.connect(self.trigger_dynamic_lens_generation)
        layout.addWidget(apply_fx_btn)
        layout.addSpacing(5)

        # 18 Camera Shortcut Button Grid
        grid = QGridLayout()
        grid.setSpacing(4)
        buttons_config = [
            ("Selfie Left", "selfie_left", 0, 0), ("Selfie Right", "selfie_right", 0, 1),
            ("Fish Eye", "fish eye", 1, 0), ("POV", "pov", 1, 1),
            ("Bird's Eye", "godview", 2, 0), ("Ortho", "ortho", 2, 1),
            ("Panoramic", "panoramic", 3, 0), ("Isometric", "isometric", 3, 1),
            ("Wide Shot", "wideshot", 4, 0), ("Close-Up", "closeup", 4, 1),
            ("High Angle", "high angle", 5, 0), ("Low Angle", "low angle", 5, 1),
            ("Eye Level", "eye level", 6, 0), ("Full Shot", "fullshot", 6, 1),
            ("Worm's Eye", "wormsview", 7, 0), ("Medium Shot", "mediumshot", 7, 1),
            ("OTS Left", "ots_left", 8, 0), ("OTS Right", "ots_right", 8, 1),
            ("Security R", "security_cam_right", 9, 0), ("Security L", "security_cam_left", 9, 1)
        ]
        
        for text, key, r, c in buttons_config:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked=False, k=key: self.execute_preset(k))
            grid.addWidget(btn, r, c)
            
        layout.addLayout(grid)
        layout.addSpacing(6)
        
        reset_btn = QPushButton("Reset Camera View & Clear Overlays")
        reset_btn.clicked.connect(self.clear_all_and_reset)
        layout.addWidget(reset_btn)
        layout.addStretch()

    def update_slider_label_text(self, value):
        """Updates the interactive scale readout message text string dynamically."""
        self.slider_title.setText(f"Effect Intensity Scale: {value}")

    def trigger_dynamic_lens_generation(self):
        """Generates dynamic post-processing layouts using native high-DPI vector drawing tracks."""
        global _saved_glob_context, _filter_overlay_label
        if not (_saved_glob_context and hasattr(_saved_glob_context, 'openGLWindow') and _filter_overlay_label):
            return

        view = _saved_glob_context.openGLWindow
        selected_effect = self.fx_dropdown.currentText().lower().strip()
        intensity = self.fx_slider.value()

        if selected_effect == "none":
            _filter_overlay_label.clear()
            return

        w, h = _filter_overlay_label.width(), _filter_overlay_label.height()
        if w <= 0 or h <= 0:
            return

        screenshot = view.grab().toImage() if hasattr(view, "grab") else QImage()
        if screenshot.isNull():
            return

        # --- HIGH-DPI PHYSICAL CANVAS SCALE FIX ---
        pixel_ratio = view.devicePixelRatioF() if hasattr(view, "devicePixelRatioF") else 1.0
        
        # Calculate full physical viewport canvas limits to prevent bottom-right cutting
        phys_w = int(w * pixel_ratio)
        phys_h = int(h * pixel_ratio)
        
        src = screenshot.scaled(phys_w, phys_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        src = src.convertToFormat(QImage.Format_ARGB32)

        canvas_pixmap = QPixmap(phys_w, phys_h)
        canvas_pixmap.setDevicePixelRatio(pixel_ratio)
        canvas_pixmap.fill(Qt.transparent)
        
        painter = QPainter(canvas_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Re-assign limits to full physical pixel resolution values
        w, h = phys_w, phys_h

        # =====================================================================
        # CORE EFFECTS DISPATCH MATRIX
        # =====================================================================
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
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
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
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
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
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
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
            # Read the layout boundaries of the widget container directly
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
            thick = int(12 + intensity / 3)
            pad = thick + 10
            
            painter.setPen(QPen(QColor(240, 230, 200, 220), thick, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.NoBrush)
            
            # Draw the outer rectangle using the true un-scaled logical endpoints
            painter.drawRect(int(thick / 2), int(thick / 2), log_w - thick, log_h - thick)
            
            # Draw the inner pin-stripe using the true un-scaled logical endpoints
            painter.setPen(QPen(QColor(180, 150, 100, 140), 1, Qt.PenStyle.SolidLine))
            painter.drawRect(pad, pad, log_w - (pad * 2), log_h - (pad * 2))


        elif selected_effect == "instant photo border":
            # Map to un-scaled logical footprints to stop content distortion may add note area for text to this one
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(245, 245, 240, 255))
            pad = int(20 + intensity)
            
            painter.drawRect(0, 0, log_w, pad) 
            painter.drawRect(0, 0, pad, log_h) 
            painter.drawRect(log_w - pad, 0, pad, log_h) 
            painter.drawRect(0, log_h - int(pad * 2.8), log_w, int(pad * 2.8))

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
            from PySide6.QtGui import QLinearGradient
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

        elif selected_effect == "rain drops":
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
            # Give the appearance a dark storm tint base layer to make the drops pop
            painter.fillRect(0, 0, log_w, log_h, QColor(15, 25, 35, int(intensity * 1.5)))
            
            from PySide6.QtGui import QLinearGradient
            
            # Populate organic*ish raindrops across the layout surface
            for _ in range(int(intensity * 2.5)):
                rx = random.randint(15, log_w - 15)
                ry = random.randint(15, log_h - 40)
                
                drop_w = random.randint(8, 16)
                drop_h = random.randint(12, 24)
                trail_length = random.randint(30, 90)
                
                # 1. DRAW STREAKS FIRST (Fades out from top to bottom)
                trail_thickness = max(1, int(1 + intensity / 15))
                # Soft vertical fluid gradient tail
                trail_grad = QLinearGradient(rx + int(drop_w / 2), ry, rx + int(drop_w / 2), ry + trail_length)
                trail_grad.setColorAt(0.0, QColor(220, 230, 245, 10))  # Thin top origin point
                trail_grad.setColorAt(0.8, QColor(240, 245, 255, 65))  # Brightens near the droplet base
                trail_grad.setColorAt(1.0, QColor(240, 245, 255, 0))   # Blends out under the drop core
                
                painter.setPen(Qt.NoPen)
                painter.setBrush(trail_grad)
                painter.drawRect(rx + int(drop_w / 2) - int(trail_thickness / 2), ry, trail_thickness, trail_length)
                
                # 2. PLACEMENT CORRECTION: Move the droplet position down to the bottom tip of the streak
                drop_y_base = ry + trail_length - int(drop_h * 0.4)
                
                # 3. DRAW HEAVY DROPLET AT THE BOTTOM OF THE STREAK
                # Outer refractive glass shadow ring
                painter.setBrush(QColor(0, 5, 15, 110))
                painter.drawEllipse(rx + 1, drop_y_base + 1, drop_w, drop_h)
                
                # Rich white fluid highlight reflection body
                painter.setBrush(QColor(235, 242, 255, 175))
                painter.drawEllipse(rx, drop_y_base, drop_w - 1, drop_h - 2)
                
                # Inner organic bead focal point glare
                painter.setBrush(QColor(255, 255, 255, 225))
                painter.drawEllipse(rx + int(drop_w / 3), drop_y_base + 2, int(drop_w / 3), int(drop_h / 4))
                
                painter.setBrush(Qt.NoBrush)


        elif selected_effect == "mirror border":
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
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
            #This is to show what is possible, can really do a lot here
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
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
            #Attention devs this one needs work but looks reasonable already
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
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
            from PySide6.QtGui import QLinearGradient
            god_light = QLinearGradient(w / 2.0, 0, w / 2.0, h)
            god_light.setColorAt(0.0, QColor(255, 255, 240, int(intensity * 7))) 
            god_light.setColorAt(0.5, QColor(255, 250, 220, int(intensity * 3))) 
            god_light.setColorAt(1.0, QColor(255, 255, 255, 0))               
            painter.setPen(Qt.NoPen)
            painter.setBrush(god_light)
            painter.drawRect(0, 0, w, h)

        elif selected_effect == "clouds layer":
            #Attention devs this one needs work but looks reasonable already
            log_w = _filter_overlay_label.width()
            log_h = _filter_overlay_label.height()
            
            painter.setPen(Qt.NoPen)
            
            # --- PICTORIAL CLOUD STAMP INNER FUNCTION ---
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

        painter.end()
        _filter_overlay_label.setPixmap(canvas_pixmap)
        _filter_overlay_label.show()
        _filter_overlay_label.raise_()
        _filter_overlay_label.update()

    def execute_preset(self, key):
        """Applies programmatic viewing coordinates and clears temporary shader view surfaces."""
        global _saved_glob_context, _filter_overlay_label
        if _saved_glob_context and hasattr(_saved_glob_context, 'openGLWindow'):
            view = _saved_glob_context.openGLWindow
            if view and hasattr(view, 'camera'):
                if _filter_overlay_label:
                    _filter_overlay_label.clear()
                self.fx_dropdown.setCurrentText("None")
                
                trigger_cinematic_preset(view.camera, key)
                view.update()

    def clear_all_and_reset(self):
        """Resets layout configurations and wipes both high-DPI surface textures from the viewport tracking window."""
        self.filter_dropdown.setCurrentText("None")
        self.fx_dropdown.setCurrentText("None")
        
        global _filter_overlay_label, _filter_png_label
        if _filter_overlay_label:
            _filter_overlay_label.clear()
        if _filter_png_label:
            _filter_png_label.clear()
            
        self.execute_preset("reset")

    def execute_render_filter_change(self, filter_text):
        """Loads and updates custom static layout graphics onto the dedicated PNG canvas layer surface."""
        global _filter_png_label
        if _filter_png_label is None:
            return
            
        name = filter_text.strip()
        if name == "None":
            _filter_png_label.clear()
            return
            
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        texture_path = os.path.join(plugin_dir, "filters", name)
            
        if os.path.exists(texture_path):
            _filter_png_label.setPixmap(QPixmap(texture_path))
            _filter_png_label.raise_()


def load_extension(app, glob):
    """Initializes extension parameters, builds user widgets, and hooks the twin high-DPI viewport graphic sheets."""
    global _active_filter_instance, _ui_panel_instance, _dock_container_instance
    global _filter_overlay_label, _filter_png_label, _saved_app_context, _saved_glob_context
    
    _saved_app_context = QApplication.instance() or app
    _saved_glob_context = glob
    
    if _saved_app_context and _active_filter_instance is None:
        _active_filter_instance = DynamicInputInterceptor()
        _saved_app_context.installEventFilter(_active_filter_instance)
        
        view = None
        main_window = None
        for widget in _saved_app_context.topLevelWidgets():
            if isinstance(widget, QMainWindow) or str(widget.objectName()).lower() == "mainwindow":
                main_window = widget
                break

        if hasattr(glob, 'openGLWindow') and glob.openGLWindow:
            view = glob.openGLWindow
        elif main_window:
            for child in main_window.findChildren(QWidget):
                if hasattr(child, 'camera') and hasattr(child, 'light'):
                    view = child
                    break

        if view and _filter_overlay_label is None:
            _filter_overlay_label = QLabel(view)
            _filter_overlay_label.setObjectName("camera_lens_overlay_filter")
            _filter_overlay_label.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")
            _filter_overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            _filter_overlay_label.setScaledContents(True)
            _filter_overlay_label.setGeometry(0, 0, view.width(), view.height())
            _filter_overlay_label.show()

        if view and _filter_png_label is None:
            _filter_png_label = QLabel(view)
            _filter_png_label.setObjectName("camera_png_overlay_filter")
            _filter_png_label.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")
            _filter_png_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            _filter_png_label.setScaledContents(True)
            _filter_png_label.setGeometry(0, 0, view.width(), view.height())
            _filter_png_label.show()

        _ui_panel_instance = CinematicPresetsUI(_active_filter_instance)

        if main_window:
            _dock_container_instance = QDockWidget("Camera Controls", main_window)
            _dock_container_instance.setObjectName("camera_controls_dock_widget")
            _dock_container_instance.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            _dock_container_instance.setWidget(_ui_panel_instance)
            main_window.addDockWidget(Qt.RightDockWidgetArea, _dock_container_instance)
            _dock_container_instance.show()
        else:
            _ui_panel_instance.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            _ui_panel_instance.show()
        
    return {"status": "camera_controls_active"}

def unload_extension():
    """Unregisters core event handlers, deletes interface widgets, and flushes layer memory structures."""
    global _active_filter_instance, _ui_panel_instance, _dock_container_instance
    global _filter_overlay_label, _filter_png_label, _saved_app_context, _saved_glob_context
    qt_app = QApplication.instance() or _saved_app_context
    
    if qt_app and _active_filter_instance is not None:
        qt_app.removeEventFilter(_active_filter_instance)
        if _active_filter_instance.rubber_band:
            _active_filter_instance.rubber_band.deleteLater()
        _active_filter_instance = None
        
    if _dock_container_instance is not None:
        _dock_container_instance.close()
        _dock_container_instance.deleteLater()
        _dock_container_instance = None

    if _ui_panel_instance is not None:
        _ui_panel_instance.close()
        _ui_panel_instance.deleteLater()
        _ui_panel_instance = None
        
    if _filter_overlay_label is not None:
        _filter_overlay_label.close()
        _filter_overlay_label.deleteLater()
        _filter_overlay_label = None
        
    if _filter_png_label is not None:
        _filter_png_label.close()
        _filter_png_label.deleteLater()
        _filter_png_label = None
        
    _saved_app_context = None
    _saved_glob_context = None
    print("[Camera Controls] Extension successfully unloaded and memory cleared.")
