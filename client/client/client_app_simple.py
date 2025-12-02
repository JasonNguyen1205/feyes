#!/usr/bin/env python3
"""
Visual AOI Client Application (Simplified)
Captures images from local camera and sends to central API server for processing.
"""

import os
import sys
import json
import time
import base64
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from io import BytesIO

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import cv2
import numpy as np
from PIL import Image, ImageTk

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualAOIClient:
    """Visual AOI Client Application - connects to API server for inspection processing."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Visual AOI - Inspection Client")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Image storage
        self.current_image = None
        self.current_image_pil = None  # For resizing
        
        # Status variables
        self.selected_product_var = tk.StringVar()
        self.overall_result_var = tk.StringVar(value="No inspection run yet")
        self.server_status_var = tk.StringVar(value="Disconnected")
        self.session_status_var = tk.StringVar(value="No Session")
        
        # API client
        self.server_url = "http://10.100.27.156:5000"
        self.session_id = None
        
        # Session management
        self.session_active = False
        
        # Camera settings
        self.camera = None
        self.camera_initialized = False
        self.selected_camera_type = None
        self.pending_camera_info = None  # Store camera info until product selection  # 'tis' or 'raspi'
        self.available_cameras = []
        
        # Barcode inspection mode
        self.auto_inspect_enabled = tk.BooleanVar(value=True)  # Default to auto-inspect mode
        
        # Initialize UI
        self.init_ui()
        
        # Setup keyboard shortcuts for barcode scanning workflow
        self.setup_keyboard_shortcuts()
        
        # Initialize camera scanning and server status check
        self.check_server_connection()
    
    def show_info_dialog(self, title, message):
        """Show info dialog with proper parent configuration."""
        self.root.attributes('-topmost', True)
        messagebox.showinfo(title, message, parent=self.root)
        self.root.attributes('-topmost', False)
    
    def show_error_dialog(self, title, message):
        """Show error dialog with proper parent configuration."""
        self.root.attributes('-topmost', True)
        messagebox.showerror(title, message, parent=self.root)
        self.root.attributes('-topmost', False)
    
    def show_warning_dialog(self, title, message):
        """Show warning dialog with proper parent configuration."""
        self.root.attributes('-topmost', True)
        messagebox.showwarning(title, message, parent=self.root)
        self.root.attributes('-topmost', False)
    
    def show_confirm_dialog(self, title, message):
        """Show confirmation dialog with proper parent configuration."""
        self.root.attributes('-topmost', True)
        result = messagebox.askyesno(title, message, parent=self.root)
        self.root.attributes('-topmost', False)
        return result
        
    def check_server_connection(self):
        """Check server connection status."""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.server_status_var.set("Connected")
                self.server_status_label.config(fg='green')
            else:
                self.server_status_var.set("Disconnected")
                self.server_status_label.config(fg='red')
        except:
            self.server_status_var.set("Disconnected")
            self.server_status_label.config(fg='red')
        
    def init_ui(self):
        """Initialize the main UI components."""
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Server connection frame
        self.init_server_frame(main_frame)
        
        # Product selection frame
        self.init_product_frame(main_frame)
        
        # Create horizontal layout
        content_frame = tk.Frame(main_frame, bg='#f0f0f0')
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left panel - Controls
        left_panel = tk.Frame(content_frame, bg='#f0f0f0', width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.init_camera_frame(left_panel)
        
        # Center panel - Device Results display
        center_panel = tk.Frame(content_frame, bg='white', relief='sunken', bd=2, width=400)
        center_panel.pack(side="left", fill="y", padx=(0, 10))
        center_panel.pack_propagate(False)
        
        # Device results area
        self.init_device_results_frame(center_panel)
        
        # Right panel - Results (ROI Details - made bigger)
        right_panel = tk.Frame(content_frame, bg='#f0f0f0', width=500)
        right_panel.pack(side="right", fill="both", expand=True)
        right_panel.pack_propagate(False)
        
        self.init_results_frame(right_panel)
        
    def init_server_frame(self, parent):
        """Initialize server connection frame."""
        server_frame = tk.LabelFrame(parent, text="Server Connection", 
                                   bg='#f0f0f0', font=("Arial", 12, "bold"))
        server_frame.pack(fill="x", pady=(0, 10))
        
        # Server URL
        url_frame = tk.Frame(server_frame, bg='#f0f0f0')
        url_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(url_frame, text="Server URL:", bg='#f0f0f0').pack(side="left")
        
        self.server_url_entry = tk.Entry(url_frame, width=40)
        self.server_url_entry.insert(0, self.server_url)
        self.server_url_entry.pack(side="left", padx=(10, 0))
        
        # Connect/Disconnect buttons
        btn_frame = tk.Frame(server_frame, bg='#f0f0f0')
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.connect_btn = tk.Button(btn_frame, text="Connect to Server",
                                   command=self.connect_to_server,
                                   bg='#28a745', fg="white", font=("Arial", 10))
        self.connect_btn.pack(side="left", padx=(0, 10))
        
        self.disconnect_btn = tk.Button(btn_frame, text="Disconnect",
                                      command=self.disconnect_from_server,
                                      bg='#dc3545', fg="white", font=("Arial", 10),
                                      state="disabled")
        self.disconnect_btn.pack(side="left")
        
        # Status labels
        status_frame = tk.Frame(server_frame, bg='#f0f0f0')
        status_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(status_frame, text="Server Status:", bg='#f0f0f0').pack(side="left")
        
        self.server_status_label = tk.Label(status_frame, textvariable=self.server_status_var,
                                          bg='#f0f0f0', fg='red')
        self.server_status_label.pack(side="left", padx=(10, 0))
        
        tk.Label(status_frame, text="Session:", bg='#f0f0f0').pack(side="left", padx=(20, 0))
        
        self.session_status_label = tk.Label(status_frame, textvariable=self.session_status_var,
                                           bg='#f0f0f0', fg='orange')
        self.session_status_label.pack(side="left", padx=(10, 0))
        
    def init_product_frame(self, parent):
        """Initialize product selection frame."""
        product_frame = tk.LabelFrame(parent, text="Product Selection", 
                                    bg='#f0f0f0', font=("Arial", 12, "bold"))
        product_frame.pack(fill="x", pady=(0, 10))
        
        # Product selection row
        selection_frame = tk.Frame(product_frame, bg='#f0f0f0')
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(selection_frame, text="Available Products:", bg='#f0f0f0').pack(side="left")
        
        # Product dropdown
        self.product_combobox = ttk.Combobox(selection_frame, width=30, state="readonly")
        self.product_combobox.pack(side="left", padx=(10, 10))
        self.product_combobox.bind('<<ComboboxSelected>>', self.on_product_selected)
        
        # Load products button
        self.load_products_btn = tk.Button(selection_frame, text="Load Products",
                                         command=self.load_products,
                                         bg='#007ACC', fg="white", font=("Arial", 10),
                                         state="disabled")
        self.load_products_btn.pack(side="left", padx=(0, 10))
        
        # Create session button
        self.create_session_btn = tk.Button(selection_frame, text="Create Session",
                                          command=self.create_session_with_selected_product,
                                          bg='#28a745', fg="white", font=("Arial", 10),
                                          state="disabled")
        self.create_session_btn.pack(side="left")
        
        # Second row for new product creation
        new_product_frame = tk.Frame(product_frame, bg='#f0f0f0')
        new_product_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(new_product_frame, text="Create New Product:", bg='#f0f0f0').pack(side="left")
        
        # Product name entry
        self.new_product_name_entry = tk.Entry(new_product_frame, width=25)
        self.new_product_name_entry.pack(side="left", padx=(10, 10))
        self.new_product_name_entry.bind('<KeyRelease>', self.on_new_product_name_changed)
        
        # Create new product button
        self.create_product_btn = tk.Button(new_product_frame, text="Create New Product",
                                          command=self.create_new_product,
                                          bg='#17a2b8', fg="white", font=("Arial", 10),
                                          state="disabled")
        self.create_product_btn.pack(side="left")
        
        # ROI management frame
        roi_mgmt_frame = tk.Frame(product_frame, bg='#f0f0f0')
        roi_mgmt_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(roi_mgmt_frame, text="ROI Management:", bg='#f0f0f0').pack(side="left")
        
        # Define ROI button
        self.define_roi_btn = tk.Button(roi_mgmt_frame, text="Define ROIs",
                                      command=self.open_roi_definition,
                                      bg='#fd7e14', fg="white", font=("Arial", 10),
                                      state="disabled")
        self.define_roi_btn.pack(side="left", padx=(10, 5))
        
        # Manage Golden Samples button
        self.manage_golden_btn = tk.Button(roi_mgmt_frame, text="Manage Golden Samples",
                                         command=self.open_golden_management,
                                         bg='#20c997', fg="white", font=("Arial", 10),
                                         state="disabled")
        self.manage_golden_btn.pack(side="left", padx=(5, 0))
        
        # Product status
        status_frame = tk.Frame(product_frame, bg='#f0f0f0')
        status_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(status_frame, text="Selected Product:", bg='#f0f0f0').pack(side="left")
        
        self.selected_product_label = tk.Label(status_frame, textvariable=self.selected_product_var,
                                             bg='#f0f0f0', fg='blue', font=("Arial", 10, "bold"))
        self.selected_product_label.pack(side="left", padx=(10, 0))
        
    def init_camera_frame(self, parent):
        """Initialize camera control frame."""
        camera_frame = tk.LabelFrame(parent, text="Camera Control",
                                   bg='#f0f0f0', font=("Arial", 12, "bold"))
        camera_frame.pack(fill="x", pady=(0, 10))
        
        # Camera selection frame
        selection_frame = tk.Frame(camera_frame, bg='#f0f0f0')
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(selection_frame, text="Camera Type:", bg='#f0f0f0').pack(side="left")
        
        self.camera_type_var = tk.StringVar(value="Select Camera")
        self.camera_type_dropdown = ttk.Combobox(selection_frame, textvariable=self.camera_type_var,
                                                state="readonly", width=20)
        self.camera_type_dropdown.pack(side="left", padx=(5, 10))
        self.camera_type_dropdown.bind('<<ComboboxSelected>>', lambda e: self.on_camera_selected())
        
        self.scan_cameras_btn = tk.Button(selection_frame, text="Scan Cameras",
                                        command=self.scan_available_cameras,
                                        bg='#28a745', fg="white", font=("Arial", 10))
        self.scan_cameras_btn.pack(side="left", padx=(5, 0))
        
        # Camera status
        status_frame = tk.Frame(camera_frame, bg='#f0f0f0')
        status_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(status_frame, text="Status:", bg='#f0f0f0').pack(side="left")
        self.camera_status_var = tk.StringVar(value="No camera selected")
        self.camera_status_label = tk.Label(status_frame, textvariable=self.camera_status_var,
                                          bg='#f0f0f0', fg='orange')
        self.camera_status_label.pack(side="left", padx=(5, 0))
        
        # Camera controls
        ctrl_frame = tk.Frame(camera_frame, bg='#f0f0f0')
        ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        self.capture_btn = tk.Button(ctrl_frame, text="Capture & Inspect",
                                   command=self.capture_and_inspect,
                                   bg='#007ACC', fg="white", 
                                   font=("Arial", 12, "bold"))
        self.capture_btn.pack(fill="x", pady=5)
        
        # Device Barcode Input Section (Dynamic based on device count)
        self.barcode_frame = tk.LabelFrame(camera_frame, text="Device Main Barcodes",
                                         bg='#f0f0f0', font=("Arial", 10, "bold"))
        self.barcode_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Initialize barcode inputs (will be updated when product is selected)
        self.device_barcode_vars = {}
        self.device_barcode_entries = {}
        self.init_barcode_inputs(2)  # Start with 2 devices by default
        
        # Initialize with scan on startup
        self.root.after(1000, self.scan_available_cameras)
        
    def init_barcode_inputs(self, device_count):
        """Initialize dynamic barcode input fields based on device count."""
        # Clear existing barcode inputs
        for widget in self.barcode_frame.winfo_children():
            widget.destroy()
            
        self.device_barcode_vars = {}
        self.device_barcode_entries = {}
        
        # Create barcode inputs for each device
        for device_id in range(1, device_count + 1):
            # Device frame
            device_frame = tk.Frame(self.barcode_frame, bg='#f0f0f0')
            device_frame.pack(fill="x", padx=5, pady=2)
            
            # Device label
            device_label = tk.Label(device_frame, text=f"Device {device_id}:", 
                                  bg='#f0f0f0', width=10, anchor='w')
            device_label.pack(side="left")
            
            # Barcode input
            barcode_var = tk.StringVar()
            barcode_entry = tk.Entry(device_frame, textvariable=barcode_var, width=20)
            barcode_entry.pack(side="left", padx=(5, 10), fill="x", expand=True)
            
            # Bind keyboard navigation for easier barcode scanning
            barcode_entry.bind('<Return>', lambda e, did=device_id: self.focus_next_barcode_entry_with_return(did, e))
            barcode_entry.bind('<Tab>', lambda e, did=device_id: self.focus_next_barcode_entry(did))
            barcode_entry.bind('<Down>', lambda e, did=device_id: self.focus_next_barcode_entry(did))
            barcode_entry.bind('<Up>', lambda e, did=device_id: self.focus_prev_barcode_entry(did))
            
            # Add focus visual indicators for better UX
            barcode_entry.bind('<FocusIn>', lambda e, entry=barcode_entry: self.on_barcode_focus_in(entry))
            barcode_entry.bind('<FocusOut>', lambda e, entry=barcode_entry: self.on_barcode_focus_out(entry))
            
            # Clear button for this device
            clear_btn = tk.Button(device_frame, text="Clear", 
                                command=lambda v=barcode_var: v.set(""),
                                bg='#6c757d', fg="white", font=("Arial", 8))
            clear_btn.pack(side="right")
            
            # Store references
            self.device_barcode_vars[device_id] = barcode_var
            self.device_barcode_entries[device_id] = barcode_entry
        
        # Set focus to first barcode entry for easier scanning workflow
        if device_count > 0 and 1 in self.device_barcode_entries:
            # Use after_idle to ensure widget is fully created before focusing
            self.root.after_idle(lambda: self.device_barcode_entries[1].focus_set())
        
        # Clear All button
        clear_all_frame = tk.Frame(self.barcode_frame, bg='#f0f0f0')
        clear_all_frame.pack(fill="x", padx=5, pady=(5, 5))
        
        clear_all_btn = tk.Button(clear_all_frame, text="Clear All Barcodes",
                                command=self.clear_all_barcodes,
                                bg='#ffc107', fg="black", font=("Arial", 9, "bold"))
        clear_all_btn.pack(anchor="w")
        
        # Auto-inspect mode toggle
        toggle_frame = tk.Frame(self.barcode_frame, bg='#f0f0f0')
        toggle_frame.pack(fill="x", padx=5, pady=(5, 5))
        
        self.auto_inspect_checkbox = tk.Checkbutton(
            toggle_frame,
            text="🚀 Auto-Inspect Mode (Enter on last device triggers inspection)",
            variable=self.auto_inspect_enabled,
            command=self.on_auto_inspect_toggle,
            bg='#f0f0f0',
            font=("Arial", 9, "bold"),
            fg='#28a745',
            selectcolor='#28a745',
            activebackground='#f0f0f0',
            relief='flat'
        )
        self.auto_inspect_checkbox.pack(anchor="w")
        
        # Info label
        self.barcode_info_label = tk.Label(self.barcode_frame, 
                            text="• Auto-filled if barcode ROI exists\n• Manual input used if no barcode ROI defined\n• Press Enter/Tab to move to next device (Enter on last device starts inspection)\n• Use ↑/↓ keys to navigate between devices\n• F1 or Ctrl+B: Focus first barcode\n• F2 or Ctrl+Shift+C: Clear all barcodes\n• Textboxes auto-disable after Enter, auto-clear after inspection",
                            bg='#f0f0f0', font=("Arial", 8), fg='#666666', justify="left")
        self.barcode_info_label.pack(anchor="w", padx=5, pady=(5, 5))
        
    def focus_next_barcode_entry(self, current_device_id):
        """Move focus to the next barcode entry in sequence."""
        try:
            # Get all device IDs in order
            device_ids = sorted(self.device_barcode_entries.keys())
            current_index = device_ids.index(current_device_id)
            
            # Move to next device (wrap around to first if at end)
            if current_index < len(device_ids) - 1:
                next_device_id = device_ids[current_index + 1]
            else:
                next_device_id = device_ids[0]  # Wrap to first
                
            # Focus on next entry
            self.device_barcode_entries[next_device_id].focus_set()
            
        except (ValueError, KeyError, IndexError):
            # Fallback: just stay on current entry
            pass
    
    def focus_prev_barcode_entry(self, current_device_id):
        """Move focus to the previous barcode entry in sequence."""
        try:
            # Get all device IDs in order
            device_ids = sorted(self.device_barcode_entries.keys())
            current_index = device_ids.index(current_device_id)
            
            # Move to previous device (wrap around to last if at beginning)
            if current_index > 0:
                prev_device_id = device_ids[current_index - 1]
            else:
                prev_device_id = device_ids[-1]  # Wrap to last
                
            # Focus on previous entry
            self.device_barcode_entries[prev_device_id].focus_set()
            
        except (ValueError, KeyError, IndexError):
            # Fallback: just stay on current entry
            pass
    
    def focus_next_barcode_entry_with_return(self, current_device_id, event):
        """Move focus to the next barcode entry when Enter is pressed, or trigger inspection if on last device."""
        try:
            # Get all device IDs in order
            device_ids = sorted(self.device_barcode_entries.keys())
            current_index = device_ids.index(current_device_id)
            
            # Disable the current textbox to prevent further input
            current_entry = self.device_barcode_entries[current_device_id]
            current_entry.config(state='disabled', bg='#e8e8e8')
            
            # Check if this is the last device 
            if current_index == len(device_ids) - 1:
                # Check if auto-inspect mode is enabled
                if self.auto_inspect_enabled.get():
                    logger.info(f"Last device barcode entered (Device {current_device_id}), triggering inspection automatically")
                    # Start inspection after a short delay to ensure UI updates
                    self.root.after(100, self.capture_and_inspect)
                    return "break"
                else:
                    # Manual mode - wrap around to first device
                    logger.info(f"Last device barcode entered (Device {current_device_id}), wrapping to first device (manual mode)")
                    next_device_id = device_ids[0]  # Wrap to first
                    
                    # Focus on first entry
                    def focus_first():
                        if next_device_id in self.device_barcode_entries:
                            next_entry = self.device_barcode_entries[next_device_id]
                            # Ensure first entry is enabled and ready for input
                            next_entry.config(state='normal', bg='white')
                            next_entry.focus_set()
                            logger.info(f"Manual mode: Device {current_device_id} (last, disabled) -> Device {next_device_id} (first, enabled)")
                    
                    self.root.after_idle(focus_first)
                    return "break"
            
            # Move to next device
            next_device_id = device_ids[current_index + 1]
                
            # Focus on next entry after a short delay to ensure proper event handling
            def focus_next():
                if next_device_id in self.device_barcode_entries:
                    next_entry = self.device_barcode_entries[next_device_id]
                    # Ensure next entry is enabled and ready for input
                    next_entry.config(state='normal', bg='white')
                    next_entry.focus_set()
                    logger.info(f"Auto-switched focus: Device {current_device_id} (disabled) -> Device {next_device_id} (enabled)")
            
            self.root.after_idle(focus_next)
            
            # Return "break" to prevent default Enter key behavior
            return "break"
            
        except (ValueError, KeyError, IndexError):
            # Fallback: just stay on current entry
            return "break"
    
    def clear_all_barcodes(self):
        """Clear all device barcode entries."""
        for barcode_var in self.device_barcode_vars.values():
            barcode_var.set("")
        # Focus on first barcode entry after clearing
        if self.device_barcode_entries and 1 in self.device_barcode_entries:
            self.device_barcode_entries[1].focus_set()
    
    def disable_all_barcode_entries(self):
        """Disable all barcode textboxes to prevent accidental input."""
        for entry in self.device_barcode_entries.values():
            entry.config(state='disabled', bg='#f0f0f0')
    
    def enable_all_barcode_entries(self):
        """Enable all barcode textboxes for input."""
        for entry in self.device_barcode_entries.values():
            entry.config(state='normal', bg='white')
    
    def clear_and_enable_barcodes_for_next_inspection(self):
        """Clear all barcodes and enable textboxes for next inspection cycle."""
        # Clear all barcode values
        for barcode_var in self.device_barcode_vars.values():
            barcode_var.set("")
        
        # Enable all entries
        self.enable_all_barcode_entries()
        
        # Focus on first barcode entry for next scan
        if self.device_barcode_entries and 1 in self.device_barcode_entries:
            self.root.after(100, lambda: self.device_barcode_entries[1].focus_set())
        
        logger.info("Barcodes cleared and enabled for next inspection")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for easier barcode scanning workflow."""
        # Bind F1 to focus first barcode entry
        self.root.bind('<F1>', lambda e: self.focus_first_barcode_entry())
        
        # Bind Ctrl+B to focus first barcode entry
        self.root.bind('<Control-b>', lambda e: self.focus_first_barcode_entry())
        
        # Bind Ctrl+Shift+C to clear all barcodes
        self.root.bind('<Control-Shift-C>', lambda e: self.clear_all_barcodes())
        
        # Bind F2 to clear all barcodes
        self.root.bind('<F2>', lambda e: self.clear_all_barcodes())
    
    def on_auto_inspect_toggle(self):
        """Handle auto-inspect mode toggle."""
        if self.auto_inspect_enabled.get():
            logger.info("Auto-Inspect Mode ENABLED - Enter on last device will trigger inspection")
            # Update checkbox text and color for enabled state
            self.auto_inspect_checkbox.config(
                text="🚀 Auto-Inspect Mode (Enter on last device triggers inspection)",
                fg='#28a745'
            )
        else:
            logger.info("Auto-Inspect Mode DISABLED - Manual inspection required")
            # Update checkbox text and color for disabled state  
            self.auto_inspect_checkbox.config(
                text="⏸️ Manual Mode (Click 'Capture and Inspect' button)",
                fg='#6c757d'
            )
        
        # Update the info text as well
        self.update_barcode_info_text()
    
    def update_barcode_info_text(self):
        """Update the barcode info text based on current auto-inspect mode."""
        if self.auto_inspect_enabled.get():
            enter_behavior = "Enter on last device starts inspection"
        else:
            enter_behavior = "Enter cycles through devices, manual inspection required"
        
        info_text = (f"• Auto-filled if barcode ROI exists\n"
                    f"• Manual input used if no barcode ROI defined\n"
                    f"• Press Enter/Tab to move to next device ({enter_behavior})\n"
                    f"• Use ↑/↓ keys to navigate between devices\n"
                    f"• F1 or Ctrl+B: Focus first barcode\n"
                    f"• F2 or Ctrl+Shift+C: Clear all barcodes\n"
                    f"• Textboxes auto-disable after Enter, auto-clear after inspection")
        
        self.barcode_info_label.config(text=info_text)
    
    def focus_first_barcode_entry(self):
        """Focus the first barcode entry for quick scanning."""
        if self.device_barcode_entries and 1 in self.device_barcode_entries:
            self.device_barcode_entries[1].focus_set()
            return True  # Return True to indicate success
        return False
    
    def on_barcode_focus_in(self, entry):
        """Handle barcode entry focus in - highlight for better visibility."""
        entry.config(bg='#e8f4fd', relief='solid', borderwidth=2)
    
    def on_barcode_focus_out(self, entry):
        """Handle barcode entry focus out - restore normal appearance."""
        entry.config(bg='white', relief='sunken', borderwidth=1)
        
    def init_results_frame(self, parent):
        """Initialize results display frame."""
        results_frame = tk.LabelFrame(parent, text="Inspection Results",
                                    bg='#f0f0f0', font=("Arial", 12, "bold"))
        results_frame.pack(fill="both", expand=True)
        
        # Overall result
        result_label_frame = tk.Frame(results_frame, bg='#f0f0f0')
        result_label_frame.pack(fill="x", padx=10, pady=10)
        
        self.overall_result_label = tk.Label(result_label_frame, 
                                           textvariable=self.overall_result_var,
                                           bg='#f0f0f0', font=("Arial", 14, "bold"),
                                           fg='blue')
        self.overall_result_label.pack()
        
        # Results tree
        tree_frame = tk.Frame(results_frame, bg='#f0f0f0')
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.results_tree = ttk.Treeview(tree_frame, height=15)
        self.results_tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar for tree
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.results_tree['columns'] = ('Type', 'Status', 'Details')
        self.results_tree.column('#0', width=80, minwidth=50)
        self.results_tree.column('Type', width=80, minwidth=60)
        self.results_tree.column('Status', width=60, minwidth=50)
        self.results_tree.column('Details', width=180, minwidth=120)
        
        # Configure headings
        self.results_tree.heading('#0', text='ROI')
        self.results_tree.heading('Type', text='Type')
        self.results_tree.heading('Status', text='Status')
        self.results_tree.heading('Details', text='Details')
        
        # Control buttons
        btn_frame = tk.Frame(results_frame, bg='#f0f0f0')
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.view_details_btn = tk.Button(btn_frame, text="View Details",
                                        command=self.show_detailed_results,
                                        bg='#007ACC', fg="white", state="disabled")
        self.view_details_btn.pack(side="left", padx=(0, 5))
        
        self.export_results_btn = tk.Button(btn_frame, text="Export Results",
                                          command=self.export_results,
                                          bg='#6c757d', fg="white", state="disabled")
        self.export_results_btn.pack(side="left")
        
    def init_device_results_frame(self, parent):
        """Initialize device results display frame."""
        # Title
        title_frame = tk.Frame(parent, bg='white')
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = tk.Label(title_frame, text="Device Results", 
                              bg='white', font=("Arial", 16, "bold"), fg='#333')
        title_label.pack()
        
        # Device list frame
        self.device_frame = tk.Frame(parent, bg='white')
        self.device_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Initial message
        self.device_message_label = tk.Label(self.device_frame, 
                                           text="Run inspection to see device results",
                                           bg='white', fg='gray', font=("Arial", 12))
        self.device_message_label.pack(expand=True)
        
        # Store device data for click handling
        self.device_data = {}
        
    def update_device_results(self, device_summaries):
        """Update the device results display."""
        logger.info(f"DEBUG: update_device_results called with: {device_summaries}")
        
        # Clear existing widgets
        for widget in self.device_frame.winfo_children():
            widget.destroy()
        
        if not device_summaries:
            logger.info("DEBUG: No device summaries - showing default message")
            self.device_message_label = tk.Label(self.device_frame, 
                                               text="No device data available",
                                               bg='white', fg='gray', font=("Arial", 12))
            self.device_message_label.pack(expand=True)
            return
        
        logger.info(f"DEBUG: Creating device cards for {len(device_summaries)} devices")
        # Store device data
        self.device_data = device_summaries
        
        # Create device cards
        for device_id, summary in device_summaries.items():
            logger.info(f"DEBUG: Creating card for device {device_id}: {summary}")
            self.create_device_card(self.device_frame, device_id, summary)
    
    def create_device_card(self, parent, device_id, summary):
        """Create a clickable device card."""
        # Device card frame
        card_frame = tk.Frame(parent, bg='#f8f9fa', relief='raised', bd=2)
        card_frame.pack(fill="x", padx=5, pady=5)
        
        # Make card clickable
        card_frame.bind("<Button-1>", lambda e: self.on_device_click(device_id))
        
        # Device header
        header_frame = tk.Frame(card_frame, bg='#f8f9fa')
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.bind("<Button-1>", lambda e: self.on_device_click(device_id))
        
        device_label = tk.Label(header_frame, text=f"Device {device_id}", 
                               bg='#f8f9fa', font=("Arial", 14, "bold"), fg='#333')
        device_label.pack(side="left")
        device_label.bind("<Button-1>", lambda e: self.on_device_click(device_id))
        
        # Device status
        device_passed = summary.get('device_passed', False)
        status_color = '#28a745' if device_passed else '#dc3545'
        status_text = 'PASS' if device_passed else 'FAIL'
        
        status_label = tk.Label(header_frame, text=status_text, 
                               bg=status_color, fg='white', font=("Arial", 12, "bold"),
                               padx=10, pady=2)
        status_label.pack(side="right")
        status_label.bind("<Button-1>", lambda e: self.on_device_click(device_id))
        
        # Device stats
        stats_frame = tk.Frame(card_frame, bg='#f8f9fa')
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        stats_frame.bind("<Button-1>", lambda e: self.on_device_click(device_id))
        
        total_rois = summary.get('total_rois', 0)
        passed_rois = summary.get('passed_rois', 0)
        failed_rois = summary.get('failed_rois', 0)
        
        stats_text = f"ROIs: {passed_rois}/{total_rois} passed"
        if failed_rois > 0:
            stats_text += f", {failed_rois} failed"
            
        stats_label = tk.Label(stats_frame, text=stats_text, 
                              bg='#f8f9fa', font=("Arial", 10), fg='#666')
        stats_label.pack(side="left")
        stats_label.bind("<Button-1>", lambda e: self.on_device_click(device_id))
        
        # Barcode info if available
        if summary.get('barcode'):
            barcode_label = tk.Label(stats_frame, text=f"Barcode: {summary['barcode']}", 
                                   bg='#f8f9fa', font=("Arial", 10), fg='#666')
            barcode_label.pack(side="right")
            barcode_label.bind("<Button-1>", lambda e: self.on_device_click(device_id))
    
    def on_device_click(self, device_id):
        """Handle device card click - show ROIs for this device."""
        logger.info(f"Device {device_id} clicked")
        
        if device_id not in self.device_data:
            logger.warning(f"Device {device_id} not found in device_data. Available: {list(self.device_data.keys())}")
            return
            
        device_summary = self.device_data[device_id]
        # Server sends 'roi_results', not 'results'
        device_rois = device_summary.get('roi_results', [])
        logger.info(f"Device {device_id} has {len(device_rois)} ROIs")
        
        # Clear and populate results tree with device ROIs
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Show device header
        device_text = f"Device {device_id}"
        device_passed = device_summary.get('device_passed', False)
        status_text = "PASS" if device_passed else "FAIL"
        
        # Handle barcode info
        barcode = device_summary.get('barcode', 'N/A')
        passed_rois = device_summary.get('passed_rois', 0)
        total_rois = device_summary.get('total_rois', 0)
        
        details_text = f"Barcode: {barcode}, ROIs: {passed_rois}/{total_rois}"
        
        # Insert device header
        device_item = self.results_tree.insert('', 'end',
                                       text=device_text,
                                       values=('Device', status_text, details_text))
        
        # Add ROI results under the device
        for roi_result in device_rois:
            roi_id = roi_result.get('roi_id', 'Unknown')
            roi_type_name = roi_result.get('roi_type_name', 'unknown')
            status = "PASS" if roi_result.get('passed', False) else "FAIL"
            
            # Normalize ROI type display
            if roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
                # Always show COMPARE for comparison operations regardless of match_result
                roi_type = "COMPARE"
            else:
                roi_type = roi_type_name.upper()
            
            # Create details text based on type
            if roi_type_name == 'barcode':
                barcode_values = roi_result.get('barcode_values', ['None'])
                barcode_text = barcode_values[0] if barcode_values else 'None'
                details = f"Barcode: {barcode_text}"
            elif roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
                # For comparison operations, show similarity score
                similarity = roi_result.get('ai_similarity', 0)
                details = f"Similarity: {similarity:.3f}"
            elif roi_type_name == 'ocr':
                ocr_text = roi_result.get('ocr_text', 'None')
                details = f"Text: {ocr_text}"
            else:
                details = f"Result: {roi_result.get('result', 'N/A')}"
            
            self.results_tree.insert(device_item, 'end',
                                   text=f"ROI {roi_id}",
                                   values=(roi_type, status, details))
        
        # Expand device item
        self.results_tree.item(device_item, open=True)
        
    def connect_to_server(self):
        """Connect to the API server."""
        try:
            self.server_url = self.server_url_entry.get().strip()
            if not self.server_url:
                self.show_error_dialog("Error", "Please enter server URL")
                return
            
            # Test connection
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            response.raise_for_status()
            
            health_data = response.json()
            logger.info(f"Connected to server: {health_data}")
            
            # Update UI
            self.server_status_var.set("Connected")
            self.server_status_label.config(fg='green')
            
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.load_products_btn.config(state="normal")
            
            # Try to initialize server
            self.initialize_server()
            
            # Load available products
            self.load_products()
            
            # Enable create product button if name is entered
            if self.new_product_name_entry.get().strip():
                self.create_product_btn.config(state="normal")
            
            # Update overall result
            self.overall_result_var.set("Server Connected\\nSelect Product")
            self.overall_result_label.config(fg='green')
            
            self.show_info_dialog("Success", "Connected to Visual AOI Server")
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            self.show_error_dialog("Connection Error", f"Failed to connect to server:\\n{e}")
            
    def disconnect_from_server(self):
        """Disconnect from the API server."""
        try:
            # Close session if active
            if self.session_active and self.session_id:
                self.close_session()
            
            # Update UI
            self.server_status_var.set("Disconnected")
            self.server_status_label.config(fg='red')
            
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.load_products_btn.config(state="disabled")
            self.create_session_btn.config(state="disabled")
            self.create_product_btn.config(state="disabled")
            
            # Clear product selection
            self.available_products = []
            self.selected_product = None
            self.selected_product_var.set("No Product Selected")
            self.product_combobox['values'] = ()
            self.product_combobox.set("")
            
            self.overall_result_var.set("Connect to Server")
            self.overall_result_label.config(fg='blue')
            
            self.show_info_dialog("Info", "Disconnected from server")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            
    def initialize_server(self):
        """Initialize the server with AI models."""
        try:
            response = requests.post(f"{self.server_url}/api/initialize", timeout=30)
            response.raise_for_status()
            
            init_data = response.json()
            logger.info(f"Server initialization: {init_data}")
            
        except Exception as e:
            logger.error(f"Server initialization failed: {e}")
            self.show_warning_dialog("Warning", f"Server initialization failed:\\n{e}")
            
    def load_products(self):
        """Load available products from server."""
        try:
            response = requests.get(f"{self.server_url}/api/products", timeout=10)
            response.raise_for_status()
            
            products_data = response.json()
            self.available_products = products_data['products']
            
            if self.available_products:
                # Update combobox with product names
                product_names = [product['product_name'] for product in self.available_products]
                self.product_combobox['values'] = product_names
                
                # Select first product by default
                self.product_combobox.current(0)
                self.on_product_selected(None)
                
                logger.info(f"Loaded {len(self.available_products)} products")
            else:
                self.selected_product_var.set("No Products Available")
                self.show_warning_dialog("Warning", "No products found on server")
                
        except Exception as e:
            logger.error(f"Load products failed: {e}")
            self.show_error_dialog("Error", f"Failed to load products:\\n{e}")
            
    def on_product_selected(self, event):
        """Handle product selection from combobox."""
        try:
            selected_name = self.product_combobox.get()
            if selected_name:
                # Find the selected product data
                self.selected_product = next(
                    (p for p in self.available_products if p['product_name'] == selected_name), 
                    None
                )
                
                if self.selected_product:
                    self.selected_product_var.set(f"{selected_name}")
                    self.create_session_btn.config(state="normal")
                    # Enable ROI management buttons when product is selected
                    self.define_roi_btn.config(state="normal")
                    self.manage_golden_btn.config(state="normal")
                    
                    # Update barcode inputs based on device count for this product
                    device_count = self.get_device_count_from_rois()
                    self.init_barcode_inputs(device_count)
                    
                    logger.info(f"Selected product: {selected_name}, devices: {device_count}")
                
        except Exception as e:
            logger.error(f"Product selection failed: {e}")
            
    def create_session_with_selected_product(self):
        """Create session with the selected product."""
        if not self.selected_product:
            self.show_error_dialog("Error", "No product selected")
            return
            
        try:
            # Close existing session if active
            if self.session_active:
                self.close_session()
            
            # Create session with selected product
            session_data = {
                'product_name': self.selected_product['product_name'],
                'client_info': {
                    'client_id': 'visual_aoi_client',
                    'version': '1.0.0',
                    'location': 'local'
                }
            }
            
            response = requests.post(f"{self.server_url}/api/session/create",
                                   json=session_data, timeout=10)
            response.raise_for_status()
            
            session_response = response.json()
            self.session_id = session_response['session_id']
            self.session_active = True
            
            product_name = self.selected_product['product_name']
            self.session_status_var.set(f"Active ({product_name})")
            self.session_status_label.config(fg='green')
            
            # Initialize camera with optimal settings for this product
            self.initialize_camera_for_product(product_name)
            
            self.overall_result_var.set("Session Active\nReady to Inspect")
            self.overall_result_label.config(fg='green')
            
            self.show_info_dialog("Success", f"Session created for product: {product_name}")
            logger.info(f"Created session {self.session_id} for product {product_name}")
            
        except Exception as e:
            logger.error(f"Create session failed: {e}")
            self.show_error_dialog("Error", f"Failed to create session:\\n{e}")
            
    def initialize_camera_for_product(self, product_name):
        """Initialize camera with optimal settings based on first ROI group - Complete TIS Workflow."""
        try:
            logger.info(f"Initializing TIS camera for product: {product_name} with complete workflow")
            
            # Step 1: Check camera prerequisites
            if not self.selected_camera_type:
                logger.info("No camera type selected - skipping camera initialization")
                return False
                
            if self.selected_camera_type != 'tis':
                logger.info(f"Non-TIS camera selected ({self.selected_camera_type}) - using basic initialization")
                return self.init_tis_camera_with_defaults()
                
            if not self.pending_camera_info:
                logger.error("No TIS camera info available for initialization")
                return False
                
            # Step 2: Get ROI groups to determine first ROI group settings
            self.camera_status_var.set("Loading ROI configuration...")
            self.camera_status_label.config(fg='blue')
            
            response = requests.get(f"{self.server_url}/get_roi_groups/{product_name}")
            if response.status_code != 200:
                logger.error(f"Failed to get ROI groups: {response.text}")
                return self.init_tis_camera_with_defaults()
                
            roi_groups = response.json().get('roi_groups', {})
            if not roi_groups:
                logger.warning("No ROI groups found, using default camera settings")
                return self.init_tis_camera_with_defaults()
            
            # Step 3: Get first ROI group settings for optimal initialization
            first_group_key = next(iter(roi_groups.keys()))
            first_group = roi_groups[first_group_key]
            focus, exposure = first_group_key.split(',')
            focus, exposure = int(focus), int(exposure)
            
            logger.info(f"Applying first ROI group settings for optimal initialization: focus={focus}, exposure={exposure}")
            
            # Step 4: Initialize TIS camera with first ROI group settings
            self.camera_status_var.set(f"Initializing camera with first ROI group (F:{focus}, E:{exposure})...")
            
            # Import TIS module directly
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from TIS import TIS, SinkFormats
            
            success = self.initialize_tis_camera_direct(
                serial=self.pending_camera_info if isinstance(self.pending_camera_info, str) else self.pending_camera_info.get('serial', ''),
                width=7716,     # Use proven working resolution from camera.json
                height=5360,    # Use proven working resolution from camera.json
                fps=7,          # Use proven working framerate
                format_type="BGRA",
                initial_focus=focus,
                initial_exposure=exposure
            )
            
            if not success:
                logger.error("Failed to initialize TIS camera with first ROI group settings")
                self.camera_status_var.set("TIS camera initialization failed")
                self.camera_status_label.config(fg='red')
                return False
            
            # Step 5: Apply settle delay for first ROI group settings
            settle_delay = self.get_camera_settle_delay()
            logger.info(f"Applying settle delay for first ROI group initialization: {settle_delay:.2f} seconds")
            self.apply_settle_delay_with_ui(settle_delay, f"Settling camera for first ROI (F:{focus}, E:{exposure})")
            
            # Step 6: Store first ROI group settings for later revert
            self.first_roi_group_settings = {
                'focus': focus,
                'exposure': exposure,
                'group_key': first_group_key
            }
            
            # Step 7: Mark camera as initialized and ready
            self.camera = True
            self.camera_initialized = True
            self.camera_status_var.set(f"Camera ready with optimal settings (F:{focus}, E:{exposure})")
            self.camera_status_label.config(fg='green')
            
            # Clear pending camera info
            self.pending_camera_info = None
            
            logger.info(f"TIS camera initialized successfully with complete workflow - ready for fast capture")
            return True
                
        except Exception as e:
            logger.error(f"Complete TIS camera initialization failed: {e}")
            self.camera_status_var.set("Camera initialization failed")
            self.camera_status_label.config(fg='red')
            return False
    
    def get_camera_settle_delay(self):
        """Get settle delay time from camera.json configuration."""
        try:
            # Load camera configuration from camera.json
            config_path = "/home/jason_nguyen/visual-aoi/config/system/camera.json"
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    camera_config = json.load(f)
                
                settle_delay = camera_config.get('camera_performance', {}).get('focus_settle_delay', 3.0)
                logger.info(f"Using camera config settle delay: {settle_delay} seconds")
                return settle_delay
            else:
                logger.warning(f"Camera config file not found at {config_path}")
                return 3.0  # Default 3 seconds
                
        except Exception as e:
            logger.warning(f"Failed to load camera settle delay config: {e}")
            return 3.0  # Default 3 seconds as per camera.json
    
    def apply_settle_delay_with_ui(self, settle_delay, status_message):
        """Apply settle delay with UI countdown feedback."""
        import threading
        import time
        
        # Create an event to track when settling is complete
        settle_complete = threading.Event()
        
        def settle_timer():
            time.sleep(settle_delay)
            settle_complete.set()
        
        # Start settle timer in background
        settle_thread = threading.Thread(target=settle_timer, daemon=True)
        settle_thread.start()
        
        # Update UI during settle delay with countdown
        start_time = time.time()
        while not settle_complete.is_set():
            elapsed = time.time() - start_time
            remaining = max(0, settle_delay - elapsed)
            self.camera_status_var.set(f"{status_message}... {remaining:.1f}s")
            self.root.update()
            time.sleep(0.1)  # Update UI every 100ms
        
        logger.info(f"Settle delay completed: {settle_delay:.2f} seconds")
    
    def apply_camera_settings(self, focus, exposure):
        """Apply focus and exposure settings to TIS camera with improved error handling."""
        try:
            if not hasattr(self, 'tis_camera') or not self.tis_camera:
                logger.error("TIS camera not initialized")
                return False
            
            settings_changed = False
            
            # Apply focus setting
            if focus is not None:
                try:
                    current_focus = self.tis_camera.get_property("Focus")
                    if current_focus != focus:
                        if self.tis_camera.set_property("Focus", focus):
                            settings_changed = True
                            logger.info(f"Applied focus: {current_focus} -> {focus}")
                        else:
                            logger.error(f"Failed to set focus to {focus}")
                            return False
                    else:
                        logger.info(f"Focus already set to: {focus}")
                except Exception as e:
                    logger.error(f"Failed to set focus: {e}")
                    return False
                    
            # Apply exposure setting with improved error handling
            if exposure is not None:
                try:
                    # TIS cameras typically use microseconds for exposure
                    # Based on camera.json default of 15000, values should be in microseconds
                    original_exposure = exposure
                    
                    # Convert and validate exposure value
                    if exposure < 1000:
                        logger.warning(f"Exposure value {exposure} seems low for TIS camera (expects microseconds)")
                        # If value is very small, assume it's in milliseconds and convert
                        if exposure < 100:
                            exposure = exposure * 1000  # Convert ms to µs
                            logger.info(f"Converted exposure from {original_exposure}ms to {exposure}µs")
                    
                    # Ensure exposure is within reasonable bounds for TIS camera
                    min_exposure = 100    # 100µs minimum
                    max_exposure = 100000 # 100ms maximum  
                    
                    if exposure < min_exposure:
                        logger.warning(f"Exposure {exposure}µs below minimum {min_exposure}µs, adjusting")
                        exposure = min_exposure
                    elif exposure > max_exposure:
                        logger.warning(f"Exposure {exposure}µs above maximum {max_exposure}µs, adjusting")
                        exposure = max_exposure
                    
                    # Step 1: Try to disable auto exposure with multiple methods
                    logger.info("Attempting to disable auto exposure...")
                    auto_exposure_disabled = False
                    
                    try:
                        # Method 1: Set ExposureAuto to "Off"
                        current_auto = self.tis_camera.get_property("ExposureAuto")
                        logger.info(f"Current ExposureAuto value: {current_auto}")
                        
                        if current_auto != "Off":
                            if self.tis_camera.set_property("ExposureAuto", "Off"):
                                logger.info("Successfully set ExposureAuto to Off")
                                auto_exposure_disabled = True
                            else:
                                logger.warning("Failed to set ExposureAuto to Off")
                    except Exception as e:
                        logger.warning(f"Method 1 failed: {e}")
                    
                    # Method 2: Try setting to False if "Off" didn't work
                    if not auto_exposure_disabled:
                        try:
                            if self.tis_camera.set_property("ExposureAuto", False):
                                logger.info("Successfully set ExposureAuto to False")
                                auto_exposure_disabled = True
                        except Exception as e:
                            logger.warning(f"Method 2 failed: {e}")
                    
                    # Method 3: Try setting to 0
                    if not auto_exposure_disabled:
                        try:
                            if self.tis_camera.set_property("ExposureAuto", 0):
                                logger.info("Successfully set ExposureAuto to 0")
                                auto_exposure_disabled = True
                        except Exception as e:
                            logger.warning(f"Method 3 failed: {e}")
                    
                    if not auto_exposure_disabled:
                        logger.warning("Could not disable auto exposure, attempting manual exposure anyway")
                    
                    # Step 2: Get current exposure value
                    try:
                        current_exposure = self.tis_camera.get_property("ExposureTime")
                        logger.info(f"Current exposure: {current_exposure}µs")
                        
                        if current_exposure != exposure:
                            logger.info(f"Setting exposure from {current_exposure}µs to {exposure}µs")
                            
                            # Step 3: Try to set the exposure value
                            if self.tis_camera.set_property("ExposureTime", exposure):
                                # Verify the setting was applied
                                try:
                                    new_exposure = self.tis_camera.get_property("ExposureTime")
                                    if new_exposure == exposure:
                                        logger.info(f"Successfully applied exposure: {current_exposure}µs -> {new_exposure}µs")
                                        settings_changed = True
                                    else:
                                        logger.warning(f"Exposure set but value differs: requested {exposure}µs, got {new_exposure}µs")
                                        settings_changed = True  # Still consider it a change
                                except Exception as e:
                                    logger.warning(f"Could not verify exposure setting: {e}")
                                    settings_changed = True  # Assume it worked
                            else:
                                # If exact value failed, try alternative approaches
                                logger.warning(f"Failed to set exact exposure {exposure}µs, trying alternatives...")
                                
                                # Try values around the target, camera defaults, and safe ranges
                                alternative_exposures = [
                                    exposure + 100,   # Slightly higher
                                    exposure - 100 if exposure > 200 else exposure,  # Slightly lower
                                    max(1000, exposure),  # Ensure at least 1ms
                                    15000,           # Camera default from config
                                    10000,           # 10ms - common safe value
                                    5000,            # 5ms
                                    2000,            # 2ms
                                    1000             # 1ms - minimum reasonable
                                ]
                                
                                success = False
                                for alt_exposure in alternative_exposures:
                                    if alt_exposure == current_exposure:
                                        continue  # Skip if it's already the current value
                                        
                                    logger.info(f"Trying alternative exposure: {alt_exposure}µs")
                                    if self.tis_camera.set_property("ExposureTime", alt_exposure):
                                        try:
                                            verify_exposure = self.tis_camera.get_property("ExposureTime")
                                            logger.info(f"Successfully set alternative exposure: {alt_exposure}µs (verified: {verify_exposure}µs)")
                                            settings_changed = True
                                            success = True
                                            break
                                        except Exception:
                                            logger.info(f"Alternative exposure {alt_exposure}µs set but could not verify")
                                            settings_changed = True
                                            success = True
                                            break
                                
                                if not success:
                                    logger.error(f"Failed to set any exposure value for target {original_exposure} (tried {exposure}µs)")
                                    return False
                        else:
                            logger.info(f"Exposure already set to: {exposure}µs")
                    except Exception as e:
                        logger.error(f"Failed to get/set exposure time: {e}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Failed to set exposure: {e}")
                    return False
            
            logger.info(f"Camera settings applied successfully (settings_changed: {settings_changed})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply camera settings: {e}")
            return False

    def initialize_tis_camera_direct(self, serial, width, height, fps, format_type, initial_focus=None, initial_exposure=None):
        """Initialize TIS camera directly without server-side camera module."""
        try:
            # Import TIS directly
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from TIS import TIS, SinkFormats
            
            # Convert format string to SinkFormats enum
            format_map = {
                "BGRA": SinkFormats.BGRA,
                "BGRX": SinkFormats.BGRX,
                "BGR": SinkFormats.BGRA,  # Map BGR to BGRA for compatibility
                "GRAY8": SinkFormats.GRAY8,
                "GRAY16_LE": SinkFormats.GRAY16_LE
            }
            
            sink_format = format_map.get(format_type, SinkFormats.BGRA)
            print(f"Using sink format: {sink_format} (from format_type: {format_type})")
            
            # Create TIS camera instance
            self.tis_camera = TIS()
            self.tis = self.tis_camera  # Also store as self.tis for consistency
            
            # Open device
            success = self.tis_camera.open_device(serial, width, height, f"{fps}/1", sink_format, False)  # showvideo=False to disable preview
            if not success:
                print("Failed to open TIS device")
                return False
            
            # Start pipeline
            if not self.tis_camera.start_pipeline():
                print("Failed to start TIS pipeline")
                return False
            
            # Wait for device to be ready
            if not self.tis_camera.wait_for_device_ready(5):
                print("Warning: Device not ready after timeout")
            
            # Set initial camera properties if provided
            if initial_focus is not None:
                try:
                    self.tis_camera.set_property("Focus", initial_focus)
                    print(f"Set initial focus: {initial_focus}")
                except Exception as e:
                    print(f"Warning: Failed to set initial focus: {e}")
            
            if initial_exposure is not None:
                try:
                    # First disable auto exposure if it's enabled
                    if self.tis_camera.get_property("ExposureAuto"):
                        self.tis_camera.set_property("ExposureAuto", "Off")
                        print("Disabled auto exposure")
                    
                    # Set exposure time
                    self.tis_camera.set_property("ExposureTime", initial_exposure)
                    print(f"Set initial exposure: {initial_exposure}")
                except Exception as e:
                    print(f"Warning: Failed to set initial exposure: {e}")
            
            print("TIS camera initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing TIS camera: {e}")
            import traceback
            traceback.print_exc()
            return False
            # Try fallback initialization
            try:
                self.init_tis_camera_with_defaults()
            except Exception as fallback_e:
                logger.error(f"Fallback camera initialization failed: {fallback_e}")
                
    def init_tis_camera_with_defaults(self):
        """Initialize TIS camera with default settings as fallback."""
        if not self.pending_camera_info:
            return False
            
        try:
            logger.info("Initializing TIS camera with default settings as fallback")
            
            # Use direct TIS initialization with default settings
            success = self.initialize_tis_camera_direct(
                serial=self.pending_camera_info.get('serial', '') if isinstance(self.pending_camera_info, dict) else str(self.pending_camera_info),
                width=1920,      # Default resolution
                height=1080,     # Default resolution  
                fps=30,          # Default FPS
                format_type="BGRA",
                initial_focus=305,    # Default focus from camera.json
                initial_exposure=15000  # Default exposure from camera.json
            )
            
            if success:
                self.camera = True
                self.camera_initialized = True
                self.camera_status_var.set(f"TIS camera ready (default settings)")
                self.camera_status_label.config(fg='green')
                self.pending_camera_info = None
                logger.info("TIS camera initialized successfully with default settings")
                return True
            else:
                logger.error("Failed to initialize TIS camera with default settings")
                return False
                
        except Exception as e:
            logger.error(f"Default TIS camera initialization failed: {e}")
            return False
            
    def on_new_product_name_changed(self, event):
        """Handle new product name entry changes."""
        try:
            product_name = self.new_product_name_entry.get().strip()
            # Enable create button only if name is provided and connected to server
            can_create = (product_name and 
                         self.server_status_var.get() == "Connected")
            
            self.create_product_btn.config(
                state="normal" if can_create else "disabled"
            )
        except Exception as e:
            logger.error(f"Product name validation error: {e}")
            
    def create_new_product(self):
        """Create a new product configuration."""
        try:
            if self.server_status_var.get() != "Connected":
                self.show_error_dialog("Error", "Not connected to server")
                return
            
            product_name = self.new_product_name_entry.get().strip()
            if not product_name:
                self.show_error_dialog("Error", "Please enter a product name")
                return
            
            # Ask for description
            description = simpledialog.askstring(
                "Product Description", 
                f"Enter description for product '{product_name}':",
                initialvalue=f"Inspection program for {product_name}"
            )
            
            if description is None:  # User cancelled
                return
            
            # Show confirmation dialog
            confirm = self.show_confirm_dialog(
                "Confirm Product Creation",
                f"Create new product '{product_name}'?\\n\\n"
                f"Description: {description}\\n\\n"
                f"This will create a default configuration with 3 ROIs:\\n"
                f"• ROI 1: Barcode detection\\n"
                f"• ROI 2: Image comparison\\n"
                f"• ROI 3: OCR text recognition\\n\\n"
                f"You can modify the configuration later."
            )
            
            if not confirm:
                return
            
            # Create product request
            product_data = {
                'product_name': product_name,
                'description': description
            }
            
            response = requests.post(f"{self.server_url}/api/products/create",
                                   json=product_data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                self.show_info_dialog("Success", 
                                  f"Product '{product_name}' created successfully!\\n\\n"
                                  f"The product has been added with default ROI settings.\\n"
                                  f"You can now select it for inspection.")
                
                # Clear the entry
                self.new_product_name_entry.delete(0, tk.END)
                self.create_product_btn.config(state="disabled")
                
                # Reload products to show the new one
                self.load_products()
                
                # Select the newly created product
                product_names = [p['product_name'] for p in self.available_products]
                if product_name in product_names:
                    index = product_names.index(product_name)
                    self.product_combobox.current(index)
                    self.on_product_selected(None)
                
                logger.info(f"Created new product: {product_name}")
                
            else:
                error_msg = result.get('error', 'Unknown error')
                self.show_error_dialog("Error", f"Failed to create product:\\n{error_msg}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Create product request failed: {e}")
            self.show_error_dialog("Error", f"Failed to create product:\\n{e}")
        except Exception as e:
            logger.error(f"Create product failed: {e}")
            self.show_error_dialog("Error", f"Failed to create product:\\n{e}")
            
    def capture_and_inspect(self):
        """Capture image directly from camera and send for inspection."""
        if not self.server_status_var.get() == "Connected":
            messagebox.showerror("Error", "Not connected to server")
            return
            
        if not self.session_active:
            messagebox.showerror("Error", "No active session. Please select a product and create a session first.")
            return
            
        # Check if camera is selected (initialization will happen automatically during capture)
        if not self.selected_camera_type and not self.camera_initialized:
            messagebox.showerror("Error", "No camera selected. Please select a camera first.")
            return
        
        # Disable all barcode textboxes during inspection to prevent interference
        self.disable_all_barcode_entries()
        logger.info("Disabled barcode entries during inspection")
            
        # Use grouped capture for better efficiency
        self.capture_grouped_images_and_inspect()
        
    def capture_grouped_images_and_inspect(self):
        """Optimized TIS camera capture process following the complete specified workflow."""
        try:
            # Step 0: Verify shared folder is accessible
            shared_folder_base = "/mnt/visual-aoi-shared"
            if not os.path.exists(shared_folder_base):
                error_msg = f"Shared folder not accessible: {shared_folder_base}\nPlease ensure the shared folder is mounted."
                logger.error(error_msg)
                messagebox.showerror("Shared Folder Error", error_msg)
                return
            
            logger.info(f"✓ Shared folder verified: {shared_folder_base}")
            
            # Verify we can write to shared folder
            try:
                test_dir = os.path.join(shared_folder_base, "sessions", self.session_id)
                os.makedirs(test_dir, exist_ok=True)
                logger.info(f"✓ Can create session directory: {test_dir}")
            except Exception as e:
                error_msg = f"Cannot write to shared folder: {e}\nPlease check permissions."
                logger.error(error_msg)
                messagebox.showerror("Permission Error", error_msg)
                return
            
            # Step 1: Ensure camera is initialized with first ROI group settings
            if not self.camera_initialized:
                product_name = self.selected_product_var.get()
                logger.info(f"Initializing camera with first ROI group settings for {product_name}")
                if not self.initialize_camera_for_product(product_name):
                    messagebox.showerror("Error", "Failed to initialize camera with optimal settings")
                    return
            
            # Step 2: Get ROI groups configuration
            self.session_status_var.set("Loading ROI configuration...")
            self.root.update()
            
            response = requests.get(f"{self.server_url}/get_roi_groups/{self.selected_product_var.get()}")
            if response.status_code != 200:
                messagebox.showerror("Error", f"Failed to get ROI configuration: {response.text}")
                return
                
            roi_groups = response.json().get('roi_groups', {})
            if not roi_groups:
                messagebox.showerror("Error", "No ROI groups found for this product")
                return
                
            logger.info(f"Found {len(roi_groups)} ROI groups for optimized capture")
            
            # Step 3: Optimized capture process
            captured_images = {}
            total_groups = len(roi_groups)
            group_list = list(roi_groups.items())
            
            capture_start_time = time.time()
            
            for group_index, (group_key, group_info) in enumerate(group_list):
                is_first_group = (group_index == 0)
                
                focus, exposure = group_key.split(',')
                focus, exposure = int(focus), int(exposure)
                rois = group_info['rois']
                
                logger.info(f"Processing group {group_index + 1}/{total_groups}: F:{focus}, E:{exposure} (first:{is_first_group})")
                
                # Step 4: Apply camera settings (skip for first group - already set during initialization)
                if not is_first_group:
                    self.session_status_var.set(f"Changing camera settings for group {group_index + 1}/{total_groups} (F:{focus}, E:{exposure})...")
                    self.root.update()
                    
                    # Apply new camera settings
                    if not self.apply_camera_settings(focus, exposure):
                        logger.error(f"Failed to apply settings for group (F:{focus}, E:{exposure})")
                        messagebox.showerror("Error", f"Failed to apply camera settings: F:{focus}, E:{exposure}")
                        return
                    
                    # Apply settle delay for setting change
                    settle_delay = self.get_camera_settle_delay()
                    self.apply_settle_delay_with_ui(settle_delay, f"Settling camera for group {group_index + 1} (F:{focus}, E:{exposure})")
                
                # Step 5: Fast capture for current ROI group
                self.session_status_var.set(f"Fast capturing group {group_index + 1}/{total_groups} (F:{focus}, E:{exposure})...")
                self.root.update()
                
                image = self.fast_capture_image()
                if image is None:
                    logger.error(f"Failed to capture image for group (F:{focus}, E:{exposure})")
                    messagebox.showerror("Error", f"Failed to capture image for group: F:{focus}, E:{exposure}")
                    return
                
                # Step 6: Save captured image
                logger.info(f"Attempting to save captured image for group {group_index + 1}/{total_groups}")
                image_saved = self.save_captured_image(image, group_key, focus, exposure, rois)
                if image_saved:
                    captured_images[group_key] = image_saved
                    logger.info(f"✓ Successfully captured and saved image for group (F:{focus}, E:{exposure})")
                    logger.info(f"  Metadata: {image_saved}")
                else:
                    error_msg = f"Failed to save image for group (F:{focus}, E:{exposure}). Check logs for details."
                    logger.error(error_msg)
                    messagebox.showerror("Save Error", error_msg)
                    return
                
                # Update progress
                progress_percent = ((group_index + 1) / total_groups) * 100
                self.session_status_var.set(f"Captured {group_index + 1}/{total_groups} groups ({progress_percent:.0f}%)...")
                self.root.update()
            
            total_capture_time = time.time() - capture_start_time
            logger.info(f"All {len(roi_groups)} images captured in {total_capture_time:.2f} seconds")
            
            # Step 7: Start inspection processing and parallel camera revert
            self.start_inspection_with_parallel_camera_revert(captured_images, total_capture_time)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during optimized capture: {e}")
            messagebox.showerror("Error", f"Network error: {e}")
            self.session_status_var.set("Capture failed - network error")
        except Exception as e:
            logger.error(f"Optimized capture failed: {e}")
            messagebox.showerror("Error", f"Optimized capture failed:\\n{e}")
            self.session_status_var.set("Capture failed")
    
    def fast_capture_image(self):
        """Fast capture image using TIS camera."""
        try:
            if not hasattr(self, 'tis_camera') or not self.tis_camera:
                logger.error("TIS camera not initialized")
                return None
            
            logger.info("Starting fast capture...")
            
            # Fast capture using TIS camera
            buffer_data = self.tis_camera.snap_image(timeout=5)
            if buffer_data is not None:
                logger.info(f"Buffer captured successfully, size: {len(buffer_data) if hasattr(buffer_data, '__len__') else 'unknown'}")
                
                # Get the converted numpy array
                image = self.tis_camera.get_image()
                if image is not None:
                    logger.info(f"Fast capture successful - image shape: {image.shape}, dtype: {image.dtype}, size: {image.size} pixels")
                    
                    # Validate image has data
                    if image.size == 0:
                        logger.error("Captured image has zero size")
                        return None
                    
                    return image
                else:
                    logger.error("Failed to convert captured buffer to numpy array")
                    return None
            else:
                logger.error("Failed to capture image with fast capture - buffer_data is None")
                return None
                
        except Exception as e:
            logger.error(f"Fast capture failed with exception: {e}", exc_info=True)
            return None
    
    def save_captured_image(self, image, group_key, focus, exposure, rois):
        """Save captured image to session directory."""
        try:
            # Validate session ID
            if not self.session_id:
                logger.error("No active session ID to save image")
                return None
            
            # Validate image
            if image is None:
                logger.error("Cannot save image - image is None")
                return None
            
            if not isinstance(image, np.ndarray):
                logger.error(f"Cannot save image - invalid type: {type(image)}")
                return None
            
            if image.size == 0:
                logger.error("Cannot save image - image is empty")
                return None
            
            logger.info(f"Preparing to save image: shape={image.shape}, dtype={image.dtype}, group_key={group_key}")
            
            # Create session directory structure
            session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
            input_dir = os.path.join(session_dir, "input")
            output_dir = os.path.join(session_dir, "output")
            
            logger.info(f"Creating directories: {input_dir}")
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            # Verify directories exist
            if not os.path.exists(input_dir):
                logger.error(f"Failed to create input directory: {input_dir}")
                return None
            
            logger.info(f"Directories verified: input_dir exists={os.path.exists(input_dir)}")
            
            # Save image with descriptive filename
            image_filename = f"capture_F{focus}_E{exposure}.jpg"
            image_filepath = os.path.join(input_dir, image_filename)
            
            logger.info(f"Saving image to: {image_filepath}")
            
            # Save as high-quality JPEG
            success = cv2.imwrite(image_filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if not success:
                logger.error(f"cv2.imwrite failed to write image to {image_filepath}")
                return None
            
            # Verify file was actually written
            if not os.path.exists(image_filepath):
                logger.error(f"Image file not found after write: {image_filepath}")
                return None
            
            file_size = os.path.getsize(image_filepath)
            logger.info(f"✓ Image saved successfully: {image_filepath} (size: {file_size} bytes)")
            
            # Return image metadata for server processing
            return {
                'image_filename': image_filename,
                'focus': focus,
                'exposure': exposure,
                'rois': rois
            }
            
        except Exception as e:
            logger.error(f"Failed to save captured image: {e}", exc_info=True)
            return None
    
    def start_inspection_with_parallel_camera_revert(self, captured_images, capture_time):
        """Start inspection processing in parallel with camera revert to first ROI group."""
        import threading
        import time
        
        # Step 1: Start inspection processing in background thread
        inspection_complete = threading.Event()
        inspection_result = {'result': None, 'error': None}
        
        def inspection_thread():
            try:
                logger.info("Starting inspection processing in background")
                inspection_start_time = time.time()
                
                # Get device barcodes for inspection
                device_barcodes = self.get_device_barcode_for_inspection()
                
                payload = {
                    'session_id': self.session_id,
                    'captured_images': captured_images
                }
                
                if device_barcodes:
                    payload['device_barcodes'] = device_barcodes
                
                # Send to server for processing
                response = requests.post(f"{self.server_url}/process_grouped_inspection", json=payload, timeout=60)
                
                inspection_end_time = time.time()
                processing_time = inspection_end_time - inspection_start_time
                
                if response.status_code == 200:
                    result = response.json()
                    result['processing_time'] = processing_time
                    result['capture_time'] = capture_time
                    result['total_time'] = capture_time + processing_time
                    inspection_result['result'] = result
                    logger.info(f"Inspection completed in {processing_time:.2f} seconds")
                else:
                    inspection_result['error'] = f"Inspection failed: {response.text}"
                    
            except Exception as e:
                inspection_result['error'] = f"Inspection processing failed: {e}"
            finally:
                inspection_complete.set()
        
        # Start inspection thread
        inspect_thread = threading.Thread(target=inspection_thread, daemon=True)
        inspect_thread.start()
        
        # Step 2: Parallel camera revert to first ROI group
        if hasattr(self, 'first_roi_group_settings') and self.first_roi_group_settings:
            self.revert_camera_to_first_roi_group_parallel()
        
        # Step 3: Wait for inspection to complete and show results
        self.session_status_var.set("Processing inspection results...")
        self.root.update()
        
        # Wait for inspection completion with UI updates
        while not inspection_complete.is_set():
            self.session_status_var.set("Processing inspection results...")
            self.root.update()
            time.sleep(0.5)
        
        # Step 4: Handle inspection results
        if inspection_result['error']:
            logger.error(inspection_result['error'])
            messagebox.showerror("Error", inspection_result['error'])
            self.session_status_var.set("Inspection failed")
        else:
            result = inspection_result['result']
            self.session_status_var.set("Inspection completed successfully")
            self.process_inspection_results(result)
            logger.info("Optimized inspection cycle completed successfully")
    
    def revert_camera_to_first_roi_group_parallel(self):
        """Revert camera settings to first ROI group in parallel with inspection."""
        try:
            if not hasattr(self, 'first_roi_group_settings') or not self.first_roi_group_settings:
                logger.info("No first ROI group settings stored, skipping revert")
                return
            
            focus = self.first_roi_group_settings['focus']
            exposure = self.first_roi_group_settings['exposure']
            
            logger.info(f"Reverting camera to first ROI group settings in parallel: F:{focus}, E:{exposure}")
            
            # Apply first ROI group settings
            if self.apply_camera_settings(focus, exposure):
                # Apply settle delay in parallel (non-blocking for inspection)
                settle_delay = self.get_camera_settle_delay()
                logger.info(f"Applying parallel settle delay for camera revert: {settle_delay:.2f} seconds")
                
                import threading
                import time
                
                def parallel_settle():
                    time.sleep(settle_delay)
                    logger.info("Parallel camera revert settle delay completed - camera ready for next session")
                
                # Start settle in background - non-blocking
                settle_thread = threading.Thread(target=parallel_settle, daemon=True)
                settle_thread.start()
                
                logger.info("Camera revert initiated in parallel with inspection processing")
            else:
                logger.error("Failed to revert camera to first ROI group settings")
                
        except Exception as e:
            logger.error(f"Parallel camera revert failed: {e}")
    
    def get_device_barcode_for_inspection(self):
        """Get device barcodes for inspection if needed."""
        try:
            # Check if there are any barcode input fields with values
            device_barcodes = []
            
            # Check device barcode entries if they exist
            for i in range(1, 5):  # Assuming up to 4 device locations
                barcode_var = getattr(self, f'device_barcode_{i}_var', None)
                if barcode_var and barcode_var.get().strip():
                    device_barcodes.append({
                        'device_id': i,
                        'barcode': barcode_var.get().strip()
                    })
            
            if device_barcodes:
                logger.info(f"Found {len(device_barcodes)} device barcodes for inspection")
                return device_barcodes
            else:
                logger.info("No device barcodes provided for inspection")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get device barcodes: {e}")
            return None
            logger.info(f"Inspection processing completed in {inspection_processing_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                # Override the server's processing_time with our client-side measurement
                result['processing_time'] = inspection_processing_time
                logger.info(f"Overriding server processing time with client measurement: {inspection_processing_time:.2f}s")
                
                self.session_status_var.set("Inspection completed successfully")
                
                # Step 5: Display results
                self.process_inspection_results(result)
                logger.info("Grouped inspection completed successfully")
                
            else:
                error_msg = f"Inspection failed: {response.text}"
                logger.error(error_msg)
                messagebox.showerror("Error", error_msg)
                self.session_status_var.set("Inspection failed")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during grouped inspection: {e}")
            messagebox.showerror("Error", f"Network error: {e}")
            self.session_status_var.set("Inspection failed - network error")
        except Exception as e:
            logger.error(f"Grouped inspection failed: {e}")
            messagebox.showerror("Error", f"Grouped inspection failed:\\n{e}")
            self.session_status_var.set("Inspection failed")
            
    def capture_with_settings(self, focus, exposure):
        """Capture image with specific focus and exposure settings."""
        try:
            logger.info(f"Capturing with focus={focus}, exposure={exposure}")
            
            if not self.tis_camera:
                logger.error("TIS camera not initialized")
                return None
                
            # Apply settings directly to TIS camera
            if focus is not None:
                try:
                    self.tis_camera.set_property("Focus", focus)
                    print(f"Applied focus: {focus}")
                except Exception as e:
                    print(f"Warning: Failed to set focus: {e}")
                    
            if exposure is not None:
                try:
                    # First disable auto exposure if it's enabled
                    if self.tis_camera.get_property("ExposureAuto"):
                        self.tis_camera.set_property("ExposureAuto", "Off")
                    
                    # Set exposure time
                    self.tis_camera.set_property("ExposureTime", exposure)
                    print(f"Applied exposure: {exposure}")
                except Exception as e:
                    print(f"Warning: Failed to set exposure: {e}")
            
            # Ensure pipeline is running
            if not self.tis_camera.start_pipeline():
                logger.error("Failed to start TIS pipeline")
                return None
            
            # Capture image
            buffer_data = self.tis_camera.snap_image(timeout=5, convert_to_mat=True)
            if buffer_data is not None:
                print(f"Buffer data type: {type(buffer_data)}, size: {len(buffer_data) if buffer_data else 0}")
                
                # Get the converted numpy array
                image = self.tis_camera.get_image()
                print(f"Converted image type: {type(image)}")
                
                if image is not None:
                    print(f"Image shape: {image.shape}, dtype: {image.dtype}")
                    logger.info(f"Image captured successfully with settings - shape: {image.shape}")
                    return image
                else:
                    logger.error("Failed to convert captured buffer to numpy array")
                    return None
            else:
                logger.error("Failed to capture image")
                return None
                
            return image
            
        except Exception as e:
            logger.error(f"Capture with settings failed: {e}")
            return None
                 
    def capture_from_camera(self):
        """Capture image from the selected camera type."""
        try:
            # Check if camera is selected (initialization can happen automatically)
            if not self.selected_camera_type and not self.camera_initialized:
                messagebox.showerror("Error", "No camera selected. Please select a camera first.")
                return
                
            # If camera is selected but not initialized, try to initialize it
            if not self.camera_initialized and self.selected_camera_type:
                if hasattr(self, 'selected_product') and self.selected_product:
                    product_name = self.selected_product.get('product_name', 'default')
                    self.initialize_camera_for_product(product_name)
                else:
                    # Initialize with default settings if no product selected
                    self.init_tis_camera_with_defaults()
                
                if not self.camera_initialized:
                    messagebox.showerror("Error", "Failed to initialize camera")
                    return
                
            image = None
            
            if self.selected_camera_type == 'tis':
                image = self.capture_from_tis_camera()
            elif self.selected_camera_type == 'raspi':
                image = self.capture_from_raspi_camera()
            else:
                messagebox.showerror("Error", f"Unsupported camera type: {self.selected_camera_type}")
                return
                
            if image is not None:
                self.process_captured_image(image)
            else:
                messagebox.showerror("Error", "Failed to capture image from camera")
                
        except Exception as e:
            logger.error(f"Camera capture failed: {e}")
            messagebox.showerror("Error", f"Camera capture failed:\\n{e}")
            
    def capture_from_tis_camera(self):
        """Capture image from TIS camera."""
        try:
            if not self.tis_camera:
                logger.error("TIS camera not initialized")
                return None
                
            # Ensure pipeline is running
            if not self.tis_camera.start_pipeline():
                logger.error("Failed to start TIS pipeline")
                return None
            
            # Capture image
            buffer_data = self.tis_camera.snap_image(timeout=5, convert_to_mat=True)
            if buffer_data is not None:
                # Get the converted numpy array
                image = self.tis_camera.get_image()
                if image is not None:
                    logger.info(f"TIS camera captured image successfully - shape: {image.shape}")
                    return image
                else:
                    logger.error("Failed to convert captured buffer to numpy array")
                    return None
            else:
                logger.error("Failed to capture image from TIS camera")
                return None
            
        except Exception as e:
            logger.error(f"TIS camera capture failed: {e}")
            return None
            
    def capture_from_raspi_camera(self):
        """Capture image from Raspberry Pi camera."""
        try:
            if self.camera.get('type') == 'libcamera':
                # Use libcamera command
                import subprocess
                import tempfile
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    temp_path = temp_file.name
                    
                result = subprocess.run([
                    'libcamera-still',
                    '-o', temp_path,
                    '--width', '1920',
                    '--height', '1080',
                    '--timeout', '1000'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    image = cv2.imread(temp_path)
                    os.unlink(temp_path)  # Clean up temp file
                    return image
                else:
                    logger.error(f"libcamera-still failed: {result.stderr}")
                    return None
                    
            else:
                # Use legacy picamera
                import io
                import numpy as np
                
                # Capture to memory
                stream = io.BytesIO()
                self.camera.capture(stream, format='jpeg')
                
                # Convert to opencv format
                stream.seek(0)
                image_array = np.frombuffer(stream.getvalue(), dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                return image
                
        except Exception as e:
            logger.error(f"Raspberry Pi camera capture failed: {e}")
            return None
            
    def process_captured_image(self, image):
        """Process and send captured image for inspection."""
        try:
            # Display the captured image
            self.display_image_from_array(image)
            
            # Send for inspection
            self.send_image_for_inspection(image)
            
        except Exception as e:
            logger.error(f"Process captured image failed: {e}")
            messagebox.showerror("Error", f"Failed to process captured image:\\n{e}")
            
    def display_image_from_array(self, image_array):
        """Display image from numpy array."""
        try:
            # Convert BGR to RGB for display
            if len(image_array.shape) == 3:
                display_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            else:
                display_image = image_array
                
            # Convert to PIL and store
            self.current_image_pil = Image.fromarray(display_image)
            self.current_image = image_array.copy()
            
            # Resize for display
            display_size = (800, 600)
            resized = self.current_image_pil.resize(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(resized)
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo  # Keep a reference
            
        except Exception as e:
            logger.error(f"Display image failed: {e}")
            
    def send_image_for_inspection(self, image_array):
        """Send image array for inspection via API."""
        try:
            # Convert image to base64
            _, buffer = cv2.imencode('.jpg', image_array)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send to server
            payload = {
                'image': image_base64,
                'timestamp': datetime.now().isoformat()
            }
            
            # Start timing the inspection processing (server-side processing only)
            inspection_start_time = time.time()
            logger.info("Starting single image inspection processing timer")
            
            response = requests.post(
                f"{self.server_url}/api/inspect/{self.session_id}",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Calculate inspection processing time
            inspection_end_time = time.time()
            inspection_processing_time = inspection_end_time - inspection_start_time
            logger.info(f"Single image inspection processing completed in {inspection_processing_time:.2f} seconds")
            
            results = response.json()
            # Override the server's processing_time with our client-side measurement
            results['processing_time'] = inspection_processing_time
            logger.info(f"Overriding server processing time with client measurement: {inspection_processing_time:.2f}s")
            
            self.process_inspection_results(results)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Send image for inspection failed: {e}")
            messagebox.showerror("Error", f"Inspection request failed:\\n{e}")
        except Exception as e:
            logger.error(f"Send image for inspection failed: {e}")
            messagebox.showerror("Error", f"Inspection failed:\\n{e}")
    
    def load_and_inspect_image(self):
        """Load an image from file and send for inspection."""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Image for Inspection",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
            )
            
            if file_path:
                cv_image = cv2.imread(file_path)
                if cv_image is not None:
                    # Display captured image
                    self.display_image(cv_image)
                    
                    # Send for inspection
                    self.send_for_inspection(cv_image)
                    
                else:
                    messagebox.showerror("Error", "Failed to load image")
            
        except Exception as e:
            logger.error(f"Load and inspect failed: {e}")
            messagebox.showerror("Error", f"Load and inspect failed:\\n{e}")
            
    def display_image(self, cv_image):
        """Display image in the UI."""
        try:
            # Resize for display
            display_height = 400
            aspect_ratio = cv_image.shape[1] / cv_image.shape[0]
            display_width = int(display_height * aspect_ratio)
            
            resized = cv2.resize(cv_image, (display_width, display_height))
            
            # Convert to PIL format
            image_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update label
            self.image_label.config(image=photo, text="")
            # Keep reference to prevent garbage collection
            self.current_photo = photo
            
        except Exception as e:
            logger.error(f"Display image failed: {e}")
            
    def has_barcode_rois(self):
        """Check if the current product has any barcode ROIs defined."""
        try:
            if not self.selected_product:
                return False
                
            response = requests.get(f"{self.server_url}/get_roi_groups/{self.selected_product['product_name']}")
            if response.status_code != 200:
                return False
                
            roi_groups = response.json().get('roi_groups', {})
            for group_info in roi_groups.values():
                for roi in group_info.get('rois', []):
                    if roi.get('roi_type_name') == 'barcode':
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking barcode ROIs: {e}")
            return False
            
    def get_device_count_from_rois(self):
        """Get the number of devices from ROI configuration."""
        try:
            if not self.selected_product:
                return 2  # Default to 2 devices
                
            response = requests.get(f"{self.server_url}/get_roi_groups/{self.selected_product['product_name']}")
            if response.status_code != 200:
                return 2  # Default to 2 devices if API fails
                
            roi_groups = response.json().get('roi_groups', {})
            device_ids = set()
            
            for group_info in roi_groups.values():
                for roi in group_info.get('rois', []):
                    # Try to get device_id from roi configuration
                    device_id = roi.get('device_id', 1)
                    device_ids.add(device_id)
            
            return max(len(device_ids), 2)  # At least 2 devices
        except Exception as e:
            logger.error(f"Error getting device count: {e}")
            return 2  # Default to 2 devices
            
    def get_device_barcode_for_inspection(self):
        """Get device barcodes for inspection - from manual input if no barcode ROIs exist."""
        has_barcode_roi = self.has_barcode_rois()
        device_barcodes = {}
        
        if not has_barcode_roi:
            # No barcode ROI defined, use manual input for each device
            for device_id, barcode_var in self.device_barcode_vars.items():
                manual_barcode = barcode_var.get().strip()
                if manual_barcode:
                    device_barcodes[device_id] = manual_barcode
        # If barcode ROI exists, barcodes will be extracted automatically
        
        return device_barcodes if device_barcodes else None
            
    def auto_populate_device_barcode(self, results):
        """Auto-populate device barcode fields if barcodes were detected from ROI."""
        try:
            # Look for barcode results in device summaries
            device_summaries = results.get('device_summaries', {})
            for device_id_str, summary in device_summaries.items():
                device_id = int(device_id_str)
                barcode = summary.get('barcode', '')
                
                # Only auto-populate if the field exists and is currently empty
                if device_id in self.device_barcode_vars:
                    current_value = self.device_barcode_vars[device_id].get().strip()
                    if not current_value and barcode and barcode != 'N/A':
                        self.device_barcode_vars[device_id].set(barcode)
                        logger.info(f"Auto-populated device {device_id} barcode: {barcode}")
                        
        except Exception as e:
            logger.error(f"Error auto-populating device barcodes: {e}")
    
    def send_for_inspection(self, cv_image):
        """Send image to server for inspection."""
        try:
            if not self.session_active or not self.session_id:
                messagebox.showerror("Error", "No active session")
                return
            
            # Encode image to base64
            _, buffer = cv2.imencode('.jpg', cv_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Get device barcodes for inspection
            device_barcodes = self.get_device_barcode_for_inspection()
            
            # Send inspection request
            inspection_data = {
                'image': f"data:image/jpeg;base64,{image_base64}"
            }
            
            # Add device barcodes if available (for cases without barcode ROI)
            if device_barcodes:
                inspection_data['device_barcodes'] = device_barcodes
            
            self.overall_result_var.set("Processing...")
            self.overall_result_label.config(fg='orange')
            self.root.update()
            
            # Start timing the inspection processing (server-side processing only)
            inspection_start_time = time.time()
            logger.info("Starting session-based inspection processing timer")
            
            response = requests.post(f"{self.server_url}/api/session/{self.session_id}/inspect",
                                   json=inspection_data, timeout=60)
            response.raise_for_status()
            
            # Calculate inspection processing time
            inspection_end_time = time.time()
            inspection_processing_time = inspection_end_time - inspection_start_time
            logger.info(f"Session-based inspection processing completed in {inspection_processing_time:.2f} seconds")
            
            # Process results
            results = response.json()
            # Override the server's processing_time with our client-side measurement
            results['processing_time'] = inspection_processing_time
            logger.info(f"Overriding server processing time with client measurement: {inspection_processing_time:.2f}s")
            
            self.process_inspection_results(results)
            
        except Exception as e:
            logger.error(f"Send for inspection failed: {e}")
            self.overall_result_var.set("INSPECTION\\nERROR")
            self.overall_result_label.config(fg='red')
            messagebox.showerror("Error", f"Inspection failed:\\n{e}")
            
    def process_inspection_results(self, results):
        """Process and display inspection results with device grouping."""
        try:
            self.last_inspection_results = results
            
            # Auto-populate device barcode if detected from barcode ROI
            self.auto_populate_device_barcode(results)

            overall_result = results['overall_result']
            passed = overall_result['passed']            # Update overall result display
            result_text = "PASS" if passed else "FAIL"
            detail_text = f"({overall_result['passed_rois']}/{overall_result['total_rois']}) ROIs"
            time_text = f"Time: {results['processing_time']:.1f}s"
            
            self.overall_result_var.set(f"{result_text}\\n{detail_text}\\n{time_text}")
            self.overall_result_label.config(fg='green' if passed else 'red')
            
            # Update device results display
            device_summaries = results.get('device_summaries', {})
            logger.info(f"DEBUG: device_summaries received: {device_summaries}")
            self.update_device_results(device_summaries)
            
            # Clear and populate results tree
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Group results by device
            device_summaries = results.get('device_summaries', {})
            
            # If we have device summaries, show them first
            if device_summaries:
                for device_id, summary in device_summaries.items():
                    device_text = f"Device {device_id}"
                    device_passed = summary.get('device_passed', False)
                    status_text = "PASS" if device_passed else "FAIL"
                    
                    # Handle missing fields safely
                    barcode = summary.get('barcode', 'N/A')
                    passed_rois = summary.get('passed_rois', 0)
                    total_rois = summary.get('total_rois', 0)
                    
                    details_text = f"Barcode: {barcode}, ROIs: {passed_rois}/{total_rois}"
                    
                    # Insert device summary
                    device_item = self.results_tree.insert('', 'end',
                                           text=device_text,
                                           values=('Device', status_text, details_text))
                    
                    # Add ROI results under each device
                    for roi_result in summary.get('results', []):
                        roi_id = roi_result['roi_id']
                        roi_type_name = roi_result['roi_type_name']
                        status = "PASS" if roi_result['passed'] else "FAIL"
                        
                        # Normalize ROI type display
                        if roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
                            # Always show COMPARE for comparison operations regardless of match_result
                            roi_type = "COMPARE"
                        else:
                            roi_type = roi_type_name.upper()
                        
                        # Create details text based on type
                        if roi_type_name == 'barcode':
                            details = f"Barcode: {roi_result.get('barcode_values', ['None'])[0] if roi_result.get('barcode_values') else 'None'}"
                        elif roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
                            # For comparison operations, show similarity score
                            similarity = roi_result.get('ai_similarity', 0)
                            details = f"Similarity: {similarity:.3f}"
                        elif roi_type_name == 'ocr':
                            details = f"Text: {roi_result.get('ocr_text', 'None')}"
                        else:
                            details = f"Result: {roi_result.get('result', 'N/A')}"
                        
                        self.results_tree.insert(device_item, 'end',
                                               text=f"ROI {roi_id}",
                                               values=(roi_type, status, details))
                
            else:
                # Fallback to flat ROI listing if no device grouping
                for roi_result in results['roi_results']:
                    roi_id = roi_result['roi_id']
                    roi_type_name = roi_result['roi_type_name']
                    status = "PASS" if roi_result['passed'] else "FAIL"
                    
                    # Normalize ROI type display
                    if roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
                        # Always show COMPARE for comparison operations regardless of match_result
                        roi_type = "COMPARE"
                    else:
                        roi_type = roi_type_name.upper()
                    
                    # Create details text based on type
                    if roi_type_name == 'barcode':
                        details = f"Barcode: {roi_result.get('barcode_values', ['None'])[0] if roi_result.get('barcode_values') else 'None'}"
                    elif roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
                        # For comparison operations, show similarity score
                        similarity = roi_result.get('ai_similarity', 0)
                        details = f"Similarity: {similarity:.3f}"
                    elif roi_type_name == 'ocr':
                        details = f"Text: {roi_result.get('ocr_text', 'None')}"
                    else:
                        details = f"Result: {roi_result.get('result', 'N/A')}"
                    
                    self.results_tree.insert('', 'end',
                                           text=f"ROI {roi_id}",
                                           values=(roi_type, status, details))
            
            # Enable detail buttons
            self.view_details_btn.config(state="normal")
            self.export_results_btn.config(state="normal")
            
            # Auto-clear and enable barcodes for next inspection cycle
            # Wait a bit to allow user to see results, then prepare for next inspection
            self.root.after(2000, self.clear_and_enable_barcodes_for_next_inspection)
            
        except Exception as e:
            logger.error(f"Process inspection results failed: {e}")
            self.overall_result_var.set("PROCESSING\\nERROR")
            self.overall_result_label.config(fg='red')
        
    def scan_available_cameras(self):
        """Scan for available cameras and populate dropdown."""
        try:
            self.camera_status_var.set("Scanning cameras...")
            self.camera_status_label.config(fg='blue')
            
            self.available_cameras = []
            camera_options = []
            
            # Try to import and scan TIS cameras
            try:
                # Add path to src for TIS module
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
                import gi
                gi.require_version("Gst", "1.0")
                from gi.repository import Gst
                
                # Initialize GStreamer
                Gst.init(None)
                
                # Enumerate TIS devices
                monitor = Gst.DeviceMonitor.new()
                monitor.add_filter("Video/Source/tcam")
                devices = monitor.get_devices()
                
                for i, device in enumerate(devices):
                    props = device.get_properties()
                    serial = props.get_string("serial")
                    model = props.get_string("model")
                    device_name = f"{model} ({serial})" if model and serial else f"TIS Camera {i}"
                    
                    self.available_cameras.append({
                        'type': 'tis',
                        'display_name': device_name,
                        'device_info': serial
                    })
                    camera_options.append(device_name)
                    
            except Exception as e:
                print(f"TIS camera scanning failed: {e}")
                # Add fallback default TIS camera option
                self.available_cameras.append({
                    'type': 'tis',
                    'display_name': "TIS Camera - Default",
                    'device_info': None
                })
                camera_options.append("TIS Camera - Default")
                
            # Try to detect Raspberry Pi cameras
            try:
                # Check for picamera/picamera2 availability
                import subprocess
                result = subprocess.run(['which', 'libcamera-hello'], capture_output=True, text=True)
                if result.returncode == 0:
                    # libcamera tools available - likely Raspberry Pi
                    self.available_cameras.append({
                        'type': 'raspi',
                        'display_name': 'Raspberry Pi Camera',
                        'camera_info': {'type': 'libcamera'}
                    })
                    camera_options.append('Raspberry Pi Camera')
                    
                # Check for older picamera
                try:
                    import picamera
                    if not any(c['type'] == 'raspi' for c in self.available_cameras):
                        self.available_cameras.append({
                            'type': 'raspi',
                            'display_name': 'Raspberry Pi Camera (Legacy)',
                            'camera_info': {'type': 'picamera'}
                        })
                        camera_options.append('Raspberry Pi Camera (Legacy)')
                except ImportError:
                    pass
                    
            except Exception as e:
                print(f"Raspberry Pi camera detection failed: {e}")
                
            # Update dropdown
            self.camera_type_dropdown['values'] = camera_options
            
            # Update status
            if self.available_cameras:
                self.camera_status_var.set(f"Found {len(self.available_cameras)} camera(s)")
                self.camera_status_label.config(fg='green')
                
                # Auto-select first camera if only one available
                if len(self.available_cameras) == 1:
                    self.camera_type_var.set(camera_options[0])
                    self.on_camera_selected()
            else:
                self.camera_status_var.set("No cameras found")
                self.camera_status_label.config(fg='red')
                
        except Exception as e:
            logger.error(f"Camera scanning failed: {e}")
            self.camera_status_var.set("Scan failed")
            self.camera_status_label.config(fg='red')
            
    def on_camera_selected(self):
        """Handle camera selection change - initialize immediately if session is active."""
        try:
            selected_display = self.camera_type_var.get()
            if selected_display == "Select Camera":
                return
                
            # Find selected camera info
            selected_camera = None
            for camera in self.available_cameras:
                if camera['display_name'] == selected_display:
                    selected_camera = camera
                    break
                    
            if not selected_camera:
                return
                
            self.selected_camera_type = selected_camera['type']
            camera_info = selected_camera.get('device_info')  # Changed from 'camera_info' to 'device_info'
            
            # Store camera info
            self.pending_camera_info = camera_info
            
            if self.selected_camera_type == 'tis':
                device_name = camera_info if camera_info else 'Default'
                self.camera_status_var.set(f"TIS camera selected - {device_name}")
                self.camera_status_label.config(fg='orange')
                logger.info(f"TIS camera selected (device: {device_name})")
                
                # If session is active, initialize camera immediately with optimal settings
                if self.session_active and hasattr(self, 'selected_product') and self.selected_product:
                    product_name = self.selected_product.get('product_name', '')
                    if product_name:
                        logger.info(f"Session is active - initializing camera immediately with optimal settings for {product_name}")
                        self.initialize_camera_for_product(product_name)
                    else:
                        logger.info("Session is active but no product name available - using default initialization")
                        self.init_tis_camera_with_defaults()
                else:
                    logger.info("No active session - camera will be initialized when session is created")
                    
            elif self.selected_camera_type == 'raspi':
                self.camera_status_var.set(f"Raspberry Pi camera selected")
                self.camera_status_label.config(fg='orange')
                logger.info(f"Raspberry Pi camera selected")
            else:
                messagebox.showerror("Error", f"Unsupported camera type: {self.selected_camera_type}")
                
        except Exception as e:
            logger.error(f"Camera selection failed: {e}")
            self.camera_status_var.set("Selection failed")
            self.camera_status_label.config(fg='red')
            
    def init_tis_camera(self, camera_info):
        """Initialize TIS camera with full configuration."""
        try:
            self.camera_status_var.set("Initializing TIS camera...")
            self.camera_status_label.config(fg='blue')
            
            # Import TIS module
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            from TIS import SinkFormats
            
            # Use direct TIS camera initialization
            device_serial = camera_info.get('device_info') if camera_info else None
            success = self.initialize_tis_camera_direct(
                serial=device_serial,
                width=7716,     # Use proven working resolution
                height=5360,    # Use proven working resolution  
                fps=7,          # Use proven working framerate
                format_type=SinkFormats.BGRA
            )
            
            if success:
                self.camera_initialized = True
                device_name = device_serial if device_serial else 'Default'
                self.camera_status_var.set(f"TIS camera ready - {device_name}")
                self.camera_status_label.config(fg='green')
            else:
                self.camera_initialized = False
                self.camera_status_var.set("TIS init failed")
                self.camera_status_label.config(fg='red')
            
        except Exception as e:
            logger.error(f"TIS camera initialization failed: {e}")
            self.camera_status_var.set("TIS init failed")
            self.camera_status_label.config(fg='red')
            self.camera_initialized = False
            
    def init_raspi_camera(self, camera_info):
        """Initialize Raspberry Pi camera with simplified configuration."""
        try:
            self.camera_status_var.set("Initializing Pi camera...")
            self.camera_status_label.config(fg='blue')
            
            if camera_info.get('type') == 'libcamera':
                # Use libcamera for modern Pi cameras
                self.camera = {
                    'type': 'libcamera',
                    'command': 'libcamera-still',
                    'resolution': (1920, 1080)
                }
            else:
                # Use legacy picamera
                import picamera
                self.camera = picamera.PiCamera()
                self.camera.resolution = (1920, 1080)
                
            self.camera_initialized = True
            self.camera_status_var.set("Pi camera ready")
            self.camera_status_label.config(fg='green')
            
        except Exception as e:
            logger.error(f"Pi camera initialization failed: {e}")
            self.camera_status_var.set("Pi init failed")
            self.camera_status_label.config(fg='red')
            self.camera_initialized = False
            
    def show_detailed_results(self):
        """Show detailed results in a new window with ROI images."""
        if not self.last_inspection_results:
            return
            
        # Create new window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Detailed Inspection Results")
        detail_window.geometry("1200x800")
        
        # Create main frame with scrollbar
        main_frame = tk.Frame(detail_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar for the main content
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Overall results section
        overall_frame = tk.LabelFrame(scrollable_frame, text="Overall Results", font=("Arial", 12, "bold"))
        overall_frame.pack(fill="x", pady=(0, 10))
        
        overall_result = self.last_inspection_results['overall_result']
        overall_text = f"Result: {'PASS' if overall_result['passed'] else 'FAIL'}\n"
        overall_text += f"ROIs: {overall_result['passed_rois']}/{overall_result['total_rois']}\n"
        overall_text += f"Processing Time: {self.last_inspection_results['processing_time']:.2f}s"
        
        tk.Label(overall_frame, text=overall_text, font=("Arial", 10), justify="left").pack(anchor="w", padx=10, pady=5)
        
        # ROI Details section
        roi_frame = tk.LabelFrame(scrollable_frame, text="ROI Details", font=("Arial", 12, "bold"))
        roi_frame.pack(fill="both", expand=True)
        
        for i, roi_result in enumerate(self.last_inspection_results['roi_results']):
            self.create_roi_detail_frame(roi_frame, roi_result, i)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
   
    def create_roi_detail_frame(self, parent, roi_result, index):
        """Create a detailed frame for a single ROI result."""
        import base64
        from PIL import Image, ImageTk
        from io import BytesIO
        
        # Create frame for this ROI
        roi_frame = tk.LabelFrame(parent, text=f"ROI {roi_result['roi_id']}", font=("Arial", 10, "bold"))
        roi_frame.pack(fill="x", pady=5, padx=5)
        
        # Create main content frame (horizontal layout)
        content_frame = tk.Frame(roi_frame)
        content_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side - Text information
        text_frame = tk.Frame(content_frame)
        text_frame.pack(side="left", fill="both", expand=True)
        
        # ROI information
        roi_type_name = roi_result['roi_type_name']
        # Normalize ROI type display
        if roi_type_name in ['compare', 'different'] or roi_result.get('match_result'):
            roi_type_display = "COMPARE"
        else:
            roi_type_display = roi_type_name.upper()
        
        info_text = f"Type: {roi_type_display}\n"
        info_text += f"Status: {'PASS' if roi_result['passed'] else 'FAIL'}\n"
        info_text += f"Coordinates: {roi_result['coordinates']}\n"
        
        # Add type-specific information
        if roi_result['roi_type_name'] == 'barcode':
            info_text += f"Barcode: {roi_result.get('barcode_values', 'None')}\n"
        elif roi_result['roi_type_name'] == 'compare':
            info_text += f"Similarity: {roi_result.get('ai_similarity', 0):.3f}\n"
            info_text += f"Threshold: {roi_result.get('threshold', 0.9):.3f}\n"
            # Add accuracy improvement note for compare ROIs
            if roi_result['passed']:
                info_text += f"✓ Comparison PASSED - Add more golden samples to improve accuracy\n"
            else:
                info_text += f"✗ Comparison FAILED - Add golden samples to improve matching\n"
        elif roi_result['roi_type_name'] == 'ocr':
            info_text += f"Text: {roi_result.get('ocr_text', 'None')}\n"
        
        tk.Label(text_frame, text=info_text, font=("Arial", 9), justify="left", anchor="nw").pack(anchor="nw")
        
        # Right side - Images and Actions
        image_frame = tk.Frame(content_frame)
        image_frame.pack(side="right", padx=(10, 0))
        
        # Golden Sample Management Frame - ALWAYS show for compare ROIs
        if roi_result.get('roi_type_name') == 'compare':
            golden_frame = tk.Frame(image_frame)
            golden_frame.pack(pady=(0, 10))
            
            # Status-based button styling and text
            if roi_result['passed']:
                # PASS case - encourage adding more samples for better accuracy
                take_golden_btn = tk.Button(golden_frame, text="🌟 Add Golden Sample", 
                                        command=lambda: self.take_golden_sample(roi_result),
                                        bg='#28a745', fg="white", font=("Arial", 8, "bold"),
                                        relief='raised', bd=2)
                take_golden_btn.pack(pady=(0, 5))
                
                # Add helpful text
                help_label = tk.Label(golden_frame, text="✓ Comparison PASSED\nAdd more samples to\nimprove accuracy", 
                                    bg='#f0f0f0', font=("Arial", 7), fg='#28a745', justify="center")
                help_label.pack(pady=(0, 5))
                
            else:
                # FAIL case - urgent need for golden samples
                take_golden_btn = tk.Button(golden_frame, text="⚠️ Add Golden Sample", 
                                        command=lambda: self.take_golden_sample(roi_result),
                                        bg='#ffc107', fg="black", font=("Arial", 8, "bold"),
                                        relief='raised', bd=2)
                take_golden_btn.pack(pady=(0, 5))
                
                # Add urgent text
                help_label = tk.Label(golden_frame, text="✗ Comparison FAILED\nAdd golden samples\nto improve matching", 
                                    bg='#f0f0f0', font=("Arial", 7), fg='#dc3545', justify="center")
                help_label.pack(pady=(0, 5))
            
            # Manage Golden Samples button (always available)
            manage_golden_btn = tk.Button(golden_frame, text="📁 Manage Golden Samples", 
                                        command=lambda: self.manage_golden_samples(roi_result),
                                        bg='#17a2b8', fg="white", font=("Arial", 8))
            manage_golden_btn.pack()
            
        # Display ROI image if available
        if roi_result.get('roi_image_file'):
            try:
                # Read ROI image from shared folder
                session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
                output_dir = os.path.join(session_dir, "output")
                roi_image_path = os.path.join(output_dir, roi_result['roi_image_file'])
                
                if os.path.exists(roi_image_path):
                    roi_img = Image.open(roi_image_path)
                    
                    # Resize image for display (max 150x150)
                    roi_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                    roi_photo = ImageTk.PhotoImage(roi_img)
                    
                    roi_label = tk.Label(image_frame, text="ROI Image")
                    roi_label.pack()
                    roi_img_label = tk.Label(image_frame, image=roi_photo)
                    roi_img_label.image = roi_photo  # Keep reference
                    roi_img_label.pack(pady=(0, 5))
                else:
                    tk.Label(image_frame, text="ROI Image\n(File not found)", bg="gray").pack()
            except Exception as e:
                logger.warning(f"Failed to display ROI image: {e}")
                tk.Label(image_frame, text="ROI Image\n(Failed to load)", bg="gray").pack()
        
        # Fallback: try base64 format for backward compatibility
        elif roi_result.get('roi_image'):
            try:
                roi_image_data = roi_result['roi_image']
                # Handle data URL format (data:image/jpeg;base64,...)
                if roi_image_data.startswith('data:'):
                    roi_image_data = roi_image_data.split(',', 1)[1]
                
                roi_img_data = base64.b64decode(roi_image_data)
                roi_img = Image.open(BytesIO(roi_img_data))
                
                # Resize image for display (max 150x150)
                roi_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                roi_photo = ImageTk.PhotoImage(roi_img)
                
                roi_label = tk.Label(image_frame, text="ROI Image")
                roi_label.pack()
                roi_img_label = tk.Label(image_frame, image=roi_photo)
                roi_img_label.image = roi_photo  # Keep reference
                roi_img_label.pack(pady=(0, 5))
            except Exception as e:
                logger.warning(f"Failed to display ROI image: {e}")
                tk.Label(image_frame, text="ROI Image\n(Failed to load)", bg="gray").pack()
        
        # Display golden image if available
        if roi_result.get('golden_image_file'):
            try:
                # Read golden image from shared folder
                session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
                output_dir = os.path.join(session_dir, "output")
                golden_image_path = os.path.join(output_dir, roi_result['golden_image_file'])
                
                if os.path.exists(golden_image_path):
                    golden_img = Image.open(golden_image_path)
                    
                    # Resize image for display (max 150x150)
                    golden_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                    golden_photo = ImageTk.PhotoImage(golden_img)
                    
                    golden_label = tk.Label(image_frame, text="Golden Image")
                    golden_label.pack()
                    golden_img_label = tk.Label(image_frame, image=golden_photo)
                    golden_img_label.image = golden_photo  # Keep reference
                    golden_img_label.pack()
                else:
                    tk.Label(image_frame, text="Golden Image\n(File not found)", bg="gray").pack()
            except Exception as e:
                logger.warning(f"Failed to display golden image: {e}")
                tk.Label(image_frame, text="Golden Image\n(Failed to load)", bg="gray").pack()
        
        # Fallback: try base64 format for backward compatibility
        elif roi_result.get('golden_image'):
            try:
                golden_image_data = roi_result['golden_image']
                # Handle data URL format (data:image/jpeg;base64,...)
                if golden_image_data.startswith('data:'):
                    golden_image_data = golden_image_data.split(',', 1)[1]
                
                golden_img_data = base64.b64decode(golden_image_data)
                golden_img = Image.open(BytesIO(golden_img_data))
                
                # Resize image for display (max 150x150)
                golden_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                golden_photo = ImageTk.PhotoImage(golden_img)
                
                golden_label = tk.Label(image_frame, text="Golden Image")
                golden_label.pack()
                golden_img_label = tk.Label(image_frame, image=golden_photo)
                golden_img_label.image = golden_photo  # Keep reference
                golden_img_label.pack()
            except Exception as e:
                logger.warning(f"Failed to display golden image: {e}")
                tk.Label(image_frame, text="Golden Image\n(Failed to load)", bg="gray").pack()
    
    def export_results(self):
        """Export results to JSON file."""
        if not self.last_inspection_results:
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Results",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(self.last_inspection_results, f, indent=2)
                
                messagebox.showinfo("Success", f"Results exported to {file_path}")
                
        except Exception as e:
            logger.error(f"Export results failed: {e}")
            messagebox.showerror("Error", f"Export failed:\\n{e}")
    
    def take_golden_sample(self, roi_result):
        """Take the current ROI image as a golden sample."""
        try:
            roi_id = roi_result['roi_id']
            roi_type = roi_result.get('roi_type_name')
            roi_passed = roi_result.get('passed', False)
            
            # Only allow taking golden samples for compare ROIs
            if roi_type != 'compare':
                self.show_warning_dialog("Warning", "Golden samples can only be taken for Compare ROIs")
                return
            
            # Get the ROI image file
            roi_image_file = roi_result.get('roi_image_file')
            if not roi_image_file:
                self.show_error_dialog("Error", "No ROI image found to save as golden sample")
                return
            
            # Get the ROI image path
            session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
            output_dir = os.path.join(session_dir, "output")
            roi_image_path = os.path.join(output_dir, roi_image_file)
            
            if not os.path.exists(roi_image_path):
                self.show_error_dialog("Error", "ROI image file not found")
                return
            
            # Create status-specific confirmation message
            if roi_passed:
                # PASS case - emphasize accuracy improvement
                similarity = roi_result.get('ai_similarity', 0)
                threshold = roi_result.get('threshold', 0.9)
                
                confirm_message = (f"ROI {roi_id} comparison PASSED with similarity {similarity:.3f} (threshold: {threshold:.3f})\n\n"
                                f"✓ Adding this as a golden sample will:\n"
                                f"• Improve comparison accuracy\n"
                                f"• Strengthen the golden sample database\n"
                                f"• Help maintain consistent PASS results\n\n"
                                f"Continue adding this golden sample?")
            else:
                # FAIL case - emphasize fixing the issue
                similarity = roi_result.get('ai_similarity', 0)
                threshold = roi_result.get('threshold', 0.9)
                
                confirm_message = (f"ROI {roi_id} comparison FAILED with similarity {similarity:.3f} (threshold: {threshold:.3f})\n\n"
                                f"⚠️ Adding this as a golden sample will:\n"
                                f"• Help future similar parts PASS\n"
                                f"• Expand acceptable variation range\n"
                                f"• Improve comparison tolerance\n\n"
                                f"Add this image as a new golden sample?")
            
            result = self.show_confirm_dialog("Add Golden Sample", confirm_message)
            
            if not result:
                return
            
            # Call server API to save golden sample
            with open(roi_image_path, 'rb') as f:
                files = {'golden_image': f}
                data = {
                    'product_name': self.selected_product_var.get(),
                    'roi_id': roi_id,
                    'sample_type': 'pass_sample' if roi_passed else 'fail_sample',  # Track the type
                    'similarity_score': roi_result.get('ai_similarity', 0)  # Track the similarity when added
                }
                
                response = requests.post(f"{self.server_url}/api/golden-sample/save", 
                                    files=files, data=data)
                response.raise_for_status()
                
                result_data = response.json()
                message = result_data.get('message', 'Golden sample saved successfully')
                
                # Status-specific success message
                if roi_passed:
                    success_message = (f"✅ Golden sample added for ROI {roi_id}!\n\n"
                                    f"{message}\n\n"
                                    f"This PASS sample will help:\n"
                                    f"• Maintain consistent results\n"
                                    f"• Improve comparison confidence\n"
                                    f"• Build a robust golden sample library")
                else:
                    success_message = (f"⚡ Golden sample added for ROI {roi_id}!\n\n"
                                    f"{message}\n\n"
                                    f"This sample will help future similar parts PASS by:\n"
                                    f"• Expanding acceptable variations\n"
                                    f"• Improving comparison tolerance\n"
                                    f"• Reducing false failures")
                
                self.show_info_dialog("Golden Sample Added", success_message)
                
        except Exception as e:
            logger.error(f"Failed to take golden sample: {e}")
            self.show_error_dialog("Error", f"Failed to save golden sample:\n{e}")
    
    def manage_golden_samples(self, roi_result):
        """Open golden sample management window for this ROI."""
        try:
            roi_id = roi_result['roi_id']
            roi_type = roi_result.get('roi_type_name')
            
            # Only allow managing golden samples for compare ROIs
            if roi_type != 'compare':
                messagebox.showwarning("Warning", "Golden samples are only available for Compare ROIs")
                return
            
            # Create golden sample management window
            golden_window = tk.Toplevel(self.root)
            golden_window.title(f"Golden Samples - ROI {roi_id}")
            golden_window.geometry("800x600")
            golden_window.configure(bg='#f0f0f0')
            
            # Make window modal
            golden_window.transient(self.root)
            golden_window.grab_set()
            
            self.create_golden_management_window(golden_window, roi_id)
            
        except Exception as e:
            logger.error(f"Failed to open golden sample management: {e}")
            messagebox.showerror("Error", f"Failed to open golden sample management:\\n{e}")
    
    def create_golden_management_window(self, window, roi_id):
        """Create the golden sample management interface."""
        # Title
        title_frame = tk.Frame(window, bg='#f0f0f0')
        title_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = tk.Label(title_frame, text=f"Golden Samples for ROI {roi_id}", 
                              bg='#f0f0f0', font=("Arial", 16, "bold"), fg='#333')
        title_label.pack()
        
        # Main content frame with scrollbar
        main_frame = tk.Frame(window, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Load and display golden samples
        self.load_golden_samples(scrollable_frame, roi_id)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_frame = tk.Frame(window, bg='#f0f0f0')
        close_frame.pack(fill="x", padx=20, pady=10)
        
        close_btn = tk.Button(close_frame, text="Close", command=window.destroy,
                             bg='#6c757d', fg="white", font=("Arial", 10))
        close_btn.pack(side="right")
    
    def load_golden_samples(self, parent, roi_id):
        """Load and display golden samples for the specified ROI."""
        try:
            # Get golden samples from server
            response = requests.get(f"{self.server_url}/api/golden-sample/{self.selected_product_var.get()}/{roi_id}")
            response.raise_for_status()
            
            golden_data = response.json()
            golden_samples = golden_data.get('golden_samples', [])
            
            if not golden_samples:
                no_samples_label = tk.Label(parent, text="No golden samples found for this ROI", 
                                          font=("Arial", 12), fg='gray', bg='white')
                no_samples_label.pack(expand=True, pady=50)
                return
            
            # Display each golden sample
            for i, sample in enumerate(golden_samples):
                self.create_golden_sample_frame(parent, sample, roi_id, i)
                
        except Exception as e:
            logger.error(f"Failed to load golden samples: {e}")
            error_label = tk.Label(parent, text=f"Error loading golden samples: {e}", 
                                 font=("Arial", 12), fg='red', bg='white')
            error_label.pack(expand=True, pady=50)
    
    def create_golden_sample_frame(self, parent, sample, roi_id, index):
        """Create a frame for displaying a single golden sample."""
        from PIL import Image, ImageTk
        
        # Create frame for this golden sample
        sample_frame = tk.LabelFrame(parent, text=sample['name'], font=("Arial", 10, "bold"))
        sample_frame.pack(fill="x", pady=5, padx=5)
        
        # Create main content frame (horizontal layout)
        content_frame = tk.Frame(sample_frame)
        content_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side - Image
        image_frame = tk.Frame(content_frame)
        image_frame.pack(side="left", padx=(0, 10))
        
        try:
            # Load and display the golden sample image
            import base64
            from io import BytesIO
            
            image_data = sample.get('image_data')
            if image_data:
                # Handle base64 image data
                if image_data.startswith('data:'):
                    image_data = image_data.split(',', 1)[1]
                
                img_data = base64.b64decode(image_data)
                img = Image.open(BytesIO(img_data))
                
                # Resize image for display (max 150x150)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_label = tk.Label(image_frame, image=photo)
                img_label.image = photo  # Keep reference
                img_label.pack()
            else:
                tk.Label(image_frame, text="Image not available", bg="gray", width=20, height=10).pack()
                
        except Exception as e:
            logger.warning(f"Failed to display golden sample image: {e}")
            tk.Label(image_frame, text="Image loading failed", bg="gray", width=20, height=10).pack()
        
        # Right side - Information and actions
        info_frame = tk.Frame(content_frame)
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Sample information
        info_text = f"Type: {sample.get('type', 'Unknown')}\n"
        info_text += f"Created: {sample.get('created_time', 'Unknown')}\n"
        info_text += f"Size: {sample.get('file_size', 'Unknown')} bytes\n"
        
        if sample.get('is_best'):
            info_text += "Status: Current Best Golden\n"
            status_color = 'green'
        else:
            info_text += "Status: Alternative Golden\n"
            status_color = 'blue'
        
        info_label = tk.Label(info_frame, text=info_text, font=("Arial", 9), 
                             justify="left", anchor="nw", fg=status_color)
        info_label.pack(anchor="nw", pady=(0, 10))
        
        # Action buttons
        button_frame = tk.Frame(info_frame)
        button_frame.pack(anchor="nw")
        
        if not sample.get('is_best'):
            # Promote to best button
            promote_btn = tk.Button(button_frame, text="Make Best Golden", 
                                  command=lambda: self.promote_golden_sample(roi_id, sample['name'], parent),
                                  bg='#28a745', fg="white", font=("Arial", 8))
            promote_btn.pack(side="left", padx=(0, 5))
        
        # Delete button (only show for non-best samples or if there are alternatives)
        if not sample.get('is_best') or len(parent.winfo_children()) > 1:
            delete_btn = tk.Button(button_frame, text="Delete", 
                                 command=lambda: self.delete_golden_sample(roi_id, sample['name'], parent),
                                 bg='#dc3545', fg="white", font=("Arial", 8))
            delete_btn.pack(side="left")
    
    def promote_golden_sample(self, roi_id, sample_name, parent_frame):
        """Promote a golden sample to be the best golden."""
        try:
            # Ask for confirmation
            result = messagebox.askyesno("Confirm", 
                f"Promote '{sample_name}' to be the best golden sample for ROI {roi_id}?\n\n" +
                "The current best golden will be demoted to alternative.")
            
            if not result:
                return
            
            # Call server API to promote golden sample
            data = {
                'product_name': self.selected_product_var.get(),
                'roi_id': roi_id,
                'sample_name': sample_name
            }
            
            response = requests.post(f"{self.server_url}/api/golden-sample/promote", json=data)
            response.raise_for_status()
            
            messagebox.showinfo("Success", f"'{sample_name}' is now the best golden sample!")
            
            # Refresh the golden samples display
            # Find the scrollable frame and reload the samples
            scrollable_frame = parent_frame
            while scrollable_frame and not isinstance(scrollable_frame, ttk.Frame):
                scrollable_frame = scrollable_frame.master
                
            if scrollable_frame:
                # Clear and reload
                for child in scrollable_frame.winfo_children():
                    child.destroy()
                self.load_golden_samples(scrollable_frame, roi_id)
                
        except Exception as e:
            logger.error(f"Failed to promote golden sample: {e}")
            messagebox.showerror("Error", f"Failed to promote golden sample:\\n{e}")
    
    def delete_golden_sample(self, roi_id, sample_name, parent_frame):
        """Delete a golden sample."""
        try:
            # Ask for confirmation
            result = messagebox.askyesno("Confirm", 
                f"Delete golden sample '{sample_name}' for ROI {roi_id}?\n\n" +
                "This action cannot be undone.")
            
            if not result:
                return
            
            # Call server API to delete golden sample
            data = {
                'product_name': self.selected_product_var.get(),
                'roi_id': roi_id,
                'sample_name': sample_name
            }
            
            response = requests.delete(f"{self.server_url}/api/golden-sample/delete", json=data)
            response.raise_for_status()
            
            messagebox.showinfo("Success", f"Golden sample '{sample_name}' deleted!")
            
            # Refresh the golden samples display
            scrollable_frame = parent_frame
            while scrollable_frame and not isinstance(scrollable_frame, ttk.Frame):
                scrollable_frame = scrollable_frame.master
                
            if scrollable_frame:
                # Clear and reload
                for child in scrollable_frame.winfo_children():
                    child.destroy()
                self.load_golden_samples(scrollable_frame, roi_id)
                
        except Exception as e:
            logger.error(f"Failed to delete golden sample: {e}")
            messagebox.showerror("Error", f"Failed to delete golden sample:\\n{e}")
            
    def close_session(self):
        """Close the current session."""
        try:
            if self.session_active and self.session_id:
                response = requests.post(f"{self.server_url}/api/session/{self.session_id}/close")
                response.raise_for_status()
                
                self.session_id = None
                self.session_active = False
                
                self.session_status_var.set("No Session")
                self.session_status_label.config(fg='orange')
                
                # Update overall result to show session needed
                if self.server_status_var.get() == "Connected":
                    self.overall_result_var.set("Select Product\\nCreate Session")
                    self.overall_result_label.config(fg='blue')
                
        except Exception as e:
            logger.error(f"Close session failed: {e}")
            
    def open_roi_definition(self):
        """Open ROI definition window."""
        if not self.selected_product_var.get():
            messagebox.showerror("Error", "Please select a product first")
            return
            
        try:
            # Create ROI definition window
            roi_window = tk.Toplevel(self.root)
            roi_window.title(f"Define ROIs - {self.selected_product_var.get()}")
            roi_window.geometry("1200x800")
            roi_window.configure(bg='#f0f0f0')
            
            # Make window modal and stay on top
            roi_window.transient(self.root)
            roi_window.grab_set()
            roi_window.attributes('-topmost', True)
            
            ROIDefinitionWindow(roi_window, self.selected_product_var.get(), self.server_url, self)
            
        except Exception as e:
            logger.error(f"Failed to open ROI definition: {e}")
            messagebox.showerror("Error", f"Failed to open ROI definition:\n{e}")
            
    def open_golden_management(self):
        """Open golden sample management window."""
        if not self.selected_product_var.get():
            messagebox.showerror("Error", "Please select a product first")
            return
            
        try:
            # Create golden sample management window
            golden_window = tk.Toplevel(self.root)
            golden_window.title(f"Manage Golden Samples - {self.selected_product_var.get()}")
            golden_window.geometry("1000x700")
            golden_window.configure(bg='#f0f0f0')
            
            # Make window modal and stay on top
            golden_window.transient(self.root)
            golden_window.grab_set()
            golden_window.attributes('-topmost', True)
            
            GoldenSampleWindow(golden_window, self.selected_product_var.get(), self.server_url)
            
        except Exception as e:
            logger.error(f"Failed to open golden sample management: {e}")
            messagebox.showerror("Error", f"Failed to open golden sample management:\n{e}")
            
    def run(self):
        """Run the client application."""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Client application error: {e}")
            
    def on_closing(self):
        """Handle application closing."""
        try:
            # Close session and disconnect
            if self.session_active:
                self.close_session()
                    
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during closing: {e}")


class ROIDefinitionWindow:
    """Window for defining ROIs on images."""
    
    def __init__(self, window, product_name, server_url, main_app):
        self.window = window
        self.product_name = product_name
        self.server_url = server_url
        self.main_app = main_app
        
        # Variables
        self.current_image = None
        self.current_image_pil = None
        self.roi_list = []
        self.drawing = False
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.scale_factor = 1.0
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # ROI types
        self.roi_types = [
            ("Barcode", 1),
            ("Compare", 2), 
            ("OCR", 3)
        ]

        self.init_ui()
        # Load existing ROIs but don't try to display them yet (no image loaded)
        self.load_existing_rois()
        # Set default model based on default ROI type
        self.update_model_for_roi_type()
    
    def show_message(self, msg_type, title, message):
        """Show messagebox dialog with proper parent and topmost settings."""
        # Ensure the dialog appears on top of the ROI window
        if msg_type == "info":
            self.window.attributes('-topmost', False)  # Temporarily disable topmost
            messagebox.showinfo(title, message, parent=self.window)
            self.window.attributes('-topmost', True)   # Re-enable topmost
        elif msg_type == "error":
            self.window.attributes('-topmost', False)
            messagebox.showerror(title, message, parent=self.window)
            self.window.attributes('-topmost', True)
        elif msg_type == "warning":
            self.window.attributes('-topmost', False)
            messagebox.showwarning(title, message, parent=self.window)
            self.window.attributes('-topmost', True)
        elif msg_type == "question":
            self.window.attributes('-topmost', False)
            result = messagebox.askyesno(title, message, parent=self.window)
            self.window.attributes('-topmost', True)
            return result
    
    def show_info(self, title, message):
        """Show info dialog."""
        return self.show_message("info", title, message)
    
    def show_error(self, title, message):
        """Show error dialog."""
        return self.show_message("error", title, message)
    
    def show_warning(self, title, message):
        """Show warning dialog."""
        return self.show_message("warning", title, message)
    
    def ask_yes_no(self, title, message):
        """Show yes/no question dialog."""
        return self.show_message("question", title, message)
        
    def init_ui(self):
        """Initialize the ROI definition UI."""
        # Main frame
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_frame, bg='#f0f0f0', width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Image capture section
        image_frame = tk.LabelFrame(left_panel, text="Image", bg='#f0f0f0', font=("Arial", 12, "bold"))
        image_frame.pack(fill="x", pady=(0, 10))
        
        # Button frame for multiple options
        btn_frame = tk.Frame(image_frame, bg='#f0f0f0')
        btn_frame.pack(padx=10, pady=10)
        
        capture_btn = tk.Button(btn_frame, text="Capture Image",
                               command=self.capture_image,
                               bg='#007ACC', fg="white", font=("Arial", 10))
        capture_btn.pack(side="left", padx=(0, 5))
        
        load_btn = tk.Button(btn_frame, text="Load File",
                           command=self.load_image,
                           bg='#6c757d', fg="white", font=("Arial", 10))
        load_btn.pack(side="left", padx=(5, 0))
        
        # Zoom controls
        zoom_frame = tk.Frame(image_frame, bg='#f0f0f0')
        zoom_frame.pack(padx=10, pady=(0, 10))
        
        tk.Label(zoom_frame, text="Zoom:", bg='#f0f0f0', font=("Arial", 10, "bold")).pack(side="left")
        
        zoom_out_btn = tk.Button(zoom_frame, text="−", width=3,
                                command=self.zoom_out,
                                bg='#dc3545', fg="white", font=("Arial", 12, "bold"))
        zoom_out_btn.pack(side="left", padx=(10, 2))
        
        self.zoom_label = tk.Label(zoom_frame, text="100%", bg='#f0f0f0', 
                                  font=("Arial", 10), width=6)
        self.zoom_label.pack(side="left", padx=2)
        
        zoom_in_btn = tk.Button(zoom_frame, text="+", width=3,
                               command=self.zoom_in,
                               bg='#28a745', fg="white", font=("Arial", 12, "bold"))
        zoom_in_btn.pack(side="left", padx=(2, 5))
        
        reset_zoom_btn = tk.Button(zoom_frame, text="Fit",
                                  command=self.reset_zoom,
                                  bg='#17a2b8', fg="white", font=("Arial", 9))
        reset_zoom_btn.pack(side="left", padx=(5, 0))
        
        # ROI definition section
        roi_frame = tk.LabelFrame(left_panel, text="ROI Definition", bg='#f0f0f0', font=("Arial", 12, "bold"))
        roi_frame.pack(fill="x", pady=(0, 10))
        
        # ROI type selection
        tk.Label(roi_frame, text="ROI Type:", bg='#f0f0f0').pack(anchor="w", padx=10, pady=(10, 5))
        
        self.roi_type_var = tk.IntVar(value=2)  # Default to Compare
        for name, value in self.roi_types:
            tk.Radiobutton(roi_frame, text=name, variable=self.roi_type_var, value=value,
                         bg='#f0f0f0', command=self.update_model_for_roi_type).pack(anchor="w", padx=20)
        
        # ROI parameters (dynamic based on type)
        self.params_frame = tk.Frame(roi_frame, bg='#f0f0f0')
        self.params_frame.pack(fill="x", padx=10, pady=10)
        
        # Initialize variables for all possible parameters
        self.focus_var = tk.IntVar(value=305)
        self.exposure_var = tk.IntVar(value=1200)
        self.threshold_var = tk.DoubleVar(value=0.9)
        self.device_id_var = tk.IntVar(value=1)
        self.model_var = tk.StringVar(value="mobilenet")
        self.rotation_var = tk.IntVar(value=0)
        self.sample_text_var = tk.StringVar(value="")  # For OCR sample text comparison
        
        # Store references to dynamic widgets
        self.param_widgets = {}
        
        # Create initial parameter UI
        self.create_dynamic_params()
        
        # Instructions
        instructions = tk.Label(roi_frame, 
                              text="Instructions:\n1. Capture image from camera or load file\n2. Use zoom controls or mouse wheel to zoom\n3. Select ROI type (parameters will update)\n4. Click and drag to define ROI\n5. Adjust type-specific parameters\n6. Save ROIs",
                              bg='#f0f0f0', justify="left", font=("Arial", 9))
        instructions.pack(padx=10, pady=10)
        
        # ROI list section
        list_frame = tk.LabelFrame(left_panel, text="Defined ROIs", bg='#f0f0f0', font=("Arial", 12, "bold"))
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # ROI listbox with scrollbar
        list_container = tk.Frame(list_frame, bg='#f0f0f0')
        list_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.roi_listbox = tk.Listbox(list_container, font=("Arial", 9))
        self.roi_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.roi_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.roi_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Add double-click binding for easier ROI editing
        self.roi_listbox.bind('<Double-Button-1>', lambda e: self.edit_roi())
        # Add right-click context menu
        self.roi_listbox.bind('<Button-3>', self.show_roi_context_menu)
        # Add hover effects for better UX
        self.roi_listbox.bind('<Motion>', self.on_roi_list_hover)
        self.roi_listbox.bind('<Leave>', self.clear_roi_hover)
        
        # ROI list controls
        list_btn_frame = tk.Frame(list_frame, bg='#f0f0f0')
        list_btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        delete_btn = tk.Button(list_btn_frame, text="Delete Selected",
                             command=self.delete_roi,
                             bg='#dc3545', fg="white", font=("Arial", 9))
        delete_btn.pack(side="left", padx=(0, 5))
        
        edit_btn = tk.Button(list_btn_frame, text="Edit",
                           command=self.edit_roi,
                           bg='#ffc107', fg="black", font=("Arial", 9))
        edit_btn.pack(side="left", padx=(0, 5))
        
        clear_btn = tk.Button(list_btn_frame, text="Clear All",
                            command=self.clear_rois,
                            bg='#6c757d', fg="white", font=("Arial", 9))
        clear_btn.pack(side="left")
        
        # Save/Cancel buttons
        btn_frame = tk.Frame(left_panel, bg='#f0f0f0')
        btn_frame.pack(fill="x")
        
        save_btn = tk.Button(btn_frame, text="Save ROIs",
                           command=self.save_rois,
                           bg='#28a745', fg="white", font=("Arial", 11, "bold"))
        save_btn.pack(side="left", padx=(0, 5))
        
        cancel_btn = tk.Button(btn_frame, text="Cancel",
                             command=self.window.destroy,
                             bg='#6c757d', fg="white", font=("Arial", 11))
        cancel_btn.pack(side="left")
        
        # Right panel - Image display
        right_panel = tk.Frame(main_frame, bg='white', relief='sunken', bd=2)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Image canvas
        self.canvas = tk.Canvas(right_panel, bg='white', cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind mouse events for ROI drawing
        self.canvas.bind("<Button-1>", self.start_roi)
        self.canvas.bind("<B1-Motion>", self.draw_roi)
        self.canvas.bind("<ButtonRelease-1>", self.end_roi)
        
        # Bind mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux
        
    def capture_image(self):
        """Capture an image from camera for ROI definition."""
        try:
            # Check if camera is available
            if not self.main_app.camera_initialized:
                self.show_error("Error", "Camera not initialized. Please initialize camera first.")
                return
                
            # Capture image using main app's camera functionality
            image = None
            if self.main_app.selected_camera_type == 'tis':
                image = self.main_app.capture_from_tis_camera()
            elif self.main_app.selected_camera_type == 'raspi':
                image = self.main_app.capture_from_raspi_camera()
            else:
                self.show_error("Error", f"Unsupported camera type: {self.main_app.selected_camera_type}")
                return
                
            if image is not None:
                # Convert numpy array to PIL Image
                if len(image.shape) == 3:
                    # BGR to RGB conversion for color images
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    self.current_image_pil = Image.fromarray(image_rgb)
                else:
                    # Grayscale image
                    self.current_image_pil = Image.fromarray(image)
                    
                self.display_image()
                self.show_info("Success", "Image captured successfully!")
                # Load existing ROIs from server and redraw them
                self.load_existing_rois_and_redraw()
                
            else:
                self.show_error("Error", "Failed to capture image from camera")
                
        except Exception as e:
            logger.error(f"Failed to capture image: {e}")
            self.show_error("Error", f"Failed to capture image:\n{e}")
                
    def load_image(self):
        """Load an image for ROI definition."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            try:
                # Load and display image
                self.current_image_pil = Image.open(file_path)
                self.display_image()
                # Load existing ROIs from server and redraw them
                self.load_existing_rois_and_redraw()
                
            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                self.show_error("Error", f"Failed to load image:\n{e}")
                
    def display_image(self):
        """Display the current image on canvas with zoom support."""
        if self.current_image_pil:
            # Get canvas size
            self.canvas.update()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calculate base scale factor to fit image in canvas
            img_width, img_height = self.current_image_pil.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            base_scale = min(scale_x, scale_y, 1.0)  # Don't scale up initially
            
            # Apply zoom factor
            self.scale_factor = base_scale * self.zoom_factor
            
            # Resize image
            new_width = int(img_width * self.scale_factor)
            new_height = int(img_height * self.scale_factor)
            
            resized_image = self.current_image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and display
            self.photo = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas and center image
            self.canvas.delete("all")
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.canvas.create_image(x, y, image=self.photo, anchor="nw")
            
            # Store image position for coordinate calculation
            self.image_x = x
            self.image_y = y
            self.image_width = new_width
            self.image_height = new_height
            
            # Update zoom label
            zoom_percent = int(self.zoom_factor * 100)
            self.zoom_label.config(text=f"{zoom_percent}%")
            
            # Redraw existing ROIs
            self.redraw_rois()
            
    def zoom_in(self):
        """Zoom in on the image."""
        if self.current_image_pil and self.zoom_factor < self.max_zoom:
            self.zoom_factor = min(self.zoom_factor * 1.2, self.max_zoom)
            self.display_image()
            
    def zoom_out(self):
        """Zoom out on the image."""
        if self.current_image_pil and self.zoom_factor > self.min_zoom:
            self.zoom_factor = max(self.zoom_factor / 1.2, self.min_zoom)
            self.display_image()
            
    def reset_zoom(self):
        """Reset zoom to fit the image in canvas."""
        if self.current_image_pil:
            self.zoom_factor = 1.0
            self.display_image()
            
    def update_model_for_roi_type(self):
        """Update model selection based on ROI type and refresh dynamic parameters."""
        roi_type = self.roi_type_var.get()
        if roi_type == 1:  # Barcode
            self.model_var.set("opencv")
        elif roi_type == 2:  # Compare
            self.model_var.set("mobilenet")
        elif roi_type == 3:  # OCR
            self.model_var.set("ocr")
            
        # Refresh dynamic parameters UI
        self.create_dynamic_params()
        
    def create_dynamic_params(self):
        """Create dynamic parameter UI based on selected ROI type."""
        # Clear existing widgets
        for widget in self.param_widgets.values():
            widget.destroy()
        self.param_widgets.clear()
        
        # Clear the frame
        for widget in self.params_frame.winfo_children():
            widget.destroy()
            
        roi_type = self.roi_type_var.get()
        row = 0
        
        # Common parameters for all types
        # Device Location (Device ID)
        label = tk.Label(self.params_frame, text="Device Location:", bg='#f0f0f0')
        label.grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(self.params_frame, textvariable=self.device_id_var, width=10)
        entry.grid(row=row, column=1, padx=(5, 0), pady=2)
        self.param_widgets[f'device_label_{row}'] = label
        self.param_widgets[f'device_entry_{row}'] = entry
        row += 1
        
        # Focus
        label = tk.Label(self.params_frame, text="Focus:", bg='#f0f0f0')
        label.grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(self.params_frame, textvariable=self.focus_var, width=10)
        entry.grid(row=row, column=1, padx=(5, 0), pady=2)
        self.param_widgets[f'focus_label_{row}'] = label
        self.param_widgets[f'focus_entry_{row}'] = entry
        row += 1
        
        # Exposure
        label = tk.Label(self.params_frame, text="Exposure:", bg='#f0f0f0')
        label.grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(self.params_frame, textvariable=self.exposure_var, width=10)
        entry.grid(row=row, column=1, padx=(5, 0), pady=2)
        self.param_widgets[f'exposure_label_{row}'] = label
        self.param_widgets[f'exposure_entry_{row}'] = entry
        row += 1
        
        # Type-specific parameters
        if roi_type == 1:  # Barcode
            # No additional parameters for barcode
            pass
            
        elif roi_type == 2:  # Compare
            # Model
            label = tk.Label(self.params_frame, text="Model:", bg='#f0f0f0')
            label.grid(row=row, column=0, sticky="w", pady=2)
            combo = ttk.Combobox(self.params_frame, textvariable=self.model_var, width=12,
                               values=["mobilenet", "yolo", "custom"])
            combo.grid(row=row, column=1, padx=(5, 0), pady=2)
            combo.state(['readonly'])
            self.param_widgets[f'model_label_{row}'] = label
            self.param_widgets[f'model_combo_{row}'] = combo
            row += 1
            
            # Threshold
            label = tk.Label(self.params_frame, text="Threshold:", bg='#f0f0f0')
            label.grid(row=row, column=0, sticky="w", pady=2)
            entry = tk.Entry(self.params_frame, textvariable=self.threshold_var, width=10)
            entry.grid(row=row, column=1, padx=(5, 0), pady=2)
            self.param_widgets[f'threshold_label_{row}'] = label
            self.param_widgets[f'threshold_entry_{row}'] = entry
            row += 1
            
        elif roi_type == 3:  # OCR
            # Rotation
            label = tk.Label(self.params_frame, text="Rotation:", bg='#f0f0f0')
            label.grid(row=row, column=0, sticky="w", pady=2)
            combo = ttk.Combobox(self.params_frame, textvariable=self.rotation_var, width=12,
                               values=["0", "90", "180", "270"])
            combo.grid(row=row, column=1, padx=(5, 0), pady=2)
            combo.state(['readonly'])
            self.param_widgets[f'rotation_label_{row}'] = label
            self.param_widgets[f'rotation_combo_{row}'] = combo
            row += 1
            
            # Sample Text for comparison
            label = tk.Label(self.params_frame, text="Sample Text:", bg='#f0f0f0')
            label.grid(row=row, column=0, sticky="w", pady=2)
            entry = tk.Entry(self.params_frame, textvariable=self.sample_text_var, width=15)
            entry.grid(row=row, column=1, padx=(5, 0), pady=2)
            self.param_widgets[f'sample_text_label_{row}'] = label
            self.param_widgets[f'sample_text_entry_{row}'] = entry
            row += 1
            
            # Add a help label for sample text
            help_label = tk.Label(self.params_frame, text="(OCR will PASS if detected text contains this value)", 
                                bg='#f0f0f0', font=("Arial", 8), fg='#666666')
            help_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 5))
            self.param_widgets[f'sample_text_help_{row}'] = help_label
            row += 1
            
    def on_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming."""
        if self.current_image_pil:
            # Get mouse position
            mouse_x = event.x
            mouse_y = event.y
            
            # Determine zoom direction
            if event.delta > 0 or event.num == 4:  # Zoom in
                if self.zoom_factor < self.max_zoom:
                    self.zoom_factor = min(self.zoom_factor * 1.1, self.max_zoom)
                    self.display_image()
            elif event.delta < 0 or event.num == 5:  # Zoom out
                if self.zoom_factor > self.min_zoom:
                    self.zoom_factor = max(self.zoom_factor / 1.1, self.min_zoom)
                    self.display_image()
            
    def start_roi(self, event):
        """Start drawing ROI rectangle."""
        if not self.current_image_pil:
            self.show_warning("Warning", "Please capture or load an image first")
            return
            
        # Check if click is within image bounds
        if (hasattr(self, 'image_x') and hasattr(self, 'image_y') and 
            hasattr(self, 'image_width') and hasattr(self, 'image_height') and
            self.image_x <= event.x <= self.image_x + self.image_width and
            self.image_y <= event.y <= self.image_y + self.image_height):
            
            self.drawing = True
            self.start_x = event.x
            self.start_y = event.y
            
    def draw_roi(self, event):
        """Draw ROI rectangle while dragging."""
        if (self.drawing and self.current_image_pil and 
            hasattr(self, 'start_x') and hasattr(self, 'start_y') and
            self.start_x is not None and self.start_y is not None):
            
            # Remove previous rectangle
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                
            # Draw new rectangle
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=2, tags="temp_roi"
            )
            
    def end_roi(self, event):
        """Finish drawing ROI rectangle."""
        if (self.drawing and self.current_image_pil and 
            hasattr(self, 'start_x') and hasattr(self, 'start_y') and
            self.start_x is not None and self.start_y is not None):
            
            self.drawing = False
            
            # Calculate actual image coordinates
            x1 = int((self.start_x - self.image_x) / self.scale_factor)
            y1 = int((self.start_y - self.image_y) / self.scale_factor)
            x2 = int((event.x - self.image_x) / self.scale_factor)
            y2 = int((event.y - self.image_y) / self.scale_factor)
            
            # Ensure coordinates are in correct order
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
                
            # Validate ROI size
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                if self.current_rect:
                    self.canvas.delete(self.current_rect)
                    self.current_rect = None
                self.show_warning("Warning", "ROI too small. Please draw a larger rectangle.")
                return
                
            # Create ROI data with proper index calculation
            roi_id = self.get_next_roi_index()
            roi_type = self.roi_type_var.get()
            focus = self.focus_var.get()
            exposure = self.exposure_var.get()
            threshold = self.threshold_var.get() if roi_type == 2 else None  # Only for Compare type
            device_id = self.device_id_var.get()
            
            # Set model based on ROI type
            if roi_type == 1:  # Barcode
                model = "opencv"
            elif roi_type == 2:  # Compare
                model = self.model_var.get()
            elif roi_type == 3:  # OCR
                model = "ocr"
            else:
                model = self.model_var.get()
                
            rotation = int(self.rotation_var.get()) if str(self.rotation_var.get()).isdigit() else 0
            
            # Get sample text for OCR ROIs
            sample_text = self.sample_text_var.get().strip() if roi_type == 3 and hasattr(self, 'sample_text_var') else None
            sample_text = sample_text if sample_text else None  # Convert empty string to None
            
            # ROI format: [id, type, [x1, y1, x2, y2], focus, exposure, threshold, model, rotation, device_id, sample_text]
            roi_data = [
                roi_id,
                roi_type,
                [x1, y1, x2, y2],
                focus,
                exposure,
                threshold,
                model,
                rotation,
                device_id,
                sample_text
            ]
            
            self.roi_list.append(roi_data)
            self.update_roi_list()
            self.redraw_rois()
            
            # Clear temporary rectangle
            if self.current_rect:
                self.canvas.delete(self.current_rect)
                self.current_rect = None
                
    def redraw_rois(self):
        """Redraw all ROIs on the canvas."""
        if not hasattr(self, 'image_x') or not hasattr(self, 'image_y'):
            return
            
        # Clear existing ROI rectangles
        self.canvas.delete("roi_rect")
        
        for i, roi in enumerate(self.roi_list):
            try:
                roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
                x1, y1, x2, y2 = coords
                
                # Convert to canvas coordinates
                canvas_x1 = int(x1 * self.scale_factor) + self.image_x
                canvas_y1 = int(y1 * self.scale_factor) + self.image_y
                canvas_x2 = int(x2 * self.scale_factor) + self.image_x
                canvas_y2 = int(y2 * self.scale_factor) + self.image_y
                
                # Color by type
                colors = {1: "blue", 2: "red", 3: "green"}
                color = colors.get(roi_type, "black")
                
                # Draw rectangle
                self.canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                    outline=color, width=2, tags="roi_rect"
                )
                
                # Draw ROI ID label
                self.canvas.create_text(
                    canvas_x1 + 5, canvas_y1 + 5,
                    text=f"ROI {roi_id}",
                    fill=color, font=("Arial", 10, "bold"),
                    anchor="nw", tags="roi_rect"
                )
            except Exception as e:
                logger.error(f"Error redrawing ROI {i}: {e}")
                continue
            
    def update_roi_list(self):
        """Update the ROI list display."""
        self.roi_listbox.delete(0, tk.END)
        
        type_names = {1: "Barcode", 2: "Compare", 3: "OCR"}
        
        for roi in self.roi_list:
            # Handle both 9-field and 10-field ROI formats for backward compatibility
            if len(roi) >= 10:
                roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id, sample_text = roi
            else:
                roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
                sample_text = None
                
            type_name = type_names.get(roi_type, "Unknown")
            x1, y1, x2, y2 = coords
            
            # Create comprehensive display text
            text = f"ROI {roi_id}: {type_name} ({x1},{y1},{x2},{y2})"
            text += f" Dev:{device_id} Model:{model}"
            text += f" F:{focus} E:{exposure}"
            
            if roi_type == 2 and threshold is not None:
                text += f" T:{threshold}"
                
            if rotation != 0:
                text += f" R:{rotation}°"
                
            # Add sample text for OCR ROIs
            if roi_type == 3 and sample_text:
                text += f" Sample:'{sample_text}'"
                
            self.roi_listbox.insert(tk.END, text)
            
    def delete_roi(self):
        """Delete selected ROI."""
        selection = self.roi_listbox.curselection()
        if selection:
            index = selection[0]
            
            # Store original ROI IDs before deletion for golden sample folder renaming
            original_roi_ids = [roi[0] for roi in self.roi_list]
            
            # Delete the selected ROI
            del self.roi_list[index]
            
            # Create mapping for golden sample folder renaming
            # Map old ROI IDs to new ROI IDs after re-numbering
            roi_mapping = {}
            
            # Re-number ROIs and build mapping
            for i, roi in enumerate(self.roi_list):
                old_roi_id = roi[0]  # Current ROI ID
                new_roi_id = i + 1   # New sequential ID
                roi[0] = new_roi_id  # Update ROI ID
                
                # Only add to mapping if the ID actually changes
                if old_roi_id != new_roi_id:
                    roi_mapping[old_roi_id] = new_roi_id
            
            # Rename golden sample folders if there are changes
            if roi_mapping and hasattr(self, 'product_name') and self.product_name:
                self.rename_golden_sample_folders(roi_mapping)
            
            self.update_roi_list()
            self.redraw_rois()
    
    def rename_golden_sample_folders(self, roi_mapping):
        """Rename golden sample folders to match new ROI indices."""
        try:
            response = requests.post(
                f"{self.server_url}/api/golden-sample/rename-folders",
                json={
                    'product_name': self.product_name,
                    'roi_mapping': roi_mapping
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('renamed_count', 0) > 0:
                    print(f"Renamed {result['renamed_count']} golden sample folders")
            else:
                print(f"Warning: Failed to rename golden sample folders: {response.text}")
                
        except Exception as e:
            print(f"Warning: Error renaming golden sample folders: {e}")
            # Don't raise the error - this is non-critical for ROI deletion
            
    def clear_rois(self):
        """Clear all ROIs."""
        if self.ask_yes_no("Confirm", "Are you sure you want to clear all ROIs?"):
            self.roi_list.clear()
            self.update_roi_list()
            self.redraw_rois()
            
    def edit_roi(self):
        """Edit selected ROI parameters with a proper dialog."""
        selection = self.roi_listbox.curselection()
        if not selection:
            self.show_warning("Warning", "Please select an ROI to edit")
            return
            
        index = selection[0]
        roi = self.roi_list[index]
        
        # Handle both 9-field and 10-field ROI formats for backward compatibility
        if len(roi) >= 10:
            roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id, sample_text = roi
        else:
            roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
            sample_text = None  # Default for backward compatibility
        
        # Create ROI editing dialog
        self.show_edit_roi_dialog(index, roi)
    
    def show_edit_roi_dialog(self, roi_index, roi):
        """Show comprehensive ROI editing dialog."""
        # Handle both 9-field and 10-field ROI formats for backward compatibility
        if len(roi) >= 10:
            roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id, sample_text = roi
        else:
            roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
            sample_text = None  # Default for backward compatibility
        
        # Create dialog window
        edit_window = tk.Toplevel(self.window)
        edit_window.title(f"Edit ROI {roi_id}")
        edit_window.geometry("500x600")
        edit_window.resizable(True, True)
        edit_window.transient(self.window)
        edit_window.grab_set()
        
        # Center the window
        edit_window.update_idletasks()
        width = edit_window.winfo_width()
        height = edit_window.winfo_height()
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Edit ROI {roi_id}", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Coordinates section (read-only)
        coords_frame = ttk.LabelFrame(main_frame, text="Coordinates", padding="10")
        coords_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(coords_frame, text=f"Position: ({coords[0]}, {coords[1]})").pack(anchor="w")
        ttk.Label(coords_frame, text=f"Size: {coords[2] - coords[0]} × {coords[3] - coords[1]}").pack(anchor="w")
        ttk.Label(coords_frame, text=f"Bounds: {coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}").pack(anchor="w")
        
        # ROI Type section
        type_frame = ttk.LabelFrame(main_frame, text="ROI Type", padding="10")
        type_frame.pack(fill=tk.X, pady=5)
        
        roi_type_var = tk.IntVar(value=roi_type)
        
        type_inner_frame = ttk.Frame(type_frame)
        type_inner_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(type_inner_frame, text="🔲 Barcode", variable=roi_type_var, 
                       value=1).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(type_inner_frame, text="🔍 Compare", variable=roi_type_var, 
                       value=2).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(type_inner_frame, text="📝 OCR", variable=roi_type_var, 
                       value=3).pack(side="left")
        
        # Camera Settings section
        camera_frame = ttk.LabelFrame(main_frame, text="Camera Settings", padding="10")
        camera_frame.pack(fill=tk.X, pady=5)
        
        # Focus
        focus_frame = ttk.Frame(camera_frame)
        focus_frame.pack(fill=tk.X, pady=2)
        ttk.Label(focus_frame, text="Focus:", width=15).pack(side="left")
        focus_var = tk.IntVar(value=focus)
        focus_spinbox = ttk.Spinbox(focus_frame, from_=0, to=1023, textvariable=focus_var, 
                                   width=10)
        focus_spinbox.pack(side="left", padx=5)
        ttk.Label(focus_frame, text="(0-1023)", foreground="gray").pack(side="left", padx=5)
        
        # Exposure
        exposure_frame = ttk.Frame(camera_frame)
        exposure_frame.pack(fill=tk.X, pady=2)
        ttk.Label(exposure_frame, text="Exposure:", width=15).pack(side="left")
        exposure_var = tk.IntVar(value=exposure)
        exposure_spinbox = ttk.Spinbox(exposure_frame, from_=100, to=1000000, 
                                      textvariable=exposure_var, width=10)
        exposure_spinbox.pack(side="left", padx=5)
        ttk.Label(exposure_frame, text="(µs)", foreground="gray").pack(side="left", padx=5)
        
        # Device ID
        device_frame = ttk.Frame(camera_frame)
        device_frame.pack(fill=tk.X, pady=2)
        ttk.Label(device_frame, text="Device ID:", width=15).pack(side="left")
        device_var = tk.IntVar(value=device_id)
        device_spinbox = ttk.Spinbox(device_frame, from_=0, to=10, textvariable=device_var, 
                                    width=10)
        device_spinbox.pack(side="left", padx=5)
        ttk.Label(device_frame, text="(camera index)", foreground="gray").pack(side="left", padx=5)
        
        # Type-specific settings section
        specific_frame = ttk.LabelFrame(main_frame, text="Type-Specific Settings", padding="10")
        specific_frame.pack(fill=tk.X, pady=5)
        
        # Compare settings
        compare_frame = ttk.Frame(specific_frame)
        
        threshold_frame = ttk.Frame(compare_frame)
        threshold_frame.pack(fill=tk.X, pady=2)
        ttk.Label(threshold_frame, text="Threshold:", width=15).pack(side="left")
        threshold_var = tk.DoubleVar(value=threshold if threshold is not None else 0.9)
        threshold_spinbox = ttk.Spinbox(threshold_frame, from_=0.5, to=1.0, increment=0.05,
                                       textvariable=threshold_var, width=10, format="%.2f")
        threshold_spinbox.pack(side="left", padx=5)
        ttk.Label(threshold_frame, text="(0.5-1.0)", foreground="gray").pack(side="left", padx=5)
        
        model_frame = ttk.Frame(compare_frame)
        model_frame.pack(fill=tk.X, pady=2)
        ttk.Label(model_frame, text="Model:", width=15).pack(side="left")
        model_var = tk.StringVar(value=model if model else "opencv")
        model_combo = ttk.Combobox(model_frame, textvariable=model_var, 
                                  values=["opencv", "mobilenet"], state="readonly", width=10)
        model_combo.pack(side="left", padx=5)
        
        # OCR settings
        ocr_frame = ttk.Frame(specific_frame)
        
        rotation_frame = ttk.Frame(ocr_frame)
        rotation_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rotation_frame, text="Rotation:", width=15).pack(side="left")
        rotation_var = tk.IntVar(value=rotation)
        rotation_combo = ttk.Combobox(rotation_frame, textvariable=rotation_var,
                                     values=["0", "90", "180", "270"], state="readonly", width=10)
        rotation_combo.pack(side="left", padx=5)
        ttk.Label(rotation_frame, text="(degrees)", foreground="gray").pack(side="left", padx=5)
        
        # Sample Text field for OCR ROIs
        sample_text_frame = ttk.Frame(ocr_frame)
        sample_text_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sample_text_frame, text="Sample Text:", width=15).pack(side="left")
        sample_text_var = tk.StringVar(value=sample_text if sample_text else "")
        sample_text_entry = ttk.Entry(sample_text_frame, textvariable=sample_text_var, width=20)
        sample_text_entry.pack(side="left", padx=5)
        ttk.Label(sample_text_frame, text="(PASS if OCR contains this text)", foreground="gray").pack(side="left", padx=5)
        
        # Dynamic field visibility based on ROI type
        def update_type_fields(*args):
            # Hide all type-specific frames
            compare_frame.pack_forget()
            ocr_frame.pack_forget()
            
            roi_type_val = roi_type_var.get()
            if roi_type_val == 2:  # Compare
                compare_frame.pack(fill=tk.X)
            elif roi_type_val == 3:  # OCR
                ocr_frame.pack(fill=tk.X)
        
        roi_type_var.trace_add('write', update_type_fields)
        update_type_fields()  # Initialize
        
        # Current vs New comparison section
        info_frame = ttk.LabelFrame(main_frame, text="Current Configuration", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        info_text = tk.Text(info_frame, height=6, width=50, wrap=tk.WORD, state="disabled")
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        
        info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar.pack(side="right", fill="y")
        
        def update_info():
            info_text.config(state="normal")
            info_text.delete(1.0, tk.END)
            
            type_names = {1: "Barcode", 2: "Compare", 3: "OCR"}
            current_type = type_names.get(roi_type, "Unknown")
            new_type = type_names.get(roi_type_var.get(), "Unknown")
            
            # Safe getter for variables that might be empty
            def safe_get(var, default=""):
                try:
                    value = var.get()
                    return value if value != "" else default
                except (tk.TclError, ValueError):
                    return default
            
            info_content = f"""ROI ID: {roi_id}
Type: {current_type} → {new_type}
Coordinates: ({coords[0]}, {coords[1]}, {coords[2]}, {coords[3]})
Focus: {focus} → {safe_get(focus_var, focus)}
Exposure: {exposure}µs → {safe_get(exposure_var, exposure)}µs
Device: {device_id} → {safe_get(device_var, device_id)}"""
            
            if roi_type_var.get() == 2:  # Compare
                threshold_val = safe_get(threshold_var, threshold)
                try:
                    threshold_formatted = f"{float(threshold_val):.2f}" if threshold_val else f"{threshold:.2f}"
                except (ValueError, TypeError):
                    threshold_formatted = f"{threshold:.2f}"
                info_content += f"\nThreshold: {threshold} → {threshold_formatted}"
                info_content += f"\nModel: {model} → {safe_get(model_var, model)}"
            elif roi_type_var.get() == 3:  # OCR
                rotation_val = safe_get(rotation_var, rotation)
                info_content += f"\nRotation: {rotation}° → {rotation_val}°"
                current_sample = sample_text if sample_text else "(none)"
                new_sample = safe_get(sample_text_var, "").strip()
                new_sample = new_sample if new_sample else "(none)"
                info_content += f"\nSample Text: {current_sample} → {new_sample}"
            
            info_text.insert(1.0, info_content)
            info_text.config(state="disabled")
        
        # Update info on any change
        for var in [roi_type_var, focus_var, exposure_var, device_var, threshold_var, model_var, rotation_var, sample_text_var]:
            var.trace_add('write', lambda *args: update_info())
        
        update_info()  # Initial update
        
        # Buttons section
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_save():
            try:
                # Validate inputs
                new_focus = focus_var.get()
                new_exposure = exposure_var.get()
                new_device = device_var.get()
                new_type = roi_type_var.get()
                
                if not (0 <= new_focus <= 1023):
                    raise ValueError("Focus must be between 0 and 1023")
                if not (100 <= new_exposure <= 1000000):
                    raise ValueError("Exposure must be between 100 and 1,000,000 µs")
                
                # Build updated ROI
                new_threshold = None
                new_model = "opencv"
                new_rotation = 0
                
                if new_type == 2:  # Compare
                    new_threshold = threshold_var.get()
                    new_model = model_var.get()
                    if not (0.5 <= new_threshold <= 1.0):
                        raise ValueError("Threshold must be between 0.5 and 1.0")
                elif new_type == 3:  # OCR
                    new_rotation = rotation_var.get()
                
                # Get sample text for OCR ROIs (convert empty string to None)
                new_sample_text = None
                if new_type == 3:  # OCR
                    sample_text_value = sample_text_var.get().strip()
                    new_sample_text = sample_text_value if sample_text_value else None
                
                # Update ROI in the list (now with 10 fields)
                updated_roi = [
                    roi_id,  # Keep original ID
                    new_type,
                    coords,  # Keep original coordinates
                    new_focus,
                    new_exposure,
                    new_threshold,
                    new_model,
                    new_rotation,
                    new_device,
                    new_sample_text
                ]
                
                self.roi_list[roi_index] = updated_roi
                self.update_roi_list()
                self.redraw_rois()
                
                # Highlight the edited ROI briefly
                self.canvas.delete("edit_highlight")
                if hasattr(self, 'image_x') and hasattr(self, 'image_y'):
                    x1, y1, x2, y2 = coords
                    # Use consistent coordinate calculation (scale_factor already includes zoom_factor)
                    canvas_x1 = int(x1 * self.scale_factor) + self.image_x
                    canvas_y1 = int(y1 * self.scale_factor) + self.image_y
                    canvas_x2 = int(x2 * self.scale_factor) + self.image_x
                    canvas_y2 = int(y2 * self.scale_factor) + self.image_y
                    
                    highlight = self.canvas.create_rectangle(canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                                                           outline="lime", width=4, tags="edit_highlight")
                    
                    # Remove highlight after 2 seconds
                    self.window.after(2000, lambda: self.canvas.delete("edit_highlight"))
                
                edit_window.destroy()
                self.show_info("Success", f"ROI {roi_id} updated successfully!")
                
            except ValueError as e:
                self.show_error("Invalid Input", str(e))
            except Exception as e:
                self.show_error("Error", f"Failed to update ROI: {e}")
        
        def on_cancel():
            edit_window.destroy()
        
        def on_preview():
            """Preview the ROI with current settings."""
            try:
                # Highlight ROI with preview styling
                self.canvas.delete("preview_highlight")
                if hasattr(self, 'image_x') and hasattr(self, 'image_y'):
                    x1, y1, x2, y2 = coords
                    # Use consistent coordinate calculation (scale_factor already includes zoom_factor)
                    canvas_x1 = int(x1 * self.scale_factor) + self.image_x
                    canvas_y1 = int(y1 * self.scale_factor) + self.image_y
                    canvas_x2 = int(x2 * self.scale_factor) + self.image_x
                    canvas_y2 = int(y2 * self.scale_factor) + self.image_y
                    
                    self.canvas.create_rectangle(canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                                               outline="orange", width=3, dash=(5, 5), 
                                               tags="preview_highlight")
                    
                    # Remove preview highlight after 3 seconds
                    self.window.after(3000, lambda: self.canvas.delete("preview_highlight"))
                
                # Show preview info
                type_names = {1: "Barcode", 2: "Compare", 3: "OCR"}
                preview_info = f"Preview: {type_names.get(roi_type_var.get(), 'Unknown')} ROI"
                preview_info += f"\nFocus: {focus_var.get()}, Exposure: {exposure_var.get()}µs"
                
                if roi_type_var.get() == 2:
                    preview_info += f"\nThreshold: {threshold_var.get():.2f}, Model: {model_var.get()}"
                elif roi_type_var.get() == 3:
                    preview_info += f"\nRotation: {rotation_var.get()}°"
                
                self.show_info("ROI Preview", preview_info)
                
            except Exception as e:
                self.show_error("Preview Error", f"Failed to preview ROI: {e}")
        
        # Button layout
        ttk.Button(button_frame, text="💾 Save Changes", command=on_save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="👁 Preview", command=on_preview).pack(side="left", padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=on_cancel).pack(side="right", padx=5)
        
        # Focus on the first input field
        focus_spinbox.focus_set()
        
        # Bind Enter key to save
        edit_window.bind('<Return>', lambda e: on_save())
        edit_window.bind('<Escape>', lambda e: on_cancel())
    
    def show_roi_context_menu(self, event):
        """Show context menu for ROI listbox."""
        try:
            # Select the item at the click position
            index = self.roi_listbox.nearest(event.y)
            if 0 <= index < self.roi_listbox.size():
                self.roi_listbox.selection_clear(0, tk.END)
                self.roi_listbox.selection_set(index)
                
                # Create context menu
                context_menu = tk.Menu(self.window, tearoff=0)
                context_menu.add_command(label="✏️ Edit ROI", command=self.edit_roi)
                context_menu.add_command(label="👁 View Details", command=lambda: self.show_roi_details(index))
                context_menu.add_separator()
                context_menu.add_command(label="🗑️ Delete ROI", command=self.delete_roi)
                context_menu.add_separator()
                context_menu.add_command(label="📋 Copy Settings", command=lambda: self.copy_roi_settings(index))
                
                # Show menu
                context_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass  # Menu was closed
    
    def show_roi_details(self, index):
        """Show detailed information about a ROI."""
        if 0 <= index < len(self.roi_list):
            roi = self.roi_list[index]
            roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
            
            type_names = {1: "Barcode", 2: "Compare", 3: "OCR"}
            type_name = type_names.get(roi_type, "Unknown")
            
            details = f"""ROI {roi_id} Details:

Type: {type_name}
Coordinates: ({coords[0]}, {coords[1]}, {coords[2]}, {coords[3]})
Position: ({coords[0]}, {coords[1]})
Size: {coords[2] - coords[0]} × {coords[3] - coords[1]} pixels

Camera Settings:
• Focus: {focus} (0-1023)
• Exposure: {exposure} µs
• Device ID: {device_id}

Type-Specific Settings:"""
            
            if roi_type == 2:  # Compare
                details += f"""
• Threshold: {threshold}
• Model: {model}"""
            elif roi_type == 3:  # OCR
                details += f"""
• Rotation: {rotation}°"""
            else:  # Barcode
                details += """
• No additional settings"""
            
            self.show_info(f"ROI {roi_id} Details", details)
    
    def copy_roi_settings(self, index):
        """Copy ROI settings to clipboard for reference."""
        if 0 <= index < len(self.roi_list):
            roi = self.roi_list[index]
            roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
            
            type_names = {1: "Barcode", 2: "Compare", 3: "OCR"}
            type_name = type_names.get(roi_type, "Unknown")
            
            settings_text = f"""ROI {roi_id} Settings:
Type: {type_name}
Focus: {focus}
Exposure: {exposure}
Device: {device_id}"""
            
            if roi_type == 2:
                settings_text += f"""
Threshold: {threshold}
Model: {model}"""
            elif roi_type == 3:
                settings_text += f"""
Rotation: {rotation}"""
            
            # Copy to clipboard
            self.window.clipboard_clear()
            self.window.clipboard_append(settings_text)
            
            self.show_info("Copied", f"ROI {roi_id} settings copied to clipboard")
    
    def on_roi_list_hover(self, event):
        """Highlight ROI on image when hovering over it in the list."""
        try:
            index = self.roi_listbox.nearest(event.y)
            if 0 <= index < len(self.roi_list) and hasattr(self, 'image_x') and hasattr(self, 'image_y'):
                roi = self.roi_list[index]
                coords = roi[2]
                
                # Clear previous hover highlight
                self.canvas.delete("hover_highlight")
                
                # Draw hover highlight
                x1, y1, x2, y2 = coords
                # Use the same coordinate calculation as redraw_rois()
                canvas_x1 = int(x1 * self.scale_factor) + self.image_x
                canvas_y1 = int(y1 * self.scale_factor) + self.image_y
                canvas_x2 = int(x2 * self.scale_factor) + self.image_x
                canvas_y2 = int(y2 * self.scale_factor) + self.image_y
                
                self.canvas.create_rectangle(canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                                           outline="cyan", width=2, dash=(3, 3),
                                           tags="hover_highlight")
        except (IndexError, AttributeError):
            pass
    
    def clear_roi_hover(self, event=None):
        """Clear ROI hover highlighting."""
        self.canvas.delete("hover_highlight")
            
    def get_next_roi_index(self):
        """Get the next available ROI index."""
        if not self.roi_list:
            return 1
            
        # Find the highest ROI ID and add 1
        max_id = max(roi[0] for roi in self.roi_list)
        return max_id + 1
        
    def get_available_device_ids(self):
        """Get list of device IDs already in use."""
        used_device_ids = set()
        for roi in self.roi_list:
            if len(roi) >= 9:  # Ensure device_id exists
                used_device_ids.add(roi[8])  # device_id is at index 8
        return used_device_ids
            
            
    def load_existing_rois(self):
        """Load existing ROIs from server."""
        try:
            response = requests.get(f"{self.server_url}/api/products/{self.product_name}/rois")
            if response.status_code == 200:
                data = response.json()
                existing_rois = data.get('rois', [])
                if existing_rois:
                    self.roi_list = existing_rois
                    self.update_roi_list()
                    # Only redraw ROIs if we have an image loaded
                    if hasattr(self, 'current_image_pil') and self.current_image_pil:
                        self.redraw_rois()
                    self.show_info("Info", f"Loaded {len(existing_rois)} existing ROIs")
                    
        except Exception as e:
            logger.error(f"Failed to load existing ROIs: {e}")
            
    def load_existing_rois_and_redraw(self):
        """Load existing ROIs from server and redraw them on the current image."""
        try:
            response = requests.get(f"{self.server_url}/api/products/{self.product_name}/rois")
            if response.status_code == 200:
                data = response.json()
                existing_rois = data.get('rois', [])
                if existing_rois:
                    self.roi_list = existing_rois
                    self.update_roi_list()
                    # Redraw ROIs on the current image
                    if hasattr(self, 'current_image_pil') and self.current_image_pil:
                        self.redraw_rois()
                    print(f"Loaded and displayed {len(existing_rois)} existing ROIs")
                else:
                    print("No existing ROIs found")
                    
        except Exception as e:
            logger.error(f"Failed to load and redraw existing ROIs: {e}")
            
    def save_rois(self):
        """Save ROIs to server."""
        if not self.roi_list:
            self.show_warning("Warning", "No ROIs defined")
            return
            
        try:
            # Send ROIs to server
            payload = {
                'product_name': self.product_name,
                'rois': self.roi_list
            }
            
            response = requests.post(f"{self.server_url}/api/products/{self.product_name}/rois", 
                                   json=payload)
            response.raise_for_status()
            
            self.show_info("Success", f"Saved {len(self.roi_list)} ROIs successfully")
            self.window.destroy()
            
        except Exception as e:
            logger.error(f"Failed to save ROIs: {e}")
            self.show_error("Error", f"Failed to save ROIs:\n{e}")


class GoldenSampleWindow:
    """Window for managing golden samples for ROIs."""
    
    def __init__(self, window, product_name, server_url):
        self.window = window
        self.product_name = product_name
        self.server_url = server_url
        
        # Variables
        self.rois = []
        self.selected_roi = None

        self.init_ui()
        self.load_rois()
    
    def show_message(self, msg_type, title, message):
        """Show messagebox dialog with proper parent and topmost settings."""
        # Ensure the dialog appears on top of the Golden Sample window
        if msg_type == "info":
            self.window.attributes('-topmost', False)  # Temporarily disable topmost
            messagebox.showinfo(title, message, parent=self.window)
            self.window.attributes('-topmost', True)   # Re-enable topmost
        elif msg_type == "error":
            self.window.attributes('-topmost', False)
            messagebox.showerror(title, message, parent=self.window)
            self.window.attributes('-topmost', True)
        elif msg_type == "warning":
            self.window.attributes('-topmost', False)
            messagebox.showwarning(title, message, parent=self.window)
            self.window.attributes('-topmost', True)
        elif msg_type == "question":
            self.window.attributes('-topmost', False)
            result = messagebox.askyesno(title, message, parent=self.window)
            self.window.attributes('-topmost', True)
            return result
    
    def show_info(self, title, message):
        """Show info dialog."""
        return self.show_message("info", title, message)
    
    def show_error(self, title, message):
        """Show error dialog."""
        return self.show_message("error", title, message)
    
    def show_warning(self, title, message):
        """Show warning dialog."""
        return self.show_message("warning", title, message)
    
    def ask_yes_no(self, title, message):
        """Show yes/no question dialog."""
        return self.show_message("question", title, message)
        
    def init_ui(self):
        """Initialize the golden sample management UI."""
        # Main frame
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - ROI selection
        left_panel = tk.Frame(main_frame, bg='#f0f0f0', width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # ROI list section
        roi_frame = tk.LabelFrame(left_panel, text="Select ROI", bg='#f0f0f0', font=("Arial", 12, "bold"))
        roi_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # ROI listbox
        self.roi_listbox = tk.Listbox(roi_frame, font=("Arial", 10))
        self.roi_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.roi_listbox.bind('<<ListboxSelect>>', self.on_roi_selected)
        
        # Golden sample management section
        golden_frame = tk.LabelFrame(left_panel, text="Golden Sample", bg='#f0f0f0', font=("Arial", 12, "bold"))
        golden_frame.pack(fill="x")
        
        # Buttons
        btn_frame = tk.Frame(golden_frame, bg='#f0f0f0')
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.load_golden_btn = tk.Button(btn_frame, text="Load Golden Sample",
                                       command=self.load_golden_sample,
                                       bg='#007ACC', fg="white", font=("Arial", 10),
                                       state="disabled")
        self.load_golden_btn.pack(fill="x", pady=(0, 5))
        
        self.capture_golden_btn = tk.Button(btn_frame, text="Capture Golden Sample",
                                          command=self.capture_golden_sample,
                                          bg='#28a745', fg="white", font=("Arial", 10),
                                          state="disabled")
        self.capture_golden_btn.pack(fill="x", pady=(0, 5))
        
        self.delete_golden_btn = tk.Button(btn_frame, text="Delete Golden Sample",
                                         command=self.delete_golden_sample,
                                         bg='#dc3545', fg="white", font=("Arial", 10),
                                         state="disabled")
        self.delete_golden_btn.pack(fill="x")
        
        # Close button
        close_btn = tk.Button(left_panel, text="Close",
                            command=self.window.destroy,
                            bg='#6c757d', fg="white", font=("Arial", 11))
        close_btn.pack(pady=(10, 0))
        
        # Right panel - Image display
        right_panel = tk.Frame(main_frame, bg='white', relief='sunken', bd=2)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Golden sample display
        self.image_label = tk.Label(right_panel, text="Select a ROI to view/manage golden sample",
                                  bg='white', font=("Arial", 14))
        self.image_label.pack(expand=True)
        
    def load_rois(self):
        """Load ROIs for the product."""
        try:
            response = requests.get(f"{self.server_url}/api/products/{self.product_name}/rois")
            if response.status_code == 200:
                data = response.json()
                self.rois = data.get('rois', [])
                
                # Update ROI listbox
                self.roi_listbox.delete(0, tk.END)
                type_names = {1: "Barcode", 2: "Compare", 3: "OCR"}
                
                for roi in self.rois:
                    roi_id, roi_type, coords, focus, exposure, threshold, model, rotation, device_id = roi
                    type_name = type_names.get(roi_type, "Unknown")
                    text = f"ROI {roi_id}: {type_name}"
                    self.roi_listbox.insert(tk.END, text)
                    
            else:
                messagebox.showerror("Error", "Failed to load ROIs. Please define ROIs first.")
                self.window.destroy()
                
        except Exception as e:
            logger.error(f"Failed to load ROIs: {e}")
            messagebox.showerror("Error", f"Failed to load ROIs:\n{e}")
            self.window.destroy()
            
    def on_roi_selected(self, event):
        """Handle ROI selection."""
        selection = self.roi_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_roi = self.rois[index]
            
            # Enable buttons
            self.load_golden_btn.config(state="normal")
            self.capture_golden_btn.config(state="normal")
            self.delete_golden_btn.config(state="normal")
            
            # Load and display golden sample if exists
            self.display_golden_sample()
            
    def display_golden_sample(self):
        """Display the golden sample for selected ROI."""
        if not self.selected_roi:
            return
            
        try:
            roi_id = self.selected_roi[0]
            response = requests.get(f"{self.server_url}/api/products/{self.product_name}/golden/{roi_id}")
            
            if response.status_code == 200:
                # Golden sample exists
                image_data = base64.b64decode(response.json()['image'])
                image = Image.open(BytesIO(image_data))
                
                # Resize image to fit display
                image.thumbnail((400, 400), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage and display
                photo = ImageTk.PhotoImage(image)
                self.image_label.configure(image=photo, text="")
                self.image_label.image = photo  # Keep a reference
                
            else:
                # No golden sample
                self.image_label.configure(image="", text=f"No golden sample for ROI {roi_id}\nClick 'Load' or 'Capture' to add one")
                
        except Exception as e:
            logger.error(f"Failed to display golden sample: {e}")
            self.image_label.configure(image="", text="Failed to load golden sample")
            
    def load_golden_sample(self):
        """Load golden sample from file."""
        if not self.selected_roi:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Golden Sample Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            try:
                # Load and encode image
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode()
                    
                # Send to server
                roi_id = self.selected_roi[0]
                payload = {
                    'product_name': self.product_name,
                    'roi_id': roi_id,
                    'image': image_data
                }
                
                response = requests.post(f"{self.server_url}/api/products/{self.product_name}/golden/{roi_id}",
                                       json=payload)
                response.raise_for_status()
                
                messagebox.showinfo("Success", f"Golden sample loaded for ROI {roi_id}")
                self.display_golden_sample()
                
            except Exception as e:
                logger.error(f"Failed to load golden sample: {e}")
                messagebox.showerror("Error", f"Failed to load golden sample:\n{e}")
                
    def capture_golden_sample(self):
        """Capture golden sample from camera."""
        messagebox.showinfo("Info", "Camera capture for golden samples will be implemented in future version.\nPlease use 'Load Golden Sample' for now.")
        
    def delete_golden_sample(self):
        """Delete golden sample."""
        if not self.selected_roi:
            return
            
        roi_id = self.selected_roi[0]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete the golden sample for ROI {roi_id}?"):
            try:
                response = requests.delete(f"{self.server_url}/api/products/{self.product_name}/golden/{roi_id}")
                response.raise_for_status()
                
                messagebox.showinfo("Success", f"Golden sample deleted for ROI {roi_id}")
                self.display_golden_sample()
                
            except Exception as e:
                logger.error(f"Failed to delete golden sample: {e}")
                messagebox.showerror("Error", f"Failed to delete golden sample:\n{e}")


if __name__ == "__main__":
    try:
        client = VisualAOIClient()
        client.run()
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"Failed to start Visual AOI Client: {e}")
