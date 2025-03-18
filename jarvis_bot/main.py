from gui import JarvisGUI
from ai_engine import AIEngine
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    ai_engine = AIEngine()
    app = JarvisGUI(root, ai_engine)
    root.mainloop()
