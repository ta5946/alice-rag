import os
import subprocess

command = ["python", "src/chatbot/mattermost_listener.py"]

if not os.path.exists("logs"):
    os.makedirs("logs")

with open("logs/chatbot.log", "w") as log_file:
    process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid, # detach from terminal
        close_fds=True
    )

print(f"run.py with PID: {process.pid}")
