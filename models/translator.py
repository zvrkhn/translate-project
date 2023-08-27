import tkinter as tk
from tkinter import ttk, filedialog

import model

language_map = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Ukrainian": "uk",
    "Russian": "ru",
    "Polish": "pl"    
}

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image-to-text translator")
        self.root.attributes("-topmost", True)

        self.lang_var = tk.StringVar()
        self.lang_var.set("English")  # Default language

        self.current_window = None  # Keep track of the currently open window

        self.create_first_window()
        self.language = ""
        self.file_path = ""
        self.model = None

    def create_window(self):
        if self.current_window:
            self.current_window.destroy()

    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    def get_language_code(self, full_name):
        global language_map

        return language_map.get(full_name, None)

    def create_first_window(self):
        global language_map
        self.create_window()

        self.center_window(self.root, 400, 300)
        self.current_window = self.root

        self.file_label = tk.Label(self.root, text="Select a File:")
        self.file_label.pack()
        self.file_button = ttk.Button(self.root, text="Choose File", command=self.choose_file)
        self.file_button.pack()

        self.lang_label = tk.Label(self.root, text="Select a Language:")
        self.lang_label.pack()
        self.lang_options = list(language_map.keys())
        self.lang_menu = ttk.Combobox(self.root, values=self.lang_options, textvariable=self.lang_var)
        self.lang_menu.pack()

        self.next_button = ttk.Button(self.root, text="Next", command=self.run_code)
        self.next_button.pack()

    def create_second_window(self):
        # self.create_window()
        self.current_window = tk.Toplevel()

        self.second_window = self.current_window
        self.second_window.title("Translating...")
        self.center_window(self.second_window, 300, 200)

        self.translating_label = tk.Label(self.second_window, text="Translating...")
        self.translating_label.pack()

        # Simulating code execution time
        self.model = model.ImageTranslator(self.file_path, "auto", self.language)
        self.model.run()

        self.create_third_window()

    def create_third_window(self):
        self.create_window()

        # self.current_window = tk.Toplevel(self.root)
        self.current_window = tk.Toplevel()
        self.third_window = self.current_window
        self.current_window.attributes("-topmost", True)

        self.third_window.title("Result")
        self.center_window(self.third_window, 400, 200)

        self.save_button = ttk.Button(self.third_window, text="Save File", command=self.save_file)
        self.save_button.pack()

        self.preview_button = ttk.Button(self.third_window, text="Preview File", command=self.preview_file)
        self.preview_button.pack()

        self.exit_button = ttk.Button(self.third_window, text="Exit", command=self.root.quit)
        self.exit_button.pack()

    def choose_file(self):
        file_path = filedialog.askopenfilename()
        print("Chosen File:", file_path)
        self.file_path = file_path

    def run_code(self):
        print("Language selected:", self.lang_var.get())
        self.language = self.get_language_code(self.lang_var.get())
        self.create_second_window()

    def save_file(self):
        save_path = filedialog.askdirectory()
        print("Save File:", save_path)
        self.model.save(save_path, 'result')


    def preview_file(self):
        self.model.preview()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GUI()
    app.run()
