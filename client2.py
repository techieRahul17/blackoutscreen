import socketio, platform, tkinter as tk, threading, time, random, os, sys
from queue import Queue

sio = socketio.Client()
event_queue = Queue()

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# ---------------- Quotes ----------------
QUOTES = [
    "Keep going. Everything you need will come at the perfect time.",
    "Small steps every day add up to big results.",
    "Your only limit is you.",
    "Trust the process. Do the work.",
    "Discipline beats motivation when motivation fades.",
    "Focus on progress, not perfection.",
    "You’ve got this. One keypress at a time."
]
def random_quote(): return random.choice(QUOTES)

# ---------------- Tk Root ----------------
root = tk.Tk()
root.withdraw()
root.overrideredirect(True)
root.attributes("-topmost", True)

# Make fully opaque for Linux
root.attributes("-alpha", 1.0)  # FULL opacity

canvas = tk.Canvas(root, highlightthickness=0, bg="black")
canvas.pack(fill="both", expand=True)

quote_var = tk.StringVar(value=random_quote())
sub_var   = tk.StringVar(value="")

quote_lbl = tk.Label(canvas, textvariable=quote_var,
                     font=("Segoe UI", 30, "bold"),
                     bg="black", fg="white", wraplength=1000, justify="center")
sub_lbl = tk.Label(canvas, textvariable=sub_var,
                   font=("Segoe UI", 16), bg="black", fg="#cccccc",
                   wraplength=1000, justify="center")

quote_lbl.place(relx=0.5, rely=0.45, anchor="center")
sub_lbl.place(relx=0.5, rely=0.6, anchor="center")

overlay_until = 0
overlay_visible = False

# -------- Windows special handling --------
if IS_WINDOWS:
    import ctypes
    user32 = ctypes.windll.user32
    GWL_EXSTYLE = -20
    WS_EX_LAYERED     = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_TOOLWINDOW  = 0x00000080
    WS_EX_NOACTIVATE  = 0x08000000
    LWA_ALPHA = 0x02
    HWND_TOPMOST = -1
    SWP_NOMOVE=0x2; SWP_NOSIZE=0x1; SWP_NOACTIVATE=0x10; SWP_SHOWWINDOW=0x40
    def win_apply_clickthrough(hwnd):
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex |= WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
        # Set opacity to fully opaque (255)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        user32.SetWindowPos(hwnd, HWND_TOPMOST,0,0,0,0,
            SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW)

# -------- Functions --------
def set_fullscreen():
    w,h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")

def show_overlay(duration):
    global overlay_visible, overlay_until
    quote_var.set(random_quote())
    set_fullscreen()
    if IS_WINDOWS:
        hwnd = root.winfo_id()
        root.deiconify()
        win_apply_clickthrough(hwnd)
    elif IS_LINUX:
        # ask WM to treat as dock so it doesn’t steal focus
        try: root.wm_attributes("-type", "dock")
        except: pass
        root.deiconify()
        root.lift()
    overlay_until = int(time.time()*1000)+duration
    overlay_visible = True

def hide_overlay():
    global overlay_visible
    overlay_visible = False
    root.withdraw()

def ticker():
    if overlay_visible:
        now = int(time.time()*1000)
        rem = max(0, overlay_until-now)
        sub_var.set(f"Blackout • Ends in {rem//1000}s (keep typing!)")
        if rem<=0: hide_overlay()
    root.after(200, ticker)
root.after(200, ticker)

def process_queue():
    while not event_queue.empty():
        e,v = event_queue.get()
        if e=="blackout": show_overlay(int(v))
        elif e=="endBlackout": hide_overlay()
    root.after(50, process_queue)
root.after(50, process_queue)

# -------- Socket.IO --------
@sio.event
def connect():
    sio.emit("register_client", {"hostname": platform.node()})
@sio.on("your_id")
def on_id(pid): print("My ID:", pid)
@sio.on("blackout")
def on_blackout(d): event_queue.put(("blackout", d))
@sio.on("endBlackout")
def on_end(): event_queue.put(("endBlackout", None))
def socket_thread():
    try:
        sio.connect("http://10.6.3.36:3000") # change server IP
        sio.wait()
    except Exception as e: print("Conn error:", e)
threading.Thread(target=socket_thread,daemon=True).start()

root.protocol("WM_DELETE_WINDOW", lambda: None)
root.mainloop()