import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os

# Directly importing logic from Project2 (1) (1).py
from Project2 import encrypt, decrypt

class CipherVisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CipherVision - Secure Image Tool")
        self.root.geometry("700x600")
        self.root.configure(bg="#f5f5f5")

        self.file_path = None
        self.processed_img = None

        # --- Header ---
        tk.Label(root, text="CipherVision", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#2c3e50").pack(pady=10)
        
        # --- File Selection ---
        file_frame = tk.LabelFrame(root, text=" 1. Select Image ", padx=10, pady=10, bg="#f5f5f5")
        file_frame.pack(fill="x", padx=20, pady=5)
        
        self.btn_browse = tk.Button(file_frame, text="Browse Files", command=self.load_file)
        self.btn_browse.pack(side="left")
        
        self.lbl_path = tk.Label(file_frame, text="No file selected", bg="#f5f5f5", fg="#7f8c8d")
        self.lbl_path.pack(side="left", padx=10)

        # --- Password Input ---
        pass_frame = tk.LabelFrame(root, text=" 2. Security Key ", padx=10, pady=10, bg="#f5f5f5")
        pass_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(pass_frame, text="Password:", bg="#f5f5f5").pack(side="left")
        self.entry_pass = tk.Entry(pass_frame, show="*", width=40)
        self.entry_pass.pack(side="left", padx=10)

        # --- Actions ---
        action_frame = tk.Frame(root, bg="#f5f5f5")
        action_frame.pack(pady=15)

        self.btn_enc = tk.Button(action_frame, text="ENCRYPT", bg="#27ae60", fg="white", 
                                font=("Arial", 10, "bold"), width=15, command=self.run_encrypt)
        self.btn_enc.grid(row=0, column=0, padx=10)

        self.btn_dec = tk.Button(action_frame, text="DECRYPT", bg="#2980b9", fg="white", 
                                font=("Arial", 10, "bold"), width=15, command=self.run_decrypt)
        self.btn_dec.grid(row=0, column=1, padx=10)

        # --- Preview ---
        self.preview_container = tk.LabelFrame(root, text=" Result Preview ", bg="#f5f5f5")
        self.preview_container.pack(expand=True, fill="both", padx=20, pady=5)
        
        self.preview_label = tk.Label(self.preview_container, text="Preview will appear after processing", bg="#ecf0f1")
        self.preview_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Save ---
        self.btn_save = tk.Button(root, text="💾 Save Result to Disk", state="disabled", 
                                 command=self.save_result, height=2, font=("Arial", 10))
        self.btn_save.pack(fill="x", padx=20, pady=10)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.file_path = path
            self.lbl_path.config(text=os.path.basename(path), fg="#2c3e50")

    def process_preview(self, img_array):
        """Prepares the image for the Tkinter UI."""
        # Normalize so encrypted noise is visible
        display_img = cv2.normalize(img_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Maintain aspect ratio for preview
        h, w = display_img.shape
        max_size = 350
        scale = min(max_size/w, max_size/h)
        new_size = (int(w * scale), int(h * scale))
        
        img = Image.fromarray(display_img)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(image=img)
        
        self.preview_label.config(image=self.img_tk, text="")
        self.btn_save.config(state="normal")

    def run_encrypt(self):
        pwd = self.entry_pass.get()
        if not self.file_path or not pwd:
            return messagebox.showwarning("Warning", "Image and Password required!")

        img = cv2.imread(self.file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return messagebox.showerror("Error", "Could not read image file.")

        # Calls the full encryption pipeline
        # We capture only the first return (the encrypted image)
        self.processed_img, *_ = encrypt(img, pwd)
        self.process_preview(self.processed_img)
        messagebox.showinfo("Success", "Image Encrypted Successfully!")

    def run_decrypt(self):
        pwd = self.entry_pass.get()
        if not self.file_path or not pwd:
            return messagebox.showwarning("Warning", "Image and Password required!")

        img = cv2.imread(self.file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return messagebox.showerror("Error", "Could not read image file.")

        # Calls the full decryption pipeline[cite: 2]
        # Same password generates the same shuffle order internally[cite: 2]
        self.processed_img = decrypt(img, pwd)
        self.process_preview(self.processed_img)
        messagebox.showinfo("Success", "Decryption Attempt Complete!")

    def save_result(self):
        if self.processed_img is not None:
            path = filedialog.asksaveasfilename(defaultextension=".png", 
                                               filetypes=[("PNG file", "*.png")])
            if path:
                cv2.imwrite(path, self.processed_img)
                messagebox.showinfo("Saved", f"File saved: {os.path.basename(path)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CipherVisionApp(root)
    root.mainloop()