#!/usr/bin/env python3
"""
Tkinter XML Creator for std.xsd schema.

This application provides a native GUI interface for creating and editing
XML files that conform to the std.xsd schema for building data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import xml.etree.ElementTree as ET
from typing import Dict, Any
from simbat.std_parser import XSDataStdParser


class TkinterXMLCreator:
    """Tkinter GUI application for creating XML instances based on std.xsd schema."""
    
    def __init__(self):
        self.parser = XSDataStdParser()
        self.current_data = self._create_empty_site()
        self.current_file = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("XML Creator - std.xsd (Tkinter)")
        self.root.geometry("1200x800")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create menu bar
        self._create_menu()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create tabs
        self._create_basic_info_tab()
        self._create_compositions_tab()
        self._create_gps_tab()
        self._create_sides_tab()
        self._create_masks_tab()
        self._create_preview_tab()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load initial data
        self._load_data_to_gui()
    
    def _create_empty_site(self) -> Dict[str, Any]:
        """Create an empty site data structure."""
        return {
            'name': 'New Building',
            'latitude': 45.0,
            'longitude': 5.0,
            'height': 10.0,
            'n_floors': 3,
            'roof_composition': '',
            'ground_composition': '',
            'floor_composition': '',
            'perimeter': {
                'offset_x': 0.0,
                'offset_y': 0.0,
                'xy_gps_id': []
            },
            'sides': [],
            'coordinates': {
                'offset_x': 0.0,
                'offset_y': 0.0,
                'xy_gps': []
            },
            'compositions': [],
            'masks': []
        }
    
    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file)
        file_menu.add_command(label="Open", command=self._open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self._save_file)
        file_menu.add_command(label="Save As", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_basic_info_tab(self):
        """Create the basic information tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Basic Info")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Building Information", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Basic info frame
        basic_frame = ttk.LabelFrame(scrollable_frame, text="Basic Information", padding=10)
        basic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Name
        ttk.Label(basic_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar(value="New Building")
        self.name_entry = ttk.Entry(basic_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Latitude and Longitude
        ttk.Label(basic_frame, text="Latitude:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lat_var = tk.StringVar(value="45.0")
        self.lat_entry = ttk.Entry(basic_frame, textvariable=self.lat_var, width=15)
        self.lat_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(basic_frame, text="Longitude:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.lon_var = tk.StringVar(value="5.0")
        self.lon_entry = ttk.Entry(basic_frame, textvariable=self.lon_var, width=15)
        self.lon_entry.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Height and Floors
        ttk.Label(basic_frame, text="Height (m):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.height_var = tk.StringVar(value="10.0")
        self.height_entry = ttk.Entry(basic_frame, textvariable=self.height_var, width=15)
        self.height_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(basic_frame, text="Number of Floors:").grid(row=2, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.floors_var = tk.StringVar(value="3")
        self.floors_entry = ttk.Entry(basic_frame, textvariable=self.floors_var, width=15)
        self.floors_entry.grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Composition references frame
        comp_frame = ttk.LabelFrame(scrollable_frame, text="Composition References", padding=10)
        comp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(comp_frame, text="Roof Composition ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.roof_comp_var = tk.StringVar()
        self.roof_comp_entry = ttk.Entry(comp_frame, textvariable=self.roof_comp_var, width=20)
        self.roof_comp_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(comp_frame, text="Ground Composition ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ground_comp_var = tk.StringVar()
        self.ground_comp_entry = ttk.Entry(comp_frame, textvariable=self.ground_comp_var, width=20)
        self.ground_comp_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(comp_frame, text="Floor Composition ID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.floor_comp_var = tk.StringVar()
        self.floor_comp_entry = ttk.Entry(comp_frame, textvariable=self.floor_comp_var, width=20)
        self.floor_comp_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Offset frame
        offset_frame = ttk.LabelFrame(scrollable_frame, text="Offset Values", padding=10)
        offset_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(offset_frame, text="Perimeter Offset X:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.perim_x_var = tk.StringVar(value="0.0")
        self.perim_x_entry = ttk.Entry(offset_frame, textvariable=self.perim_x_var, width=15)
        self.perim_x_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(offset_frame, text="Perimeter Offset Y:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.perim_y_var = tk.StringVar(value="0.0")
        self.perim_y_entry = ttk.Entry(offset_frame, textvariable=self.perim_y_var, width=15)
        self.perim_y_entry.grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(offset_frame, text="Coordinates Offset X:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.coord_x_var = tk.StringVar(value="0.0")
        self.coord_x_entry = ttk.Entry(offset_frame, textvariable=self.coord_x_var, width=15)
        self.coord_x_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(offset_frame, text="Coordinates Offset Y:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.coord_y_var = tk.StringVar(value="0.0")
        self.coord_y_entry = ttk.Entry(offset_frame, textvariable=self.coord_y_var, width=15)
        self.coord_y_entry.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_compositions_tab(self):
        """Create the compositions tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Compositions")
        
        # Left panel for composition list
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="Compositions", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Composition listbox
        self.comp_listbox = tk.Listbox(left_frame, height=15)
        self.comp_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.comp_listbox.bind('<<ListboxSelect>>', self._on_composition_select)
        
        # Composition buttons
        comp_btn_frame = ttk.Frame(left_frame)
        comp_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(comp_btn_frame, text="Add Composition", 
                  command=self._add_composition).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_btn_frame, text="Edit Composition", 
                  command=self._edit_composition).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_btn_frame, text="Delete Composition", 
                  command=self._delete_composition).pack(side=tk.LEFT)
        
        # Right panel for composition details
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="Composition Details", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Composition ID
        ttk.Label(right_frame, text="Composition ID:").pack(anchor=tk.W)
        self.comp_id_var = tk.StringVar()
        self.comp_id_entry = ttk.Entry(right_frame, textvariable=self.comp_id_var, width=30)
        self.comp_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Layers frame
        layers_frame = ttk.LabelFrame(right_frame, text="Layers", padding=10)
        layers_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Layers listbox
        self.layers_listbox = tk.Listbox(layers_frame, height=8)
        self.layers_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Layer buttons
        layer_btn_frame = ttk.Frame(layers_frame)
        layer_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(layer_btn_frame, text="Add Layer", 
                  command=self._add_layer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(layer_btn_frame, text="Edit Layer", 
                  command=self._edit_layer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(layer_btn_frame, text="Delete Layer", 
                  command=self._delete_layer).pack(side=tk.LEFT)
    
    def _create_gps_tab(self):
        """Create the GPS points tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="GPS Points")
        
        # Left panel for GPS list
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="GPS Points", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # GPS listbox
        self.gps_listbox = tk.Listbox(left_frame, height=15)
        self.gps_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # GPS buttons
        gps_btn_frame = ttk.Frame(left_frame)
        gps_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(gps_btn_frame, text="Add GPS Point", 
                  command=self._add_gps_point).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gps_btn_frame, text="Edit GPS Point", 
                  command=self._edit_gps_point).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gps_btn_frame, text="Delete GPS Point", 
                  command=self._delete_gps_point).pack(side=tk.LEFT)
        
        # Right panel for GPS details and quick add
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # GPS details frame
        gps_details_frame = ttk.LabelFrame(right_frame, text="GPS Point Details", padding=10)
        gps_details_frame.pack(fill=tk.X, pady=(10, 10))
        
        ttk.Label(gps_details_frame, text="Point ID:").pack(anchor=tk.W)
        self.gps_id_var = tk.StringVar()
        self.gps_id_entry = ttk.Entry(gps_details_frame, textvariable=self.gps_id_var, width=20)
        self.gps_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # X and Y coordinates
        coord_frame = ttk.Frame(gps_details_frame)
        coord_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(coord_frame, text="X Coordinate:").pack(side=tk.LEFT)
        self.gps_x_var = tk.StringVar()
        self.gps_x_entry = ttk.Entry(coord_frame, textvariable=self.gps_x_var, width=15)
        self.gps_x_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(coord_frame, text="Y Coordinate:").pack(side=tk.LEFT)
        self.gps_y_var = tk.StringVar()
        self.gps_y_entry = ttk.Entry(coord_frame, textvariable=self.gps_y_var, width=15)
        self.gps_y_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Quick add rectangle frame
        rect_frame = ttk.LabelFrame(right_frame, text="Quick Add Rectangle", padding=10)
        rect_frame.pack(fill=tk.X, pady=10)
        
        rect_coord_frame = ttk.Frame(rect_frame)
        rect_coord_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rect_coord_frame, text="Width (m):").pack(side=tk.LEFT)
        self.rect_width_var = tk.StringVar(value="20.0")
        self.rect_width_entry = ttk.Entry(rect_coord_frame, textvariable=self.rect_width_var, width=10)
        self.rect_width_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(rect_coord_frame, text="Height (m):").pack(side=tk.LEFT)
        self.rect_height_var = tk.StringVar(value="15.0")
        self.rect_height_entry = ttk.Entry(rect_coord_frame, textvariable=self.rect_height_var, width=10)
        self.rect_height_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(rect_frame, text="Create Rectangle", 
                  command=self._create_rectangle).pack(pady=10)
    
    def _create_sides_tab(self):
        """Create the building sides tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Building Sides")
        
        # Left panel for sides list
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="Building Sides", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Sides listbox
        self.sides_listbox = tk.Listbox(left_frame, height=15)
        self.sides_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Sides buttons
        sides_btn_frame = ttk.Frame(left_frame)
        sides_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(sides_btn_frame, text="Add Side", 
                  command=self._add_side).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(sides_btn_frame, text="Edit Side", 
                  command=self._edit_side).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(sides_btn_frame, text="Delete Side", 
                  command=self._delete_side).pack(side=tk.LEFT)
        
        # Right panel for side details and auto-generation
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Side details frame
        side_details_frame = ttk.LabelFrame(right_frame, text="Side Details", padding=10)
        side_details_frame.pack(fill=tk.X, pady=(10, 10))
        
        # GPS Point 1
        ttk.Label(side_details_frame, text="GPS Point 1:").pack(anchor=tk.W)
        self.side_gps1_var = tk.StringVar()
        self.side_gps1_combo = ttk.Combobox(side_details_frame, textvariable=self.side_gps1_var, width=20)
        self.side_gps1_combo.pack(fill=tk.X, pady=(0, 10))
        
        # GPS Point 2
        ttk.Label(side_details_frame, text="GPS Point 2:").pack(anchor=tk.W)
        self.side_gps2_var = tk.StringVar()
        self.side_gps2_combo = ttk.Combobox(side_details_frame, textvariable=self.side_gps2_var, width=20)
        self.side_gps2_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Composition
        ttk.Label(side_details_frame, text="Composition ID:").pack(anchor=tk.W)
        self.side_comp_var = tk.StringVar()
        self.side_comp_combo = ttk.Combobox(side_details_frame, textvariable=self.side_comp_var, width=20)
        self.side_comp_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Glazing
        ttk.Label(side_details_frame, text="Glazing ID (optional):").pack(anchor=tk.W)
        self.side_glazing_var = tk.StringVar()
        self.side_glazing_entry = ttk.Entry(side_details_frame, textvariable=self.side_glazing_var, width=20)
        self.side_glazing_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-generation frame
        auto_frame = ttk.LabelFrame(right_frame, text="Auto-generation", padding=10)
        auto_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(auto_frame, text="Generate sides from GPS points:").pack(pady=5)
        ttk.Button(auto_frame, text="Generate Sides", 
                  command=self._generate_sides).pack(pady=10)
    
    def _create_masks_tab(self):
        """Create the masks tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Masks")
        
        # Left panel for masks list
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="Masks", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Masks listbox
        self.masks_listbox = tk.Listbox(left_frame, height=15)
        self.masks_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.masks_listbox.bind('<<ListboxSelect>>', self._on_mask_select)
        
        # Masks buttons
        masks_btn_frame = ttk.Frame(left_frame)
        masks_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(masks_btn_frame, text="Add Mask", 
                  command=self._add_mask).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(masks_btn_frame, text="Edit Mask", 
                  command=self._edit_mask).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(masks_btn_frame, text="Delete Mask", 
                  command=self._delete_mask).pack(side=tk.LEFT)
        
        # Right panel for mask details
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="Mask Details", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Mask details frame
        mask_details_frame = ttk.LabelFrame(right_frame, text="Mask Properties", padding=10)
        mask_details_frame.pack(fill=tk.X, pady=5)
        
        # Height and Width
        ttk.Label(mask_details_frame, text="Height (m):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mask_height_var = tk.StringVar()
        self.mask_height_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_height_var, width=15)
        self.mask_height_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(mask_details_frame, text="Width (m):").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.mask_width_var = tk.StringVar()
        self.mask_width_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_width_var, width=15)
        self.mask_width_entry.grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Distance to ground and Exposure
        ttk.Label(mask_details_frame, text="Distance to Ground (m):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mask_distance_var = tk.StringVar()
        self.mask_distance_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_distance_var, width=15)
        self.mask_distance_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(mask_details_frame, text="Exposure (°):").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.mask_exposure_var = tk.StringVar()
        self.mask_exposure_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_exposure_var, width=15)
        self.mask_exposure_entry.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Slope and Rotation
        ttk.Label(mask_details_frame, text="Slope (°):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.mask_slope_var = tk.StringVar(value="90")
        self.mask_slope_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_slope_var, width=15)
        self.mask_slope_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(mask_details_frame, text="Rotation (°):").grid(row=2, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.mask_rotation_var = tk.StringVar(value="0")
        self.mask_rotation_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_rotation_var, width=15)
        self.mask_rotation_entry.grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Elevation
        ttk.Label(mask_details_frame, text="Elevation (m):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.mask_elevation_var = tk.StringVar(value="0")
        self.mask_elevation_entry = ttk.Entry(mask_details_frame, textvariable=self.mask_elevation_var, width=15)
        self.mask_elevation_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Save button
        ttk.Button(mask_details_frame, text="Save Mask", 
                  command=self._save_mask).grid(row=4, column=0, columnspan=4, pady=10)
    
    def _create_preview_tab(self):
        """Create the preview tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Preview")
        
        # Title
        ttk.Label(frame, text="XML Preview", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        
        # Preview text area
        self.preview_text = scrolledtext.ScrolledText(frame, height=25, width=80, 
                                                    font=("Courier", 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Preview buttons
        preview_btn_frame = ttk.Frame(frame)
        preview_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(preview_btn_frame, text="Refresh Preview", 
                  command=self._refresh_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preview_btn_frame, text="Copy to Clipboard", 
                  command=self._copy_to_clipboard).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preview_btn_frame, text="Generate XML", 
                  command=self._generate_xml).pack(side=tk.LEFT)
    
    def _load_data_to_gui(self):
        """Load current data into GUI elements."""
        # Basic info
        self.name_var.set(self.current_data.get('name', ''))
        self.lat_var.set(str(self.current_data.get('latitude', 0)))
        self.lon_var.set(str(self.current_data.get('longitude', 0)))
        self.height_var.set(str(self.current_data.get('height', 0)))
        self.floors_var.set(str(self.current_data.get('n_floors', 1)))
        self.roof_comp_var.set(self.current_data.get('roof_composition', ''))
        self.ground_comp_var.set(self.current_data.get('ground_composition', ''))
        self.floor_comp_var.set(self.current_data.get('floor_composition', ''))
        self.perim_x_var.set(str(self.current_data.get('perimeter', {}).get('offset_x', 0)))
        self.perim_y_var.set(str(self.current_data.get('perimeter', {}).get('offset_y', 0)))
        self.coord_x_var.set(str(self.current_data.get('coordinates', {}).get('offset_x', 0)))
        self.coord_y_var.set(str(self.current_data.get('coordinates', {}).get('offset_y', 0)))
        
        # Update lists
        self._update_composition_list()
        self._update_gps_list()
        self._update_sides_list()
        self._update_masks_list()
        self._refresh_preview()
    
    def _save_gui_to_data(self):
        """Save GUI elements to current data."""
        # Basic info
        self.current_data['name'] = self.name_var.get()
        self.current_data['latitude'] = float(self.lat_var.get() or 0)
        self.current_data['longitude'] = float(self.lon_var.get() or 0)
        self.current_data['height'] = float(self.height_var.get() or 0)
        self.current_data['n_floors'] = int(self.floors_var.get() or 1)
        self.current_data['roof_composition'] = self.roof_comp_var.get()
        self.current_data['ground_composition'] = self.ground_comp_var.get()
        self.current_data['floor_composition'] = self.floor_comp_var.get()
        
        # Perimeter
        if 'perimeter' not in self.current_data:
            self.current_data['perimeter'] = {}
        self.current_data['perimeter']['offset_x'] = float(self.perim_x_var.get() or 0)
        self.current_data['perimeter']['offset_y'] = float(self.perim_y_var.get() or 0)
        
        # Coordinates
        if 'coordinates' not in self.current_data:
            self.current_data['coordinates'] = {}
        self.current_data['coordinates']['offset_x'] = float(self.coord_x_var.get() or 0)
        self.current_data['coordinates']['offset_y'] = float(self.coord_y_var.get() or 0)
    
    def _update_composition_list(self):
        """Update the composition list display."""
        self.comp_listbox.delete(0, tk.END)
        compositions = self.current_data.get('compositions', [])
        for comp in compositions:
            comp_id = comp.get('composition_id', 'Unknown')
            layer_count = len(comp.get('layers', []))
            self.comp_listbox.insert(tk.END, f"{comp_id} ({layer_count} layers)")
    
    def _update_gps_list(self):
        """Update the GPS points list display."""
        self.gps_listbox.delete(0, tk.END)
        gps_points = self.current_data.get('coordinates', {}).get('xy_gps', [])
        for gps in gps_points:
            gps_id = gps.get('id', 'Unknown')
            x = gps.get('x', 0)
            y = gps.get('y', 0)
            self.gps_listbox.insert(tk.END, f"{gps_id}: ({x}, {y})")
        
        # Update GPS combos in sides tab
        gps_ids = [gps.get('id', '') for gps in gps_points]
        self.side_gps1_combo['values'] = gps_ids
        self.side_gps2_combo['values'] = gps_ids
    
    def _update_sides_list(self):
        """Update the sides list display."""
        self.sides_listbox.delete(0, tk.END)
        sides = self.current_data.get('sides', [])
        for i, side in enumerate(sides):
            xy_ids = side.get('xy_id', ['', ''])
            comp_id = side.get('composition_id', 'Unknown')
            self.sides_listbox.insert(tk.END, f"Side {i+1}: {xy_ids[0]} → {xy_ids[1]} ({comp_id})")
        
        # Update composition combos in sides tab
        compositions = self.current_data.get('compositions', [])
        comp_ids = [comp.get('composition_id', '') for comp in compositions]
        self.side_comp_combo['values'] = comp_ids
        # If editor has a current comp index, keep it in sync (if list changed)
        if hasattr(self, 'current_comp_index') and self.current_comp_index < len(compositions):
            self.comp_listbox.selection_clear(0, tk.END)
            self.comp_listbox.selection_set(self.current_comp_index)
            self.comp_listbox.see(self.current_comp_index)
    
    def _update_masks_list(self):
        """Update the masks list display."""
        self.masks_listbox.delete(0, tk.END)
        masks = self.current_data.get('masks', [])
        for i, mask in enumerate(masks):
            height = mask.get('height', 0)
            width = mask.get('width', 0)
            exposure = mask.get('exposure', 0)
            self.masks_listbox.insert(tk.END, f"Mask {i+1}: {height}m×{width}m, {exposure}°")
    
    def _refresh_preview(self):
        """Update the XML preview."""
        try:
            self._save_gui_to_data()
            xml_string = self._generate_xml_string()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, xml_string)
        except Exception as e:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Error generating preview: {e}")
    
    def _generate_xml_string(self) -> str:
        """Generate XML string from current data."""
        # Create XML structure
        root = ET.Element('site', xmlns="http://simbat.fr/std")
        
        # Basic info
        ET.SubElement(root, 'name').text = str(self.current_data.get('name', ''))
        ET.SubElement(root, 'latitude').text = str(self.current_data.get('latitude', 0))
        ET.SubElement(root, 'longitude').text = str(self.current_data.get('longitude', 0))
        ET.SubElement(root, 'height').text = str(self.current_data.get('height', 0))
        
        # Perimeter
        perimeter = ET.SubElement(root, 'perimeter')
        ET.SubElement(perimeter, 'offset_x').text = str(self.current_data.get('perimeter', {}).get('offset_x', 0))
        ET.SubElement(perimeter, 'offset_y').text = str(self.current_data.get('perimeter', {}).get('offset_y', 0))
        for gps_id in self.current_data.get('perimeter', {}).get('xy_gps_id', []):
            ET.SubElement(perimeter, 'xy_gps_id').text = str(gps_id)
        
        ET.SubElement(root, 'n_floors').text = str(self.current_data.get('n_floors', 1))
        ET.SubElement(root, 'roof_composition').text = str(self.current_data.get('roof_composition', ''))
        ET.SubElement(root, 'ground_composition').text = str(self.current_data.get('ground_composition', ''))
        if self.current_data.get('floor_composition'):
            ET.SubElement(root, 'floor_composition').text = str(self.current_data.get('floor_composition', ''))
        
        # Sides
        sides_elem = ET.SubElement(root, 'sides')
        for side in self.current_data.get('sides', []):
            side_elem = ET.SubElement(sides_elem, 'side')
            for xy_id in side.get('xy_id', []):
                ET.SubElement(side_elem, 'xy_id').text = str(xy_id)
            ET.SubElement(side_elem, 'composition_id').text = str(side.get('composition_id', ''))
            if side.get('glazing'):
                ET.SubElement(side_elem, 'glazing').text = str(side.get('glazing', ''))
        
        # Coordinates
        coords = ET.SubElement(root, 'coordinates')
        ET.SubElement(coords, 'offset_x').text = str(self.current_data.get('coordinates', {}).get('offset_x', 0))
        ET.SubElement(coords, 'offset_y').text = str(self.current_data.get('coordinates', {}).get('offset_y', 0))
        for gps in self.current_data.get('coordinates', {}).get('xy_gps', []):
            gps_elem = ET.SubElement(coords, 'xy_gps')
            ET.SubElement(gps_elem, 'id').text = str(gps.get('id', ''))
            ET.SubElement(gps_elem, 'x').text = str(gps.get('x', 0))
            ET.SubElement(gps_elem, 'y').text = str(gps.get('y', 0))
        
        # Compositions
        comps = ET.SubElement(root, 'compositions')
        for comp in self.current_data.get('compositions', []):
            comp_elem = ET.SubElement(comps, 'composition')
            ET.SubElement(comp_elem, 'composition_id').text = str(comp.get('composition_id', ''))
            for layer in comp.get('layers', []):
                layer_elem = ET.SubElement(comp_elem, 'layer')
                ET.SubElement(layer_elem, 'material').text = str(layer.get('material', ''))
                ET.SubElement(layer_elem, 'thickness').text = str(layer.get('thickness', 0))
        
        # Masks (optional)
        masks = self.current_data.get('masks', [])
        if masks:
            masks_elem = ET.SubElement(root, 'masks')
            for mask in masks:
                mask_elem = ET.SubElement(masks_elem, 'mask')
                ET.SubElement(mask_elem, 'height').text = str(mask.get('height', 0))
                ET.SubElement(mask_elem, 'width').text = str(mask.get('width', 0))
                ET.SubElement(mask_elem, 'distance_to_ground_gravity_m').text = str(mask.get('distance_to_ground_gravity_m', 0))
                ET.SubElement(mask_elem, 'exposure').text = str(mask.get('exposure', 0))
                ET.SubElement(mask_elem, 'slope').text = str(mask.get('slope', 90))
                ET.SubElement(mask_elem, 'rotation').text = str(mask.get('rotation', 0))
                ET.SubElement(mask_elem, 'elevation').text = str(mask.get('elevation', 0))
        
        # Format XML
        ET.indent(root, space="    ")
        return ET.tostring(root, encoding='unicode')
    
    def _new_file(self):
        """Create a new file."""
        self.current_data = self._create_empty_site()
        self.current_file = None
        self._load_data_to_gui()
        self.status_var.set("New file created")
    
    def _open_file(self):
        """Open an existing XML file."""
        filename = filedialog.askopenfilename(
            title="Open XML file",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Parse existing XML file
                site = self.parser.parse_file(filename)
                
                # Convert to our data format
                self.current_data = self._site_to_dict(site)
                self.current_file = filename
                self._load_data_to_gui()
                self.status_var.set(f"Opened: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error opening file: {e}")
    
    def _save_file(self):
        """Save current data to file."""
        if self.current_file:
            self._save_file_to_path(self.current_file)
        else:
            self._save_file_as()
    
    def _save_file_as(self):
        """Save current data to a new file."""
        filename = filedialog.asksaveasfilename(
            title="Save XML file",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self._save_file_to_path(filename)
    
    def _save_file_to_path(self, filename):
        """Save current data to specified file path."""
        try:
            self._save_gui_to_data()
            xml_string = self._generate_xml_string()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_string)
            
            self.status_var.set(f"Saved: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {e}")
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "XML Creator for std.xsd Schema\n\n"
            "A Tkinter-based GUI application for creating and editing\n"
            "XML files that conform to the std.xsd schema.\n\n"
            "Version: 1.0\n"
            "Built with Python and Tkinter"
        )
    
    def _add_composition(self):
        """Add a new composition."""
        comp_id = simpledialog.askstring("Add Composition", "Enter composition ID:")
        if comp_id:
            new_comp = {'composition_id': comp_id, 'layers': []}
            self.current_data.setdefault('compositions', []).append(new_comp)
            self._update_composition_list()
            self._update_sides_list()
            self._refresh_preview()
    
    def _edit_composition(self):
        """Edit selected composition."""
        selection = self.comp_listbox.curselection()
        if selection:
            self._load_composition_into_editor(selection[0])
    
    def _delete_composition(self):
        """Delete selected composition."""
        selection = self.comp_listbox.curselection()
        if selection:
            comp_index = selection[0]
            del self.current_data['compositions'][comp_index]
            self._update_composition_list()
            self._update_sides_list()
            self._refresh_preview()

    def _on_composition_select(self, event):
        """Handle list selection to load composition details automatically."""
        selection = self.comp_listbox.curselection()
        if selection:
            self._load_composition_into_editor(selection[0])

    def _load_composition_into_editor(self, comp_index: int):
        """Load composition details and layers into the right editor panel."""
        comp = self.current_data['compositions'][comp_index]
        # Show composition details
        self.comp_id_var.set(comp.get('composition_id', ''))
        # Update layer list
        self.layers_listbox.delete(0, tk.END)
        for layer in comp.get('layers', []):
            material = layer.get('material', 'Unknown')
            thickness = layer.get('thickness', 0)
            self.layers_listbox.insert(tk.END, f"{material}: {thickness}m")
        # Store current composition index
        self.current_comp_index = comp_index
    
    def _add_layer(self):
        """Add a new layer to current composition."""
        if hasattr(self, 'current_comp_index'):
            material = simpledialog.askstring("Add Layer", "Enter material:")
            if material:
                thickness = simpledialog.askfloat("Add Layer", "Enter thickness (m):")
                if thickness is not None:
                    new_layer = {'material': material, 'thickness': thickness}
                    comp = self.current_data['compositions'][self.current_comp_index]
                    comp.setdefault('layers', []).append(new_layer)
                    
                    # Update layer list
                    self.layers_listbox.insert(tk.END, f"{material}: {thickness}m")
                    self._update_composition_list()
                    self._refresh_preview()
        else:
            messagebox.showwarning("Warning", "Please select a composition first.")
    
    def _edit_layer(self):
        """Edit selected layer."""
        if hasattr(self, 'current_comp_index'):
            selection = self.layers_listbox.curselection()
            if selection:
                layer_index = selection[0]
                comp = self.current_data['compositions'][self.current_comp_index]
                layer = comp['layers'][layer_index]
                
                # Create edit dialog
                dialog = tk.Toplevel(self.root)
                dialog.title("Edit Layer")
                dialog.geometry("300x150")
                dialog.transient(self.root)
                dialog.grab_set()
                
                ttk.Label(dialog, text="Material:").pack(pady=5)
                material_var = tk.StringVar(value=layer.get('material', ''))
                material_entry = ttk.Entry(dialog, textvariable=material_var, width=30)
                material_entry.pack(pady=5)
                
                ttk.Label(dialog, text="Thickness (m):").pack(pady=5)
                thickness_var = tk.StringVar(value=str(layer.get('thickness', 0)))
                thickness_entry = ttk.Entry(dialog, textvariable=thickness_var, width=30)
                thickness_entry.pack(pady=5)
                
                def save_changes():
                    layer['material'] = material_var.get()
                    layer['thickness'] = float(thickness_var.get() or 0)
                    self._update_composition_list()
                    self._refresh_preview()
                    dialog.destroy()
                
                ttk.Button(dialog, text="Save", command=save_changes).pack(pady=10)
        else:
            messagebox.showwarning("Warning", "Please select a composition first.")
    
    def _delete_layer(self):
        """Delete selected layer."""
        if hasattr(self, 'current_comp_index'):
            selection = self.layers_listbox.curselection()
            if selection:
                layer_index = selection[0]
                comp = self.current_data['compositions'][self.current_comp_index]
                del comp['layers'][layer_index]
                
                # Update layer list
                self.layers_listbox.delete(layer_index)
                self._update_composition_list()
                self._refresh_preview()
        else:
            messagebox.showwarning("Warning", "Please select a composition first.")
    
    def _add_gps_point(self):
        """Add a new GPS point."""
        gps_id = simpledialog.askstring("Add GPS Point", "Enter GPS point ID:")
        if gps_id:
            x = simpledialog.askfloat("Add GPS Point", "Enter X coordinate:")
            if x is not None:
                y = simpledialog.askfloat("Add GPS Point", "Enter Y coordinate:")
                if y is not None:
                    new_gps = {'id': gps_id, 'x': x, 'y': y}
                    self.current_data.setdefault('coordinates', {}).setdefault('xy_gps', []).append(new_gps)
                    self._update_gps_list()
                    self._refresh_preview()
    
    def _edit_gps_point(self):
        """Edit selected GPS point."""
        selection = self.gps_listbox.curselection()
        if selection:
            gps_index = selection[0]
            gps = self.current_data['coordinates']['xy_gps'][gps_index]
            
            # Show GPS details
            self.gps_id_var.set(gps['id'])
            self.gps_x_var.set(str(gps['x']))
            self.gps_y_var.set(str(gps['y']))
            
            # Store current GPS index
            self.current_gps_index = gps_index
    
    def _delete_gps_point(self):
        """Delete selected GPS point."""
        selection = self.gps_listbox.curselection()
        if selection:
            gps_index = selection[0]
            del self.current_data['coordinates']['xy_gps'][gps_index]
            self._update_gps_list()
            self._refresh_preview()
    
    def _create_rectangle(self):
        """Create rectangular GPS points."""
        try:
            width = float(self.rect_width_var.get())
            height = float(self.rect_height_var.get())
            
            # Clear existing GPS points
            self.current_data['coordinates']['xy_gps'] = []
            
            # Create rectangle GPS points
            gps_points = [
                {'id': 'gps_1', 'x': 0, 'y': 0},
                {'id': 'gps_2', 'x': width, 'y': 0},
                {'id': 'gps_3', 'x': width, 'y': height},
                {'id': 'gps_4', 'x': 0, 'y': height}
            ]
            
            self.current_data['coordinates']['xy_gps'] = gps_points
            self.current_data['perimeter']['xy_gps_id'] = ['gps_1', 'gps_2', 'gps_3', 'gps_4']
            
            self._update_gps_list()
            self._refresh_preview()
            messagebox.showinfo("Success", "Rectangle created successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for width and height.")
    
    def _add_side(self):
        """Add a new side."""
        gps_ids = [gps.get('id', '') for gps in self.current_data.get('coordinates', {}).get('xy_gps', [])]
        comp_ids = [comp.get('composition_id', '') for comp in self.current_data.get('compositions', [])]
        
        if len(gps_ids) < 2:
            messagebox.showerror("Error", "Need at least 2 GPS points to create a side.")
            return
        
        if not comp_ids:
            messagebox.showerror("Error", "Need at least 1 composition to create a side.")
            return
        
        # Create side dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Side")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="GPS Point 1:").pack(pady=5)
        gps1_var = tk.StringVar()
        gps1_combo = ttk.Combobox(dialog, textvariable=gps1_var, values=gps_ids)
        gps1_combo.pack(pady=5)
        
        ttk.Label(dialog, text="GPS Point 2:").pack(pady=5)
        gps2_var = tk.StringVar()
        gps2_combo = ttk.Combobox(dialog, textvariable=gps2_var, values=gps_ids)
        gps2_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Composition:").pack(pady=5)
        comp_var = tk.StringVar()
        comp_combo = ttk.Combobox(dialog, textvariable=comp_var, values=comp_ids)
        comp_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Glazing (optional):").pack(pady=5)
        glazing_var = tk.StringVar()
        glazing_entry = ttk.Entry(dialog, textvariable=glazing_var, width=30)
        glazing_entry.pack(pady=5)
        
        def save_side():
            new_side = {
                'xy_id': [gps1_var.get(), gps2_var.get()],
                'composition_id': comp_var.get(),
                'glazing': glazing_var.get() if glazing_var.get() else None
            }
            self.current_data.setdefault('sides', []).append(new_side)
            self._update_sides_list()
            self._refresh_preview()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_side).pack(pady=10)
    
    def _edit_side(self):
        """Edit selected side."""
        selection = self.sides_listbox.curselection()
        if selection:
            side_index = selection[0]
            side = self.current_data['sides'][side_index]
            
            # Show side details
            self.side_gps1_var.set(side['xy_id'][0])
            self.side_gps2_var.set(side['xy_id'][1])
            self.side_comp_var.set(side['composition_id'])
            self.side_glazing_var.set(side.get('glazing', ''))
            
            # Store current side index
            self.current_side_index = side_index
    
    def _delete_side(self):
        """Delete selected side."""
        selection = self.sides_listbox.curselection()
        if selection:
            side_index = selection[0]
            del self.current_data['sides'][side_index]
            self._update_sides_list()
            self._refresh_preview()
    
    def _generate_sides(self):
        """Auto-generate sides from GPS points."""
        gps_points = self.current_data.get('coordinates', {}).get('xy_gps', [])
        comp_ids = [comp.get('composition_id', '') for comp in self.current_data.get('compositions', [])]
        
        if len(gps_points) < 3:
            messagebox.showerror("Error", "Need at least 3 GPS points to generate sides.")
            return
        
        if not comp_ids:
            messagebox.showerror("Error", "Need at least 1 composition to generate sides.")
            return
        
        # Auto-generate sides connecting consecutive GPS points
        self.current_data['sides'] = []
        for i in range(len(gps_points)):
            gps1 = gps_points[i]['id']
            gps2 = gps_points[(i + 1) % len(gps_points)]['id']
            
            side = {
                'xy_id': [gps1, gps2],
                'composition_id': comp_ids[0],  # Use first composition
                'glazing': None
            }
            self.current_data['sides'].append(side)
        
        self._update_sides_list()
        self._refresh_preview()
        messagebox.showinfo("Success", f"Generated {len(self.current_data['sides'])} sides!")
    
    def _add_mask(self):
        """Add a new mask."""
        # Clear form for new mask
        self._clear_mask_form()
        self.current_mask_index = None
    
    def _edit_mask(self):
        """Edit selected mask."""
        selection = self.masks_listbox.curselection()
        if selection:
            self._load_mask_into_editor(selection[0])
    
    def _delete_mask(self):
        """Delete selected mask."""
        selection = self.masks_listbox.curselection()
        if selection:
            mask_index = selection[0]
            del self.current_data['masks'][mask_index]
            self._update_masks_list()
            self._refresh_preview()
    
    def _on_mask_select(self, event):
        """Handle mask list selection to load mask details automatically."""
        selection = self.masks_listbox.curselection()
        if selection:
            self._load_mask_into_editor(selection[0])
    
    def _load_mask_into_editor(self, mask_index: int):
        """Load mask details into the editor form."""
        mask = self.current_data['masks'][mask_index]
        self.mask_height_var.set(str(mask.get('height', 0)))
        self.mask_width_var.set(str(mask.get('width', 0)))
        self.mask_distance_var.set(str(mask.get('distance_to_ground_gravity_m', 0)))
        self.mask_exposure_var.set(str(mask.get('exposure', 0)))
        self.mask_slope_var.set(str(mask.get('slope', 90)))
        self.mask_rotation_var.set(str(mask.get('rotation', 0)))
        self.mask_elevation_var.set(str(mask.get('elevation', 0)))
        self.current_mask_index = mask_index
    
    def _clear_mask_form(self):
        """Clear the mask form."""
        self.mask_height_var.set("")
        self.mask_width_var.set("")
        self.mask_distance_var.set("")
        self.mask_exposure_var.set("")
        self.mask_slope_var.set("90")
        self.mask_rotation_var.set("0")
        self.mask_elevation_var.set("0")
    
    def _save_mask(self):
        """Save mask from form to data."""
        try:
            mask_data = {
                'height': float(self.mask_height_var.get() or 0),
                'width': float(self.mask_width_var.get() or 0),
                'distance_to_ground_gravity_m': float(self.mask_distance_var.get() or 0),
                'exposure': float(self.mask_exposure_var.get() or 0),
                'slope': float(self.mask_slope_var.get() or 90),
                'rotation': float(self.mask_rotation_var.get() or 0),
                'elevation': float(self.mask_elevation_var.get() or 0)
            }
            
            if hasattr(self, 'current_mask_index') and self.current_mask_index is not None:
                # Edit existing mask
                self.current_data['masks'][self.current_mask_index] = mask_data
            else:
                # Add new mask
                self.current_data.setdefault('masks', []).append(mask_data)
            
            self._update_masks_list()
            self._refresh_preview()
            self._clear_mask_form()
            self.current_mask_index = None
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all mask properties.")
    
    def _copy_to_clipboard(self):
        """Copy XML to clipboard."""
        try:
            xml_string = self._generate_xml_string()
            self.root.clipboard_clear()
            self.root.clipboard_append(xml_string)
            messagebox.showinfo("Success", "XML copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Error copying to clipboard: {e}")
    
    def _generate_xml(self):
        """Generate and show XML in a new window."""
        try:
            xml_string = self._generate_xml_string()
            
            # Create new window
            xml_window = tk.Toplevel(self.root)
            xml_window.title("Generated XML")
            xml_window.geometry("800x600")
            
            # XML text area
            text_area = scrolledtext.ScrolledText(xml_window, font=("Courier", 10))
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(1.0, xml_string)
            
            # Buttons
            btn_frame = ttk.Frame(xml_window)
            btn_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(btn_frame, text="Copy", 
                      command=lambda: self._copy_xml_to_clipboard(xml_string)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(btn_frame, text="Save", 
                      command=lambda: self._save_xml_file(xml_string)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(btn_frame, text="Close", 
                      command=xml_window.destroy).pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating XML: {e}")
    
    def _copy_xml_to_clipboard(self, xml_string):
        """Copy XML string to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(xml_string)
        messagebox.showinfo("Success", "XML copied to clipboard!")
    
    def _save_xml_file(self, xml_string):
        """Save XML string to file."""
        filename = filedialog.asksaveasfilename(
            title="Save XML file",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(xml_string)
                messagebox.showinfo("Success", f"XML saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {e}")
    
    def _site_to_dict(self, site) -> Dict[str, Any]:
        """Convert Site object to dictionary format."""
        data = {
            'name': site.name,
            'latitude': site.latitude,
            'longitude': site.longitude,
            'height': site.height,
            'n_floors': site.n_floors,
            'roof_composition': site.roof_composition,
            'ground_composition': site.ground_composition,
            'floor_composition': site.floor_composition,
            'perimeter': {
                'offset_x': site.perimeter.offset_x,
                'offset_y': site.perimeter.offset_y,
                'xy_gps_id': site.perimeter.xy_gps_id
            },
            'coordinates': {
                'offset_x': site.coordinates.offset_x,
                'offset_y': site.coordinates.offset_y,
                'xy_gps': [
                    {'id': gps.id, 'x': gps.x, 'y': gps.y}
                    for gps in site.coordinates.xy_gps
                ]
            },
            'compositions': [
                {
                    'composition_id': comp.composition_id,
                    'layers': [
                        {'material': layer.material, 'thickness': layer.thickness}
                        for layer in comp.layer
                    ]
                }
                for comp in site.compositions.composition
            ],
            'sides': [
                {
                    'xy_id': side.xy_id,
                    'composition_id': side.composition_id,
                    'glazing': side.glazing
                }
                for side in site.sides.side
            ],
            'masks': [
                {
                    'height': mask.height,
                    'width': mask.width,
                    'distance_to_ground_gravity_m': mask.distance_to_ground_gravity_m,
                    'exposure': mask.exposure,
                    'slope': mask.slope,
                    'rotation': mask.rotation,
                    'elevation': mask.elevation
                }
                for mask in (site.masks.mask if site.masks else [])
            ]
        }
        return data
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = TkinterXMLCreator()
    app.run()
