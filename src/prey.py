import multiprocessing
import sys
import time
import os
import socket

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import configs

def prey_process(memoire,lock,dict_entites):
    id=os.getpid()
    print(f"Démarrage du prédateur {id}")
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            s.connect((configs.HOST,configs.PORT))
            s.sendall(configs.nouveau_predateur)
    except (ConnectionRefusedError, OSError) as e:
        pass
    nature,energie,etat=dict_entites[id]
    while True:
            

