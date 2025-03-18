import sys, threading, time
from PyQt5 import QtWidgets, QtGui, QtCore
from ai_engine import AIEngine

class JarvisWindow(QtWidgets.QMainWindow):
    response_ready = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ai_engine = AIEngine()
        self.response_ready.connect(self.finish_response)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Jarvis - AI Assistant")
        self.resize(900, 600)
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Top area: AI Mode drop-down
        mode_layout = QtWidgets.QHBoxLayout()
        mode_label = QtWidgets.QLabel("AI Mode:")
        mode_label.setStyleSheet("color: #f0f0f0; font-family: 'Segoe UI'; font-size: 11pt;")
        mode_layout.addWidget(mode_label)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                color: #f0f0f0;
                font-family: 'Segoe UI';
                font-size: 11pt;
                padding: 5px;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        # Add model modes
        self.mode_combo.addItems(["phi3_only", "openai_only", "hybrid"])
        self.mode_combo.setCurrentText(self.ai_engine.ai_mode)
        self.mode_combo.currentTextChanged.connect(self.change_ai_mode)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        # Chat history area
        self.chat_history = QtWidgets.QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #f0f0f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                border: none;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.chat_history)
        # Initial welcome message
        self.append_chat("Jarvis", "Hello! I'm Jarvis, your AI assistant. How can I help you today?")

        # Input area layout
        input_layout = QtWidgets.QHBoxLayout()
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                color: #f0f0f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #66ccff;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: #f0f0f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #66ccff;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: #f0f0f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        self.stop_button.clicked.connect(self.stop_response)
        input_layout.addWidget(self.stop_button)
        main_layout.addLayout(input_layout)

        # Thinking indicator area
        self.thinking_label = QtWidgets.QLabel("")
        self.thinking_label.setAlignment(QtCore.Qt.AlignCenter)
        self.thinking_label.setStyleSheet("""
            QLabel {
                color: #66ccff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
        """)
        main_layout.addWidget(self.thinking_label)

        # Timer for pulsing dots
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_thinking)
        self.thinking_state = 0

        # For response timing
        self.start_time = None

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.append_chat("You", text)
        self.input_field.clear()

        # Start the thinking indicator
        self.thinking_label.setText("Thinking")
        self.thinking_state = 0
        self.timer.start(500)

        # Record start time
        self.start_time = time.time()
        self.ai_engine.stop_response_flag = False

        # Get AI response in a background thread
        threading.Thread(target=self.get_response_thread, args=(text,), daemon=True).start()

    def get_response_thread(self, text):
        print("[DEBUG] Sending message to AI engine:", text)
        response = self.ai_engine.get_response(text, update_chat_live=lambda x: None)
        print("[DEBUG] Received response from AI engine:", repr(response))
        self.response_ready.emit(response)

    @QtCore.pyqtSlot(str)
    def finish_response(self, response):
        self.timer.stop()
        self.thinking_label.clear()
        thought_time = time.time() - self.start_time if self.start_time else 0
        self.append_chat("System", f"Thought for {thought_time:.2f} seconds")
        self.append_chat("Jarvis", response.strip())
        print("[DEBUG] Chat updated successfully")

    def update_thinking(self):
        self.thinking_state = (self.thinking_state % 3) + 1
        self.thinking_label.setText("Thinking" + "." * self.thinking_state)

    def append_chat(self, sender, message):
        self.chat_history.setReadOnly(False)
        formatted = f"<p><b>{sender}:</b> {message}</p>"
        self.chat_history.append(formatted)
        self.chat_history.setReadOnly(True)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def stop_response(self):
        print("[DEBUG] Stopping response generation")
        self.ai_engine.stop_response_flag = True
        self.thinking_label.setText("Stopping...")

    def change_ai_mode(self, mode):
        print(f"[DEBUG] Changing AI mode to: {mode}")
        self.ai_engine.set_ai_mode(mode)
        # Optionally, display a system message that the mode changed:
        self.append_chat("System", f"AI Mode switched to: {mode}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    # Create dark palette
    dark_palette = QtGui.QPalette()
    dark_color = QtGui.QColor(45, 45, 45)
    dark_palette.setColor(QtGui.QPalette.Window, dark_color)
    dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Button, dark_color)
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    app.setPalette(dark_palette)
    
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec_())
