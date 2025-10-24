from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QLabel, QListWidget, QFrame, QGridLayout, QMessageBox
)
import importlib.resources as pkg_resources
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidgetItem
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import cv2
import time
import numpy as np
import os
from PIL import Image, ImageOps
from silicrop.layout.dragdrop import FileDropListPanel
from silicrop.processing.prediction import EllipsePredictor
from silicrop.processing.crop import FitAndCrop
from silicrop.processing.rotate import Rotate
from silicrop.processing.prediction_batch import EllipsePredictorBatch
from silicrop.layout.styles import (
    drag_drop_area_style,
    list_widget_style,
    frame_style,
    button_style,
    button_scale_active,
    button_scale_inactive,
    button_style_model,
    button_style_notch,
    button_style_ai,
    button_style_howto
)
from silicrop.layout.how_to import show_howto_popup
 
from joblib import Parallel, delayed
import os
import cv2
import traceback
import time


def process_single_image(img_path, output_dir, model_path, idx, total):
    

    try:
        print(f"[{idx+1}/{total}] ▶ {os.path.basename(img_path)}")

        predictor = EllipsePredictorBatch(model_path)
        result_img, _, _ = predictor.run_inference(img_path, dataset_type='200')

        if result_img is not None:
            name = os.path.splitext(os.path.basename(img_path))[0]
            save_path = os.path.join(output_dir, f"{name}_processed.png")
            cv2.imwrite(save_path, result_img)
            print(f"[{idx+1}/{total}] ✅ Enregistré : {save_path}")
            return {"status": "ok", "path": img_path, "index": idx}
        else:
            return {"status": "vide", "path": img_path, "index": idx}

    except Exception as e:
        print(f"[{idx+1}/{total}] ❌ Erreur : {e}")
        traceback.print_exc()
        return {"status": "erreur", "path": img_path, "index": idx}
    
class ImageProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Silicrop")
        self.resize(900, 520)
        self.setFixedHeight(940)
        self.move(0, 0)

        # Initialize attributes
        self.image_paths = []
        self.filter_150_button = None
        self.filter_200_button = None

        # Set up the main layout
        self.global_layout = QGridLayout(self)
        self.setLayout(self.global_layout)

        # Initialize UI components
        self.scale()
        self.init_left_panel()
        self.init_right_panel()
        self.init_controls()
        self.init_controls_batch()
        self.init_howto()
        self.model_button()
        
    def model_button(self):
        self.select_model_button = QPushButton("Select a model")
        self.select_model_button.setStyleSheet(button_style_model())
        self.select_model_button.clicked.connect(self.select_model_path)
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.select_model_button.setSizePolicy(size_policy)
        self.global_layout.addWidget(self.select_model_button, 4, 0, 2, 1)

    def select_model_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir un modèle", "", "Fichiers PyTorch (*.pth *.pt)")
        if path:
            self.model_path = path
            print(f"Model path : {self.model_path}")


    def on_file_dropped(self, path):
        print(f"Files added to the list : {path}")

    def init_left_panel(self):
        self.drop_panel = FileDropListPanel(on_files_dropped=self.on_file_dropped)
        self.list_widget = self.drop_panel.get_list_widget()
        self.list_widget.itemSelectionChanged.connect(self.display_selected_image)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.drop_panel)


        container = QWidget()
        container.setLayout(left_layout)
        self.global_layout.addWidget(container, 0, 0, 1, 1)

    def init_right_panel(self):
        """Initialize the right panel with original and processed image frames."""
        # Original image frame
        self.original_frame = QFrame()
        self.original_frame.setStyleSheet(frame_style())
        self.original_frame.setFixedSize(700, 700)
        original_layout = QVBoxLayout()
        self.original_frame.setLayout(original_layout)

        # Add instruction label to the original frame
        original_instructions = QLabel("Scroll to zoom and Ctrl + drag to move the image")
        original_instructions.setAlignment(Qt.AlignCenter)
        original_instructions.setStyleSheet("color: gray; font-size: 12px; font-style: italic;")
        original_layout.addWidget(original_instructions)

        # Processed image frame
        self.processed_frame = QFrame()
        self.processed_frame.setStyleSheet(frame_style())
        self.processed_frame.setFixedSize(700, 700)
        processed_layout = QVBoxLayout()
        self.processed_frame.setLayout(processed_layout)

        # Add instruction label to the processed frame
        processed_instructions = QLabel("Scroll to zoom and Ctrl + drag to move the image")
        processed_instructions.setAlignment(Qt.AlignCenter)
        processed_instructions.setStyleSheet("color: gray; font-size: 12px; font-style: italic;")
        processed_layout.addWidget(processed_instructions)

        # Set layout margins and spacing
        original_layout.setContentsMargins(0, 0, 0, 0)
        original_layout.setSpacing(0)
        processed_layout.setContentsMargins(0, 0, 0, 0)
        processed_layout.setSpacing(0)

        # Initialize widgets
        self.processed_widget = Rotate(700, 700, filter_200_button=self.filter_200_button, filter_150_button=self.filter_150_button)
        processed_layout.addWidget(self.processed_widget)

        self.original_widget = FitAndCrop(self.processed_widget, 700, 700, filter_200_button=self.filter_200_button, filter_150_button=self.filter_150_button, header=True)
        original_layout.addWidget(self.original_widget)

        # Add frames to the grid layout
        self.global_layout.addWidget(self.original_frame, 0, 1, 1, 1)
        self.global_layout.addWidget(self.processed_frame, 0, 2, 1, 1)

        self.fit_crop_widget = self.original_widget

    def init_controls(self):
        """Initialize control buttons for saving masks and images."""
        # Save mask button

        self.IA_button = QPushButton("Run AI")
        self.IA_button.setCheckable(False)
        self.IA_button.setStyleSheet(button_style_ai())
        self.IA_button.clicked.connect(self.run_auto_dl_process)

        self.save_mask_button = QPushButton("Save Mask")
        self.save_mask_button.setStyleSheet(button_style())
        self.save_mask_button.clicked.connect(self.original_widget.save_mask)

        self.save_mask_notch_button = QPushButton("Save Mask w/ notch")
        self.save_mask_notch_button.setStyleSheet(button_style_notch())
        self.save_mask_notch_button.clicked.connect(self.original_widget.save_combined_mask)

        # Save image button
        self.save_image_button = QPushButton("Save Image")
        self.save_image_button.setStyleSheet(button_style())
        self.save_image_button.clicked.connect(self.processed_widget.save_processed_image)

        self.global_layout.addWidget(self.IA_button, 3, 2, 1, 1, alignment=Qt.AlignTop)
        self.global_layout.addWidget(self.save_image_button, 3, 1,  1, 1, alignment=Qt.AlignTop)
        self.global_layout.addWidget(self.save_mask_button, 4, 1,  1, 1, alignment=Qt.AlignTop)
        self.global_layout.addWidget(self.save_mask_notch_button, 5, 1,  1, 1, alignment=Qt.AlignTop)



    def init_howto(self):
        """Initialize control buttons for pop up how-to."""
        # Create the "How to Use" button
        self.howto_button = QPushButton("How to Use")
        self.howto_button.setStyleSheet(button_style_howto())
        self.howto_button.clicked.connect(lambda: show_howto_popup(self))

        # Add the button to the layout
        self.global_layout.addWidget(self.howto_button, 2, 1, 1, 2, alignment=Qt.AlignTop)
    def init_controls_batch(self):
        """Initialize control buttons for saving masks and images."""
        # Save mask button

        self.IA_button_batch = QPushButton("Run AI (batch)")
        self.IA_button_batch.setCheckable(False)
        self.IA_button_batch.setStyleSheet(button_style_ai())
        self.IA_button_batch.clicked.connect(self.run_auto_dl_process_batch)
        self.IA_button_batch.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.global_layout.addWidget(self.IA_button_batch, 4, 2, 2, 1)

    def add_images(self, paths):
        """Add images to the file list."""
        for path in paths:
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                if path not in self.image_paths:
                    self.image_paths.append(path)
                    self.list_widget.addItem(path)

    def display_selected_image(self):
        # Vérifier si c'est une sélection programmatique (Select All/Deselect All)
        if hasattr(self.list_widget, 'programmatic_selection') and self.list_widget.programmatic_selection:
            return  # Ne pas charger d'image pour les sélections programmatiques
        
        selected_items = self.list_widget.selectedItems()
        
        # Charger une image si un élément est sélectionné
        if selected_items:
            selected_item = selected_items[0]  # Prendre le premier élément sélectionné
            full_path = selected_item.data(Qt.UserRole)
            image = cv2.imread(full_path)

            if image is None:
                print(f"❌ Échec de lecture : {full_path}")
            else:
                print(f"✅ Image chargée : {full_path}")
                self.original_widget.set_image(image)
                self.processed_widget.set_image(None)
        else:
            # Aucun item sélectionné → on nettoie l'affichage
            self.original_widget.set_image(None)
            self.processed_widget.set_image(None)

    def scale(self):
        """Initialize scale filter buttons."""
        self.filter_150_button = QPushButton("<=150")
        self.filter_150_button.setCheckable(True)
        self.filter_150_button.setStyleSheet(button_scale_inactive())
        self.filter_150_button.clicked.connect(lambda checked: self.check_scale_filters(self.filter_150_button))

        self.filter_200_button = QPushButton(">200")
        self.filter_200_button.setCheckable(True)
        self.filter_200_button.setStyleSheet(button_scale_inactive())
        self.filter_200_button.clicked.connect(lambda checked: self.check_scale_filters(self.filter_200_button))
        
        self.global_layout.addWidget(self.filter_150_button, 2, 0, alignment=Qt.AlignTop)
        self.global_layout.addWidget(self.filter_200_button, 3, 0, alignment=Qt.AlignTop)


    def run_auto_dl_process(self):
        """Run the automatic deep learning process."""
        # Vérifier qu'un modèle est sélectionné
        if not hasattr(self, 'model_path') or not self.model_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Modèle requis", 
                                "Veuillez sélectionner un modèle avec le bouton 'Select a model' avant de continuer.")
            return

        print(f"Model path : {self.model_path}")
        # Initialize the EllipsePredictor with the model path and fit_crop_widget
        self.ellipse_predictor = EllipsePredictor(self.model_path, self.fit_crop_widget)

        # 🔁 Mode interactif (image déjà chargée depuis QListWidget)
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            print("Aucune image sélectionnée.")
            return
        
        # Vérifier qu'une seule image est sélectionnée
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Sélection multiple", "Select only 1 wafer")
            return
            
        path = selected_items[0].data(Qt.UserRole)
        
        # 🔮 Inference
        start_time = time.time()

        if self.filter_150_button.isChecked():
            result_img, mask, ellipse, pre_rot = self.ellipse_predictor.run_inference(path, dataset_type='150', apply_projection=True, plot=False)
            print(f"✅ Process 150 déclenchée")
        else:
            result_img, mask, ellipse, pre_rot = self.ellipse_predictor.run_inference(path, dataset_type='200', apply_projection=True, plot=False)

        # 🖼️ Sinon affichage dans le widget
        if result_img is not None:
            self.processed_widget.set_image(result_img)
        else:
            print("Erreur : pas d'image résultat.")

        if mask is not None:

            # Assign the processed mask to the widget
            self.original_widget.mask_image = mask
        else:
            print("Erreur : le masque généré est vide")
        
    def run_auto_dl_process_batch(self):

        output_dir = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sauvegarde")
        if not output_dir or not self.model_path:
            print("⚠️ Dossier ou modèle manquant.")
            return

        # Utiliser la nouvelle liste avec les méthodes du dragdrop panel
        selected_paths = self.drop_panel.get_selected_paths()
        all_paths = self.drop_panel.get_all_paths()
        
        # Si des éléments sont sélectionnés, utiliser seulement ceux-là
        # Sinon, utiliser tous les éléments
        if selected_paths:
            paths = selected_paths
            print(f"🔧 Traitement de {len(paths)} éléments sélectionnés")
        else:
            paths = all_paths
            print(f"🔧 Traitement de tous les {len(paths)} éléments")
            
        total = len(paths)

        # Auto-ajuste le nombre de threads selon la taille du batch
        if total < 12:
            n_jobs = 1
        else:
            n_jobs = min(4, total)

        t0 = time.time()

        results = Parallel(n_jobs=n_jobs)(
            delayed(process_single_image)(path, output_dir, self.model_path, idx, total)
            for idx, path in enumerate(paths)
        )

        print(f"\n✅ Tous les traitements terminés en {time.time() - t0:.2f}s")
    

    def check_scale_filters(self, clicked_button):
        """Handle scale filter button clicks."""
        if clicked_button == self.filter_150_button:
            self.filter_150_button.setChecked(True)
            self.filter_150_button.setStyleSheet(button_scale_active())

            self.filter_200_button.setChecked(False)
            self.filter_200_button.setStyleSheet(button_scale_inactive())

            print("<=150 activated")

        elif clicked_button == self.filter_200_button:
            self.filter_200_button.setChecked(True)
            self.filter_200_button.setStyleSheet(button_scale_active())

            self.filter_150_button.setChecked(False)
            self.filter_150_button.setStyleSheet(button_scale_inactive())

            print(">200 activated")

        self.fit_crop_widget = FitAndCrop(processed_label=self.processed_widget, filter_150_button=self.filter_150_button, filter_200_button=self.filter_200_button)
        
        # Réinitialiser EllipsePredictor avec le nouveau fit_crop_widget
        if hasattr(self, 'model_path'):
            self.ellipse_predictor = EllipsePredictor(self.model_path, self.fit_crop_widget)
