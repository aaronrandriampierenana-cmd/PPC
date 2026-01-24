import multiprocessing
import sys
import time
import os
import socket

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import configs


def manger_herbe(energie, memoire, lock):
    with lock:
        if memoire[configs.index_herbe] >= configs.qte_herbe_mangee:
            memoire[configs.index_herbe] -= configs.qte_herbe_mangee
            energie += configs.gain_repas
    return energie    

def reproduction_proie(energie):
    if energie >= configs.seuil_reproduction_proie:
        energie//=configs.facteur_reproduction
        return True, energie
    return False, energie


def prey_process(memoire,lock,msg_queue,dict_entites):
    id=os.getpid()
    nature,energie,etat=dict_entites[id]
    while True:
        with lock:
            if id in dict_entites:
                nature, energie, etat = dict_entites[id]
            else:
                break
        if energie <= 0:
            break
        etat = 'actif'  # Reset l etat a chaque iteration
        if energie<=configs.seuil_faim:
            energie = manger_herbe(energie,memoire,lock)
            dict_entites[id]=(nature,energie,etat)
        if energie>=configs.seuil_reproduction_proie:
            success, energie = reproduction_proie(energie)
            if success:
                print(f"Proie {os.getpid()} se reproduit")
                dict_entites[id]=(nature,energie,etat)
                try:
                    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                        s.connect((configs.HOST,configs.PORT))
                        s.sendall(configs.nouvelle_proie)
                except (ConnectionRefusedError, OSError) as e:
                    pass
        energie-=configs.cout_vie
        dict_entites[id]=(nature,energie,etat)
        time.sleep(1)
    print(f"Proie {id} est morte")
    with lock:
        memoire[configs.index_proie]-=1
        del dict_entites[id]


