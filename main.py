import tkinter as tk
from tkinter import messagebox
import webbrowser
from image_converter import open_image_converter
from image_filter import open_image_filter
from rotate_flip import open_image_rotate_flip
from image_error_fix import open_image_error_fix
from image_to_tag import open_image_to_tag
from image_to_caption import open_image_to_caption  # Import the function from image_to_caption.py
from photo_fantasy import open_photo_fantasy
from shuffle_image import open_image_shuffle  # Import the function from shuffle_image.py

def open_main_menu():
    root = tk.Tk()
    root.title("IMageDucHaiten")

    def center_window(window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def open_converter_app():
        root.destroy()
        open_image_converter()

    def open_image_filter_app():
        root.destroy()
        open_image_filter()

    def open_rotate_flip_app():
        root.destroy()
        open_image_rotate_flip()

    def open_image_error_fix_app():
        root.destroy()
        open_image_error_fix()

    def open_image_to_tag_app():
        root.destroy()
        open_image_to_tag()

    def open_image_to_caption_app():
        root.destroy()
        open_image_to_caption()

    def open_photo_fantasy_app():
        root.destroy()
        open_photo_fantasy()

    def open_shuffle_image_app():
        root.destroy()
        open_image_shuffle()

    def open_future_app():
        messagebox.showinfo("Information", "Other applications are still under development.")

    def exit_app():
        root.destroy()

    def open_discord():
        webbrowser.open("https://discord.gg/vKEW6jqa49")

    def open_patreon():
        webbrowser.open("https://www.patreon.com/duchaitenreal")

    def open_paypal():
        webbrowser.open("https://www.paypal.com/paypalme/duchaiten")

    # Setup the interface
    top_frame = tk.Frame(root)
    top_frame.pack(fill='x', padx=10, pady=10)

    discord_button = tk.Button(top_frame, text="Discord", font=('Helvetica', 12), command=open_discord)
    discord_button.pack(side='left')

    patreon_button = tk.Button(top_frame, text="Patreon", font=('Helvetica', 12), command=open_patreon)
    patreon_button.pack(side='right')

    paypal_button = tk.Button(top_frame, text="PayPal", font=('Helvetica', 12), command=open_paypal)
    paypal_button.pack(side='right')

    title_label = tk.Label(root, text="IMageDucHaiten", font=('Helvetica', 24))
    title_label.pack(pady=20)

    converter_button = tk.Button(root, text="Image Converter", font=('Helvetica', 16), command=open_converter_app)
    converter_button.pack(pady=20)

    image_filter_button = tk.Button(root, text="Image Filter", font=('Helvetica', 16), command=open_image_filter_app)
    image_filter_button.pack(pady=20)

    rotate_flip_button = tk.Button(root, text="Rotate & Flip", font=('Helvetica', 16), command=open_rotate_flip_app)
    rotate_flip_button.pack(pady=20)

    error_fix_button = tk.Button(root, text="Image Error Fix", font=('Helvetica', 16), command=open_image_error_fix_app)
    error_fix_button.pack(pady=20)

    caption_button = tk.Button(root, text="Image To Tag", font=('Helvetica', 16), command=open_image_to_tag_app)
    caption_button.pack(pady=20)

    image_to_caption_button = tk.Button(root, text="Image To Caption", font=('Helvetica', 16), command=open_image_to_caption_app)
    image_to_caption_button.pack(pady=20)

    photo_fantasy_button = tk.Button(root, text="Photo Fantasy", font=('Helvetica', 16), command=open_photo_fantasy_app)
    photo_fantasy_button.pack(pady=20)

    shuffle_image_button = tk.Button(root, text="Shuffle Image", font=('Helvetica', 16), command=open_shuffle_image_app)
    shuffle_image_button.pack(pady=20)

    future_app_button = tk.Button(root, text="Future App Template", font=('Helvetica', 16), command=open_future_app)
    future_app_button.pack(pady=20)

    exit_button = tk.Button(root, text="Exit", font=('Helvetica', 16), command=exit_app)
    exit_button.pack(pady=20)

    center_window(root)
    root.geometry("550x950")  # Set the window size larger
    root.mainloop()

if __name__ == "__main__":
    open_main_menu()
