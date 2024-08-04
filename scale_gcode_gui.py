from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsLineItem
from PySide6.QtWidgets import QInputDialog, QFileDialog, QMenuBar, QMenu, QMessageBox
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
from PySide6.QtGui import QAction, QScreen
from PySide6.QtCore import Qt, QRectF
import sys
import re


# global DEBUG flag
DEBUG = False

class GCodeViewer(QMainWindow):
    def __init__(self, file_name=None):
        super().__init__()

        self.setWindowTitle("G-code Viewer")
        self.resize(800, 600)
        self.center()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.create_menu()

        self.draw_grid = False
        self.raster = 10
        self.draw_surrounding_rect = False

        if file_name:
            self.load_gcode_file(file_name)

    def center(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)

    def create_menu(self):
        # File menu
        open_action = QAction("Open G-code File", self)
        open_action.triggered.connect(self.load_gcode_file_dialog)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        file_menu = QMenu("File", self)
        menubar.addMenu(file_menu)
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = QMenu("Help", self)
        menubar.addMenu(help_menu)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_gcode_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open G-code File", "", "G-code Files (*.gcode *.nc);;All Files (*)")
        if file_name:
            self.load_gcode_file(file_name)

    def load_gcode_file(self, file_name):
        with open(file_name, 'r') as file:
            gcode = file.read()
            self.parse_gcode(gcode)
            self.draw()
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def parse_gcode(self, gcode):
        self.scene.clear()
        self.lines = []
        first_point_set = False
        debug_info = []

        # Refined regex patterns
        g1_pattern = re.compile(r'^(?:N\d+\s+)?(G1)\s.*[XY][0-9\.\-]+', re.IGNORECASE)
        g0_pattern = re.compile(r'^(?:N\d+\s+)?(G0)\s.*[XY][0-9\.\-]+', re.IGNORECASE)
        coord_pattern = re.compile(r'([XY][0-9\.\-]+)', re.IGNORECASE)

        x, y = None, None

        for line in gcode.split('\n'):
            if not first_point_set and (self.is_gcode_line(line, g1_pattern) or self.is_gcode_line(line, g0_pattern)):
                x, y = self.get_new_coordinates(line, coord_pattern, x, y)
                first_point_set = True
                continue

            if self.is_gcode_line(line, g0_pattern):
                x, y = self.get_new_coordinates(line, coord_pattern, x, y)
                continue  # Start a new line

            if self.is_gcode_line(line, g1_pattern):
                x_new, y_new = self.get_new_coordinates(line, coord_pattern, x, y)
                if (x_new, y_new) != (x, y):  # Only update and draw if coordinates have changed
                    debug_info.append((x, y, x_new, y_new))
                    self.lines.append((x, y, x_new, y_new))
                    x, y = x_new, y_new
        
        # Calculate the bounding box
        self.min_x = min(min(line[0], line[2]) for line in self.lines)
        self.max_x = max(max(line[0], line[2]) for line in self.lines)
        self.min_y = min(min(line[1], line[3]) for line in self.lines)
        self.max_y = max(max(line[1], line[3]) for line in self.lines)

        if DEBUG:
            self.write_debug_info(debug_info, limit=20)

    def is_gcode_line(self, line, pattern):
        return pattern.match(line) is not None

    def get_new_coordinates(self, line, pattern, x, y):
        x_new, y_new = x, y
        coord_matches = pattern.findall(line)
        for coord in coord_matches:
            if coord.startswith('X') and len(coord) > 1 and coord[1] not in ['#', '=']:
                x_new = self.safe_float(coord[1:], x)
            elif coord.startswith('Y') and len(coord) > 1 and coord[1] not in ['#', '=']:
                y_new = self.safe_float(coord[1:], y)
        return x_new, y_new

    def safe_float(self, value, default):
        try:
            return float(value)
        except ValueError:
            return default

    def write_debug_info(self, debug_info, limit):
        with open('debug_coordinates.txt', 'w') as debug_file:
            for i, (x, y, x_new, y_new) in enumerate(debug_info):
                if i < limit:
                    debug_file.write(f'Original: ({x}, {y}) Parsed: ({x_new}, {y_new})\n')

    def draw(self):
        self.scene.clear()

        # Draw the grid
        if self.draw_grid:
            # Draw background grid
            self.draw_background_grid()

        # Draw the surrounding rectangle
        if self.draw_surrounding_rect:
            self.draw_surrounding_rectangle(self.lines)

        for line in self.lines:
            self.draw_line(*line)

    def draw_line(self, x1, y1, x2, y2):
        line = QGraphicsLineItem(x1, -y1, x2, -y2)  # Invert y-axis for correct orientation
        self.scene.addItem(line)

    def draw_background_grid(self):
        pen = QPen(QColor(200, 200, 200), 0.2)  # Light gray grid lines

        num_x = (self.max_x - self.min_x) // self.raster
        num_y = (self.max_y - self.min_y) // self.raster

        for i in range(int(num_x)+1):
            x = self.min_x + i * self.raster
            line = QGraphicsLineItem(x, -self.max_y, x, -self.min_y)
            line.setPen(pen)
            self.scene.addItem(line)
        for j in range(int(num_y)+1):
            y = self.min_y + j * self.raster
            line = QGraphicsLineItem(self.min_x, -y, self.max_x, -y)
            line.setPen(pen)
            self.scene.addItem(line)

    def draw_surrounding_rectangle(self, lines):
        if not lines:
            return
        
        # Draw surrounding rectangle
        pen = QPen(QColor(150, 150, 150), 0.5)
        rect = QRectF(self.min_x, -self.max_y, self.max_x - self.min_x, self.max_y - self.min_y)
        self.surrounding_rect = QGraphicsRectItem(rect)
        self.surrounding_rect.setPen(pen)
        self.scene.addItem(self.surrounding_rect)

        # Adding dimension annotations
        font = QFont("Arial", 5)
        width_text = QGraphicsTextItem(f"Width: {self.max_x - self.min_x} mm")
        width_text.setFont(font)

        height_text = QGraphicsTextItem(f"Height: {self.max_y - self.min_y} mm")
        height_text.setFont(font)

        # place texts below (outside) the rectangle, beside each other
        width_text.setPos(self.min_x, -self.min_y)
        height_text.setPos(self.min_x + width_text.boundingRect().width() + 3, -self.min_y)

        self.scene.addItem(width_text)
        self.scene.addItem(height_text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.on_resize(event)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        toggle_grid_action = QAction('Toggle Grid', self)
        toggle_grid_action.triggered.connect(self.toggle_grid)
        context_menu.addAction(toggle_grid_action)

        toggle_rect_action = QAction('Toggle Surrounding Rectangle', self)
        toggle_rect_action.triggered.connect(self.toggle_rect)
        context_menu.addAction(toggle_rect_action)

        # set raster size
        set_raster_action = QAction('Set Raster Size', self)
        set_raster_action.triggered.connect(self.set_raster_size)
        context_menu.addAction(set_raster_action)

        context_menu.exec(event.globalPos())

    def toggle_grid(self):
        self.draw_grid = not self.draw_grid
        self.draw()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def toggle_rect(self):
        self.draw_surrounding_rect = not self.draw_surrounding_rect
        self.draw()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def set_raster_size(self):
        raster, ok = QInputDialog.getInt(self, "Set Raster Size", "Enter the raster size:", self.raster, 1, 100, 1)
        if ok:
            self.raster = raster
            self.draw()
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def on_resize(self, event):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def show_about(self):
        QMessageBox.about(self, "About G-code Viewer", "G-code Viewer\nVersion 1.0\nA simple G-code viewer application.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Ensure menus are displayed within the application window on macOS
    if sys.platform == "darwin":
        app.setAttribute(Qt.AA_DontUseNativeMenuBar)
    
    file_name = sys.argv[1] if len(sys.argv) > 1 else None
    viewer = GCodeViewer(file_name)
    viewer.show()
    # ensure that the scene fits (even when the filename is passed as an argument)
    # seems weird, but it works
    viewer.view.fitInView(viewer.scene.sceneRect(), Qt.KeepAspectRatio)
    sys.exit(app.exec())
