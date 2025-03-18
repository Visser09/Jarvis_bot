import requests
import json
import os
import tkinter as tk
from memory import Memory
from dotenv import load_dotenv

class AIEngine:
    def __init__(self, model_name="phi3", api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url
        self.memory = Memory()
        self.stop_response_flag = False

        # Load OpenAI API key from .env
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Debugging: Print the API key to confirm it's loaded
        if self.openai_api_key:
            print(f"[DEBUG] OpenAI API Key Loaded: {self.openai_api_key[:5]}********")
        else:
            print("[DEBUG] OpenAI API Key is missing!")

        self.openai_url = "https://api.openai.com/v1/chat/completions"

        # 🔥 FIX: Ensure `ai_mode` exists
        self.ai_mode = "hybrid"  # Possible values: "phi3_only", "openai_only", "hybrid"

        # Define categories where OpenAI should be used
        self.factual_categories = [
            "who won", "latest", "current", "real-time", "news",
            "historical event", "what happened in", "results of",
            "final score", "winner of"
        ]

        # Caching for AI responses
        self.cache = {}


    def get_response(self, user_input, update_chat_live):
        """Handles AI response based on selected mode."""
        print(f"[DEBUG] Current AI mode: {self.ai_mode}")

        # Check cache first
        if user_input in self.cache:
            print("[DEBUG] Returning cached response...")
            cached_response = self.cache[user_input]
            update_chat_live(cached_response)
            return cached_response

        # Mode logic
        if self.ai_mode == "phi3_only":
            print("[DEBUG] Using Phi-3 only...")
            final_response = f"(Phi-3) {self.ask_phi3(user_input)}"

        elif self.ai_mode == "openai_only":
            print("[DEBUG] Using OpenAI only...")
            final_response = f"(OpenAI) {self.get_openai_response(user_input)}"

        else:  # Hybrid Mode
            print("[DEBUG] Asking Phi-3...")
            phi3_response = self.ask_phi3(user_input)

            if self.should_use_openai(user_input):
                print("[DEBUG] Phi-3's response may not be reliable, asking OpenAI directly...")
                final_response = f"(OpenAI) {self.get_openai_response(user_input)}"
            else:
                final_response = f"(Phi-3) {phi3_response}"

        # Clean up response
        final_response = final_response.replace("Jarvis:", "").strip()

        # Store response in cache
        self.cache[user_input] = final_response
        self.memory.store_conversation(user_input, final_response)

        # Update chat UI
        update_chat_live(final_response)
        return final_response

    def ask_phi3(self, user_input):
        """Queries Phi-3 API for a response."""
        prompt = f"User: {user_input}\nAI:"
        data = {"model": self.model_name, "prompt": prompt, "stream": False}  # No streaming

        try:
            response = requests.post(self.api_url, json=data)
            response_json = response.json()
            return response_json.get("response", "Error: No response from Phi-3.")
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

    def get_openai_response(self, user_input):
        """Calls OpenAI API only when necessary."""
        if not self.openai_api_key:
            print("[DEBUG] OpenAI API key is missing or not loaded.")
            return "I couldn't find an answer, and OpenAI access is not configured."

        print(f"[DEBUG] Using OpenAI API key: {self.openai_api_key[:5]}********")

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o",  # Switched to GPT-4o for better accuracy
            "messages": [
                {"role": "system", "content": "You are an AI assistant providing factual, up-to-date information."},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.3
        }

        try:
            print("[DEBUG] Sending request to OpenAI...")
            response = requests.post(self.openai_url, headers=headers, json=data)

            # Print raw response status and content for debugging
            print(f"[DEBUG] OpenAI response status: {response.status_code}")
            print(f"[DEBUG] OpenAI raw response: {response.text}")

            response_json = response.json()

            # Check if "choices" is in the response
            if "choices" in response_json:
                return response_json["choices"][0]["message"]["content"].strip()
            else:
                error_message = response_json.get("error", {}).get("message", "Unknown error")
                return f"OpenAI API Error: {error_message}"

        except requests.exceptions.RequestException as e:
            print("[DEBUG] OpenAI request failed:", e)
            return f"Error contacting OpenAI: {str(e)}"

    def should_use_openai(self, user_input):
        """Determines if OpenAI should be used based on the type of query."""
        return any(keyword in user_input.lower() for keyword in self.factual_categories)

    def set_ai_mode(self, mode):
        """Allows switching between AI modes dynamically."""
        if mode in ["phi3_only", "openai_only", "hybrid"]:
            self.ai_mode = mode
            print(f"[DEBUG] AI mode changed to: {mode}")
        else:
            print("[DEBUG] Invalid AI mode selection.")

# GUI Integration
class AIInterface:
    def __init__(self, root, ai_engine):
        self.root = root
        self.ai_engine = ai_engine
        self.root.title("AI Assistant")

        # Dropdown for AI Mode Selection
        self.ai_mode_var = tk.StringVar(value=self.ai_engine.ai_mode)
        self.ai_mode_dropdown = tk.OptionMenu(
            root, self.ai_mode_var, "phi3_only", "openai_only", "hybrid", self.change_ai_mode
        )
        self.ai_mode_dropdown.pack(pady=10)

        # Chat display
        self.chat_history = tk.Text(root, wrap="word", state="disabled", height=20, width=60)
        self.chat_history.pack(pady=10)

        # Input field
        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.pack(pady=5)
        self.input_entry.bind("<Return>", self.process_input)

        # Send button
        self.send_button = tk.Button(root, text="Send", command=self.process_input)
        self.send_button.pack(pady=5)

    def process_input(self, event=None):
        user_input = self.input_entry.get()
        if not user_input.strip():
            return
        self.input_entry.delete(0, tk.END)
        self.update_chat(f"You: {user_input}")
        response = self.ai_engine.get_response(user_input, self.update_chat)
        self.update_chat(f"Jarvis: {response}")

    def update_chat(self, message):
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", message + "\n")
        self.chat_history.config(state="disabled")
        self.chat_history.see("end")

    def change_ai_mode(self, mode):
        self.ai_engine.set_ai_mode(mode)
        print(f"[DEBUG] AI mode switched to: {mode}")

if __name__ == "__main__":
    root = tk.Tk()
    ai_engine = AIEngine()
    app = AIInterface(root, ai_engine)
    root.mainloop()
