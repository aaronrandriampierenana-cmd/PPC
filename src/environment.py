import multiprocessing
import os
import time
import socket
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import configs
import random
import queue
from pred import pred_process
from prey import prey_process

def secheresse(etat):
    chances=random.randint(1,100)
    if chances <=50 and not etat:
        etat="activée"
        print(f"La sécheresse est maintenant {etat}.")
    elif chances>=50 and etat:
        etat="désactivée"
        print(f"La sécheresse est maintenant {etat}.")

def croissance_herbe(memoire):
        if memoire[configs.index_herbe]<100:
            croissance = 1.0 if configs.sech else 0.5
            memoire[configs.index_herbe]+=croissance
            if memoire[configs.index_herbe]>100.0:
                memoire[configs.index_herbe]=100.0

def env_process(memoire,lock,msg_queue,dict_entites):
    print("Démarrage de l'environnement...")
    temps_debut = time.time()
    compteur_iterations=0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((configs.HOST,configs.PORT))
        except socket.error as e:
            print(f"Erreur de liaison de la socket {e}")
            return
        s.listen()
        s.setblocking(False)
        print(f"Server en écoute sur {configs.HOST}:{configs.PORT}")
        try:
            while True:
                compteur_iterations+=1
                if compteur_iterations%configs.frequence_secheresse==0:
                    secheresse(configs.sech)
                with lock:
                    croissance_herbe(memoire)
                try :
                    conn,addr=s.accept()
                    with conn:
                        msg=conn.recv(1024)
                        if msg==configs.nouveau_predateur:
                            with lock:
                                memoire[configs.index_pred]+=1
                            p = multiprocessing.Process(target=pred_process, args=(memoire, lock, msg_queue, dict_entites))
                            p.start()
                            with lock:
                                dict_entites[p.pid] = ('predateur',50,'actif')
                        elif msg==configs.nouvelle_proie:
                            with lock:
                                memoire[configs.index_proie]+=1
                            p = multiprocessing.Process(target=prey_process, args=(memoire, lock, msg_queue, dict_entites))
                            p.start()
                            with lock:
                                dict_entites[p.pid] = ('proie',30,'actif')
                except BlockingIOError:
                    pass
                except socket.timeout:
                    pass
                except Exception as e:
                    print(f"Erreur inattendue : {e}")
                print(f"\nÉTAT: Proies={memoire[configs.index_proie]} | Prédateurs={memoire[configs.index_pred]} | Herbe={memoire[configs.index_herbe]}")
                with lock:
                    if compteur_iterations > 10 and memoire[configs.index_proie] == 0 and memoire[configs.index_pred] == 0:
                        duree = time.time() - temps_debut
                        print("\nExtinction totale - Aucune entité restante")
                        print(f"Durée de la simulation : {duree}s")
                        print("Arrêt de la simulation...")
                        break
                
                if not msg_queue.full(): 
                    etat_acc=list(memoire)
                    msg_queue.put(etat_acc)
                time.sleep(1)
        except KeyboardInterrupt:
            duree = time.time() - temps_debut
            print("\nArrêt de l'environnement")
            print(f"Durée de la simulation : {duree}s")

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    memoire = manager.list([0, 0, 50])  # proies, prédateurs, herbe
    lock = manager.Lock()
    msg_queue = manager.Queue(maxsize=10)
    dict_entites = manager.dict()
    env_proc = multiprocessing.Process(target=env_process, args=(memoire, lock, msg_queue, dict_entites))
    env_proc.start()
    env_proc.join()


                
