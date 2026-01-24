
import socket
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import configs

def envoyer_message(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((configs.HOST, configs.PORT))
            s.sendall(message)
            print(f"Message envoyé : {message.decode()}")
            return True
    except ConnectionRefusedError:
        print("Serveur non disponible. Assurez-vous que environment.py est en cours d'exécution.")
        return False
    except Exception as e:
        print(f"Erreur : {e}")
        return False

def main():
    print("Test de la simulation prédateur-proie")
    time.sleep(2)
    for _ in range(3):
        envoyer_message(configs.nouvelle_proie)
        time.sleep(1)
    for _ in range(2):
        envoyer_message(configs.nouveau_predateur)
        time.sleep(1)

if __name__ == "__main__":
    main()
