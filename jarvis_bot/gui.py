import tkinter as tk
from tkinter import ttk
import threading
import time
from ai_engine import AIEngine

class JarvisGUI:
    def __init__(self, root, ai_engine):
        self.root = root
        self.ai_engine = ai_engine
        self.root.title("AI Assistant")

        # Window sizing & centering
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.6)
        height = int(screen_height * 0.6)
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Dark mode styling
        self.root.configure(bg="#2b2b2b")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("DarkFrame.TFrame", background="#2b2b2b")
        style.configure("DarkButton.TButton",
                        background="#3c3f41", foreground="#ffffff",
                        font=("Segoe UI", 11), padding=10, borderwidth=0)
        style.map("DarkButton.TButton", background=[("active", "#464a4d")])
        style.configure("DarkEntry.TEntry",
                        foreground="#ffffff", fieldbackground="#3c3f41",
                        font=("Segoe UI", 11), padding=5, borderwidth=0)
        style.configure("DarkCombobox.TCombobox",
                        foreground="#ffffff", fieldbackground="#3c3f41",
                        background="#3c3f41", font=("Segoe UI", 11))
        style.map("DarkCombobox.TCombobox",
                  fieldbackground=[("readonly", "#3c3f41")],
                  selectbackground=[("readonly", "#3c3f41")])
        style.configure("DarkLabel.TLabel",
                        background="#2b2b2b", foreground="#ffffff",
                        font=("Segoe UI", 11))

        # Top frame: AI mode selection
        top_frame = ttk.Frame(self.root, style="DarkFrame.TFrame")
        top_frame.pack(fill="x", padx=10, pady=10)
        self.ai_mode_var = tk.StringVar(value=self.ai_engine.ai_mode)
        self.ai_mode_dropdown = ttk.Combobox(
            top_frame,
            textvariable=self.ai_mode_var,
            values=["phi3_only", "openai_only", "hybrid"],
            state="readonly",
            style="DarkCombobox.TCombobox"
        )
        self.ai_mode_dropdown.bind("<<ComboboxSelected>>", self.change_ai_mode)
        self.ai_mode_dropdown.pack(side="left", padx=5)

        # Chat frame
        chat_frame = ttk.Frame(self.root, style="DarkFrame.TFrame")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.chat_history = tk.Text(
            chat_frame,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 11),
            bg="#3c3f41",
            fg="#ffffff",
            relief="flat",
            padx=10,
            pady=10
        )
        self.chat_history.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_history.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.chat_history.configure(yscrollcommand=self.scrollbar.set)

        # Define two text tags for user and bot
        self.chat_history.tag_config(
            "user",
            foreground="#99ff99",  # light green
            font=("Segoe UI", 11, "bold"),
            spacing1=5,  # extra spacing above
            spacing3=5   # extra spacing below
        )
        self.chat_history.tag_config(
            "bot",
            foreground="#ffcc66",  # light orange
            font=("Segoe UI", 11),
            spacing1=5,
            spacing3=5
        )

        # Input frame
        input_frame = ttk.Frame(self.root, style="DarkFrame.TFrame")
        input_frame.pack(fill="x", padx=10, pady=5)
        self.entry = ttk.Entry(input_frame, style="DarkEntry.TEntry")
        self.entry.insert(0, "Type your message...")
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", self.add_placeholder)
        self.entry.bind("<Return>", self.send_message)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)

        # Button frame
        button_frame = ttk.Frame(self.root, style="DarkFrame.TFrame")
        button_frame.pack(fill="x", padx=10, pady=5)

        self.send_button = ttk.Button(
            button_frame,
            text="Send",
            command=self.send_message,
            style="DarkButton.TButton"
        )
        self.send_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Response",
            command=self.stop_response,
            style="DarkButton.TButton"
        )
        self.stop_button.pack(side="right", padx=5)

        # Frame at bottom for pulsing circle (like before)
        thinking_frame = ttk.Frame(self.root, style="DarkFrame.TFrame")
        thinking_frame.pack(side="bottom", fill="x", pady=5)
        self.thinking_canvas = tk.Canvas(thinking_frame, width=50, height=50, bg="#2b2b2b", highlightthickness=0)
        self.thinking_canvas.pack(pady=5)
        self.circle_id = None
        self.circle_radius = 10
        self.grow = True

        # For measuring how long the AI took
        self.start_time = None

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input or user_input == "Type your message...":
            return

        # Insert the user's text with the "user" tag
        self.add_chat_line(f"You: {user_input}", "user")
        self.entry.delete(0, tk.END)

        # Start the pulsing circle
        self.start_thinking()

        # Record the start time
        self.start_time = time.time()

        # Offload AI call to a thread
        threading.Thread(target=self.process_response, args=(user_input,), daemon=True).start()

    def process_response(self, user_input):
        # Get final response (no partial text)
        response = self.ai_engine.get_response(user_input, update_chat_live=lambda x: None)
        self.root.after(0, self.finish_response, response)

    def finish_response(self, response):
        # Stop pulsing circle
        self.stop_thinking()

        # Calculate how long the AI spent thinking
        if self.start_time:
            thought_time = time.time() - self.start_time
            # Insert a line in chat: "Thought for X.XX seconds" with "bot" style
            self.add_chat_line(f"Thought for {thought_time:.2f} seconds", "bot")

        # Insert the final AI response with the "bot" tag
        self.add_chat_line(response.strip(), "bot")

    # Pulsing circle logic
    def start_thinking(self):
        self.circle_radius = 10
        self.grow = True
        self.draw_circle()
        self.animate_circle()

    def stop_thinking(self):
        self.grow = False
        self.thinking_canvas.delete("all")

    def draw_circle(self):
        self.thinking_canvas.delete("all")
        cx = 25
        cy = 25
        r = self.circle_radius
        self.thinking_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#66ccff", outline="")

    def animate_circle(self):
        if not self.grow:
            return

        if self.circle_radius >= 15:
            self.grow = False
        elif self.circle_radius <= 5:
            self.grow = True

        if self.grow:
            self.circle_radius += 1
        else:
            self.circle_radius -= 1

        self.draw_circle()
        self.root.after(100, self.animate_circle)

    # Updated add_chat_line method with optional tag
    def add_chat_line(self, message, tag=None):
        self.chat_history.config(state="normal")
        if tag:
            self.chat_history.insert("end", message + "\n", tag)
        else:
            self.chat_history.insert("end", message + "\n")
        self.chat_history.config(state="disabled")
        self.chat_history.see("end")

    def stop_response(self):
        self.ai_engine.stop_response_flag = True

    def clear_placeholder(self, event):
        if self.entry.get() == "Type your message...":
            self.entry.delete(0, tk.END)

    def add_placeholder(self, event):
        if not self.entry.get():
            self.entry.insert(0, "Type your message...")

    def change_ai_mode(self, event=None):
        mode = self.ai_mode_var.get()
        self.ai_engine.set_ai_mode(mode)
        print(f"[DEBUG] AI mode switched to: {mode}")

if __name__ == "__main__":
    root = tk.Tk()
    ai_engine = AIEngine()
    app = JarvisGUI(root, ai_engine)
    root.mainloop()
