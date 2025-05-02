import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests

class FLStudioMCPClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FL Studio AI MCP")
        self.root.geometry("500x300")
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Enter your request:").grid(row=0, column=0, sticky=tk.W)
        self.text_input = tk.Text(main_frame, height=5, width=50)
        self.text_input.grid(row=1, column=0, pady=5)
        
        ttk.Button(main_frame, text="Generate MIDI", command=self.generate_midi).grid(row=2, column=0, pady=10)
        
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=3, column=0, pady=5)
    
    def generate_midi(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            self.status_label.config(text="Please enter some text")
            return
        self.status_label.config(text="Generating MIDI...")
        try:
            response = requests.post(
                "http://localhost:8000/generate/midi",
                json={"text": text}
            )
            if response.status_code == 200:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".mid",
                    filetypes=[("MIDI files", "*.mid")],
                    initialfile="generated_ai_midi.mid"
                )
                if file_path:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    self.status_label.config(text=f"MIDI file saved: {file_path}")
                    messagebox.showinfo("Success", f"MIDI file saved: {file_path}")
                else:
                    self.status_label.config(text="Save cancelled.")
            else:
                self.status_label.config(text=f"Error: {response.status_code}")
                messagebox.showerror("Error", f"Server error: {response.text}")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = FLStudioMCPClient()
    client.run() 