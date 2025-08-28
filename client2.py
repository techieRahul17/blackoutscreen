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
lab = tk.Label(text="Hello",font = ("Courier New",20,"bold"),bg="black",fg="white")

def label_text():
    # update random text
    lab.config(text="".join(random.choices("qwertyuiopasdfghjklzxcvbnm", k=500)))
    lab.pack(expand=True)  # ensure it's visible
    # schedule again after 1000 ms
    root.after(1000, label_text)

# Start the label updater once
root.after(1000, label_text)
def process_queue():
    while not event_queue.empty():
        event, value = event_queue.get()
        if event == "blackout":
            root.deiconify()
            
            duration = value
            root.after(duration, lambda: root.withdraw())
        elif event == "endBlackout":
            root.withdraw()
    root.after(50, process_queue)  # check queue every 50ms

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

# Run Socket.IO in a separate thread so Tkinter mainloop is free
def socket_thread():
    sio.connect("http://10.106.60.188:3000")  # replace with your server IP
    sio.wait()

threading.Thread(target=socket_thread, daemon=True).start()

root.protocol("WM_DELETE_WINDOW",lambda:None)
root.bind("<Alt-F4>",lambda e:"break")
root.bind("<Alt-Tab>",lambda e:"break")
#root.bind("<Win>",lambda e:"break")
# Run Tkinter main loop
root.mainloop()
