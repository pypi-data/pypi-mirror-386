"""
Module cmatrix - Effet Matrix authentique avec noms CDA
Usage: from cmatrix import cmatrix
       cmatrix()
"""

import tkinter as tk
import random


class MatrixRain:
    def __init__(self, width=None, height=None, speed=50, fullscreen=True):
        """Initialise l'effet Matrix authentique

        Args:
            width: Largeur de la fenêtre en pixels (None = auto-detect)
            height: Hauteur de la fenêtre en pixels (None = auto-detect)
            speed: Vitesse en ms entre chaque frame
            fullscreen: True pour plein écran
        """

        # Création de la fenêtre principale
        self.root = tk.Tk()
        self.root.title("Matrix Rain")
        self.speed = speed

        # Configuration plein écran ou dimensions auto
        if fullscreen:
            self.root.attributes('-fullscreen', True)
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
        else:
            if width is None:
                width = 1200
            if height is None:
                height = 800

        # Canvas pour dessiner
        self.canvas = tk.Canvas(self.root, width=width, height=height,
                                bg='#000000', highlightthickness=0)
        self.canvas.pack()

        # Caractères Matrix authentiques (katakana japonais + quelques chiffres)
        self.chars = "ｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ012345789Z:・."

        # Noms CDA 2025-2026 - concaténés avec espaces
        cda_list = [
            "CDA 2025-2026",
            "PIERRE-YVES",
            "MELANIE",
            "SEVERINE",
            "LUDO",
            "HUGH",
            "VINCENT",
            "HEDWIGE",
            "WILEM",
            "KEWIN",
            "ALEKSANDER",
            "IMANE"
        ]
        # Crée une seule chaîne avec tous les noms séparés par des espaces
        self.cda_string = "  ".join(cda_list) + "  "  # Double espace entre chaque nom

        # Paramètres des colonnes - beaucoup plus serrées
        self.font_size = 14
        self.col_width = 12
        self.row_height = 16
        self.num_cols = width // self.col_width
        self.num_rows = height // self.row_height

        # Grille pour stocker les caractères et leur âge
        self.grid = {}  # {(x, y): {'char': char, 'age': age}}

        # Initialise les gouttes - beaucoup plus nombreuses
        self.drops = []
        for x in range(self.num_cols):
            # 60% de chance d'avoir une goutte active
            if random.random() < 0.6:
                # 15% de chance que cette goutte affiche des noms CDA
                is_cda_drop = random.random() < 0.15

                self.drops.append({
                    'x': x,
                    'y': random.randint(-20, 0),
                    'speed': random.uniform(0.5, 1.5),
                    'length': random.randint(15, 35),
                    'active': True,
                    'is_cda': is_cda_drop,
                    'cda_char_index': random.randint(0, len(self.cda_string) - 1) if is_cda_drop else 0
                })
            else:
                self.drops.append({
                    'x': x,
                    'y': -50,
                    'speed': 1.0,
                    'length': 20,
                    'active': False,
                    'is_cda': False,
                    'cda_char_index': 0
                })

        # Bind pour fermer
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('q', lambda e: self.root.destroy())

        # Lance l'animation
        self.animate()

    def get_color(self, age):
        """Retourne la couleur selon l'âge du caractère"""
        if age == 0:
            return '#FFFFFF'  # Blanc brillant pour la tête
        elif age == 1:
            return '#E0FFE0'
        elif age == 2:
            return '#C0FFC0'
        elif age == 3:
            return '#A0FFA0'
        elif age == 4:
            return '#80FF80'
        elif age < 8:
            return '#60FF60'
        elif age < 12:
            return '#40DD40'
        elif age < 16:
            return '#30BB30'
        elif age < 20:
            return '#209920'
        elif age < 25:
            return '#107710'
        else:
            return '#005500'  # Très sombre avant de disparaître

    def get_next_char(self, drop):
        """Retourne le prochain caractère pour une goutte"""
        if drop['is_cda']:
            # Retourne le caractère actuel de la chaîne CDA
            char = self.cda_string[drop['cda_char_index']]

            # Avance dans la chaîne (boucle à la fin)
            drop['cda_char_index'] = (drop['cda_char_index'] + 1) % len(self.cda_string)

            return char
        else:
            # Sinon, caractère Matrix normal
            return random.choice(self.chars)

    def animate(self):
        """Anime une frame"""
        # Vieillit tous les caractères existants
        to_remove = []
        for pos, data in self.grid.items():
            data['age'] += 1
            if data['age'] > 30:  # Disparaît après 30 frames
                to_remove.append(pos)

        for pos in to_remove:
            del self.grid[pos]

        # Efface le canvas
        self.canvas.delete("all")

        # Met à jour et dessine chaque goutte
        for drop in self.drops:
            if drop['active']:
                # Avance la goutte
                drop['y'] += drop['speed']

                # Ajoute un nouveau caractère à la tête
                head_row = int(drop['y'])
                if 0 <= head_row < self.num_rows:
                    pos = (drop['x'], head_row)
                    self.grid[pos] = {
                        'char': self.get_next_char(drop),
                        'age': 0
                    }

                # Change aléatoirement des caractères dans la traînée (seulement pour les gouttes normales)
                if not drop['is_cda'] and random.random() < 0.1:
                    trail_row = head_row - random.randint(1, 10)
                    if 0 <= trail_row < self.num_rows:
                        pos = (drop['x'], trail_row)
                        if pos in self.grid:
                            self.grid[pos]['char'] = random.choice(self.chars)

                # Réinitialise si sortie d'écran
                if drop['y'] > self.num_rows + 10:
                    drop['y'] = random.randint(-30, -5)
                    drop['speed'] = random.uniform(0.5, 1.5)
                    drop['length'] = random.randint(15, 35)
                    # Rechoisit si c'est une goutte CDA ou non
                    drop['is_cda'] = random.random() < 0.15
                    if drop['is_cda']:
                        drop['cda_char_index'] = random.randint(0, len(self.cda_string) - 1)
            else:
                # Réactive aléatoirement les gouttes inactives
                if random.random() < 0.002:
                    drop['active'] = True
                    drop['y'] = random.randint(-30, -5)
                    drop['speed'] = random.uniform(0.5, 1.5)
                    drop['is_cda'] = random.random() < 0.15
                    if drop['is_cda']:
                        drop['cda_char_index'] = random.randint(0, len(self.cda_string) - 1)

        # Dessine tous les caractères de la grille
        for (col, row), data in self.grid.items():
            x = col * self.col_width + 5
            y = row * self.row_height + 12

            color = self.get_color(data['age'])

            self.canvas.create_text(
                x, y,
                text=data['char'],
                fill=color,
                font=('Courier', self.font_size, 'bold'),
                anchor='nw'
            )

        # Planifie la prochaine frame
        self.root.after(self.speed, self.animate)

    def run(self):
        """Lance la fenêtre"""
        self.root.mainloop()


def cmatrix(width=None, height=None, speed=50, fullscreen=True):
    """
    Lance l'effet Matrix authentique avec noms CDA

    Args:
        width: Largeur de la fenêtre (None = taille écran)
        height: Hauteur de la fenêtre (None = taille écran)
        speed: Vitesse en ms entre chaque frame (30 = fluide)
        fullscreen: True pour plein écran

    Utilisation:
        from cmatrix import cmatrix
        cmatrix()  # Plein écran par défaut
        cmatrix(fullscreen=False)  # Fenêtre normale
        cmatrix(width=1200, height=800)  # Taille personnalisée
        cmatrix(speed=40)  # Plus lent

    Appuyez sur Echap ou Q pour fermer
    """
    matrix = MatrixRain(width, height, speed, fullscreen)
    matrix.run()


if __name__ == "__main__":
    cmatrix()