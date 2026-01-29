import multiprocessing
import sys
import time
import os
import socket
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import configs


def manger_proie(energie, memoire, lock, dict_entites, pred_id, msg_queue):
    mange = False
    proie_id = None
    with lock:
        if memoire[configs.index_proie] >= 1:
            for pid, (nature, ener, et) in list(dict_entites.items()):
                if nature == 'proie' and ener > 0 and pid != pred_id:
                    dict_entites[pid] = (nature, 0, et)
                    energie += configs.gain_repas
                    mange = True
                    proie_id = pid
                    break
    if mange and proie_id:
        msg_queue.put(f"Prédateur {pred_id} mange Proie {proie_id}")
    
    return energie, mange

def reproduction_predateur(energie):
    if energie >= configs.seuil_reproduction_predateur:
        energie //= configs.facteur_reproduction
        return True, energie
    return False, energie


def pred_process(memoire,lock,msg_queue,dict_entites):
    time.sleep(random.uniform(0, 0.5)) # pour desynchroniser les prédateurs sinon ils mangent tous en meme temps
    
    id=os.getpid()
    with lock:
        if id not in dict_entites:
            dict_entites[id] = ('predateur', configs.energie_depart_predateur, 'passif')
            memoire[configs.index_pred] += 1
        nature, energie, etat = dict_entites[id]
    while True:
        with lock:
            if id in dict_entites:
                nature, energie, etat = dict_entites[id]
            else:
                break
        if energie <= 0:
            break
        if energie <= configs.seuil_faim or energie >= configs.seuil_reproduction_predateur:
            etat = 'actif'
        if etat == 'actif' and energie <= configs.seuil_faim:
            energie, mange = manger_proie(energie, memoire, lock, dict_entites, id, msg_queue)
            if mange:
                if energie >= configs.seuil_reproduction_predateur:
                    success, energie = reproduction_predateur(energie)
                    if success:
                        msg_queue.put(f"Prédateur {id} se reproduit")
                        try:
                            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                                s.connect((configs.HOST,configs.PORT))
                                s.sendall(configs.nouveau_predateur)
                        except (ConnectionRefusedError, OSError) as e:
                            pass
                etat = 'passif'
        elif etat == 'actif' and energie >= configs.seuil_reproduction_predateur:
            success, energie = reproduction_predateur(energie)
            if success:
                msg_queue.put(f"Prédateur {id} se reproduit")
                etat = 'passif'
                try:
                    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                        s.connect((configs.HOST,configs.PORT))
                        s.sendall(configs.nouveau_predateur)
                except (ConnectionRefusedError, OSError) as e:
                    pass
        energie -= configs.cout_vie
        dict_entites[id] = (nature, energie, etat)
        time.sleep(1)
    with lock:
        memoire[configs.index_pred]-=1
        del dict_entites[id]
    msg_queue.put(f"Prédateur {id} est mort")
