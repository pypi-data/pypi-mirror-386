import tkinter as tk
from tkinter import ttk
from .gui import MainApp
from .gui_elements import set_dark_style, spacrButton

def convert_to_number(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Unable to convert '{value}' to an integer or float.")
    
def initiate_annotation_app(parent_frame):
    from .gui_utils import generate_annotate_fields, annotate_app, convert_to_number
    # Set up the settings window
    settings_window = tk.Toplevel(parent_frame)
    settings_window.title("Annotation Settings")
    style_out = set_dark_style(ttk.Style())
    settings_window.configure(bg=style_out['bg_color'])
    settings_frame = tk.Frame(settings_window, bg=style_out['bg_color'])
    settings_frame.pack(fill=tk.BOTH, expand=True)
    vars_dict = generate_annotate_fields(settings_frame)
    
    def start_annotation_app():
        settings = {key: data['entry'].get() for key, data in vars_dict.items()}
        settings['channels'] = settings['channels'].split(',')
        settings['img_size'] = list(map(int, settings['img_size'].split(',')))  # Convert string to list of integers
        settings['percentiles'] = list(map(convert_to_number, settings['percentiles'].split(','))) if settings['percentiles'] else [2, 98]
        settings['normalize'] = True
        #settings['normalize'] = settings['normalize'].lower() == 'true'
        settings['normalize_channels'] = settings['normalize_channels'].split(',')
        settings['outline'] = settings['outline'].split(',') if settings['outline'] else None
        settings['outline_threshold_factor'] = float(settings['outline_threshold_factor']) if settings['outline_threshold_factor'] else 1.0
        settings['outline_sigma'] = float(settings['outline_threshold_factor']) if settings['outline_threshold_factor'] else 1.0
        
        try:
            settings['measurement'] = settings['measurement'].split(',') if settings['measurement'] else None
            settings['threshold'] = None if settings['threshold'].lower() == 'none' else int(settings['threshold'])
        except:
            settings['measurement']  = None
            settings['threshold'] = None

        settings['db'] = settings.get('db', 'default.db')

        # Convert empty strings to None
        for key, value in settings.items():
            if isinstance(value, list):
                settings[key] = [v if v != '' else None for v in value]
            elif value == '':
                settings[key] = None

        settings_window.destroy()
        annotate_app(parent_frame, settings)
    
    start_button = spacrButton(settings_window, text="annotate", command=start_annotation_app, show_text=False)
    start_button.pack(pady=10)

def start_annotate_app():
    app = MainApp(default_app="Annotate")
    app.mainloop()

if __name__ == "__main__":
    start_annotate_app()