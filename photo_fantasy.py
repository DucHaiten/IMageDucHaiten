import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import queue
import shutil
import subprocess

# Global variables for controlling filtering and error handling
stop_event = threading.Event()
error_messages = []
error_window = None
selected_files = []
worker_thread = None

def open_photo_fantasy():
    global error_messages, error_window, selected_files
    global save_dir_var, status_var, num_files_var, errors_var, thread_count_var, progress
    global q, worker_thread, root, stop_button, saved_files

    # Create the Tkinter window
    root = tk.Tk()
    root.title("Photo Fantasy")

    # Initialize Tkinter variables
    save_dir_var = tk.StringVar()
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    thread_count_var = tk.StringVar(value="4")
    progress = tk.IntVar()
    q = queue.Queue()

    def center_window(window):
        window.update_idletasks()
        width = window.winfo_width() + 120  # Add 120 pixels to width
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def select_directory():
        filepaths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("All Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff")]
        )
        if filepaths:
            selected_files.clear()
            selected_files.extend(filepaths)
            update_selected_files_label()

    def choose_directory():
        directory = filedialog.askdirectory()
        if directory:
            save_dir_var.set(directory)
            save_dir_entry.config(state='normal')
            save_dir_entry.delete(0, tk.END)
            save_dir_entry.insert(0, directory)
            save_dir_entry.config(state='readonly')

    def save_file_with_unique_name(filepath, save_directory, saved_files):
        """Save file with a unique name to avoid overwriting."""
        if filepath in saved_files:
            return  # File already saved, do not save again
    
        base_name, ext = os.path.splitext(os.path.basename(filepath))
        save_path = os.path.join(save_directory, f"{base_name}{ext}")
        counter = 1
        while os.path.exists(save_path):
            save_path = os.path.join(save_directory, f"{base_name} ({counter}){ext}")
            counter += 1
        try:
            shutil.copy(filepath, save_path)
            saved_files.add(filepath)  # Mark this file as saved
        except Exception as e:
            error_messages.append(f"Error saving file {filepath}: {e}")
            update_error_count()

    def update_selected_files_label():
        """Update the label showing the number of selected files."""
        num_files_var.set(f"{len(selected_files)} files selected.")

    def update_error_count():
        """Update the error count displayed in the Errors button."""
        errors_var.set(f"Errors: {len(error_messages)}")

    def run_task(task_func):
        """Run the given task function in a separate thread."""
        global worker_thread
        stop_event.clear()
        disable_buttons()
        worker_thread = threading.Thread(target=task_func)
        worker_thread.start()
        root.after(100, check_thread)

    def check_thread():
        """Check if the worker thread is still running."""
        if worker_thread.is_alive():
            root.after(100, check_thread)
        else:
            enable_buttons()
            if stop_event.is_set():
                status_var.set("Task stopped.")
            else:
                status_var.set("Task completed.")

    def disable_buttons():
        """Disable all buttons except the stop button."""
        select_directory_button.config(state='disabled')
        choose_dir_button.config(state='disabled')
        auto_adjust_button.config(state='disabled')
        enhance_vivid_button.config(state='disabled')
        horror_theme_button.config(state='disabled')
        cinematic_theme_button.config(state='disabled')
        cyberpunk_theme_button.config(state='disabled')
        fairytale_theme_button.config(state='disabled')
        classic_vintage_button.config(state='disabled')
        dark_fantasy_button.config(state='disabled')
        stop_button.config(state='normal')

    def enable_buttons():
        """Enable all buttons."""
        select_directory_button.config(state='normal')
        choose_dir_button.config(state='normal')
        auto_adjust_button.config(state='normal')
        enhance_vivid_button.config(state='normal')
        horror_theme_button.config(state='normal')
        cinematic_theme_button.config(state='normal')
        cyberpunk_theme_button.config(state='normal')
        fairytale_theme_button.config(state='normal')
        classic_vintage_button.config(state='normal')
        dark_fantasy_button.config(state='normal')
        stop_button.config(state='normal')

    def process_images(process_func):
        global saved_files
        saved_files = set()  # Initialize saved_files set

        if not selected_files or not save_dir_var.get():
            messagebox.showerror("Input Error", "Please select images and a save directory.")
            enable_buttons()
            return

        save_directory = save_dir_var.get()
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        for file in selected_files:
            if stop_event.is_set():
                break

            base_name, ext = os.path.splitext(os.path.basename(file))
            save_path = os.path.join(save_directory, f"{base_name}{ext}")
            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(save_directory, f"{base_name} ({counter}){ext}")
                counter += 1

            try:
                process_func(file, save_path)
                saved_files.add(file)  # Mark this file as saved
            except subprocess.CalledProcessError as e:
                error_messages.append(f"Error processing file {file}: {e}")
                update_error_count()

        messagebox.showinfo("Processing Complete", f"Processed {len(saved_files)} files.")

    def auto_adjust_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file, 
                                                               '-enhance', 
                                                               '-contrast-stretch', '0.1x0.1%', 
                                                               '-sharpen', '0x1', 
                                                               save_path], check=True))

    def enhance_vivid_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file, 
                                                               '-enhance', 
                                                               '-contrast-stretch', '0.1x0.1%', 
                                                               '-sharpen', '0x1', 
                                                               '-modulate', '105,120,100', 
                                                               save_path], check=True))

    def horror_theme_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file, 
                                                               '-modulate', '100,90,100',
                                                               '-level', '-5%,95%', 
                                                               '-brightness-contrast', '1x1',
                                                               '-sigmoidal-contrast', '3x50%', 
                                                               '-noise', '3',
                                                               '-sharpen', '0x1.5', 
                                                               '(', '+clone', '-fill', 'black', '-colorize', '5%', ')', 
                                                               '-compose', 'multiply', '-flatten', 
                                                               save_path], check=True))

    def cinematic_theme_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file,
                                                               '-level', '-5%,95%', 
                                                               '-modulate', '100,150,100',
                                                               '-colorize', '0,5,0',   
                                                               '-brightness-contrast', '5x-0',
                                                               '-sigmoidal-contrast', '3x50%', 
                                                               '-sharpen', '0x1.5', 
                                                               '-noise', '0.1', 
                                                               '(', '+clone', '-blur', '0x1', ')', 
                                                               '-compose', 'blend', '-define', 'compose:args=10', '-composite', 
                                                               '(', '+clone', '-fill', 'black', '-colorize', '10%', ')', 
                                                               '-compose', 'multiply', '-flatten', 
                                                               save_path], check=True))

    def cyberpunk_theme_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file,
                                                               '-modulate', '100,130,100',
                                                               '-level', '-5%,95%', 
                                                               '-colorize', '10,0,20', 
                                                               '-brightness-contrast', '1x1',
                                                               '-sigmoidal-contrast', '3x50%', 
                                                               '-sharpen', '0x0.5', 
                                                               '-noise', '0.5', 
                                                               '(', '+clone', '-blur', '0x2', ')', 
                                                               '-compose', 'blend', '-define', 'compose:args=20', '-composite',
                                                               '(', '+clone', '-fill', 'black', '-colorize', '10%', ')', 
                                                               '-compose', 'multiply', '-flatten',
                                                               save_path], check=True))

    def fairytale_theme_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file,
                                                               '-modulate', '100,120,100', 
                                                               '-blur', '0x1.2', 
                                                               '-brightness-contrast', '2x-1', 
                                                               '(', '+clone', '-alpha', 'extract', '-virtual-pixel', 'black',
                                                               '-blur', '0x15', '-shade', '120x45', ')', 
                                                               '-compose', 'softlight', '-composite',
                                                               save_path], check=True))

    def classic_vintage_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file,
                                                               '-modulate', '110,80,100', 
                                                               '-fill', '#704214', '-colorize', '10%', 
                                                               '-attenuate', '0.3', '+noise', 'Multiplicative', 
                                                               '-blur', '0x1.2',
                                                               '-level', '5%,90%', 
                                                               '-unsharp', '0x5',
                                                               '-colorspace', 'sRGB',
                                                               '-brightness-contrast', '-5x15',
                                                               save_path], check=True))

    def dark_fantasy_images():
        process_images(lambda file, save_path: subprocess.run(['magick', 'convert', file,
                                                               '-modulate', '110,130,100', 
                                                               '-blur', '0x1', 
                                                               '-brightness-contrast', '5x-10', 
                                                               '-attenuate', '0.1', '+noise', 'Multiplicative', 
                                                               '-unsharp', '0x5',
                                                               '-level', '5%,95%', 
                                                               '-modulate', '105,125,100', 
                                                               '-brightness-contrast', '0x1', 
                                                               '(', '+clone', '-fill', 'black', '-colorize', '10%', ')', 
                                                               '-compose', 'multiply', '-flatten',
                                                               '-colorspace', 'sRGB',
                                                               save_path], check=True))

    def stop_filtering_func():
        stop_event.set()  # Signal the worker thread to stop
        status_var.set("Filtering stopped.")
        # Do not disable the Stop button to keep it always enabled
        # Re-enable all buttons
        enable_buttons()
        if worker_thread is not None:
            worker_thread.join()  # Wait for worker thread to finish

    def return_to_menu():
        stop_filtering_func()
        root.destroy()
        # Import main menu and open it
        from main import open_main_menu
        open_main_menu()

    def on_closing():
        stop_filtering_func()
        return_to_menu()

    def show_errors():
        global error_window
        if error_window is not None:
            return

        error_window = tk.Toplevel(root)
        error_window.title("Error Details")
        error_window.geometry("500x400")

        error_text = tk.Text(error_window, wrap='word')
        error_text.pack(expand=True, fill='both')

        if error_messages:
            for error in error_messages:
                error_text.insert('end', error + '\n')
        else:
            error_text.insert('end', "No errors recorded.")

        error_text.config(state='disabled')

        def on_close_error_window():
            global error_window
            error_window.destroy()
            error_window = None

        error_window.protocol("WM_DELETE_WINDOW", on_close_error_window)

    def validate_number(P):
        if P.isdigit() or P == "":
            return True
        else:
            messagebox.showerror("Input Error", "Please enter only numbers.")
            return False

    validate_command = root.register(validate_number)

    # Create UI elements
    back_button = tk.Button(root, text="<-", font=('Helvetica', 14), command=return_to_menu)
    back_button.pack(anchor='nw', padx=10, pady=10)

    title_label = tk.Label(root, text="Photo Fantasy", font=('Helvetica', 16))
    title_label.pack(pady=10)

    select_directory_button = tk.Button(root, text="Select Images", command=select_directory)
    select_directory_button.pack(pady=5)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    choose_dir_button = tk.Button(root, text="Choose Save Directory", command=choose_directory)
    choose_dir_button.pack(pady=5)

    save_dir_entry = tk.Entry(root, textvariable=save_dir_var, state='readonly', justify='center')
    save_dir_entry.pack(pady=5, fill=tk.X)

    # Add Auto Adjust button
    auto_adjust_button = tk.Button(root, text="Auto Adjust Images", command=lambda: run_task(auto_adjust_images))
    auto_adjust_button.pack(pady=10)

    # Add Enhance Vivid button
    enhance_vivid_button = tk.Button(root, text="Enhance Vivid Images", command=lambda: run_task(enhance_vivid_images))
    enhance_vivid_button.pack(pady=10)

    # Add Horror Theme button
    horror_theme_button = tk.Button(root, text="Horror Theme Images", command=lambda: run_task(horror_theme_images))
    horror_theme_button.pack(pady=10)

    # Add Cinematic Theme button
    cinematic_theme_button = tk.Button(root, text="Cinematic Theme Images", command=lambda: run_task(cinematic_theme_images))
    cinematic_theme_button.pack(pady=10)

    # Add Cyberpunk Theme button
    cyberpunk_theme_button = tk.Button(root, text="Cyberpunk Theme Images", command=lambda: run_task(cyberpunk_theme_images))
    cyberpunk_theme_button.pack(pady=10)

    # Add Fairytale Theme button
    fairytale_theme_button = tk.Button(root, text="Fairytale Theme Images", command=lambda: run_task(fairytale_theme_images))
    fairytale_theme_button.pack(pady=10)

    # Add Classic Vintage button
    classic_vintage_button = tk.Button(root, text="Classic Vintage Images", command=lambda: run_task(classic_vintage_images))
    classic_vintage_button.pack(pady=10)

    # Add Dark Fantasy button
    dark_fantasy_button = tk.Button(root, text="Dark Fantasy Images", command=lambda: run_task(dark_fantasy_images))
    dark_fantasy_button.pack(pady=10)

    # Add label and entry for thread count
    thread_count_label = tk.Label(root, text="Number of Threads:")
    thread_count_label.pack(pady=5)

    thread_count_entry = tk.Entry(root, textvariable=thread_count_var, validate="key", validatecommand=(validate_command, '%P'), justify='center', width=4)
    thread_count_entry.pack(pady=5)

    stop_button = tk.Button(root, text="Stop", command=stop_filtering_func)  # Ensure stop button is a global variable
    stop_button.pack(pady=5)

    errors_button = tk.Button(root, textvariable=errors_var, command=show_errors)
    errors_button.pack(pady=5)

    progress_bar = ttk.Progressbar(root, variable=progress, maximum=100)
    progress_bar.pack(pady=5, fill=tk.X)

    status_label = tk.Label(root, textvariable=status_var, fg="green")
    status_label.pack(pady=5)

    center_window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    open_photo_fantasy()
