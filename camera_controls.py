"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Camera Controls V2.5 - Formerly Zoom Patch- Cinematic Composition & Camera Presets
"""
from PySide6.QtCore import Qt, QPoint, QObject, QEvent, QRect
from PySide6.QtWidgets import QApplication, QRubberBand, QWidget, QVBoxLayout, QPushButton, QGridLayout, QLabel
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

    # =========================================================================
    # DECIMETER ANATOMICAL TARGET HEIGHTS (1 unit = 10cm)
    # Based on an average character height of 17.0 decimeters (~1.7m)
    # =========================================================================
    head_height = 16.2    # Target eyes/face center line precisely
    chest_height = 13.5   # Target center line for upper body framing
    mid_height = 8.5      # Target exact mid-torso center balance point

    # Default fallback properties
    target_rh = 0.0
    target_rv = 0.0
    target_dist = 32.0    # Balanced default tracking baseline (~3.2 meters)
    target_fov = 45.0

    # =========================================================================
    # DETAILED CINEMATIC PRESET VALUE ASSIGNMENTS
    # =========================================================================
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
        # Precise mathematical isometric downward lens pitch tilt
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
    camera.verticalAngle = target_fov
    camera.cameraDist = target_dist
    
    if hasattr(camera, 'rh_angle'): camera.rh_angle = target_rh
    if hasattr(camera, 'rv_angle'): camera.rv_angle = target_rv

    # Tell the official system to recalculate position vectors without locking the mouse
    if hasattr(camera, 'updateCameraPosition'):
        camera.updateCameraPosition()
    elif hasattr(camera, 'update'):
        camera.update()

    camera.updateViewMatrix()
    camera.calculateProjMatrix()

    # ============================================
    # COORDINATE OVERRIDE PIPELINE (RUNS SECOND)
    # ============================================
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
        class_name = obj.metaObject().className() if obj.metaObject() else ""
        is_canvas = "View3D" in class_name or "Canvas" in class_name or "GL" in class_name or hasattr(obj, 'view_matrix')
        if not is_canvas:
            return super().eventFilter(obj, event)

        camera = None
        app = QApplication.instance()
        
        if hasattr(obj, 'camera'): 
            camera = obj.camera
        elif hasattr(app, 'camera'): 
            camera = app.camera
        elif hasattr(app, 'view') and hasattr(app.view, 'camera'): 
            camera = app.view.camera
        elif hasattr(app, 'view3d') and hasattr(app.view3d, 'camera'): 
            camera = app.view3d.camera

        if not camera:
            return super().eventFilter(obj, event)

        # ----------------------
        # EVENT MOUSE CAPTURE 
        # ----------------------
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

# ==================
# MANAGEMENT HOOKS 
# ==================
_active_filter_instance = None
_ui_panel_instance = None

# Persistent global references to prevent PySide garbage collection dropouts
_saved_app_context = None
_saved_glob_context = None

def load_extension(app, glob):
    """Triggered when the user runs this file script via the official MH2 extensions panel."""
    global _active_filter_instance, _ui_panel_instance, _saved_app_context, _saved_glob_context
    
    _saved_app_context = QApplication.instance() or app
    _saved_glob_context = glob
    
    if _saved_app_context and _active_filter_instance is None:
        _active_filter_instance = DynamicInputInterceptor()
        _saved_app_context.installEventFilter(_active_filter_instance)
        
        target_panel = None
        for attr in ['extensions_panel', 'community_panel', 'right_panel', 'side_panel']:
            if hasattr(glob, attr) and getattr(glob, attr):
                target_panel = getattr(glob, attr)
                break
                
        if not target_panel and hasattr(glob, 'window') and glob.window:
            target_panel = glob.window.findChild(QWidget, "extensions_panel") or glob.window.findChild(QWidget, "right_panel")

        # Fallback to the floating tool palette window
        _ui_panel_instance = CinematicPresetsUI(_active_filter_instance)
        
        if target_panel:
            if target_panel.layout():
                target_panel.layout().addWidget(_ui_panel_instance)
            else:
                layout = QVBoxLayout(target_panel)
                layout.addWidget(_ui_panel_instance)
            glob.env.logLine(1, "+++ [Camera Controls Engine] Docked successfully inside sidebar.")
        else:
            _ui_panel_instance.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            _ui_panel_instance.setWindowTitle("MH2 Studio Camera Presets")
            _ui_panel_instance.resize(250, 300)
            _ui_panel_instance.show()
            glob.env.logLine(1, "+++ [Camera Controls Engine] Sidebar missing. Spawned floating layout utility window.")
        
    return {"status": "camera_controls_active"}

# =====================
# UI PRESET EXECUTOR 
# =====================
class CinematicPresetsUI(QWidget):
    """Injected UI container displaying the studio layout shortcut triggers."""
    def __init__(self, target_interceptor, parent=None):
        super().__init__(parent)
        self.interceptor = target_interceptor
        
        layout = QVBoxLayout(self)
        title = QLabel("Cinematic Lenses & Framing")
        title.setStyleSheet("font-weight: bold; font-size: 13px; margin: 10px 0px 5px 0px; color: #E0E0E0;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        
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
        
        layout.addSpacing(10)
        reset_btn = QPushButton("Reset Camera View")
        
        reset_btn.setObjectName("btn_camera_reset")
        reset_btn.setProperty("class", "action-button primary-button")
        
        reset_btn.clicked.connect(lambda: self.execute_preset("reset"))
        layout.addWidget(reset_btn)
        
        layout.addStretch()

    def execute_preset(self, key):
        """Finds current active rendering context"""
        global _saved_app_context, _saved_glob_context
        
        app = _saved_app_context or QApplication.instance()
        camera = None
        
        # 1. Direct Framework Reference Checks
        if hasattr(app, 'camera'): camera = app.camera
        elif hasattr(app, 'view') and hasattr(app.view, 'camera'): camera = app.view.camera
        elif hasattr(app, 'view3d') and hasattr(app.view3d, 'camera'): camera = app.view3d.camera
        
        if not camera and _saved_glob_context:
            glob = _saved_glob_context
            if hasattr(glob, 'camera'): camera = glob.camera
            elif hasattr(glob, 'view') and hasattr(glob.view, 'camera'): camera = glob.view.camera
            elif hasattr(glob, 'view3d') and hasattr(glob.view3d, 'camera'): camera = glob.view3d.camera
            
            # Nested Viewport Configurations
            elif hasattr(glob, 'scene') and glob.scene:
                if hasattr(glob.scene, 'camera'): camera = glob.scene.camera
                elif hasattr(glob.scene, 'view') and hasattr(glob.scene.view, 'camera'): camera = glob.scene.view.camera
                elif hasattr(glob.scene, 'getView') and glob.scene.getView() and hasattr(glob.scene.getView(), 'camera'):
                    camera = glob.scene.getView().camera

        # 2. REFLECTION LOOP (Failsafe for dynamic MH2 property changes)
        if not camera and _saved_glob_context:
            # Check all properties attached to glob for sub-objects with camera definitions
            for attr_name in dir(_saved_glob_context):
                try:
                    attr_val = getattr(_saved_glob_context, attr_name)
                    if attr_val and hasattr(attr_val, 'camera'):
                        camera = getattr(attr_val, 'camera')
                        break
                    elif attr_val and hasattr(attr_val, 'view') and hasattr(attr_val.view, 'camera'):
                        camera = attr_val.view.camera
                        break
                except Exception:
                    continue

        # 3. Apply transformation parameters if located (Clean single execution path)
        if camera:
            trigger_cinematic_preset(camera, key)
            
            # Force canvas view updates across all discovered viewports
            if hasattr(app, 'view'): app.view.update()
            if hasattr(app, 'view3d'): app.view3d.update()
            if _saved_glob_context:
                if hasattr(_saved_glob_context, 'view'): _saved_glob_context.view.update()
                if hasattr(_saved_glob_context, 'view3d'): _saved_glob_context.view3d.update()
                if hasattr(_saved_glob_context, 'scene') and hasattr(_saved_glob_context.scene, 'update'):
                    _saved_glob_context.scene.update()
                    
            print(f"-> Matrix transformed to snapshot preset configuration setup: {key}")
        else:
            # Print object types to the console to let us inspect the active namespace mappings
            app_type = type(app).__name__ if app else "None"
            glob_type = type(_saved_glob_context).__name__ if _saved_glob_context else "None"
            print(f"![Error] Camera missing. App Context: {app_type} | Glob Context: {glob_type}")

def unload_extension():
    """Triggered when refreshing extensions."""
    global _active_filter_instance, _ui_panel_instance, _saved_app_context, _saved_glob_context
    qt_app = QApplication.instance() or _saved_app_context
    
    if qt_app and _active_filter_instance is not None:
        qt_app.removeEventFilter(_active_filter_instance)
        if _active_filter_instance.rubber_band:
            _active_filter_instance.rubber_band.deleteLater()
            _active_filter_instance.rubber_band = None
        _active_filter_instance = None
        
    if _ui_panel_instance is not None:
        _ui_panel_instance.close()
        _ui_panel_instance.deleteLater()
        _ui_panel_instance = None
        
    _saved_app_context = None
    _saved_glob_context = None
    print("--- [Camera Controls Engine] Cleanly unhooked context threads.")

