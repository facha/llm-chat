import sys
import os
import json
import openai
import signal
from dotenv import load_dotenv

GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

def load_config():
    load_dotenv() 
    os.environ.setdefault("OPENAI_API_KEY", "dummy-key")
    os.environ.setdefault("OPENAI_BASE_URL", "http://localhost:8080/v1")

class ChatClient:
    def __init__(self):
        self.client = openai.OpenAI()
        self.messages = []
        self.interrupt_requested = False
        self.is_generating = False

    def signal_handler(self, sig, frame):
        if self.is_generating:
            self.interrupt_requested = True
            print(f"\n{YELLOW}Operation interrupted. Returning to prompt...{RESET}")
        else:
            self.exit_gracefully()

    def get_completion(self, messages):
        try:
            self.is_generating = True
            response_text = ""
            for chunk in self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                stream=True
            ):
                if self.interrupt_requested:
                    self.interrupt_requested = False
                    self.is_generating = False
                    return response_text
                    
                if chunk.choices[0].delta.content:
                    new_text = chunk.choices[0].delta.content
                    response_text += new_text
                    print(new_text, end="", flush=True)
            return response_text
        finally:
            self.is_generating = False

    def show_raw_history(self):
        print(f"\n{CYAN}Raw Conversation History:{RESET}")
        print(json.dumps(self.messages, indent=2))
        print()

    def exit_gracefully(self):
        print(f"\n{YELLOW}Goodbye!{RESET}")
        sys.exit(0)

    def run(self):
        print(f"\n{GREEN}Chat with LLM{RESET}")
        print("Commands:")
        print("- Type 'exit' to quit")
        print("- Type 'hist' to show raw conversation history")
        print("- Press Ctrl+C to interrupt current response\n")

        while True:
            try:
                user_input = input(f"{MAGENTA}User{RESET}: ")
                
                if user_input.lower() == "exit":
                    self.exit_gracefully()
                elif user_input.lower() == "hist":
                    self.show_raw_history()
                    continue

                self.messages.append({"role": "user", "content": user_input})
                print(f"{CYAN}LLM:{RESET}", end=" ")
                
                response_text = self.get_completion(self.messages)
                if response_text:
                    self.messages.append({"role": "assistant", "content": response_text})
                print()

            except KeyboardInterrupt:
                if not self.is_generating:
                    self.exit_gracefully()
                continue
            except EOFError:
                self.exit_gracefully()

def main():
    try:
        load_config()
        chat_client = ChatClient()
        signal.signal(signal.SIGINT, chat_client.signal_handler)
        chat_client.run()
    except Exception as e:
        print(f"{RED}Fatal error: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
