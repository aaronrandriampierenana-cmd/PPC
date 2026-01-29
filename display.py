import sys, os, threading, multiprocessing, tkinter as tk
from tkinter import ttk
import time, queue, socket
import configs, environment

def envoyer_message(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5); s.connect((configs.HOST, configs.PORT)); s.sendall(message)
            return True
    except: return False

class Display:
    def __init__(self):
        self.fenetre = tk.Tk()
        self.fenetre.title("Simulation PPC - Paramètres & Graphique")
        self.fenetre.geometry("1200x900")
        self.canvas_items = {}
        self.memoire = None
        self.lock = None
        self.dict_entites = None
        self.start_time = None
        self.env_process = None
        self.setup_ui()

    def setup_ui(self):
        # Stats et Graphique (Canvas optimisé)
        control_panel = tk.Frame(self.fenetre, width=300, bg="#ecf0f1")
        control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(control_panel, text="PARAMÈTRES", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Champs de saisie
        self.entries = {}
        params = [("Proies Init", "5"), ("Preds Init", "3"), ("Seuil Faim", "40"), ("Gain Repas", "25")]
        for label, default in params:
            tk.Label(control_panel, text=label).pack()
            e = tk.Entry(control_panel); e.insert(0, default); e.pack()
            self.entries[label] = e

        self.boutton_debut = tk.Button(control_panel, text="DÉMARRER", bg="green", fg="white", command=self.start_simulation)
        self.boutton_debut.pack(fill=tk.X, pady=10)

        tk.Label(control_panel, text="STATISTIQUES", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        self.nb_proies_label = tk.Label(control_panel, text="Proies: 0")
        self.nb_proies_label.pack(anchor="w")
        self.nb_pred_label = tk.Label(control_panel, text="Prédateurs: 0")
        self.nb_pred_label.pack(anchor="w")
        self.herbe_label = tk.Label(control_panel, text="Herbe: 0%")
        self.herbe_label.pack(anchor="w")
        self.temps_label = tk.Label(control_panel, text="Temps: 0s")
        self.temps_label.pack(anchor="w")

        self.canvas = tk.Canvas(self.fenetre, bg="#27ae60")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.btn_reset = tk.Button(control_panel, text="REINITIALISER", bg="red", fg="white", command=self.reset_simulation)
        self.btn_reset.pack(fill=tk.X, pady=10)

    def reset_simulation(self):
        # 1. Arrêter brutalement le processus d'environnement
        if self.env_process and self.env_process.is_alive():
            self.env_process.terminate()
            self.env_process.join()
            if self.env_process.is_alive():
                os.kill(self.env_process.pid, 9) # Kill forcé si nécessaire
            self.env_process = None
            
        # 2. Fermer le Manager (libère les ressources IPC)
        if self.manager:
            try:
                self.manager.shutdown()
            except: pass
            self.manager = None

        # 3. Réinitialiser les pointeurs
        self.dict_entites = None
        self.memoire = None
        self.lock = None

        # 3. Nettoyer le Canvas (Supprimer tous les ronds)
        self.canvas.delete("all")
        self.canvas_items.clear()

        # 4. Réinitialiser les labels de l'interface
        self.nb_proies_label.config(text="Proies: 0")
        self.nb_pred_label.config(text="Prédateurs: 0")
        self.temps_label.config(text="Temps: 0s")
        
        # 5. Réactiver le bouton de démarrage
        self.boutton_debut.config(state=tk.NORMAL)
    
    def start_simulation(self):
        # Appliquer les paramètres de l'UI vers configs.py
        configs.seuil_faim = int(self.entries["Seuil Faim"].get())
        configs.gain_repas = int(self.entries["Gain Repas"].get())
        
        self.manager = multiprocessing.Manager()
        self.memoire = self.manager.list([0, 0, 50.0])
        self.lock = self.manager.Lock()
        self.msg_queue = self.manager.Queue()
        self.dict_entites = self.manager.dict()
        self.start_time = time.time()

        self.env_process = multiprocessing.Process(target=environment.env_process, args=(self.memoire, self.lock, self.msg_queue, self.dict_entites))
        self.env_process.start()
        
        time.sleep(0.5)
        for _ in range(int(self.entries["Proies Init"].get())): envoyer_message(configs.nouvelle_proie)
        for _ in range(int(self.entries["Preds Init"].get())): envoyer_message(configs.nouveau_predateur)
        
        self.update_loop()

    def update_loop(self):
        self.update_stats()
        self.update_canvas()
        self.fenetre.after(100, self.update_loop)

    def update_stats(self):
        if self.memoire is None or self.lock is None:
            return

        with self.lock:
            nb_proies = int(self.memoire[configs.index_proie])
            nb_preds = int(self.memoire[configs.index_pred])
            herbe = float(self.memoire[configs.index_herbe])

        self.nb_proies_label.config(text=f"Proies: {nb_proies}")
        self.nb_pred_label.config(text=f"Prédateurs: {nb_preds}")
        self.herbe_label.config(text=f"Herbe: {herbe:.0f}%")

        if self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            self.temps_label.config(text=f"Temps: {elapsed}s")

    def update_canvas(self):
        if self.dict_entites is None: return

        with self.lock:
            # On prend une photo instantanée des IDs vivants
            ids_vivants_actuellement = list(self.dict_entites.keys())
            entites_data = dict(self.dict_entites)

        # --- ÉTAPE 1 : EFFACER LES MORTS ---
        # On regarde tous les ronds affichés sur le canvas
        for eid in list(self.canvas_items.keys()):
            if eid not in ids_vivants_actuellement:
                # Si l'ID n'est plus dans le dictionnaire, on efface le rond
                self.canvas.delete(self.canvas_items[eid])
                del self.canvas_items[eid]
                print(f"DEBUG: Suppression visuelle de {eid}")

        # --- ÉTAPE 2 : METTRE À JOUR LES VIVANTS ---
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        for eid, data in entites_data.items():
            # Attention : 'data' doit être un dict ou un tuple avec x, y
            # Si tu utilises des tuples : x, y = data[3], data[4]
            # Si tu utilises des dicts : x, y = data['x'], data['y']
            try:
                x_px = (data['x'] / configs.GRID_SIZE) * w
                y_px = (data['y'] / configs.GRID_SIZE) * h
                
                if eid not in self.canvas_items:
                    color = "white" if data['type'] == 'proie' else "red"
                    self.canvas_items[eid] = self.canvas.create_oval(x_px-5, y_px-5, x_px+5, y_px+5, fill=color)
                else:
                    self.canvas.coords(self.canvas_items[eid], x_px-5, y_px-5, x_px+5, y_px+5)
            except KeyError:
                continue # Évite les crashs si l'entité disparait pendant la boucle
                
if __name__ == "__main__":
    Display().fenetre.mainloop()
    try:
        Display().fenetre.mainloop()
    finally: #ca permet d'executer ce bout de code quoi qu'il se passe
        print("Nettoyage final des processus...")
        Display().reset_simulation()
