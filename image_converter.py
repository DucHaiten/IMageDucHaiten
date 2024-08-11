import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image as PILImage, ImageTk
from wand.image import Image
import os
import queue
import hashlib
import threading
import subprocess

# Biến toàn cục để điều khiển việc dừng và lưu lỗi
stop_conversion = False
error_messages = []
selected_files = []
converted_hashes = set()
save_directory = ""

def open_image_converter():
    global stop_conversion, error_messages, selected_files, save_dir_var, format_var, status_var, num_files_var, errors_var, thread_count_var, filename_var, filter_var, progress, q, root

    # Tạo cửa sổ Tkinter
    root = tk.Tk()
    root.title("Image Converter")

    # Khởi tạo các biến Tkinter
    save_dir_var = tk.StringVar()
    format_var = tk.StringVar(value='png')
    status_var = tk.StringVar()
    num_files_var = tk.StringVar(value="0 files selected.")
    errors_var = tk.StringVar(value="Errors: 0")
    thread_count_var = tk.StringVar(value="4")
    filename_var = tk.StringVar()
    filter_var = tk.BooleanVar(value=False)
    progress = tk.IntVar(value=0)
    q = queue.Queue()

    # Định nghĩa các định dạng được hỗ trợ
    SUPPORTED_TO_PS = ['pdf', 'jpeg', 'jpg', 'tiff', 'pnm']
    SUPPORTED_TO_EPS = ['pdf', 'jpeg', 'jpg', 'tiff', 'pnm']
    NEEDS_INTERMEDIATE_CONVERSION = {
        'psd': 'pdf', 'svg': 'pdf', 'png': 'pdf',
        'bmp': 'pdf', 'gif': 'pdf', 'ico': 'png'
    }

    # Các hàm trợ giúp
    def center_window(window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def select_files():
        filepaths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("All Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff;*.tif;*.svg;*.webp;*.pdf;*.psd;*.ico"),
                       ("JPEG files", "*.jpg;*.jpeg"),
                       ("PNG files", "*.png"),
                       ("GIF files", "*.gif"),
                       ("BMP files", "*.bmp"),
                       ("TIFF files", "*.tiff;*.tif"),
                       ("SVG files", "*.svg"),
                       ("WEBP files", "*.webp"),
                       ("PDF files", "*.pdf"),
                       ("PSD files", "*.psd"),
                       ("ICO files", "*.ico")]
        )
        if filepaths:
            selected_files.clear()
            selected_files.extend(filepaths)
            num_files_var.set(f"{len(selected_files)} files selected.")
            update_image_preview()

    def choose_save_directory():
        global save_directory
        directory = filedialog.askdirectory()
        if directory:
            save_directory = directory
            save_dir_var.set(directory)
            save_dir_entry.config(state='normal')
            save_dir_entry.delete(0, tk.END)
            save_dir_entry.insert(0, directory)
            save_dir_entry.config(state='readonly')

    def hash_image(file_path):
        """Tạo hàm băm SHA-256 từ nội dung ảnh."""
        hash_sha256 = hashlib.sha256()
        try:
            file_path = os.path.normpath(file_path)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        except Exception as e:
            print(f"Error hashing file {file_path}: {e}")
            return None
        return hash_sha256.hexdigest()

    def filter_duplicate_images(filepaths):
        unique_images = {}
        filtered_files = []
        for filepath in filepaths:
            image_hash = hash_image(filepath)
            if image_hash and image_hash not in unique_images:
                if image_hash not in converted_hashes:
                    unique_images[image_hash] = filepath
                    filtered_files.append(filepath)
        return filtered_files

    def can_convert_directly(input_format, output_format):
        """Kiểm tra xem có thể chuyển đổi trực tiếp từ định dạng nguồn sang định dạng đích không."""
        if output_format == 'ps':
            return input_format in SUPPORTED_TO_PS
        elif output_format == 'eps':
            return input_format in SUPPORTED_TO_EPS
        elif output_format == 'ico':
            return input_format not in ['ps', 'eps', 'pdf']
        elif input_format == 'ico':
            return output_format not in ['ps', 'eps']
        return True

    def notify_conversion_path(input_format, output_format):
        """Hiển thị thông báo nhắc nhở người dùng về bước chuyển đổi trung gian cần thiết."""
        intermediate_format = NEEDS_INTERMEDIATE_CONVERSION.get(input_format, None)
        if intermediate_format:
            if output_format in ['ps', 'eps']:
                message = (f"Cannot convert directly from {input_format.upper()} to {output_format.upper()}. "
                           f"Please convert to PDF first, then convert to {output_format.upper()}.")
            else:
                message = (f"Cannot convert directly from {input_format.upper()} to {output_format.upper()}. "
                           f"Please convert to {intermediate_format.upper()} first, then convert to {output_format.upper()}.")
        else:
            message = (f"Conversion from {input_format.upper()} to {output_format.upper()} is not supported. "
                       "Please use a different format for conversion.")
        messagebox.showwarning("Conversion Notice", message)

    def convert_image_with_wand(input_path, output_format, output_path):
        """Chuyển đổi ảnh sử dụng ImageMagick thông qua Wand."""
        try:
            with Image(filename=input_path) as img:
                img.format = output_format
                img.save(filename=output_path)
        except Exception as e:
            raise RuntimeError(f"Error converting {input_path} to {output_format}: {e}")

    def convert_image_with_ghostscript(input_path, output_format, output_path):
        """Chuyển đổi ảnh sử dụng Ghostscript."""
        try:
            gs_command = [
                "gswin64c",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=" + ("ps2write" if output_format == "ps" else "eps2write"),
                f"-sOutputFile={output_path}",
                input_path
            ]
            subprocess.run(gs_command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ghostscript error: {e}")

    def convert_image(input_path, save_directory, output_format, output_filename, q):
        if stop_conversion:
            return

        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        ext = ext[1:].lower()
        original_name = name

        try:
            if output_filename:
                name = output_filename

            output_path = os.path.join(save_directory, f"{name}.{output_format}")

            counter = 1
            while os.path.exists(output_path):
                new_name = f"{name} ({counter})"
                output_path = os.path.join(save_directory, f"{new_name}.{output_format}")
                counter += 1

            if ext in NEEDS_INTERMEDIATE_CONVERSION and output_format in ["ps", "eps"]:
                intermediate_format = NEEDS_INTERMEDIATE_CONVERSION[ext]
                intermediate_path = os.path.join(save_directory, f"{name}.{intermediate_format}")

                # Chuyển đổi sang định dạng trung gian
                convert_image_with_wand(input_path, intermediate_format, intermediate_path)

                # Chuyển đổi từ định dạng trung gian sang định dạng cuối
                if output_format in ["ps", "eps"]:
                    convert_image_with_ghostscript(intermediate_path, output_format, output_path)
                else:
                    convert_image_with_wand(intermediate_path, output_format, output_path)

                os.remove(intermediate_path)
            else:
                if output_format in ["ps", "eps"]:
                    convert_image_with_ghostscript(input_path, output_format, output_path)
                else:
                    convert_image_with_wand(input_path, output_format, output_path)
                
            q.put(input_path)
            converted_hashes.add(hash_image(output_path))
        except Exception as e:
            error_message = f"Error converting {filename}: {str(e)}"
            q.put(error_message)
            error_messages.append(error_message)

    def worker(save_directory, output_format, num_threads, output_filename, q, filter_duplicates):
        try:
            total_files = selected_files
            if filter_duplicates:
                total_files = filter_duplicate_images(selected_files)
            progress.set(0)
            for i, input_path in enumerate(total_files, 1):
                if stop_conversion:
                    break
                input_format = os.path.splitext(input_path)[1][1:].lower()
                if not can_convert_directly(input_format, output_format):
                    notify_conversion_path(input_format, output_format)
                    q.put(None)
                    return

                thread = threading.Thread(target=convert_image, args=(input_path, save_directory, output_format, output_filename, q))
                thread.start()
                thread.join()

            q.put(None)
        except Exception as e:
            if not stop_conversion:
                q.put(e)

    def update_progress():
        try:
            completed = 0
            while True:
                item = q.get()
                if item is None:
                    break
                if isinstance(item, str):
                    if "Error" in item:
                        root.after(0, errors_var.set, f"Errors: {len(error_messages)}")
                        continue
                completed += 1
                progress.set(int((completed / len(selected_files)) * 100))
                if not stop_conversion:
                    root.after(0, status_var.set, f"Converted {completed} files")
                    root.after(0, root.update_idletasks)
            if not stop_conversion:
                root.after(0, progress.set, 100)
                show_completion_message(completed)
        except Exception as e:
            if not stop_conversion:
                root.after(0, status_var.set, f"Error: {e}")

    def show_completion_message(completed):
        message = f"Conversion complete. {completed} files converted."
        if error_messages:
            message += f" {len(error_messages)} errors occurred."
        messagebox.showinfo("Conversion Complete", message)

    def convert_files():
        global stop_conversion, error_messages
        stop_conversion = False
        error_messages.clear()
        errors_var.set("Errors: 0")
        save_directory = save_dir_var.get()
        output_format = format_var.get()
        try:
            num_threads = int(thread_count_var.get() or 4)
        except ValueError:
            messagebox.showerror("Input Error", "Threads must be a number.")
            return
        output_filename = filename_var.get()
        filter_duplicates = filter_var.get()
        if not selected_files or not save_directory or not output_format:
            status_var.set("Please select images, output format, and save location.")
            return

        threading.Thread(target=worker, args=(save_directory, output_format, num_threads, output_filename, q, filter_duplicates)).start()
        threading.Thread(target=update_progress).start()

    def stop_conversion_func():
        global stop_conversion
        stop_conversion = True
        status_var.set("Conversion stopped.")

    def return_to_menu():
        stop_conversion_func()
        root.destroy()
        import main
        main.open_main_menu()

    def on_closing():
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

    def update_image_preview():
        for widget in image_preview_frame.winfo_children():
            widget.destroy()

        for i, file_path in enumerate(selected_files):
            thumbnail_size = (100, 100)
            try:
                image = PILImage.open(file_path)
                image.thumbnail(thumbnail_size)
                thumbnail = ImageTk.PhotoImage(image)

                tk.Label(image_preview_frame, image=thumbnail).grid(row=i, column=0, padx=5, pady=5)
                tk.Label(image_preview_frame, text=os.path.basename(file_path)).grid(row=i, column=1, padx=5, pady=5)
                tk.Label(image_preview_frame, text="Caption placeholder", wraplength=300).grid(row=i, column=2, padx=5, pady=5)
            except Exception as e:
                tk.Label(image_preview_frame, text="Error loading image").grid(row=i, column=0, columnspan=3, padx=5, pady=5)

    def validate_number(P):
        if P.isdigit() or P == "":
            return True
        else:
            messagebox.showerror("Input Error", "Please enter only numbers.")
            return False

    validate_command = root.register(validate_number)

    # Tạo các thành phần giao diện
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    control_frame = tk.Frame(main_frame)
    control_frame.pack(fill=tk.X, padx=10, pady=10)

    back_button = tk.Button(control_frame, text="<-", font=('Helvetica', 14), command=return_to_menu)
    back_button.pack(side=tk.TOP, anchor='w', padx=5, pady=5)

    title_label = tk.Label(control_frame, text="Image Converter", font=('Helvetica', 16))
    title_label.pack(side=tk.TOP, padx=5, pady=5)

    select_button = tk.Button(control_frame, text="Select Files", command=select_files)
    select_button.pack(side=tk.TOP, padx=5, pady=5)

    num_files_label = tk.Label(control_frame, textvariable=num_files_var)
    num_files_label.pack(side=tk.TOP, padx=5, pady=5)

    save_dir_button = tk.Button(control_frame, text="Choose Save Directory", command=choose_save_directory)
    save_dir_button.pack(side=tk.TOP, padx=5, pady=5)

    save_dir_entry = tk.Entry(control_frame, textvariable=save_dir_var, state='readonly', justify='center')
    save_dir_entry.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)

    format_frame = tk.Frame(main_frame)
    format_frame.pack(fill=tk.X, padx=10, pady=5)

    format_label = tk.Label(format_frame, text="Output Format:")
    format_label.pack(side=tk.LEFT, padx=5)

    format_dropdown = ttk.Combobox(format_frame, textvariable=format_var, values=['png', 'jpg', 'gif', 'bmp', 'tiff', 'svg', 'webp', 'pdf', 'psd', 'ps', 'eps', 'ico'])
    format_dropdown.pack(side=tk.LEFT, padx=5)

    thread_count_label = tk.Label(format_frame, text="Threads:")
    thread_count_label.pack(side=tk.LEFT, padx=5)

    thread_count_entry = tk.Entry(format_frame, textvariable=thread_count_var, width=5, validate="key", validatecommand=(validate_command, '%P'), justify='center')
    thread_count_entry.pack(side=tk.LEFT, padx=5)

    filename_label = tk.Label(main_frame, text="Output Filename (optional):")
    filename_label.pack(fill=tk.X, padx=10, pady=5)

    filename_entry = tk.Entry(main_frame, textvariable=filename_var, justify='center')
    filename_entry.pack(fill=tk.X, padx=10, pady=5)

    filter_frame = tk.Frame(main_frame)
    filter_frame.pack(fill=tk.X, padx=10, pady=5)

    filter_checkbox = tk.Checkbutton(filter_frame, text="Filter duplicate images", variable=filter_var)
    filter_checkbox.pack(side=tk.LEFT)

    convert_button = tk.Button(main_frame, text="Convert", command=convert_files)
    convert_button.pack(pady=10)

    stop_button = tk.Button(main_frame, text="Stop", command=stop_conversion_func)
    stop_button.pack(pady=5)

    errors_button = tk.Button(main_frame, textvariable=errors_var, command=show_errors)
    errors_button.pack(pady=5)

    progress_bar = ttk.Progressbar(main_frame, variable=progress, maximum=100)
    progress_bar.pack(pady=5, fill=tk.X)

    status_label = tk.Label(main_frame, textvariable=status_var, fg="green")
    status_label.pack(pady=5)

    # Khung hiển thị ảnh và caption
    image_preview_frame = tk.Frame(root)
    image_preview_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    center_window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    open_image_converter()
