import socketio
import platform
import tkinter as tk
from queue import Queue
import threading
import time
import random

sio = socketio.Client()
event_queue = Queue()

# Tkinter overlay in main thread
root = tk.Tk()
root.withdraw()  # hide initially
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg='black')
lab = tk.Label(text="Hello", font=("Courier New", 20, "bold"), bg="black", fg="white")

def label_text():
    lab.config(text="".join(random.choices("qwertyuiopasdfghjklzxcvbnm", k=500)))
    lab.pack(expand=True)
    root.after(1000, label_text)

root.after(1000, label_text)

def process_queue():
    while not event_queue.empty():
        event, value = event_queue.get()
        if event == "blackout":
            # --- FIX IS HERE ---
            # Tell the OS this is a tool window that shouldn't get focus
            root.attributes('-toolwindow', True)
            root.deiconify()
            
            duration = value
            # Schedule the hide and reset the attribute
            root.after(duration, lambda: (root.withdraw(), root.attributes('-toolwindow', False)))
            
        elif event == "endBlackout":
            root.withdraw()
            # Also reset the attribute here
            root.attributes('-toolwindow', False)
            
    root.after(50, process_queue)

root.after(50, process_queue)

# Socket.IO events
@sio.event
def connect():
    print("Connected to server")
    hostname = platform.node()
    sio.emit("register_client", {"hostname": hostname})

@sio.on("your_id")
def on_your_id(player_id):
    print("My player ID:", player_id)

@sio.on("blackout")
def on_blackout(duration):
    print(f"Blackout triggered for {duration}ms")
    event_queue.put(("blackout", duration))

@sio.on("endBlackout")
def on_end_blackout():
    print("Blackout ended by admin")
    event_queue.put(("endBlackout", None))

@sio.event
def disconnect():
    print("Disconnected from server")

# Run Socket.IO in a separate thread
def socket_thread():
    try:
        sio.connect("http://192.168.0.5:3000")  # replace with your server IP
        sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")

threading.Thread(target=socket_thread, daemon=True).start()

# Prevent closing
root.protocol("WM_DELETE_WINDOW", lambda: None)
root.bind("<Alt-F4>", lambda e: "break")
root.bind("<Alt-Tab>", lambda e: "break")

# Run Tkinter main loop
root.mainloop()