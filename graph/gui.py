"""
CityMind – Premium Visual Interface
====================================
Run:  python gui.py
"""
import sys, os, random, threading, time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

sys.setrecursionlimit(10000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from CityGraph import CityGraph
from PathCalculationEngine import AstarEngine

# ── Palette ────────────────────────────────────────────────────────
BG         = "#080810"
PANEL      = "#101020"
CARD       = "#181830"
ACCENT     = "#7c6aff"
MINT       = "#00e8a2"
TEXT       = "#eeeef4"
DIM        = "#6c6c8a"
BORDER     = "#28284a"
RED        = "#ff4466"
ORANGE     = "#ff9933"
GRID_BG    = "#0c0c1a"
ROAD_CLR   = "#5566aa"
PATH_CLR   = "#00ff99"
FLOOD_CLR  = "#ff2244"

NODE_CLR = {
    "Residential":     "#3b8beb",
    "Hospital":        "#ef4466",
    "School":          "#f5a623",
    "Industrial":      "#9b6dff",
    "Power Plant":     "#ff6e2e",
    "Ambulance Depot": "#00e8a2",
    "":                "#1e1e36",
}
RISK_CLR = {"High": "#552233", "Medium": "#553322", "Low": "#113322"}
ABBR = {"Residential":"R","Hospital":"H","School":"S",
        "Industrial":"I","Power Plant":"P","Ambulance Depot":"A"}


class CityMindGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CityMind — Urban Intelligence System")
        self.root.configure(bg=BG)
        self.root.state("zoomed")

        self.graph = None
        self.road_net = None
        self.sim_step = 0
        self.sim_running = False
        self.sim_speed = 1.0
        self.civilians = []
        self.rescue_path = []
        self.amb_positions = []
        self.flood_edges = []

        self.show_roads  = tk.BooleanVar(value=True)
        self.show_amb    = tk.BooleanVar(value=True)
        self.show_risk   = tk.BooleanVar(value=False)
        self.show_floods = tk.BooleanVar(value=True)
        self.show_path   = tk.BooleanVar(value=True)

        self._build()

    # ── UI ─────────────────────────────────────────────────────────
    def _build(self):
        # top bar
        top = tk.Frame(self.root, bg="#12122a", height=52)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Label(top, text="⚡ CityMind", font=("Segoe UI",20,"bold"),
                 bg="#12122a", fg=ACCENT).pack(side="left", padx=16)
        tk.Label(top, text="Urban Intelligence System",
                 font=("Segoe UI",11), bg="#12122a", fg=DIM).pack(side="left")
        self.step_lbl = tk.Label(top, text="Step: — / 20",
                                 font=("Consolas",13,"bold"),
                                 bg="#12122a", fg=MINT)
        self.step_lbl.pack(side="right", padx=20)
        self.status_lbl = tk.Label(top, text="● IDLE",
                                    font=("Segoe UI",10,"bold"),
                                    bg="#12122a", fg=DIM)
        self.status_lbl.pack(side="right", padx=10)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=6, pady=6)

        # canvas
        cf = tk.Frame(body, bg=PANEL, highlightthickness=2,
                      highlightbackground=BORDER)
        cf.pack(side="left", fill="both", expand=True, padx=(0,4))
        self.canvas = tk.Canvas(cf, bg=GRID_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=3, pady=3)

        # right panel
        rp = tk.Frame(body, bg=PANEL, width=310,
                      highlightthickness=2, highlightbackground=BORDER)
        rp.pack(side="right", fill="y"); rp.pack_propagate(False)

        self._controls(rp)
        self._overlays(rp)
        self._legend(rp)
        self._logpanel(rp)

    def _sec(self, p, title):
        f = tk.Frame(p, bg=CARD); f.pack(fill="x", padx=6, pady=(6,0))
        tk.Label(f, text=title, font=("Segoe UI",10,"bold"),
                 bg=CARD, fg=ACCENT).pack(anchor="w", padx=8, pady=(5,1))
        inner = tk.Frame(f, bg=CARD); inner.pack(fill="x", padx=8, pady=(0,6))
        return inner

    def _mbtn(self, p, txt, cmd, bg_=ACCENT):
        return tk.Button(p, text=txt, command=cmd, font=("Segoe UI",10,"bold"),
                         fg="white", bg=bg_, activebackground=bg_, bd=0,
                         padx=10, pady=5, cursor="hand2")

    def _controls(self, p):
        s = self._sec(p, "⚙  Controls")
        r = tk.Frame(s, bg=CARD); r.pack(fill="x", pady=2)
        tk.Label(r, text="Grid:", bg=CARD, fg=DIM,
                 font=("Segoe UI",10)).pack(side="left")
        self.gv1 = tk.StringVar(value="8")
        self.gv2 = tk.StringVar(value="8")
        for v in [self.gv1, self.gv2]:
            tk.Entry(r, textvariable=v, width=3, bg=BG, fg=TEXT,
                     insertbackground=TEXT, font=("Segoe UI",10),
                     bd=0, justify="center").pack(side="left", padx=2)
            if v is self.gv1:
                tk.Label(r, text="×", bg=CARD, fg=DIM).pack(side="left")

        bf = tk.Frame(s, bg=CARD); bf.pack(fill="x", pady=3)
        self._mbtn(bf,"▶  Initialise City", self._init).pack(fill="x",pady=1)
        self._mbtn(bf,"🔄  Run 20-Step Sim", self._run, MINT).pack(fill="x",pady=1)
        self._mbtn(bf,"⏭  Single Step", self._step1,"#9b6dff").pack(fill="x",pady=1)
        self._mbtn(bf,"⏹  Stop", self._stop, RED).pack(fill="x",pady=1)

        sf = tk.Frame(s, bg=CARD); sf.pack(fill="x", pady=2)
        tk.Label(sf, text="Speed:", bg=CARD, fg=DIM,
                 font=("Segoe UI",9)).pack(side="left")
        self.spd = tk.Scale(sf, from_=0.2, to=3.0, resolution=0.2,
                            orient="horizontal", bg=CARD, fg=TEXT,
                            highlightthickness=0, troughcolor=BG,
                            font=("Segoe UI",8))
        self.spd.set(1.0); self.spd.pack(side="left", fill="x", expand=True)

    def _overlays(self, p):
        s = self._sec(p, "🗺  Overlays")
        for txt, var in [("Roads (thick)", self.show_roads),
                         ("Ambulance Coverage", self.show_amb),
                         ("Crime Risk Heatmap", self.show_risk),
                         ("Flood Markers 🌊", self.show_floods),
                         ("Rescue Path 🚑", self.show_path)]:
            tk.Checkbutton(s, text=txt, variable=var, bg=CARD, fg=TEXT,
                           selectcolor=BG, activebackground=CARD,
                           activeforeground=TEXT, font=("Segoe UI",10),
                           command=self._draw).pack(anchor="w")

    def _legend(self, p):
        s = self._sec(p, "🏷  Legend")
        for nm, cl in NODE_CLR.items():
            if not nm: continue
            r = tk.Frame(s, bg=CARD); r.pack(anchor="w", pady=1)
            cv = tk.Canvas(r, width=16, height=16, bg=CARD, highlightthickness=0)
            cv.pack(side="left", padx=(0,5))
            cv.create_rectangle(1,1,15,15, fill=cl, outline="")
            tk.Label(r, text=nm, bg=CARD, fg=TEXT,
                     font=("Segoe UI",9)).pack(side="left")
        # extra legend items
        for sym, desc in [("━━ thick","Road"), ("╳ red","Flood Block"),
                          ("── green","Rescue Path"),("◯ dashed","Amb. Range")]:
            r = tk.Frame(s, bg=CARD); r.pack(anchor="w", pady=0)
            tk.Label(r, text=f"  {sym} = {desc}", bg=CARD, fg=DIM,
                     font=("Consolas",8)).pack(anchor="w")

    def _logpanel(self, p):
        s = self._sec(p, "📋  Live Event Log")
        self.log = scrolledtext.ScrolledText(
            s, height=10, bg=BG, fg=TEXT, font=("Consolas",9),
            bd=0, wrap="word", insertbackground=TEXT)
        self.log.pack(fill="both", expand=True)
        self.log.tag_configure("flood", foreground=RED)
        self.log.tag_configure("ok", foreground=MINT)
        self.log.tag_configure("warn", foreground=ORANGE)

    def _lmsg(self, msg, tag=None):
        self.log.insert("end", msg+"\n", tag)
        self.log.see("end")

    # ── init city ──────────────────────────────────────────────────
    def _init(self):
        try:
            rows, cols = int(self.gv1.get()), int(self.gv2.get())
        except ValueError:
            messagebox.showerror("Error","Grid must be integers"); return
        if rows < 4 or cols < 4:
            messagebox.showerror("Error","Min 4×4"); return

        self.sim_step = 0; self.flood_edges = []
        self.civilians = []; self.rescue_path = []
        self.step_lbl.config(text="Step: 0 / 20")
        self.status_lbl.config(text="● BUILDING…", fg=ORANGE)
        self.log.delete("1.0","end")
        self._lmsg(f"══ Initialising {rows}×{cols} city ══", "ok")

        def work():
            self.graph = CityGraph(rows, cols)
            self._lmsg("[Ch1] CSP layout…")
            self.graph.applyCSP()
            self._lmsg("[Ch1] ✓ Layout assigned", "ok")
            self.root.after(0, self._draw)

            self._lmsg("[Ch2] Road network GA…")
            self.road_net = self.graph.assignCosts()
            self._lmsg(f"[Ch2] ✓ {len(self.road_net.built_roads)} roads, "
                       f"cost {self.road_net.total_cost:.1f}", "ok")
            self.root.after(0, self._draw)

            self._lmsg("[Ch5] Risk analysis (K-Means + KNN)…")
            self.graph.applyRiskAnalysis()
            self._lmsg("[Ch5] ✓ Risk applied", "ok")

            self._lmsg("[Ch3] Ambulance placement GA…")
            self.graph.ReallocateAmbulance()
            self._lmsg("[Ch3] ✓ Ambulances placed", "ok")

            self._cache_amb()
            self._make_civilians()
            self.root.after(0, self._draw)
            self.root.after(0, lambda: self.status_lbl.config(
                text="● READY", fg=MINT))
            self._lmsg("══ City ready — run simulation ══", "ok")

        threading.Thread(target=work, daemon=True).start()

    def _cache_amb(self):
        self.amb_positions = [p for p,n in self.graph.nodes.items()
                              if n.NodeType == "Ambulance Depot"]

    def _make_civilians(self):
        res = [p for p,n in self.graph.nodes.items()
               if n.NodeType == "Residential"]
        self.civilians = random.sample(res, min(4, len(res))) if len(res)>=4 else res[:]
        self._lmsg(f"[Ch4] {len(self.civilians)} trapped civilians placed", "warn")

    # ── simulation ─────────────────────────────────────────────────
    def _run(self):
        if not self.graph:
            messagebox.showinfo("Info","Initialise first"); return
        if self.sim_running: return
        self.sim_running = True
        self.status_lbl.config(text="● RUNNING", fg=MINT)
        def loop():
            while self.sim_running and self.sim_step < 20:
                self.root.after(0, self._do_step)
                time.sleep(max(0.4, 2.0 / float(self.spd.get())))
            self.sim_running = False
            self.root.after(0, lambda: self.status_lbl.config(
                text="● DONE" if self.sim_step>=20 else "● PAUSED", fg=DIM))
        threading.Thread(target=loop, daemon=True).start()

    def _step1(self):
        if not self.graph:
            messagebox.showinfo("Info","Initialise first"); return
        if self.sim_step >= 20:
            self._lmsg("[SIM] Already complete."); return
        self._do_step()

    def _stop(self):
        self.sim_running = False
        self.status_lbl.config(text="● PAUSED", fg=ORANGE)
        self._lmsg("[SIM] Paused.", "warn")

    def _do_step(self):
        self.sim_step += 1
        self.step_lbl.config(text=f"Step: {self.sim_step} / 20")
        self._lmsg(f"\n─── Step {self.sim_step}/20 ───")

        # --- FLOODS: random blocking ---
        blocked = self.graph.trigger_random_flood()
        for a, b in blocked:
            self.flood_edges.append((a, b))
            self._lmsg(f"  🌊 FLOOD  {a} ↔ {b}  BLOCKED", "flood")

        # --- CHALLENGE 4: emergency routing with reroute ---
        if self.civilians and self.amb_positions:
            engine = AstarEngine()
            sp = self.amb_positions[0]
            start = self.graph.nodes[sp]
            tgts = [self.graph.nodes[c] for c in self.civilians if c in self.graph.nodes]
            if tgts:
                self._lmsg(f"  🚑 Routing from {sp} → {len(tgts)} targets…")
                path, cost, segs = engine.FindSequentialPath(start, tgts, self.graph)
                self.rescue_path = [(n.Coordinates_X, n.Coordinates_Y)
                                    for n in path] if path else []
                ok = sum(1 for s in segs if s["status"]=="OK")
                self._lmsg(f"  🚑 Reached {ok}/{len(tgts)}  cost={cost:.1f}",
                           "ok" if ok==len(tgts) else "warn")
                self.graph.log_event(
                    f"[Step {self.sim_step}] Route: {ok}/{len(tgts)} reached, cost={cost:.1f}")

        # --- Re-evaluate ambulances every 5 steps ---
        if self.sim_step % 5 == 0:
            self._lmsg("  🔄 Re-evaluating ambulance positions…", "warn")
            self.graph.ReallocateAmbulance()
            self._cache_amb()
            self._lmsg("  ✓ Ambulances repositioned", "ok")

        self._draw()
        if self.sim_step >= 20:
            self.sim_running = False
            self._lmsg("\n══ SIMULATION COMPLETE ══", "ok")

    # ── drawing ────────────────────────────────────────────────────
    def _draw(self):
        if not self.graph: return
        c = self.canvas; c.delete("all")
        W = c.winfo_width() or 750
        H = c.winfo_height() or 700
        R, C = self.graph.rows, self.graph.cols
        pad = 48
        cell = min((W - 2*pad)/C, (H - 2*pad)/R)
        ox = (W - C*cell)/2
        oy = (H - R*cell)/2

        def cx(col): return ox + col*cell + cell/2
        def cy(row): return oy + row*cell + cell/2

        # background grid lines (subtle)
        for r in range(R+1):
            y = oy + r*cell
            c.create_line(ox, y, ox+C*cell, y, fill="#1a1a30", width=1)
        for col in range(C+1):
            x = ox + col*cell
            c.create_line(x, oy, x, oy+R*cell, fill="#1a1a30", width=1)

        # ── risk heatmap ──
        if self.show_risk.get():
            for pos, nd in self.graph.nodes.items():
                ri = nd.RiskIndex
                if ri and ri in RISK_CLR:
                    x1, y1 = ox+pos[1]*cell, oy+pos[0]*cell
                    c.create_rectangle(x1, y1, x1+cell, y1+cell,
                                       fill=RISK_CLR[ri], outline="",
                                       stipple="gray50")

        # ── ROADS — thick and visible ──
        if self.show_roads.get():
            drawn = set()
            for (u, v) in self.graph.EdgesCost:
                key = (min(u,v), max(u,v))
                if key in drawn: continue
                drawn.add(key)
                # glow layer
                c.create_line(cx(u[1]),cy(u[0]),cx(v[1]),cy(v[0]),
                              fill="#1a2a44", width=6)
                # main road
                c.create_line(cx(u[1]),cy(u[0]),cx(v[1]),cy(v[0]),
                              fill=ROAD_CLR, width=3, capstyle="round")

        # ── FLOOD markers — big red X ──
        if self.show_floods.get():
            for a, b in self.flood_edges:
                mx = (cx(a[1]) + cx(b[1]))/2
                my = (cy(a[0]) + cy(b[0]))/2
                # red dashed line
                c.create_line(cx(a[1]),cy(a[0]),cx(b[1]),cy(b[0]),
                              fill=FLOOD_CLR, width=4, dash=(8,4))
                # flood X marker
                sz = cell*0.22
                c.create_line(mx-sz,my-sz,mx+sz,my+sz, fill="white", width=3)
                c.create_line(mx+sz,my-sz,mx-sz,my+sz, fill="white", width=3)
                # water emoji
                c.create_text(mx, my-sz-6, text="🌊",
                              font=("Segoe UI", max(8, int(cell/5))))

        # ── RESCUE PATH — bright green animated ──
        if self.show_path.get() and len(self.rescue_path) > 1:
            for i in range(len(self.rescue_path)-1):
                a, b = self.rescue_path[i], self.rescue_path[i+1]
                # glow
                c.create_line(cx(a[1]),cy(a[0]),cx(b[1]),cy(b[0]),
                              fill="#114422", width=8)
                c.create_line(cx(a[1]),cy(a[0]),cx(b[1]),cy(b[0]),
                              fill=PATH_CLR, width=3, capstyle="round")
            # start & end markers
            st = self.rescue_path[0]
            en = self.rescue_path[-1]
            c.create_oval(cx(st[1])-6,cy(st[0])-6,cx(st[1])+6,cy(st[0])+6,
                          fill=MINT, outline="white", width=2)
            c.create_oval(cx(en[1])-6,cy(en[0])-6,cx(en[1])+6,cy(en[0])+6,
                          fill=RED, outline="#2a2a4a", width=2)

        # ── AMBULANCE COVERAGE ──
        if self.show_amb.get():
            for pos in self.amb_positions:
                rad = cell*3.5
                c.create_oval(cx(pos[1])-rad, cy(pos[0])-rad,
                              cx(pos[1])+rad, cy(pos[0])+rad,
                              outline=MINT, width=2, dash=(6,3))
                # inner zone
                rad2 = cell*2
                c.create_oval(cx(pos[1])-rad2, cy(pos[0])-rad2,
                              cx(pos[1])+rad2, cy(pos[0])+rad2,
                              outline=MINT, width=1, dash=(3,3))

        # ── NODE CELLS ──
        for pos, nd in self.graph.nodes.items():
            r, cc = pos
            x1, y1 = ox + cc*cell + 3, oy + r*cell + 3
            x2, y2 = ox + (cc+1)*cell - 3, oy + (r+1)*cell - 3
            clr = NODE_CLR.get(nd.NodeType, NODE_CLR[""])

            # shadow
            c.create_rectangle(x1+2,y1+2,x2+2,y2+2, fill="#050508", outline="")
            # cell
            c.create_rectangle(x1,y1,x2,y2, fill=clr, outline="#2a2a4a",
                               width=1)
            # highlight on top edge
            c.create_line(x1+1,y1,x2-1,y1, fill="#444466", width=1)

            # abbreviation
            ab = ABBR.get(nd.NodeType, "")
            if cell > 22 and ab:
                fs = max(8, int(cell/3.5))
                c.create_text((x1+x2)/2, (y1+y2)/2, text=ab,
                              fill="white", font=("Segoe UI", fs, "bold"))

        # ── CIVILIAN SOS markers ──
        for civ in self.civilians:
            if civ in self.graph.nodes:
                x, y = cx(civ[1]), cy(civ[0]) - cell*0.38
                c.create_text(x, y, text="🆘",
                              font=("Segoe UI", max(10, int(cell/2.8))))

        # ── coord labels ──
        if cell > 30:
            for col in range(C):
                c.create_text(cx(col), oy-14, text=str(col),
                              fill=DIM, font=("Consolas",8))
            for row in range(R):
                c.create_text(ox-14, cy(row), text=str(row),
                              fill=DIM, font=("Consolas",8))


if __name__ == "__main__":
    root = tk.Tk()
    root.minsize(1100, 650)
    app = CityMindGUI(root)
    root.mainloop()
