#!/usr/bin/env python3
"""
Event handlers for the Tkinter XML Creator.

This module contains all the event handler methods for the tkinter GUI application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog


class TkinterEventHandlers:
    """Event handlers for the Tkinter XML Creator."""
    
    def __init__(self, app):
        self.app = app
    
    def _new_file(self):
        """Create a new file."""
        self.app.current_data = self.app._create_empty_site()
        self.app.current_file = None
        self.app._load_data_to_gui()
        self.app.status_var.set("New file created")
    
    def _open_file(self):
        """Open an existing XML file."""
        filename = filedialog.askopenfilename(
            title="Open XML file",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Parse existing XML file
                site = self.app.parser.parse_file(filename)
                
                # Convert to our data format
                self.app.current_data = self._site_to_dict(site)
                self.app.current_file = filename
                self.app._load_data_to_gui()
                self.app.status_var.set(f"Opened: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error opening file: {e}")
    
    def _save_file(self):
        """Save current data to file."""
        if self.app.current_file:
            self._save_file_to_path(self.app.current_file)
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
            self.app.current_file = filename
            self._save_file_to_path(filename)
    
    def _save_file_to_path(self, filename):
        """Save current data to specified file path."""
        try:
            self.app._save_gui_to_data()
            xml_string = self.app._generate_xml_string()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_string)
            
            self.app.status_var.set(f"Saved: {filename}")
            
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
        comp_id = tk.simpledialog.askstring("Add Composition", "Enter composition ID:")
        if comp_id:
            new_comp = {'composition_id': comp_id, 'layers': []}
            self.app.current_data.setdefault('compositions', []).append(new_comp)
            self.app._update_composition_list()
            self.app._update_sides_list()
            self.app._refresh_preview()
    
    def _edit_composition(self):
        """Edit selected composition."""
        selection = self.app.comp_listbox.curselection()
        if selection:
            comp_index = selection[0]
            comp = self.app.current_data['compositions'][comp_index]
            
            # Show composition details
            self.app.comp_id_var.set(comp['composition_id'])
            
            # Update layer list
            self.app.layers_listbox.delete(0, tk.END)
            for layer in comp.get('layers', []):
                material = layer.get('material', 'Unknown')
                thickness = layer.get('thickness', 0)
                self.app.layers_listbox.insert(tk.END, f"{material}: {thickness}m")
            
            # Store current composition index
            self.app.current_comp_index = comp_index
    
    def _delete_composition(self):
        """Delete selected composition."""
        selection = self.app.comp_listbox.curselection()
        if selection:
            comp_index = selection[0]
            del self.app.current_data['compositions'][comp_index]
            self.app._update_composition_list()
            self.app._update_sides_list()
            self.app._refresh_preview()
    
    def _add_layer(self):
        """Add a new layer to current composition."""
        if hasattr(self.app, 'current_comp_index'):
            material = tk.simpledialog.askstring("Add Layer", "Enter material:")
            if material:
                thickness = tk.simpledialog.askfloat("Add Layer", "Enter thickness (m):")
                if thickness is not None:
                    new_layer = {'material': material, 'thickness': thickness}
                    comp = self.app.current_data['compositions'][self.app.current_comp_index]
                    comp.setdefault('layers', []).append(new_layer)
                    
                    # Update layer list
                    self.app.layers_listbox.insert(tk.END, f"{material}: {thickness}m")
                    self.app._update_composition_list()
                    self.app._refresh_preview()
        else:
            messagebox.showwarning("Warning", "Please select a composition first.")
    
    def _edit_layer(self):
        """Edit selected layer."""
        if hasattr(self.app, 'current_comp_index'):
            selection = self.app.layers_listbox.curselection()
            if selection:
                layer_index = selection[0]
                comp = self.app.current_data['compositions'][self.app.current_comp_index]
                layer = comp['layers'][layer_index]
                
                # Create edit dialog
                dialog = tk.Toplevel(self.app.root)
                dialog.title("Edit Layer")
                dialog.geometry("300x150")
                dialog.transient(self.app.root)
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
                    self.app._update_composition_list()
                    self.app._refresh_preview()
                    dialog.destroy()
                
                ttk.Button(dialog, text="Save", command=save_changes).pack(pady=10)
        else:
            messagebox.showwarning("Warning", "Please select a composition first.")
    
    def _delete_layer(self):
        """Delete selected layer."""
        if hasattr(self.app, 'current_comp_index'):
            selection = self.app.layers_listbox.curselection()
            if selection:
                layer_index = selection[0]
                comp = self.app.current_data['compositions'][self.app.current_comp_index]
                del comp['layers'][layer_index]
                
                # Update layer list
                self.app.layers_listbox.delete(layer_index)
                self.app._update_composition_list()
                self.app._refresh_preview()
        else:
            messagebox.showwarning("Warning", "Please select a composition first.")
    
    def _add_gps_point(self):
        """Add a new GPS point."""
        gps_id = tk.simpledialog.askstring("Add GPS Point", "Enter GPS point ID:")
        if gps_id:
            x = tk.simpledialog.askfloat("Add GPS Point", "Enter X coordinate:")
            if x is not None:
                y = tk.simpledialog.askfloat("Add GPS Point", "Enter Y coordinate:")
                if y is not None:
                    new_gps = {'id': gps_id, 'x': x, 'y': y}
                    self.app.current_data.setdefault('coordinates', {}).setdefault('xy_gps', []).append(new_gps)
                    self.app._update_gps_list()
                    self.app._refresh_preview()
    
    def _edit_gps_point(self):
        """Edit selected GPS point."""
        selection = self.app.gps_listbox.curselection()
        if selection:
            gps_index = selection[0]
            gps = self.app.current_data['coordinates']['xy_gps'][gps_index]
            
            # Show GPS details
            self.app.gps_id_var.set(gps['id'])
            self.app.gps_x_var.set(str(gps['x']))
            self.app.gps_y_var.set(str(gps['y']))
            
            # Store current GPS index
            self.app.current_gps_index = gps_index
    
    def _delete_gps_point(self):
        """Delete selected GPS point."""
        selection = self.app.gps_listbox.curselection()
        if selection:
            gps_index = selection[0]
            del self.app.current_data['coordinates']['xy_gps'][gps_index]
            self.app._update_gps_list()
            self.app._refresh_preview()
    
    def _create_rectangle(self):
        """Create rectangular GPS points."""
        try:
            width = float(self.app.rect_width_var.get())
            height = float(self.app.rect_height_var.get())
            
            # Clear existing GPS points
            self.app.current_data['coordinates']['xy_gps'] = []
            
            # Create rectangle GPS points
            gps_points = [
                {'id': 'gps_1', 'x': 0, 'y': 0},
                {'id': 'gps_2', 'x': width, 'y': 0},
                {'id': 'gps_3', 'x': width, 'y': height},
                {'id': 'gps_4', 'x': 0, 'y': height}
            ]
            
            self.app.current_data['coordinates']['xy_gps'] = gps_points
            self.app.current_data['perimeter']['xy_gps_id'] = ['gps_1', 'gps_2', 'gps_3', 'gps_4']
            
            self.app._update_gps_list()
            self.app._refresh_preview()
            messagebox.showinfo("Success", "Rectangle created successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for width and height.")
    
    def _add_side(self):
        """Add a new side."""
        gps_ids = [gps.get('id', '') for gps in self.app.current_data.get('coordinates', {}).get('xy_gps', [])]
        comp_ids = [comp.get('composition_id', '') for comp in self.app.current_data.get('compositions', [])]
        
        if len(gps_ids) < 2:
            messagebox.showerror("Error", "Need at least 2 GPS points to create a side.")
            return
        
        if not comp_ids:
            messagebox.showerror("Error", "Need at least 1 composition to create a side.")
            return
        
        # Create side dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Add Side")
        dialog.geometry("400x250")
        dialog.transient(self.app.root)
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
            self.app.current_data.setdefault('sides', []).append(new_side)
            self.app._update_sides_list()
            self.app._refresh_preview()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_side).pack(pady=10)
    
    def _edit_side(self):
        """Edit selected side."""
        selection = self.app.sides_listbox.curselection()
        if selection:
            side_index = selection[0]
            side = self.app.current_data['sides'][side_index]
            
            # Show side details
            self.app.side_gps1_var.set(side['xy_id'][0])
            self.app.side_gps2_var.set(side['xy_id'][1])
            self.app.side_comp_var.set(side['composition_id'])
            self.app.side_glazing_var.set(side.get('glazing', ''))
            
            # Store current side index
            self.app.current_side_index = side_index
    
    def _delete_side(self):
        """Delete selected side."""
        selection = self.app.sides_listbox.curselection()
        if selection:
            side_index = selection[0]
            del self.app.current_data['sides'][side_index]
            self.app._update_sides_list()
            self.app._refresh_preview()
    
    def _generate_sides(self):
        """Auto-generate sides from GPS points."""
        gps_points = self.app.current_data.get('coordinates', {}).get('xy_gps', [])
        comp_ids = [comp.get('composition_id', '') for comp in self.app.current_data.get('compositions', [])]
        
        if len(gps_points) < 3:
            messagebox.showerror("Error", "Need at least 3 GPS points to generate sides.")
            return
        
        if not comp_ids:
            messagebox.showerror("Error", "Need at least 1 composition to generate sides.")
            return
        
        # Auto-generate sides connecting consecutive GPS points
        self.app.current_data['sides'] = []
        for i in range(len(gps_points)):
            gps1 = gps_points[i]['id']
            gps2 = gps_points[(i + 1) % len(gps_points)]['id']
            
            side = {
                'xy_id': [gps1, gps2],
                'composition_id': comp_ids[0],  # Use first composition
                'glazing': None
            }
            self.app.current_data['sides'].append(side)
        
        self.app._update_sides_list()
        self.app._refresh_preview()
        messagebox.showinfo("Success", f"Generated {len(self.app.current_data['sides'])} sides!")
    
    def _refresh_preview(self):
        """Update the XML preview."""
        self.app._refresh_preview()
    
    def _copy_to_clipboard(self):
        """Copy XML to clipboard."""
        try:
            xml_string = self.app._generate_xml_string()
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(xml_string)
            messagebox.showinfo("Success", "XML copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Error copying to clipboard: {e}")
    
    def _generate_xml(self):
        """Generate and show XML in a new window."""
        try:
            xml_string = self.app._generate_xml_string()
            
            # Create new window
            xml_window = tk.Toplevel(self.app.root)
            xml_window.title("Generated XML")
            xml_window.geometry("800x600")
            
            # XML text area
            text_area = tk.scrolledtext.ScrolledText(xml_window, font=("Courier", 10))
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
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(xml_string)
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
    
    def _site_to_dict(self, site) -> dict:
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
            ]
        }
        return data
