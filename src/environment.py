import multiprocessing
import os
import time
import socket
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import configs
import random
import queue
from pred import pred_process
from prey import prey_process

def secheresse(etat):
    chances=random.randint(1,100)
    if chances <=33 and not etat:
        etat="activée"
        print(f"La sécheresse est maintenant {etat}.")
    elif chances>=67 and etat:
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
    compteur_secheresse=0 # pour ne changer la sécheresse que toutes les frequences_secheresse itérations
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
                compteur_secheresse+=1
                if compteur_secheresse%configs.frequence_secheresse==0:
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
                        print(f"Nouveau prédateur (Total : {memoire[configs.index_pred]})")
                        p = multiprocessing.Process(target=pred_process, args=(memoire, lock, msg_queue, dict_entites))
                        p.start()
                        with lock:
                            dict_entites[p.pid] = ('predateur',50,'actif')
                    elif msg==configs.nouvelle_proie:
                        with lock:
                            memoire[configs.index_proie]+=1
                        print(f"Nouvelle proie (Total : {memoire[configs.index_proie]})")
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
            if not msg_queue.full(): 
                etat_acc=list(memoire)
                msg_queue.put(etat_acc)
            
            time.sleep(1)
        except KeyboardInterrupt:
            print("Arrêt de l'environnement")




                
