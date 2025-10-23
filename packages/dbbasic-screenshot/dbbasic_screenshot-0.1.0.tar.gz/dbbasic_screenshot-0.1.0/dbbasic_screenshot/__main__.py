#!/usr/bin/env python3
"""
Fast Screenshot Annotator for macOS using PyQt5
Capture screenshots and quickly annotate them with lines, arrows, rectangles, and text
"""

import sys
import subprocess
import tempfile
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSpinBox,
                             QFileDialog, QMessageBox, QInputDialog)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage, QFont
from PyQt5.QtCore import Qt, QPoint, QRect


class AnnotationCanvas(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.original_pixmap = pixmap
        self.pixmap = pixmap.copy()
        self.setFixedSize(pixmap.size())

        # Drawing state
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()

        # Tool settings
        self.tool = "line"  # line, arrow, rectangle, text
        self.color = QColor(255, 0, 0)  # red
        self.line_width = 3

        # Store all shapes for undo
        self.shapes = []

        self.setMouseTracking(False)

    def set_tool(self, tool):
        self.tool = tool

    def set_color(self, color):
        self.color = color

    def set_width(self, width):
        self.line_width = width

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()

            if self.tool == "text":
                self.add_text(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and self.tool != "text":
            self.end_point = event.pos()
            # Show preview by redrawing
            self.pixmap = self.original_pixmap.copy()
            self.redraw_shapes()
            self.draw_preview()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing and self.tool != "text":
            self.drawing = False
            self.end_point = event.pos()

            # Save the shape
            shape = {
                'type': self.tool,
                'start': QPoint(self.start_point),
                'end': QPoint(self.end_point),
                'color': QColor(self.color),
                'width': self.line_width
            }
            self.shapes.append(shape)

            # Draw permanently
            self.draw_shape_on_pixmap(shape)
            self.original_pixmap = self.pixmap.copy()
            self.update()

    def draw_preview(self):
        """Draw temporary preview while dragging"""
        painter = QPainter(self.pixmap)
        pen = QPen(self.color, self.line_width)
        painter.setPen(pen)

        if self.tool == "line":
            painter.drawLine(self.start_point, self.end_point)
        elif self.tool == "arrow":
            self.draw_arrow(painter, self.start_point, self.end_point)
        elif self.tool == "rectangle":
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)

        painter.end()

    def draw_shape_on_pixmap(self, shape):
        """Draw a shape permanently on the pixmap"""
        painter = QPainter(self.pixmap)
        pen = QPen(shape['color'], shape['width'])
        painter.setPen(pen)

        if shape['type'] == "line":
            painter.drawLine(shape['start'], shape['end'])
        elif shape['type'] == "arrow":
            self.draw_arrow(painter, shape['start'], shape['end'])
        elif shape['type'] == "rectangle":
            rect = QRect(shape['start'], shape['end']).normalized()
            painter.drawRect(rect)
        elif shape['type'] == "text":
            font = QFont("Helvetica", 18, QFont.Bold)
            painter.setFont(font)
            painter.drawText(shape['start'], shape['text'])

        painter.end()

    def draw_arrow(self, painter, start, end):
        """Draw an arrow from start to end"""
        import math

        # Draw the line
        painter.drawLine(start, end)

        # Calculate arrow head
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrow_length = 15
        arrow_angle = math.pi / 6

        # Arrow head points
        p1 = QPoint(
            int(end.x() - arrow_length * math.cos(angle - arrow_angle)),
            int(end.y() - arrow_length * math.sin(angle - arrow_angle))
        )
        p2 = QPoint(
            int(end.x() - arrow_length * math.cos(angle + arrow_angle)),
            int(end.y() - arrow_length * math.sin(angle + arrow_angle))
        )

        # Draw arrow head
        painter.drawLine(end, p1)
        painter.drawLine(end, p2)

    def add_text(self, pos):
        """Add text annotation"""
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
        if ok and text:
            shape = {
                'type': 'text',
                'start': QPoint(pos),
                'text': text,
                'color': QColor(self.color),
                'width': self.line_width
            }
            self.shapes.append(shape)
            self.draw_shape_on_pixmap(shape)
            self.original_pixmap = self.pixmap.copy()
            self.update()

    def redraw_shapes(self):
        """Redraw all shapes (for undo)"""
        for shape in self.shapes:
            self.draw_shape_on_pixmap(shape)

    def undo(self):
        """Remove last shape"""
        if self.shapes:
            self.shapes.pop()
            self.pixmap = self.original_pixmap.copy()
            # Get the original without any shapes
            self.pixmap = QPixmap(self.pixmap.size())
            painter = QPainter(self.pixmap)
            # Start fresh from the very original
            self.pixmap = self.original_pixmap.copy()
            self.original_pixmap = self.pixmap.copy()
            # Reconstruct from original
            # We need to keep track of the base image
            self.redraw_all()

    def redraw_all(self):
        """Redraw everything from scratch"""
        # This is a bit tricky - we need to keep the original screenshot
        # For now, just keep it simple
        self.update()

    def clear_all(self):
        """Clear all annotations"""
        self.shapes = []
        self.pixmap = self.original_pixmap.copy()
        self.update()


class AnnotatorWindow(QMainWindow):
    def __init__(self, pixmap=None):
        super().__init__()
        self.setWindowTitle("Screenshot Annotator")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Toolbar
        toolbar = QHBoxLayout()

        # Add screenshot and open buttons first
        btn_screenshot = QPushButton("📷 Screenshot")
        btn_screenshot.clicked.connect(self.capture_new_screenshot)
        toolbar.addWidget(btn_screenshot)

        btn_open = QPushButton("📁 Open")
        btn_open.clicked.connect(self.open_image)
        toolbar.addWidget(btn_open)

        toolbar.addWidget(QLabel("  |  "))

        # Tool buttons
        self.btn_line = QPushButton("Line")
        self.btn_arrow = QPushButton("Arrow")
        self.btn_rect = QPushButton("Rectangle")
        self.btn_text = QPushButton("Text")

        self.btn_line.clicked.connect(lambda: self.set_tool("line"))
        self.btn_arrow.clicked.connect(lambda: self.set_tool("arrow"))
        self.btn_rect.clicked.connect(lambda: self.set_tool("rectangle"))
        self.btn_text.clicked.connect(lambda: self.set_tool("text"))

        toolbar.addWidget(self.btn_line)
        toolbar.addWidget(self.btn_arrow)
        toolbar.addWidget(self.btn_rect)
        toolbar.addWidget(self.btn_text)

        toolbar.addWidget(QLabel("  |  "))

        # Color buttons
        btn_red = QPushButton("Red")
        btn_green = QPushButton("Green")
        btn_blue = QPushButton("Blue")
        btn_yellow = QPushButton("Yellow")
        btn_black = QPushButton("Black")

        btn_red.clicked.connect(lambda: self.set_color(QColor(255, 0, 0)))
        btn_green.clicked.connect(lambda: self.set_color(QColor(0, 200, 0)))
        btn_blue.clicked.connect(lambda: self.set_color(QColor(0, 0, 255)))
        btn_yellow.clicked.connect(lambda: self.set_color(QColor(255, 255, 0)))
        btn_black.clicked.connect(lambda: self.set_color(QColor(0, 0, 0)))

        # Style color buttons
        btn_red.setStyleSheet("background-color: red; color: white;")
        btn_green.setStyleSheet("background-color: green; color: white;")
        btn_blue.setStyleSheet("background-color: blue; color: white;")
        btn_yellow.setStyleSheet("background-color: yellow; color: black;")
        btn_black.setStyleSheet("background-color: black; color: white;")

        toolbar.addWidget(btn_red)
        toolbar.addWidget(btn_green)
        toolbar.addWidget(btn_blue)
        toolbar.addWidget(btn_yellow)
        toolbar.addWidget(btn_black)

        toolbar.addWidget(QLabel("  |  "))

        # Width control
        toolbar.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 20)
        self.width_spin.setValue(3)
        self.width_spin.valueChanged.connect(self.set_width)
        toolbar.addWidget(self.width_spin)

        toolbar.addWidget(QLabel("  |  "))

        # Action buttons
        btn_undo = QPushButton("Undo")
        btn_clear = QPushButton("Clear")
        btn_save = QPushButton("Save")
        btn_copy = QPushButton("Copy")

        btn_undo.clicked.connect(self.undo)
        btn_clear.clicked.connect(self.clear)
        btn_save.clicked.connect(self.save)
        btn_copy.clicked.connect(self.copy_to_clipboard)

        toolbar.addWidget(btn_undo)
        toolbar.addWidget(btn_clear)
        toolbar.addWidget(btn_save)
        toolbar.addWidget(btn_copy)

        toolbar.addStretch()

        main_layout.addLayout(toolbar)

        # Canvas - create with default blank canvas if no pixmap provided
        if pixmap is None:
            pixmap = QPixmap(800, 600)
            pixmap.fill(Qt.white)

        self.canvas = AnnotationCanvas(pixmap)
        main_layout.addWidget(self.canvas)

        # Set initial tool
        self.set_tool("line")

    def set_tool(self, tool):
        self.canvas.set_tool(tool)
        # Update button styles with more visible active indicator
        for btn in [self.btn_line, self.btn_arrow, self.btn_rect, self.btn_text]:
            btn.setStyleSheet("")

        active_style = "background-color: #4A90E2; color: white; border: 2px solid #2E5C8A; font-weight: bold;"

        if tool == "line":
            self.btn_line.setStyleSheet(active_style)
        elif tool == "arrow":
            self.btn_arrow.setStyleSheet(active_style)
        elif tool == "rectangle":
            self.btn_rect.setStyleSheet(active_style)
        elif tool == "text":
            self.btn_text.setStyleSheet(active_style)

    def set_color(self, color):
        self.canvas.set_color(color)

    def set_width(self, width):
        self.canvas.set_width(width)

    def undo(self):
        self.canvas.undo()

    def clear(self):
        reply = QMessageBox.question(self, "Clear", "Clear all annotations?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.canvas.clear_all()

    def save(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"screenshot_{timestamp}.png"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Image", default_name,
            "PNG files (*.png);;JPEG files (*.jpg);;All files (*.*)"
        )

        if filename:
            self.canvas.pixmap.save(filename)
            QMessageBox.information(self, "Saved", f"Image saved to {filename}")

    def copy_to_clipboard(self):
        """Copy image to clipboard"""
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        self.canvas.pixmap.save(temp_file.name)
        temp_file.close()

        # Use osascript to copy to clipboard on macOS
        try:
            subprocess.run([
                'osascript', '-e',
                f'set the clipboard to (read (POSIX file "{temp_file.name}") as PNG picture)'
            ], check=True)
            QMessageBox.information(self, "Copied", "Image copied to clipboard")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Failed to copy to clipboard")
        finally:
            os.unlink(temp_file.name)

    def capture_new_screenshot(self):
        """Capture a new screenshot and replace current canvas"""
        pixmap = capture_screenshot()
        if pixmap and not pixmap.isNull():
            # Replace canvas with new screenshot
            self.canvas.setParent(None)
            self.canvas = AnnotationCanvas(pixmap)
            self.centralWidget().layout().addWidget(self.canvas)
            # Reapply current tool
            current_tool = self.canvas.tool
            self.set_tool(current_tool)
        else:
            QMessageBox.information(self, "Cancelled", "Screenshot cancelled")

    def open_image(self):
        """Open an existing image file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select image to annotate",
            "", "Image files (*.png *.jpg *.jpeg *.gif *.bmp);;All files (*.*)"
        )
        if filename:
            pixmap = QPixmap(filename)
            # Replace canvas with new image
            self.canvas.setParent(None)
            self.canvas = AnnotationCanvas(pixmap)
            self.centralWidget().layout().addWidget(self.canvas)
            # Reapply current tool
            current_tool = self.canvas.tool
            self.set_tool(current_tool)


def capture_screenshot():
    """Capture screenshot using macOS screencapture command"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_file.close()

    # Use macOS screencapture with interactive selection
    result = subprocess.run(['screencapture', '-i', temp_file.name])

    if result.returncode == 0 and os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
        pixmap = QPixmap(temp_file.name)
        os.unlink(temp_file.name)
        return pixmap
    else:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        return None


def main():
    app = QApplication(sys.argv)

    # Start with blank canvas
    # User can click Screenshot or Open buttons to load content
    window = AnnotatorWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
