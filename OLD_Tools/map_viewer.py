import struct
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os

# === Config ===
MAP_PATH = "test.bmp"
NAV_VEC_PATH = "nav_vec.dat"
MATRIX_PATH = "matrix_int.dat"

# Coordinate originali e reali
OLD_WIDTH, OLD_HEIGHT = 640, 472
REAL_WIDTH, REAL_HEIGHT = 2272, 1672
VIEW_WIDTH, VIEW_HEIGHT = 1080, 720
BORDER_OFFSET = 64

# Fattori di scala per ridimensionamento e offset
SCALE_X = VIEW_WIDTH / (REAL_WIDTH + ( 2 * BORDER_OFFSET ) )
SCALE_Y = VIEW_HEIGHT / (REAL_HEIGHT + ( 2 * BORDER_OFFSET ) )

def scale_and_offset(x, y):
    """Scala da coordinate originali (640x472) a coordinate finali su canvas."""
    x_real = x * REAL_WIDTH / OLD_WIDTH + BORDER_OFFSET
    y_real = y * REAL_HEIGHT / OLD_HEIGHT + BORDER_OFFSET
    x_canvas = int(x_real * SCALE_X)
    y_canvas = int(y_real * SCALE_Y)
    print(f"Scaled ({x}, {y}) to canvas coordinates ({x_canvas}, {y_canvas})")
    return x_canvas, y_canvas

# === Load Points ===
def load_points(path):
    with open(path, 'rb') as f:
        num_points = struct.unpack('<I', f.read(4))[0]
        points = []
        for _ in range(num_points):
            x = struct.unpack('<H', f.read(2))[0]
            y = struct.unpack('<H', f.read(2))[0]
            scaled = scale_and_offset(x, y)
            points.append(scaled)
    return points

# === Load Matrix ===
def load_matrix(path, num_points):
    matrix = []
    with open(path, 'rb') as f:
        for i in range(num_points):
            row = []
            for j in range(num_points):
                dist = struct.unpack('<I', f.read(4))[0]
                next_node = struct.unpack('<H', f.read(2))[0]
                row.append((dist, next_node))
            matrix.append(row)
    return matrix


def trova_percorso(matrix, points, start, end, max_steps=1000):
    print(f"\n🔍 Inizio calcolo percorso da {start} a {end}")
    print(f"📍 Coordinate partenza: {start} = {points[start]}")
    print(f"📍 Coordinate destinazione: {end} = {points[end]}\n")

    a = start
    b = end
    path = [a]
    visited = set(path)
    
    for step in range(max_steps):
        try:
            dist, next_node = matrix[a][b]
        except IndexError:
            print(f"❌ Errore: indice fuori dai limiti matrix[{a}][{b}]")
            return path

        print(f"🔎 matrix[{a}][{b}] = (distanza: {dist}, next_node: {next_node})")

        # Evita loop su se stesso o assenza di connessione
        if dist == 0 and next_node == a:
            print(f"🚫 Nessun percorso valido: {a} → {b} ha distanza 0 e ritorna su se stesso.")
            break

        if next_node in visited:
            print(f"\n⚠️ Loop rilevato al passo {step + 1}")
            print(f"🔁 Nodo attuale: {a} -> Next node: {next_node} (già visitato)")
            print(f"🎯 Obiettivo: {b}")
            print(f"🧭 Distanza tra {a} e {b}: {dist}")
            print(f"📌 Percorso parziale: {path}")
            print(f"📍 Coordinate attuale: {points[a]}, next: {points[next_node]}, target: {points[b]}")
            return path

        print(f"✅ Step {step}: {a} → {next_node}, distanza = {dist}")
        path.append(next_node)
        visited.add(next_node)

        if next_node == b:
            print(f"\n🎉 Percorso completato! Totale passi: {len(path)-1}")
            return path

        a = next_node

    print(f"\n⚠️ Raggiunto numero massimo di passi ({max_steps}) senza trovare destinazione.")
    return path


# === Get path from A to B using next_node links ===
def get_path(matrix, a, b, points=None):
    path = [a]
    visited = set()
    attempt = 0

    print(f"\n🔍 Inizio calcolo percorso da {a} a {b}")
    print(f"📌 Contenuto matrix[{a}][{b}]")
    if points:
        ax, ay = points[a]
        bx, by = points[b]
        print(f"📍 Coordinate partenza: {a} = ({ax}, {ay})")
        print(f"📍 Coordinate destinazione: {b} = ({bx}, {by})")
    while a != b:
        if a < 0 or a >= len(matrix) or b < 0 or b >= len(matrix[a]):
            print(f"❌ Indici fuori limite: a={a}, b={b}")
            break

        dist, next_node = matrix[a][b]

        if dist == 0 and next_node == a:
            print(f"\n❌ Nessuna connessione da {a} a {b}")
            print(f"📌 Contenuto matrix[{a}][{b}] = (distanza: {dist}, next_node: {next_node})")
            break

        if next_node == a or next_node in visited:
            print(f"\n⚠️ Loop rilevato al passo {attempt}")
            print(f"🔁 Nodo attuale: {a} -> Next node: {next_node} (già visitato o è se stesso)")
            if points:
                cx, cy = points[a]
                nx, ny = points[next_node]
                print(f"📍 Coord attuale: {a} = ({cx}, {cy})")
                print(f"📍 Coord next_node: {next_node} = ({nx}, {ny})")
            print(f"🎯 Obiettivo: {b}")
            print(f"🧭 Distanza tra {a} e {b}: {dist}")
            print(f"📌 Percorso parziale: {path}")
            break

        visited.add(next_node)
        path.append(next_node)

        print(f"✅ Step {attempt}: {a} → {next_node}, distanza = {dist}")
        if points:
            cx, cy = points[a]
            nx, ny = points[next_node]
            print(f"   Coord {a}: ({cx}, {cy}) → {next_node}: ({nx}, {ny})")

        a = next_node
        attempt += 1

    return path




# === GUI ===
class MapApp:
    def __init__(self, root, map_path, points, matrix):
        self.root = root
        self.points = points
        self.matrix = matrix
        self.selected = []

        self.canvas = tk.Canvas(root, width=VIEW_WIDTH, height=VIEW_HEIGHT)
        self.canvas.pack()

        # Carica e ridimensiona l'immagine
        img = Image.open(map_path)
        img = img.resize((VIEW_WIDTH, VIEW_HEIGHT))
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.tk_img)

        # Disegna tutti i punti
        for i, (x, y) in enumerate(points):
            self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill='red', tags=("point", str(i)))

        # Gestione eventi
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.clear_paths)
        self.root.bind("<s>", self.save_image_with_points)
        self.root.bind("<S>", self.save_image_with_points)

        self.label = tk.Label(root, text="Click due punti per mostrare il percorso", font=("Arial", 14))
        self.label.pack()



    def on_click(self, event):
        x, y = event.x, event.y
        clicked = self.find_nearest_point(x, y)
        if clicked is not None:
            self.selected.append(clicked)
            px, py = self.points[clicked]
            self.canvas.create_oval(px - 4, py - 4, px + 4, py + 4, outline='blue', width=2, tags="path")
            if len(self.selected) == 2:
                self.show_path()
                self.selected.clear()

    def find_nearest_point(self, x, y):
        for i, (px, py) in enumerate(self.points):
            if abs(px - x) < 6 and abs(py - y) < 6:
                return i
        return None

    def show_path(self):
        a, b = self.selected
        path = get_path(self.matrix, a, b)
        total_dist = 0
        for i in range(len(path) - 1):
            x1, y1 = self.points[path[i]]
            x2, y2 = self.points[path[i + 1]]
            self.canvas.create_line(x1, y1, x2, y2, fill='lime', width=2, tags="path")
            total_dist += self.matrix[path[i]][path[i + 1]][0]
        self.label.config(text=f"Percorso: {' -> '.join(map(str, path))} | Distanza totale: {total_dist}")

    def clear_paths(self, event=None):
        self.canvas.delete("path")
        self.label.config(text="Percorso cancellato. Seleziona due punti.")
        self.selected.clear()

    def save_image_with_points(self, event=None):
        # Crea una nuova immagine RGB nera con le dimensioni reali + bordo
        final_width = REAL_WIDTH + 2 * BORDER_OFFSET
        final_height = REAL_HEIGHT + 2 * BORDER_OFFSET
        output_img = Image.new("RGB", (final_width, final_height), "black")

        # Carica l'immagine di sfondo e ridimensionala
        base_img = Image.open(MAP_PATH).resize((final_width, final_height))
        output_img.paste(base_img)

        draw = ImageDraw.Draw(output_img)

        # Ridisegna i punti sulla nuova immagine
        for x, y in self.points:
            x_img = int(x / SCALE_X)
            y_img = int(y / SCALE_Y)
            r = 4
            draw.ellipse((x_img - r, y_img - r, x_img + r, y_img + r), fill='red')

        # Salva come BMP
        output_path = r"C:\Users\marzi\OneDrive\Desktop\P3Modding\images\Vollansichtskarte.bmp"
        output_img.save(output_path, format="BMP")
        print(f"Immagine salvata come {output_path}")

# === Main ===
if __name__ == '__main__':
    points = load_points(NAV_VEC_PATH)
    matrix = load_matrix(MATRIX_PATH, len(points))

    root = tk.Tk()
    root.title("Percorso su mappa (1080x720)")
    app = MapApp(root, MAP_PATH, points, matrix)
    root.mainloop()