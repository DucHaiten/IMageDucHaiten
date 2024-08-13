import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image as PILImage, ImageTk
import os
import queue
import threading
import torch
from transformers import AutoModelForCausalLM, LlamaTokenizer
import json
import traceback
import math

torch.set_grad_enabled(False)

stop_processing = False
error_messages = []
selected_files = []
save_directory = ""
caption_window = None
caption_frame = None
thumbnails = []
caption_text_widgets = []
error_window = None
status_var = None
num_files_var = None
errors_var = None
progress = None
prompt_var = None
max_new_tokens_var = None
do_sample_var = None
temperature_var = None
top_k_var = None
top_p_var = None
thread_count_var = None
precision_var = None
batch_size_var = None
prepend_text_var = None
append_text_var = None
caption_handling_var = None  # Variable to handle radio buttons for caption handling
start_button = None
stop_button = None
model = None
prompt_entry = None
select_files_button = None
show_captions_button = None
thread_count_entry = None
precision_entry = None
batch_size_entry = None
prepend_text_entry = None
append_text_entry = None
root = None
q = queue.Queue()

current_page = 0
images_per_page = 20
total_pages = 1
content_canvas = None
search_var = None
original_selected_files = []
action_var = None
action_entry = None

def load_model():
    global model, tokenizer
    if model is None:
        tokenizer = LlamaTokenizer.from_pretrained('lmsys/vicuna-7b-v1.5')

        bit_precision = bit_precision_var.get()
        
        load_in_4bit = load_in_8bit = False

        # Thiết lập torch_type dựa trên giá trị bit_precision
        if bit_precision == 4:
            load_in_4bit = True
            torch_type = torch.float16  # Dùng float16 khi sử dụng bitsandbytes
        elif bit_precision == 8:
            load_in_8bit = True
            torch_type = torch.float16  # Dùng float16 khi sử dụng bitsandbytes
        elif bit_precision == 16:
            torch_type = torch.float16
        elif bit_precision == 32:
            torch_type = torch.float32

        try:
            import bitsandbytes as bnb
            model = AutoModelForCausalLM.from_pretrained(
                'THUDM/cogvlm-chat-hf',
                torch_dtype=torch_type,
                low_cpu_mem_usage=True,
                load_in_4bit=load_in_4bit,
                load_in_8bit=load_in_8bit,
                trust_remote_code=True,
            )
        except ImportError:
            # Nếu không có bitsandbytes hoặc dùng 16-bit hoặc 32-bit
            model = AutoModelForCausalLM.from_pretrained(
                'THUDM/cogvlm-chat-hf',
                torch_dtype=torch_type,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )

        # Chỉ chuyển mô hình sang GPU nếu không sử dụng chế độ 4-bit hoặc 8-bit
        if not load_in_4bit and not load_in_8bit:
            model = model.to(torch.device('cuda'))

            # Đảm bảo chuyển đổi mô hình sang float32 nếu đang ở chế độ 32-bit
            if bit_precision == 32:
                model = model.to(torch.float32)
            elif bit_precision == 16:
                model = model.to(torch.float16)
        
        model.eval()

        # Kiểm tra thông tin model nạp vào
        print(f"Model loaded with dtype: {torch_type}, 4bit: {load_in_4bit}, 8bit: {load_in_8bit}")


def update_and_save_config():
    top_p_value = top_p_var.get() if do_sample_var.get() else None
    config_entry = {
        'prompt': prompt_var.get(),
        'max_new_tokens': max_new_tokens_var.get(),
        'temperature': temperature_var.get(),
        'top_k': top_k_var.get(),
        'top_p': float(top_p_value) if top_p_value is not None else None,
        'bit_precision': bit_precision_var.get(),  # Hợp nhất cả precision và bit
        'thread_count': thread_count_var.get(),
        'batch_size': batch_size_var.get(),
        'prepend_text': prepend_text_var.get(),
        'append_text': append_text_var.get(),
        'caption_handling': caption_handling_var.get()
    }

    try:
        with open('captions.json', 'w') as f:
            json.dump(config_entry, f, indent=2)
    except Exception as e:
        print(f"Error saving config to captions.json: {e}")

def load_config_from_json():
    try:
        if os.path.exists('captions.json'):
            with open('captions.json', 'r') as f:
                config_entry = json.load(f)
                prompt_var.set(config_entry.get('prompt', ''))
                max_new_tokens_var.set(config_entry.get('max_new_tokens', 200))
                temperature_var.set(config_entry.get('temperature', 1.0))
                top_k_var.set(config_entry.get('top_k', 50))
                top_p_var.set(config_entry.get('top_p', 0.95))
                bit_precision_var.set(config_entry.get('bit_precision', 8))  # Tải bit_precision
                thread_count_var.set(config_entry.get('thread_count', 4))
                batch_size_var.set(config_entry.get('batch_size', 1))
                prepend_text_var.set(config_entry.get('prepend_text', ''))
                append_text_var.set(config_entry.get('append_text', ''))
                caption_handling_var.set(config_entry.get('caption_handling', 'skip'))

                prompt_entry.delete("1.0", tk.END)
                prompt_entry.insert(tk.END, config_entry.get('prompt', ''))
    except Exception as e:
        print(f"Error loading config from captions.json: {e}")

def on_config_change(*args):
    root.after(100, update_config)

def update_config():
    try:
        precision_value = precision_var.get()
        if precision_value == "":
            return  # Không làm gì nếu giá trị là chuỗi rỗng

        update_and_save_config()
    except Exception as e:
        print(f"Lỗi khi xử lý giá trị: {e}")

def on_prompt_change(event=None):
    prompt_var.set(prompt_entry.get("1.0", tk.END).strip())
    update_and_save_config()

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

def validate_numeric_input(value):
    if value == "" or value == "-":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def toggle_sampling_options():
    if do_sample_var.get():
        temperature_label.pack(pady=5, after=do_sample_check)
        temperature_entry.pack(pady=5, after=temperature_label)
        top_k_label.pack(pady=5, after=temperature_entry)
        top_k_entry.pack(pady=5, after=top_k_label)
        top_p_label.pack(pady=5, after=top_k_entry)
        top_p_entry.pack(pady=5, after=top_p_label)
        root.geometry(f"{root.winfo_width()}x{root.winfo_height() + 150}")
    else:
        temperature_label.pack_forget()
        temperature_entry.pack_forget()
        top_k_label.pack_forget()
        top_k_entry.pack_forget()
        top_p_label.pack_forget()
        top_p_entry.pack_forget()
        root.geometry(f"{root.winfo_width()}x{root.winfo_height() - 150}")
    center_window(root)

def open_image_to_caption():
    global bit_precision_var, root
    global initial_bit_precision
    global app_initialized
    global stop_processing, error_messages, selected_files, save_directory, status_var, num_files_var, errors_var, progress
    global prompt_var, max_new_tokens_var, do_sample_var, temperature_var, top_k_var, top_p_var, thread_count_var, precision_var, batch_size_var
    global prepend_text_var, append_text_var, search_var, action_var, caption_handling_var
    global start_button, stop_button
    global temperature_label, temperature_entry, top_k_label, top_k_entry, top_p_label, top_p_entry
    global do_sample_check, prompt_entry, select_files_button, show_captions_button, thread_count_entry, precision_entry, batch_size_entry
    global prepend_text_entry, append_text_entry
    global q

    app_initialized = False

    # Định nghĩa hàm xử lý khi bit_precision thay đổi
    def on_bit_precision_change(*args):
        if not app_initialized:
            return
        
        update_and_save_config()

        result = messagebox.showinfo(
            "Bit Precision Changed",
            "You have changed the bit precision. Please restart the app for the changes to take effect."
        )
            
        if result == "ok":
            root.destroy()  # Tắt ứng dụng hiện tại
            python = sys.executable
            os.execl(python, python, "main.py")
            

    # Initialize the main Tkinter root window
    root = tk.Tk()
    root.title("Image to Caption")
    root.geometry("1050x950")

    # Khởi tạo các biến Tkinter sau khi root đã được tạo
    status_var = tk.StringVar()
    num_files_var = tk.StringVar()
    errors_var = tk.StringVar(value="Errors: 0")
    progress = tk.IntVar()
    prompt_var = tk.StringVar(value="Describe this image")
    max_new_tokens_var = tk.IntVar(value=200)
    do_sample_var = tk.BooleanVar(value=False)
    temperature_var = tk.DoubleVar(value=1.0)
    top_k_var = tk.IntVar(value=50)
    top_p_var = tk.DoubleVar(value=0.95)
    thread_count_var = tk.IntVar(value=4)
    precision_var = tk.IntVar(value=1)
    batch_size_var = tk.IntVar(value=1)
    prepend_text_var = tk.StringVar()
    append_text_var = tk.StringVar()
    caption_handling_var = tk.StringVar(value='skip')  # Default value is 'skip'
    search_var = tk.StringVar()  # Biến search_var khởi tạo ở đây
    action_var = tk.StringVar()  # Biến action_var khởi tạo ở đây

    bit_precision_var = tk.IntVar(value=8)
    initial_bit_precision = bit_precision_var.get()

    q = queue.Queue()

    validate_cmd = root.register(validate_numeric_input)

    back_button = tk.Button(root, text="<-", font=('Helvetica', 14), command=return_to_menu)
    back_button.pack(anchor='nw', padx=10, pady=10)

    title_label = tk.Label(root, text="Image Caption Generator", font=('Helvetica', 16))
    title_label.pack(pady=10)

    warning_label = tk.Label(root, text="NOTE: 4-bit requires 20GB of RAM and 12GB of VRAM, 8-bit requires 20GB of RAM and 16GB of VRAM, 16-bit requires 50GB of RAM and 24GB of VRAM, 32-bit requires 85GB of RAM and 40GB of VRAM. Although GPUs with less VRAM can still run, the performance will be very slow.",
                             font=('Helvetica', 10), fg="red", wraplength=850, justify="left")
    warning_label.pack(pady=10)

    select_files_button = tk.Button(root, text="Select Files", command=select_files)
    select_files_button.pack(pady=10)

    show_captions_button = tk.Button(root, text="Show Captions", command=open_caption_window)
    show_captions_button.pack(pady=10)

    num_files_label = tk.Label(root, textvariable=num_files_var)
    num_files_label.pack(pady=5)

    bit_frame = tk.Frame(root)
    bit_frame.pack(pady=5)

    bit_label = tk.Label(bit_frame, text="Select Bit Precision:")
    bit_label.pack(side="left", padx=10)

    tk.Radiobutton(bit_frame, text="4-bit", variable=bit_precision_var, value=4).pack(side="left", padx=5)
    tk.Radiobutton(bit_frame, text="8-bit", variable=bit_precision_var, value=8).pack(side="left", padx=5)
    tk.Radiobutton(bit_frame, text="16-bit", variable=bit_precision_var, value=16).pack(side="left", padx=5)
    tk.Radiobutton(bit_frame, text="32-bit", variable=bit_precision_var, value=32).pack(side="left", padx=5)

    prompt_label = tk.Label(root, text="Prompt (text to describe the image):")
    prompt_label.pack(pady=5)
    prompt_entry = tk.Text(root, height=3, wrap='word', width=60)
    prompt_entry.pack(pady=5, padx=10, fill='both', expand=True)
    prompt_entry.bind('<KeyRelease>', on_prompt_change)

    prepend_text_label = tk.Label(root, text="Prepend Text:")
    prepend_text_label.pack(pady=5)
    prepend_text_entry = tk.Entry(root, textvariable=prepend_text_var, justify='center', width=60)
    prepend_text_entry.pack(pady=5)

    append_text_label = tk.Label(root, text="Append Text:")
    append_text_label.pack(pady=5)
    append_text_entry = tk.Entry(root, textvariable=append_text_var, justify='center', width=60)
    append_text_entry.pack(pady=5)

    # Thêm các radio button để xử lý caption khi ảnh đã có caption
    caption_handling_label = tk.Label(root, text="If a caption already exists for an image:", font=('Helvetica', 12))
    caption_handling_label.pack(pady=5)

    # Frame chứa các radio button
    options_frame = tk.Frame(root)
    options_frame.pack(pady=5)

    # Radio buttons
    overwrite_radio = tk.Radiobutton(options_frame, text="Overwrite existing caption", variable=caption_handling_var, value='overwrite')
    overwrite_radio.pack(side="left", padx=10)

    append_radio = tk.Radiobutton(options_frame, text="Append to existing caption", variable=caption_handling_var, value='append')
    append_radio.pack(side="left", padx=10)

    skip_radio = tk.Radiobutton(options_frame, text="Skip images with existing caption", variable=caption_handling_var, value='skip')
    skip_radio.pack(side="left", padx=10)

    bit_precision_var.trace('w', on_bit_precision_change)

    load_config_from_json()

    app_initialized = True

    prompt_var.trace('w', on_config_change)
    max_new_tokens_var.trace('w', on_config_change)
    temperature_var.trace('w', on_config_change)
    top_k_var.trace('w', on_config_change)
    top_p_var.trace('w', on_config_change)
    precision_var.trace('w', on_config_change)
    thread_count_var.trace('w', on_config_change)
    batch_size_var.trace('w', on_config_change)
    prepend_text_var.trace('w', on_config_change)
    append_text_var.trace('w', on_config_change)
    caption_handling_var.trace('w', on_config_change)  # Trace for the caption handling radio buttons

    max_new_tokens_label = tk.Label(root, text="Max New Tokens (max number of tokens to generate):")
    max_new_tokens_label.pack(pady=5)
    max_new_tokens_entry = tk.Entry(root, textvariable=max_new_tokens_var, justify='center', width=5, validate='key', validatecommand=(validate_cmd, '%P'))
    max_new_tokens_entry.pack(pady=5)

    do_sample_check = tk.Checkbutton(root, text="Do Sample (random sampling):", variable=do_sample_var, command=toggle_sampling_options)
    do_sample_check.pack(pady=5)

    temperature_label = tk.Label(root, text="Temperature (control randomness of sampling):")
    top_k_label = tk.Label(root, text="Top-k (consider top k tokens):")
    top_p_label = tk.Label(root, text="Top-p (consider tokens with cumulative probability p):")

    temperature_entry = tk.Entry(root, textvariable=temperature_var, justify='center', width=5, validate='key', validatecommand=(validate_cmd, '%P'))
    top_k_entry = tk.Entry(root, textvariable=top_k_var, justify='center', width=5, validate='key', validatecommand=(validate_cmd, '%P'))
    top_p_entry = tk.Entry(root, textvariable=top_p_var, justify='center', width=5, validate='key', validatecommand=(validate_cmd, '%P'))

    # Frame to hold all three horizontally aligned elements
    horizontal_frame = tk.Frame(root)
    horizontal_frame.pack(pady=5, padx=5)

    thread_count_label = tk.Label(horizontal_frame, text="Thread Count (number of threads to use):")
    thread_count_label.pack(side=tk.LEFT, padx=5)
    thread_count_entry = tk.Entry(horizontal_frame, textvariable=thread_count_var, justify='center', width=5, validate='key', validatecommand=(validate_cmd, '%P'))
    thread_count_entry.pack(side=tk.LEFT, padx=5)

    batch_size_label = tk.Label(horizontal_frame, text="Batch Size (number of images to process at once):")
    batch_size_label.pack(side=tk.LEFT, padx=5)
    batch_size_entry = tk.Entry(horizontal_frame, textvariable=batch_size_var, justify='center', width=5, validate='key', validatecommand=(validate_cmd, '%P'))
    batch_size_entry.pack(side=tk.LEFT, padx=5)

    errors_button = tk.Button(root, textvariable=errors_var, command=show_errors)
    errors_button.pack(pady=10)

    start_button = tk.Button(root, text="Generate Captions", command=lambda: [process_files(), update_and_save_config()])
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop", command=stop_processing_func)
    stop_button.pack(pady=10)

    progress_bar = ttk.Progressbar(root, variable=progress, maximum=100)
    progress_bar.pack(pady=10, fill=tk.X)

    status_label = tk.Label(root, textvariable=status_var, fg="green")
    status_label.pack(pady=5)

    center_window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def select_files():
    global selected_files, save_directory, total_pages, original_selected_files
    filetypes = [("All Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff;*.tif;*.svg;*.webp")]
    filepaths = filedialog.askopenfilenames(title="Select Image Files", filetypes=filetypes)
    if filepaths:
        selected_files.clear()
        selected_files.extend(filepaths)
        original_selected_files = selected_files.copy()
        validate_selected_files()

        num_files_var.set(f"{len(selected_files)} files selected.")
        save_directory = os.path.dirname(selected_files[0])
        total_pages = (len(selected_files) + images_per_page - 1) // images_per_page
        if caption_window is not None:
            update_image_preview(content_canvas)

def validate_selected_files():
    global selected_files, num_files_var
    selected_files = [file for file in selected_files if os.path.exists(file)]
    num_files_var.set(f"{len(selected_files)} files selected.")

def toggle_buttons(state):
    state = tk.NORMAL if state else tk.DISABLED
    select_files_button.config(state=state)
    show_captions_button.config(state=state)
    prompt_entry.config(state=state)
    prepend_text_entry.config(state=state)
    append_text_entry.config(state=state)
    do_sample_check.config(state=state)
    temperature_entry.config(state=state)
    top_k_entry.config(state=state)
    top_p_entry.config(state=state)
    thread_count_entry.config(state=state)
    batch_size_entry.config(state=state)
    start_button.config(state=state)
    stop_button.config(state=tk.NORMAL)

def generate_caption(image_path, save_directory, q):
    if stop_processing:
        return

    try:
        load_model()

        filename = os.path.splitext(os.path.basename(image_path))[0]
        caption_file_path = os.path.join(save_directory, f"{filename}.txt")

        # Kiểm tra các lựa chọn của người dùng
        if os.path.exists(caption_file_path):
            if caption_handling_var.get() == 'skip':
                q.put(image_path)
                return
            elif caption_handling_var.get() == 'append':
                with open(caption_file_path, 'r', encoding='utf-8') as f:
                    existing_caption = f.read()
            else:
                existing_caption = ""
        else:
            existing_caption = ""

        image = PILImage.open(image_path).convert('RGB')
        if not isinstance(image, PILImage.Image):
            raise ValueError(f"Expected image to be of type PIL.Image.Image, but got {type(image)}")

        inputs = model.build_conversation_input_ids(
            tokenizer,
            query=prompt_var.get(),
            history=[],
            images=[image]
        )

        # Điều chỉnh dtype dựa trên bit_precision
        if bit_precision_var.get() == 32:
            image_tensor = inputs['images'][0].to('cuda').to(torch.float32)
        else:
            image_tensor = inputs['images'][0].to('cuda').to(torch.float16)

        inputs = {
            'input_ids': inputs['input_ids'].unsqueeze(0).to('cuda'),
            'token_type_ids': inputs['token_type_ids'].unsqueeze(0).to('cuda'),
            'attention_mask': inputs['attention_mask'].unsqueeze(0).to('cuda'),
            'images': [[image_tensor]],
        }

        gen_kwargs = {
            "max_new_tokens": max_new_tokens_var.get(),
            "do_sample": do_sample_var.get(),
            "temperature": temperature_var.get(),
            "top_k": top_k_var.get(),
            "top_p": top_p_var.get() if do_sample_var.get() else None,
            "num_beams": precision_var.get()
        }

        with torch.no_grad():
            outputs = model.generate(**inputs, **gen_kwargs)
            outputs = outputs[:, inputs['input_ids'].shape[1]:]
            new_caption = tokenizer.decode(outputs[0], skip_special_tokens=True)

        final_caption = f"{prepend_text_var.get()} {existing_caption} {new_caption} {append_text_var.get()}".strip()

        with open(caption_file_path, 'w', encoding='utf-8') as file:
            file.write(final_caption)

        q.put(image_path)
        torch.cuda.empty_cache()
    except torch.cuda.OutOfMemoryError as e:
        torch.cuda.empty_cache()
        error_message = f"CUDA OutOfMemoryError: {traceback.format_exc()}"
        print(error_message)
        q.put(error_message)
        error_messages.append(error_message)
    except Exception as e:
        error_message = f"Error processing image {image_path}: {traceback.format_exc()}"
        print(error_message)
        q.put(error_message)
        error_messages.append(error_message)


def worker(save_directory, num_threads, batch_size):
    try:
        progress.set(0)
        threads = []

        num_batches = math.ceil(len(selected_files) / batch_size)
        batch_size_per_thread = max(1, batch_size // num_threads)  # Số ảnh mỗi luồng xử lý trong một batch

        for batch_index in range(num_batches):
            if stop_processing:
                break

            start_index = batch_index * batch_size
            end_index = min(start_index + batch_size, len(selected_files))
            batch = selected_files[start_index:end_index]

            # Chia ảnh trong batch cho các luồng
            for i in range(0, len(batch), batch_size_per_thread):
                thread_batch = batch[i:i + batch_size_per_thread]
                thread = threading.Thread(target=generate_captions_for_batch, args=(thread_batch, save_directory, q))
                threads.append(thread)
                thread.start()

            # Đợi các luồng trong batch hiện tại hoàn thành
            for thread in threads:
                thread.join()
            threads.clear()

        q.put(None)
    except Exception as e:
        if not stop_processing:
            q.put(e)

def generate_captions_for_batch(batch, save_directory, q):
    for image_path in batch:
        generate_caption(image_path, save_directory, q)

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
            root.after(0, status_var.set(f"Error: {e}"))
    finally:
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

    validate_selected_files()

    if not selected_files or not save_directory:
        status_var.set("Please select images.")
        return

    toggle_buttons(False)

    threading.Thread(target=worker, args=(save_directory, thread_count_var.get(), batch_size_var.get())).start()
    threading.Thread(target=update_progress).start()

def stop_processing_func():
    global stop_processing
    stop_processing = True
    torch.cuda.empty_cache()
    status_var.set("Processing stopped.")

def open_caption_window():
    global caption_window, caption_frame, caption_text_widgets, current_page, total_pages, content_canvas
    if caption_window is not None:
        return
    
    validate_selected_files()

    caption_window = tk.Toplevel(root)
    caption_window.title("Image Thumbnails and Captions")
    caption_window.geometry("940x900")

    main_frame = tk.Frame(caption_window)
    main_frame.pack(fill=tk.BOTH, expand=True)

    search_frame = tk.Frame(main_frame)
    search_frame.pack(side=tk.TOP, fill=tk.X)

    search_entry = tk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

    search_button = tk.Button(search_frame, text="Search", command=search_captions)
    search_button.pack(side=tk.LEFT, padx=10)

    reset_button = tk.Button(search_frame, text="Reset Order", command=reset_order)
    reset_button.pack(side=tk.LEFT, padx=10)

    action_frame = tk.Frame(main_frame)
    action_frame.pack(side=tk.TOP, fill=tk.X)

    action_entry = tk.Entry(action_frame, textvariable=action_var)
    action_entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

    prepend_button = tk.Button(action_frame, text="Add to Beginning", command=lambda: add_to_captions("prepend"))
    prepend_button.pack(side=tk.LEFT, padx=5)

    append_button = tk.Button(action_frame, text="Add to End", command=lambda: add_to_captions("append"))
    append_button.pack(side=tk.LEFT, padx=5)

    insert_middle_button = tk.Button(action_frame, text="Add to Middle", command=lambda: add_to_captions("insert_middle"))
    insert_middle_button.pack(side=tk.LEFT, padx=5)

    delete_keyword_button = tk.Button(action_frame, text="Delete Keyword", command=delete_keyword_from_captions)
    delete_keyword_button.pack(side=tk.LEFT, padx=5)

    delete_images_button = tk.Button(action_frame, text="Delete Images with Keyword", command=delete_images_with_keyword)
    delete_images_button.pack(side=tk.LEFT, padx=5)

    content_canvas = tk.Canvas(main_frame)
    content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    caption_frame = tk.Frame(content_canvas)
    content_canvas.create_window((0, 0), window=caption_frame, anchor='nw')

    caption_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=content_canvas.yview)
    caption_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
    content_canvas.configure(yscrollcommand=caption_scrollbar.set)

    caption_frame.bind("<Configure>", lambda e: content_canvas.configure(scrollregion=content_canvas.bbox("all")))
    content_canvas.bind_all("<MouseWheel>", lambda event: content_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    # Định nghĩa hàm on_mouse_wheel
    def on_mouse_wheel(event):
        try:
            if content_canvas.winfo_exists():
                content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except tk.TclError:
            pass

    content_canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    def on_caption_window_close():
        global caption_window
        caption_window.destroy()
        caption_window = None

    caption_window.protocol("WM_DELETE_WINDOW", on_caption_window_close)

    update_image_preview(content_canvas)

def update_image_preview(content_canvas):
    global thumbnails, caption_text_widgets, current_page, images_per_page, total_pages
    if caption_frame is None:
        return

    for widget in caption_frame.winfo_children():
        if isinstance(widget, tk.Label) or isinstance(widget, tk.Text) or isinstance(widget, tk.Frame):
            widget.destroy()

    thumbnails.clear()
    caption_text_widgets.clear()

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
            thumbnails.append(thumbnail)

            img_label = tk.Label(caption_frame, image=thumbnail)
            img_label.grid(row=i*2, column=0, padx=5, pady=5, sticky="nsew")

            file_label = tk.Label(caption_frame, text=os.path.basename(file_path), font=('Helvetica', 12), wraplength=300, justify="left")
            file_label.grid(row=i*2, column=1, padx=5, pady=5, sticky="nsew")

            caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
            if os.path.exists(caption_file):
                with open(caption_file, 'r', encoding='utf-8') as file:
                    caption_text = file.read()
            else:
                caption_text = ""

            caption_var = tk.StringVar(value=caption_text)    

            caption_text_widget = tk.Text(caption_frame, width=50, height=3, wrap=tk.WORD, font=('Helvetica', 12))
            caption_text_widget.insert(tk.END, caption_text)
            caption_text_widget.grid(row=i*2, column=2, padx=5, pady=5, sticky="nsew")

            caption_var.trace_add("write", lambda *args, fp=file_path, cv=caption_var: save_caption(fp, cv.get()))

            caption_text_widget.bind("<KeyRelease>", lambda e, cv=caption_var, w=caption_text_widget: cv.set(w.get("1.0", "end-1c")))
            caption_text_widgets.append(caption_text_widget)

        except Exception as e:
            tk.Label(caption_frame, text="Error loading image").grid(row=i*2, column=0, columnspan=4, padx=5, pady=5)

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
    output_path = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(caption_text.strip())
    except Exception as e:
        print(f"Error saving captions: {e}")    

def search_captions():
    global selected_files
    search_term = search_var.get().lower().strip()
    if not search_term:
        return
    
    try:
        selected_files.sort(key=lambda x: search_score(x, search_term), reverse=True)
    except Exception as e:
        error_message = f"Error during sorting: {e}"
        print(error_message)
        error_messages.append(error_message)

    update_image_preview(content_canvas)

def search_score(file_path, search_term):
    caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
    try:
        if os.path.exists(caption_file):
           with open(caption_file, 'r', encoding='utf-8') as file:
               caption_text = file.read().lower()
               if search_term in caption_text:
                   return caption_text.count(search_term)
               
    except Exception as e:
        error_message = f"Error reading file {caption_file}: {e}"
        print(error_message)
        error_messages.append(error_message)           
    return 0

def reset_order():
    global selected_files
    selected_files = original_selected_files.copy()
    update_image_preview(content_canvas)

def add_to_captions(position):
    global selected_files
    keyword = action_var.get()
    if not keyword:
        return

    for file_path in selected_files:
        caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
        if os.path.exists(caption_file):
            with open(caption_file, 'r+', encoding='utf-8') as file:
                caption_text = file.read()
                if position == "prepend":
                    caption_text = f"{keyword} {caption_text}"
                elif position == "append":
                    caption_text = f"{caption_text} {keyword}"
                elif position == "insert_middle":
                    middle_index = len(caption_text) // 2
                    caption_text = f"{caption_text[:middle_index]} {keyword} {caption_text[middle_index:]}"
                file.seek(0)
                file.write(caption_text)
                file.truncate()

    update_image_preview(content_canvas)

def delete_keyword_from_captions():
    keyword = action_var.get().lower().strip()
    if not keyword:
        return

    for file_path in selected_files:
        caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
        if os.path.exists(caption_file):
            with open(caption_file, 'r+', encoding='utf-8') as file:
                caption_text = file.read().lower().replace(keyword, "")

                updated_caption = caption_text.replace(keyword, "").strip()

                file.seek(0)
                file.write(updated_caption)
                file.truncate()

    update_image_preview(content_canvas)

def delete_images_with_keyword():
    global selected_files
    keyword = action_var.get().lower()
    if not keyword:
        return
    
    files_to_delete = []
    for file_path in selected_files:
        caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
        if os.path.exists(caption_file):
            with open(caption_file, 'r', encoding='utf-8') as file:
                caption_text = file.read().lower()
                if keyword in caption_text:
                    files_to_delete.append(file_path)

    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            caption_file = os.path.join(save_directory, f"{os.path.basename(file_path)}_caption.txt")
            if os.path.exists(caption_file):
               os.remove(caption_file)
        except Exception as e:
            error_message = f"Error deleting file {file_path} or its caption: {e}"
            print(error_message)
            error_messages.append(error_message)

    selected_files = [file_path for file_path in selected_files if file_path not in files_to_delete]

    validate_selected_files()

    update_image_preview(content_canvas)

def return_to_menu():
    stop_processing_func()
    root.destroy()
    import main
    main.open_main_menu()

def on_closing():
    return_to_menu()

if __name__ == "__main__":
    open_image_to_caption()
