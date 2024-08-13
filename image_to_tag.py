import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image as PILImage, ImageTk
import os
import queue
import threading
import subprocess
import sys
import json

# Global variables to control the process and track errors
stop_processing = False
error_messages = []
selected_files = []
save_directory = ""  # Sử dụng thư mục của ảnh đầu tiên được chọn
caption_window = None
caption_frame = None
thumbnails = []  # To hold references to thumbnail objects
caption_text_widgets = []  # To hold Text widgets containing captions
tag_dict = {}  # Store tags and their counts
selected_tag = None  # Store the selected tag widget
edit_buttons = {}  # To hold the edit and delete buttons for each tag
error_window = None  # To ensure only one error window is open at a time
tag_text_frame = None  # Define globally to manage tag frame

# Global Tkinter variable placeholders
status_var = None
num_files_var = None
errors_var = None
progress = None
character_threshold_var = None
general_threshold_var = None
thread_count_var = None
batch_size_var = None
start_button = None
stop_button = None
prepend_text_var = None
append_text_var = None
current_page = 0
images_per_page = 20
total_pages = 1  # Initialize total pages

def update_and_save_config():
    """Update and save the configuration to JSON."""
    save_config_to_json(
        model="swinv2",  # Default model
        general_threshold=general_threshold_var.get(),
        character_threshold=character_threshold_var.get(),
        model_dir="D:/test/models/wd-swinv2-tagger-v3"  # Default model directory
    )

def show_errors(root):
    """Display error details in a new window."""
    global error_window
    if error_window is not None:
        return  # Only one error window can be open at a time

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

def save_config_to_json(model, general_threshold, character_threshold, model_dir, filepath='config.json'):
    """Save the model and threshold values to a JSON file."""
    config = {
        'model': model,
        'general_threshold': general_threshold,
        'character_threshold': character_threshold,
        'model_dir': model_dir
    }
    try:
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config to JSON: {e}")

def open_image_to_tag():
    global stop_processing, error_messages, selected_files, save_directory, caption_window, caption_frame, thumbnails, caption_text_widgets, tag_dict, selected_tag, edit_buttons, tag_text_frame, current_page, total_pages, content_canvas
    global status_var, num_files_var, errors_var, progress, character_threshold_var, general_threshold_var, thread_count_var, batch_size_var
    global start_button, stop_button, prepend_text_var, append_text_var

    # Create Tkinter window
    root = tk.Tk()
    root.title("Image Caption Generator")

    # Initialize Tkinter variables
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    progress = tk.IntVar()
    character_threshold_var = tk.DoubleVar(value=0.35)
    general_threshold_var = tk.DoubleVar(value=0.35)
    thread_count_var = tk.IntVar(value=4)
    batch_size_var = tk.IntVar(value=4)
    prepend_text_var = tk.StringVar()
    append_text_var = tk.StringVar()
    q = queue.Queue()

    def center_window(window, width_extra=0, height_extra=0):
        window.update_idletasks()
        width = 100 + width_extra
        height = 820 + height_extra
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def select_files():
        global selected_files, save_directory, total_pages
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
            save_directory = os.path.dirname(selected_files[0])  # Lấy thư mục của ảnh đầu tiên
            total_pages = (len(selected_files) + images_per_page - 1) // images_per_page  # Cập nhật tổng số trang
            if caption_window is not None:
                update_image_preview(content_canvas)

    def toggle_buttons(state):
        """Enable or disable buttons based on the state."""
        state = tk.NORMAL if state else tk.DISABLED
        select_files_button.config(state=state)
        show_captions_button.config(state=state)
        general_threshold_entry.config(state=state)
        character_threshold_entry.config(state=state)
        thread_count_entry.config(state=state)
        batch_size_entry.config(state=state)
        prepend_text_entry.config(state=state)
        append_text_entry.config(state=state)
        start_button.config(state=state)
        # Stop button should always be enabled
        stop_button.config(state=tk.NORMAL)

    def generate_caption(image_path, save_directory, q):
        """Generate captions for a single image using the wd-swinv2-tagger-v3 model."""
        if stop_processing:
            return

        try:
            filename = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(save_directory, f"{filename}.txt")

            command = [
                sys.executable, 'D:/test/wdv3-timm-main/wdv3_timm.py',
                '--model', "swinv2",
                '--image_path', image_path,
                '--model_dir', "D:/test/models/wd-swinv2-tagger-v3",
                '--general_threshold', str(general_threshold_var.get()),
                '--character_threshold', str(character_threshold_var.get())
            ]

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            output = result.stdout
            print(output)  # Debug: In ra toàn bộ đầu ra từ lệnh subprocess
            error_output = result.stderr
            print(output)  # In ra đầu ra từ lệnh subprocess
            print(error_output)  # In ra đầu ra lỗi từ lệnh subprocess

            # Filter out information to contain only Caption or General tags
            filtered_output = []
            recording = False
            for line in output.split('\n'):
                if "General tags" in line:
                    recording = True
                    continue
                if recording:
                    if line.startswith('  '):
                        tag = line.strip().split(':')[0].replace('_', ' ')
                        filtered_output.append(tag)
                    else:
                        recording = False
                        break

            # Convert list of tags to comma-separated string
            final_tags = ','.join(filtered_output) if filtered_output else "No tags found"
            print("Filtered output:", final_tags)  # Debug: In ra các nhãn cuối cùng sau khi lọc

            # Add prepend and append text
            final_tags = f"{prepend_text_var.get()},{final_tags},{append_text_var.get()}".strip(',')

            # Save result to text file
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(final_tags)

            q.put(image_path)
        except Exception as e:
            error_message = f"Error processing image {image_path}: {str(e)}"
            print(error_message)  # Debug: In ra thông báo lỗi
            q.put(error_message)
            error_messages.append(error_message)

    def worker(save_directory, num_threads, batch_size):
        try:
            progress.set(0)
            batch = []
            threads = []
            for i, input_path in enumerate(selected_files, 1):
                if stop_processing:
                    break

                batch.append(input_path)
                if len(batch) == batch_size or i == len(selected_files):
                    for image_path in batch:
                        thread = threading.Thread(target=generate_caption, args=(image_path, save_directory, q))
                        threads.append(thread)
                        thread.start()

                    for thread in threads:
                        thread.join()

                    batch.clear()
                    threads.clear()

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
                    if caption_window is not None:
                        root.after(0, update_image_preview, content_canvas)
            if not stop_processing:
                root.after(0, progress.set(100))
                show_completion_message(completed)
        except Exception as e:
            if not stop_processing:
                root.after(0, status_var.set, f"Error: {e}")
        finally:
            # Re-enable buttons after processing completes
            toggle_buttons(True)

    def show_completion_message(completed):
        message = f"Processing complete. {completed} files processed."
        if error_messages:
            message += f" {len(error_messages)} errors occurred."
        messagebox.showinfo("Process Complete", message)

    def process_files():
        global stop_processing, error_messages
        stop_processing = False
        error_messages.clear()
        errors_var.set("Errors: 0")
        if not selected_files or not save_directory:
            status_var.set("Please select images.")
            return

        # Disable buttons during processing
        toggle_buttons(False)

        threading.Thread(target=worker, args=(save_directory, thread_count_var.get(), batch_size_var.get())).start()
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
        # Save all captions before closing
        save_all_captions()
        return_to_menu()

    def validate_threshold(P):
        """Validate that the threshold value is between 0 and 1."""
        if P == "" or (P.replace('.', '', 1).isdigit() and 0 <= float(P) <= 1):
            return True
        return False

    def validate_thread_count(P):
        """Validate that the thread count is a positive integer."""
        if P == "" or P.isdigit() and int(P) > 0:
            return True
        return False

    def validate_batch_size(P):
        """Validate that the batch size is a positive integer."""
        if P == "" or P.isdigit() and int(P) > 0:
            return True
        return False

    def open_caption_window():
        global caption_window, caption_frame, caption_text_widgets, tag_text_frame, current_page, total_pages, content_canvas
        if caption_window is not None:
            return  # A caption window is already open, do not create a new one

        caption_window = tk.Toplevel(root)
        caption_window.title("Image Thumbnails and Captions")
        caption_window.geometry("1400x900")  # Điều chỉnh kích thước cửa sổ

        # Create main frame to hold canvas and other elements
        main_frame = tk.Frame(caption_window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas for content
        content_canvas = tk.Canvas(main_frame)
        content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create frame for content
        caption_frame = tk.Frame(content_canvas)
        content_canvas.create_window((0, 0), window=caption_frame, anchor='nw')

        # Add scrollbar for caption_frame
        caption_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=content_canvas.yview)
        caption_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        content_canvas.configure(yscrollcommand=caption_scrollbar.set)

        caption_frame.bind("<Configure>", lambda e: content_canvas.configure(scrollregion=content_canvas.bbox("all")))

        # Ensure caption_window is reset to None when the window is closed
        def on_caption_window_close():
            global caption_window, tag_text_frame
            caption_window.destroy()
            caption_window = None
            tag_text_frame = None  # Reset tag_text_frame when window is closed

        caption_window.protocol("WM_DELETE_WINDOW", on_caption_window_close)

        # Display content and set dividers
        update_image_preview(content_canvas)

        # Create frame for tags (on the right side)
        tag_frame = tk.Frame(main_frame, padx=0)
        tag_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Create sorting buttons
        sort_label = tk.Label(tag_frame, text="Sort by:", font=('Helvetica', 12))
        sort_label.pack(anchor='nw', pady=5)

        sort_alpha_button = tk.Button(tag_frame, text="Alphabetical", command=sort_tags_alpha)
        sort_alpha_button.pack(anchor='nw', pady=2)

        sort_count_button = tk.Button(tag_frame, text="Count", command=sort_tags_count)
        sort_count_button.pack(anchor='nw', pady=2)

        # Create display area for tags
        tag_canvas = tk.Canvas(tag_frame)
        tag_text_frame = tk.Frame(tag_canvas)
        tag_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tag_canvas.create_window((0, 0), window=tag_text_frame, anchor='nw')

        # Add scrollbar for tag_frame
        tag_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=tag_canvas.yview)
        tag_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tag_canvas.configure(yscrollcommand=tag_scrollbar.set)

        tag_text_frame.bind("<Configure>", lambda e: tag_canvas.configure(scrollregion=tag_canvas.bbox("all")))

        # Update initial tag display
        update_tag_display()

    def update_image_preview(content_canvas):
        global thumbnails, caption_text_widgets, current_page, images_per_page, total_pages
        if caption_frame is None:
            return

        for widget in caption_frame.winfo_children():
            if isinstance(widget, tk.Label) or isinstance(widget, tk.Text) or isinstance(widget, tk.Frame):
                widget.destroy()

        thumbnails.clear()  # Clear old thumbnails
        caption_text_widgets.clear()  # Clear old caption_entries

        if not selected_files:
            return

        start_index = current_page * images_per_page
        end_index = start_index + images_per_page
        files_to_display = selected_files[start_index:end_index]

        for i, file_path in enumerate(files_to_display):
            thumbnail_size = (200, 200)
            try:
                image = PILImage.open(file_path)
                image.thumbnail(thumbnail_size)
                thumbnail = ImageTk.PhotoImage(image)
                thumbnails.append(thumbnail)  # Keep reference to thumbnail object

                # Display thumbnail
                img_label = tk.Label(caption_frame, image=thumbnail)
                img_label.grid(row=i*2, column=0, padx=5, pady=5, sticky="nsew")

                # Display file name
                file_label = tk.Label(caption_frame, text=os.path.basename(file_path), font=('Helvetica', 12), wraplength=300, justify="left")
                file_label.grid(row=i*2, column=1, padx=5, pady=5, sticky="nsew")

                # Check and display caption if available
                caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_tags.txt")
                if os.path.exists(caption_file):
                    with open(caption_file, 'r', encoding='utf-8') as file:
                        caption_text = file.read()
                else:
                    caption_text = ""  # Set empty string if no caption available

                caption_text_widget = tk.Text(caption_frame, width=50, height=3, wrap=tk.WORD, font=('Helvetica', 12))
                caption_text_widget.insert(tk.END, caption_text)
                caption_text_widget.grid(row=i*2, column=2, padx=5, pady=5, sticky="nsew")
                caption_text_widget.bind("<FocusOut>", lambda e, fp=file_path: save_caption(fp, caption_text_widget.get("1.0", "end-1c")))
                caption_text_widgets.append(caption_text_widget)

                # Update tags in tag_dict
                update_tag_dict(caption_text)

            except Exception as e:
                tk.Label(caption_frame, text="Error loading image").grid(row=i*2, column=0, columnspan=4, padx=5, pady=5)

        # Add navigation buttons
        nav_frame = tk.Frame(caption_frame)
        nav_frame.grid(row=images_per_page*2, column=0, columnspan=3, pady=10)

        if current_page > 0:
            prev_button = tk.Button(nav_frame, text="Previous", command=lambda: navigate(-1, content_canvas))
            prev_button.pack(side=tk.LEFT)

        page_label = tk.Label(nav_frame, text=f"Page {current_page + 1} of {total_pages}")
        page_label.pack(side=tk.LEFT, padx=5)

        page_entry = tk.Entry(nav_frame, width=5)
        page_entry.pack(side=tk.LEFT)

        go_button = tk.Button(nav_frame, text="Go", command=lambda: go_to_page(page_entry.get(), content_canvas))
        go_button.pack(side=tk.LEFT, padx=5)

        if current_page < total_pages - 1:
            next_button = tk.Button(nav_frame, text="Next", command=lambda: navigate(1, content_canvas))
            next_button.pack(side=tk.RIGHT)

        # Update tag display after loading images
        update_tag_display()

    def navigate(direction, content_canvas):
        global current_page
        current_page += direction
        update_image_preview(content_canvas)

    def go_to_page(page_number, content_canvas):
        global current_page, total_pages
        try:
            page_number = int(page_number)
            if 1 <= page_number <= total_pages:
                current_page = page_number - 1
                update_image_preview(content_canvas)
            else:
                messagebox.showerror("Invalid Page", f"Please enter a valid page number between 1 and {total_pages}.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the page number.")

    def save_caption(file_path, caption_text):
        """Save caption when user changes it."""
        output_path = os.path.join(save_directory, f"{os.path.basename(file_path)}_tags.txt")
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(caption_text)

        # Update tags after editing caption
        update_tag_dict(caption_text)
        update_tag_display()

    def save_all_captions():
        """Save all captions when closing the window."""
        for i, caption_text_widget in enumerate(caption_text_widgets):
            if caption_text_widget.winfo_exists():
                file_path = selected_files[current_page * images_per_page + i]
                caption_text = caption_text_widget.get("1.0", "end-1c")
                save_caption(file_path, caption_text)

    def update_tag_dict(caption_text=None):
        """Update tag dictionary based on caption_text."""
        global tag_dict
        new_tag_dict = {}
        for caption_widget in caption_text_widgets:
            if caption_widget.winfo_exists():
                caption_text = caption_widget.get("1.0", "end-1c")
                tags = caption_text.split(',')
                for tag in tags:
                    tag = tag.strip()
                    if tag:
                        if tag in new_tag_dict:
                            new_tag_dict[tag] += 1
                        else:
                            new_tag_dict[tag] = 1
        tag_dict = new_tag_dict

    def update_tag_display():
        """Update tag display on Text widget."""
        global tag_dict, selected_tag, edit_buttons, tag_text_frame
        if tag_text_frame is None:
            return  # If the tag_text_frame is not created yet, return
        for widget in tag_text_frame.winfo_children():
            widget.destroy()

        row = 0
        for tag, count in tag_dict.items():
            tag_label = tk.Label(tag_text_frame, text=tag, bg="white", padx=5, pady=2, anchor="w", relief="solid", borderwidth=1)
            tag_label.grid(row=row, column=0, sticky="w", padx=2, pady=1)
            count_label = tk.Label(tag_text_frame, text=f"({count})", anchor='w', width=5)
            count_label.grid(row=row, column=1, padx=5, pady=2, sticky='w')

            # Add tag manipulation buttons
            add_tag_button = tk.Button(tag_text_frame, text="Add", command=lambda r=row: add_tag(r))
            add_tag_button.grid(row=row, column=2, padx=2)
            edit_button = tk.Button(tag_text_frame, text="Edit", command=lambda t=tag_label: edit_tag(t))
            edit_button.grid(row=row, column=3, padx=2)
            delete_button = tk.Button(tag_text_frame, text="Delete", command=lambda t=tag_label: delete_tag(t))
            delete_button.grid(row=row, column=4, padx=2)
            delete_all_button = tk.Button(tag_text_frame, text="Delete All", command=lambda t=tag_label: delete_all_files_with_tag(t))
            delete_all_button.grid(row=row, column=5, padx=2)

            edit_buttons[tag_label] = [add_tag_button, edit_button, delete_button, delete_all_button]

            row += 1

        # Điều chỉnh trọng số cột để không mở rộng quá mức
        tag_text_frame.grid_columnconfigure(0, weight=1)  # Cột cho tag
        tag_text_frame.grid_columnconfigure(1, weight=0)  # Cột cho số lượng
        tag_text_frame.grid_columnconfigure(2, weight=0)  # Cột cho nút Add
        tag_text_frame.grid_columnconfigure(3, weight=0)  # Cột cho nút Edit
        tag_text_frame.grid_columnconfigure(4, weight=0)  # Cột cho nút Delete
        tag_text_frame.grid_columnconfigure(5, weight=0)  # Cột cho nút Delete All

        tag_text_frame.update_idletasks()  # Làm mới giao diện sau khi cập nhật danh sách tag
        tag_text_frame.update()  # Làm mới giao diện ngay lập tức

    def add_tag(row):
        """Add a new tag above the selected row."""
        def save_new_tag(event=None):
            new_tag = entry.get().strip()
            if new_tag:
                # Add the new tag to the tag_dict
                if new_tag in tag_dict:
                    tag_dict[new_tag] += 1
                else:
                    tag_dict[new_tag] = 1

                # Update the captions in the respective files
                for file_path in selected_files:
                    caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_tags.txt")
                    if os.path.exists(caption_file):
                        with open(caption_file, 'r', encoding='utf-8') as file:
                            caption_text = file.read()
                        new_caption_text = caption_text + ',' + new_tag if caption_text else new_tag
                        with open(caption_file, 'w', encoding='utf-8') as file:
                            file.write(new_caption_text)

                update_image_preview(content_canvas)  # Update image preview
                update_tag_display()  # Update the display of tags

        # Create entry above the row
        for widget in tag_text_frame.grid_slaves():
            if int(widget.grid_info()["row"]) >= row:
                widget.grid_configure(row=int(widget.grid_info()["row"]) + 1)

        entry = tk.Entry(tag_text_frame)
        entry.grid(row=row, column=0, sticky="w", padx=2, pady=1)
        entry.bind("<Return>", save_new_tag)
        entry.bind("<FocusOut>", save_new_tag)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.focus_set()

    def edit_tag(tag_label):
        """Edit the selected tag."""
        def save_edit(event=None):
            new_tag = entry.get().strip()
            old_tag = tag_label.cget("text").strip()
            if new_tag and new_tag != old_tag:
                # Update the tag_dict with new tag
                tag_dict[new_tag] = tag_dict.pop(old_tag)

                # Update the captions in the respective files
                for i, file_path in enumerate(selected_files):
                    caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_tags.txt")
                    if os.path.exists(caption_file):
                        with open(caption_file, 'r', encoding='utf-8') as file:
                            caption_text = file.read()
                        new_caption_text = caption_text.replace(old_tag, new_tag)
                        with open(caption_file, 'w', encoding='utf-8') as file:
                            file.write(new_caption_text)

                update_image_preview(content_canvas)  # Update image preview
                update_tag_display()  # Update the display of tags

        old_tag = tag_label.cget("text").strip()
        entry = tk.Entry(tag_text_frame)
        entry.insert(0, old_tag)
        entry.grid(row=tag_label.grid_info()["row"], column=0, sticky="w", padx=2, pady=1)
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.focus_set()

    def delete_tag(tag_label):
        """Delete the selected tag."""
        global selected_tag
        if tag_label:
            tag_to_delete = tag_label.cget("text").strip()
            if tag_to_delete in tag_dict:
                del tag_dict[tag_to_delete]

                # Update the captions in the respective files
                for i, file_path in enumerate(selected_files):
                    caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_tags.txt")
                    if os.path.exists(caption_file):
                        with open(caption_file, 'r', encoding='utf-8') as file:
                            caption_text = file.read()
                        new_caption_text = caption_text.replace(tag_to_delete, "")
                        with open(caption_file, 'w', encoding='utf-8') as file:
                            file.write(new_caption_text)

                update_image_preview(content_canvas)  # Update image preview
                update_tag_display()  # Update the display of tags

    def delete_all_files_with_tag(tag_label):
        """Delete all images and their corresponding text files containing the tag."""
        tag_to_delete = tag_label.cget("text").strip()
        if tag_to_delete in tag_dict:
            del tag_dict[tag_to_delete]

            # Delete the files containing the tag
            files_to_delete = []
            for i, file_path in enumerate(selected_files):
                caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_tags.txt")
                if os.path.exists(caption_file):
                    with open(caption_file, 'r', encoding='utf-8') as file:
                        caption_text = file.read()
                    if tag_to_delete in caption_text:
                        files_to_delete.append((file_path, caption_file))
            for image_file, caption_file in files_to_delete:
                # Remove image file
                try:
                    os.remove(image_file)
                except Exception as e:
                    error_messages.append(f"Error deleting image {image_file}: {str(e)}")
                # Remove caption file
                try:
                    os.remove(caption_file)
                except Exception as e:
                    error_messages.append(f"Error deleting caption {caption_file}: {str(e)}")

            # Remove deleted files from selected_files list
            selected_files[:] = [file for file in selected_files if file not in [img for img, cap in files_to_delete]]

            # Clear tag_dict and update tag display
            update_tag_dict()  # Update tag dictionary
            update_tag_display()  # Update the display of tags
            update_image_preview(content_canvas)  # Update image preview

    def sort_tags_alpha():
        """Sort tags alphabetically."""
        global tag_dict
        sorted_tags = sorted(tag_dict.items())
        tag_dict = dict(sorted_tags)
        update_tag_display()

    def sort_tags_count():
        """Sort tags by count."""
        global tag_dict
        sorted_tags = sorted(tag_dict.items(), key=lambda item: item[1], reverse=True)
        tag_dict = dict(sorted_tags)
        update_tag_display()

    # Create GUI components
    back_button = tk.Button(root, text="<-", font=('Helvetica', 14), command=return_to_menu)
    back_button.pack(anchor='nw', padx=10, pady=10)

    title_label = tk.Label(root, text="Image Tag Generator", font=('Helvetica', 16))
    title_label.pack(pady=10)

    select_files_button = tk.Button(root, text="Select Files", command=select_files)
    select_files_button.pack(pady=10)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    show_captions_button = tk.Button(root, text="Show Captions", command=open_caption_window)
    show_captions_button.pack(pady=10)

    general_threshold_label = tk.Label(root, text="General Threshold:")
    general_threshold_label.pack(pady=5)
    general_threshold_entry = tk.Entry(root, textvariable=general_threshold_var, justify='center', width=5, validate='key')
    general_threshold_entry.pack(pady=5)

    character_threshold_label = tk.Label(root, text="Character Threshold:")
    character_threshold_label.pack(pady=5)
    character_threshold_entry = tk.Entry(root, textvariable=character_threshold_var, justify='center', width=5, validate='key')
    character_threshold_entry.pack(pady=5)

    prepend_text_label = tk.Label(root, text="Prepend Text:")
    prepend_text_label.pack(pady=5)
    prepend_text_entry = tk.Entry(root, textvariable=prepend_text_var, justify='center', width=20)
    prepend_text_entry.pack(pady=5)

    append_text_label = tk.Label(root, text="Append Text:")
    append_text_label.pack(pady=5)
    append_text_entry = tk.Entry(root, textvariable=append_text_var, justify='center', width=20)
    append_text_entry.pack(pady=5)

    thread_count_label = tk.Label(root, text="Thread Count:")
    thread_count_label.pack(pady=5)
    thread_count_entry = tk.Entry(root, textvariable=thread_count_var, justify='center', width=5, validate='key')
    thread_count_entry.pack(pady=5)

    batch_size_label = tk.Label(root, text="Batch Size:")
    batch_size_label.pack(pady=5)
    batch_size_entry = tk.Entry(root, textvariable=batch_size_var, justify='center', width=5, validate='key')
    batch_size_entry.pack(pady=5)

    errors_button = tk.Button(root, textvariable=errors_var, command=lambda: show_errors(root))
    errors_button.pack(pady=10)

    start_button = tk.Button(root, text="Generate Captions", command=lambda: [process_files(), update_and_save_config()])
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop", command=stop_processing_func)
    stop_button.pack(pady=10)

    progress_bar = ttk.Progressbar(root, variable=progress, maximum=100)
    progress_bar.pack(pady=10, fill=tk.X)

    status_label = tk.Label(root, textvariable=status_var, fg="green")
    status_label.pack(pady=5)

    # Add input validation
    general_threshold_entry.config(validatecommand=(root.register(validate_threshold), '%P'))
    character_threshold_entry.config(validatecommand=(root.register(validate_threshold), '%P'))
    thread_count_entry.config(validatecommand=(root.register(validate_thread_count), '%P'))
    batch_size_entry.config(validatecommand=(root.register(validate_batch_size), '%P'))

    # Update config when the thresholds or thread count change
    general_threshold_var.trace_add('write', lambda *args: update_and_save_config())
    character_threshold_var.trace_add('write', lambda *args: update_and_save_config())
    thread_count_var.trace_add('write', lambda *args: update_and_save_config())

    center_window(root, width_extra=200)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    open_image_to_tag()
