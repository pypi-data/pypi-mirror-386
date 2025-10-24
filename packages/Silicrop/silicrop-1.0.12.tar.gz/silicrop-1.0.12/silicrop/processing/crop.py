"""
Manage ellipse fitting and cropping functionality.

This module provides a widget for interactive ellipse fitting and image cropping
with support for notch detection and mask generation.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Ellipse, Polygon
import cv2
import numpy as np

from silicrop.processing.rotate import Rotate
from silicrop.processing.utils import MouseNavigationHandler

class FitAndCrop(QWidget):
    """
    Interactive widget for ellipse fitting and image cropping.
    
    Features:
    - Manual ellipse fitting with 5 points
    - Notch detection mode with 3 points
    - Perspective transformation and cropping
    - Mask generation and export
    - Integration with rotation and filtering
    """
    
    def __init__(self, processed_label, width=800, height=800, 
                 filter_200_button=None, filter_150_button=None, header=False):
        """
        Initialize the FitAndCrop widget.
        
        Args:
            processed_label: Widget to display processed images
            width: Canvas width in pixels
            height: Canvas height in pixels
            filter_200_button: Button for 200mm filter mode
            filter_150_button: Button for 150mm filter mode
            header: Whether to create GUI components (False for headless mode)
        """
        super().__init__()
        
        # Configuration
        self.header = header
        self.processed_widget = processed_label
        self.filter_200_button = filter_200_button
        self.filter_150_button = filter_150_button
        
        # Image and processing data
        self.image = None
        self.points = []
        self.ellipse_params = None
        self.mask_image = None
        self.processed_ellipse = None
        
        # Interaction settings
        self.shift_pressed = False
        self.max_points = 5
        self.tolerance_px = 300
        self.scale = 1.0
        self.press_event = None
        self.panning = False
        
        # Notch detection mode
        self.notch_mode = False
        self.notch_points = []
        self.notch_mask = None
        
        # Connect filter buttons to the image processing function
        if self.filter_150_button and hasattr(self.filter_150_button, "clicked"):
            self.filter_150_button.clicked.connect(self.process_and_display_corrected_image)
        
        if self.filter_200_button and hasattr(self.filter_200_button, "clicked"):
            self.filter_200_button.clicked.connect(self.process_and_display_corrected_image)
        
        if self.header:
            # Set up the layout and canvas only if not headless
            layout = QVBoxLayout(self)
            self.fig, self.ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
            self.canvas = FigureCanvas(self.fig)
            layout.addWidget(self.canvas)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
            
            # Mouse navigation handler
            self.mouse_nav = MouseNavigationHandler(self.canvas, self.ax)
            
            # Configure the axis and connect events
            self.ax.axis('off')
            self.canvas.mpl_connect('button_press_event', self.on_click)
            # Keyboard shortcut activation for "N" key
            self.canvas.setFocusPolicy(Qt.StrongFocus)
            self.canvas.setFocus()  # Optional but useful to ensure initial focus
            self.canvas.keyPressEvent = self.keyPressEvent

    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == Qt.Key_N:
            self.toggle_notch_mode()
            status = "activated" if self.notch_mode else "deactivated"
            print(f"🔵 Notch mode {status}")
    
    def is_checked(self, button):
        """Check if a button is checked."""
        if hasattr(button, "isChecked"):
            return button.isChecked()
        return bool(button)
    
    def toggle_notch_mode(self):
        """Toggle between normal mode and notch drawing mode."""
        self.notch_mode = not self.notch_mode
        print(f"Notch mode: {'ON' if self.notch_mode else 'OFF'}")

    def set_image(self, cv_img):
        """
        Set the input image and reset all processing data.
        
        Args:
            cv_img: OpenCV image (BGR format)
        """
        self.image = cv_img
        self.points = []
        self.ellipse_params = None
        self.mask_image = None
        self.processed_ellipse = None
        self.notch_points = []  # Reset notch points
        self.notch_mask = None  # Reset notch mask
        
        if self.header and self.ax is not None:
            self.ax.clear()
            self.ax.axis("off")
            if self.image is not None:
                # Convert BGR to RGB for matplotlib
                img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                self.ax.imshow(img_rgb)
                
                # Force the axis limits to match the image dimensions
                height, width = self.image.shape[:2]
                self.ax.set_xlim(0, width)
                self.ax.set_ylim(height, 0)  # Invert y-axis for correct display
            
            self.canvas.draw()

    def draw_points_and_ellipse(self):
        """Draw points and fitted ellipse on the canvas."""
        if self.header is None or self.ax is None:
            return  # Do nothing if headless
        
        self.ax.clear()
        self.ax.axis('off')
        
        # Display image
        if self.image is not None:
            img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.ax.imshow(img_rgb)
            
            # Keep the axis limits fixed to the image dimensions
            height, width = self.image.shape[:2]
            self.ax.set_xlim(0, width)
            self.ax.set_ylim(height, 0)  # Invert y-axis for correct display
        
        # Draw points
        if self.points:
            pts = np.array(self.points)
            self.ax.plot(pts[:, 0], pts[:, 1], 'ro')
            
            # Add point numbers next to each point
            for idx, (x, y) in enumerate(pts):
                self.ax.text(x + 2, y - 2, str(idx + 1), 
                           color='black', fontsize=10, fontweight='bold')
        
        # Draw ellipse and bounding box
        if self.ellipse_params is not None:
            center, axes, angle = self.ellipse_params
            ellipse = Ellipse(center, axes[0], axes[1], angle=angle, 
                            edgecolor='b', facecolor='none', linewidth=2)
            self.ax.add_patch(ellipse)
            
            # Draw bounding box
            box_params = (center, (axes[0], axes[1]), angle)
            box_points = cv2.boxPoints(box_params).astype(np.float32)
            polygon = Polygon(box_points, closed=True, 
                            edgecolor='g', facecolor='none', linewidth=2)
            self.ax.add_patch(polygon)
        
        self.canvas.draw()

    def on_click(self, event=None):
        """
        Handle mouse click events for adding, moving, or removing points.
        
        Args:
            event: Mouse click event
        """
        if event is None:
            print("Button clicked - on_click called without event")
            return
        
        # Ignore clicks during panning or outside axes
        if getattr(self, 'panning', False) or event.inaxes != self.ax:
            return
        
        if self.header is None or self.ax is None:
            return  # Do nothing if headless
        
        # Handle notch mode clicks
        if self.notch_mode:
            self.handle_notch_click(event)
            return
        
        # Ignore Ctrl+click events
        ctrl_pressed = (hasattr(event, 'guiEvent') and 
                       event.guiEvent.modifiers() & Qt.ControlModifier)
        if ctrl_pressed:
            return
        
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        
        click_pos = np.array([x, y])
        
        # Right-click to remove a point
        if event.button == 3:
            for i, pt in enumerate(self.points):
                if np.linalg.norm(click_pos - np.array(pt)) < self.tolerance_px:
                    del self.points[i]
                    self.ellipse_params = None
                    if self.processed_widget:
                        self.processed_widget.clear()
                    self.draw_points_and_ellipse()
                    return
        
        # Move an existing point
        for i, pt in enumerate(self.points):
            if np.linalg.norm(click_pos - np.array(pt)) < self.tolerance_px:
                self.points[i] = (x, y)
                self.draw_points_and_ellipse()
                if len(self.points) == self.max_points:
                    pts = np.array(self.points, dtype=np.float32)
                    self.ellipse_params = cv2.fitEllipse(pts)
                    self.process_and_display_corrected_image()
                return
        
        # Add a new point
        if len(self.points) < self.max_points:
            self.points.append((x, y))
        
        # Fit the ellipse if enough points are added
        if len(self.points) == self.max_points:
            pts = np.array(self.points, dtype=np.float32)
            self.ellipse_params = cv2.fitEllipse(pts)
            self.process_and_display_corrected_image()
        else:
            self.ellipse_params = None
            if self.processed_widget:
                self.processed_widget.clear()
        
        self.draw_points_and_ellipse()
    
    def handle_notch_click(self, event):
        """
        Handle clicks for notch mode (3 points max, low tolerance).
        
        Args:
            event: Mouse click event
        """
        if event.xdata is None or event.ydata is None:
            return
        
        ctrl_pressed = (hasattr(event, 'guiEvent') and 
                       event.guiEvent.modifiers() & Qt.ControlModifier)
        if ctrl_pressed:
            return
        
        x, y = event.xdata, event.ydata
        click_pos = np.array([x, y])
        tolerance_px = 3  # Low tolerance for precise notch editing
        
        # Right-click to remove a point
        if event.button == 3:
            for i, pt in enumerate(self.notch_points):
                if np.linalg.norm(click_pos - np.array(pt)) < tolerance_px:
                    del self.notch_points[i]
                    self.draw_notch_points()
                    return
        
        # Left-click to add a point (max 3)
        if event.button == 1 and len(self.notch_points) < 3:
            self.notch_points.append((x, y))
            self.draw_notch_points()     

    def process_and_display_corrected_image(self, points=None):
        """
        Process the image and display the corrected version.
        
        Args:
            points: Optional points to use instead of self.points
        """
        if self.ellipse_params is None or self.image is None:
            return
        
        if not isinstance(points, (list, np.ndarray)):
            points = self.points
        
        used_points = points
        print("✅ Used points:", used_points)
        
        # Create ellipse mask
        (cx, cy), (MA, ma), angle = self.ellipse_params
        mask = np.zeros(self.image.shape[:2], np.uint8)
        cv2.ellipse(mask, (int(cx), int(cy)), (int(MA / 2), int(ma / 2)), 
                   angle, 0, 360, 255, -1)
        
        # Split mask for 150mm filter if needed
        if (len(used_points) == 2 or 
            (len(used_points) == 5 and self.is_checked(self.filter_150_button))):
            p1 = tuple(map(int, used_points[0]))
            p5 = tuple(map(int, used_points[-1]))
            mask = self.split_ellipse_mask(mask, p1, p5)
        
        self.mask_image = mask.copy()
        
        # Perspective transformation
        diameter = int(max(MA, ma))
        pts1 = cv2.boxPoints(self.ellipse_params).astype(np.float32)
        pts2 = np.array([
            [0, 0],
            [diameter - 1, 0],
            [diameter - 1, diameter - 1],
            [0, diameter - 1]
        ], dtype=np.float32)
        
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        warped = cv2.warpPerspective(self.image, matrix, (diameter, diameter))
        warped_mask = cv2.warpPerspective(mask, matrix, (diameter, diameter))
        
        # Apply the final mask to the transformed image
        white_bg = np.ones_like(warped, dtype=np.uint8) * 255
        for c in range(3):
            white_bg[:, :, c] = np.where(warped_mask == 255, warped[:, :, c], 255)
        
        if self.processed_widget:
            self.processed_widget.set_image(white_bg)
        
        # Draw points on the processed image
        if len(used_points) == 5:
            orig_points = np.array(used_points, dtype=np.float32).reshape(-1, 1, 2)
            projected_points = cv2.perspectiveTransform(orig_points, matrix).reshape(-1, 2)
            
            self.processed_widget.ax.clear()
            self.processed_widget.ax.axis('off')
            img_rgb = cv2.cvtColor(white_bg, cv2.COLOR_BGR2RGB)
            self.processed_widget.ax.imshow(img_rgb)
            
            # Draw red points
            xs, ys = projected_points[:, 0], projected_points[:, 1]
            self.processed_widget.ax.plot(xs, ys, 'ro', markersize=7)
            
            for idx, (xp, yp) in enumerate(projected_points):
                self.processed_widget.ax.text(xp + 2, yp - 2, f'{idx + 1}', 
                                            color='black', fontsize=12, fontweight='bold')
            
            self.processed_widget.canvas.draw()
            self.processed_ellipse = white_bg
        else:
            self.processed_widget.set_image(white_bg)
            self.processed_ellipse = white_bg
                
        # if isinstance(self.processed_widget, Rotate):
        #     if self.is_checked(self.filter_150_button) and len(used_points) >= 2:
        #         # Calculate transformation matrix for rotation points
        #         orig_pts = np.array([used_points[0], used_points[-1]], 
        #                           dtype=np.float32).reshape(-1, 1, 2)
        #         print("✅ Rotation 150 triggered", orig_pts)
        #         projected = cv2.perspectiveTransform(orig_pts, matrix).reshape(-1, 2)
        #         self.processed_widget.rotation_points = [tuple(projected[0]), tuple(projected[1])]
        #         self.processed_widget.rotate_line_to_horizontal()
        #         self.processed_widget.draw()
        #     else:
        #         # Handle 200mm rotation
        #         orig_pts = np.array(used_points[0], dtype=np.float32).reshape(-1, 1, 2)
        #         print("✅ Rotation 200 triggered", orig_pts)
        #         projected = cv2.perspectiveTransform(orig_pts, matrix).reshape(-1, 2)
        #         self.processed_widget.rotation_point = tuple(projected[0])
        #         self.processed_widget.rotate_image_point_to_bottom_center()
        #         self.processed_widget.draw()
        # else:
        #     print(f"❌ Rotation not triggered - processed_widget is not a Rotate instance: {type(self.processed_widget)}")
    
    def draw_notch_points(self):
        """Draw notch triangle points and polygon on the image."""
        if self.ax is None or self.image is None:
            return
        
        self.ax.clear()
        img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.ax.imshow(img_rgb)
        self.ax.set_xlim(0, self.image.shape[1])
        self.ax.set_ylim(self.image.shape[0], 0)
        self.ax.axis('off')
        
        # Redraw ellipse if it exists
        if self.ellipse_params is not None:
            center, axes, angle = self.ellipse_params
            ellipse = Ellipse(center, axes[0], axes[1], angle=angle, 
                            edgecolor='b', facecolor='none', linewidth=2)
            self.ax.add_patch(ellipse)
            
            box_points = cv2.boxPoints((center, (axes[0], axes[1]), angle)).astype(np.float32)
            polygon = Polygon(box_points, closed=True, 
                            edgecolor='g', facecolor='none', linewidth=2)
            self.ax.add_patch(polygon)
        
        # Draw notch points
        if self.notch_points:
            pts = np.array(self.notch_points)
            self.ax.plot(pts[:, 0], pts[:, 1], 'bs')  # Blue squares
            for idx, (x, y) in enumerate(pts):
                self.ax.text(x + 2, y - 2, f'N{idx+1}', 
                           color='blue', fontsize=10, fontweight='bold')
            
            # Draw triangle if 3 points
            if len(self.notch_points) == 3:
                triangle = Polygon(pts, closed=True, 
                                 edgecolor='blue', facecolor='none', linewidth=2)
                self.ax.add_patch(triangle)
        
        self.canvas.draw()

    def generate_notch_mask(self):
        """
        Generate a mask from the notch polygon.
        
        Returns:
            numpy.ndarray: Binary mask with notch area marked as 255
        """
        if not self.notch_points or self.image is None:
            print("⚠️ No points for notch.")
            return None
        
        if len(self.notch_points) != 3:
            print("⚠️ Notch must have exactly 3 points.")
            return None
        
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        pts = np.array(self.notch_points, dtype=np.int32)
        
        # Check if points are within image bounds
        if (np.any(pts[:, 0] < 0) or np.any(pts[:, 1] < 0) or 
            np.any(pts[:, 0] >= self.image.shape[1]) or 
            np.any(pts[:, 1] >= self.image.shape[0])):
            print("⛔ Notch points outside image bounds.")
            return None
        
        cv2.fillPoly(mask, [pts], color=255)
        self.notch_mask = mask
        return mask
    
    def save_notch_mask(self):
        """Save the notch mask to a file."""
        if self.notch_mask is None:
            self.generate_notch_mask()
        
        if self.notch_mask is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Notch Mask", "", "PNG Files (*.png);;All Files (*)")
            if file_path:
                cv2.imwrite(file_path, self.notch_mask)
    
    def save_mask(self):
        """Save the ellipse mask to a file."""
        if self.mask_image is None:
            if self.image is None:
                return  # Can't create a mask if we don't know the image size
            height, width = self.image.shape[:2]
            self.mask_image = np.zeros((height, width), dtype=np.uint8)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Mask", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            cv2.imwrite(file_path, self.mask_image)

    def split_ellipse_mask(self, mask, p1, p5):
        """
        Split the ellipse mask along the line [p1, p5] and keep the larger part.
        
        Args:
            mask: Input ellipse mask
            p1: First point of the splitting line
            p5: Second point of the splitting line
            
        Returns:
            numpy.ndarray: Split mask with larger part
        """
        h, w = mask.shape
        Y, X = np.ogrid[:h, :w]
        x1, y1 = p1
        x2, y2 = p5
        
        # Line equation: ax + by + c = 0
        a = y2 - y1
        b = x1 - x2
        c = x2 * y1 - x1 * y2
        
        # Determine which side of the line each pixel is on
        side1 = (a * X + b * Y + c) > 0
        side2 = ~side1
        
        # Create masks for each side
        mask1 = np.zeros_like(mask)
        mask2 = np.zeros_like(mask)
        mask1[side1 & (mask > 0)] = 255
        mask2[side2 & (mask > 0)] = 255
        
        # Return the larger part
        return mask1 if cv2.countNonZero(mask1) > cv2.countNonZero(mask2) else mask2
    
    def generate_combined_mask(self):
        """
        Combine ellipse and notch masks into a single 3-class mask.
        
        Returns:
            numpy.ndarray: Combined mask where:
                0 = background
                1 = ellipse
                2 = notch
        """
        if self.image is None:
            print("⛔ No image loaded.")
            return None
        
        height, width = self.image.shape[:2]
        combined_mask = np.zeros((height, width), dtype=np.uint8)
        
        # Add ellipse mask
        if self.mask_image is not None and np.any(self.mask_image == 255):
            combined_mask[self.mask_image == 255] = 1
            print("✅ Ellipse added to combined mask.")
        else:
            print("⚠️ mask_image missing or empty.")
        
        # Add notch mask
        if self.notch_mask is None:
            print("↪️ notch_mask missing, attempting generation...")
            self.generate_notch_mask()
        
        if self.notch_mask is not None and np.any(self.notch_mask == 255):
            combined_mask[self.notch_mask == 255] = 2
            print("✅ Notch added to combined mask.")
        else:
            print("⚠️ notch_mask missing or empty.")
        
        nonzero = np.count_nonzero(combined_mask)
        print(f"🧮 Non-zero pixels in combined mask: {nonzero}")
        return combined_mask

    def save_combined_mask(self):
        """
        Save two versions of the combined mask:
        - Raw version for training (0/1/2 values)
        - Colored version for visualization
        """
        # Generate masks if needed
        ellipse_mask = self.mask_image
        notch_mask = self.notch_mask or self.generate_notch_mask()
        
        if self.image is None:
            print("⛔ Source image missing.")
            return
        
        if ellipse_mask is None and notch_mask is None:
            print("⛔ No masks to save.")
            return
        
        # Create combined mask: 0 = background, 1 = ellipse, 2 = notch
        combined_mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        
        if ellipse_mask is not None:
            combined_mask[ellipse_mask == 255] = 1
        
        if notch_mask is not None:
            combined_mask[notch_mask == 255] = 2  # Overwrite ellipse if overlap
        
        # Save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Combined Mask (base name)", "", "PNG Files (*.png);;All Files (*)")
        
        if not file_path:
            return
        
        # Save raw version for training (0/1/2)
        raw_path = file_path.replace(".png", "_train.png")
        cv2.imwrite(raw_path, combined_mask)
        print(f"✅ Raw mask saved: {raw_path}")
        
        # Save colored version for visualization
        color_mask = np.zeros((*combined_mask.shape, 3), dtype=np.uint8)
        color_mask[combined_mask == 1] = [255, 0, 0]   # Red for ellipse
        color_mask[combined_mask == 2] = [0, 0, 255]   # Blue for notch
        visu_path = file_path.replace(".png", "_visu.png")
        cv2.imwrite(visu_path, color_mask)
        print(f"👁️ Colored mask saved: {visu_path}")