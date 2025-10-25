import sys, threading
class Game:
    def __init__(self, width=30, height=10):
        # ----------------- Grille -----------------
        self.width = width
        self.height = height
        self.empty = " "
        self.game_list = [[self.empty for _ in range(self.width)] for _ in range(self.height)]

        self.skins = ["▇", "█"]
        self.caracters = "█"
        self.coordonnates = (5, 15)

        self.wall_vertical_coordonnates = []
        self.wall_horizontal_coordonnates = []

        self.textlist = ["", ""]

        # ----------------- Menu -----------------
        self.menu_items = [""]
        self.menu_index = 0
        self.running_menu = False
        self.running_game = False
        self.stop_threads = False
        self.menu_actions = {}

        self.overlay_texts = []  # chaque élément = (x, y, texte)


    # ---------------- Menu ----------------
    def info():
        print
        ('''
        ---------------- How to use ----------------
                    
        Salut voici mon projet de RPG dans une console 
        (si l'on peut l'appeler comme ca).

        ----------------- Function -----------------

        Game() : Nom de la classe a définir ex :
            import module_name
            game = module_name.Game()
        
        set_menu_action(name_of_item, function) :
        ''')


    def start(self):
        self.running_menu = True
        self.running_game = False
        self.show_menu_loop()

    def show_menu_loop(self):
        import keyboard, time
        print("\033[?25l", end="")  # cache curseur
        self.show_menu()
        while self.running_menu:
            try :
                if keyboard.is_pressed("down"):
                    self.menu_index = (self.menu_index + 1) % len(self.menu_items)
                    self.show_menu()
                    while keyboard.is_pressed("down"): time.sleep(0.05)
                elif keyboard.is_pressed("up"):
                    self.menu_index = (self.menu_index - 1) % len(self.menu_items)
                    self.show_menu()
                    while keyboard.is_pressed("up"): time.sleep(0.05)
                elif keyboard.is_pressed("enter"):
                    item = self.menu_items[self.menu_index]
                    if item in self.menu_actions and callable(self.menu_actions[item]):
                        self.menu_actions[item]()  # exécute la fonction associée
                    while keyboard.is_pressed("enter"): time.sleep(0.05)
                
            except IndexError :
                print('choose option')
                time.sleep(0.05)

    def show_menu(self):
        print("\033[H\033[J", end="")
        print(" ")  # Ligne au-dessus
        for i, item in enumerate(self.menu_items):
            arrow = ">" if i == self.menu_index else ""
            print(f"{arrow} {item}")

    def set_menu_action(self, item_name, func):
        self.menu_actions[item_name] = func

    # ----------------- Jeu ----------------
    def start_game(self):
        import threading, time
        self.running_menu = False
        self.running_game = True
        self.game_list = [[self.empty for _ in range(self.width)] for _ in range(self.height)]
        self.create_wall()
        x, y = self.coordonnates
        self.game_list[x][y] = self.caracters

        threading.Thread(target=self.skin, daemon=True).start()
        threading.Thread(target=self.detect_flèches, daemon=True).start()
        self.show()

        while self.running_game:
            time.sleep(0.1)

    def skin(self):
        import time
        while not self.stop_threads and self.running_game:
            self.caracters = self.skins[0] if self.caracters == self.skins[1] else self.skins[1]
            x, y = self.coordonnates
            self.game_list[x][y] = self.caracters
            self.show()
            time.sleep(0.8)

    def create_wall(self):
        for coord in self.wall_vertical_coordonnates:
            x, y = coord
            if 0 <= x < self.height and 0 <= y < self.width:
                self.game_list[x][y] = "|"
        for coord in self.wall_horizontal_coordonnates:
            x, y = coord
            if 0 <= x < self.height and 0 <= y < self.width:
                self.game_list[x][y] = "-"

    def add_vertical_wall(self, x, y):
        if [x,y] not in self.wall_vertical_coordonnates:
            self.wall_vertical_coordonnates.append([x,y])
            self.create_wall()

    def add_horizontal_wall(self, x, y):
        if [x,y] not in self.wall_horizontal_coordonnates:
            self.wall_horizontal_coordonnates.append([x,y])
            self.create_wall()

    def remove_vertical_wall(self, x, y):
        if [x,y] in self.wall_vertical_coordonnates:
            self.wall_vertical_coordonnates.remove([x,y])
            self.create_wall()

    def remove_horizontal_wall(self, x, y):
        if [x,y] in self.wall_horizontal_coordonnates:
            self.wall_horizontal_coordonnates.remove([x,y])
            self.create_wall()

    def resize_map(self, new_width, new_height):
        self.width = new_width
        self.height = new_height
        self.game_list = [[self.empty for _ in range(self.width)] for _ in range(self.height)]
        self.create_wall()
        x, y = self.coordonnates
        if x >= self.height: self.coordonnates = (self.height-1, y)
        if y >= self.width: self.coordonnates = (x, self.width-1)
        self.show()

    def wall(self, x, y):
        for coord in self.wall_vertical_coordonnates + self.wall_horizontal_coordonnates:
            if coord[0]==x and coord[1]==y: return False
        return True

    def show(self):
        if not self.running_menu:
            print("\033[H\033[J", end="")  # efface écran
            # copie de la grille
            display_grid = [row.copy() for row in self.game_list]

            # affiche
            print(self.textlist[0])
            for row in display_grid:
                print("".join(row))
            print(self.textlist[1])

    def set_text(self, position, text):
        if position == "top" :
            self.textlist[0] = text
        elif position == "bottom" :
            self.textlist[1] = text

    def move(self, direction):
        x, y = self.coordonnates
        new_x, new_y = x, y
        if direction == "up" and x>0: new_x -=1
        elif direction=="down" and x<self.height-1: new_x +=1
        elif direction=="left" and y>0: new_y -=1
        elif direction=="right" and y<self.width-1: new_y +=1
        if self.wall(new_x,new_y):
            self.game_list[x][y] = self.empty
            self.coordonnates = (new_x,new_y)
            self.game_list[new_x][new_y] = self.caracters
            self.show()

    def detect_flèches(self):
        import time, keyboard
        while not self.stop_threads and self.running_game:
            if keyboard.is_pressed("up"): self.move("up")
            elif keyboard.is_pressed("down"): self.move("down")
            elif keyboard.is_pressed("left"): self.move("left")
            elif keyboard.is_pressed("right"): self.move("right")
            elif keyboard.is_pressed("esc"):
                self.running_game = False
                self.running_menu = True
                self.show_menu()
                return  # On sort du thread proprement

            time.sleep(0.1)

    def quit_game(self):
        self.stop_threads = True
        print("\033[?25h", end="")
        print("\nAu revoir ! 👋")
        sys.exit(0)
