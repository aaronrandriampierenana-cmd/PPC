import multiprocessing
import sys
import time
import os
import socket
import random
import math
import configs

def trouver_proie_proche(pred_x, pred_y, dict_entites, lock):
    plus_proche = None
    dist_min = float('inf')
    RAYON_VISION = 10  # Le prédateur ne voit pas toute la carte
    
    with lock:
        items = list(dict_entites.items())
    
    for pid, data in items:
        if data.get('type') == 'proie':
            px, py = data.get('x'), data.get('y')
            # Distance de Manhattan (plus simple pour la grille)
            dist = abs(px - pred_x) + abs(py - pred_y)
            
            if dist < dist_min and dist <= RAYON_VISION:
                dist_min = dist
                plus_proche = (px, py)
    return plus_proche

def pred_process(memoire, lock, msg_queue, dict_entites):
    id = os.getpid()
    # Position initiale aléatoire
    x = random.randint(0, configs.GRID_SIZE - 1)
    y = random.randint(0, configs.GRID_SIZE - 1)
    
    # Enregistrement initial
    with lock:
        dict_entites[id] = {'type': 'predateur', 'energie': configs.energie_depart_predateur, 'x': x, 'y': y}
        memoire[configs.index_pred] += 1

    while True:
        # 1. Récupération de l'énergie actuelle
        with lock:
            if id not in dict_entites: break
            energie = dict_entites[id]['energie']
        
        if energie <= 0: break

        # 2. CHASSE : On cherche la proie la plus proche
        cible = trouver_proie_proche(x, y, dict_entites, lock)
        
        if cible:
            target_x, target_y = cible
            # Déplacement intelligent vers la cible
            if x < target_x: x += 1
            elif x > target_x: x -= 1
            if y < target_y: y += 1
            elif y > target_y: y -= 1
        else:
            # Si aucune proie, mouvement aléatoire pour ne pas rester immobile
            x = x + random.choice([-1, 0, 1])
            y = y + random.choice([-1, 0, 1])

        # Empêcher la sortie de la carte
        x = max(0, min(configs.GRID_SIZE - 1, x))
        y = max(0, min(configs.GRID_SIZE - 1, y))

        # 3. Tentative de manger (Collision)
        # On vérifie si une proie est sur la case actuelle
        mange = False
        # Dans pred.py, modifie la détection de collision :
        with lock:
            for pid, data in list(dict_entites.items()):
                if data.get('type') == 'proie' and data.get('x') == x and data.get('y') == y:
                    # SUPPRESSION IMMÉDIATE pour l'affichage
                    if pid in dict_entites:
                        del dict_entites[pid] 
                    
                    # Mise à jour des stats et énergie
                    memoire[configs.index_proie] -= 1
                    energie = min(energie + configs.gain_repas, configs.energie_max)
                    mange = True
                    msg_queue.put(f"Proie {pid} dévorée par {id}")
                    break
        
        if mange:
            msg_queue.put(f"Prédateur {id} a capturé une proie !")

        # 4. Reproduction
        if energie >= configs.seuil_reproduction_predateur:
            energie //= configs.facteur_reproduction
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    s.connect((configs.HOST, configs.PORT))
                    s.sendall(configs.nouveau_predateur)
            except: pass

        # 5. Coût de survie et mise à jour
        energie -= configs.cout_vie
        with lock:
            dict_entites[id] = {'type': 'predateur', 'energie': energie, 'x': x, 'y': y}
        
        # Temps de pause pour la fluidité (0.1s pour une chasse rapide)
        time.sleep(0.1)

        if energie <= 0:
            with lock:
                if id in dict_entites:
                    del dict_entites[id] # On retire l'entrée du dictionnaire
            break # On tue le processus

    # Nettoyage en cas de mort
    with lock:
        if id in dict_entites:
            del dict_entites[id]
        memoire[configs.index_pred] -= 1
    msg_queue.put(f"Prédateur {id} est mort de faim.")
