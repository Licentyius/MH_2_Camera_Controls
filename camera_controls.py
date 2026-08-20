"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Camera Controls V3.5(presets seperated) - Formerly Zoom Patch- Cinematic Filters, overlays & Camera Presets Plus Box/marqee zoom
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
    """Core graphic processor routing interface."""
    @staticmethod
    def draw_effect(painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio):
        import math_presets
        math_presets.CameraFXProcessor.draw_effect(
            painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio
        )


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
        
        # 1. PNG Dropdown
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
            "80s Tube Television",
            "90s Camcorder",
            "Chromatic Aberration", 
            "Clouds Layer",
            "Comic Book Style",
            "Crime Scene",
            "Cyberpunk Terminal",
            "Found Footage",
            "Halo Godlight",
            "Hearts Valentine",
            "Hologram",
            "Instant Photo Border",
            "Lighting Energy",
            "Mirror Border",
            "Model Portfolio",
            "Mugshot",
            "Oil Painting",            
            "Postcard",
            "Prism Light Leaks",
            "Psychedelic",
            "Raindrops",
            "Security Cam HUD",
            "Smoke Curls",
            "Stickers Overlay",
            "Thermal Mapping (FLIR)",
            "True Black and White",
            "Vintage Film Noise",
            "Western",
            "X-Ray View"
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

        pixel_ratio = view.devicePixelRatioF() if hasattr(view, "devicePixelRatioF") else 1.0
        
        phys_w = int(w * pixel_ratio)
        phys_h = int(h * pixel_ratio)
        
        src = screenshot.scaled(phys_w, phys_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        src = src.convertToFormat(QImage.Format.Format_ARGB32)

        canvas_pixmap = QPixmap(phys_w, phys_h)
        canvas_pixmap.setDevicePixelRatio(pixel_ratio)
        canvas_pixmap.fill(Qt.transparent)
        
        painter = QPainter(canvas_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        log_w = w
        log_h = h
        w, h = phys_w, phys_h

        # Route out rendering directly to the split file class
        CameraFXProcessor.draw_effect(
            painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio
        )

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
                
                # Routes out to separated configuration file
                import math_presets
                math_presets.trigger_cinematic_preset(view.camera, key)
                view.update()

    def clear_all_and_reset(self):
        """Resets layout configurations and wipes both surface textures from the viewport tracking window."""
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
    """Initializes extension parameters, builds user widgets, and hooks the viewport graphic sheets."""
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

