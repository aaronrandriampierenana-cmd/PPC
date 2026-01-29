import multiprocessing
import sys
import time
import os
import socket
import random
import configs

def manger_herbe(energie, memoire, lock):
    mange = False
    with lock:
        if memoire[configs.index_herbe] >= configs.qte_herbe_mangee:
            memoire[configs.index_herbe] -= configs.qte_herbe_mangee
            energie += configs.gain_repas
            mange = True
    return min(energie, configs.energie_max), mange

def prey_process(memoire, lock, msg_queue, dict_entites):
    time.sleep(random.uniform(0, 0.5))
    id = os.getpid()
    # Initialisation de la position
    x, y = random.randint(0, configs.GRID_SIZE-1), random.randint(0, configs.GRID_SIZE-1)
    
    with lock:
        dict_entites[id] = {'type': 'proie', 'energie': configs.energie_depart_proie, 'x': x, 'y': y, 'etat': 'passif'}
        memoire[configs.index_proie] += 1

    while True:
        with lock:
            if id not in dict_entites:
                break
            energie = dict_entites[id]['energie']
            if energie <= 0:
                break

        # Déplacement
        x = x + random.choice([-1, 0, 1])
        y = y + random.choice([-1, 0, 1])

        # Empêcher la sortie de la carte
        x = max(0, min(configs.GRID_SIZE - 1, x))
        y = max(0, min(configs.GRID_SIZE - 1, y))
        
        # Logique d'état: actif si faim ou prêt à se reproduire
        a_faim = energie <= configs.seuil_faim
        peut_se_reproduire = energie >= configs.seuil_reproduction_proie
        etat = 'actif' if (a_faim or peut_se_reproduire) else 'passif'

        # Logique de faim/reproduction
        mange = False

        if a_faim:
            energie, mange = manger_herbe(energie, memoire, lock)
        
        elif peut_se_reproduire:
            energie //= configs.facteur_reproduction
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((configs.HOST, configs.PORT)); s.sendall(configs.nouvelle_proie)
            except: pass

        energie -= configs.cout_vie
        with lock:
            if id not in dict_entites:
                break
            dict_entites[id] = {'type': 'proie', 'energie': energie, 'x': x, 'y': y, 'etat': etat}
        time.sleep(0.2) # Plus rapide pour la fluidité visuelle

        if energie <= 0:
            break # On tue le processus

    with lock:
        if id in dict_entites:
            del dict_entites[id]
            memoire[configs.index_proie] -= 1
