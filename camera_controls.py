"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Camera Controls V4.0(presets seperated/.py) - Formerly Zoom Patch- Cinematic Filters, overlays & Camera Presets
    Plus Box/marqee zoom
"""
import sys
import os
import math
import random
import importlib.util
from math import pi as M_PI

from PySide6.QtCore import Qt, QPoint, QObject, QEvent, QRect, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QRubberBand, QComboBox, QDockWidget, QSlider)
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor, QRadialGradient, QPen

from . import math_presets

class CameraFXProcessor:
    """Core graphic processor routing interface."""
    @staticmethod
    def draw_effect(painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio, config=None):
        math_presets.CameraFXProcessor.draw_effect(
            painter, src, w, h, intensity, selected_effect, log_w, log_h, pixel_ratio, config
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

    def __init__(self, glob, plugin, parent=None):
        super().__init__(parent)
        self.active = False
        self.glob = glob
        self.plugin = plugin
        self.glWindow = self.glob.openGLWindow
        self.camera = self.glWindow.camera
        self.start_pos = QPoint()
        self.rubber_band = None

    def eventFilter(self, obj, event):
        if not obj or not hasattr(obj, 'metaObject') or not obj.metaObject():
            return False

        # only work for OpenGLView, otherwise return to normal event dispatching
        #
        class_name = obj.metaObject().className()
        if class_name != "OpenGLView":
            return super().eventFilter(obj, event)

        if event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.Wheel]:
            if self.plugin.filter_overlay_label and not self.plugin.filter_overlay_label.isHidden():
                self.plugin.filter_overlay_label.clear()
                self.plugin.panel.fx_dropdown.setCurrentText("None")

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
                apply_box_zoom(self.camera, self.start_pos.x(), self.start_pos.y(), end_point.x(), end_point.y())
                obj.update()
                return True

        elif event.type() == QEvent.Paint:
            result = super().eventFilter(obj, event)
            
            # Dynamically force both transparent sheets to stretch to 100% of the active window space
            if self.plugin.filter_overlay_label and self.plugin.filter_overlay_label.isVisible():
                # Force alignment map to match obj.width() and obj.height() live!
                self.plugin.filter_overlay_label.setGeometry(0, 0, obj.width(), obj.height())
                self.plugin.filter_overlay_label.raise_()
                
            if self.plugin.filter_png_label and self.plugin.filter_png_label.isVisible():
                self.plugin.filter_png_label.setGeometry(0, 0, obj.width(), obj.height())
                self.plugin.filter_png_label.raise_()
                
            return result


        return super().eventFilter(obj, event)

# ======================================================
# CONTROL PANEL WITH IMAGE DROPDOWN AND EFFECT SLIDERS
# ======================================================

class CameraPlugin(QWidget):
    def __init__(self, app_reference, glob_reference, pluginname):
        super().__init__()
        self.glob = glob_reference
        self.mh_app = app_reference
        self.pluginname = pluginname
        self.mainwindow = self.glob.MainWindow      # simplify access to mainwindow, openGLWindow and camera
        self.glWindow = self.glob.openGLWindow
        self.camera = self.glWindow.camera
        self.repo = self.glob.pluginRepo
        self.env = self.glob.env

        plugin_dir = os.path.dirname(os.path.abspath(__file__)) # self directory
        self.filters_dir = os.path.join(plugin_dir, "filters")
        self.effects_dir = os.path.join(plugin_dir, "effects")

        self.dock = None
        self.panel = None
        self.filter_overlay_label = None
        self.filter_png_label = None

    class Panel(QWidget):
        def __init__(self, parent, glob, target_interceptor=None):
            super().__init__()
            self.glob = glob
            self.interceptor = target_interceptor
            self.setObjectName("CinematicPresetsUI")
        
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
        
            dynamic_filters = ["None"]
            if os.path.exists(parent.filters_dir):
                dynamic_filters += sorted([f for f in os.listdir(parent.filters_dir) if f.lower().endswith('.png')])
            
            self.filter_dropdown.addItems(dynamic_filters)
            self.filter_dropdown.currentTextChanged.connect(parent.execute_render_filter_change)
            layout.addWidget(self.filter_dropdown)
            layout.addSpacing(4)

            # 2. Dynamic Shader Engine Options
            fx_section_title = QLabel("Dynamic Lens Shader Engine:")
            fx_section_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #E0E0E0; margin-top: 5px;")
            layout.addWidget(fx_section_title)

            self.fx_dropdown = QComboBox()
        
            # --- DYNAMIC PYTHON SHADER MOD SCANNER ---
        
            self.dynamic_effects_registry = {}
            dropdown_options = ["None"]
        
            if os.path.exists(parent.effects_dir):
                for filename in sorted(os.listdir(parent.effects_dir)):
                    # Dynamically discover any standalone script file while bypassing structural systems
                    if filename.lower().endswith('.py') and filename != "__init__.py":
                        file_path = os.path.join(parent.effects_dir, filename)
                        module_name = f"runtime_fx_{filename[:-3]}"
                        # print("Modulename:", module_name)
                    
                        try:
                            # Compile and map the independent module straight into memory
                            spec = importlib.util.spec_from_file_location(module_name, file_path)
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)

                            # Grab the target screen identity row declared inside the mod
                            effect_name = getattr(mod, "NAME", filename[:-3])
                            # print("Effectname:", effect_name)
                        
                            self.dynamic_effects_registry[effect_name] = mod
                            dropdown_options.append(effect_name)
                        except Exception as e:
                            self.glob.logLine(2, f"Camera UI: Skipped broken module script {filename}: {e}")
            else:
                self.glob.logLine(2,f"Camera UI Warning: 'effects' folder not found at: {effects_dir}")
            
            self.fx_dropdown.addItems(dropdown_options)
            # --------------------------------------------

            layout.addWidget(self.fx_dropdown)

            # Intensity tuning slider element
            slider_row = QVBoxLayout()
            self.slider_title = QLabel("Effect Intensity Scale: 8")
            self.slider_title.setStyleSheet("font-size: 10px; color: #A0A0A0;")
        
            self.fx_slider = QSlider(Qt.Horizontal)
            self.fx_slider.setMinimum(0)
            self.fx_slider.setMaximum(30)
            self.fx_slider.setValue(8)
            self.fx_slider.valueChanged.connect(parent.update_slider_label_text)
        
            slider_row.addWidget(self.slider_title)
            slider_row.addWidget(self.fx_slider)
            layout.addLayout(slider_row)

            # Action execution button
            apply_fx_btn = QPushButton("Generate Lens Shader Overlay")
            apply_fx_btn.setStyleSheet("font-weight: bold; padding: 4px;")

            apply_fx_btn.clicked.connect(parent.trigger_dynamic_lens_generation)
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
                btn.clicked.connect(lambda checked=False, k=key: parent.execute_preset(k))
                grid.addWidget(btn, r, c)
            
            layout.addLayout(grid)
            layout.addSpacing(6)
        
            reset_btn = QPushButton("Reset Camera View & Clear Overlays")
            reset_btn.clicked.connect(parent.clear_all_and_reset)
            layout.addWidget(reset_btn)
            layout.addStretch()

    def createOverlay(self, name):
        plabel = QLabel(self.glWindow)
        plabel.setObjectName(name)
        plabel.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")
        plabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        plabel.setScaledContents(True)
        plabel.setGeometry(0, 0, self.glWindow.width(), self.glWindow.height())
        plabel.show()
        return plabel

    def deleteOverlay(self, widget):
        if widget is not None:
            widget.close()
            widget.deleteLater()
            widget = None


    def update_slider_label_text(self, value):
        """Updates the interactive scale readout message text string dynamically."""
        self.panel.slider_title.setText(f"Effect Intensity Scale: {value}")

    def trigger_dynamic_lens_generation(self):
        """Generates dynamic post-processing layouts using native high-DPI vector drawing tracks."""

        view = self.glWindow
        
        # 1. Grab selected name exactly as it shows in the dropdown
        selected_effect = self.panel.fx_dropdown.currentText()
        intensity = self.panel.fx_slider.value()

        if selected_effect == "None":
            self.filter_overlay_label.clear()
            return

        # Fetch the loaded executable script module directly from registry memory
        effect_module = self.panel.dynamic_effects_registry.get(selected_effect)
        if not effect_module or not hasattr(effect_module, "draw"):
            self.glob.logLine(1, f"Camera Controls Error: Executable module missing or broken for '{selected_effect}'")
            return

        w, h = self.filter_overlay_label.width(), self.filter_overlay_label.height()
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

        try:
            # Route execution directly into the isolated script's drawing track
            effect_module.draw(painter, src, w, h, intensity, log_w, log_h, pixel_ratio)
        except Exception as e:
            self.glob.logLine(1, f"Camera FX Error: Exception occurred inside module '{selected_effect}': {e}")

        painter.end()
        self.filter_overlay_label.setPixmap(canvas_pixmap)
        self.filter_overlay_label.show()
        self.filter_overlay_label.raise_()
        self.filter_overlay_label.update()

    def execute_preset(self, key):
        """Applies programmatic viewing coordinates and clears temporary shader view surfaces."""

        self.filter_overlay_label.clear()
        self.panel.fx_dropdown.setCurrentText("None")

        math_presets.trigger_cinematic_preset(self.camera, key)
        self.glWindow.update()

    def clear_all_and_reset(self):
        """Resets layout configurations and wipes both surface textures from the viewport tracking window."""
        self.panel.filter_dropdown.setCurrentText("None")
        self.panel.fx_dropdown.setCurrentText("None")

        self.filter_overlay_label.clear()
        self.filter_png_label.clear()
            
        self.execute_preset("reset")

    def execute_render_filter_change(self, filter_text):
        """Loads and updates custom static layout graphics onto the dedicated PNG canvas layer surface."""
            
        name = filter_text.strip()
        if name == "None":
            self.filter_png_label.clear()
            return
            
        texture_path = os.path.join(self.filters_dir, name)
            
        if os.path.exists(texture_path):
            self.filter_png_label.setPixmap(QPixmap(texture_path))
            self.filter_png_label.raise_()


    def shutdown(self):

        self.deleteOverlay(self.filter_overlay_label)
        self.deleteOverlay(self.filter_png_label)

        self.mh_app.removeEventFilter(self.active_filter)
        if self.active_filter.rubber_band:
            self.active_filter.rubber_band.deleteLater()
        self.active_filter = None

        self.panel.close()
        self.panel.deleteLater()
        self.mainwindow.removeDockWidget(self.dock)
        self.dock.close()
        self.dock.deleteLater()
        self.dock = None

    def initialize(self):
        """
        the initialize function for this dock panel
        """
        if self.pluginname in self.repo:
            # if loaded second time
            # Clean up old references just in case
            self.shutdown()

        self.dock = QDockWidget("Camera Controls", self.mainwindow)
        self.dock.setObjectName("camera_controls_dock_widget")
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # create UI
        self.panel = self.Panel(self, self.glob)
        self.dock.setWidget(self.panel)

        if hasattr(self.mainwindow, "addDockWidget"):
            self.mainwindow.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        else:
            self.dock.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.dock.show()

        # create overlays
        #
        self.filter_overlay_label = self.createOverlay("camera_lens_overlay_filter")
        self.filter_png_label = self.createOverlay("camera_png_overlay_filtee")

        # not to work on mainwindow, installEventFilter must be called on QApplication.instance()
        #
        self.active_filter = DynamicInputInterceptor(self.glob, self)
        QApplication.instance().installEventFilter(self.active_filter)

        # now add plugin to repository
        #
        self.repo[self.pluginname] = self
        return True


def load_extension(app, glob):
    """Initializes extension parameters, builds user widgets, and hooks the viewport graphic sheets."""

    glob.env.logLine(1, "[Camera Controls] Executing native decoupled official tool initialization sequence...")

    pluginname = os.path.abspath(__file__)
    plugin = CameraPlugin(app, glob, pluginname)
    return plugin.initialize()

def unload_extension(glob):
    """Unregisters core event handlers, deletes interface widgets, and flushes layer memory structures."""

    pluginname = os.path.abspath(__file__)
    if pluginname in glob.pluginRepo:
        glob.pluginRepo[pluginname].shutdown()
        glob.pluginRepo.pop(pluginname)     # and delete from repo

