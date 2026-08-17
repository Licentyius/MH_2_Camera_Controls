"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Camera Controls V2.5 - Formerly Zoom Patch- Cinematic Filters & Camera Presets Plus Box/marqee zoom
"""
from PySide6.QtCore import Qt, QPoint, QObject, QEvent, QRect, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QRubberBand, QComboBox, QDockWidget)

_active_filter_instance = None
_ui_panel_instance = None
_filter_overlay_label = None  
_saved_app_context = None
_saved_glob_context = None

import sys
import os
import math

from math import pi as M_PI


def apply_box_zoom(camera, x1, y1, x2, y2):
    """Calculates box zooming dimensions based on screen coordinates."""
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
    """
    Forces stable cinematic layout adjustments calibrated for MH2 Decimeter units.
    Ensures precise framing across all perspectives without clipping.
    """
    if not camera:
        return

    name = preset_name.lower().strip()

    if name in ["ortho", "isometric"]:
        camera.cameraPers = False
    else:
        camera.cameraPers = True

    # Lock core X and Z anchor vectors to keep the character centered
    camera.lookAt.setX(0.0)
    camera.lookAt.setZ(0.0)

    # ===================================================================
    # DECIMETER ANATOMICAL TARGET HEIGHTS (1 unit = 10cm)
    # Based on an average character height of 17.0 decimeters (~1.7m)
    # ===================================================================
    head_height = 16.2    # Target eyes/face center line precisely
    chest_height = 13.5   # Target center line for upper body framing
    mid_height = 8.5      # Target exact mid-torso center balance point

    # Default fallback properties
    target_rh = 0.0
    target_rv = 0.0
    target_dist = 32.0    # Balanced default tracking baseline (~3.2 meters)
    target_fov = 45.0

    # ============================
    # DETAILED CINEMATIC PRESETS
    # ============================
    if name == "selfie_left":
        camera.lookAt.setY(5.8)
        target_fov = 55.0
        target_dist = 30.0   
        target_rh = -38.0
        target_rv = -4.0

    elif name == "selfie_right":
        camera.lookAt.setY(5.8)
        target_fov = 55.0
        target_dist = 30.0   
        target_rh = 38.0
        target_rv = -4.0

    elif name == "wormsview":
        camera.lookAt.setY(1.5)
        
        target_fov = 45.0
        target_dist = 45.0   
        
        target_rh = 0.0

        target_rv = -40.0  

    elif name == "fish eye":
        # nose cam-Target the nose line height to center the lens right over the face
        camera.lookAt.setY(6.95)
        
        # Open the lens field wide to maximize the dramatic warping effect
        target_fov = 120.0          
        target_dist = 4.6              
        target_rh = 0.0
        target_rv = 0.0

    elif name in ["godview", "birdview"]:
        # Look directly down at the middle core mass height
        camera.lookAt.setY(4.5)
        
        target_fov = 45.0
        target_dist = 110.0               
        target_rh = 0.0
        target_rv = 89.9         

    elif name == "ortho":
        camera.lookAt.setY(3.5)
        camera.ortho_magnification = 2.8 
        target_dist = 38.0
        target_rh = 0.0
        target_rv = 0.0

    elif name == "pov":
        camera.lookAt.setY(7.2)
        camera.lookAt.setZ(1.5)
        camera.lookAt.setX(0.0)
        target_fov = 65.0
        target_dist = 0.1     
        target_rh = 180.0
        target_rv = 0.0

    elif name == "panoramic":
        camera.lookAt.setZ(0.0)
        camera.lookAt.setX(0.0)
        camera.lookAt.setY(4.5)
        target_fov = 75.0     
        target_dist = 160.0    
        target_rh = 0.0
        target_rv = 0.0

    elif name == "isometric":
        # Lower focus target to center the dummy's entire mass envelope
        camera.lookAt.setY(3.8)
        
        # INCREASE VIEW SIZE
        camera.ortho_magnification = 6.2  
        
        target_dist = 45.0        
        target_rh = 45.0      
        # mathematical isometric lens pitch tilt
        target_rv = -35.264   

    elif name == "wideshot":
        camera.lookAt.setY(2.5)
        camera.lookAt.setX(0.0)
        camera.lookAt.setZ(0.0)
        target_fov = 50.0
        target_dist = 90.0    
        target_rh = 0.0      
        target_rv = -12.0

    elif name == "closeup":
        camera.lookAt.setY(6.8)
        target_fov = 22.0     
        target_dist = 12.0    
        target_rh = 0.0
        target_rv = 0.0

    elif name == "high angle":
        camera.lookAt.setY(4.5)
        target_fov = 46.0
        target_dist = 25.0    
        target_rh = 0.0
        target_rv = 32.0   

    elif name == "low angle":
        camera.lookAt.setY(6.5)
        target_fov = 46.0
        target_dist = 30.0    
        target_rh = 0.0
        target_rv = -32.0    

    elif name == "eye level":
        camera.lookAt.setY(5.2)
        target_fov = 38.0
        target_dist = 30.0    
        target_rh = 0.0
        target_rv = 0.0

    elif name == "ots_left":
        # Over the Shoulder Left: Positioned behind the left shoulder blade looking forward
        camera.lookAt.setY(8.0)
        camera.lookAt.setZ(-4.9)
        target_fov = 50.0
        target_dist = 3.0
        target_rh = -165.0   
        target_rv = 8.0

    elif name == "ots_right":
        # Over the Shoulder Right: Positioned behind the right shoulder blade looking forward
        camera.lookAt.setY(8.0)
        camera.lookAt.setZ(-4.9)
        target_fov = 50.0
        target_dist = 3.0
        target_rh = 165.0    
        target_rv = 8.0

    elif name == "mediumshot":
        camera.lookAt.setY(4.5)
        target_fov = 40.0
        target_dist = 48.0    
        target_rh = 0.0
        target_rv = 0.0

    elif name == "fullshot":
        camera.lookAt.setY(1.5)
        target_fov = 35.0
        target_dist = 75.0    
        target_rh = 0.0
        target_rv = 0.0

    elif name == "reset":
        camera.lookAt.setY(1.5)
        target_fov = 45.0
        target_dist = 65.0    
        target_rh = 0.0
        target_rv = 0.0

    # =========================
    # CLEAN CORE SYNC PIPELINE 
    # =========================
    # Assign parameters natively so MakeHuman's input math remains active
    if 'target_fov' in locals(): camera.verticalAngle = target_fov
    if 'target_dist' in locals(): camera.cameraDist = target_dist
    
    if 'target_rh' in locals():
        if hasattr(camera, 'rh_angle'): camera.rh_angle = target_rh
    if 'target_rv' in locals():
        if hasattr(camera, 'rv_angle'): camera.rv_angle = target_rv

    # Tell the official system to recalculate position vectors without locking the mouse
    if hasattr(camera, 'updateCameraPosition'):
        camera.updateCameraPosition()
    elif hasattr(camera, 'update'):
        camera.update()

    camera.updateViewMatrix()
    camera.calculateProjMatrix()

    # ===========================================
    # COORDINATE OVERRIDE PIPELINE (RUNS SECOND)
    # ===========================================
    # Only execute 3D vector transformations if a positioning button was tapped!
    if 'target_dist' in locals() and 'target_rh' in locals() and 'target_rv' in locals():
        import math
        rad_h = math.radians(target_rh)
        rad_v = math.radians(target_rv)
        
        cx = target_dist * math.sin(rad_h) * math.cos(rad_v)
        cy = target_dist * math.sin(rad_v)
        cz = target_dist * math.cos(rad_h) * math.cos(rad_v)
        
        camera.cameraPos.setX(camera.lookAt.x() + cx)
        camera.cameraPos.setY(camera.lookAt.y() + cy)
        camera.cameraPos.setZ(camera.lookAt.z() + cz)

        # Force immediate openGL buffer recomputations
        camera.updateViewMatrix()
        camera.calculateProjMatrix()

# =====================================
# APPLICATION EVENT LOOP INTERCEPTOR 
# =====================================
class DynamicInputInterceptor(QObject):
    """Handles visual bounding rubberbands without interrupting canvas routines."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = False
        self.start_pos = QPoint()
        self.rubber_band = None

    def eventFilter(self, obj, event):
        # 1. CORE TYPE FILTER:
        if not obj or not hasattr(obj, 'metaObject') or not obj.metaObject():
            # Returning False safely passes non-widgets down to MakeHuman's native drawer loop
            return False

        # 2. VIEWPORT VERIFICATION GATEWAY
        class_name = obj.metaObject().className() if obj.metaObject() else ""
        is_canvas = "View3D" in class_name or "Canvas" in class_name or "GL" in class_name or hasattr(obj, 'view_matrix')
        if not is_canvas:
            return super().eventFilter(obj, event)

        global _saved_glob_context
        camera = None
        if _saved_glob_context and hasattr(_saved_glob_context, 'openGLWindow'):
            view = _saved_glob_context.openGLWindow
            if view and hasattr(view, 'camera'):
                camera = view.camera

        if not camera:
            return super().eventFilter(obj, event)

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

        return super().eventFilter(obj, event)


_active_filter_instance = None
_ui_panel_instance = None
_dock_container_instance = None  
_filter_overlay_label = None  
_saved_app_context = None
_saved_glob_context = None

def load_extension(app, glob):
    """Initializes the extension and mounts UI layout inside a dockable widget panel."""
    global _active_filter_instance, _ui_panel_instance, _dock_container_instance
    global _filter_overlay_label, _saved_app_context, _saved_glob_context
    
    _saved_app_context = QApplication.instance() or app
    _saved_glob_context = glob
    
    if _saved_app_context and _active_filter_instance is None:
        _active_filter_instance = DynamicInputInterceptor()
        _saved_app_context.installEventFilter(_active_filter_instance)
        
        # 1. Locate the main application window and viewport
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
                if not hasattr(child, 'metaObject') or not child.metaObject():
                    continue
                if hasattr(child, 'camera') and hasattr(child, 'light'):
                    view = child
                    break

        # 2. Set up lens overlay filter layer 
        if view and _filter_overlay_label is None:
            _filter_overlay_label = QLabel(view)
            _filter_overlay_label.setObjectName("camera_lens_overlay_filter")
            _filter_overlay_label.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")
            _filter_overlay_label.setFrameShape(QLabel.NoFrame)
            _filter_overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            _filter_overlay_label.setScaledContents(True)
            _filter_overlay_label.setGeometry(0, 0, view.width(), view.height())
            _filter_overlay_label.show()

        # 3. Instantiate the UI panel
        _ui_panel_instance = CinematicPresetsUI(_active_filter_instance)

        # 4. Docking Layer: Wrap the panel and attach it to the Main Window
        if main_window:
            _dock_container_instance = QDockWidget("Camera Controls", main_window)
            _dock_container_instance.setObjectName("camera_controls_dock_widget")
            
            # Allows you to drag/dock it to the Left or Right sides of your screen
            _dock_container_instance.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            
            # Place your exact UI panel inside the dock container
            _dock_container_instance.setWidget(_ui_panel_instance)
            
            # Snap it to the Right side panel layout area by default
            main_window.addDockWidget(Qt.RightDockWidgetArea, _dock_container_instance)
            _dock_container_instance.show()
        else:
            # Floating fallback if main window isn't detected
            _ui_panel_instance.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            _ui_panel_instance.setWindowTitle("Camera Controls")
            _ui_panel_instance.resize(250, 350)
            _ui_panel_instance.show()
        
    return {"status": "camera_controls_active"}

# =================================
# QSS COMPLIANT UI COMPONENT PANEL 
# =================================
class CinematicPresetsUI(QWidget):
    """Injected UI container displaying convenient studio layout shortcut triggers."""
    def __init__(self, target_interceptor, parent=None):
        super().__init__(parent)
        self.interceptor = target_interceptor
        self.setObjectName("CinematicPresetsUI")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)
        
        title = QLabel("Cinematic Lenses & Framing")
        title.setStyleSheet("font-weight: bold; font-size: 13px; margin: 10px 0px 5px 0px; color: #E0E0E0;")
        layout.addWidget(title)
        
        # ----------------------------------------
        # CINEMATIC POST-PROCESS FILTER DROPDOWN 
        # ----------------------------------------
        filter_label = QLabel("Camera Post-Process Filter:")
        filter_label.setStyleSheet("font-size: 11px; color: #A0A0A0; margin-top: 5px;")
        layout.addWidget(filter_label)
        
        self.filter_dropdown = QComboBox()
        self.filter_dropdown.setObjectName("camera_filter_dropdown")
        self.filter_dropdown.setProperty("class", "action-combo-box")
        
        # 1. Locate the "filters" folder next to this running script file
        import os
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        filters_dir = os.path.join(plugin_dir, "filters")
        
        # 2. Automatically scan the folder for all .png file templates
        if os.path.exists(filters_dir):
            dynamic_filters = sorted([f for f in os.listdir(filters_dir) if f.lower().endswith('.png')])
        else:
            dynamic_filters = ["default.png"]
            print(f"![Camera Controls Engine] Path not found for dynamic population: {filters_dir}")
            
        # 3. Mount the discovered file list directly into the dropdown layout
        self.filter_dropdown.addItems(dynamic_filters)
        
        # Hook up the filter change execution trigger
        self.filter_dropdown.currentTextChanged.connect(self.execute_render_filter_change)
        layout.addWidget(self.filter_dropdown)
        layout.addSpacing(5)

        # -----------------------------------------
        # 18 CAMERA FRAMING SHORTCUT GRID
        # -----------------------------------------
        grid = QGridLayout()
        grid.setSpacing(4)
        
        buttons_config = [
            ("Selfie Left", "selfie_left", 0, 0),
            ("Selfie Right", "selfie_right", 0, 1),
            ("Fish Eye", "fish eye", 1, 0),
            ("POV", "pov", 1, 1),
            ("Bird's Eye", "godview", 2, 0),
            ("Ortho", "ortho", 2, 1),
            ("Panoramic", "panoramic", 3, 0),
            ("Isometric", "isometric", 3, 1),
            ("Wide Shot", "wideshot", 4, 0),
            ("Close-Up", "closeup", 4, 1),
            ("High Angle", "high angle", 5, 0),
            ("Low Angle", "low angle", 5, 1),
            ("Eye Level", "eye level", 6, 0),
            ("Full Shot", "fullshot", 6, 1),
            ("Worm's Eye", "wormsview", 7, 0),
            ("Medium Shot", "mediumshot", 7, 1),
            ("OTS Left", "ots_left", 8, 0),
            ("OTS Right", "ots_right", 8, 1)
        ]
        
        for text, key, r, c in buttons_config:
            btn = QPushButton(text)
            btn.setObjectName(f"btn_{key.replace(' ', '_')}")
            btn.setProperty("class", "action-button secondary-button")
            btn.clicked.connect(lambda checked=False, k=key: self.execute_preset(k))
            grid.addWidget(btn, r, c)
            
        layout.addLayout(grid)
        
        layout.addSpacing(6)
        reset_btn = QPushButton("Reset Camera View")
        reset_btn.setObjectName("btn_camera_reset")
        reset_btn.setProperty("class", "action-button primary-button")
        reset_btn.clicked.connect(lambda: self.execute_preset("reset"))
        layout.addWidget(reset_btn)
        
        layout.addStretch()

    def execute_preset(self, key):
        """Finds active viewport camera structure via glob to apply framing matrix angles."""
        global _saved_glob_context
        camera = None
        if _saved_glob_context and hasattr(_saved_glob_context, 'openGLWindow'):
            view = _saved_glob_context.openGLWindow
            if view and hasattr(view, 'camera'):
                camera = view.camera

        if camera:
            trigger_cinematic_preset(camera, key)
            _saved_glob_context.openGLWindow.update()

    def execute_render_filter_change(self, filter_text):
        """Loads and updates the post-process texture overlay from the filters directory."""
        global _filter_overlay_label
        if _filter_overlay_label is None:
            return
            
        name = filter_text.strip()
        
        # Point this directly to the "filters" folder location
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        texture_path = os.path.join(plugin_dir, "filters", name)
            
        if os.path.exists(texture_path):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(texture_path)
            
            _filter_overlay_label.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")
            _filter_overlay_label.setFrameShape(QLabel.NoFrame)
            _filter_overlay_label.setScaledContents(True)
            _filter_overlay_label.setPixmap(pixmap)
            
            if _filter_overlay_label.parentWidget():
                parent = _filter_overlay_label.parentWidget()
                _filter_overlay_label.setGeometry(parent.rect())
                _filter_overlay_label.setContentsMargins(0, 0, 0, 0)
                
            _filter_overlay_label.raise_()
            _filter_overlay_label.update()
            
            self.filter_dropdown.clearFocus()
            if _filter_overlay_label.parentWidget():
                _filter_overlay_label.parentWidget().setFocus()
        else:
            # This print statement will now accurately show if it's hitting the "filters" path
            print(f"![Camera Controls Engine] Checking file directory path: {texture_path}")

def unload_extension():
    """Removes input filters, destroys the dock window wrapper, and clears memory context."""
    global _active_filter_instance, _ui_panel_instance, _dock_container_instance, _saved_app_context, _saved_glob_context
    qt_app = QApplication.instance() or _saved_app_context
    
    if qt_app and _active_filter_instance is not None:
        qt_app.removeEventFilter(_active_filter_instance)
        if _active_filter_instance.rubber_band:
            _active_filter_instance.rubber_band.deleteLater()
            _active_filter_instance.rubber_band = None
        _active_filter_instance = None
        
    # Safely delete the dock wrapper container widget
    if _dock_container_instance is not None:
        _dock_container_instance.close()
        _dock_container_instance.deleteLater()
        _dock_container_instance = None

    if _ui_panel_instance is not None:
        _ui_panel_instance.close()
        _ui_panel_instance.deleteLater()
        _ui_panel_instance = None
        
    _saved_app_context = None
    _saved_glob_context = None
    print("[Camera Controls] Extension successfully unloaded.")
