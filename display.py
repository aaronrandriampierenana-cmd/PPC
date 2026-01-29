import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/src")
import configs
import multiprocessing
import tkinter as tk
import time
from tkinter import ttk
import environment
import pred
import prey
import queue
import socket

def envoyer_message(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((configs.HOST, configs.PORT))
            s.sendall(message)
            print(f"Message envoyé : {message.decode()}")
            return True
    except ConnectionRefusedError:
        print("Serveur non disponible. Assurez-vous que environment.py est en cours d'exécution.")
        return False
    except Exception as e:
        print(f"Erreur : {e}")
        return False


class Display:
    def __init__(self):
        self.fenetre = tk.Tk()
        self.fenetre.title("Simulation Prédateurs-Proies")
        self.fenetre.geometry("1200x800")
        
        self.manager = None
        self.memoire = None
        self.lock = None
        self.msg_queue = None
        self.env_process = None
        self.dict_entites = None

        stats_frame = tk.Frame(self.fenetre, bg='lightblue', relief=tk.RIDGE, bd=2)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.nb_proies_label = tk.Label(stats_frame, text="Nombre de Proies: 0", font=("Helvetica", 14), bg='lightblue')
        self.nb_proies_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.nb_pred_label = tk.Label(stats_frame, text="Nombre de Prédateurs: 0", font=("Helvetica", 14), bg='lightblue')
        self.nb_pred_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        tk.Label(stats_frame, text="Herbe:", font=("Helvetica", 14), bg='lightblue').pack(side=tk.LEFT, padx=5)
        self.nb_herbe_label = ttk.Progressbar(stats_frame, orient="horizontal", length=200, mode="determinate", maximum=100)
        self.nb_herbe_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.temps_label = tk.Label(stats_frame, text="Temps: 0 s", font=("Helvetica", 14), bg='lightblue')
        self.temps_label.pack(side=tk.LEFT, padx=20, pady=5)

        config_container = tk.Frame(self.fenetre) # Pour couper la fenetre en deux parties apres la section des stats
        config_container.pack(fill=tk.BOTH, padx=10, pady=5)

        left_config = tk.Frame(config_container) # Pour la partie gauche de la configuration
        left_config.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        right_config = tk.Frame(config_container) # Pour la partie droite de la configuration
        right_config.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        init_frame = tk.LabelFrame(left_config, text="Paramètres Initiaux", font=("Helvetica", 12, "bold"), padx=10, pady=10)
        init_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(init_frame, text="Nombre de Proies:", font=("Helvetica", 10)).grid(row=0, column=0, sticky='w', pady=2)
        self.proies_entry = tk.Entry(init_frame, width=10)
        self.proies_entry.insert(0, "5")
        self.proies_entry.grid(row=0, column=1, pady=2)
        
        tk.Label(init_frame, text="Nombre de Prédateurs:", font=("Helvetica", 10)).grid(row=1, column=0, sticky='w', pady=2)
        self.predateurs_entry = tk.Entry(init_frame, width=10)
        self.predateurs_entry.insert(0, "3")
        self.predateurs_entry.grid(row=1, column=1, pady=2)
        
        tk.Label(init_frame, text="Niveau d'Herbe Initial:", font=("Helvetica", 10)).grid(row=2, column=0, sticky='w', pady=2)
        self.herbe_entry = tk.Entry(init_frame, width=10)
        self.herbe_entry.insert(0, str(configs.index_herbe))
        self.herbe_entry.grid(row=2, column=1, pady=2)
        
        entites_frame = tk.LabelFrame(left_config, text="Paramètres des Entités", font=("Helvetica", 12, "bold"), padx=10, pady=10)
        entites_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(entites_frame, text="Seuil de Faim:", font=("Helvetica", 10)).grid(row=0, column=0, sticky='w', pady=2)
        self.seuil_faim_entry = tk.Entry(entites_frame, width=10)
        self.seuil_faim_entry.insert(0, str(configs.seuil_faim))
        self.seuil_faim_entry.grid(row=0, column=1, pady=2)
        
        tk.Label(entites_frame, text="Seuil Reproduction Proies:", font=("Helvetica", 10)).grid(row=1, column=0, sticky='w', pady=2)
        self.seuil_repro_proie_entry = tk.Entry(entites_frame, width=10)
        self.seuil_repro_proie_entry.insert(0, str(configs.seuil_reproduction_proie))
        self.seuil_repro_proie_entry.grid(row=1, column=1, pady=2)
        
        tk.Label(entites_frame, text="Seuil Reproduction Prédateurs:", font=("Helvetica", 10)).grid(row=2, column=0, sticky='w', pady=2)
        self.seuil_repro_pred_entry = tk.Entry(entites_frame, width=10)
        self.seuil_repro_pred_entry.insert(0, str(configs.seuil_reproduction_predateur))
        self.seuil_repro_pred_entry.grid(row=2, column=1, pady=2)
        
        tk.Label(entites_frame, text="Énergie Maximale:", font=("Helvetica", 10)).grid(row=3, column=0, sticky='w', pady=2)
        self.energie_max_entry = tk.Entry(entites_frame, width=10)
        self.energie_max_entry.insert(0, str(configs.energie_max))
        self.energie_max_entry.grid(row=3, column=1, pady=2)
        
        tk.Label(entites_frame, text="Gain par Repas:", font=("Helvetica", 10)).grid(row=4, column=0, sticky='w', pady=2)
        self.gain_repas_entry = tk.Entry(entites_frame, width=10)
        self.gain_repas_entry.insert(0, str(configs.gain_repas))
        self.gain_repas_entry.grid(row=4, column=1, pady=2)
        
        tk.Label(entites_frame, text="Coût de Vie:", font=("Helvetica", 10)).grid(row=5, column=0, sticky='w', pady=2)
        self.cout_vie_entry = tk.Entry(entites_frame, width=10)
        self.cout_vie_entry.insert(0, str(configs.cout_vie))
        self.cout_vie_entry.grid(row=5, column=1, pady=2)
        
        tk.Label(entites_frame, text="Facteur de Reproduction:", font=("Helvetica", 10)).grid(row=6, column=0, sticky='w', pady=2)
        self.facteur_repro_entry = tk.Entry(entites_frame, width=10)
        self.facteur_repro_entry.insert(0, str(configs.facteur_reproduction))
        self.facteur_repro_entry.grid(row=6, column=1, pady=2)

        tk.Label(entites_frame, text="Énergie Départ Proies:", font=("Helvetica", 10)).grid(row=7, column=0, sticky='w', pady=2)
        self.energie_depart_proie_entry = tk.Entry(entites_frame, width=10)
        self.energie_depart_proie_entry.insert(0, str(configs.energie_depart_proie))
        self.energie_depart_proie_entry.grid(row=7, column=1, pady=2)
        
        tk.Label(entites_frame, text="Énergie Départ Prédateurs:", font=("Helvetica", 10)).grid(row=8, column=0, sticky='w', pady=2)
        self.energie_depart_pred_entry = tk.Entry(entites_frame, width=10)
        self.energie_depart_pred_entry.insert(0, str(configs.energie_depart_predateur))
        self.energie_depart_pred_entry.grid(row=8, column=1, pady=2)
        
        env_frame = tk.LabelFrame(right_config, text="Paramètres d'Environnement", font=("Helvetica", 12, "bold"), padx=10, pady=10)
        env_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(env_frame, text="Quantité d'Herbe Mangée:", font=("Helvetica", 10)).grid(row=0, column=0, sticky='w', pady=2)
        self.qte_herbe_mangee_entry = tk.Entry(env_frame, width=10)
        self.qte_herbe_mangee_entry.insert(0, str(configs.qte_herbe_mangee))
        self.qte_herbe_mangee_entry.grid(row=0, column=1, pady=2)
        
        tk.Label(env_frame, text="Fréquence Sécheresse:", font=("Helvetica", 10)).grid(row=1, column=0, sticky='w', pady=2)
        self.freq_secheresse_entry = tk.Entry(env_frame, width=10)
        self.freq_secheresse_entry.insert(0, str(configs.frequence_secheresse))
        self.freq_secheresse_entry.grid(row=1, column=1, pady=2)
        
        buttons_frame = tk.Frame(right_config)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        self.boutton_debut = tk.Button(buttons_frame, text="Démarrer la Simulation", command=self.start_simulation, bg='green', fg='white', font=("Helvetica", 12, "bold"), width=20, height=2)
        self.boutton_debut.pack(pady=5)
        
        self.boutton_reset = tk.Button(buttons_frame, text="Réinitialiser", command=self.reset_simulation, bg='orange', fg='white', font=("Helvetica", 12, "bold"), width=20, height=2)
        self.boutton_reset.pack(pady=5)

        log_frame = tk.Frame(self.fenetre)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(log_frame, text="Log des événements:", font=("Helvetica", 12, "bold")).pack(anchor='w')
        self.log_text = tk.Text(log_frame, height=15, state='disabled', bg='#f0f0f0', font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def add_log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_simulation(self):
        try:
            nb_proies = int(self.proies_entry.get())
            nb_predateurs = int(self.predateurs_entry.get())
            niveau_herbe = float(self.herbe_entry.get())

            configs.seuil_faim = int(self.seuil_faim_entry.get())
            configs.seuil_reproduction_proie = int(self.seuil_repro_proie_entry.get())
            configs.seuil_reproduction_predateur = int(self.seuil_repro_pred_entry.get())
            configs.energie_max = int(self.energie_max_entry.get())
            configs.gain_repas = int(self.gain_repas_entry.get())
            configs.cout_vie = int(self.cout_vie_entry.get())
            configs.facteur_reproduction = int(self.facteur_repro_entry.get())
            configs.energie_depart_proie = int(self.energie_depart_proie_entry.get())
            configs.energie_depart_predateur = int(self.energie_depart_pred_entry.get())

            configs.qte_herbe_mangee = int(self.qte_herbe_mangee_entry.get())
            configs.frequence_secheresse = int(self.freq_secheresse_entry.get())
            
        except ValueError:
            self.add_log("ERREUR: Veuillez entrer des valeurs numériques valides dans tous les champs.")
            return
        
        self.manager = multiprocessing.Manager()
        self.memoire = self.manager.list([0, 0, niveau_herbe])
        self.lock = self.manager.Lock()
        self.msg_queue = self.manager.Queue(maxsize=100)  # Augmenté de 10 à 100
        self.dict_entites = self.manager.dict()

        self.env_process = multiprocessing.Process(target=environment.env_process, args=(self.memoire, self.lock, self.msg_queue, self.dict_entites))
        self.env_process.start()

        time.sleep(0.5) # attendre que le serveur soit pret 

        for _ in range(nb_proies):
            envoyer_message(configs.nouvelle_proie)
        for _ in range(nb_predateurs):
            envoyer_message(configs.nouveau_predateur)

        self.temps_debut = time.time()
        self.update_loop()
        self.boutton_debut.config(state=tk.DISABLED)

    def reset_simulation(self):
        if self.env_process and self.env_process.is_alive():
            self.env_process.terminate()
            self.env_process.join()
            if self.env_process.is_alive():
                os.kill(self.env_process.pid, 9) # Kill forcé si nécessaire
        
        if self.manager:
            try:
                self.manager.shutdown()
            except: pass
            self.manager = None
        
        self.memoire = None
        self.lock = None
        self.msg_queue = None
        self.env_process = None
        self.dict_entites = None

        self.nb_proies_label.config(text="Nombre de Proies: 0")
        self.nb_pred_label.config(text="Nombre de Prédateurs: 0")
        self.nb_herbe_label['value'] = 0
        self.temps_label.config(text="Temps: 0 s")

        self.proies_entry.delete(0, tk.END)
        self.predateurs_entry.delete(0, tk.END)
        self.herbe_entry.delete(0, tk.END)
        
        self.proies_entry.insert(0, "5")
        self.predateurs_entry.insert(0, "3")
        self.herbe_entry.insert(0, "50")

        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        self.boutton_debut.config(state=tk.NORMAL)

    def update_loop(self):
        if not self.env_process or not self.env_process.is_alive():
            return 
        derniers_stats = None
        while True:
            try:
                etat = self.msg_queue.get_nowait()
                
                if isinstance(etat, list):
                    derniers_stats = etat
                elif isinstance(etat, str):
                    self.add_log(etat)
                    
            except queue.Empty:
                break
        if derniers_stats is not None:
            nb_proies, nb_predateurs, niveau_herbe = derniers_stats[0], derniers_stats[1], derniers_stats[2]
            self.nb_proies_label.config(text=f"Nombre de Proies: {nb_proies}")
            self.nb_pred_label.config(text=f"Nombre de Prédateurs: {nb_predateurs}")
            self.nb_herbe_label['value'] = niveau_herbe
            duree = int(time.time() - self.temps_debut)
            self.temps_label.config(text=f"Temps: {duree} s")

        self.fenetre.after(1000, self.update_loop)

    def run(self):
        self.fenetre.mainloop()

if __name__ == "__main__":
    try:
        Display().run()
    finally: #ca permet d'executer ce bout de code quoi qu'il se passe
        print("Nettoyage final des processus...")
        Display().reset_simulation()


