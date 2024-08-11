import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading
import queue
import random
import shutil

# Biến toàn cục để điều khiển việc dừng và lưu lỗi
stop_processing = False
error_messages = []
error_window = None
selected_files = []
save_directory = ""
random_selected_files = []
shuffle_enabled = True  # Biến để lưu trạng thái xáo trộn

def open_image_shuffle():
    global stop_processing, error_messages, error_window, selected_files, save_dir_var, status_var, num_files_var, errors_var, thread_count_var, progress, q, random_selected_files, random_file_count_var, shuffle_enabled

    # Tạo cửa sổ Tkinter
    root = tk.Tk()
    root.title("Image Shuffle")

    # Khởi tạo các biến Tkinter
    save_dir_var = tk.StringVar()
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    thread_count_var = tk.StringVar(value="4")
    random_file_count_var = tk.StringVar(value="0")
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

    def shuffle_and_save_images(num_random):
        """Chọn ngẫu nhiên và lưu ảnh."""
        try:
            if num_random > len(selected_files):
                messagebox.showerror("Error", "Not enough images to select.")
                return
            
            random_selected_files = random.sample(selected_files, num_random)
            if shuffle_enabled:
                random.shuffle(random_selected_files)  # Xáo trộn danh sách file nếu được bật

            for i, original_path in enumerate(random_selected_files):
                filename = os.path.basename(original_path)
                new_filename = f"shuffled_{i+1:03d}_{filename}"  # Tạo tên file mới với tiền tố shuffled và số thứ tự
                new_path = os.path.join(save_directory, new_filename)
                shutil.copy(original_path, new_path)
                q.put(i + 1)  # Gửi tiến trình hoàn thành cho hàng đợi

            q.put(None)  # Thông báo hoàn thành
        except Exception as e:
            q.put(e)  # Gửi lỗi vào hàng đợi

    def select_and_save_sequentially(num_random):
        """Chọn và lưu ảnh theo thứ tự."""
        try:
            if num_random > len(selected_files):
                messagebox.showerror("Error", "Not enough images to select.")
                return

            step = len(selected_files) // num_random
            sequential_selected_files = selected_files[::step]

            for i, original_path in enumerate(sequential_selected_files[:num_random]):
                filename = os.path.basename(original_path)
                new_filename = f"sequential_{i+1:03d}_{filename}"  # Tạo tên file mới với tiền tố sequential và số thứ tự
                new_path = os.path.join(save_directory, new_filename)
                shutil.copy(original_path, new_path)
                q.put(i + 1)  # Gửi tiến trình hoàn thành cho hàng đợi

            q.put(None)  # Thông báo hoàn thành
        except Exception as e:
            q.put(e)  # Gửi lỗi vào hàng đợi

    def worker(num_random):
        try:
            progress.set(0)
            if shuffle_enabled:
                shuffle_and_save_images(num_random)
            else:
                select_and_save_sequentially(num_random)
        except Exception as e:
            q.put(e)  # Gửi lỗi vào hàng đợi

    def update_progress():
        try:
            completed = 0
            total_files = int(random_file_count_var.get())
            while True:
                item = q.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item
                completed = item
                progress.set(int((completed / total_files) * 100))
                if not stop_processing:
                    root.after(0, status_var.set, f"Processed {completed} of {total_files} files")
                    root.after(0, root.update_idletasks)
            if not stop_processing:
                root.after(0, progress.set(100))
                show_completion_message(completed)
        except Exception as e:
            root.after(0, status_var.set, f"Error: {e}")

    def show_completion_message(completed):
        message = f"Processing complete. {completed} files processed."
        if error_messages:
            message += f" {len(error_messages)} errors occurred."
        messagebox.showinfo("Process Complete", message)

    def validate_and_process():
        global stop_processing, error_messages
        stop_processing = False
        error_messages.clear()
        errors_var.set("Errors: 0")
        if not selected_files or not save_directory:
            status_var.set("Please select images and save location.")
            return

        num_random = int(random_file_count_var.get())

        threading.Thread(target=worker, args=(num_random,)).start()
        threading.Thread(target=update_progress).start()

    def validate_number(P):
        return P.isdigit() or P == ""

    def toggle_shuffle():
        global shuffle_enabled
        shuffle_enabled = shuffle_var.get() == 1
        if shuffle_enabled:
            shuffle_and_save_button.config(text="Shuffle")
            random_file_count_label.config(text="Number of Random Files:")
        else:
            shuffle_and_save_button.config(text="Sequentially")
            random_file_count_label.config(text="Number of Files to Select:")

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

    title_label = tk.Label(root, text="Image Shuffle", font=('Helvetica', 16))
    title_label.pack(pady=10)

    select_files_button = tk.Button(root, text="Select Files", command=select_files)
    select_files_button.pack(pady=5)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    choose_dir_button = tk.Button(root, text="Choose Save Directory", command=choose_directory)
    choose_dir_button.pack(pady=10)

    save_dir_entry = tk.Entry(root, textvariable=save_dir_var, state='readonly', justify='center')
    save_dir_entry.pack(pady=5, fill=tk.X)

    # Mô tả về các lựa chọn Shuffle và Sequential
    description_label = tk.Label(root, text="Choose to shuffle or select sequentially the images before saving them:", font=('Helvetica', 10))
    description_label.pack(pady=5)

    # Khung cho hai lựa chọn Shuffle và Sequential
    option_frame = tk.Frame(root)
    option_frame.pack(pady=5)

    shuffle_var = tk.IntVar(value=1)  # Biến để lưu trạng thái xáo trộn

    shuffle_radio_button = tk.Radiobutton(option_frame, text="Shuffle", variable=shuffle_var, value=1, command=toggle_shuffle)
    shuffle_radio_button.pack(side='left', padx=5)

    sequential_radio_button = tk.Radiobutton(option_frame, text="Sequential", variable=shuffle_var, value=0, command=toggle_shuffle)
    sequential_radio_button.pack(side='left', padx=5)

    random_file_count_label = tk.Label(root, text="Number of Random Files:")
    random_file_count_label.pack(pady=5)

    random_file_count_entry = tk.Entry(root, textvariable=random_file_count_var, width=10, justify='center', validate="key", validatecommand=(validate_command, '%P'))
    random_file_count_entry.pack(pady=5)

    shuffle_and_save_button = tk.Button(root, text="Shuffle", command=validate_and_process)
    shuffle_and_save_button.pack(pady=10)

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

    center_window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    open_image_shuffle()
