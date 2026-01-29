import multiprocessing
import os
import time
import socket
import sys
import threading
import configs
import random
import queue
from pred import pred_process
from prey import prey_process

msg_queue_global = None
timer_secheresse = None

def secheresse():
    global msg_queue_global, timer_secheresse  
    if msg_queue_global is not None:
        chances = random.randint(1, 100)
        if chances <= 50 and not configs.sech:
            configs.sech = True
            msg_queue_global.put("La sécheresse est maintenant activée.")
        elif chances >= 50 and configs.sech:
            configs.sech = False
            msg_queue_global.put("La sécheresse est maintenant désactivée.")
    timer_secheresse = threading.Timer(configs.frequence_secheresse, secheresse)
    timer_secheresse.daemon = True
    timer_secheresse.start()

def croissance_herbe(memoire):
        if memoire[configs.index_herbe]<100:
            croissance = 1.0 if not configs.sech else 0.5
            memoire[configs.index_herbe]+=croissance
            if memoire[configs.index_herbe]>100.0:
                memoire[configs.index_herbe]=100.0

def env_process(memoire,lock,msg_queue,dict_entites):
    global msg_queue_global, timer_secheresse
    msg_queue_global = msg_queue
    
    msg_queue.put("Démarrage de l'environnement...")
    temps_debut = time.time()
    compteur_iterations=0
    
    timer_secheresse = threading.Timer(configs.frequence_secheresse, secheresse)
    timer_secheresse.daemon = True
    timer_secheresse.start()
    msg_queue.put(f"Timer de sécheresse configuré (fréquence: {configs.frequence_secheresse}s)")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((configs.HOST,configs.PORT))
        except socket.error as e:
            msg_queue.put(f"Erreur de liaison de la socket {e}")
            return
        s.listen()
        s.setblocking(False)
        msg_queue.put(f"Serveur en écoute sur {configs.HOST}:{configs.PORT}")
        try:
            while True:
                compteur_iterations+=1
                with lock:
                    croissance_herbe(memoire)
                try :
                    conn,addr=s.accept()
                    with conn:
                        msg=conn.recv(1024)
                        if msg==configs.nouveau_predateur:
                            p = multiprocessing.Process(target=pred_process, args=(memoire, lock, msg_queue, dict_entites))
                            p.start()
                        elif msg==configs.nouvelle_proie:
                            p = multiprocessing.Process(target=prey_process, args=(memoire, lock, msg_queue, dict_entites))
                            p.start()
                except BlockingIOError:
                    pass
                except socket.timeout:
                    pass
                except Exception as e:
                    msg_queue.put(f"Erreur inattendue : {e}")
                
                if not msg_queue.full(): 
                    etat_acc=list(memoire)
                    msg_queue.put(etat_acc)
                
                with lock:
                    if compteur_iterations > 10 and memoire[configs.index_proie] == 0 and memoire[configs.index_pred] == 0:
                        time.sleep(0.5)
                        etat_final = list(memoire)
                        msg_queue.put(etat_final)
                        duree = time.time() - temps_debut
                        msg_queue.put("\nExtinction totale - Aucune entité restante")
                        msg_queue.put(f"Durée de la simulation : {duree:.1f}s")
                        print("Arrêt de la simulation...")
                        break
                
                time.sleep(1)
        except KeyboardInterrupt:
            duree = time.time() - temps_debut
            print("\nArrêt de l'environnement")
            print(f"Durée de la simulation : {duree}s")

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    memoire = manager.list([0, 0, 50])  # proies, prédateurs, herbe
    lock = manager.Lock()
    msg_queue = manager.Queue(maxsize=100)
    dict_entites = manager.dict()
    env_proc = multiprocessing.Process(target=env_process, args=(memoire, lock, msg_queue, dict_entites))
    env_proc.start()
    env_proc.join()


                
