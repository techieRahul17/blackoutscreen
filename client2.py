import socketio, platform, tkinter as tk, threading, time, random
from queue import Queue

sio = socketio.Client()
event_queue = Queue()

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"

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

username = input("Enter your name: ").strip() or "Anonymous"

root = tk.Tk()
root.withdraw()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 1.0)

canvas = tk.Canvas(root, highlightthickness=0, bg="black")
canvas.pack(fill="both", expand=True)

quote_var = tk.StringVar(value=random_quote())
comp_var  = tk.StringVar(value="Competition • 30m 0s")
black_var = tk.StringVar(value="Blackout • Not active")

quote_lbl = tk.Label(canvas, textvariable=quote_var,
                     font=("Segoe UI", 30, "bold"),
                     bg="black", fg="white", wraplength=1000, justify="center")
comp_lbl = tk.Label(canvas, textvariable=comp_var,
                    font=("Segoe UI", 18), bg="black", fg="#00ff99",
                    wraplength=1000, justify="center")
black_lbl = tk.Label(canvas, textvariable=black_var,
                     font=("Segoe UI", 18), bg="black", fg="#ff4444",
                     wraplength=1000, justify="center")

quote_lbl.place(relx=0.5, rely=0.35, anchor="center")
comp_lbl.place(relx=0.5, rely=0.55, anchor="center")
black_lbl.place(relx=0.5, rely=0.65, anchor="center")

overlay_visible = False
competition_total = 30 * 60 * 1000  # 30 min
competition_start = int(time.time() * 1000)

blackout_duration = 0
blackout_until = 0
recurring_blackout_timer = None  # for 1-min restore

# pause/resume state
paused = False
paused_comp_remaining = None
paused_black_remaining = None
auto_end = False

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
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        user32.SetWindowPos(hwnd, HWND_TOPMOST,0,0,0,0,
            SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW)

def set_fullscreen():
    w,h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")

def show_overlay(duration):
    global overlay_visible, blackout_until, blackout_duration, paused, paused_black_remaining, paused_comp_remaining

    if paused:  # resume from paused values
        blackout_duration = paused_black_remaining
        blackout_until = int(time.time() * 1000) + paused_black_remaining
        competition_resume_at = int(time.time() * 1000)
        globals()["competition_start"] = competition_resume_at - (competition_total - paused_comp_remaining)
        paused = False
    else:       # fresh blackout
        blackout_duration = duration
        blackout_until = int(time.time() * 1000) + duration

    quote_var.set(random_quote())
    set_fullscreen()
    if IS_WINDOWS:
        hwnd = root.winfo_id()
        root.deiconify()
        win_apply_clickthrough(hwnd)
    elif IS_LINUX:
        try: root.wm_attributes("-type", "dock")
        except: pass
        root.deiconify()
        root.lift()
    overlay_visible = True

def hide_overlay(auto=False):
    global overlay_visible, blackout_duration, blackout_until, auto_end, recurring_blackout_timer
    overlay_visible = False
    blackout_duration = 0
    blackout_until = 0
    root.withdraw()
    auto_end = auto
    if recurring_blackout_timer:
        root.after_cancel(recurring_blackout_timer)
        recurring_blackout_timer = None

def end_blackout_pause():
    global paused, paused_comp_remaining, paused_black_remaining, blackout_until, recurring_blackout_timer
    now = int(time.time() * 1000)
    paused = True
    paused_comp_remaining = max(0, (competition_start + competition_total - now))
    paused_black_remaining = max(0, blackout_until - now)
    hide_overlay(auto=False)

def start_recurring_blackout(duration):
    global recurring_blackout_timer

    def cycle():
        now = int(time.time() * 1000)
        if paused or now >= competition_start + competition_total:
            return  # stop recurring if paused or competition ended
        show_overlay(duration)
        # schedule hide after duration, then 1 min later restore
        def lift_then_restore():
            hide_overlay(auto=True)
            global recurring_blackout_timer
            recurring_blackout_timer = root.after(60000, cycle)  # 1 min lift
        recurring_blackout_timer = root.after(duration, lift_then_restore)
    cycle()

def ticker():
    now = int(time.time() * 1000)

    if paused:
        comp_var.set(f"Competition • Paused at {paused_comp_remaining//1000//60}m {paused_comp_remaining//1000%60}s")
        if paused_black_remaining > 0:
            black_var.set(f"Blackout • Paused at {paused_black_remaining//1000//60}m {paused_black_remaining//1000%60}s")
        else:
            black_var.set("Blackout • Not active")
    else:
        comp_rem = max(0, (competition_start + competition_total - now) // 1000)
        comp_var.set(f"Competition • Ends in {comp_rem//60}m {comp_rem%60}s")

        if overlay_visible:
            rem = max(0, blackout_until - now)
            black_var.set(f"Blackout • Ends in {rem//1000//60}m {rem//1000%60}s")
            if rem <= 0:
                black_var.set("Blackout • Finished")
                hide_overlay(auto=True)
        else:
            if auto_end:
                black_var.set("Blackout • Lifted (auto)")
            else:
                black_var.set("Blackout • Not active")

        if comp_rem <= 0:
            hide_overlay(auto=True)
            comp_var.set("Competition • Finished")
            black_var.set("Blackout • Lifted (competition ended)")

    root.after(200, ticker)
root.after(200, ticker)

def process_queue():
    while not event_queue.empty():
        e,v = event_queue.get()
        if e == "blackout":
            start_recurring_blackout(int(v))
        elif e == "endBlackout":
            end_blackout_pause()
    root.after(50, process_queue)
root.after(50, process_queue)

@sio.event
def connect():
    sio.emit("register_client", {"username": username, "hostname": platform.node()})

@sio.on("your_id")
def on_id(pid):
    print("My ID:", pid)

@sio.on("blackout")
def on_blackout(d):
    event_queue.put(("blackout", d))

@sio.on("endBlackout")
def on_end(data=None):
    event_queue.put(("endBlackout", data))

def socket_thread():
    try:
        sio.connect("http://10.6.3.36:3000")
        sio.wait()
    except Exception as e:
        print("Conn error:", e)
threading.Thread(target=socket_thread,daemon=True).start()

root.protocol("WM_DELETE_WINDOW", lambda: None)
root.mainloop()

