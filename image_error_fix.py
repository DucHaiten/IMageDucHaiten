import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading, queue
from PIL import Image, UnidentifiedImageError

# Global variables for managing state and errors
stop_processing = False
error_messages = []
selected_files = []
error_list = []

def open_image_error_fix():
    global stop_processing, error_messages, selected_files, status_var, num_files_var, errors_var, progress, q, error_list, error_window, thread_count_var

    # Initialize the main Tkinter window
    root = tk.Tk()
    root.title("Image Error Fix")

    # Initialize Tkinter variables
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    progress = tk.IntVar()
    thread_count_var = tk.StringVar(value="4")  # Default thread count
    q = queue.Queue()

    def center_window(window):
        window.update_idletasks()
        width = window.winfo_width() + 120
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def validate_number(P):
        return P.isdigit() or P == ""

    def validate_thread_count(var):
        value = var.get()
        if value != "":
            try:
                int_value = int(value)
                if int_value <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number of threads.")
                var.set("")

    def select_files():
        global selected_files
        filetypes = [
            ("All Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff;*.tif;*.svg;*.webp"),
            ("JPEG files", "*.jpg;*.jpeg"),
            ("PNG files", "*.png"),
            ("GIF files", "*.gif"),
            ("BMP files", "*.bmp"),
            ("TIFF files", "*.tiff;*.tif"),
            ("SVG files", "*.svg"),
            ("WEBP files", "*.webp")
        ]
        filepaths = filedialog.askopenfilenames(title="Select Image Files", filetypes=filetypes)
        if filepaths:
            selected_files.clear()
            selected_files.extend(filepaths)
            num_files_var.set(f"{len(selected_files)} files selected.")

    def detect_errors(file_path):
        """Detect potential errors in an image file."""
        errors = []
        if not os.access(file_path, os.R_OK):
            errors.append("Permission Denied")
        # Additional error checks
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify the image integrity
                img = Image.open(file_path)
                img.load()  # Load the image data to ensure it's not truncated
        except UnidentifiedImageError:
            errors.append("Unidentified image format or corrupted file")
        except IOError as e:
            errors.append(f"IOError: {str(e)}")
        except Exception as e:
            errors.append(f"Unknown error: {str(e)}")
        return errors

    def fix_error(file_path, error_type):
        """Fix errors in an image file, if possible."""
        if error_type == "Permission Denied":
            # Attempt to change permissions
            try:
                os.chmod(file_path, 0o644)
                return "Permissions fixed. File permissions were successfully updated."
            except Exception as e:
                return f"Failed to fix permissions. Ensure you have the necessary permissions to modify this file. Error: {str(e)}"
        elif error_type == "Unidentified image format or corrupted file":
            return "The file format is unrecognized or the file is corrupted. Please try to re-download or restore from a backup."
        elif error_type == "Invalid Format":
            return ("Cannot automatically fix invalid formats. Ensure the file extension matches the file content.\n"
                    "To fix this issue, please follow these steps:\n"
                    "1. Identify the correct file format by using a file type checker tool (e.g., CheckFileType.com).\n"
                    "2. Rename the file with the correct extension:\n"
                    "   - Right-click on the file and select 'Rename'.\n"
                    "   - Change the file extension to the correct format (e.g., .jpg, .png).\n"
                    "   - Press Enter to save the changes.\n"
                    "3. Try opening the file again. If the problem persists, the file may be corrupted or contain unsupported data.")
        elif error_type == "File Not Found":
            return ("The file could not be found at the specified path. Please ensure that the file has not been moved or deleted.\n"
                    "1. Verify the file path is correct.\n"
                    "2. If the file has been moved, update the path in the application or locate the file manually.\n"
                    "3. If the file was deleted, check your Recycle Bin or use a data recovery tool to attempt to restore it.")
        elif error_type == "File Path Too Long":
            return ("The file path exceeds the system limit. Windows has a maximum path length of 260 characters.\n"
                    "To fix this issue:\n"
                    "1. Move the file to a location with a shorter path, closer to the root directory (e.g., C:\\).\n"
                    "2. Rename folders in the path to shorter names.\n"
                    "3. Enable long path support in Windows if using Windows 10 (version 1607 hoặc cao hơn):\n"
                    "   - Open the Group Policy Editor (gpedit.msc).\n"
                    "   - Navigate to 'Local Computer Policy > Computer Configuration > Administrative Templates > System > Filesystem'.\n"
                    "   - Enable the 'Enable Win32 long paths' option.")
        elif error_type == "Transmission Errors":
            return ("The file may be incomplete or corrupted due to transmission errors. This can happen if the file was downloaded or transferred incorrectly.\n"
                    "To fix this issue:\n"
                    "1. Re-download hoặc re-transfer the file.\n"
                    "2. Use a reliable network connection to ensure the file is not corrupted during transfer.\n"
                    "3. Verify the integrity of the file by comparing checksums (if available).")
        elif error_type == "Unsupported Format":
            return ("The file format is not supported by this application. Supported formats include JPEG, PNG, GIF, BMP, TIFF, SVG, và WEBP.\n"
                    "To fix this issue:\n"
                    "1. Convert the file to a supported format using an image converter tool.\n"
                    "2. Ensure that the file is not corrupted and can be opened with other image viewers or editors.")
        else:
            return "No action taken. This error type is not recognized or cannot be fixed automatically."

    def delete_file(file_path):
        """Delete the specified file."""
        try:
            os.remove(file_path)
            # Remove from selected files
            selected_files.remove(file_path)
            num_files_var.set(f"{len(selected_files)} files selected.")
            return f"File {file_path} deleted successfully."
        except Exception as e:
            return f"Failed to delete file {file_path}. Error: {str(e)}"

    def process_image(file_path, q):
        if stop_processing:
            return

        errors = detect_errors(file_path)
        if errors:
            q.put((file_path, errors))

    def worker():
        try:
            progress.set(0)
            total_files = len(selected_files)
            thread_count = int(thread_count_var.get())  # Get the number of threads
            for i, input_path in enumerate(selected_files, 1):
                if stop_processing:
                    break

                thread = threading.Thread(target=process_image, args=(input_path, q))
                thread.start()
                thread.join()

                # Update progress bar
                progress.set(int(i / total_files * 100))
            
            q.put(None)
        except Exception as e:
            if not stop_processing:
                q.put(e)

    def update_progress():
        try:
            global error_list
            error_list = []
            while True:
                item = q.get()
                if item is None:
                    break
                if isinstance(item, tuple):
                    error_list.append(item)

            if not error_list:
                messagebox.showinfo("No Errors Found", "No errors were detected in the selected images.")
            else:
                errors_var.set(f"Errors: {len(error_list)}")
                display_errors(error_list)
        except Exception as e:
            if not stop_processing:
                root.after(0, status_var.set, f"Error: {e}")

    def update_error_display():
        """Update the display of errors in the error window."""
        global error_list, frame
        # Clear all existing widgets in the frame
        for widget in frame.winfo_children():
            widget.destroy()

        # Repopulate the frame with updated error list
        for file_path, errors in error_list:
            for error in errors:
                frame_row = tk.Frame(frame)
                frame_row.pack(fill="x", pady=2)

                # Hiển thị đường dẫn đầy đủ và tự động xuống dòng
                file_label = tk.Label(frame_row, text=f"{file_path}: {error}", anchor="w", wraplength=500, justify='left')
                file_label.pack(side=tk.LEFT, fill="x", expand=True)

                delete_button = tk.Button(frame_row, text="Delete", command=lambda fp=file_path: delete_file_action(fp))
                delete_button.pack(side=tk.RIGHT)

                fix_button = tk.Button(frame_row, text="Fix", command=lambda fp=file_path, et=error: fix_error_action(fp, et))
                fix_button.pack(side=tk.RIGHT)

                # Thêm dấu phân cách giữa các lỗi
                separator = ttk.Separator(frame, orient='horizontal')
                separator.pack(fill='x', pady=5)

        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def display_errors(error_list):
        global error_window, canvas, frame
        # Create or raise the error window
        if 'error_window' in globals() and error_window.winfo_exists():
            error_window.lift()
        else:
            error_window = tk.Toplevel(root)
            error_window.title("Error Details")
            error_window.geometry("600x400")

            canvas = tk.Canvas(error_window)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar = tk.Scrollbar(error_window, command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            canvas.configure(yscrollcommand=scrollbar.set)

            frame = tk.Frame(canvas)
            canvas.create_window((0, 0), window=frame, anchor="nw")

            update_error_display()

    def fix_error_action(file_path, error_type):
        fix_message = fix_error(file_path, error_type)
        messagebox.showinfo("Fix Error", fix_message)

    def delete_file_action(file_path):
        global error_list
        delete_message = delete_file(file_path)
        messagebox.showinfo("Delete File", delete_message)
        # Remove the error from the error_list and refresh the display
        error_list = [(fp, errs) for fp, errs in error_list if fp != file_path]
        errors_var.set(f"Errors: {len(error_list)}")
        update_error_display()

    def delete_all_errors():
        global error_list
        for file_path, _ in error_list:
            delete_file(file_path)
        error_list.clear()
        errors_var.set("Errors: 0")
        messagebox.showinfo("Delete All Files", "All files with errors have been deleted.")
        update_error_display()  # Update the error display after deleting all errors

    def scan_and_fix():
        global stop_processing, error_messages
        stop_processing = False
        error_messages.clear()
        errors_var.set("Errors: 0")
        if not selected_files:
            status_var.set("Please select images to scan.")
            return

        threading.Thread(target=worker).start()
        threading.Thread(target=update_progress).start()

    def stop_processing_func():
        global stop_processing
        stop_processing = True
        status_var.set("Processing stopped.")

    def return_to_menu():
        stop_processing_func()
        root.destroy()
        import main
        main.open_main_menu()

    def on_closing():
        return_to_menu()

    # Create GUI elements
    validate_command = root.register(validate_number)

    back_button = tk.Button(root, text="<-", font=('Helvetica', 14), command=return_to_menu)
    back_button.pack(anchor='nw', padx=10, pady=10)

    title_label = tk.Label(root, text="Image Error Fix", font=('Helvetica', 16))
    title_label.pack(pady=10)

    select_files_button = tk.Button(root, text="Select Files", command=select_files)
    select_files_button.pack(pady=5)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    thread_count_label = tk.Label(root, text="Number of Threads:")
    thread_count_label.pack(pady=5)

    thread_count_var = tk.StringVar(value="4")
    thread_count_entry = tk.Entry(root, textvariable=thread_count_var, width=3, justify='center', validate="key", validatecommand=(validate_command, '%P'))
    thread_count_entry.pack(pady=5)

    # Separator for aesthetics
    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x', pady=10)

    scan_fix_button = tk.Button(root, text="Scan and Fix", command=scan_and_fix)
    scan_fix_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop", command=stop_processing_func)
    stop_button.pack(pady=5)

    progress_bar = ttk.Progressbar(root, variable=progress, maximum=100)
    progress_bar.pack(pady=5, fill=tk.X)

    delete_all_label = tk.Label(root, text="Click 'Delete All' to remove all files with errors.")
    delete_all_label.pack(pady=5)

    delete_all_button = tk.Button(root, text="Delete All", command=delete_all_errors)
    delete_all_button.pack(pady=5)

    errors_label = tk.Label(root, textvariable=errors_var, fg="red")
    errors_label.pack(pady=5)

    status_label = tk.Label(root, textvariable=status_var, fg="green")
    status_label.pack(pady=5)

    center_window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    open_image_error_fix()
