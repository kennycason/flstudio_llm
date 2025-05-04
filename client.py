import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests

class FLStudioLLMClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FL Studio LLM")
        self.root.geometry("500x340")
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Enter your request:").grid(row=0, column=0, sticky=tk.W)
        self.text_input = tk.Text(main_frame, height=5, width=50)
        self.text_input.grid(row=1, column=0, pady=5)
        
        ttk.Label(main_frame, text="Output type:").grid(row=2, column=0, sticky=tk.W)
        self.output_type = ttk.Combobox(main_frame, values=[
            "MIDI File (.mid)",
            "Serum Preset (.fxp)",
            "3xOsc Preset (.fst)"
        ])
        self.output_type.grid(row=3, column=0, pady=5)
        self.output_type.set("MIDI File (.mid)")
        
        ttk.Button(main_frame, text="Generate", command=self.generate).grid(row=4, column=0, pady=10)
        
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=5, column=0, pady=5)
    
    def generate(self):
        text = self.text_input.get("1.0", tk.END).strip()
        output_type = self.output_type.get()
        if not text:
            self.status_label.config(text="Please enter some text")
            return
        self.status_label.config(text=f"Generating {output_type}...")
        try:
            if output_type == "MIDI File (.mid)":
                endpoint = "http://localhost:8000/generate/midi"
                filetypes = [("MIDI files", "*.mid")]
                default_ext = ".mid"
                default_name = "generated_ai_midi.mid"
            elif output_type == "Serum Preset (.fxp)":
                endpoint = "http://localhost:8000/generate/fxp"
                filetypes = [("Serum Preset files", "*.fxp")]
                default_ext = ".fxp"
                default_name = "generated_serum_preset.fxp"
            elif output_type == "3xOsc Preset (.fst)":
                endpoint = "http://localhost:8000/generate/3xosc-fst"
                filetypes = [("3xOsc Preset files", "*.fst")]
                default_ext = ".fst"
                default_name = "generated_3xosc_preset.fst"
            else:
                self.status_label.config(text="Unknown output type selected.")
                return
            response = requests.post(endpoint, json={"text": text})
            if response.status_code == 200:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=default_ext,
                    filetypes=filetypes,
                    initialfile=default_name
                )
                if file_path:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    self.status_label.config(text=f"{output_type} file saved: {file_path}")
                    messagebox.showinfo("Success", f"{output_type} file saved: {file_path}")
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
    client = FLStudioLLMClient()
    client.run() 