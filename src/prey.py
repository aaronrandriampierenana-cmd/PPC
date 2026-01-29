import multiprocessing
import sys
import time
import os
import socket
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import configs


def manger_herbe(energie, memoire, lock):
    mange = False
    with lock:
        if memoire[configs.index_herbe] >= configs.qte_herbe_mangee:
            memoire[configs.index_herbe] -= configs.qte_herbe_mangee
            energie += configs.gain_repas
            mange = True
    return energie, mange

def reproduction_proie(energie):
    if energie >= configs.seuil_reproduction_proie:
        energie //= configs.facteur_reproduction
        return True, energie
    return False, energie


def prey_process(memoire,lock,msg_queue,dict_entites):
    time.sleep(random.uniform(0, 0.5))# pour desynchroniser les proies sinon elles meurent toutes en meme temps
    
    id=os.getpid()
    with lock:
        if id not in dict_entites:
            dict_entites[id] = ('proie', configs.energie_depart_proie, 'passif')
            memoire[configs.index_proie] += 1
        nature, energie, etat = dict_entites[id]    
    while True:
        with lock:
            if id in dict_entites:
                nature, energie, etat = dict_entites[id]
            else:
                break
        if energie <= 0:
            break
        if energie <= configs.seuil_faim or energie >= configs.seuil_reproduction_proie:
            etat = 'actif'
        if etat == 'actif' and energie <= configs.seuil_faim:
            energie, mange = manger_herbe(energie, memoire, lock)
            if mange:
                if energie >= configs.seuil_reproduction_proie:
                    success, energie = reproduction_proie(energie)
                    if success:
                        msg_queue.put(f"Proie {id} se reproduit")
                        try:
                            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                                s.connect((configs.HOST,configs.PORT))
                                s.sendall(configs.nouvelle_proie)
                        except (ConnectionRefusedError, OSError) as e:
                            pass
                etat = 'passif'
        elif etat == 'actif' and energie >= configs.seuil_reproduction_proie:
            success, energie = reproduction_proie(energie)
            if success:
                msg_queue.put(f"Proie {id} se reproduit")
                etat = 'passif'
                try:
                    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                        s.connect((configs.HOST,configs.PORT))
                        s.sendall(configs.nouvelle_proie)
                except (ConnectionRefusedError, OSError) as e:
                    pass
        
        energie -= configs.cout_vie
        dict_entites[id] = (nature, energie, etat)
        time.sleep(1)
    with lock:
        memoire[configs.index_proie]-=1
        del dict_entites[id]
    msg_queue.put(f"Proie {id} est morte")
