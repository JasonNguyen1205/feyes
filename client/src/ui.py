"""
User Interface components for Visual AOI system.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

from .config import load_theme_preference, save_theme_preference
# Camera imports removed - UI should not directly handle camera operations
from .roi import get_rois, set_rois, save_rois_to_config, get_next_roi_index, save_golden_roi
from .utils import get_thumbnail_pil

# Stub functions for camera operations - UI should not handle camera directly
def capture_tis_image(*args, **kwargs):
    """Stub function - camera operations are handled by client."""
    print("WARNING: UI attempted image capture - this should be handled by client")
    return None

def set_camera_properties(*args, **kwargs):
    """Stub function - camera operations are handled by client."""
    print("WARNING: UI attempted camera property setting - this should be handled by client")
    return False

# iOS-inspired theme configuration with Liquid Glass effects
IOS_THEME = {
    # Background colors
    'bg': '#F2F2F7',           # iOS light gray background
    'secondary_bg': '#FFFFFF',  # Pure white for cards/panels
    'tertiary_bg': '#F8F8F8',  # Very light gray
    'surface': '#FFFFFF',       # Card/surface background
    
    # Liquid Glass effect colors
    'glass_bg': '#FFFFFF',      # White for glass effect
    'glass_surface': '#F8F8F8', # Light gray surface
    'glass_surface_hover': '#F0F0F0', # Slightly darker on hover
    'glass_border': '#E0E0E0',  # Light border effect
    'glass_highlight': '#E8E8E8', # Light highlight effect
    'glass_shadow': '#F5F5F5',  # Very subtle shadow for glass
    'glass_backdrop': '#F2F2F7', # Backdrop background
    
    # Text colors
    'fg': '#000000',           # Primary text (black)
    'secondary_fg': '#3C3C43', # Secondary text (iOS gray)
    'tertiary_fg': '#8E8E93',  # Tertiary text (light gray)
    'placeholder_fg': '#C7C7CC', # Placeholder text
    
    # Accent colors (iOS blue theme)
    'primary': '#007AFF',      # iOS blue
    'primary_light': '#34C759', # iOS green
    'primary_dark': '#005BBB', # Darker blue
    
    # Status colors
    'success': '#34C759',      # iOS green
    'warning': '#FF9500',      # iOS orange  
    'error': '#FF3B30',        # iOS red
    'info': '#007AFF',         # iOS blue
    
    # Interactive elements
    'button_bg': '#007AFF',    # Primary button background
    'button_fg': '#FFFFFF',    # Button text
    'button_secondary': '#F2F2F7', # Secondary button
    'button_secondary_fg': '#007AFF', # Secondary button text
    'button_active': '#005BBB', # Active/pressed state
    
    # Form elements
    'input_bg': '#FFFFFF',     # Input background
    'input_fg': '#000000',     # Input text
    'input_border': '#D1D1D6', # Input border
    'input_border_focus': '#007AFF', # Focused input border
    
    # Selection and highlights
    'select_bg': '#007AFF',    # Selection background
    'select_fg': '#FFFFFF',    # Selection text
    'highlight': '#007AFF',    # Highlight color
    
    # Borders and separators
    'border': '#D1D1D6',       # Default border
    'separator': '#C6C6C8',    # Separator lines
    
    # Shadows and depth
    'shadow': '#00000010',     # Light shadow
    'shadow_dark': '#00000020', # Darker shadow
    
    # Card and panel styling
    'card_bg': '#FFFFFF',      # Card background
    'panel_bg': '#F8F8F8',     # Panel background
    
    # Scrollbars
    'scrollbar_bg': '#F2F2F7', 
    'scrollbar_fg': '#C7C7CC',
}

# Dark theme configuration with Liquid Glass effects
DARK_THEME = {
    # Background colors
    'bg': '#1C1C1E',           # Dark gray background
    'secondary_bg': '#2C2C2E',  # Darker gray for cards/panels
    'tertiary_bg': '#3A3A3C',  # Medium gray
    'surface': '#2C2C2E',       # Card/surface background
    
    # Liquid Glass effect colors (dark mode)
    'glass_bg': '#3A3A3C',      # Medium gray for glass effect
    'glass_surface': '#2C2C2E', # Dark surface
    'glass_surface_hover': '#404040', # Lighter gray on hover
    'glass_border': '#505050',  # Subtle border
    'glass_highlight': '#555555', # Highlight effect
    'glass_shadow': '#1A1A1A',  # Darker shadow for glass in dark mode
    'glass_backdrop': '#1C1C1E', # Backdrop background
    
    # Text colors
    'fg': '#FFFFFF',           # Primary text (white)
    'secondary_fg': '#EBEBF5', # Secondary text (light gray)
    'tertiary_fg': '#8E8E93',  # Tertiary text (gray)
    'placeholder_fg': '#48484A', # Placeholder text
    
    # Accent colors (dark theme blue)
    'primary': '#0A84FF',      # Brighter blue for dark mode
    'primary_light': '#30D158', # Brighter green for dark mode
    'primary_dark': '#0056CC', # Darker blue
    
    # Status colors
    'success': '#30D158',      # Bright green
    'warning': '#FF9F0A',      # Bright orange  
    'error': '#FF453A',        # Bright red
    'info': '#0A84FF',         # Bright blue
    
    # Interactive elements
    'button_bg': '#0A84FF',    # Primary button background
    'button_fg': '#FFFFFF',    # Button text
    'button_secondary': '#48484A', # Secondary button
    'button_secondary_fg': '#0A84FF', # Secondary button text
    'button_active': '#0056CC', # Active/pressed state
    
    # Form elements
    'input_bg': '#3A3A3C',     # Input background
    'input_fg': '#FFFFFF',     # Input text
    'input_border': '#48484A', # Input border
    'input_border_focus': '#0A84FF', # Focused input border
    
    # Selection and highlights
    'select_bg': '#0A84FF',    # Selection background
    'select_fg': '#FFFFFF',    # Selection text
    'highlight': '#0A84FF',    # Highlight color
    
    # Borders and separators
    'border': '#48484A',       # Default border
    'separator': '#48484A',    # Separator lines
    
    # Shadows and depth
    'shadow': '#00000030',     # Dark shadow
    'shadow_dark': '#00000050', # Darker shadow
    
    # Card and panel styling
    'card_bg': '#2C2C2E',      # Card background
    'panel_bg': '#3A3A3C',     # Panel background
    
    # Scrollbars
    'scrollbar_bg': '#48484A', 
    'scrollbar_fg': '#8E8E93',
}

# Current active theme - will be set based on user preference
CURRENT_THEME = IOS_THEME  # Default to light theme

def set_theme(theme_name):
    """Set the current theme globally."""
    global CURRENT_THEME
    if theme_name == "dark":
        CURRENT_THEME = DARK_THEME
    else:
        CURRENT_THEME = IOS_THEME

def get_current_theme():
    """Get the current active theme."""
    return CURRENT_THEME

def apply_theme(widget, is_root=False):
    """Apply current theme to a widget and all its children."""
    theme = get_current_theme()
    try:
        widget_class = widget.winfo_class()
        
        if widget_class == 'Tk' or widget_class == 'Toplevel':
            widget.configure(bg=theme['bg'])
        elif widget_class == 'Frame':
            widget.configure(bg=theme['secondary_bg'], highlightbackground=theme['border'])
        elif widget_class == 'Label':
            widget.configure(bg=theme['secondary_bg'], fg=theme['fg'])
        elif widget_class == 'Button':
            widget.configure(
                bg=theme['button_bg'], 
                fg=theme['button_fg'],
                activebackground=theme['button_active'],
                activeforeground=theme['button_fg'],
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                font=('SF Pro Display', 16, 'normal'),  # iOS system font
                pady=12,
                cursor='hand2'
            )
        elif widget_class == 'Entry':
            widget.configure(
                bg=theme['input_bg'], 
                fg=theme['input_fg'],
                insertbackground=theme['fg'],
                selectbackground=theme['select_bg'],
                selectforeground=theme['select_fg'],
                relief='solid',
                borderwidth=1,
                highlightthickness=2,
                highlightcolor=theme['input_border_focus'],
                font=('SF Pro Display', 16)
            )
        elif widget_class == 'Text':
            widget.configure(
                bg=theme['input_bg'], 
                fg=theme['input_fg'],
                insertbackground=theme['fg'],
                selectbackground=theme['select_bg'],
                selectforeground=theme['select_fg'],
                relief='solid',
                borderwidth=1,
                font=('SF Pro Display', 16)
            )
        elif widget_class == 'Canvas':
            widget.configure(bg=theme['surface'], highlightthickness=0)
        elif widget_class == 'Scrollbar':
            widget.configure(
                bg=theme['scrollbar_bg'],
                troughcolor=theme['bg'],
                activebackground=theme['scrollbar_fg'],
                relief='flat',
                width=8  # Thin iOS-style scrollbars
            )
        elif widget_class == 'Radiobutton':
            widget.configure(
                bg=theme['secondary_bg'], 
                fg=theme['fg'],
                activebackground=theme['secondary_bg'],
                activeforeground=theme['fg'],
                selectcolor=theme['primary'],
                font=('SF Pro Display', 16)
            )
        elif widget_class == 'PanedWindow':
            widget.configure(bg=theme['bg'], sashrelief='flat')
        elif widget_class == 'Menu':
            widget.configure(
                bg=theme['surface'],
                fg=theme['fg'],
                activebackground=theme['select_bg'],
                activeforeground=theme['select_fg']
            )
    except Exception:
        pass  # Some widgets may not support all configurations
    
    # Apply theme to all children
    try:
        for child in widget.winfo_children():
            apply_theme(child)
    except Exception:
        pass

# Keep backward compatibility
def apply_ios_theme(widget, is_root=False):
    """Apply iOS-inspired theme to a widget and all its children."""
    apply_theme(widget, is_root)

def configure_ttk_theme():
    """Configure ttk widgets for current theme."""
    theme = get_current_theme()
    style = ttk.Style()
    
    # Configure Notebook (tabs)
    style.theme_use('clam')
    style.configure('TNotebook', 
                   background=theme['bg'],
                   borderwidth=0)
    style.configure('TNotebook.Tab',
                   background=theme['surface'],
                   foreground=theme['secondary_fg'],
                   padding=[8, 4],
                   borderwidth=0,
                   font=('SF Pro Display', 11, 'normal'),
                   justify='center')
    style.map('TNotebook.Tab',
              background=[('selected', theme['primary']),
                         ('active', theme['primary_light'])],
              foreground=[('selected', theme['button_fg'])])
    
    # Configure Combobox
    style.configure('TCombobox',
                   fieldbackground=theme['input_bg'],
                   background=theme['input_bg'],
                   foreground=theme['input_fg'],
                   borderwidth=1,
                   relief='solid',
                   font=('SF Pro Display', 17))
    style.map('TCombobox',
              fieldbackground=[('readonly', theme['input_bg'])],
              selectbackground=[('readonly', theme['select_bg'])])
    
    # Configure Separator
    style.configure('TSeparator', background=theme['separator'])

# Keep backward compatibility
def configure_ios_ttk_theme():
    """Configure ttk widgets for iOS-inspired theme."""
    configure_ttk_theme()

def apply_glass_effect(widget, glass_type="panel"):
    """Apply iOS 26 liquid glass effect to widgets."""
    theme = get_current_theme()
    
    try:
        widget_class = widget.winfo_class()
        
        if glass_type == "panel":
            # Main glass panel effect
            widget.configure(
                bg=theme.get('glass_surface', theme['surface']),
                highlightbackground=theme.get('glass_border', theme['border']),
                highlightthickness=1,
                relief='flat'
            )
        elif glass_type == "button":
            # Glass button effect
            widget.configure(
                bg=theme.get('glass_bg', theme['button_bg']),
                fg=theme['fg'],
                activebackground=theme.get('glass_highlight', theme['button_active']),
                relief='flat',
                borderwidth=0,
                highlightthickness=1,
                highlightbackground=theme.get('glass_border', theme['border']),
                font=('SF Pro Display', 16, 'normal'),
                pady=12,
                cursor='hand2'
            )
        elif glass_type == "surface":
            # Glass surface effect for frames
            widget.configure(
                bg=theme.get('glass_bg', theme['surface']),
                highlightbackground=theme.get('glass_border', theme['border']),
                highlightthickness=1,
                relief='flat'
            )
    except Exception as e:
        # Fallback to regular theme if glass effects fail
        print(f"Glass effect fallback: {e}")
        pass

def add_button_hover_effect(button, style="secondary"):
    """Add hover effect to an existing button."""
    theme = get_current_theme()
    
    # Determine colors based on style
    if style == "primary":
        original_bg = theme.get('glass_bg', theme['primary'])
        hover_bg = theme.get('glass_highlight', theme['primary_light'])
    elif style == "success":
        original_bg = theme['success']
        hover_bg = theme.get('button_active', theme['primary_dark'])
    elif style == "secondary":
        original_bg = theme.get('glass_surface', theme['button_secondary'])
        hover_bg = theme.get('glass_surface_hover', theme.get('glass_surface', theme['button_secondary']))
    else:
        # Auto-detect based on current background
        current_bg = button.cget('bg')
        original_bg = current_bg
        if current_bg == theme['success']:
            hover_bg = theme.get('button_active', theme['primary_dark'])
        elif current_bg == theme['primary'] or current_bg == theme.get('glass_bg'):
            hover_bg = theme.get('glass_highlight', theme['primary_light'])
        else:
            hover_bg = theme.get('glass_surface_hover', theme.get('glass_surface', theme['button_secondary']))
    
    # Add hover effects
    def on_enter(event):
        button.config(bg=hover_bg)
    
    def on_leave(event):
        button.config(bg=original_bg)
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

def create_glass_frame(parent, glass_type="panel", **kwargs):
    """Create a frame with liquid glass effect."""
    frame = tk.Frame(parent, **kwargs)
    apply_glass_effect(frame, glass_type)
    return frame

class EditROIWindow(tk.Frame):
    """ROI Editor window for drawing and editing ROIs."""
    
    def __init__(self, master, image, rois, save_callback, as_tab=False):
        super().__init__(master)
        self.image = image
        self.rois = rois
        self.save_callback = save_callback
        self.as_tab = as_tab
        self.rectangles = []
        self.temp_rect = None
        self.canvas = None
        
        # Zoom functionality variables
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        
        # Thumbnail display variables (fixed size, no zoom)
        self.thumbnail_base_width = 400
        self.thumbnail_base_height = 300
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        
        self.init_ui()

    def reload_image(self):
        """Reload the image from the camera."""
        try:
            focus = 305  # default
            if self.rois and len(self.rois) > 0 and self.rois[0] is not None and len(self.rois[0]) >= 4:
                focus = self.rois[0][3]
            
            # Set camera to appropriate focus before capture
            from .camera import set_camera_properties
            set_camera_properties(focus, None)
            
            new_img = capture_tis_image()
            if new_img is not None:
                self.image = new_img
                self.draw_image()
                from .inspection import ui_instance
                if ui_instance:
                    ui_instance.set_status("ROI editor image captured and validated successfully.")
            else:
                messagebox.showwarning("Warning", "Camera capture failed after retries. Please check camera connection and try again.")
        except Exception as e:
            print(f"Exception in reload_image: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to capture image: {e}")

    def init_ui(self):
        """Initialize the UI components."""
        if self.as_tab:
            self.pack(fill="both", expand=True)
        else:
            self.grid(row=0, column=0, sticky="nsew")
        
        # Image display canvas
        self.canvas = tk.Canvas(self, bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # Bind mouse events for ROI drawing and zoom/pan
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)  # Linux scroll down
        
        # Middle mouse button for panning
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)
        
        # Keyboard shortcuts
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.focus_set()  # Allow canvas to receive keyboard events
        
        # Scrollbars
        h_scroll = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        h_scroll.pack(fill="x")
        v_scroll = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        v_scroll.pack(fill="y")
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        # Control buttons with glass styling
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=2)
        
        # Zoom control frame
        zoom_frame = tk.Frame(btn_frame)
        zoom_frame.pack(side="left", padx=10)
        
        # Zoom controls
        zoom_in_btn = tk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in,
                               font=('SF Pro Display', 10), 
                               bg=get_current_theme().get('glass_surface', get_current_theme()['button_secondary']),
                               fg=get_current_theme()['fg'],
                               relief='flat', borderwidth=1, pady=4, cursor='hand2')
        zoom_in_btn.pack(side="left", padx=2)
        add_button_hover_effect(zoom_in_btn, "secondary")
        
        zoom_out_btn = tk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out,
                                font=('SF Pro Display', 10), 
                                bg=get_current_theme().get('glass_surface', get_current_theme()['button_secondary']),
                                fg=get_current_theme()['fg'],
                                relief='flat', borderwidth=1, pady=4, cursor='hand2')
        zoom_out_btn.pack(side="left", padx=2)
        add_button_hover_effect(zoom_out_btn, "secondary")
        
        zoom_reset_btn = tk.Button(zoom_frame, text="Reset Zoom", command=self.zoom_reset,
                                  font=('SF Pro Display', 10), 
                                  bg=get_current_theme().get('glass_surface', get_current_theme()['button_secondary']),
                                  fg=get_current_theme()['fg'],
                                  relief='flat', borderwidth=1, pady=4, cursor='hand2')
        zoom_reset_btn.pack(side="left", padx=2)
        add_button_hover_effect(zoom_reset_btn, "secondary")
        
        # Zoom level display
        self.zoom_label = tk.Label(zoom_frame, text=f"Zoom: {self.zoom_factor:.1f}x",
                                  bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                                  font=('SF Pro Display', 10))
        self.zoom_label.pack(side="left", padx=10)
        
        # Create glass-styled buttons
        save_btn = tk.Button(btn_frame, text="Save ROIs", command=self.save_rois_to_file,
                            font=('SF Pro Display', 14), 
                            bg=get_current_theme().get('glass_surface', get_current_theme()['button_secondary']),
                            fg=get_current_theme()['fg'],
                            relief='flat', borderwidth=1,
                            highlightthickness=1,
                            highlightcolor=get_current_theme().get('glass_border', get_current_theme()['primary']),
                            pady=8, cursor='hand2')
        save_btn.pack(side="right", padx=10)
        add_button_hover_effect(save_btn, "secondary")
        
        reload_btn = tk.Button(btn_frame, text="Capture Image", command=self.reload_image,
                              font=('SF Pro Display', 14), 
                              bg=get_current_theme().get('glass_bg', get_current_theme()['primary']),
                              fg=get_current_theme()['fg'],
                              relief='flat', borderwidth=1,
                              highlightthickness=1,
                              highlightcolor=get_current_theme().get('glass_highlight', get_current_theme()['primary_light']),
                              pady=8, cursor='hand2')
        reload_btn.pack(side="right", padx=10)
        add_button_hover_effect(reload_btn, "primary")
        
        # Load initial image
        self.draw_image()

    def draw_image(self, img_array=None):
        """Draw the image on the canvas."""
        if img_array is not None:
            self.image = img_array
        if self.image is not None:
            # Get canvas size
            self.update_idletasks()
            c_w = self.canvas.winfo_width()
            c_h = self.canvas.winfo_height()
            if c_w < 10 or c_h < 10:
                c_w, c_h = 800, 600
            
            img_h, img_w = self.image.shape[:2]
            
            # Apply zoom factor to the scale calculation
            base_scale = min(c_w / img_w, c_h / img_h)
            scale = base_scale * self.zoom_factor
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            
            self._img_scale = scale
            
            # Use existing offset if available (for panning), otherwise center
            if not hasattr(self, '_img_offset') or self.zoom_factor == 1.0:
                self._img_offset = ((c_w - new_w) // 2, (c_h - new_h) // 2)
            
            img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            # Use Image.Resampling.LANCZOS for newer PIL versions
            try:
                img_pil = Image.fromarray(img_rgb).resize((new_w, new_h), Image.Resampling.LANCZOS)
            except AttributeError:
                # Fallback for older PIL versions
                img_pil = Image.fromarray(img_rgb).resize((new_w, new_h))
            img_tk = ImageTk.PhotoImage(img_pil)
            self.canvas.delete("all")
            self.canvas.create_image(self._img_offset[0], self._img_offset[1], image=img_tk, anchor="nw")
            self.canvas.image = img_tk
        self.draw_rois()

    def draw_rois(self):
        """Draw ROI rectangles on the canvas."""
        if not hasattr(self, '_img_scale'):
            return
        scale = self._img_scale
        offset_x, offset_y = self._img_offset
        for rect in self.rectangles:
            self.canvas.delete(rect)
        self.rectangles = []
        for roi in self.rois:
            if roi is not None and isinstance(roi, tuple):
                # Unpack with feature_method and rotation
                if len(roi) >= 8:
                    roi_idx, roi_type, coords, focus, exposure_time, ai_threshold, feature_method, rotation = roi[:8]
                elif len(roi) == 7:
                    roi_idx, roi_type, coords, focus, exposure_time, ai_threshold, feature_method = roi
                    rotation = 0
                elif len(roi) == 6:
                    roi_idx, roi_type, coords, focus, exposure_time, ai_threshold = roi
                    feature_method = "mobilenet" if roi_type == 2 else "opencv"
                    rotation = 0
                elif len(roi) == 5:
                    roi_idx, roi_type, coords, focus, exposure_time = roi
                    ai_threshold = 0.9
                    feature_method = "opencv"
                    rotation = 0
                else:
                    continue
                x1, y1, x2, y2 = coords
                # Draw rectangle for ROI
                outline_color = "blue" if roi_type == 2 and feature_method == "mobilenet" else "orange" if roi_type == 2 and feature_method == "opencv" else "magenta" if roi_type == 3 else "brown"
                rect = self.canvas.create_rectangle(
                    int(x1*scale+offset_x), int(y1*scale+offset_y),
                    int(x2*scale+offset_x), int(y2*scale+offset_y),
                    outline=outline_color, width=2
                )
                self.rectangles.append(rect)
                
                # Draw ROI index label next to the rectangle
                label_x = int(x1*scale+offset_x) + 5
                label_y = int(y1*scale+offset_y) - 5
                # Ensure label stays within canvas bounds
                if label_y < 15:
                    label_y = int(y1*scale+offset_y) + 15
                
                text_label = self.canvas.create_text(
                    label_x, label_y,
                    text=str(roi_idx),
                    fill=outline_color,
                    font=("SF Pro Display", 12, "bold"),
                    anchor="nw"
                )
                self.rectangles.append(text_label)

    def save_rois_to_file(self):
        """Save ROIs to configuration file."""
        if hasattr(self, 'save_callback') and callable(self.save_callback):
            self.save_callback(self.rois.copy())
        from .inspection import ui_instance
        if ui_instance:
            ui_instance.set_status("ROIs saved to config file.")

    def on_mousewheel(self, event):
        """Handle mouse wheel events for zooming"""
        # Get the position of the mouse relative to the canvas
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:  # Zoom in
            new_zoom = min(self.zoom_factor + self.zoom_step, self.max_zoom)
        else:  # Zoom out
            new_zoom = max(self.zoom_factor - self.zoom_step, self.min_zoom)
        
        if new_zoom != self.zoom_factor:
            # Calculate zoom center point in image coordinates
            zoom_center_x = (canvas_x - self._img_offset[0]) / self.zoom_factor
            zoom_center_y = (canvas_y - self._img_offset[1]) / self.zoom_factor
            
            # Update zoom factor
            self.zoom_factor = new_zoom
            
            # Adjust offset to keep zoom centered on mouse position
            new_offset_x = canvas_x - zoom_center_x * self.zoom_factor
            new_offset_y = canvas_y - zoom_center_y * self.zoom_factor
            self._img_offset = (new_offset_x, new_offset_y)
            
            self.update_zoom_display()
            self.draw_image()

    def on_pan_start(self, event):
        """Start panning with middle mouse button"""
        self.last_pan_x = event.x
        self.last_pan_y = event.y
        self.panning = True

    def on_pan_drag(self, event):
        """Handle pan dragging"""
        if self.panning:
            dx = event.x - self.last_pan_x
            dy = event.y - self.last_pan_y
            
            # Update image offset
            self._img_offset = (self._img_offset[0] + dx, self._img_offset[1] + dy)
            
            self.last_pan_x = event.x
            self.last_pan_y = event.y
            self.draw_image()

    def on_pan_end(self, event):
        """End panning"""
        self.panning = False

    def on_key_press(self, event):
        """Handle keyboard events for zoom and pan shortcuts"""
        if event.keysym == "plus" or event.keysym == "equal":
            self.zoom_in()
        elif event.keysym == "minus":
            self.zoom_out()
        elif event.keysym == "0":
            self.zoom_reset()
    
    def zoom_in(self):
        """Zoom in on the image"""
        new_zoom = min(self.zoom_factor + self.zoom_step, self.max_zoom)
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self.update_zoom_display()
            self.draw_image()
    
    def zoom_out(self):
        """Zoom out on the image"""
        new_zoom = max(self.zoom_factor - self.zoom_step, self.min_zoom)
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self.update_zoom_display()
            self.draw_image()
    
    def zoom_reset(self):
        """Reset zoom to 1.0x"""
        if self.zoom_factor != 1.0:
            self.zoom_factor = 1.0
            self.update_zoom_display()
            self.draw_image()
    
    def update_zoom_display(self):
        """Update the zoom level display"""
        if hasattr(self, 'zoom_label'):
            self.zoom_label.config(text=f"Zoom: {self.zoom_factor:.1f}x")

    def delete_roi(self, idx):
        """Delete a ROI by index."""
        if 0 <= idx < len(self.rois):       
            del self.rois[idx]
            if hasattr(self, 'save_callback') and callable(self.save_callback):
                self.save_callback(self.rois.copy())
            self.draw_image()

    def on_right_click(self, event):
        """Handle right-click events for ROI editing/deletion."""
        # Map event to image coordinates
        x, y = self._event_to_image_coords(event)
        # Find ROI containing this point
        for idx, roi in enumerate(self.rois):
            if roi is None or not isinstance(roi, tuple):
                continue
            # Robust unpacking for all valid ROI tuple lengths
            if len(roi) >= 9:
                _, roi_type, (x1, y1, x2, y2), focus, exposure_time, ai_threshold, feature_method, rotation, device_location = roi
            elif len(roi) == 8:
                _, roi_type, (x1, y1, x2, y2), focus, exposure_time, ai_threshold, feature_method, rotation = roi
                device_location = 1  # Default device location
            elif len(roi) == 7:
                _, roi_type, (x1, y1, x2, y2), focus, exposure_time, ai_threshold, feature_method = roi
                device_location = 1  # Default device location
            elif len(roi) == 6:
                _, roi_type, (x1, y1, x2, y2), focus, exposure_time = roi
                ai_threshold = 0.9
                feature_method = "mobilenet" if roi_type == 2 else "opencv"
                device_location = 1  # Default device location
            elif len(roi) == 5:
                _, roi_type, (x1, y1, x2, y2), focus, exposure_time = roi
                ai_threshold = 0.9
                feature_method = "mobilenet" if roi_type == 2 else "opencv"
                device_location = 1  # Default device location
            elif len(roi) == 4:
                _, roi_type, (x1, y1, x2, y2), focus = roi
                ai_threshold = 0.9
                exposure_time = 3000
                feature_method = "mobilenet" if roi_type == 2 else "opencv"
                device_location = 1  # Default device location
            else:
                continue
            if x1 <= x <= x2 and y1 <= y <= y2:
                # Show context menu for edit/delete
                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label="Edit Attributes", command=lambda idx=idx: self.show_edit_roi_dialog(idx))
                menu.add_command(label="Delete ROI", command=lambda idx=idx: self.delete_roi(idx))
                menu.tk_popup(event.x_root, event.y_root)
                break

    def on_press(self, event):
        """Handle mouse press events for starting ROI drawing."""
        # Convert canvas event to image coordinates for starting point
        x_img, y_img = self._event_to_image_coords(event)
        self.temp_rect_img = (x_img, y_img, x_img, y_img)
        self.draw_temp_rectangle()

    def on_drag(self, event):
        """Handle mouse drag events for ROI drawing."""
        # Update temp_rect_img with new image coordinates
        if not hasattr(self, 'temp_rect_img') or self.temp_rect_img is None:
            return
        x1, y1, _, _ = self.temp_rect_img
        x2, y2 = self._event_to_image_coords(event)
        self.temp_rect_img = (x1, y1, x2, y2)
        self.draw_temp_rectangle()

    def draw_temp_rectangle(self):
        """Draw temporary rectangle during ROI creation."""
        self.draw_image()
        if hasattr(self, 'temp_rect_img') and self.temp_rect_img:
            scale = getattr(self, '_img_scale', 1.0)
            offset_x, offset_y = getattr(self, '_img_offset', (0, 0))
            x1, y1, x2, y2 = self.temp_rect_img
            sx1, sy1, sx2, sy2 = [v * scale for v in (x1, y1, x2, y2)]
            sx1 += offset_x
            sx2 += offset_x
            sy1 += offset_y
            sy2 += offset_y
            rect = self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline="red", width=2)
            self.rectangles.append(rect)

    def on_release(self, event):
        """Handle mouse release events for completing ROI creation."""
        from .config import default_focus, default_exposure
        # Use temp_rect_img (image coordinates) for ROI creation
        if hasattr(self, 'temp_rect_img') and self.temp_rect_img:
            x1, y1, x2, y2 = self.temp_rect_img
            img_h, img_w = self.image.shape[:2]
            ix1 = max(0, min(int(round(x1)), img_w - 1))
            ix2 = max(0, min(int(round(x2)), img_w - 1))
            iy1 = max(0, min(int(round(y1)), img_h - 1))
            iy2 = max(0, min(int(round(y2)), img_h - 1))
            # Always sort coordinates so x1 < x2 and y1 < y2
            x1f, x2f = sorted([ix1, ix2])
            y1f, y2f = sorted([iy1, iy2])
            if x1f != x2f and y1f != y2f:
                self.show_new_roi_dialog(x1f, y1f, x2f, y2f)
            self.temp_rect_img = None
            self.draw_image()

    def show_new_roi_dialog(self, x1, y1, x2, y2):
        """Show dialog for creating new ROI."""
        from .config import DEFAULT_FOCUS, DEFAULT_EXPOSURE
        
        # Get default values from first ROI if it exists, otherwise use config defaults
        default_focus = DEFAULT_FOCUS
        default_exposure = DEFAULT_EXPOSURE
        default_ai_threshold = 0.9
        default_feature_method = "mobilenet"
        
        if hasattr(self, 'rois') and self.rois and len(self.rois) > 0:
            first_roi = self.rois[0]
            if first_roi is not None and len(first_roi) >= 5:
                default_focus = first_roi[3]
                default_exposure = first_roi[4]
            if first_roi is not None and len(first_roi) >= 6 and first_roi[5] is not None:
                default_ai_threshold = first_roi[5]
            if first_roi is not None and len(first_roi) >= 7 and first_roi[6] is not None:
                default_feature_method = first_roi[6]
        
        popup = tk.Toplevel(self.master if hasattr(self, 'master') else None)
        popup.title("New ROI Attributes")
        popup.geometry("480x630")
        popup.configure(bg=get_current_theme()['bg'])
        
        # Apply dark theme to the popup
        apply_ios_theme(popup)
        
        tk.Label(popup, text="ROI Type:", bg=get_current_theme()['bg'], fg=get_current_theme()['fg'], 
                font=("SF Pro Display", 11, "bold")).pack(pady=8)
        roi_type_var = tk.IntVar(value=2)
        type_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        type_frame.pack(pady=4)
        
        for value, text in [(1, "Barcode"), (2, "Compare"), (3, "OCR")]:
            tk.Radiobutton(type_frame, text=text, variable=roi_type_var, value=value,
                          bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                          activebackground=get_current_theme()['bg'], activeforeground=get_current_theme()['fg'],
                          selectcolor=get_current_theme()['surface'], font=("SF Pro Display", 10)).pack(side="left", padx=15)
        
        tk.Label(popup, text="Focus (0-1023):", bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                font=("SF Pro Display", 11)).pack(pady=(15,5))
        focus_entry = tk.Entry(popup, bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                              insertbackground=get_current_theme()['fg'], font=("SF Pro Display", 10))
        focus_entry.insert(0, str(default_focus)) 
        focus_entry.pack(pady=2)
        
        tk.Label(popup, text="Exposure Time (us):", bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                font=("SF Pro Display", 11)).pack(pady=(10,5))
        exposure_entry = tk.Entry(popup, bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                                 insertbackground=get_current_theme()['fg'], font=("SF Pro Display", 10))
        exposure_entry.insert(0, str(default_exposure))
        exposure_entry.pack(pady=2)
        
        # Device Location field
        tk.Label(popup, text="Device Location (1-4):", bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                font=("SF Pro Display", 11)).pack(pady=(10,5))
        device_location_var = tk.IntVar(value=1)  # Default to device 1
        device_location_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        device_location_frame.pack(pady=2)
        for i in range(1, 5):
            tk.Radiobutton(device_location_frame, text=f"Device {i}", variable=device_location_var, value=i,
                          bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                          activebackground=get_current_theme()['bg'], activeforeground=get_current_theme()['fg'],
                          selectcolor=get_current_theme()['surface'], font=("SF Pro Display", 10)).pack(side="left", padx=5)
        
        rotation_label = tk.Label(popup, text="Rotation (deg, e.g. 0/90/180/270):",
                                 bg=get_current_theme()['bg'], fg=get_current_theme()['fg'], font=("SF Pro Display", 11))
        rotation_entry = tk.Entry(popup, bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                                 insertbackground=get_current_theme()['fg'], font=("SF Pro Display", 10))
        rotation_entry.insert(0, "0")
        
        # Compare ROI only: threshold and feature method
        ai_threshold_label = tk.Label(popup, text="Compare Threshold (0.5-1.0):",
                                     bg=get_current_theme()['bg'], fg=get_current_theme()['fg'], font=("SF Pro Display", 11))
        ai_threshold_var = tk.DoubleVar(value=default_ai_threshold)
        ai_threshold_entry = tk.Entry(popup, textvariable=ai_threshold_var,
                                     bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                                     insertbackground=get_current_theme()['fg'], font=("SF Pro Display", 10))
        
        feature_method_label = tk.Label(popup, text="Feature Method:",
                                       bg=get_current_theme()['bg'], fg=get_current_theme()['fg'], font=("SF Pro Display", 11))
        feature_method_var = tk.StringVar(value=default_feature_method)
        feature_method_menu = ttk.Combobox(popup, textvariable=feature_method_var, 
                                          values=["mobilenet", "opencv"], state="readonly",
                                          font=("SF Pro Display", 10))
        
        def update_compare_fields(*args):
            if roi_type_var.get() == 2:
                ai_threshold_label.pack(pady=(10,5))
                ai_threshold_entry.pack(pady=2)
                feature_method_label.pack(pady=(10,5))
                feature_method_menu.pack(pady=2)
                rotation_label.pack_forget()
                rotation_entry.pack_forget()
            elif roi_type_var.get() == 3:
                ai_threshold_label.pack_forget()
                ai_threshold_entry.pack_forget()
                feature_method_label.pack_forget()
                feature_method_menu.pack_forget()
                rotation_label.pack(pady=(10,5))
                rotation_entry.pack(pady=2)
            else:
                ai_threshold_label.pack_forget()
                ai_threshold_entry.pack_forget()
                feature_method_label.pack_forget()
                feature_method_menu.pack_forget()
                rotation_label.pack_forget()
                rotation_entry.pack_forget()
        
        roi_type_var.trace_add('write', update_compare_fields)
        update_compare_fields()
        
        def on_ok():
            try:
                roi_type = roi_type_var.get()
                focus = int(focus_entry.get())
                exposure_time = int(exposure_entry.get())
                device_location = device_location_var.get()
                
                if focus < 0 or focus > 1023:
                    raise ValueError("Focus must be between 0 and 1023.")
                if exposure_time < 100 or exposure_time > 1000000:
                    raise ValueError("Exposure time must be between 100 and 1000000 us.")
                if device_location < 1 or device_location > 4:
                    raise ValueError("Device location must be between 1 and 4.")
                
                roi_idx = get_next_roi_index()
                if roi_type == 2:
                    ai_threshold = float(ai_threshold_entry.get())
                    if ai_threshold < 0.5 or ai_threshold > 1.0:
                        raise ValueError("AI Threshold must be between 0.5 and 1.0.")
                    feature_method = feature_method_var.get()
                    self.rois.append((roi_idx, 2, (x1, y1, x2, y2), focus, exposure_time, ai_threshold, feature_method, 0, device_location))
                elif roi_type == 3:
                    rotation = int(rotation_entry.get())
                    self.rois.append((roi_idx, 3, (x1, y1, x2, y2), focus, exposure_time, None, "ocr", rotation, device_location))
                else:
                    self.rois.append((roi_idx, 1, (x1, y1, x2, y2), focus, exposure_time, None, "opencv", 0, device_location))
                
                if hasattr(self, 'save_callback') and callable(self.save_callback):
                    self.save_callback(self.rois.copy())
                
                popup.destroy()
                self.draw_image()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=popup)
        
        def on_cancel():
            popup.destroy()
        
        btn_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        btn_frame.pack(pady=20)
        
        ok_btn = tk.Button(btn_frame, text="OK", command=on_ok, width=10,
                          bg=get_current_theme()['success'], fg="white", 
                          activebackground=get_current_theme()['button_active'],
                          font=("SF Pro Display", 11, "bold"), relief='flat')
        ok_btn.pack(side="left", padx=10)
        add_button_hover_effect(ok_btn, "success")
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10,
                              bg=get_current_theme()['button_bg'], fg=get_current_theme()['button_fg'],
                              activebackground=get_current_theme()['button_active'],
                              font=("SF Pro Display", 11), relief='flat')
        cancel_btn.pack(side="left", padx=10)
        add_button_hover_effect(cancel_btn, "secondary")
        
        popup.transient(self.winfo_toplevel())
        def on_popup_visible(event):
            popup.grab_set()
        popup.bind("<Visibility>", on_popup_visible)
        popup.wait_window()

    def show_edit_roi_dialog(self, idx):
        """Show dialog for editing existing ROI."""
        if not (0 <= idx < len(self.rois)):
            return
        
        roi = self.rois[idx]
        if roi is None or not isinstance(roi, tuple):
            return
        
        # Unpack current ROI values
        roi_idx = roi[0]
        roi_type = roi[1]
        coords = roi[2]
        focus = roi[3] if len(roi) >= 4 else 305
        exposure_time = roi[4] if len(roi) >= 5 else 3000
        ai_threshold = roi[5] if len(roi) >= 6 and roi[5] is not None else 0.9
        feature_method = roi[6] if len(roi) >= 7 and roi[6] is not None else "mobilenet"
        rotation = roi[7] if len(roi) >= 8 else 0
        device_location = roi[8] if len(roi) >= 9 else 1
        
        popup = tk.Toplevel(self.master if hasattr(self, 'master') else None)
        popup.title(f"Edit ROI {roi_idx} Attributes")
        popup.geometry("450x650")
        popup.configure(bg=get_current_theme()['bg'])
        
        # Apply theme to the popup
        apply_theme(popup)
        
        # ROI Index (read-only)
        tk.Label(popup, text=f"ROI Index: {roi_idx}", font=("SF Pro Display", 12, "bold"),
                bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(pady=5)
        
        # Coordinates (read-only)
        tk.Label(popup, text=f"Coordinates: ({coords[0]}, {coords[1]}, {coords[2]}, {coords[3]})",
                bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(pady=2)
        
        tk.Label(popup, text="ROI Type:", bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(pady=5)
        roi_type_var = tk.IntVar(value=roi_type)
        type_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        type_frame.pack(pady=2)
        tk.Radiobutton(type_frame, text="Barcode", variable=roi_type_var, value=1,
                      bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                      selectcolor=get_current_theme()['surface']).pack(side="left", padx=10)
        tk.Radiobutton(type_frame, text="Compare", variable=roi_type_var, value=2,
                      bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                      selectcolor=get_current_theme()['surface']).pack(side="left", padx=10)
        tk.Radiobutton(type_frame, text="OCR", variable=roi_type_var, value=3,
                      bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                      selectcolor=get_current_theme()['surface']).pack(side="left", padx=10)
        
        tk.Label(popup, text="Focus (0-1023):", bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(pady=5)
        focus_entry = tk.Entry(popup, bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                              insertbackground=get_current_theme()['fg'])
        focus_entry.insert(0, str(focus))
        focus_entry.pack(pady=2)
        
        tk.Label(popup, text="Exposure Time (us):", bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(pady=5)
        exposure_entry = tk.Entry(popup, bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                                 insertbackground=get_current_theme()['fg'])
        exposure_entry.insert(0, str(exposure_time))
        exposure_entry.pack(pady=2)
        
        # Device Location field
        tk.Label(popup, text="Device Location (1-4):", bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(pady=5)
        device_location_var = tk.IntVar(value=device_location)
        device_location_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        device_location_frame.pack(pady=2)
        for i in range(1, 5):
            tk.Radiobutton(device_location_frame, text=f"Device {i}", variable=device_location_var, value=i,
                          bg=get_current_theme()['bg'], fg=get_current_theme()['fg'],
                          selectcolor=get_current_theme()['surface']).pack(side="left", padx=5)
        
        # Rotation field (for OCR ROIs)
        rotation_label = tk.Label(popup, text="Rotation (deg, e.g. 0/90/180/270):",
                                 bg=get_current_theme()['bg'], fg=get_current_theme()['fg'])
        rotation_entry = tk.Entry(popup, bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                                 insertbackground=get_current_theme()['fg'])
        rotation_entry.insert(0, str(rotation))
        
        # Compare ROI only: threshold and feature method
        ai_threshold_label = tk.Label(popup, text="Compare Threshold (0.5-1.0):",
                                     bg=get_current_theme()['bg'], fg=get_current_theme()['fg'])
        ai_threshold_var = tk.DoubleVar(value=ai_threshold)
        ai_threshold_entry = tk.Entry(popup, textvariable=ai_threshold_var,
                                     bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'],
                                     insertbackground=get_current_theme()['fg'])
        
        feature_method_label = tk.Label(popup, text="Feature Method:",
                                       bg=get_current_theme()['bg'], fg=get_current_theme()['fg'])
        feature_method_var = tk.StringVar(value=feature_method)
        feature_method_menu = ttk.Combobox(popup, textvariable=feature_method_var, values=["mobilenet", "opencv"], state="readonly")
        
        def update_fields(*args):
            current_type = roi_type_var.get()
            # Hide all optional fields first
            ai_threshold_label.pack_forget()
            ai_threshold_entry.pack_forget()
            feature_method_label.pack_forget()
            feature_method_menu.pack_forget()
            rotation_label.pack_forget()
            rotation_entry.pack_forget()
            
            if current_type == 2:  # Compare ROI
                ai_threshold_label.pack(pady=5)
                ai_threshold_entry.pack(pady=2)
                feature_method_label.pack(pady=5)
                feature_method_menu.pack(pady=2)
            elif current_type == 3:  # OCR ROI
                rotation_label.pack(pady=5)
                rotation_entry.pack(pady=2)
        
        roi_type_var.trace_add('write', update_fields)
        update_fields()
        
        # Separator
        separator = ttk.Separator(popup, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # Current values display (read-only info)
        info_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        info_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(info_frame, text="Current Configuration:", font=("SF Pro Display", 10, "bold"),
                bg=get_current_theme()['bg'], fg=get_current_theme()['fg']).pack(anchor="w")
        
        info_text = tk.Text(info_frame, height=6, width=50,
                           bg=get_current_theme()['input_bg'], fg=get_current_theme()['input_fg'])
        info_text.pack(fill="x", pady=5)
        
        # Populate info text
        info_content = f"""ROI Index: {roi_idx}
ROI Type: {'Barcode' if roi_type == 1 else 'Compare' if roi_type == 2 else 'OCR'}
Coordinates: ({coords[0]}, {coords[1]}, {coords[2]}, {coords[3]})
Focus: {focus}
Exposure Time: {exposure_time} us
Device Location: {device_location}"""
        
        if roi_type == 2:
            info_content += f"\nAI Threshold: {ai_threshold}\nFeature Method: {feature_method}"
        elif roi_type == 3:
            info_content += f"\nRotation: {rotation}°"
            
        info_text.insert("1.0", info_content)
        info_text.config(state="disabled")
        
        def on_ok():
            try:
                new_roi_type = roi_type_var.get()
                new_focus = int(focus_entry.get())
                new_exposure_time = int(exposure_entry.get())
                new_device_location = device_location_var.get()
                
                if new_focus < 0 or new_focus > 1023:
                    raise ValueError("Focus must be between 0 and 1023.")
                if new_exposure_time < 100 or new_exposure_time > 1000000:
                    raise ValueError("Exposure time must be between 100 and 1000000 us.")
                if new_device_location < 1 or new_device_location > 4:
                    raise ValueError("Device location must be between 1 and 4.")
                
                # Build updated ROI tuple
                if new_roi_type == 2:  # Compare ROI
                    new_ai_threshold = float(ai_threshold_entry.get())
                    if new_ai_threshold < 0.5 or new_ai_threshold > 1.0:
                        raise ValueError("AI Threshold must be between 0.5 and 1.0.")
                    new_feature_method = feature_method_var.get()
                    updated_roi = (roi_idx, 2, coords, new_focus, new_exposure_time, new_ai_threshold, new_feature_method, 0, new_device_location)
                elif new_roi_type == 3:  # OCR ROI
                    new_rotation = int(rotation_entry.get())
                    updated_roi = (roi_idx, 3, coords, new_focus, new_exposure_time, None, "ocr", new_rotation, new_device_location)
                else:  # Barcode ROI
                    updated_roi = (roi_idx, 1, coords, new_focus, new_exposure_time, None, "opencv", 0, new_device_location)
                
                # Update the ROI in the list
                self.rois[idx] = updated_roi
                
                if hasattr(self, 'save_callback') and callable(self.save_callback):
                    self.save_callback(self.rois.copy())
                
                popup.destroy()
                self.draw_image()
                
                from .inspection import ui_instance
                if ui_instance:
                    ui_instance.set_status(f"ROI {roi_idx} updated successfully.")
                    
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=popup)
        
        def on_cancel():
            popup.destroy()
        
        btn_frame = tk.Frame(popup, bg=get_current_theme()['bg'])
        btn_frame.pack(pady=15)
        save_changes_btn = tk.Button(btn_frame, text="Save Changes", command=on_ok, width=12,
                 bg=get_current_theme()['success'], fg="white",
                 activebackground=get_current_theme()['button_active'],
                 font=("SF Pro Display", 11, "bold"), relief='flat')
        save_changes_btn.pack(side="left", padx=10)
        add_button_hover_effect(save_changes_btn, "success")
        
        cancel_edit_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=12,
                 bg=get_current_theme()['button_bg'], fg=get_current_theme()['button_fg'],
                 activebackground=get_current_theme()['button_active'],
                 font=("SF Pro Display", 11), relief='flat')
        cancel_edit_btn.pack(side="left", padx=10)
        add_button_hover_effect(cancel_edit_btn, "secondary")
        
        popup.transient(self.winfo_toplevel())
        def on_popup_visible(event):
            popup.grab_set()
        popup.bind("<Visibility>", on_popup_visible)
        popup.wait_window()

    def _event_to_image_coords(self, event):
        """Map canvas event coordinates to image coordinates."""
        if not hasattr(self, '_img_scale') or not hasattr(self, '_img_offset'):
            return (0, 0)
        scale = self._img_scale
        offset_x, offset_y = self._img_offset
        # Canvas coordinates
        cx, cy = event.x, event.y
        # Remove offset, then scale
        ix = int(round((cx - offset_x) / scale))
        iy = int(round((cy - offset_y) / scale))
        # Clamp to image bounds
        img_h, img_w = self.image.shape[:2]
        ix = max(0, min(ix, img_w - 1))
        iy = max(0, min(iy, img_h - 1))
        return (ix, iy)


class ImageCompareUI:
    """Main UI class for the Visual AOI system."""
    
    def __init__(self, root):
        self.root = root
        self.last_img = None
        self.timer_start_time = time.time()
        self.timer_running = False
        self._timer_after_id = None
        self.roi_editor = None
        self.current_roi_idx = None
        self.selected_center_idx = None
        
        # Flow UI state
        self.flow_steps = []
        self.current_flow_step = 0
        self.flow_canvas = None
        self.flow_active = False
        self.system_initialized = False  # Track if system initialization is complete
        
        # Thumbnail display variables (fixed size, no zoom)
        self.thumbnail_base_width = 400
        self.thumbnail_base_height = 300
        
        # Load theme preference and set theme
        theme_preference = load_theme_preference()
        set_theme(theme_preference)
        
        # Configure theme
        configure_ttk_theme()
        
        # Initialize UI
        self.init_ui()
        
        # Apply theme to the entire interface
        apply_theme(self.root, is_root=True)

    def create_glass_button(self, parent, text="Button", command=None, style="primary", **kwargs):
        """Create a button with liquid glass effect and hover animations."""
        button = tk.Button(parent, text=text, command=command, **kwargs)
        
        # Get theme for color setup
        theme = get_current_theme()
        
        # Determine colors based on style BEFORE applying glass effect
        if style == "primary":
            original_bg = theme.get('glass_bg', theme['primary'])
            hover_bg = theme.get('glass_highlight', theme['primary_light'])
        else:
            original_bg = theme.get('glass_surface', theme['button_secondary'])
            hover_bg = theme.get('glass_surface_hover', theme.get('glass_surface', theme['button_secondary']))
        
        # Apply glass styling based on style
        glass_type = "primary" if style == "primary" else "button"
        apply_glass_effect(button, glass_type)
        
        # Override the background color from apply_glass_effect with our intended color
        button.config(bg=original_bg)
        
        # Add hover effects for enhanced glass appearance
        def on_enter(event):
            # Enhance glass effect on hover
            button.config(bg=hover_bg)
        
        def on_leave(event):
            # Return to original glass effect
            button.config(bg=original_bg)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button

    def add_hover_effect(self, button, style="secondary"):
        """Add hover effect to an existing button."""
        add_button_hover_effect(button, style)

    def init_ui(self):
        """Initialize the main UI components."""
        # Maximize main window
        try:
            self.root.attributes('-zoomed', True)
        except Exception:
            self.root.state('zoomed')
        
        # Use ttk.Notebook for tabbed UI
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Inspection tab (main UI)
        self.inspection_frame = tk.Frame(self.notebook)
        self.notebook.add(self.inspection_frame, text="Inspection")
        
        # ROI Editor tab
        self.roi_editor_frame = tk.Frame(self.notebook)
        self.notebook.add(self.roi_editor_frame, text="Edit ROIs")
        
        # Create menu bar
        menubar = tk.Menu(self.root)
        
        # ROIs menu
        roi_menu = tk.Menu(menubar, tearoff=0)
        roi_menu.add_command(label="Edit ROIs", command=self.open_edit_rois_tab)
        menubar.add_cascade(label="ROIs", menu=roi_menu)
        
        # View menu with theme options
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Light Mode", command=lambda: self.switch_theme("light"))
        view_menu.add_command(label="Dark Mode", command=lambda: self.switch_theme("dark"))
        menubar.add_cascade(label="View", menu=view_menu)
        
        menubar.add_command(label="Exit", command=self.root.destroy)
        self.root.config(menu=menubar)
        
        # Initialize inspection UI components
        self.init_inspection_ui()
        
        # Initialize ROI editor
        self.init_roi_editor_tab()

    def init_inspection_ui(self):
        """Initialize the inspection tab UI."""
        # Main horizontal split: left for ROI list, center for thumbnail, right for overall result
        main_pane = tk.PanedWindow(self.inspection_frame, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, 
                                 bg=get_current_theme()['bg'], sashwidth=3)
        main_pane.pack(fill="both", expand=True)
        
        # Left: ROI result list (scrollable frame) with glass effect
        left_frame = create_glass_frame(main_pane, "panel", width=240, relief='flat', borderwidth=1)
        
        # ROI list header
        roi_header = tk.Label(left_frame, text="ROI RESULTS", 
                             font=('SF Pro Display', 20, 'bold'),
                             bg=get_current_theme()['surface'], fg=get_current_theme()['fg'], pady=16)
        roi_header.pack(fill="x")
        
        self.roi_canvas = tk.Canvas(left_frame, width=240, bg=get_current_theme()['surface'], 
                                   highlightthickness=0, borderwidth=0)
        self.roi_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=self.roi_canvas.yview,
                                         bg=get_current_theme()['scrollbar_bg'], troughcolor=get_current_theme()['bg'],
                                         activebackground=get_current_theme()['scrollbar_fg'])
        self.roi_frame = tk.Frame(self.roi_canvas, bg=get_current_theme()['surface'])
        self.roi_frame.bind(
            "<Configure>",
            lambda e: self.roi_canvas.configure(scrollregion=self.roi_canvas.bbox("all"))
        )
        self.roi_canvas.create_window((0, 0), window=self.roi_frame, anchor="nw")
        self.roi_canvas.configure(yscrollcommand=self.roi_scrollbar.set)
        self.roi_canvas.pack(side="left", fill="both", expand=True)
        self.roi_scrollbar.pack(side="right", fill="y")
        main_pane.add(left_frame, minsize=220, width=240)

        # Center: Flow UI or ROI detail display with glass effect
        center_frame = create_glass_frame(main_pane, "panel", width=480, relief='flat', borderwidth=1)
        
        # Center header - changes based on mode
        self.center_header = tk.Label(center_frame, text="PROCESS FLOW", 
                                font=('SF Pro Display', 20, 'bold'),
                                bg=get_current_theme()['surface'], fg=get_current_theme()['fg'], pady=16)
        self.center_header.pack(fill="x")
        
        # Create thumbnail frame with conditional zoom controls
        thumb_container = tk.Frame(center_frame, bg=get_current_theme()['surface'])
        thumb_container.pack(fill="both", expand=True)
        
        self.center_thumb_frame = tk.Frame(thumb_container, bg=get_current_theme()['surface'])
        self.center_thumb_frame.pack(fill="both", expand=True)
        
        # Initialize flow UI in center panel
        self.flow_active = True  # Start with flow UI active
        self.init_flow_ui()
        
        main_pane.add(center_frame, minsize=400, width=480)

        # Right: Overall result display with glass effect
        right_frame = create_glass_frame(main_pane, "panel", width=240, relief='flat', borderwidth=1)
        
        # Overall result header
        result_header = tk.Label(right_frame, text="INSPECTION RESULT", 
                                font=('SF Pro Display', 20, 'bold'),
                                bg=get_current_theme()['surface'], fg=get_current_theme()['fg'], pady=16)
        result_header.pack(fill="x")
        
        self.overall_result_var = tk.StringVar(value="Result: N/A")
        self.overall_result_label = tk.Label(
            right_frame,
            textvariable=self.overall_result_var,
            font=("SF Pro Display", 32, "bold"),
            fg=get_current_theme()['fg'],
            bg=get_current_theme()['surface'],
            anchor="center",
            justify="center"
        )
        self.overall_result_label.pack(expand=True, fill="both", padx=20, pady=(20,10))
        
        # Add Starting Visual button with glass effect
        self.start_btn = self.create_glass_button(
            right_frame, 
            text="System Initializing...", 
            style="primary",
            font=('SF Pro Display', 20, 'bold'),
            state=tk.DISABLED,
            pady=16
        )
        self.start_btn.pack(pady=(0,20), padx=20, fill="x")
        
        self.timer_var = tk.StringVar()
        self.timer_label = tk.Label(right_frame, textvariable=self.timer_var, 
                                   font=('SF Pro Display', 17), 
                                   fg=get_current_theme()['info'], bg=get_current_theme()['surface'])
        self.timer_label.pack(pady=(0,20))
        self.timer_label.pack_forget()  # Hide initially
        
        # Add Show Overview button with glass styling
        self.show_overview_btn = self.create_glass_button(
            right_frame, text="Show Overview", 
            command=self.show_overview_window,
            style='secondary'
        )
        self.show_overview_btn.pack(pady=(0, 20), padx=20, fill="x")
        main_pane.add(right_frame, minsize=220, width=240)

        # Set pane weights for balanced layout
        main_pane.paneconfig(left_frame, stretch='always')
        main_pane.paneconfig(center_frame, stretch='always')
        main_pane.paneconfig(right_frame, stretch='always')

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.FLAT, anchor='w',
                                  bg=get_current_theme()['surface'], fg=get_current_theme()['fg'], font=("SF Pro Display", 10),
                                  pady=5, padx=10)
        self.status_bar.pack(fill="x", side="bottom")
        
        # Setup button/timer logic
        def start_and_enable():
            self.start_btn.config(state=tk.DISABLED, text="Start Visual Inspection")
            self.start_btn.pack_forget()
            self.timer_var.set("Operation time: 0.000s")
            self.timer_label.pack(pady=(0,20))
            self.timer_start_time = time.time()
            self.timer_running = True
            
            # Start flow UI - ensure System Ready is marked as complete before starting
            if hasattr(self, 'flow_steps') and len(self.flow_steps) > 0:
                self.flow_steps[0]["status"] = "complete"  # System Ready
            self.start_flow_ui()
            
            def update_timer():
                if self.timer_running:
                    elapsed = (time.time() - self.timer_start_time)
                    self.timer_var.set(f"Operation time: {elapsed:.3f}s")
                    self._timer_after_id = self.timer_label.after(100, update_timer)
            update_timer()
            
            def run_task():
                try:
                    from .inspection import capture_and_update
                    capture_and_update()
                finally:
                    pass  # Timer stop/hide is now handled after all ROI/UI updates
            threading.Thread(target=run_task).start()
        
        self.start_btn.config(command=start_and_enable)

    def init_roi_editor_tab(self):
        """Initialize the ROI editor tab."""
        focus = 305
        exposure_time = 3000
        rois = get_rois()
        if rois and len(rois) > 0 and rois[0] is not None and len(rois[0]) >= 4:
            focus = rois[0][3]
        if rois and len(rois) > 0 and rois[0] is not None and len(rois[0]) >= 5:
            exposure_time = rois[0][4]
            
        # Try to capture image from real camera for ROI editing
        img = capture_tis_image()
        if img is None:
            # Create a placeholder image when camera is not available
            # This allows the UI to start but camera is still required for actual operation
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(img, "Capture image for previewing", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            print("Warning: Using placeholder image - real camera required for operation")
        
        def save_rois(new_rois):
            set_rois(new_rois)
            from .config import get_product_name
            current_product = get_product_name()
            if current_product:
                save_rois_to_config(current_product)
        
        self.roi_editor = EditROIWindow(self.roi_editor_frame, img, rois, save_rois, as_tab=True)

    def open_edit_rois_tab(self):
        """Switch to the ROI editor tab."""
        self.notebook.select(self.roi_editor_frame)
        if self.roi_editor:
            self.roi_editor.draw_image()

    def refresh_roi_editor(self):
        """Refresh the ROI editor with current ROI configuration."""
        if hasattr(self, 'roi_editor') and self.roi_editor:
            # Reload ROIs in the editor
            rois = get_rois()
            self.roi_editor.rois = rois
            self.roi_editor.draw_rois()
            print(f"ROI editor refreshed with {len(rois)} ROIs")

    def init_flow_ui(self):
        """Initialize the flow UI components."""
        # Clear any existing content
        for widget in self.center_thumb_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame for flow canvas
        canvas_frame = tk.Frame(self.center_thumb_frame, bg=get_current_theme()['surface'])
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create flow canvas with scrollbars
        self.flow_canvas = tk.Canvas(
            canvas_frame, 
            bg=get_current_theme()['bg'], 
            highlightthickness=0,
            height=400
        )
        
        # Add scrollbars
        v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.flow_canvas.yview)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.flow_canvas.xview)
        self.flow_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.flow_canvas.pack(side="left", fill="both", expand=True)
        
        # Initialize flow steps with detailed hierarchical sub-nodes
        system_ready_status = "complete" if (hasattr(self, 'system_initialized') and self.system_initialized) else "pending"
        
        # Get current product name for display
        from .config import get_product_name
        current_product = get_product_name() or "Unknown"
        
        self.flow_steps = [
            {
                "name": "System Ready", 
                "status": system_ready_status, 
                "color": "#757575",
                "sub_nodes": [
                    {"name": "Initializing components", "status": system_ready_status},
                    {"name": f"Loading ROIs config from product: {current_product}", "status": system_ready_status},
                    {"name": "Camera initialization", "status": system_ready_status}
                ]
            },
            {
                "name": "Capture ROIs Images", 
                "status": "pending", 
                "color": "#757575",
                "sub_nodes": []  # Will be populated dynamically based on ROI groups
            },
            {
                "name": "Process ROIs", 
                "status": "pending", 
                "color": "#757575",
                "sub_nodes": []  # Will be populated dynamically based on actual ROIs
            },
            {
                "name": "Analysis Complete", 
                "status": "pending", 
                "color": "#757575",
                "sub_nodes": [
                    {"name": "Collect ROI Data", "status": "pending"},
                    {"name": "Determinate Final Result", "status": "pending"},
                    {"name": "Display Output", "status": "pending"}
                ]
            }
        ]
        
        # Populate dynamic sub-nodes based on current ROI configuration
        self.populate_dynamic_sub_nodes()
        
        self.draw_flow_ui()
    
    def populate_dynamic_sub_nodes(self):
        """Populate dynamic sub-nodes based on current ROI configuration."""
        from .roi import get_rois
        from .config import get_product_name
        
        # Get current product and ROIs
        current_product = get_product_name()
        rois = get_rois()
        
        # Populate System Ready sub-nodes with dynamic product info
        system_sub_nodes = [
            {"name": "Initializing components", "status": "completed"}
        ]
        
        if current_product:
            try:
                import json
                import os
                from .config import get_config_filename
                
                # Get the absolute path to the project root
                # This file is in src/ui.py, so project root is one level up from src
                current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
                project_root = os.path.dirname(current_file_dir)  # project root
                config_path = os.path.join(project_root, get_config_filename(current_product))
                
                print(f"DEBUG: UI trying to load config from: {config_path}")
                print(f"DEBUG: Config file exists: {os.path.exists(config_path)}")
                
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                        roi_count = len(rois)
                        system_sub_nodes.append({
                            "name": f"Found {roi_count} ROIs in configuration",
                            "status": "completed"
                        })
                        print(f"DEBUG: Successfully loaded {roi_count} ROIs from config")
                else:
                    print(f"DEBUG: Config file not found at: {config_path}")
                    system_sub_nodes.append({
                        "name": "ROI configuration file not found",
                        "status": "error"
                    })
            except Exception as e:
                print(f"DEBUG: Exception in UI config loading: {e}")
                import traceback
                traceback.print_exc()
        if rois and len(rois) > 0:
            system_sub_nodes.append({
                "name": f"Loaded {len(rois)} ROIs from current configuration",
                "status": "completed"
            })   
        self.flow_steps[0]["sub_nodes"] = system_sub_nodes
        
        # Populate Capture ROIs Images sub-nodes based on ROI groups
        capture_sub_nodes = []
        roi_groups = {}
        
        # Group ROIs by focus and exposure settings
        for roi in rois:
            if roi and len(roi) >= 5:
                roi_idx, roi_type, coords, focus, exposure_time = roi[:5]
                group_key = (focus, exposure_time)
                if group_key not in roi_groups:
                    roi_groups[group_key] = []
                roi_groups[group_key].append(roi_idx)
        
        # Create sub-nodes for each ROI group
        for i, ((focus, exposure), roi_indices) in enumerate(roi_groups.items(), 1):
            roi_list = ", ".join(map(str, roi_indices))
            capture_sub_nodes.append({
                "name": f"ROI group {i}: Focus: {focus} Exposure: {exposure}",
                "status": "pending",
                "detail": f"ROIs: {roi_list}"
            })
        
        # If no ROI groups, add default
        if not capture_sub_nodes:
            capture_sub_nodes.append({
                "name": "No ROI groups configured",
                "status": "pending"
            })
        
        self.flow_steps[1]["sub_nodes"] = capture_sub_nodes
        
        # Populate Process ROIs sub-nodes based on individual ROIs
        process_sub_nodes = []
        
        for roi in rois:
            if roi and len(roi) >= 2:
                roi_idx, roi_type = roi[:2]
                type_name = "Barcode" if roi_type == 1 else "Compare" if roi_type == 2 else "OCR"
                process_sub_nodes.append({
                    "name": f"ROI index {roi_idx}: ROI type: {type_name}",
                    "status": "pending"
                })
        
        # If no ROIs, add default
        if not process_sub_nodes:
            process_sub_nodes.append({
                "name": "No ROIs configured",
                "status": "pending"
            })
        
        self.flow_steps[2]["sub_nodes"] = process_sub_nodes
    
    def draw_flow_ui(self):
        """Draw the flow UI visualization with vertical hierarchical graph layout to prevent overlapping."""
        if not self.flow_canvas:
            return
            
        # Clear canvas
        self.flow_canvas.delete("all")
        
        # Get canvas dimensions
        self.flow_canvas.update_idletasks()
        canvas_width = self.flow_canvas.winfo_width()
        canvas_height = self.flow_canvas.winfo_height()
        
        if canvas_width < 50 or canvas_height < 50:
            # Canvas not ready yet
            self.flow_canvas.after(100, self.draw_flow_ui)
            return
        
        # Vertical layout parameters to prevent overlapping
        main_node_width = 200
        main_node_height = 50
        sub_node_width = 280
        sub_node_height = 25
        
        # Vertical hierarchical spacing to prevent overlap
        base_main_node_spacing_y = 80   # Base vertical space between main nodes
        sub_node_spacing_y = 30         # Vertical space between sub-nodes
        sub_node_offset_x = 50          # Horizontal offset for sub-nodes
        level_spacing_x = 60            # Horizontal space between main nodes and sub-nodes
        min_spacing_between_nodes = 20  # Minimum gap between main node groups
        
        # Calculate dynamic spacing for each main node based on its sub-nodes
        main_node_spacings = []
        main_node_heights = []
        
        for i, step in enumerate(self.flow_steps):
            sub_node_count = len(step.get("sub_nodes", []))
            
            # Calculate height needed for this main node including its sub-nodes
            if sub_node_count > 0:
                # Height of sub-nodes area
                sub_nodes_total_height = sub_node_count * sub_node_spacing_y
                # Space needed for this main node (max of main node height or sub-nodes height)
                node_group_height = max(main_node_height, sub_nodes_total_height)
            else:
                node_group_height = main_node_height
            
            main_node_heights.append(node_group_height)
            
            # Calculate spacing to next node (half of current node + half of next node + minimum gap)
            if i < len(self.flow_steps) - 1:
                next_step = self.flow_steps[i + 1]
                next_sub_node_count = len(next_step.get("sub_nodes", []))
                if next_sub_node_count > 0:
                    next_sub_nodes_height = next_sub_node_count * sub_node_spacing_y
                    next_node_group_height = max(main_node_height, next_sub_nodes_height)
                else:
                    next_node_group_height = main_node_height
                
                # Dynamic spacing: half current + half next + minimum gap + base spacing
                dynamic_spacing = (node_group_height // 2) + (next_node_group_height // 2) + min_spacing_between_nodes + base_main_node_spacing_y
            else:
                dynamic_spacing = base_main_node_spacing_y
            
            main_node_spacings.append(dynamic_spacing)
        
        # Calculate total height and positions
        total_main_height = sum(main_node_spacings)
        start_y = max(30, (canvas_height - total_main_height) // 2)
        main_level_x = 30
        
        # Store node positions for connection drawing
        node_positions = {}
        
        # Calculate maximum sub-nodes for proper canvas width
        max_sub_nodes = max(len(step.get("sub_nodes", [])) for step in self.flow_steps)
        required_width = main_level_x + main_node_width + level_spacing_x + sub_node_width + 50
        
        # Update canvas scroll region if needed
        self.flow_canvas.configure(scrollregion=(0, 0, max(canvas_width, required_width), max(canvas_height, total_main_height + 100)))
        
        # Calculate all main node positions first using dynamic spacing
        current_y = start_y
        for i, step in enumerate(self.flow_steps):
            x = main_level_x
            y = current_y
            
            # Store position for connections
            node_positions[f"main_{i}"] = (x + main_node_width // 2, y + main_node_height // 2)
            
            # Move to next position using dynamic spacing
            if i < len(main_node_spacings):
                current_y += main_node_spacings[i]
        
        # Draw the actual nodes after calculating all positions
        current_y = start_y
        for i, step in enumerate(self.flow_steps):
            x = main_level_x
            y = current_y
            
            # Enhanced color scheme based on status with better visual feedback
            if step["status"] == "complete":
                fill_color = get_current_theme()['success']      # Green for completed
                text_color = "white"
                border_color = "#2E7D32"                         # Darker green border
                shadow_color = "#4CAF50"                         # Lighter green shadow
            elif step["status"] == "active":
                fill_color = get_current_theme()['primary']      # Blue for active
                text_color = "white"
                border_color = "#1565C0"                         # Darker blue border
                shadow_color = "#42A5F5"                         # Lighter blue shadow
            elif step["status"] == "failed":
                fill_color = get_current_theme()['error']        # Red for failed
                text_color = "white"
                border_color = "#C62828"                         # Darker red border
                shadow_color = "#EF5350"                         # Lighter red shadow
            else:  # pending
                fill_color = get_current_theme()['glass_surface']
                text_color = get_current_theme()['secondary_fg']
                border_color = get_current_theme()['border']
                shadow_color = get_current_theme()['separator']
            
            # Draw shadow for depth effect
            self.draw_rounded_rect(x + 3, y + 3, main_node_width, main_node_height,
                                 fill=shadow_color, outline="", outline_width=0)
            
            # Draw main step with rounded rectangle
            self.draw_rounded_rect(x, y, main_node_width, main_node_height, 
                                 fill=fill_color, outline=border_color, outline_width=2)
            
            # Draw main step text with better formatting
            self.flow_canvas.create_text(
                x + main_node_width // 2, y + main_node_height // 2,
                text=step["name"], fill=text_color,
                font=('SF Pro Display', 12, 'bold'), 
                width=main_node_width - 20,
                justify='center'
            )
            
            # Draw sub-nodes in vertical hierarchical layout
            if "sub_nodes" in step and step["sub_nodes"]:
                sub_nodes = step["sub_nodes"]
                sub_start_x = x + main_node_width + level_spacing_x
                sub_start_y = y - ((len(sub_nodes) - 1) * sub_node_spacing_y // 2)  # Center sub-nodes vertically
                
                for j, sub_node in enumerate(sub_nodes):
                    sub_x = sub_start_x
                    sub_y = sub_start_y + j * sub_node_spacing_y
                    
                    # Store sub-node position
                    node_positions[f"sub_{i}_{j}"] = (sub_x + sub_node_width // 2, sub_y + sub_node_height // 2)
                    
                    # Enhanced sub-node colors with immediate visual feedback
                    if sub_node["status"] == "completed":
                        sub_fill = "#4CAF50"                     # Bright green for completed
                        sub_text_color = "white"
                        sub_border = "#2E7D32"                   # Dark green border
                        sub_shadow = "#81C784"                   # Light green shadow
                    elif sub_node["status"] == "active":
                        sub_fill = "#2196F3"                     # Bright blue for active
                        sub_text_color = "white"
                        sub_border = "#1565C0"                   # Dark blue border
                        sub_shadow = "#64B5F6"                   # Light blue shadow
                    elif sub_node["status"] == "error":
                        sub_fill = "#F44336"                     # Bright red for error
                        sub_text_color = "white"
                        sub_border = "#C62828"                   # Dark red border
                        sub_shadow = "#E57373"                   # Light red shadow
                    else:  # pending
                        sub_fill = get_current_theme()['glass_surface']
                        sub_text_color = get_current_theme()['tertiary_fg']
                        sub_border = get_current_theme()['border']
                        sub_shadow = get_current_theme()['separator']
                    
                    # Draw sub-node shadow for depth
                    self.draw_rounded_rect(sub_x + 2, sub_y + 2, sub_node_width, sub_node_height,
                                         fill=sub_shadow, outline="", outline_width=0)
                    
                    # Draw sub-node with smaller rounded rectangle
                    self.draw_rounded_rect(sub_x, sub_y, sub_node_width, sub_node_height,
                                         fill=sub_fill, outline=sub_border, outline_width=1)
                    
                    # Draw sub-node text (truncated if too long)
                    display_text = sub_node["name"]
                    if len(display_text) > 35:
                        display_text = display_text[:32] + "..."
                    
                    self.flow_canvas.create_text(
                        sub_x + sub_node_width // 2, sub_y + sub_node_height // 2,
                        text=display_text, fill=sub_text_color,
                        font=('SF Pro Display', 9), 
                        width=sub_node_width - 10,
                        justify='center'
                    )
                    
                    # Draw connection line from main step to sub-node
                    main_center_x, main_center_y = node_positions[f"main_{i}"]
                    sub_center_x, sub_center_y = node_positions[f"sub_{i}_{j}"]
                    
                    # Draw angled connection line with better styling
                    connection_color = border_color if step["status"] in ["complete", "active"] else get_current_theme()['tertiary_fg']
                    connection_width = 2 if step["status"] in ["complete", "active"] else 1
                    
                    # Horizontal line from main node to sub-node
                    self.flow_canvas.create_line(
                        x + main_node_width, main_center_y,      # Right edge of main node
                        sub_x, sub_center_y,                     # Left edge of sub-node
                        fill=connection_color, width=connection_width, capstyle='round'
                    )
                    
                    # Add connection dot at main node
                    self.flow_canvas.create_oval(
                        x + main_node_width - 3, main_center_y - 3,
                        x + main_node_width + 3, main_center_y + 3,
                        fill=connection_color, outline=""
                    )
            
            # Draw vertical flow connection line to next main step
            if i < len(self.flow_steps) - 1:
                current_center = node_positions[f"main_{i}"]
                next_center = node_positions[f"main_{i+1}"]
                
                # Enhanced line styling based on current step progress
                if step["status"] == "complete":
                    line_color = get_current_theme()['success']
                    line_width = 4
                    arrow_color = "#2E7D32"
                elif step["status"] == "active":
                    line_color = get_current_theme()['primary']
                    line_width = 3
                    arrow_color = "#1565C0"
                else:
                    line_color = get_current_theme()['separator']
                    line_width = 2
                    arrow_color = get_current_theme()['separator']
                
                # Draw vertical arrow between main nodes using dynamic positioning
                arrow_start_y = y + main_node_height + 5
                arrow_end_y = next_center[1] - main_node_height // 2 - 5
                arrow_x = current_center[0]
                
                self.flow_canvas.create_line(
                    arrow_x, arrow_start_y, arrow_x, arrow_end_y,
                    fill=line_color, width=line_width, capstyle='round',
                    arrow=tk.LAST, arrowshape=(12, 15, 4)
                )
                
                # Add progress indicator circle
                circle_y = arrow_start_y + (arrow_end_y - arrow_start_y) // 2
                circle_color = line_color if step["status"] == "complete" else get_current_theme()['glass_surface']
                self.flow_canvas.create_oval(
                    arrow_x - 6, circle_y - 6, arrow_x + 6, circle_y + 6,
                    fill=circle_color, outline=arrow_color, width=2
                )
            
            # Move to next position using dynamic spacing
            if i < len(main_node_spacings):
                current_y += main_node_spacings[i]
    
    def draw_rounded_rect(self, x, y, width, height, radius=8, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        if not self.flow_canvas:
            return
            
        # Extract outline_width if provided
        outline_width = kwargs.pop('outline_width', 1)
        
        # For simplicity, draw a rectangle with slightly rounded effect using overlapping shapes
        # Main rectangle
        rect = self.flow_canvas.create_rectangle(
            x + radius//2, y, x + width - radius//2, y + height, 
            **kwargs
        )
        
        # Top rounded parts
        self.flow_canvas.create_rectangle(
            x, y + radius//2, x + width, y + height - radius//2,
            outline="", fill=kwargs.get('fill', 'white')
        )
        
        # Overlay the border if specified
        if 'outline' in kwargs:
            self.flow_canvas.create_rectangle(
                x, y, x + width, y + height,
                fill="", outline=kwargs['outline'], width=outline_width
            )
    
    def update_flow_step(self, step_name, status, sub_node_name=None):
        """Update a flow step or sub-node status and redraw."""
        for step in self.flow_steps:
            if step["name"] == step_name:
                if sub_node_name:
                    # Update specific sub-node
                    for sub_node in step.get("sub_nodes", []):
                        if sub_node["name"] == sub_node_name:
                            sub_node["status"] = status
                            break
                else:
                    # Update main step
                    step["status"] = status
                break
        
        if self.flow_active:
            self.draw_flow_ui()
    
    def update_sub_node(self, step_name, sub_node_name, status):
        """Update a specific sub-node status."""
        self.update_flow_step(step_name, status, sub_node_name)
    
    def set_step_sub_nodes_status(self, step_name, status):
        """Set all sub-nodes of a step to the same status."""
        for step in self.flow_steps:
            if step["name"] == step_name:
                for sub_node in step.get("sub_nodes", []):
                    sub_node["status"] = status
                break
        
        if self.flow_active:
            self.draw_flow_ui()
    
    def start_flow_ui(self):
        """Start the flow UI and switch center panel to flow mode."""
        self.flow_active = True
        self.center_header.config(text="PROCESS FLOW")
        
        # Reset all steps and sub-nodes to pending except system ready (if system is actually ready)
        for i, step in enumerate(self.flow_steps):
            if i == 0:  # System Ready step
                # Keep as complete if system has been initialized
                if hasattr(self, 'system_initialized') and self.system_initialized:
                    step["status"] = "complete"
                    # Set all sub-nodes to complete
                    for sub_node in step.get("sub_nodes", []):
                        sub_node["status"] = "completed"
                elif hasattr(self, 'start_btn') and self.start_btn['state'] == 'normal':
                    step["status"] = "complete"
                    # Set all sub-nodes to complete
                    for sub_node in step.get("sub_nodes", []):
                        sub_node["status"] = "completed"
                else:
                    step["status"] = "pending"
                    # Set all sub-nodes to pending
                    for sub_node in step.get("sub_nodes", []):
                        sub_node["status"] = "pending"
            else:
                step["status"] = "pending"
                # Set all sub-nodes to pending
                for sub_node in step.get("sub_nodes", []):
                    sub_node["status"] = "pending"
        
        # Show flow UI
        self.init_flow_ui()
    
    def complete_flow_ui(self):
        """Complete the flow UI but keep it visible until user clicks on ROI."""
        # Keep flow active but mark all steps as complete
        self.flow_active = True  # Keep flow UI active
        
        # Mark all steps and sub-nodes as complete
        for step in self.flow_steps:
            step["status"] = "complete"
            # Mark all sub-nodes as complete
            for sub_node in step.get("sub_nodes", []):
                sub_node["status"] = "complete"
        
        # Redraw the flow UI with completed status
        self.draw_flow_ui()
        
        # Update center header to indicate completion but keep flow visible
        self.center_header.config(text="INSPECTION COMPLETE - Click ROI for Details")
    
    def _switch_to_detail_view(self):
        """Switch center panel to detail view."""
        # Clear flow UI
        for widget in self.center_thumb_frame.winfo_children():
            widget.destroy()
        
        # Show instruction to click on ROI
        instruction = tk.Label(
            self.center_thumb_frame,
            text="Click on any ROI in the result list\nto view detailed analysis",
            font=("SF Pro Display", 14),
            bg=get_current_theme()['bg'],
            fg=get_current_theme()['fg'],
            justify=tk.CENTER
        )
        instruction.pack(expand=True, fill="both")

    def update_flow_progress(self, step_name, status="active"):
        """Update flow progress - can be called from inspection module."""
        if hasattr(self, 'flow_active') and self.flow_active:
            self.update_flow_step(step_name, status)

    def stop_operation_timer(self):
        """Stop the operation timer."""
        self.timer_running = False
        if self._timer_after_id:
            self.timer_label.after_cancel(self._timer_after_id)
            self._timer_after_id = None
        self.timer_label.pack_forget()
        self.start_btn.config(state=tk.NORMAL)
        self.start_btn.pack(pady=(0,10))

    def set_status(self, text):
        """Set the status bar text."""
        self.status_var.set(text)
        # Set status bar text color based on content
        if hasattr(self, 'status_bar'):
            if any(word in text.lower() for word in ["error", "fail"]):
                self.status_bar.config(fg=get_current_theme()['error'])
            elif any(word in text.lower() for word in ["pass", "success", "complete"]):
                self.status_bar.config(fg=get_current_theme()['success'])
            elif any(word in text.lower() for word in ["warning", "retry"]):
                self.status_bar.config(fg=get_current_theme()['warning'])
            else:
                self.status_bar.config(fg=get_current_theme()['fg'])
        self.root.update_idletasks()

    def set_system_ready(self, ready):
        """Enable or disable the Starting Visual button based on system readiness."""
        print(f"DEBUG: set_system_ready called with ready={ready}")
        if hasattr(self, 'start_btn'):
            if ready:
                print("DEBUG: Enabling start button - system is ready")
                self.system_initialized = True  # Mark system as initialized
                self.start_btn.config(
                    state=tk.NORMAL, 
                    bg=get_current_theme()['success'],
                    text="Start Visual Inspection",
                    fg="white"
                )
                # Re-apply hover effects after manual color change
                add_button_hover_effect(self.start_btn, "success")
                # Update flow UI: mark System Ready as complete
                if hasattr(self, 'flow_steps') and len(self.flow_steps) > 0:
                    self.flow_steps[0]["status"] = "complete"
                    if hasattr(self, 'flow_active') and self.flow_active:
                        self.draw_flow_ui()
            else:
                print("DEBUG: Disabling start button - system not ready")
                self.start_btn.config(
                    state=tk.DISABLED, 
                    bg=get_current_theme()['button_bg'],
                    text="System Initializing...",
                    fg=get_current_theme()['button_fg']
                )
                # Re-apply hover effects after manual color change
                add_button_hover_effect(self.start_btn, "secondary")
                # Update flow UI: mark System Ready as pending/active
                if hasattr(self, 'flow_steps') and len(self.flow_steps) > 0:
                    self.flow_steps[0]["status"] = "pending"
                    if hasattr(self, 'flow_active') and self.flow_active:
                        self.draw_flow_ui()
                if hasattr(self, 'flow_steps') and len(self.flow_steps) > 0:
                    self.flow_steps[0]["status"] = "active"
                    if hasattr(self, 'flow_active') and self.flow_active:
                        self.draw_flow_ui()
        else:
            print("DEBUG: start_btn not found in UI")
        self.root.update_idletasks()

    def switch_theme(self, theme_name):
        """Switch between light and dark themes."""
        # Save the theme preference
        save_theme_preference(theme_name)
        
        # Set the theme globally
        set_theme(theme_name)
        
        # Reconfigure ttk theme
        configure_ttk_theme()
        
        # Re-apply theme to all widgets
        apply_theme(self.root, is_root=True)
        
        # Update status
        self.set_status(f"Theme switched to {theme_name} mode")
        
        print(f"Theme switched to: {theme_name}")

    def show_result(self, roi_results=None, device_summaries=None):
        """Display inspection results with per-device summary."""
        print("DEBUG: Entered show_result")
        print(f"DEBUG: roi_results parameter: {type(roi_results)} with {len(roi_results) if roi_results else 0} items")
        print(f"DEBUG: device_summaries parameter: {type(device_summaries)} with {len(device_summaries) if device_summaries else 0} items")
        if device_summaries:
            print(f"DEBUG: Received device summaries for {len(device_summaries)} devices")
        
        # Complete flow UI when results are ready
        if self.flow_active:
            self.complete_flow_ui()
        
        self.roi_results_for_overview = roi_results.copy() if roi_results else []
        self.device_summaries = device_summaries or {}
        
        print(f"DEBUG: roi_results type: {type(roi_results)}, length: {len(roi_results) if roi_results else 0}")
        print(f"DEBUG: device_summaries type: {type(device_summaries)}, length: {len(device_summaries) if device_summaries else 0}")

        # Clear ROI list display
        for widget in self.roi_frame.winfo_children():
            widget.destroy()
        self.original_rois = {}
        roi_img_width = 120
        roi_img_height = 90

        # Sort ROI results: Group by device, then FAIL first, then by ROI type, then by ROI index
        def roi_sort_key(roi):
            if not isinstance(roi, tuple) or len(roi) < 2:
                return (999, 2, 999, 999)  # Put invalid ROIs at the end
            
            roi_idx = roi[0] if roi[0] is not None else 999
            roi_type = roi[1] if roi[1] is not None else 999
            
            # Get device location from ROI index
            device_location = self._get_device_location_for_roi(roi_idx)
            
            # Determine if ROI passed
            roi_passed = self._is_roi_passed(roi)
            
            # Sort order: By device location, then Failed ROIs first (0), then passed ROIs (1)
            # Then by ROI type (1=Barcode, 2=Compare, 3=OCR)
            # Finally by ROI index
            pass_sort = 0 if not roi_passed else 1
            
            return (device_location, pass_sort, roi_type, roi_idx)
        
        if roi_results and isinstance(roi_results, (list, tuple)):
            roi_results = sorted(roi_results, key=roi_sort_key)

        # Compute overall result based on device results
        overall_pass = True
        if device_summaries:
            # Overall passes only if ALL devices pass
            overall_pass = all(summary['device_passed'] for summary in device_summaries.values())
        elif roi_results and isinstance(roi_results, (list, tuple)):
            # Fallback to original logic if no device summaries
            for roi in roi_results:
                if not self._is_roi_passed(roi):
                    overall_pass = False
                    break
        else:
            roi_results = []

        # Update overall result label with device information
        if hasattr(self, 'overall_result_var'):
            if device_summaries:
                elapsed = (time.time() - getattr(self, 'timer_start_time', time.time()))
                passed_devices = sum(1 for s in device_summaries.values() if s['device_passed'])
                total_devices = len(device_summaries)
                result_text = f"Result: {'PASS' if overall_pass else 'FAIL'}\nDevices: {passed_devices}/{total_devices}\nTime: {elapsed:.3f}s"
                self.overall_result_var.set(result_text)
                self.overall_result_label.config(fg=get_current_theme()['success'] if overall_pass else get_current_theme()['error'])
            elif roi_results:
                elapsed = (time.time() - getattr(self, 'timer_start_time', time.time()))
                if overall_pass:
                    self.overall_result_var.set(f"Result: PASS\nTime: {elapsed:.3f}s")
                    self.overall_result_label.config(fg=get_current_theme()['success'])
                else:
                    self.overall_result_var.set(f"Result: FAIL\nTime: {elapsed:.3f}s")
                    self.overall_result_label.config(fg=get_current_theme()['error'])
            else:
                self.overall_result_var.set("Result: N/A")
                self.overall_result_label.config(fg=get_current_theme()['fg'])

        # Display device summary if available
        if device_summaries:
            device_frame = tk.Frame(self.roi_frame, bg=get_current_theme()['bg'])
            device_frame.pack(fill="x", padx=6, pady=(6, 10))
            
            device_header = tk.Label(device_frame, text="DEVICE RESULTS", 
                                   font=("SF Pro Display", 12, "bold"),
                                   bg=get_current_theme()['bg'], 
                                   fg=get_current_theme()['fg'])
            device_header.pack(anchor="w")
            
            for device_id in sorted(device_summaries.keys()):
                summary = device_summaries[device_id]
                device_passed = summary['device_passed']
                barcode = summary.get('barcode', 'N/A')
                
                # Device result row
                device_row_frame = tk.Frame(device_frame, bg=get_current_theme()['surface'],
                                          relief="solid", borderwidth=1)
                device_row_frame.pack(fill="x", pady=2)
                
                # Status indicator
                status_color = get_current_theme()['success'] if device_passed else get_current_theme()['error']
                status_text = "PASS" if device_passed else "FAIL"
                
                status_label = tk.Label(device_row_frame, 
                                      text=f"Device {device_id}: {status_text}",
                                      font=("SF Pro Display", 10, "bold"),
                                      bg=get_current_theme()['surface'],
                                      fg=status_color)
                status_label.pack(side="left", padx=8, pady=4)
                
                # Barcode information
                barcode_label = tk.Label(device_row_frame,
                                       text=f"Barcode: {barcode}",
                                       font=("SF Pro Display", 10),
                                       bg=get_current_theme()['surface'],
                                       fg=get_current_theme()['fg'])
                barcode_label.pack(side="right", padx=8, pady=4)

        # Render ROI result widgets grouped by device
        if roi_results:
            print(f"DEBUG: About to render {len(roi_results)} ROI results")
            
            # Group ROI results by device location
            device_roi_groups = {}
            for roi in roi_results:
                print(f"DEBUG: Processing ROI: {roi[:3] if len(roi) >= 3 else roi}")  # Show first 3 fields
                if not isinstance(roi, tuple) or len(roi) < 2:
                    continue
                    
                roi_idx = roi[0]
                device_location = self._get_device_location_for_roi(roi_idx)
                
                if device_location not in device_roi_groups:
                    device_roi_groups[device_location] = []
                device_roi_groups[device_location].append(roi)
            
            # Display ROI results grouped by device
            for device_id in sorted(device_roi_groups.keys()):
                device_rois = device_roi_groups[device_id]
                
                # Device group header
                device_group_frame = tk.Frame(self.roi_frame, bg=get_current_theme()['bg'])
                device_group_frame.pack(fill="x", padx=6, pady=(10, 5))
                
                # Device group title with pass/fail status
                device_passed = True
                if device_summaries and device_id in device_summaries:
                    device_passed = device_summaries[device_id]['device_passed']
                    device_barcode = device_summaries[device_id].get('barcode', 'N/A')
                else:
                    # Fallback: determine pass/fail from ROI results
                    for roi in device_rois:
                        if not self._is_roi_passed(roi):
                            device_passed = False
                            break
                    device_barcode = 'N/A'
                
                status_color = get_current_theme()['success'] if device_passed else get_current_theme()['error']
                status_text = "PASS" if device_passed else "FAIL"
                
                device_header = tk.Label(device_group_frame, 
                                       text=f"DEVICE {device_id} - {status_text} | Barcode: {device_barcode}",
                                       font=("SF Pro Display", 11, "bold"),
                                       bg=get_current_theme()['bg'],
                                       fg=status_color)
                device_header.pack(anchor="w")
                
                # Sort ROIs within device: Failed first, then by type, then by index
                device_rois.sort(key=lambda roi: (
                    0 if not self._is_roi_passed(roi) else 1,  # Failed ROIs first
                    roi[1] if len(roi) > 1 else 999,  # Then by ROI type
                    roi[0] if len(roi) > 0 else 999   # Then by ROI index
                ))
                
                # Display each ROI in this device group
                for roi in device_rois:
                    roi_idx = roi[0]
                    roi_type = roi[1]
                    
                    # Determine if ROI passed for border color
                    roi_passed = self._is_roi_passed(roi)
                    frame_bg = get_current_theme()['surface'] if roi_passed else '#4a1a1a'  # Slight red tint for failures
                    border_color = get_current_theme()['success'] if roi_passed else get_current_theme()['error']
                    
                    frame = tk.Frame(self.roi_frame, relief="solid", borderwidth=2, 
                                   bg=frame_bg, highlightbackground=border_color, highlightthickness=1)
                    frame.pack(fill="x", padx=6, pady=3)

                    if roi_type == 2 and len(roi) >= 9:  # Image Compare ROI
                        best_golden_img = roi[2]
                        roi_img2 = roi[3]
                        roi_info = roi[4]
                        roi_text = roi[5]
                        color = roi[6]
                        ai_similarity = roi[7]
                        ai_threshold = roi[8]
                        similarity_str = f" (AI sim: {ai_similarity:.3f})" if ai_similarity is not None else ""
                        threshold_str = f" | Threshold: {ai_threshold}" if ai_threshold is not None else ""
                        display_text = f"ROI {roi_idx} | {roi_text}{similarity_str}{threshold_str}"
                        border_color = "green" if roi_text and "Match" in roi_text else "red"
                        
                        # Create thumbnails
                        img1 = get_thumbnail_pil(best_golden_img, roi_img_width, roi_img_height)
                        img2 = get_thumbnail_pil(roi_img2, roi_img_width, roi_img_height)
                        tk_img1 = ImageTk.PhotoImage(img1)
                        tk_img2 = ImageTk.PhotoImage(img2)
                        
                        # Display images with borders
                        c1 = tk.Canvas(frame, width=roi_img_width+4, height=roi_img_height+4, highlightthickness=0)
                        c1.pack(side="left")
                        c1.create_rectangle(2, 2, roi_img_width+2, roi_img_height+2, outline=border_color, width=4)
                        l1 = tk.Label(c1, image=tk_img1, bd=0)
                        l1.image = tk_img1
                        l1.place(x=2, y=2)
                        
                        c2 = tk.Canvas(frame, width=roi_img_width+4, height=roi_img_height+4, highlightthickness=0)
                        c2.pack(side="left")
                        c2.create_rectangle(2, 2, roi_img_width+2, roi_img_height+2, outline=border_color, width=4)
                        l2 = tk.Label(c2, image=tk_img2, bd=0)
                        l2.image = tk_img2
                        l2.place(x=2, y=2)
                        
                        r = tk.Label(frame, text=display_text, font=("SF Pro Display", 10),
                                   bg=frame_bg, fg=get_current_theme()['fg'])
                        r.pack(side="left", padx=4)
                        
                        def make_callback(idx, rt, gimg, r2, txt, bcolor):
                            def callback(event):
                                self.current_roi_idx = idx
                                self.selected_center_idx = idx
                                # Switch to detailed view and show ROI details
                                self.flow_active = False
                                self.center_header.config(text="DETAILED VIEW")
                                self.show_center_thumbnail(rt, gimg, r2, txt, border_color=bcolor, idx=idx)
                            return callback
                        
                        l1.bind("<Button-1>", make_callback(roi_idx, roi_type, best_golden_img, roi_img2, roi_text, border_color))
                        l2.bind("<Button-1>", make_callback(roi_idx, roi_type, best_golden_img, roi_img2, roi_text, border_color))
                        r.bind("<Button-1>", make_callback(roi_idx, roi_type, best_golden_img, roi_img2, roi_text, border_color))

                    elif roi_type == 1 and len(roi) >= 7:  # Barcode ROI
                        roi_image = roi[2]  # The barcode image
                        coordinates = roi[4]  # Coordinates tuple
                        barcode_label = roi[5]  # "Barcode" label
                        barcode_values = roi[6]  # The actual barcode data
                        
                        print(f"DEBUG: Barcode ROI {roi_idx} - values: {barcode_values}, type: {type(barcode_values)}")
                        
                        # Format barcode values for display
                        if barcode_values and isinstance(barcode_values, list):
                            barcode_text = ", ".join(str(b) for b in barcode_values)
                        elif barcode_values:
                            barcode_text = str(barcode_values)
                        else:
                            barcode_text = "No barcode detected"
                        
                        display_text = f"ROI {roi_idx} | Barcode: {barcode_text}"
                        
                        # Try to display the barcode image if available
                        if roi_image is not None:
                            try:
                                img = get_thumbnail_pil(roi_image, roi_img_width, roi_img_height)
                                tk_img = ImageTk.PhotoImage(img)
                                
                                c = tk.Canvas(frame, width=roi_img_width+4, height=roi_img_height+4, highlightthickness=0)
                                c.pack(side="left")
                                c.create_rectangle(2, 2, roi_img_width+2, roi_img_height+2, outline=border_color, width=4)
                                img_label = tk.Label(c, image=tk_img, bd=0)
                                img_label.image = tk_img
                                img_label.place(x=2, y=2)
                                
                            except Exception as e:
                                print(f"Error displaying barcode image: {e}")
                        
                        r = tk.Label(frame, text=display_text, font=("SF Pro Display", 10),
                                   bg=frame_bg, fg=get_current_theme()['fg'])
                        r.pack(side="left", padx=6, pady=6)
                    
                    elif roi_type == 3 and len(roi) >= 7:  # OCR ROI
                        ocr_text = roi[6] if len(roi) > 6 else ""  # OCR text is in field 6
                        ocr_label = roi[5] if len(roi) > 5 else "OCR"  # OCR label is in field 5
                        coordinates = roi[4] if len(roi) > 4 else None  # Coordinates in field 4
                        
                        # OCR ROIs don't include image data in the result tuple
                        # The image would need to be extracted from the original captured image using coordinates
                        display_text = f"ROI {roi_idx} | {ocr_label}: {ocr_text if ocr_text else 'No text detected'}"
                        
                        r = tk.Label(frame, text=display_text, font=("SF Pro Display", 10),
                                   bg=frame_bg, fg=get_current_theme()['fg'])
                        r.pack(side="left", padx=6)
                        
                        # Add click callback for OCR ROIs (without image display)
                        def make_ocr_callback(idx, txt):
                            def callback(event):
                                self.current_roi_idx = idx
                                self.selected_center_idx = idx
                                # Switch to detailed view
                                self.flow_active = False
                                self.center_header.config(text="DETAILED VIEW")
                                # For OCR, we can show text details without image
                                print(f"OCR ROI {idx} clicked: {txt}")
                            return callback
                        
                        r.bind("<Button-1>", make_ocr_callback(roi_idx, display_text))
        else:
            print("DEBUG: No ROI results to display")
            # Show a message when no ROI results are available
            no_results_frame = tk.Frame(self.roi_frame, bg=get_current_theme()['bg'])
            no_results_frame.pack(fill="x", padx=6, pady=10)
            
            no_results_label = tk.Label(no_results_frame, 
                                      text="No ROI results available",
                                      font=("SF Pro Display", 12),
                                      bg=get_current_theme()['bg'],
                                      fg=get_current_theme()['fg'])
            no_results_label.pack(anchor="center")

    def _get_device_location_for_roi(self, roi_idx):
        """Get device location for a given ROI index."""
        try:
            from .roi import get_rois
            rois = get_rois()
            for roi in rois:
                if roi and len(roi) > 0 and roi[0] == roi_idx:
                    return roi[8] if len(roi) >= 9 else 1
            return 1  # Default device location
        except:
            return 1  # Default device location

    def refresh_thumbnail_display(self):
        """Refresh the thumbnail display"""
        # Re-display the current thumbnail
        if hasattr(self, 'current_thumbnail_data'):
            roi_type, roi_img1, roi_img2, roi_text, border_color, idx = self.current_thumbnail_data
            self.show_center_thumbnail(roi_type, roi_img1, roi_img2, roi_text, border_color, idx)

    def show_center_thumbnail(self, roi_type, roi_img1, roi_img2, roi_text, border_color="black", idx=None):
        """Display enlarged thumbnail in center panel with fixed size."""
        # Store current thumbnail data for refresh functionality
        self.current_thumbnail_data = (roi_type, roi_img1, roi_img2, roi_text, border_color, idx)
        
        for widget in self.center_thumb_frame.winfo_children():
            widget.destroy()
        roi_idx = idx if idx is not None else getattr(self, 'selected_center_idx', 0)
        
        # Use fixed thumbnail dimensions (no zoom)
        base_width = self.thumbnail_base_width
        base_height = self.thumbnail_base_height
        
        if roi_type == 2 and roi_img2 is not None:
            # Create container for dual images
            images_container = tk.Frame(self.center_thumb_frame, bg=get_current_theme()['surface'])
            images_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            # Prepare images with fixed aspect ratio
            img1 = get_thumbnail_pil(roi_img1, base_width, base_height)
            img2 = get_thumbnail_pil(roi_img2, base_width, base_height)
            tk_img1 = ImageTk.PhotoImage(img1)
            tk_img2 = ImageTk.PhotoImage(img2)
            
            # Add first image
            img_label1 = tk.Label(images_container, image=tk_img1, bd=2, relief="solid",
                                 highlightthickness=2, highlightcolor=border_color,
                                 highlightbackground=border_color)
            img_label1.image = tk_img1
            img_label1.grid(row=0, column=0, padx=(0, 5))
            
            # Add second image
            img_label2 = tk.Label(images_container, image=tk_img2, bd=2, relief="solid",
                                 highlightthickness=2, highlightcolor=border_color,
                                 highlightbackground=border_color)
            img_label2.image = tk_img2
            img_label2.grid(row=0, column=1, padx=(5, 0))
            
            # Configure grid weights
            images_container.grid_columnconfigure(0, weight=1)
            images_container.grid_columnconfigure(1, weight=1)
            
            tk.Label(self.center_thumb_frame, text=roi_text, font=("SF Pro Display", 14)).grid(row=1, column=0, pady=10)
            
            def save_current_as_golden():
                # Get current product name dynamically
                from .config import get_product_name
                current_product = get_product_name()
                if current_product is None:
                    messagebox.showerror("Error", "No product name is set. Please restart the application.")
                    return
                save_golden_roi(roi_idx, roi_img2, current_product)
                messagebox.showinfo("Saved", f"Current ROI (index {roi_idx}) saved as golden reference.")
            
            btn = tk.Button(self.center_thumb_frame, text="Confirm this ROI is correct and teach AI to recognize it", 
                           command=save_current_as_golden, font=("SF Pro Display", 12),
                           bg=get_current_theme()['success'], fg="white",
                           activebackground=get_current_theme()['button_active'],
                           relief='flat', pady=8, cursor='hand2')
            btn.grid(row=2, column=0, pady=10)
            add_button_hover_effect(btn, "success")
        else:
            # Prepare image with fixed aspect ratio
            img = get_thumbnail_pil(roi_img1, base_width, base_height)
            tk_img = ImageTk.PhotoImage(img)
            
            # Add single image
            img_label = tk.Label(self.center_thumb_frame, image=tk_img, bd=2, relief="solid",
                               highlightthickness=2, highlightcolor=border_color,
                               highlightbackground=border_color)
            img_label.image = tk_img
            img_label.grid(row=0, column=0, padx=10, pady=10)
            
            tk.Label(self.center_thumb_frame, text=roi_text, font=("SF Pro Display", 14)).grid(row=1, column=0, pady=10)
        
        # Configure grid weights for center frame
        self.center_thumb_frame.grid_rowconfigure(0, weight=1)
        self.center_thumb_frame.grid_columnconfigure(0, weight=1)

    def _is_roi_passed(self, roi):
        """Check if a ROI result indicates a pass."""
        if not roi or not isinstance(roi, tuple) or len(roi) < 2:
            return False
        
        roi_type = roi[1]
        
        if roi_type == 2:  # Compare ROI
            roi_text = roi[5] if len(roi) > 5 else ""
            return roi_text and "Match" in str(roi_text) and "No Match" not in str(roi_text)
        elif roi_type == 1:  # Barcode ROI
            barcode_result = roi[6] if len(roi) > 6 else None
            return bool(barcode_result)
        elif roi_type == 3:  # OCR ROI
            ocr_result = roi[6] if len(roi) > 6 else ""  # OCR text is in field 6
            ocr_text = str(ocr_result).strip()
            # Pass if OCR has text and doesn't contain error messages
            return bool(ocr_text and ocr_text != "N/A" and not ocr_text.startswith("Error"))
        
        return False

    def show_overview_window(self):
        """Show overview window with full image and comprehensive ROI result overlays."""
        img = getattr(self, 'last_img', None)
        if img is None:
            messagebox.showerror("Error", "No captured image available for overview.")
            return
        if not hasattr(self, 'roi_results_for_overview') or not self.roi_results_for_overview:
            messagebox.showerror("Error", "No ROI results available for overview.")
            return

        roi_results = self.roi_results_for_overview
        img_disp = img.copy()
        
        # Calculate overall result status
        overall_pass = True
        total_rois = len(roi_results)
        passed_rois = 0
        
        # Process each ROI and overlay detailed information
        for roi in roi_results:
            if not isinstance(roi, tuple) or len(roi) < 2:
                continue
                
            roi_idx = roi[0]
            roi_type = roi[1]
            roi_passed = self._is_roi_passed(roi)
            
            if roi_passed:
                passed_rois += 1
            else:
                overall_pass = False
            
            # Extract ROI coordinates
            roi_info = None
            if len(roi) >= 5:
                roi_info = roi[4]
            if not roi_info or not isinstance(roi_info, (tuple, list)) or len(roi_info) != 4:
                continue
                
            x1, y1, x2, y2 = roi_info
            
            # Determine color based on ROI type and result
            if roi_passed:
                color = (0, 255, 0)  # Green for pass
                text_color = (0, 255, 0)
            else:
                color = (0, 0, 255)  # Red for fail
                text_color = (0, 0, 255)
            
            # Draw ROI rectangle with thicker border
            cv2.rectangle(img_disp, (x1, y1), (x2, y2), color, 4)
            
            # Only show ROI index - simplified display
            roi_index_text = str(roi_idx)
            
            # Draw ROI index only (larger, centered in ROI)
            text_size = cv2.getTextSize(roi_index_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            text_x = x1 + (x2 - x1 - text_size[0]) // 2  # Center horizontally
            text_y = y1 + (y2 - y1 + text_size[1]) // 2  # Center vertically
            
            # Ensure text is within ROI bounds
            text_x = max(x1 + 5, min(text_x, x2 - text_size[0] - 5))
            text_y = max(y1 + text_size[1] + 5, min(text_y, y2 - 5))
            
            # Draw white background for better text visibility
            cv2.rectangle(img_disp, 
                         (text_x - 5, text_y - text_size[1] - 5), 
                         (text_x + text_size[0] + 5, text_y + 5), 
                         (255, 255, 255), -1)
            
            # Draw ROI index with black text on white background
            cv2.putText(img_disp, roi_index_text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3, cv2.LINE_AA)

        # Add overall summary at the top of the image
        summary_text = f"Overall: {'PASS' if overall_pass else 'FAIL'} ({passed_rois}/{total_rois} ROIs passed)"
        elapsed_time = getattr(self, 'last_processing_time', 0)
        time_text = f"Processing time: {elapsed_time:.3f}s" if elapsed_time > 0 else ""
        
        # Draw summary background
        img_h, img_w = img_disp.shape[:2]
        cv2.rectangle(img_disp, (10, 10), (img_w - 10, 100), (0, 0, 0), -1)  # Black background
        cv2.rectangle(img_disp, (10, 10), (img_w - 10, 100), (255, 255, 255), 2)  # White border
        
        # Draw summary text
        summary_color = (0, 255, 0) if overall_pass else (0, 0, 255)
        cv2.putText(img_disp, summary_text, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, summary_color, 3, cv2.LINE_AA)
        
        if time_text:
            cv2.putText(img_disp, time_text, (20, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        # Create overview window
        win = tk.Toplevel(self.root)
        win.title("Overview - Complete Inspection Results")
        
        # Initialize window to fit current screen
        win.update_idletasks()  # Ensure window is ready
        
        # Get screen dimensions
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        
        # Set window to fit screen with some padding
        window_width = int(screen_width * 0.9)  # 90% of screen width
        window_height = int(screen_height * 0.9)  # 90% of screen height
        
        # Center the window on screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        win.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Try to maximize if possible, fallback to geometry sizing
        try:
            win.state('zoomed')  # Windows
        except Exception:
            try:
                win.attributes('-zoomed', True)  # Linux
            except Exception:
                # Use the geometry we set above as fallback
                pass
        
        win.minsize(800, 600)  # Set minimum size

        # Convert to RGB for display
        img_rgb = cv2.cvtColor(img_disp, cv2.COLOR_BGR2RGB)
        pil_img_orig = Image.fromarray(img_rgb)

        # Create main frame and toolbar
        main_frame = tk.Frame(win)
        main_frame.pack(fill="both", expand=True)
        
        # Enhanced toolbar with zoom controls
        toolbar = tk.Frame(main_frame, bg=get_current_theme()['surface'], height=40)
        toolbar.pack(side="top", fill="x", padx=5, pady=2)
        
        # Zoom state variables
        zoom_state = {
            'zoom_level': 1.0,
            'min_zoom': 0.1,
            'max_zoom': 10.0,
            'pan_start': None,
            'canvas_width': 0,
            'canvas_height': 0,
            'image_width': pil_img_orig.width,
            'image_height': pil_img_orig.height,
            'current_image': pil_img_orig,
            'canvas_image_id': None,
            'pan_offset_x': 0,
            'pan_offset_y': 0
        }
        
        # Zoom control buttons
        zoom_frame = tk.Frame(toolbar, bg=get_current_theme()['surface'])
        zoom_frame.pack(side="left", padx=(10, 20))
        
        # Zoom out button
        zoom_out_btn = tk.Button(zoom_frame, text="🔍−", font=("SF Pro Display", 12, "bold"),
                                bg=get_current_theme()['button_bg'], fg=get_current_theme()['button_fg'],
                                activebackground=get_current_theme()['button_active'],
                                relief='flat', padx=8, pady=4)
        zoom_out_btn.pack(side="left", padx=(0, 5))
        
        # Zoom level label
        zoom_label = tk.Label(zoom_frame, text="100%", font=("SF Pro Display", 10),
                             bg=get_current_theme()['surface'], fg=get_current_theme()['fg'],
                             width=6)
        zoom_label.pack(side="left", padx=5)
        
        # Zoom in button
        zoom_in_btn = tk.Button(zoom_frame, text="🔍+", font=("SF Pro Display", 12, "bold"),
                               bg=get_current_theme()['button_bg'], fg=get_current_theme()['button_fg'],
                               activebackground=get_current_theme()['button_active'],
                               relief='flat', padx=8, pady=4)
        zoom_in_btn.pack(side="left", padx=(5, 0))
        
        # Fit to window button
        fit_btn = tk.Button(toolbar, text="Fit to Window", font=("SF Pro Display", 10),
                           bg=get_current_theme()['button_bg'], fg=get_current_theme()['button_fg'],
                           activebackground=get_current_theme()['button_active'],
                           relief='flat', padx=10, pady=4)
        fit_btn.pack(side="left", padx=(20, 10))
        
        # Actual size button
        actual_btn = tk.Button(toolbar, text="Actual Size", font=("SF Pro Display", 10),
                              bg=get_current_theme()['button_bg'], fg=get_current_theme()['button_fg'],
                              activebackground=get_current_theme()['button_active'],
                              relief='flat', padx=10, pady=4)
        actual_btn.pack(side="left", padx=(0, 10))
        
        # Reset view button
        reset_btn = tk.Button(toolbar, text="Reset View", font=("SF Pro Display", 10),
                             bg=get_current_theme()['warning'], fg="white",
                             activebackground=get_current_theme()['button_active'],
                             relief='flat', padx=10, pady=4)
        reset_btn.pack(side="left", padx=(10, 0))
        
        # Create scrollable canvas for the image
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="black", highlightthickness=0)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        def update_zoom_label():
            """Update the zoom level label."""
            zoom_label.config(text=f"{int(zoom_state['zoom_level'] * 100)}%")
        
        def clamp_pan_offset():
            """Clamp pan offset to prevent image from being dragged completely out of view."""
            img_w = int(zoom_state['image_width'] * zoom_state['zoom_level'])
            img_h = int(zoom_state['image_height'] * zoom_state['zoom_level'])
            canvas_w = zoom_state['canvas_width']
            canvas_h = zoom_state['canvas_height']
            
            # Calculate maximum offsets
            max_offset_x = max(0, img_w - canvas_w)
            max_offset_y = max(0, img_h - canvas_h)
            
            # Clamp offsets
            zoom_state['pan_offset_x'] = max(min(zoom_state['pan_offset_x'], max_offset_x), -max_offset_x)
            zoom_state['pan_offset_y'] = max(min(zoom_state['pan_offset_y'], max_offset_y), -max_offset_y)
        
        def update_image_display():
            """Update the image display with current zoom and pan settings."""
            zoom_level = zoom_state['zoom_level']
            
            # Calculate new image size
            new_width = int(zoom_state['image_width'] * zoom_level)
            new_height = int(zoom_state['image_height'] * zoom_level)
            
            # Resize image with high quality
            try:
                if zoom_level > 1.0:
                    # Use LANCZOS for upscaling (higher quality)
                    resized_img = zoom_state['current_image'].resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    # Use LANCZOS for downscaling as well
                    resized_img = zoom_state['current_image'].resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                # Fallback for older PIL versions
                resized_img = zoom_state['current_image'].resize((new_width, new_height))
            
            # Create PhotoImage
            photo = ImageTk.PhotoImage(resized_img)
            
            # Clear canvas and create new image
            canvas.delete("all")
            
            # Calculate position with pan offset
            x_pos = -zoom_state['pan_offset_x']
            y_pos = -zoom_state['pan_offset_y']
            
            zoom_state['canvas_image_id'] = canvas.create_image(x_pos, y_pos, image=photo, anchor="nw")
            
            # Store reference to prevent garbage collection
            zoom_state['current_photo'] = photo
            
            # Update scroll region
            canvas.configure(scrollregion=(x_pos, y_pos, x_pos + new_width, y_pos + new_height))
            
            # Update zoom label
            update_zoom_label()
        
        def zoom_to_level(new_zoom, center_x=None, center_y=None):
            """Zoom to a specific level, optionally centered on a point."""
            # Clamp zoom level
            new_zoom = max(zoom_state['min_zoom'], min(zoom_state['max_zoom'], new_zoom))
            
            if center_x is not None and center_y is not None:
                # Calculate relative position before zoom
                old_zoom = zoom_state['zoom_level']
                
                # Convert canvas coordinates to image coordinates
                img_x = (center_x + zoom_state['pan_offset_x']) / old_zoom
                img_y = (center_y + zoom_state['pan_offset_y']) / old_zoom
                
                # Update zoom level
                zoom_state['zoom_level'] = new_zoom
                
                # Calculate new pan offset to keep the same point under cursor
                zoom_state['pan_offset_x'] = img_x * new_zoom - center_x
                zoom_state['pan_offset_y'] = img_y * new_zoom - center_y
            else:
                # Simple center zoom
                zoom_state['zoom_level'] = new_zoom
            
            clamp_pan_offset()
            update_image_display()
        
        def zoom_in(event=None):
            """Zoom in by 25%."""
            zoom_to_level(zoom_state['zoom_level'] * 1.25)
        
        def zoom_out(event=None):
            """Zoom out by 25%."""
            zoom_to_level(zoom_state['zoom_level'] / 1.25)
        
        def fit_to_window(event=None):
            """Fit image to window while maintaining aspect ratio."""
            # Get current canvas dimensions
            canvas_w = canvas.winfo_width()
            canvas_h = canvas.winfo_height()
            
            # Account for scrollbars and padding
            effective_canvas_w = max(canvas_w - 20, 100)  # Subtract scrollbar width + padding
            effective_canvas_h = max(canvas_h - 20, 100)  # Subtract scrollbar height + padding
            
            if effective_canvas_w > 1 and effective_canvas_h > 1:
                # Calculate scale to fit image in effective canvas area
                scale_x = effective_canvas_w / zoom_state['image_width']
                scale_y = effective_canvas_h / zoom_state['image_height']
                new_zoom = min(scale_x, scale_y) * 0.95  # 95% to add some padding
                
                zoom_state['zoom_level'] = max(zoom_state['min_zoom'], new_zoom)
                zoom_state['pan_offset_x'] = 0
                zoom_state['pan_offset_y'] = 0
                
                update_image_display()
            else:
                # Fallback for very small windows
                zoom_state['zoom_level'] = 0.5
                zoom_state['pan_offset_x'] = 0
                zoom_state['pan_offset_y'] = 0
                update_image_display()
        
        def actual_size(event=None):
            """Show image at actual size (100%)."""
            zoom_state['zoom_level'] = 1.0
            zoom_state['pan_offset_x'] = 0
            zoom_state['pan_offset_y'] = 0
            update_image_display()
        
        def reset_view(event=None):
            """Reset view to initial state."""
            fit_to_window()
        
        def on_mouse_wheel(event):
            """Handle mouse wheel zoom."""
            # Get mouse position relative to canvas
            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)
            
            # Determine zoom factor
            if event.delta > 0:
                factor = 1.1
            else:
                factor = 0.9
            
            new_zoom = zoom_state['zoom_level'] * factor
            zoom_to_level(new_zoom, canvas_x, canvas_y)
        
        def start_pan(event):
            """Start panning operation."""
            zoom_state['pan_start'] = (event.x, event.y)
            canvas.config(cursor="fleur")
        
        def do_pan(event):
            """Perform panning operation."""
            if zoom_state['pan_start']:
                dx = event.x - zoom_state['pan_start'][0]
                dy = event.y - zoom_state['pan_start'][1]
                
                zoom_state['pan_offset_x'] -= dx
                zoom_state['pan_offset_y'] -= dy
                
                clamp_pan_offset()
                update_image_display()
                
                zoom_state['pan_start'] = (event.x, event.y)
        
        def end_pan(event):
            """End panning operation."""
            zoom_state['pan_start'] = None
            canvas.config(cursor="")
        
        # Bind button commands
        zoom_in_btn.config(command=zoom_in)
        zoom_out_btn.config(command=zoom_out)
        fit_btn.config(command=fit_to_window)
        actual_btn.config(command=actual_size)
        reset_btn.config(command=reset_view)
        
        # Bind mouse events for zoom and pan
        canvas.bind("<MouseWheel>", on_mouse_wheel)
        canvas.bind("<Button-4>", lambda e: on_mouse_wheel(type('Event', (), {'delta': 120, 'x': e.x, 'y': e.y})()))
        canvas.bind("<Button-5>", lambda e: on_mouse_wheel(type('Event', (), {'delta': -120, 'x': e.x, 'y': e.y})()))
        
        # Pan with left mouse button
        canvas.bind("<ButtonPress-1>", start_pan)
        canvas.bind("<B1-Motion>", do_pan)
        canvas.bind("<ButtonRelease-1>", end_pan)
        
        # Keyboard shortcuts
        win.bind("<KeyPress-plus>", zoom_in)
        win.bind("<KeyPress-equal>", zoom_in)  # + key without shift
        win.bind("<KeyPress-minus>", zoom_out)
        win.bind("<Control-0>", fit_to_window)
        win.bind("<Control-1>", actual_size)
        win.bind("<Control-r>", reset_view)
        win.bind("<Escape>", lambda e: win.destroy())
        
        # Make window focusable for keyboard shortcuts
        win.focus_set()
        
        # Store canvas dimensions and handle resize
        def on_canvas_configure(event):
            zoom_state['canvas_width'] = event.width
            zoom_state['canvas_height'] = event.height
        
        # Resize debouncing state
        resize_timer = {'after_id': None}  # type: dict
        
        # Handle window resize to re-fit image
        def on_window_configure(event):
            """Handle window resize events to maintain proper image fitting."""
            # Only handle main window resize events, not canvas or other widgets
            if event.widget == win:
                # Debounce resize events - only act after resize is complete
                if resize_timer['after_id']:
                    win.after_cancel(resize_timer['after_id'])
                
                def delayed_refit():
                    # Update canvas dimensions
                    win.update_idletasks()
                    new_canvas_w = canvas.winfo_width()
                    new_canvas_h = canvas.winfo_height()
                    
                    if new_canvas_w > 50 and new_canvas_h > 50:  # Valid dimensions
                        zoom_state['canvas_width'] = new_canvas_w
                        zoom_state['canvas_height'] = new_canvas_h
                        # Auto re-fit image to new window size
                        fit_to_window()
                    
                    resize_timer['after_id'] = None
                
                resize_timer['after_id'] = win.after(300, delayed_refit)  # 300ms delay
        
        canvas.bind("<Configure>", on_canvas_configure)
        win.bind("<Configure>", on_window_configure)
        
        # Initialize display after window is ready
        def initialize_display():
            """Initialize display with proper window and image sizing."""
            # Force window update to get accurate dimensions
            win.update_idletasks()
            
            # Wait a bit more for window to be fully rendered
            win.after(50, lambda: win.update_idletasks())
            
            # Get actual canvas dimensions after window is rendered
            actual_canvas_w = canvas.winfo_width()
            actual_canvas_h = canvas.winfo_height()
            
            # If canvas is too small, use window dimensions as fallback
            if actual_canvas_w < 100 or actual_canvas_h < 100:
                win_w = win.winfo_width()
                win_h = win.winfo_height()
                # Account for toolbar and status bar heights (approximately 100px total)
                actual_canvas_w = max(win_w - 50, 400)
                actual_canvas_h = max(win_h - 150, 300)
            
            zoom_state['canvas_width'] = actual_canvas_w
            zoom_state['canvas_height'] = actual_canvas_h
            
            print(f"DEBUG: Canvas dimensions: {actual_canvas_w}x{actual_canvas_h}")
            print(f"DEBUG: Image dimensions: {zoom_state['image_width']}x{zoom_state['image_height']}")
            
            # Calculate initial zoom to fit image in window
            scale_x = (actual_canvas_w - 40) / zoom_state['image_width']  # Account for scrollbars
            scale_y = (actual_canvas_h - 40) / zoom_state['image_height']
            initial_zoom = min(scale_x, scale_y, 1.0) * 0.9  # 90% for padding, max 100%
            
            zoom_state['zoom_level'] = max(zoom_state['min_zoom'], initial_zoom)
            zoom_state['pan_offset_x'] = 0
            zoom_state['pan_offset_y'] = 0
            
            print(f"DEBUG: Initial zoom level: {zoom_state['zoom_level']:.3f}")
            
            # Update display with fitted image
            update_image_display()
        
        # Schedule initialization with proper timing
        win.after(200, initialize_display)  # Increased delay for better window initialization
        
        # Enhanced status bar with more information
        status_frame = tk.Frame(win, bg=get_current_theme()['surface'])
        status_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        status_text = f"Results: {summary_text} | Simplified View: ROI Index Only | Mouse: Wheel=Zoom, Drag=Pan | Keys: +/- Zoom, Ctrl+0 Fit, Ctrl+1 Actual, Ctrl+R Reset, Esc Close"
        status_label = tk.Label(status_frame, text=status_text, 
                               font=("SF Pro Display", 9),
                               bg=get_current_theme()['surface'], 
                               fg=get_current_theme()['fg'])
        status_label.pack(side="left")
        
        # Store processing time for future reference
        if hasattr(self, 'timer_start_time'):
            self.last_processing_time = time.time() - self.timer_start_time
