import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# On demande l'accès complet à Gmail pour envoyer des mails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_refresh_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    # Cela va ouvrir ton navigateur
    creds = flow.run_local_server(port=0)
    
    print("\n✅ AUTHENTIFICATION RÉUSSIE !")
    print(f"Voici ton REFRESH_TOKEN : {creds.refresh_token}")
    print("\nCopie cette valeur dans ton fichier .env")

if __name__ == '__main__':
    get_refresh_token()