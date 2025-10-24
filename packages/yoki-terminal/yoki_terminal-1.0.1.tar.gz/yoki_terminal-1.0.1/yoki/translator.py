import os
import platform
import google.generativeai as genai
from .config import load_api_key

SYSTEM_PROMPT = """
You are a shell command generator.
The user is on a {os_name} operating system.
Convert the user's natural language request into a single valid shell command for their OS.
Output ONLY the command and nothing else.
"""

class Translator:
    def __init__(self):
        api_key = load_api_key()
        if not api_key:
            raise ValueError("❌ Missing API key. Please run 'yoki setkey YOUR_API_KEY'.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.os_name = platform.system()  # e.g., 'Windows', 'Linux', 'Darwin'

    def translate(self, text: str) -> str:
        try:
            prompt = f"{SYSTEM_PROMPT}\nUser: {text}\nCommand:"
            response = self.model.generate_content(prompt)
            cmd = response.text.strip().split("\n")[0]

            # Remove backticks for Windows compatibility
            import platform
            if platform.system() == "Windows":
                cmd = cmd.replace("`", "").strip()

            return cmd
        except Exception as e:
            return f"# Error generating command: {e}"

