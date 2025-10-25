"""
A class to manage and display frames in the UI, providing functionality
for plotting and saving combined screenshots of images and plots.
"""
import os
import numpy as np
import glob
import re
import pandas as pd
from PIL import Image
from PyQt5.QtWidgets import QFrame, QGroupBox, QWidget, QVBoxLayout, QPushButton, \
    QGridLayout, QLabel, QFileDialog, QProgressDialog, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from semapp.Plot.utils import create_savebutton
from semapp.Plot.styles import OPEN_BUTTON_STYLE, MESSAGE_BOX_STYLE, FRAME_STYLE

# Constants
FRAME_SIZE = 600
CANVAS_SIZE = 600
radius = 10

class PlotFrame(QWidget):
    """
    A class to manage and display frames in the UI,
    allowing plotting and image viewing.
    Provides functionality to open and display TIFF
    images and plot coordinate mappings.
    """

    def __init__(self, layout, button_frame):
        """
        Initializes the PlotFrame class by setting up the
        UI components and initializing variables.

        :param layout: The layout to which the frames will be added.
        :param button_frame: The button frame containing
        additional control elements.
        """
        super().__init__()
        self.layout = layout
        self.button_frame = button_frame
        
        # Initialize state
        self.coordinates = None
        self.image_list = []
        self.current_index = 0
        self.canvas_connection_id = None
        self.selected_wafer = None
        self.radius = None
        self.is_complus4t_mode = False  # COMPLUS4T mode detected
        
        self._setup_frames()
        self._setup_plot()
        self._setup_controls()

    def _setup_frames(self):
        """Initialize left and right display frames."""
        # Left frame for images
        self.frame_left = self._create_frame()
        self.frame_left_layout = QVBoxLayout()
        self.frame_left.setLayout(self.frame_left_layout)
        
        # Right frame for plots
        self.frame_right = self._create_frame()
        self.frame_right_layout = QGridLayout()
        self.frame_right.setLayout(self.frame_right_layout)
        
        # Add frames to main layout
        self.layout.addWidget(self.frame_left, 2, 0, 1, 3)
        self.layout.addWidget(self.frame_right, 2, 3, 1, 3)

    def _create_frame(self):
        """Create a styled frame with fixed size."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(FRAME_STYLE)
        frame.setFixedSize(FRAME_SIZE+100, FRAME_SIZE)
        return frame

    def _setup_plot(self):
        """Initialize matplotlib figure and canvas."""
        self.figure = Figure(figsize=(5, 5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.frame_right_layout.addWidget(self.canvas)
        
        # Initialize image display
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.frame_left_layout.addWidget(self.image_label)

    def _setup_controls(self):
        """Set up control buttons."""
        create_savebutton(self.layout, self.frame_left, self.frame_right)
        
        open_button = QPushButton('Open TIFF', self)
        open_button.setStyleSheet(OPEN_BUTTON_STYLE)
        open_button.clicked.connect(self.open_tiff)
        self.layout.addWidget(open_button, 1, 5)
    
    def extract_positions(self, filepath, wafer_id=None):
        """
        Extract defect positions from KLARF file.
        
        Args:
            filepath: Path to the KLARF (.001) file
            wafer_id: Specific wafer ID to extract (for COMPLUS4T files with multiple wafers)
                     If None, extracts all defects (normal mode)
        """
        data = {
            "SampleSize": None,
            "DiePitch": {"X": None, "Y": None},
            "DieOrigin": {"X": None, "Y": None},
            "SampleCenterLocation": {"X": None, "Y": None},
            "Defects": []
        }

        dans_defect_list = False
        current_wafer_id = None
        target_wafer_found = False
        reading_target_wafer = False

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line = line.strip()

            # Detect WaferID
            if line.startswith("WaferID"):
                match = re.search(r'WaferID\s+"@(\d+)"', line)
                if match:
                    current_wafer_id = int(match.group(1))
                    
                    # If looking for a specific wafer
                    if wafer_id is not None:
                        if current_wafer_id == wafer_id:
                            target_wafer_found = True
                            reading_target_wafer = True
                            # Do NOT reset global data already read (DiePitch, etc.)
                            # Only reset Defects
                            data["Defects"] = []
                        elif target_wafer_found:
                            # Already found our wafer and reached another one
                            # Stop reading
                            break
                        else:
                            reading_target_wafer = False
                    else:
                        # Normal mode (no wafer_id specified)
                        reading_target_wafer = True
                continue

            # If looking for specific wafer, skip lines until finding the right wafer
            # EXCEPT for DefectList where we filter in the elif block
            if wafer_id is not None and not reading_target_wafer and not line.startswith("DefectList"):
                # Don't skip parameters before first WaferID
                if current_wafer_id is None:
                    # Haven't seen WaferID yet, read global parameters
                    pass
                else:
                    # Seen a WaferID but it's not the right one, skip
                    continue

            if line.startswith("SampleSize"):
                match = re.search(r"SampleSize\s+1\s+(\d+)", line)
                if match:
                    data["SampleSize"] = int(match.group(1))

            elif line.startswith("DiePitch"):
                match = re.search(r"DiePitch\s+([0-9.e+-]+)\s+([0-9.e+-]+);", line)
                if match:
                    data["DiePitch"]["X"] = float(match.group(1))
                    data["DiePitch"]["Y"] = float(match.group(2))

            elif line.startswith("DieOrigin"):
                match = re.search(r"DieOrigin\s+([0-9.e+-]+)\s+([0-9.e+-]+);", line)
                if match:
                    data["DieOrigin"]["X"] = float(match.group(1))
                    data["DieOrigin"]["Y"] = float(match.group(2))

            elif line.startswith("SampleCenterLocation"):
                match = re.search(r"SampleCenterLocation\s+([0-9.e+-]+)\s+([0-9.e+-]+);", line)
                if match:
                    data["SampleCenterLocation"]["X"] = float(match.group(1))
                    data["SampleCenterLocation"]["Y"] = float(match.group(2))

            elif line.startswith("DefectList"):
                dans_defect_list = True
                continue

            elif dans_defect_list:
                # If in DefectList, filter by wafer if necessary
                if wafer_id is not None and not reading_target_wafer:
                    # In DefectList but not the right wafer, skip
                    if line.startswith("EndOfFile") or line.startswith("}"):
                        dans_defect_list = False
                    continue
                    
                if re.match(r"^\d+\s", line):
                    value = line.split()
                    if len(value) >= 12:
                        # Check if next line has exactly 2 columns
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            next_values = next_line.split()
                            if len(next_values) == 2:
                                # The real DEFECTID is the first element of next_values
                                real_defect_id = int(next_values[0])
                                defect = {f"val{i+1}": float(val) for i, val in enumerate(value[:10])}
                                defect["defect_id"] = real_defect_id
                                data["Defects"].append(defect)
                elif line.startswith("EndOfFile") or line.startswith("}"):
                    # End of DefectList
                    dans_defect_list = False

        pitch_x = data["DiePitch"]["X"]
        pitch_y = data["DiePitch"]["Y"]
        Xcenter = data["SampleCenterLocation"]["X"]
        Ycenter = data["SampleCenterLocation"]["Y"]

        corrected_positions = []
        for d in data["Defects"]:
            real_defect_id = d["defect_id"]  # Real DEFECTID (63, 64, 261, 262...)
            val2 = d["val2"]
            val3 = d["val3"]
            val4_scaled = d["val4"] * pitch_x - Xcenter
            val5_scaled = d["val5"] * pitch_y - Ycenter
            defect_size = d["val9"]

            x_corr = round((val2 + val4_scaled) / 10000, 1)
            y_corr = round((val3 + val5_scaled) / 10000, 1)

            corrected_positions.append({
                "defect_id": real_defect_id,
                "X": x_corr,
                "Y": y_corr,
                "defect_size": defect_size
            })

        self.coordinates = pd.DataFrame(corrected_positions, columns=["defect_id", "X", "Y", "defect_size"])
        
        # Save mapping to CSV
        import os
        file_dir = os.path.dirname(filepath)
        
        # If wafer_id is specified (COMPLUS4T mode), save to wafer subfolder
        if wafer_id is not None:
            # COMPLUS4T mode: save to dirname/wafer_id/mapping.csv
            csv_folder = os.path.join(file_dir, str(wafer_id))
            os.makedirs(csv_folder, exist_ok=True)
            csv_path = os.path.join(csv_folder, "mapping.csv")
        else:
            # Normal mode: save in same folder as .001 file
            csv_path = os.path.join(file_dir, "mapping.csv")
        
        self.coordinates.to_csv(csv_path, index=False)

        return self.coordinates

    def load_coordinates(self, csv_path):
        """
        Loads the X/Y coordinates from a CSV file for plotting.

        :param csv_path: Path to the CSV file containing the coordinates.
        """
        if os.path.exists(csv_path):
            self.coordinates = pd.read_csv(csv_path)
        else:
            # CSV not found, will need to extract from KLARF file
            pass

    def open_tiff(self):
        """Handle TIFF file opening and display."""
        self.selected_wafer = self.button_frame.get_selected_option()
        
        if not all([self.selected_wafer]):
            self._reset_display()
            return

        # Check if COMPLUS4T mode is active
        dirname = self.button_frame.folder_var_changed()
        is_complus4t = self._check_complus4t_mode(dirname)
        self.is_complus4t_mode = is_complus4t  # Store mode for later use
        
        if is_complus4t:
            # COMPLUS4T mode: .001 and .tiff files in parent directory
            folder_path = dirname
            
            # Find the .001 file with the selected wafer ID in parent directory
            matching_files = glob.glob(os.path.join(dirname, '*.001'))
            recipe_path = None
            
            for file_path in matching_files:
                if self._is_wafer_in_klarf(file_path, self.selected_wafer):
                    recipe_path = file_path
                    break
            
            # Find the only .tiff file in the parent directory
            tiff_files = glob.glob(os.path.join(dirname, '*.tiff'))
            if not tiff_files:
                tiff_files = glob.glob(os.path.join(dirname, '*.tif'))
            
            if tiff_files:
                tiff_path = tiff_files[0]
            else:
                self._reset_display()
                return
            
            # Extract positions for the specific wafer
            self.coordinates = self.extract_positions(recipe_path, wafer_id=self.selected_wafer)
        else:
            # Normal mode: subfolders
            folder_path = os.path.join(dirname, str(self.selected_wafer))
            
            # Find the first .001 file in the selected folder
            matching_files = glob.glob(os.path.join(folder_path, '*.001'))

            # Sort the files to ensure consistent ordering
            if matching_files:
                recipe_path = matching_files[0]
            else:
                recipe_path = None  
            
            tiff_path = os.path.join(folder_path, "data.tif")

            if not os.path.isfile(tiff_path):
                self._reset_display()
                return
            
            # Extract all positions (normal mode)
            self.coordinates = self.extract_positions(recipe_path)     

        self._load_tiff(tiff_path)
        self._update_plot()
        
        # Set reference to plot_frame in button_frame for slider updates
        self.button_frame.plot_frame = self

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Wafer {self.selected_wafer} opened successfully")
        msg.setWindowTitle("Wafer Opened")
        msg.setStyleSheet(MESSAGE_BOX_STYLE)
        msg.exec_()

    def _check_complus4t_mode(self, dirname):
        """Check if we are in COMPLUS4T mode (.001 files with COMPLUS4T in parent directory)."""
        if not dirname or not os.path.exists(dirname):
            return False
        
        # Check for .001 files with COMPLUS4T in the parent directory
        matching_files = glob.glob(os.path.join(dirname, '*.001'))
        for file_path in matching_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'COMPLUS4T' in content:
                        return True
            except Exception:
                pass
        
        return False

    def _is_wafer_in_klarf(self, file_path, wafer_id):
        """Check if a specific wafer ID is in the KLARF file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                pattern = r'WaferID\s+"@' + str(wafer_id) + r'"'
                return re.search(pattern, content) is not None
        except Exception:
            return False

    def _reset_display(self):
        """
        Resets the display by clearing the figure and reinitializing the subplot.
        Also clears the frame_left_layout to remove any existing widgets.
        """
        # Clear all widgets from the left frame layout
        while self.frame_left_layout.count():
            item = self.frame_left_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()  # Properly delete the widget

        # Recreate the image label in the left frame
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.frame_left_layout.addWidget(self.image_label)

        # Clear the figure associated with the canvas
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)  # Create a new subplot
        self.plot_mapping_tpl(self.ax)  # Plot the default template

        # Disconnect any existing signal connection
        if self.canvas_connection_id is not None:
            self.canvas.mpl_disconnect(self.canvas_connection_id)
            self.canvas_connection_id = None

        self.canvas.draw()  # Redraw the updated canvas

    def _update_plot(self):
        """
        Updates the plot with the current wafer mapping.
        Ensures the plot is clean before adding new data.
        """
        if hasattr(self, 'ax') and self.ax:
            self.ax.clear()  # Clear the existing plot
        else:
            self.ax = self.figure.add_subplot(111)  # Create new axes

        self.plot_mapping_tpl(self.ax)  # Plot wafer mapping

        # Ensure only one connection to the button press event
        if self.canvas_connection_id is not None:
            self.canvas.mpl_disconnect(self.canvas_connection_id)

        self.canvas_connection_id = self.canvas.mpl_connect(
            'button_press_event', self.on_click)
        self.canvas.draw()

    def show_image(self):
        """
        Displays the current image from the image list in the QLabel.
        """
        if self.image_list:
            pil_image = self.image_list[self.current_index]
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qimage = QImage(data, pil_image.width, pil_image.height,
                            QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap)

    def plot_mapping_tpl(self, ax):
        """Plots the mapping of the wafer with coordinate points."""
        ax.set_xlabel('X (cm)', fontsize=20)
        ax.set_ylabel('Y (cm)', fontsize=20)
        
        if self.coordinates is not None:
            # Get all coordinates
            x_coords = self.coordinates['X']
            y_coords = self.coordinates['Y']
            defect_size = self.coordinates['defect_size']
            
            # Determine color based on mode
            if self.is_complus4t_mode:
                # Mode COMPLUS4T: color based on slider threshold
                threshold = 0.0  # Default threshold
                result = self.button_frame.get_selected_image()
                if result is not None:
                    threshold = result[0]  # Slider value in nm
                
                # Red if size >= threshold, blue otherwise
                colors = ['red' if size >= threshold else 'blue' for size in defect_size]
            else:
                # Normal mode: color based on fixed threshold (10 nm)
                colors = ['red' if size > 1.0e+01 else 'blue' for size in defect_size]
            
            ax.scatter(x_coords, y_coords, color=colors, marker='o',
                       s=100, label='Positions')

            # Calculate the maximum value for scaling using ALL coordinates
            x_coords_all = self.coordinates['X']
            y_coords_all = self.coordinates['Y']
            max_val = max(abs(x_coords_all).max(), abs(y_coords_all).max())

            if max_val <= 5:
                radius = 5
            elif max_val <= 7.5:
                radius = 7.5
            elif max_val <= 10:
                radius = 10
            elif max_val <= 15:
                radius = 15
            else:
                radius = max_val  # fallback for > 15

            self.radius = radius
            
            # Set limits based on the radius
            ax.set_xlim(-radius - 1, radius + 1)
            ax.set_ylim(-radius - 1, radius + 1)

            circle = plt.Circle((0, 0), radius, color='black',
                                fill=False, linewidth=0.5)
            ax.add_patch(circle)
            ax.set_aspect('equal')
            
            # Add grid
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
        else:
            # No coordinates available
            pass
        

        ax.figure.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.1)
        self.canvas.draw()

    def on_click(self, event):
        """
        Handles mouse click events on the plot, identifying the closest point
        and updating the plot with a red circle around the selected point.

        :param event: The event generated by the mouse click.
        """
        result = self.button_frame.get_selected_image()
        if result is not None:
            self.image_type, self_number_type = result
        else:
            return

        if event.inaxes:
            x_pos = event.xdata
            y_pos = event.ydata


            if self.coordinates is not None and not self.coordinates.empty:
                distances = np.sqrt((self.coordinates['X'] - x_pos) ** 2 +
                                    (self.coordinates['Y'] - y_pos) ** 2)
                closest_idx = distances.idxmin()
                closest_pt = self.coordinates.iloc[closest_idx]
                
                # Replot with a red circle around the selected point
                self.ax.clear()  # Clear the existing plot
                self.plot_mapping_tpl(self.ax)
                self.ax.scatter([closest_pt['X']], [closest_pt['Y']],
                                color='red', marker='o', s=100,
                                label='Selected point')
                coord_text = f"{closest_pt['X']:.1f} / {closest_pt['Y']:.1f}"
                self.ax.text(-self.radius -0.5, self.radius-0.5, coord_text, fontsize=16, color='black')
                self.canvas.draw()

                # Update the image based on the selected point
                if self.is_complus4t_mode:
                    # COMPLUS4T mode: use DEFECTID from KLARF file
                    defect_id = int(closest_pt['defect_id'])
                    # DEFECTID starts at 1, but Python indices start at 0
                    result = defect_id - 1
                else:
                    # Normal mode: use DataFrame index (original behavior)
                    result = self.image_type + (closest_idx * self_number_type)
                
                self.current_index = result
                
                # Check if index is valid
                if 0 <= self.current_index < len(self.image_list):
                    self.show_image()

    def _load_tiff(self, tiff_path):
        """Load and prepare TIFF images for display.
        
        Args:
            tiff_path: Path to the TIFF file to load
        """
        try:
            img = Image.open(tiff_path)
            self.image_list = []

            # Load all TIFF pages and resize them
            while True:
                resized_img = img.copy().resize((CANVAS_SIZE, CANVAS_SIZE),
                                              Image.Resampling.LANCZOS)
                self.image_list.append(resized_img)
                try:
                    img.seek(img.tell() + 1)  # Move to next page
                except EOFError:
                    break  # No more pages

            self.current_index = 0
            self.show_image()  # Display first image
            
        except Exception as e:
            # Error loading TIFF file
            pass
            self._reset_display()
