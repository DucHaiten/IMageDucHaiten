import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from wand.image import Image as WandImage
import os
import threading
import queue

# Biến toàn cục để điều khiển việc dừng và lưu lỗi
stop_processing = False
error_messages = []
error_window = None
selected_files = []
save_directory = ""

def open_image_rotate_flip():
    global stop_processing, error_messages, error_window, selected_files, save_dir_var, status_var, num_files_var, errors_var, thread_count_var, progress, q, rotate_left_angle_var, rotate_right_angle_var

    # Tạo cửa sổ Tkinter
    root = tk.Tk()
    root.title("Image Rotate & Flip")

    # Khởi tạo các biến Tkinter
    save_dir_var = tk.StringVar()
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    thread_count_var = tk.StringVar(value="4")
    rotate_left_angle_var = tk.StringVar(value="90")
    rotate_right_angle_var = tk.StringVar(value="90")
    progress = tk.IntVar()
    q = queue.Queue()

    def center_window(window):
        window.update_idletasks()
        width = window.winfo_width() + 120
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

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

    def choose_directory():
        global save_directory
        directory = filedialog.askdirectory()
        if directory:
            save_directory = directory
            save_dir_var.set(directory)

    def rotate_image(input_path, angle, output_path):
        """Xoay ảnh sử dụng ImageMagick thông qua Wand."""
        try:
            with WandImage(filename=input_path) as img:
                img.rotate(angle)
                img.save(filename=output_path)
        except Exception as e:
            raise RuntimeError(f"Error rotating image: {e}")

    def flip_image(input_path, direction, output_path):
        """Lật ảnh sử dụng ImageMagick thông qua Wand."""
        try:
            with WandImage(filename=input_path) as img:
                if direction == "horizontal":
                    img.flip()
                elif direction == "vertical":
                    img.flop()
                img.save(filename=output_path)
        except Exception as e:
            raise RuntimeError(f"Error flipping image: {e}")

    def process_image(input_path, save_directory, operation, angle, q):
        if stop_processing:
            return

        filename = os.path.basename(input_path)
        try:
            output_path = os.path.join(save_directory, filename)
            if operation == "rotate_left":
                rotate_image(input_path, -angle, output_path)
            elif operation == "rotate_right":
                rotate_image(input_path, angle, output_path)
            elif operation == "flip_horizontal":
                flip_image(input_path, "horizontal", output_path)
            elif operation == "flip_vertical":
                flip_image(input_path, "vertical", output_path)

            q.put(input_path)
        except Exception as e:
            error_message = f"Error processing {filename}: {str(e)}"
            q.put(error_message)
            error_messages.append(error_message)

    def worker(save_directory, operation, num_threads, angle):
        try:
            progress.set(0)
            for i, input_path in enumerate(selected_files, 1):
                if stop_processing:
                    break

                thread = threading.Thread(target=process_image, args=(input_path, save_directory, operation, angle, q))
                thread.start()
                thread.join()

            q.put(None)
        except Exception as e:
            if not stop_processing:
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
                if not stop_processing:
                    root.after(0, status_var.set, f"Processed {completed} files")
                    root.after(0, root.update_idletasks)
            if not stop_processing:
                root.after(0, progress.set(100))
                show_completion_message(completed)
        except Exception as e:
            if not stop_processing:
                root.after(0, status_var.set, f"Error: {e}")

    def show_completion_message(completed):
        message = f"Processing complete. {completed} files processed."
        if error_messages:
            message += f" {len(error_messages)} errors occurred."
        messagebox.showinfo("Process Complete", message)

    def process_files(operation):
        global stop_processing, error_messages
        stop_processing = False
        error_messages.clear()
        errors_var.set("Errors: 0")
        if not selected_files or not save_directory:
            status_var.set("Please select images and save location.")
            return

        num_threads = int(thread_count_var.get() or 4)
        if operation in ["rotate_left", "rotate_right"]:
            angle = int(rotate_left_angle_var.get() or 0 if operation == "rotate_left" else rotate_right_angle_var.get() or 0)
            if angle < 0 or angle > 360:
                messagebox.showerror("Invalid Input", "Please enter a valid angle between 0 and 360.")
                return
        else:
            angle = 0

        threading.Thread(target=worker, args=(save_directory, operation, num_threads, angle)).start()
        threading.Thread(target=update_progress).start()

    def validate_number(P):
        return P.isdigit() or P == ""

    def validate_angle_input(var):
        value = var.get()
        if value != "":
            try:
                int_value = int(value)
                if int_value < 0 or int_value > 360:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid angle between 0 and 360.")
                var.set("")

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

    # Tạo các thành phần giao diện
    validate_command = root.register(validate_number)

    back_button = tk.Button(root, text="<-", font=('Helvetica', 14), command=return_to_menu)
    back_button.pack(anchor='nw', padx=10, pady=10)

    title_label = tk.Label(root, text="Image Rotate & Flip", font=('Helvetica', 16))
    title_label.pack(pady=10)

    select_files_button = tk.Button(root, text="Select Files", command=select_files)
    select_files_button.pack(pady=5)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    choose_dir_button = tk.Button(root, text="Choose Save Directory", command=choose_directory)
    choose_dir_button.pack(pady=10)

    save_dir_entry = tk.Entry(root, textvariable=save_dir_var, state='readonly', justify='center')
    save_dir_entry.pack(pady=5, fill=tk.X)

    rotate_left_label = tk.Label(root, text="Enter the rotation angle (°):")
    rotate_left_label.pack(pady=5)
    rotate_left_entry = tk.Entry(root, textvariable=rotate_left_angle_var, justify='center', width=5, validate="key", validatecommand=(validate_command, '%P'))
    rotate_left_entry.pack(pady=5)

    rotate_left_button = tk.Button(root, text="Rotate Left", command=lambda: process_files("rotate_left"))
    rotate_left_button.pack(pady=5)

    rotate_right_label = tk.Label(root, text="Enter the rotation angle (°):")
    rotate_right_label.pack(pady=5)
    rotate_right_entry = tk.Entry(root, textvariable=rotate_right_angle_var, justify='center', width=5, validate="key", validatecommand=(validate_command, '%P'))
    rotate_right_entry.pack(pady=5)

    rotate_right_button = tk.Button(root, text="Rotate Right", command=lambda: process_files("rotate_right"))
    rotate_right_button.pack(pady=5)

    # Đường kẻ phân cách
    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x', pady=10)

    flip_horizontal_button = tk.Button(root, text="Flip Horizontal", command=lambda: process_files("flip_horizontal"))
    flip_horizontal_button.pack(pady=5)

    flip_vertical_button = tk.Button(root, text="Flip Vertical", command=lambda: process_files("flip_vertical"))
    flip_vertical_button.pack(pady=5)

    thread_count_label = tk.Label(root, text="Number of Threads:")
    thread_count_label.pack(pady=5)

    thread_count_entry = tk.Entry(root, textvariable=thread_count_var, width=5, justify='center', validate="key", validatecommand=(validate_command, '%P'))
    thread_count_entry.pack(pady=5)

    stop_button = tk.Button(root, text="Stop", command=stop_processing_func)
    stop_button.pack(pady=5)

    errors_button = tk.Button(root, textvariable=errors_var, command=show_errors)
    errors_button.pack(pady=5)

    progress_bar = ttk.Progressbar(root, variable=progress, maximum=100)
    progress_bar.pack(pady=5, fill=tk.X)

    status_label = tk.Label(root, textvariable=status_var, fg="green")
    status_label.pack(pady=5)

    # Ràng buộc xác thực đầu vào cho các ô nhập
    rotate_left_angle_var.trace_add('write', lambda *args: validate_angle_input(rotate_left_angle_var))
    rotate_right_angle_var.trace_add('write', lambda *args: validate_angle_input(rotate_right_angle_var))
    thread_count_var.trace_add('write', lambda *args: validate_thread_count(thread_count_var))

    center_window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    open_image_rotate_flip()
