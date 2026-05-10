"""
══════════════════════════════════════════════════════════════════════════
CityMind — Advanced Holographic Command Center v4.0
══════════════════════════════════════════════════════════════════════════
"""
import sys, os, random, time, math
from collections import deque

# pyrefly: ignore [missing-import]
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
                             QVBoxLayout, QWidget, QPushButton, QLabel, 
                             QDockWidget, QListWidget, QListWidgetItem, QSpinBox, 
                             QGroupBox, QFormLayout, QCheckBox)
# pyrefly: ignore [missing-import]
from PyQt5.QtGui import QColor, QPen, QBrush, QPolygonF, QFont, QPainter, QLinearGradient
# pyrefly: ignore [missing-import]
from PyQt5.QtCore import Qt, QPointF, QTimer, pyqtSignal, QObject

sys.setrecursionlimit(10000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from CityGraph import CityGraph
from PathCalculationEngine import AstarEngine

# ══════════════════════════════════════════════════════════════════════════
#  COLOR & AESTHETIC CONSTANTS
# ══════════════════════════════════════════════════════════════════════════

BG_COLOR = QColor(6, 9, 20)
GRID_COLOR = QColor(30, 41, 59, 100)
ROAD_COLOR = QColor(71, 85, 105, 150)
PATH_COLOR = QColor(16, 185, 129)  # Emerald
FLOOD_COLOR = QColor(239, 68, 68)  # Red
# Two edge-disjoint backup routes (primary hospital → reference depot)
REDUNDANT_PATH_A = QColor(6, 182, 212)
REDUNDANT_PATH_B = QColor(249, 115, 22)

def path_to_undirected_edges(path):
    edges = set()
    if not path or len(path) < 2:
        return edges
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        edges.add((min(a, b), max(a, b)))
    return edges

def get_node_style(node_type, risk_index="Low", is_primary_hospital=False):
    """Returns (CoreColor, EdgeColor, HeightMultiplier)"""
    if node_type == "Hospital":
        if is_primary_hospital:
            return QColor(255, 215, 0), QColor(185, 28, 28), 2.8
        return QColor(255, 255, 255), QColor(220, 38, 38), 2.5 
    elif node_type == "Ambulance Depot":
        return QColor(255, 255, 255), QColor(148, 163, 184), 1.0
    elif node_type == "Residential":
        if risk_index == "High":
            return QColor(239, 68, 68), QColor(153, 27, 27), 1.6   
        elif risk_index == "Medium":
            return QColor(234, 179, 8), QColor(161, 98, 7), 1.3    
        else:
            return QColor(59, 130, 246), QColor(30, 64, 175), 1.1  
    elif node_type == "School":
        return QColor(245, 158, 11), QColor(180, 83, 9), 1.8       
    elif node_type == "Industrial":
        return QColor(139, 92, 246), QColor(91, 33, 182), 2.0      
    elif node_type == "Power Plant":
        return QColor(249, 115, 22), QColor(154, 52, 18), 2.8      
    else:
        return QColor(30, 41, 59), QColor(15, 23, 42), 0.1        

class InteractiveMap(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(BG_COLOR))
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.zoom_factor = 1.15

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

class CityMindWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CityMind Holographic Command Center")
        self.setGeometry(100, 100, 1600, 900)
        
        self.graph = None
        self.sim_step = 0
        self.civilians = []
        self.rescue_path = []
        self.amb_positions = []
        self.flood_edges = []
        self.view_mode = "3D"  
        self.cell_size = 65

        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #030712; }
            QDockWidget { color: #f8fafc; font-weight: bold; }
            QDockWidget::title { background: #0f172a; padding: 10px; }
            QPushButton { background-color: #1e293b; color: #38bdf8; border: 1px solid #334155; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #0f172a; border-color: #38bdf8; }
            QLabel { color: #cbd5e1; font-family: Consolas; }
            QListWidget { background-color: #0b1120; color: #f8fafc; border: none; font-family: Consolas; font-size: 13px; }
            QSpinBox { background-color: #1e293b; color: white; border: 1px solid #334155; padding: 4px; }
            QGroupBox { color: #60a5fa; font-weight: bold; border: 1px solid #1e293b; margin-top: 15px; padding-top: 15px;}
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QCheckBox { color: #94a3b8; font-family: Consolas; }
            QCheckBox::indicator { width: 14px; height: 14px; background-color: #1e293b; border: 1px solid #334155; }
            QCheckBox::indicator:checked { background-color: #38bdf8; }
        """)

        self.scene = QGraphicsScene()
        self.view = InteractiveMap(self.scene)
        self.setCentralWidget(self.view)

        control_dock = QDockWidget("COMMAND PROTOCOLS", self)
        control_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        control_widget = QWidget()
        control_layout = QVBoxLayout()

        dim_group = QGroupBox("MATRIX DIMENSIONS")
        dim_layout = QFormLayout()
        self.row_spin = QSpinBox(); self.row_spin.setRange(4, 50); self.row_spin.setValue(10)
        self.col_spin = QSpinBox(); self.col_spin.setRange(4, 50); self.col_spin.setValue(10)
        dim_layout.addRow(QLabel("Rows:"), self.row_spin)
        dim_layout.addRow(QLabel("Cols:"), self.col_spin)
        dim_group.setLayout(dim_layout)
        control_layout.addWidget(dim_group)

        layer_group = QGroupBox("TACTICAL OVERLAYS")
        layer_layout = QVBoxLayout()
        self.chk_roads = QCheckBox("Road Network Matrix")
        self.chk_roads.setChecked(True)
        self.chk_roads.stateChanged.connect(self.render_scene)
        
        self.chk_amb = QCheckBox("Ambulance Cov. Radius")
        self.chk_amb.setChecked(True)
        self.chk_amb.stateChanged.connect(self.render_scene)
        
        self.chk_risk = QCheckBox("Crime Risk Thermal")
        self.chk_risk.setChecked(False)
        self.chk_risk.stateChanged.connect(self.render_scene)

        self.chk_redundant = QCheckBox("Backup routes (Hosp→Depot ×2)")
        self.chk_redundant.setChecked(True)
        self.chk_redundant.stateChanged.connect(self.render_scene)

        layer_layout.addWidget(self.chk_roads)
        layer_layout.addWidget(self.chk_amb)
        layer_layout.addWidget(self.chk_risk)
        layer_layout.addWidget(self.chk_redundant)
        layer_group.setLayout(layer_layout)
        control_layout.addWidget(layer_group)

        btn_init = QPushButton("1. INITIALIZE MATRIX")
        btn_init.clicked.connect(self.init_simulation)
        btn_run = QPushButton("2. EXECUTE SIMULATION")
        btn_run.clicked.connect(self.run_simulation)
        btn_step = QPushButton("3. STEP FORWARD")
        btn_step.clicked.connect(self._do_step)
        btn_toggle = QPushButton("TOGGLE 2D / 3D VIEW")
        btn_toggle.clicked.connect(self.toggle_view)

        control_layout.addSpacing(10)
        control_layout.addWidget(btn_init)
        control_layout.addWidget(btn_run)
        control_layout.addWidget(btn_step)
        control_layout.addSpacing(10)
        control_layout.addWidget(btn_toggle)

        self.lbl_step = QLabel("TIMELINE STEP: 0 / 20")
        self.lbl_step.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8; margin-top: 15px;")
        control_layout.addWidget(self.lbl_step)
        
        control_layout.addStretch()
        control_widget.setLayout(control_layout)
        control_dock.setWidget(control_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, control_dock)

        log_dock = QDockWidget("LIVE TELEMETRY LOG", self)
        self.log_list = QListWidget()
        log_dock.setWidget(self.log_list)
        self.addDockWidget(Qt.RightDockWidgetArea, log_dock)

        self.log("SYSTEM BOOT SEQUENCE COMPLETED.", "info")

    def log(self, message, level="info"):
        item = QListWidgetItem(f"[{self.sim_step:02d}] {message}")
        if level == "danger": item.setForeground(QColor("#ef4444"))
        elif level == "success": item.setForeground(QColor("#10b981"))
        elif level == "warn": item.setForeground(QColor("#eab308"))
        else: item.setForeground(QColor("#94a3b8"))
        self.log_list.addItem(item)
        self.log_list.scrollToBottom()

    def toggle_view(self):
        self.view_mode = "2D" if self.view_mode == "3D" else "3D"
        self.render_scene()

    def init_simulation(self):
        rows, cols = self.row_spin.value(), self.col_spin.value()
        self.sim_step = 0
        self.flood_edges = []
        self.civilians = []
        self.rescue_path = []
        self.lbl_step.setText(f"TIMELINE STEP: 0 / 20")
        self.log_list.clear()

        self.log(f"Rebuilding Matrix ({rows}x{cols})...", "info")
        
        self.graph = CityGraph(rows, cols)
        self.graph.applyCSP()
        if self.graph.csp_all_rules_ok:
            self.log("Constraints applied — all planning rules satisfied.", "success")
        else:
            self.log(
                f"Constraints applied — {self.graph.csp_violation_count} rule(s) still violated (see terminal).",
                "warn",
            )
        
        self.graph.assignCosts()
        self.graph.applyRiskAnalysis()
        self.log("ML Demographics mapped to grid.", "warn")
        
        self.graph.ReallocateAmbulance()

        self.amb_positions = [p for p, n in self.graph.nodes.items() if n.NodeType == "Ambulance Depot"]
        res = [p for p, n in self.graph.nodes.items() if n.NodeType == "Residential"]
        self.civilians = random.sample(res, min(4, len(res))) if len(res) >= 4 else res[:]

        self.render_scene()
        self.view.resetTransform()
        self.view.centerOn(0, 0)
        self.view.scale(0.8, 0.8) 

    def run_simulation(self):
        if not self.graph or self.sim_step >= 20: return
        self.log("Automated run initiated.", "info")
        self.timer = QTimer()
        self.timer.timeout.connect(self._timer_step)
        self.timer.start(800)

    def _timer_step(self):
        if self.sim_step < 20:
            self._do_step()
        else:
            self.timer.stop()
            self.log("Simulation concluded.", "success")

    def _do_step(self):
        if not self.graph or self.sim_step >= 20: return
        self.sim_step += 1
        self.lbl_step.setText(f"TIMELINE STEP: {self.sim_step} / 20")

        if random.random() < 0.25:
            blocked = self.graph.trigger_random_flood()
            for a, b in blocked:
                self.flood_edges.append((a, b))
                self.log(f"CRITICAL: Road {a}<->{b} collapsed!", "danger")

        if self.civilians and self.amb_positions:
            engine = AstarEngine()
            start = self.graph.nodes[self.amb_positions[0]]
            tgts = [self.graph.nodes[c] for c in self.civilians if c in self.graph.nodes]
            if tgts:
                path, cost, _ = engine.FindSequentialPath(start, tgts, self.graph)
                if path:
                    self.rescue_path = [(n.Coordinates_X, n.Coordinates_Y) for n in path]
                    self.log(f"Route secured. Cost: {cost:.1f}", "success")
                else:
                    self.rescue_path = []
                    self.log("Routing failure. Paths blocked.", "danger")

        if self.sim_step % 5 == 0:
            self.graph.ReallocateAmbulance()
            self.amb_positions = [p for p, n in self.graph.nodes.items() if n.NodeType == "Ambulance Depot"]
            self.log("GA: Ambulances reallocated.", "info")

        self.render_scene()

    def iso_project(self, r, c, z):
        c_offset = c - (self.graph.cols / 2)
        r_offset = r - (self.graph.rows / 2)
        x = (c_offset - r_offset) * self.cell_size * 0.866
        y = (c_offset + r_offset) * self.cell_size * 0.5
        return QPointF(x, y - z)

    def get_centered_2d(self, r, c):
        x = (c - self.graph.cols / 2) * self.cell_size
        y = (r - self.graph.rows / 2) * self.cell_size
        return x, y

    def render_scene(self):
        if not self.graph: return
        self.scene.clear()

        path_set = set((min(a,b), max(a,b)) for a, b in zip(self.rescue_path[:-1], self.rescue_path[1:])) if self.rescue_path else set()
        flood_set = set((min(a,b), max(a,b)) for a, b in self.flood_edges)
        nodes_data = [(pos[0], pos[1], nd) for pos, nd in self.graph.nodes.items()]

        show_roads = self.chk_roads.isChecked()
        show_amb = self.chk_amb.isChecked()
        show_risk = self.chk_risk.isChecked()
        show_redundant = self.chk_redundant.isChecked()
        red_edges_a = path_to_undirected_edges(getattr(self.graph, "redundancy_path_a", []) or [])
        red_edges_b = path_to_undirected_edges(getattr(self.graph, "redundancy_path_b", []) or [])
        
        if self.view_mode == "3D":
            nodes_data.sort(key=lambda item: item[0] + item[1])
            
            # Draw Holographic Base Grid
            for r in range(self.graph.rows + 1):
                p1 = self.iso_project(r, 0, 0)
                p2 = self.iso_project(r, self.graph.cols, 0)
                self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(GRID_COLOR, 1))
            for c in range(self.graph.cols + 1):
                p1 = self.iso_project(0, c, 0)
                p2 = self.iso_project(self.graph.rows, c, 0)
                self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(GRID_COLOR, 1))
            
            if show_risk:
                for r, c, nd in nodes_data:
                    top_col, _, _ = get_node_style(
                        nd.NodeType, getattr(nd, 'RiskIndex', 'Low'), getattr(nd, 'is_primary_hospital', False)
                    )
                    b1 = self.iso_project(r, c, 0)
                    b2 = self.iso_project(r, c+1, 0)
                    b3 = self.iso_project(r+1, c+1, 0)
                    b4 = self.iso_project(r+1, c, 0)
                    heatmap_brush = QBrush(QColor(top_col.red(), top_col.green(), top_col.blue(), 50))
                    self.scene.addPolygon(QPolygonF([b1, b2, b3, b4]), QPen(Qt.NoPen), heatmap_brush)

            if show_roads:
                for (u, v), cost in self.graph.EdgesCost.items():
                    if u > v: continue
                    p1 = self.iso_project(u[0]+0.5, u[1]+0.5, 0)
                    p2 = self.iso_project(v[0]+0.5, v[1]+0.5, 0)
                    
                    key = (min(u,v), max(u,v))
                    if key in flood_set:
                        self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(FLOOD_COLOR, 3, Qt.DashLine))
                    elif key in path_set:
                        # Glow effect for active paths
                        self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(QColor(16, 185, 129, 100), 8))
                        self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(PATH_COLOR, 3))
                    else:
                        self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(ROAD_COLOR, 2))

            if show_roads and show_redundant and getattr(self.graph, "redundancy_ok", False):
                for key, col, w in ((red_edges_a, REDUNDANT_PATH_A, 5), (red_edges_b, REDUNDANT_PATH_B, 5)):
                    for u, v in key:
                        p1 = self.iso_project(u[0] + 0.5, u[1] + 0.5, 0)
                        p2 = self.iso_project(v[0] + 0.5, v[1] + 0.5, 0)
                        self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(col, w))

            # Render 3D Prisms with Gradients
            for r, c, nd in nodes_data:
                top_col, side_col, h_mult = get_node_style(
                    nd.NodeType, getattr(nd, 'RiskIndex', 'Low'), getattr(nd, 'is_primary_hospital', False)
                )
                h = h_mult * self.cell_size * 0.45
                pad = 0.20  # Smaller footprint for sleeker look
                
                # Base Pad (Glowing anchor)
                b1 = self.iso_project(r+pad, c+pad, 0)
                b2 = self.iso_project(r+pad, c+1-pad, 0)
                b3 = self.iso_project(r+1-pad, c+1-pad, 0)
                b4 = self.iso_project(r+1-pad, c+pad, 0)
                base_brush = QBrush(QColor(top_col.red(), top_col.green(), top_col.blue(), 80))
                self.scene.addPolygon(QPolygonF([b1, b2, b3, b4]), QPen(Qt.NoPen), base_brush)
                
                if h > 0:
                    t1 = self.iso_project(r+pad, c+pad, h)
                    t2 = self.iso_project(r+pad, c+1-pad, h)
                    t3 = self.iso_project(r+1-pad, c+1-pad, h)
                    t4 = self.iso_project(r+1-pad, c+pad, h)

                    # Dynamic Gradients for "Glass" Effect
                    grad_left = QLinearGradient(b4, t4)
                    grad_left.setColorAt(0, QColor(6, 9, 20, 200)) # Dark at bottom
                    grad_left.setColorAt(1, QColor(side_col.red(), side_col.green(), side_col.blue(), 180))
                    
                    grad_right = QLinearGradient(b3, t3)
                    grad_right.setColorAt(0, QColor(6, 9, 20, 220))
                    grad_right.setColorAt(1, QColor(side_col.red(), side_col.green(), side_col.blue(), 140))

                    outline_pen = QPen(top_col, 1)

                    self.scene.addPolygon(QPolygonF([b4, b3, t3, t4]), outline_pen, grad_left)
                    self.scene.addPolygon(QPolygonF([b3, b2, t2, t3]), outline_pen, grad_right)
                    
                    # Top face semi-transparent
                    top_brush = QBrush(QColor(top_col.red(), top_col.green(), top_col.blue(), 220))
                    self.scene.addPolygon(QPolygonF([t1, t2, t3, t4]), outline_pen, top_brush)

                    # Floating HUD Label
                    if nd.NodeType:
                        hud_y = t3.y() - 35
                        
                        # Leader line
                        self.scene.addLine(t3.x(), t3.y(), t3.x(), hud_y + 10, QPen(top_col, 1, Qt.DotLine))
                        
                        text_item = self.scene.addText(nd.NodeType.upper())
                        text_item.setDefaultTextColor(QColor(255, 255, 255))
                        text_item.setFont(QFont("Segoe UI", 7, QFont.Bold))
                        
                        tw = text_item.boundingRect().width()
                        th = text_item.boundingRect().height()
                        tx = t3.x() - tw / 2
                        
                        # HUD Background Badge
                        badge_rect = text_item.boundingRect().translated(tx, hud_y)
                        self.scene.addRect(badge_rect, QPen(top_col, 1), QBrush(QColor(15, 23, 42, 200)))
                        text_item.setPos(tx, hud_y)

            if show_amb and self.amb_positions:
                grid_area = self.graph.rows * self.graph.cols
                area_per_amb = grid_area / len(self.amb_positions)
                cell_radius = math.sqrt(area_per_amb / math.pi) * 1.5
                cov_radius = self.cell_size * cell_radius
                
                for r, c in self.amb_positions:
                    center = self.iso_project(r+0.5, c+0.5, 0)
                    cov_pen = QPen(QColor(16, 185, 129, 255), 2, Qt.DashLine)
                    cov_brush = QBrush(QColor(16, 185, 129, 20))
                    self.scene.addEllipse(center.x() - cov_radius, center.y() - (cov_radius/2), 
                                          cov_radius*2, cov_radius, cov_pen, cov_brush)

        else:
            # --- 2D TACTICAL VIEW ---
            if show_risk:
                for r, c, nd in nodes_data:
                    top_col, _, _ = get_node_style(
                        nd.NodeType, getattr(nd, 'RiskIndex', 'Low'), getattr(nd, 'is_primary_hospital', False)
                    )
                    x, y = self.get_centered_2d(r, c)
                    self.scene.addRect(x, y, self.cell_size, self.cell_size, QPen(Qt.NoPen), QBrush(QColor(top_col.red(), top_col.green(), top_col.blue(), 30)))

            if show_roads:
                for (u, v), cost in self.graph.EdgesCost.items():
                    if u > v: continue
                    x1, y1 = self.get_centered_2d(u[0], u[1])
                    x2, y2 = self.get_centered_2d(v[0], v[1])
                    x1 += self.cell_size/2; y1 += self.cell_size/2
                    x2 += self.cell_size/2; y2 += self.cell_size/2
                    
                    key = (min(u,v), max(u,v))
                    if key in flood_set:
                        self.scene.addLine(x1, y1, x2, y2, QPen(FLOOD_COLOR, 4, Qt.DashLine))
                    elif key in path_set:
                        self.scene.addLine(x1, y1, x2, y2, QPen(QColor(16, 185, 129, 100), 8))
                        self.scene.addLine(x1, y1, x2, y2, QPen(PATH_COLOR, 3))
                    else:
                        self.scene.addLine(x1, y1, x2, y2, QPen(ROAD_COLOR, 2))

            if show_roads and show_redundant and getattr(self.graph, "redundancy_ok", False):
                for key, col, w in ((red_edges_a, REDUNDANT_PATH_A, 6), (red_edges_b, REDUNDANT_PATH_B, 6)):
                    for u, v in key:
                        x1, y1 = self.get_centered_2d(u[0], u[1])
                        x2, y2 = self.get_centered_2d(v[0], v[1])
                        x1 += self.cell_size / 2
                        y1 += self.cell_size / 2
                        x2 += self.cell_size / 2
                        y2 += self.cell_size / 2
                        self.scene.addLine(x1, y1, x2, y2, QPen(col, w))

            if show_amb and self.amb_positions:
                grid_area = self.graph.rows * self.graph.cols
                area_per_amb = grid_area / len(self.amb_positions)
                cell_radius = math.sqrt(area_per_amb / math.pi) * 1.5
                cov_radius = self.cell_size * cell_radius
                
                for r, c in self.amb_positions:
                    x, y = self.get_centered_2d(r, c)
                    cx, cy = x + self.cell_size/2, y + self.cell_size/2
                    self.scene.addEllipse(cx - cov_radius, cy - cov_radius, cov_radius*2, cov_radius*2, 
                                          QPen(QColor(16, 185, 129, 200), 2, Qt.DashLine), QBrush(QColor(16, 185, 129, 20)))

            for r, c, nd in nodes_data:
                top_col, side_col, _ = get_node_style(
                    nd.NodeType, getattr(nd, 'RiskIndex', 'Low'), getattr(nd, 'is_primary_hospital', False)
                )
                x, y = self.get_centered_2d(r, c)
                rad = self.cell_size * 0.5
                cx = x + (self.cell_size - rad)/2
                cy = y + (self.cell_size - rad)/2

                # Glow behind node
                self.scene.addEllipse(cx-4, cy-4, rad+8, rad+8, QPen(Qt.NoPen), QBrush(QColor(top_col.red(), top_col.green(), top_col.blue(), 40)))
                self.scene.addEllipse(cx, cy, rad, rad, QPen(top_col, 2), QBrush(QColor(15, 23, 42)))

                if nd.NodeType:
                    text_item = self.scene.addText(nd.NodeType[:3].upper())
                    text_item.setDefaultTextColor(top_col)
                    text_item.setFont(QFont("Consolas", 8, QFont.Bold))
                    text_item.setPos(cx + rad/2 - text_item.boundingRect().width()/2, cy + rad/2 - 10)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CityMindWindow()
    window.show()
    sys.exit(app.exec_())