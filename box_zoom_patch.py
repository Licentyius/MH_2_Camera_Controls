"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026
    Patch fix for zoom V1.0 Might include more features in future

"""
from PySide6.QtCore import Qt, QPoint, QObject, QEvent, QRect
from PySide6.QtWidgets import QApplication, QRubberBand
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

class DynamicInputInterceptor(QObject):
    """
    Application-wide performance-optimized input interceptor.
    Uses QRubberBand overlays to render visual rectangles without forcing canvas redraws.
    """
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
        if hasattr(obj, 'camera'):
            camera = obj.camera
        else:
            app = QApplication.instance()
            if hasattr(app, 'camera'): camera = app.camera
            elif hasattr(app, 'view') and hasattr(app.view, 'camera'): camera = app.view.camera
            elif hasattr(app, 'view3d') and hasattr(app.view3d, 'camera'): camera = app.view3d.camera

        if not camera:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
                self.active = True
                self.start_pos = event.position().toPoint()
                
                # Initialize or reuse the native widget overlay structure
                if not self.rubber_band:
                    self.rubber_band = QRubberBand(QRubberBand.Rectangle, obj)
                self.rubber_band.setGeometry(QRect(self.start_pos, self.start_pos))
                self.rubber_band.show()
                return True

        elif event.type() == QEvent.MouseMove:
            if self.active and self.rubber_band:
                current_point = event.position().toPoint()
                # Update visual coordinates on screen dynamically without triggering painter pipeline loops
                self.rubber_band.setGeometry(QRect(self.start_pos, current_point).normalized())
                return True

        elif event.type() == QEvent.MouseButtonRelease:
            if self.active and event.button() == Qt.LeftButton:
                self.active = False
                if self.rubber_band:
                    self.rubber_band.hide()
                    
                end_point = event.position().toPoint()
                # Execute external matrix bounding-box zoom math calculation routine
                apply_box_zoom(camera, self.start_pos.x(), self.start_pos.y(), end_point.x(), end_point.y())
                obj.update()  # Request a single clean repaint pass after calculation finishes
                return True

        return super().eventFilter(obj, event)

# =========================================================================
# MANAGEMENT HOOKS (INTEGRATED INTO COMMUNITY_PANEL CHECKBOX CODES)
# =========================================================================

_active_filter_instance = None

def load_extension(app, glob):
    """Triggered when the user checks the 'Box Zoom Patch' box in your UI panel."""
    global _active_filter_instance
    qt_app = QApplication.instance() or app
    
    if qt_app and _active_filter_instance is None:
        _active_filter_instance = DynamicInputInterceptor()
        qt_app.installEventFilter(_active_filter_instance)
        glob.env.logLine(1, "+++ [Box Zoom Extension] Active with high-performance overlay active.")
        
    return {"status": "box_zoom_active"}

def unload_extension():
    """Triggered when the user unchecks the box or clicks 'Refresh Community Extensions'."""
    global _active_filter_instance
    qt_app = QApplication.instance()
    
    if qt_app and _active_filter_instance is not None:
        qt_app.removeEventFilter(_active_filter_instance)
        if _active_filter_instance.rubber_band:
            _active_filter_instance.rubber_band.deleteLater()
            _active_filter_instance.rubber_band = None
        _active_filter_instance = None
        print("--- [Box Zoom Extension] Safely deactivated and removed from event loop.")

