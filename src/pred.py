import multiprocessing
import sys
import time
import os
import socket

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import configs


def manger_proie(energie, memoire, lock,dict_entites,pred_id):
    with lock:
        if memoire[configs.index_proie] >= 1:
            for pid, (nature, ener, et) in list(dict_entites.items()):
                if nature == 'proie' and ener > 0 and pid != pred_id:
                    dict_entites[pid] = (nature, 0, et)
                    energie += configs.gain_repas
                    break
    return energie

def reproduction_predateur(energie):
    if energie >= configs.seuil_reproduction_predateur:
        energie//=configs.facteur_reproduction
        return True, energie
    return False, energie


def pred_process(memoire,lock,msg_queue,dict_entites):
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
        etat = 'actif'  #Reset l etat a chaque iteration
        if energie<=configs.seuil_faim:
            energie = manger_proie(energie,memoire,lock,dict_entites,id)
            dict_entites[id]=(nature,energie,'actif')
        if energie>=configs.seuil_reproduction_predateur:
            success, energie = reproduction_predateur(energie)
            if success:
                print(f"Prédateur {os.getpid()} se reproduit")
                dict_entites[id]=(nature,energie,'actif')
                try:
                    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
                        s.connect((configs.HOST,configs.PORT))
                        s.sendall(configs.nouveau_predateur)
                except (ConnectionRefusedError, OSError) as e:
                    pass
        energie-=configs.cout_vie
        dict_entites[id]=(nature,energie,'actif')
        time.sleep(1)
    print(f"Prédateur {id} est mort")
    with lock:
        memoire[configs.index_pred]-=1
        del dict_entites[id]
    

            

