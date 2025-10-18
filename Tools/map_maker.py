import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import struct
import math
import heapq
import os

# Constants
POINT_RADIUS = 3
COLOR_CONNECTED = "red"
COLOR_NOT_CONNECTED = "black"
COLOR_NOT_CONNECTED2 = "darkorange"
NAV_MATRIX_FILE = "nav_matrix.dat"
VEC_FILE = "nav_vec.dat"
MATRIX_FILE = "matrix_int.dat"

REAL_WIDTH = 640
REAL_HEIGHT = 472

VIEW_WIDTH = 1280
VIEW_HEIGHT = 944

class NavPointEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Nav Point Editor")

        self.canvas = tk.Canvas(root, width=VIEW_WIDTH, height=VIEW_HEIGHT)
        self.canvas.pack()

        # Load navigation matrix
        if os.path.exists(NAV_MATRIX_FILE):
            with open(NAV_MATRIX_FILE, "rb") as f:
                # Leggi tutto il file e salta i primi 4 byte
                data = f.read()[4:]
                self.nav_matrix = list(data)
        else:
            self.nav_matrix = [0] * (REAL_WIDTH * REAL_HEIGHT)

        self.width = REAL_WIDTH
        self.height = REAL_HEIGHT

        # Create background image
        nav_img = Image.new("RGB", (self.width, self.height))
        pixels = nav_img.load()
        for y in range(self.height):
            for x in range(self.width):
                val = self.nav_matrix[y * self.width + x]
                pixels[x, y] = (0, 0, 255) if val == 0 else (0, 0, 0)

        nav_img_resized = nav_img.resize((VIEW_WIDTH, VIEW_HEIGHT), Image.Resampling.NEAREST)
        self.bg_image = ImageTk.PhotoImage(nav_img_resized)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        self.points = []  # List of points (x_real, y_real)
        self.dragging_point_index = None

        # Bind events
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<Button-3>", self.remove_point)
        self.root.bind("<KeyPress-s>", self.save_all)

        # Buttons frame
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=5)

        # Main buttons
        self.btn_save_points = tk.Button(self.btn_frame, text="Save Points", command=self.save_points)
        self.btn_save_points.pack(side=tk.LEFT, padx=5)

        self.btn_load_last = tk.Button(self.btn_frame, text="Load Last", command=self.load_last_save)
        self.btn_load_last.pack(side=tk.LEFT, padx=5)

        self.btn_generate_matrix = tk.Button(self.btn_frame, text="Generate Matrix", command=self.generate_matrix_file)
        self.btn_generate_matrix.pack(side=tk.LEFT, padx=5)

        # Verification buttons
        self.btn_verify_all = tk.Button(self.btn_frame, text="Verify All", command=self.verify_all_points)
        self.btn_verify_all.pack(side=tk.LEFT, padx=5)

        self.btn_validate_case = tk.Button(self.btn_frame, text="Validate Case", command=self.validate_specific_case)
        self.btn_validate_case.pack(side=tk.LEFT, padx=5)

    def is_walkable(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.nav_matrix[y * self.width + x] == 0

    def is_clear_path(self, x0, y0, x1, y1):
        """Bresenham's line algorithm with walkability check"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1

        if dx > dy:
            err = dx / 2.0
            while x != x1:
                if not self.is_walkable(x, y):
                    return False
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                if not self.is_walkable(x, y):
                    return False
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        
        return self.is_walkable(x1, y1)

    def on_left_click(self, event):
        x_real = int(event.x * REAL_WIDTH / VIEW_WIDTH)
        y_real = int(event.y * REAL_HEIGHT / VIEW_HEIGHT)
        for i, (px, py) in enumerate(self.points):
            if abs(px - x_real) <= POINT_RADIUS and abs(py - y_real) <= POINT_RADIUS:
                self.dragging_point_index = i
                return
        self.points.append((x_real, y_real))
        self.draw_points()

    def on_left_release(self, event):
        self.dragging_point_index = None

    def on_mouse_drag(self, event):
        if self.dragging_point_index is not None:
            x_real = int(event.x * REAL_WIDTH / VIEW_WIDTH)
            y_real = int(event.y * REAL_HEIGHT / VIEW_HEIGHT)
            x_real = max(0, min(self.width - 1, x_real))
            y_real = max(0, min(self.height - 1, y_real))
            self.points[self.dragging_point_index] = (x_real, y_real)
            self.draw_points()

    def remove_point(self, event):
        x_real = int(event.x * REAL_WIDTH / VIEW_WIDTH)
        y_real = int(event.y * REAL_HEIGHT / VIEW_HEIGHT)
        for i, (px, py) in enumerate(self.points):
            if abs(px - x_real) <= POINT_RADIUS and abs(py - y_real) <= POINT_RADIUS:
                del self.points[i]
                break
        self.draw_points()

    def draw_points(self):
        self.canvas.delete("point")
        for i, (x_real, y_real) in enumerate(self.points):
            x = x_real * VIEW_WIDTH / REAL_WIDTH
            y = y_real * VIEW_HEIGHT / REAL_HEIGHT
            color = COLOR_CONNECTED  # Default color
            
            # Check if current point is in walkable area
            current_walkable = self.is_walkable(x_real, y_real)
            
            # Check previous and next points if they exist
            prev_connected = True
            next_connected = True
            
            if i > 0:  # Has previous point
                px_prev, py_prev = self.points[i-1]
                # Check if previous point is walkable AND path is clear
                prev_walkable = self.is_walkable(px_prev, py_prev)
                prev_connected = prev_walkable and current_walkable and self.is_clear_path(px_prev, py_prev, x_real, y_real)
            
            if i < len(self.points) - 1:  # Has next point
                px_next, py_next = self.points[i+1]
                # Check if next point is walkable AND path is clear
                next_walkable = self.is_walkable(px_next, py_next)
                next_connected = current_walkable and next_walkable and self.is_clear_path(x_real, y_real, px_next, py_next)
            
            # Debug print
            #print(f"Point {i} at ({x_real},{y_real}) - walkable: {current_walkable}")
            #if i > 0:
            #    print(f"  Connection to {i-1}: {prev_connected}")
            #if i < len(self.points) - 1:
            #    print(f"  Connection to {i+1}: {next_connected}")
            
            # Change color based on connections
            if not current_walkable:
                color = "black"  # Completely unwalkable point
                self.canvas.create_text(x, y + 10, text='ERROR NON WALKABLE', fill="purple", tags="point")
            elif not prev_connected and not next_connected:
                color = COLOR_NOT_CONNECTED  # Isolated between neighbors
                self.canvas.create_text(x, y + 10, text='ERROR', fill="purple", tags="point")
            elif not prev_connected or not next_connected:
                color = "orange"  # Only one connection missing
            
            self.canvas.create_oval(
                x - POINT_RADIUS, y - POINT_RADIUS,
                x + POINT_RADIUS, y + POINT_RADIUS,
                fill=color, tags="point"
            )
            self.canvas.create_text(x, y - 10, text=str(i), fill="white", tags="point")
    def save_all(self, event=None):
        self.save_points()
        self.generate_matrix_file()
        self.save_image()  # Aggiungi questa linea

    def save_image(self, filename="navigation_map.png"):
        """Salva l'immagine corrente del canvas come file PNG"""
        try:
            # Crea un'immagine PIL dal canvas
            from PIL import ImageGrab
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            
            # Cattura l'area del canvas
            ImageGrab.grab().crop((x, y, x1, y1)).save(filename)
            print(f"Immagine salvata come {filename}")
        except Exception as e:
            print(f"Errore nel salvataggio dell'immagine: {str(e)}")


    def save_points(self):
        with open(VEC_FILE, "wb") as f:
            f.write(struct.pack("<H", len(self.points)))
            f.write(b"\x00\x00")  # Padding
            for x, y in self.points:
                f.write(struct.pack("<2H", x, y))
        print(f"Saved {len(self.points)} points to {VEC_FILE}")

    def load_last_save(self):
        """Load last saved points from file"""
        try:
            with open(VEC_FILE, "rb") as f:
                data = f.read()
                num_points = struct.unpack("<H", data[:2])[0]
                self.points.clear()
                
                for i in range(num_points):
                    offset = 4 + i * 4
                    x, y = struct.unpack("<2H", data[offset:offset+4])
                    self.points.append((x, y))
                
                self.draw_points()
                print(f"Loaded {num_points} points from last save")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load points: {str(e)}")

    def generate_matrix_file(self):
        num_points = len(self.points)
        matrix_data = bytearray()
        
        print(f"\nGenerating matrix for {num_points} points (using float distances)...")
        
        # Build adjacency list with floating-point distances
        adj = [[] for _ in range(num_points)]
        for i in range(num_points):
            for j in range(num_points):
                if i != j and self.is_clear_path(*self.points[i], *self.points[j]):
                    dx = self.points[i][0] - self.points[j][0]
                    dy = self.points[i][1] - self.points[j][1]
                    dist = math.sqrt(dx*dx + dy*dy)  # Now a float
                    adj[i].append((j, dist))
                    # Debug print for direct connections
                    if i == 0 and j == 9:
                        print(f"Direct connection 0→9: distance={dist:.7f}")
        
        # Generate routing matrix using Dijkstra's algorithm with float distances
        for i in range(num_points):
            # Debug print for source point
            if i == 0:
                print(f"\nCalculating paths from point 0 ({self.points[i]})")
            
            # Dijkstra's algorithm with float distances
            dist = [math.inf] * num_points
            prev = [-1] * num_points
            dist[i] = 0.0
            heap = [(0.0, i)]
            
            while heap:
                current_dist, u = heapq.heappop(heap)
                if current_dist > dist[u]:
                    continue
                for v, weight in adj[u]:
                    if dist[v] > dist[u] + weight:
                        dist[v] = dist[u] + weight
                        prev[v] = u
                        heapq.heappush(heap, (dist[v], v))
            
            # Generate matrix entries for current node
            for j in range(num_points):
                if i == 0 and j == 9:  # Debug for specific case
                    print(f"Path 0→9: total_dist={dist[j]:.7f}, path={self.get_path(prev, j)}")
                
                if i == j:
                    # Self-connection
                    matrix_data += struct.pack("<f", 0.0)  # 4-byte float
                    matrix_data += struct.pack("<H", i)     # 2-byte unsigned short
                elif dist[j] == math.inf:
                    # No path exists
                    matrix_data += struct.pack("<f", 0.0)
                    matrix_data += struct.pack("<H", 0)
                else:
                    # Find first hop
                    next_hop = j
                    while prev[next_hop] != i and prev[next_hop] != -1:
                        next_hop = prev[next_hop]
                    
                    if prev[next_hop] == -1:  # Shouldn't happen for reachable nodes
                        matrix_data += struct.pack("<f", 0.0)
                        matrix_data += struct.pack("<H", 0)
                    else:
                        # Debug for specific case
                        if i == 0 and j == 9:
                            print(f"Final entry: dist={dist[j]:.7f}, next_hop={next_hop}")
                        
                        # Ensure distance is reasonable
                        if dist[j] > 100000.0:  # Arbitrary large number
                            print(f"Warning: Large distance {dist[j]:.7f} from {i} to {j}")
                        
                        distance_fixed_point = int(round(dist[j] * 65536))
                        matrix_data += struct.pack("<I", distance_fixed_point)  # 4-byte float
                        matrix_data += struct.pack("<H", next_hop)  # 2-byte unsigned short

        with open(MATRIX_FILE, "wb") as f:
            f.write(matrix_data)
        
        # Verify the written data for the specific case
        offset = (0 * num_points + 9) * 6  # Still 6 bytes per entry (4 float + 2 short)
        if offset + 6 <= len(matrix_data):
            written_dist, written_next = struct.unpack_from("<fH", matrix_data, offset)
            print(f"\nWritten data for 0→9: dist={written_dist:.7f}, next={written_next}")
        
        print(f"Generated matrix with {len(matrix_data)} bytes ({num_points}x{num_points} nodes)")

    def get_path(self, prev, j):
        """Helper to reconstruct path for debugging"""
        path = []
        while j != -1:
            path.append(j)
            j = prev[j]
        return path[::-1]

    def verify_all_points(self):
        """Verify connectivity between all points"""
        print("\n=== Full Connectivity Verification ===")
        num_points = len(self.points)
        
        # Build connectivity matrix
        connectivity = [[False]*num_points for _ in range(num_points)]
        for i in range(num_points):
            for j in range(num_points):
                if i != j:
                    connectivity[i][j] = self.is_clear_path(*self.points[i], *self.points[j])
        
        # Find isolated points
        isolated_points = []
        for i in range(num_points):
            has_incoming = any(connectivity[j][i] for j in range(num_points) if j != i)
            has_outgoing = any(connectivity[i][j] for j in range(num_points) if j != i)
            if not has_incoming and not has_outgoing:
                isolated_points.append(i)
        
        # Find problematic pairs
        problematic_pairs = []
        for i in range(num_points):
            for j in range(i+1, num_points):
                if connectivity[i][j] or connectivity[j][i]:
                    i_has_others = any(connectivity[i][k] or connectivity[k][i] 
                                     for k in range(num_points) if k != i and k != j)
                    j_has_others = any(connectivity[j][k] or connectivity[k][j] 
                                     for k in range(num_points) if k != i and k != j)
                    
                    if not i_has_others or not j_has_others:
                        problematic_pairs.append((i, j, not i_has_others, not j_has_others))
        
        # Find unreachable points
        unreachable_points = []
        for i in range(num_points):
            if i not in isolated_points:
                has_incoming = any(connectivity[j][i] for j in range(num_points) if j != i)
                if not has_incoming:
                    unreachable_points.append(i)
        
        # Display results
        self.canvas.delete("verification")
        
        # Highlight isolated points (red)
        for i in isolated_points:
            x, y = self.points[i]
            x_view = x * VIEW_WIDTH / REAL_WIDTH
            y_view = y * VIEW_HEIGHT / REAL_HEIGHT
            self.canvas.create_oval(x_view-8, y_view-8, x_view+8, y_view+8,
                                  outline="red", width=3, tags="verification")
            self.canvas.create_text(x_view, y_view-15, text=f"ISOLATED {i}", 
                                  fill="red", font=('Helvetica', 10, 'bold'), tags="verification")
        
        # Highlight unreachable points (purple)
        for i in unreachable_points:
            x, y = self.points[i]
            x_view = x * VIEW_WIDTH / REAL_WIDTH
            y_view = y * VIEW_HEIGHT / REAL_HEIGHT
            self.canvas.create_oval(x_view-6, y_view-6, x_view+6, y_view+6,
                                  outline="purple", width=3, tags="verification")
            self.canvas.create_text(x_view, y_view-15, text=f"UNREACHABLE {i}", 
                                  fill="purple", font=('Helvetica', 10, 'bold'), tags="verification")
        
        # Highlight problematic connections (orange)
        for i, j, _, _ in problematic_pairs:
            x1, y1 = self.points[i]
            x2, y2 = self.points[j]
            x1_view = x1 * VIEW_WIDTH / REAL_WIDTH
            y1_view = y1 * VIEW_HEIGHT / REAL_HEIGHT
            x2_view = x2 * VIEW_WIDTH / REAL_WIDTH
            y2_view = y2 * VIEW_HEIGHT / REAL_HEIGHT
            self.canvas.create_line(x1_view, y1_view, x2_view, y2_view,
                                  fill="orange", width=2, tags="verification")
        
        # Print results
        if isolated_points:
            print("\n🔴 ISOLATED POINTS:")
            for i in isolated_points:
                print(f" - Point {i} {self.points[i]} (no connections)")
        
        if unreachable_points:
            print("\n🟣 UNREACHABLE POINTS:")
            for i in unreachable_points:
                print(f" - Point {i} {self.points[i]} (no incoming connections)")
        
        if problematic_pairs:
            print("\n🟠 PROBLEMATIC PAIRS:")
            for i, j, i_isolated, j_isolated in problematic_pairs:
                print(f" - Points {i} and {j}:")
                print(f"   - Connection {i}→{j}: {'✅' if connectivity[i][j] else '❌'}")
                print(f"   - Connection {j}→{i}: {'✅' if connectivity[j][i] else '❌'}")
                if i_isolated and j_isolated:
                    print("   - BOTH ISOLATED (only connected to each other)")
                elif i_isolated:
                    print(f"   - POINT {i} ISOLATED (only connected to {j})")
                else:
                    print(f"   - POINT {j} ISOLATED (only connected to {i})")
        
        if not isolated_points and not unreachable_points and not problematic_pairs:
            print("✅ No connectivity issues found")

    def validate_specific_case(self):
        """Validate connectivity between two specific points"""
        if len(self.points) < 2:
            messagebox.showwarning("Warning", "Need at least 2 points to validate")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Validate Specific Case")
        
        # Source point selection
        tk.Label(dialog, text="Source Point:").grid(row=0, column=0, padx=5, pady=5)
        self.source_var = tk.StringVar(dialog)
        self.source_var.set("0")
        source_menu = tk.OptionMenu(dialog, self.source_var, *[str(i) for i in range(len(self.points))])
        source_menu.grid(row=0, column=1, padx=5, pady=5)
        
        # Destination point selection
        tk.Label(dialog, text="Destination Point:").grid(row=1, column=0, padx=5, pady=5)
        self.dest_var = tk.StringVar(dialog)
        self.dest_var.set("1")
        dest_menu = tk.OptionMenu(dialog, self.dest_var, *[str(i) for i in range(len(self.points))])
        dest_menu.grid(row=1, column=1, padx=5, pady=5)
        
        # Validate button
        tk.Button(dialog, text="Validate", 
                 command=lambda: self.run_validation(dialog)).grid(row=2, columnspan=2, pady=10)

    def run_validation(self, dialog):
        """Execute the validation between selected points including matrix values"""
        try:
            source = int(self.source_var.get())
            dest = int(self.dest_var.get())
            
            if source == dest:
                messagebox.showwarning("Warning", "Source and destination must be different")
                return
            
            # Check connectivity
            forward = self.is_clear_path(*self.points[source], *self.points[dest])
            backward = self.is_clear_path(*self.points[dest], *self.points[source])
            
            # Load matrix data if exists
            matrix_values = {}
            if os.path.exists(MATRIX_FILE):
                with open(MATRIX_FILE, "rb") as f:
                    data = f.read()
                    num_points = int(math.sqrt(len(data)/6))  # Each entry is 6 bytes (4 distance + 2 nextnode)
                    
                    if source < num_points and dest < num_points:
                        # Calculate offsets
                        offset_source_dest = (source * num_points + dest) * 6
                        offset_dest_source = (dest * num_points + source) * 6
                        
                        # Read source->dest
                        if offset_source_dest + 6 <= len(data):
                            dist_source_dest, next_source_dest = struct.unpack_from("<IH", data, offset_source_dest)
                            matrix_values['source_dest'] = (dist_source_dest, next_source_dest)
                        
                        # Read dest->source
                        if offset_dest_source + 6 <= len(data):
                            dist_dest_source, next_dest_source = struct.unpack_from("<IH", data, offset_dest_source)
                            matrix_values['dest_source'] = (dist_dest_source, next_dest_source)
            
            # Show results
            result = tk.Toplevel(self.root)
            result.title(f"Validation Results: {source} ↔ {dest}")
            
            # Main title
            tk.Label(result, text=f"Validation Results: Point {source} ↔ Point {dest}", 
                font=('Helvetica', 12, 'bold')).pack(pady=10)
            
            # Path validation frame
            path_frame = tk.Frame(result)
            path_frame.pack(pady=5)
            
            # Forward direction
            tk.Label(path_frame, text=f"{source} → {dest}:", width=15).grid(row=0, column=0, sticky=tk.W)
            status = "✅ CONNECTED" if forward else "❌ BLOCKED"
            color = "green" if forward else "red"
            tk.Label(path_frame, text=status, fg=color).grid(row=0, column=1, sticky=tk.W)
            
            # Backward direction
            tk.Label(path_frame, text=f"{dest} → {source}:", width=15).grid(row=1, column=0, sticky=tk.W)
            status = "✅ CONNECTED" if backward else "❌ BLOCKED"
            color = "green" if backward else "red"
            tk.Label(path_frame, text=status, fg=color).grid(row=1, column=1, sticky=tk.W)
            
            # Matrix values frame (only if matrix exists)
            if matrix_values:
                matrix_frame = tk.Frame(result)
                matrix_frame.pack(pady=10)
                
                tk.Label(matrix_frame, text="Matrix Values:", font=('Helvetica', 10, 'bold')).grid(row=0, columnspan=3)
                
                # Header
                tk.Label(matrix_frame, text="Direction", relief=tk.RIDGE, width=15).grid(row=1, column=0)
                tk.Label(matrix_frame, text="Distance", relief=tk.RIDGE, width=10).grid(row=1, column=1)
                tk.Label(matrix_frame, text="Next Node", relief=tk.RIDGE, width=10).grid(row=1, column=2)
                
                # Source->Dest values
                tk.Label(matrix_frame, text=f"matrix[{source}][{dest}]").grid(row=2, column=0, sticky=tk.W)
                if 'source_dest' in matrix_values:
                    dist, next_node = matrix_values['source_dest']
                    tk.Label(matrix_frame, text=str(dist)).grid(row=2, column=1)
                    tk.Label(matrix_frame, text=str(next_node)).grid(row=2, column=2)
                else:
                    tk.Label(matrix_frame, text="N/A", fg="gray").grid(row=2, column=1, columnspan=2)
                
                # Dest->Source values
                tk.Label(matrix_frame, text=f"matrix[{dest}][{source}]").grid(row=3, column=0, sticky=tk.W)
                if 'dest_source' in matrix_values:
                    dist, next_node = matrix_values['dest_source']
                    tk.Label(matrix_frame, text=str(dist)).grid(row=3, column=1)
                    tk.Label(matrix_frame, text=str(next_node)).grid(row=3, column=2)
                else:
                    tk.Label(matrix_frame, text="N/A", fg="gray").grid(row=3, column=1, columnspan=2)
            else:
                tk.Label(result, text="No matrix data found", fg="gray").pack()
            
            # Visual highlight
            self.highlight_validation_case(source, dest, forward, backward)
            
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {str(e)}")

    def highlight_validation_case(self, source, dest, forward, backward):
        """Highlight the validation case on canvas"""
        self.canvas.delete("validation")
        
        # Get view coordinates
        x1, y1 = self.points[source]
        x2, y2 = self.points[dest]
        
        x1_view = x1 * VIEW_WIDTH / REAL_WIDTH
        y1_view = y1 * VIEW_HEIGHT / REAL_HEIGHT
        x2_view = x2 * VIEW_WIDTH / REAL_WIDTH
        y2_view = y2 * VIEW_HEIGHT / REAL_HEIGHT
        
        # Draw points
        self.canvas.create_oval(x1_view-8, y1_view-8, x1_view+8, y1_view+8,
                              outline="blue", width=3, fill="lightblue", tags="validation")
        self.canvas.create_text(x1_view, y1_view-15, text=f"SRC {source}", 
                              fill="blue", font=('Helvetica', 10, 'bold'), tags="validation")
        
        self.canvas.create_oval(x2_view-8, y2_view-8, x2_view+8, y2_view+8,
                              outline="green", width=3, fill="lightgreen", tags="validation")
        self.canvas.create_text(x2_view, y2_view-15, text=f"DST {dest}", 
                              fill="green", font=('Helvetica', 10, 'bold'), tags="validation")
        
        # Draw connections
        if forward:
            self.canvas.create_line(x1_view, y1_view, x2_view, y2_view,
                                  fill="blue", width=2, arrow=tk.LAST, tags="validation")
        else:
            self.canvas.create_line(x1_view, y1_view, x2_view, y2_view,
                                  fill="red", width=2, dash=(3,1), tags="validation")
        
        if backward:
            self.canvas.create_line(x2_view, y2_view, x1_view, y1_view,
                                  fill="green", width=2, arrow=tk.LAST, tags="validation")
        else:
            self.canvas.create_line(x2_view, y2_view, x1_view, y1_view,
                                  fill="red", width=2, dash=(3,1), tags="validation")
        
        # Add legend
        legend = tk.Toplevel(self.root)
        legend.title("Validation Legend")
        tk.Label(legend, text="Legend:", font=('Helvetica', 10, 'bold')).pack(pady=5)
        tk.Label(legend, text="Blue: Source Point", fg="blue").pack(anchor=tk.W)
        tk.Label(legend, text="Green: Destination Point", fg="green").pack(anchor=tk.W)
        tk.Label(legend, text="Blue Arrow: Valid SRC→DST path").pack(anchor=tk.W)
        tk.Label(legend, text="Green Arrow: Valid DST→SRC path").pack(anchor=tk.W)
        tk.Label(legend, text="Red Dashed: Blocked path").pack(anchor=tk.W)

if __name__ == "__main__":
    root = tk.Tk()
    app = NavPointEditor(root)
    root.mainloop()
