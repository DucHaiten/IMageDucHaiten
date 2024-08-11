import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import queue
import hashlib
import shutil
from PIL import Image

# Global variables for controlling filtering and error handling
stop_event = threading.Event()
error_messages = []
error_window = None
filtered_hashes = set()
selected_files = []
worker_thread = None

def open_image_filter():
    global error_messages, error_window, filtered_hashes, selected_files
    global save_dir_var, status_var, num_files_var, errors_var, thread_count_var, progress
    global q, format_filter_var, filter_duplicate_var, min_size_var, max_size_var
    global min_total_resolution_var, max_total_resolution_var, format_mode_var, format_filter_label
    global delete_originals_var, worker_thread, root, stop_button, saved_files

    # Create the Tkinter window
    root = tk.Tk()
    root.title("Image Filter")

    # Initialize Tkinter variables
    save_dir_var = tk.StringVar()
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    thread_count_var = tk.StringVar(value="4")
    progress = tk.IntVar()
    q = queue.Queue()
    format_filter_var = tk.StringVar()
    filter_duplicate_var = tk.BooleanVar()
    min_size_var = tk.IntVar()
    max_size_var = tk.IntVar()
    min_total_resolution_var = tk.IntVar()
    max_total_resolution_var = tk.IntVar()
    format_mode_var = tk.StringVar(value="exclude")  # 'include' or 'exclude'

    # Initialize variable for deleting original images
    delete_originals_var = tk.BooleanVar()

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

    def hash_image(file_path):
        """Create SHA-256 hash of image content."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        except Exception as e:
            error_messages.append(f"Error hashing file {file_path}: {e}")
            update_error_count()
            return None
        return hash_sha256.hexdigest()

    def filter_duplicate_images(filepaths):
        unique_images = {}
        filtered_files = []
        for filepath in filepaths:
            image_hash = hash_image(filepath)
            if image_hash and image_hash not in filtered_hashes:
                unique_images[image_hash] = filepath
                filtered_hashes.add(image_hash)
            else:
                filtered_files.append(filepath)  # Duplicate images will be added to the list
        return filtered_files

    def parse_formats(format_string):
        return [fmt.strip().lower() for fmt in format_string.split(',') if fmt.strip()]

    def filter_image_formats(filepaths, include_formats):
        filtered_files = []
        formats = parse_formats(format_filter_var.get())
        if not formats:
            return filepaths  # No filtering if the format list is empty

        for filepath in filepaths:
            ext = os.path.splitext(filepath)[1][1:].lower()  # Get the file extension
            if (ext in formats) == include_formats:
                filtered_files.append(filepath)
        return filtered_files

    def filter_image_size(filepaths, min_size, max_size):
        filtered_files = []
        for filepath in filepaths:
            size = os.path.getsize(filepath)
            if (min_size <= 0 or size >= min_size) and (max_size <= 0 or size <= max_size):
                filtered_files.append(filepath)
        return filtered_files

    def filter_image_resolution(filepaths, min_total_resolution, max_total_resolution):
        filtered_files = []
        for filepath in filepaths:
            try:
                image = Image.open(filepath)
                width, height = image.size
                total_resolution = width + height
                if (min_total_resolution <= 0 or total_resolution >= min_total_resolution) and \
                   (max_total_resolution <= 0 or total_resolution <= max_total_resolution):
                    filtered_files.append(filepath)
            except Exception as e:
                error_messages.append(f"Error reading image {filepath}: {e}")
                update_error_count()
                continue
        return filtered_files

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

    def delete_original_images():
        """Delete the original images if delete_originals_var is set."""
        if delete_originals_var.get():
            # Iterate through a copy of selected_files to avoid modifying the list during iteration
            for filepath in selected_files[:]:
                try:
                    os.remove(filepath)
                    selected_files.remove(filepath)  # Remove from selected_files if deleted
                except FileNotFoundError:
                    error_messages.append(f"File not found for deletion: {filepath}")
                    update_error_count()
                except Exception as e:
                    error_messages.append(f"Error deleting file {filepath}: {e}")
                    update_error_count()
            update_selected_files_label()

    def update_selected_files_label():
        """Update the label showing the number of selected files."""
        num_files_var.set(f"{len(selected_files)} files selected.")

    def update_error_count():
        """Update the error count displayed in the Errors button."""
        errors_var.set(f"Errors: {len(error_messages)}")

    def check_all_files_filtered(filtered_files, filter_type):
        """Check if all files have been filtered out and display a specific error message."""
        if not filtered_files:
            error_message = f"All images would be filtered out by the selected {filter_type} filter. Please adjust the filter settings."
            messagebox.showerror("Filtering Error", error_message)
            return True
        return False

    def filter_images_preview(filepaths):
        """
        Preview the number of images left after applying the filters.
        Return the count of images left after filtering.
        """
        filtered_files = filepaths[:]

        # Preview filtering by image format
        include_formats = format_mode_var.get() == "include"
        filtered_files = filter_image_formats(filtered_files, include_formats)

        # Preview filtering by image size
        filtered_files = filter_image_size(filtered_files, min_size_var.get(), max_size_var.get())

        # Preview filtering by total resolution
        filtered_files = filter_image_resolution(filtered_files, min_total_resolution_var.get(), max_total_resolution_var.get())

        # Preview filtering duplicates if selected
        if filter_duplicate_var.get():
            filtered_files = filter_duplicate_images(filtered_files)

        return len(filtered_files)

    def filter_images(save_directory):
        global saved_files
        saved_files = set()  # Initialize saved_files set
        num_initial_files = 0  # Initialize before try-except block
        try:
            num_initial_files = len(selected_files)
            filtered_files = selected_files[:]

            # Filter by image format
            include_formats = format_mode_var.get() == "include"
            filtered_files = filter_image_formats(filtered_files, include_formats)
            if check_all_files_filtered(filtered_files, "format"):
                return [], num_initial_files, 0, 0

            # Filter by image size
            filtered_files = filter_image_size(filtered_files, min_size_var.get(), max_size_var.get())
            if check_all_files_filtered(filtered_files, "size"):
                return [], num_initial_files, 0, 0

            # Filter by total resolution
            filtered_files = filter_image_resolution(filtered_files, min_total_resolution_var.get(), max_total_resolution_var.get())
            if check_all_files_filtered(filtered_files, "resolution"):
                return [], num_initial_files, 0, 0

            # Filter duplicates if selected
            if filter_duplicate_var.get():
                filtered_files = filter_duplicate_images(filtered_files)
                if check_all_files_filtered(filtered_files, "duplicate"):
                    return [], num_initial_files, 0, 0

            # Calculate the number of filtered out images
            num_filtered_files = len(filtered_files)
            num_filtered_out_files = num_initial_files - num_filtered_files

            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            for file in filtered_files:
                save_file_with_unique_name(file, save_directory, saved_files)

            return filtered_files, num_initial_files, num_filtered_files, num_filtered_out_files

        except Exception as e:
            error_messages.append(str(e))
            update_error_count()
            return [], num_initial_files, 0, 0

    def worker(save_directory, num_threads, q):
        try:
            filtered_files, num_initial_files, num_filtered_files, num_filtered_out_files = filter_images(save_directory)
            if not filtered_files:  # Check again if any files left after filtering
                return  # Stop if no files left
            for i, file in enumerate(filtered_files):
                if stop_event.is_set():
                    break
                save_file_with_unique_name(file, save_directory, saved_files)
                progress.set(int((i + 1) / num_initial_files * 100))
                q.put((filtered_files, num_initial_files, num_filtered_files, num_filtered_out_files))
            q.put(None)
        except Exception as e:
            if not stop_event.is_set():
                error_messages.append(str(e))
                update_error_count()
                q.put(str(e))
        finally:
            stop_event.clear()  # Clear the stop event for the next run

    def update_progress():
        try:
            completed = 0
            while True:
                item = q.get()
                if item is None:
                    break
                if isinstance(item, tuple):
                    filtered_files, num_initial_files, num_filtered_files, num_filtered_out_files = item
                    completed += 1
                    progress.set(int((completed / num_initial_files) * 100))
                    root.after(0, root.update_idletasks)
                elif isinstance(item, str):
                    if "Error" in item:
                        error_messages.append(item)
                        root.after(0, update_error_count)
                        continue
            if not stop_event.is_set():
                root.after(0, progress.set(100))
                show_completion_message(num_initial_files, num_filtered_files, num_filtered_out_files)
                delete_original_images()  # Delete original images after completion
            # Re-enable all buttons after completion
            root.after(0, lambda: filter_button.config(state='normal'))
            root.after(0, lambda: select_directory_button.config(state='normal'))
            root.after(0, lambda: choose_dir_button.config(state='normal'))
            root.after(0, lambda: delete_originals_checkbox.config(state='normal'))
        except Exception as e:
            if not stop_event.is_set():
                error_messages.append(str(e))
                root.after(0, update_error_count)
                root.after(0, status_var.set, f"Error: {e}")

    def show_completion_message(num_initial_files, num_filtered_files, num_filtered_out_files):
        message = (
            f"Filtering complete.\n"
            f"Total files selected: {num_initial_files}\n"
            f"Files processed and saved: {num_filtered_files}\n"
            f"Files filtered out: {num_filtered_out_files}\n"
            f"{len(error_messages)} errors occurred."
        )
        messagebox.showinfo("Filtering Complete", message)

    def filter_files():
        global error_messages, error_window, worker_thread
        stop_event.clear()  # Clear the stop event before starting a new task
        error_messages.clear()
        update_error_count()
        save_directory = save_dir_var.get()
        try:
            num_threads = int(thread_count_var.get() or 4)
            if num_threads <= 0:
                raise ValueError("Number of threads must be greater than 0.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid number of threads: {e}")
            return

        if not selected_files or not save_directory:
            status_var.set("Please select images and save location.")
            return

        # Preview filtered results
        remaining_images = filter_images_preview(selected_files)
        if remaining_images == 0:
            messagebox.showerror("Filtering Error", "No images will remain after applying the filters. Please adjust the filter settings.")
            return

        # Disable all buttons except Stop button
        filter_button.config(state='disabled')
        select_directory_button.config(state='disabled')
        choose_dir_button.config(state='disabled')
        delete_originals_checkbox.config(state='disabled')

        worker_thread = threading.Thread(target=worker, args=(save_directory, num_threads, q))
        worker_thread.start()
        threading.Thread(target=update_progress).start()

    def stop_filtering_func():
        stop_event.set()  # Signal the worker thread to stop
        status_var.set("Filtering stopped.")
        # Do not disable the Stop button to keep it always enabled
        # Re-enable all buttons
        filter_button.config(state='normal')
        select_directory_button.config(state='normal')
        choose_dir_button.config(state='normal')
        delete_originals_checkbox.config(state='normal')
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

    def toggle_format_mode():
        if format_mode_var.get() == "include":
            format_filter_label.config(text="Include Image Formats (comma-separated, e.g., png,jpg):")
        else:
            format_filter_label.config(text="Exclude Image Formats (comma-separated, e.g., png,jpg):")

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

    title_label = tk.Label(root, text="Image Filter", font=('Helvetica', 16))
    title_label.pack(pady=10)

    select_directory_button = tk.Button(root, text="Select Images", command=select_directory)
    select_directory_button.pack(pady=5)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    choose_dir_button = tk.Button(root, text="Choose Save Directory", command=choose_directory)
    choose_dir_button.pack(pady=5)

    save_dir_entry = tk.Entry(root, textvariable=save_dir_var, state='readonly', justify='center')
    save_dir_entry.pack(pady=5, fill=tk.X)

    # Checkbox to delete original images
    delete_originals_checkbox = tk.Checkbutton(root, text="Delete Original Images After Filtering", variable=delete_originals_var)
    delete_originals_checkbox.pack(pady=5)

    # Toggle image format filter mode
    format_mode_frame = tk.Frame(root)
    format_mode_frame.pack(pady=5)
    format_mode_label = tk.Label(format_mode_frame, text="Toggle Format Mode (Include/Exclude):")
    format_mode_label.pack(side="left")

    # Radio buttons
    include_radio = tk.Radiobutton(format_mode_frame, text="Include Formats", variable=format_mode_var, value="include", command=toggle_format_mode)
    include_radio.pack(side="left", padx=5)
    exclude_radio = tk.Radiobutton(format_mode_frame, text="Exclude Formats", variable=format_mode_var, value="exclude", command=toggle_format_mode)
    exclude_radio.pack(side="left")

    # Description for image format filter mode
    format_filter_label = tk.Label(root, text="Exclude Image Formats (comma-separated, e.g., png,jpg):")
    format_filter_label.pack(pady=5)

    format_filter_entry = tk.Entry(root, textvariable=format_filter_var, justify='center')
    format_filter_entry.pack(pady=5, fill=tk.X)

    min_size_label = tk.Label(root, text="Min Size (bytes):")
    min_size_label.pack(pady=5)

    min_size_entry = tk.Entry(root, textvariable=min_size_var, validate="key", validatecommand=(validate_command, '%P'), justify='center', width=8)
    min_size_entry.pack(pady=5)

    max_size_label = tk.Label(root, text="Max Size (bytes):")
    max_size_label.pack(pady=5)

    max_size_entry = tk.Entry(root, textvariable=max_size_var, validate="key", validatecommand=(validate_command, '%P'), justify='center', width=8)
    max_size_entry.pack(pady=5)

    min_resolution_label = tk.Label(root, text="Min Total Resolution (sum of width and height):")
    min_resolution_label.pack(pady=5)

    min_resolution_entry = tk.Entry(root, textvariable=min_total_resolution_var, validate="key", validatecommand=(validate_command, '%P'), justify='center', width=8)
    min_resolution_entry.pack(pady=5)

    max_resolution_label = tk.Label(root, text="Max Total Resolution (sum of width and height):")
    max_resolution_label.pack(pady=5)

    max_resolution_entry = tk.Entry(root, textvariable=max_total_resolution_var, validate="key", validatecommand=(validate_command, '%P'), justify='center', width=8)
    max_resolution_entry.pack(pady=5)

    # Add label and entry for thread count
    thread_count_label = tk.Label(root, text="Number of Threads:")
    thread_count_label.pack(pady=5)

    thread_count_entry = tk.Entry(root, textvariable=thread_count_var, validate="key", validatecommand=(validate_command, '%P'), justify='center', width=4)
    thread_count_entry.pack(pady=5)

    filter_duplicate_checkbox = tk.Checkbutton(root, text="Filter Duplicate Images", variable=filter_duplicate_var)
    filter_duplicate_checkbox.pack(pady=5)

    filter_button = tk.Button(root, text="Filter", command=filter_files)
    filter_button.pack(pady=10)

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
    open_image_filter()
