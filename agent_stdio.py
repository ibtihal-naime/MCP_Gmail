import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

# 1. Charger les variables d'environnement
load_dotenv()

async def main():
    print("🚀 Démarrage de l'agent MCP avec Google Workspace...\n")
    
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
    if not Path(credentials_path).exists():
        print(f"❌ Fichier credentials.json introuvable.")
        return
    
    # 2. Extraire les IDs du fichier credentials.json
    with open(credentials_path, 'r') as f:
        creds = json.load(f)
        installed = creds.get('installed', {})
        client_id = installed.get('client_id', '')
        client_secret = installed.get('client_secret', '')
    
    refresh_token = os.getenv('GOOGLE_WORKSPACE_REFRESH_TOKEN')
    if not refresh_token:
        print("❌ ERREUR : GOOGLE_WORKSPACE_REFRESH_TOKEN absent du .env")
        return

    # 3. Configuration du serveur MCP
    mcp_servers = {
        "google-workspace": {
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "google_workspace_mcp", "--credentials", credentials_path],
            "env": {
                "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
                "GOOGLE_WORKSPACE_CLIENT_ID": client_id,
                "GOOGLE_WORKSPACE_CLIENT_SECRET": client_secret,
                "GOOGLE_WORKSPACE_REFRESH_TOKEN": refresh_token,
            }
        }
    }
    
    try:
        # 4. Initialiser le client
        client = MultiServerMCPClient(mcp_servers)
        
        print("🔌 Connexion et récupération des outils...")
        # 5. Récupérer les outils directement
        tools = await client.get_tools()
        
        gmail_tools = [tool for tool in tools if "gmail" in tool.name.lower()]
        print(f"✅ {len(gmail_tools)} outils Gmail chargés !")

        # 6. Configurer le modèle et l'agent
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        agent_executor = create_react_agent(llm, tools=gmail_tools)
        
        print("\n🤖 Agent prêt ! (Tapez 'exit' pour quitter)")
        print("="*60)
        
        system_message = SystemMessage(
            content="Tu es un assistant intelligent expert Gmail. Réponds toujours en français."
        )
        
        while True:
            user_input = input("👤 Vous : ")
            if user_input.lower() in ['exit', 'quit', 'q']: break
            if not user_input.strip(): continue
            
            print("\n🤖 Agent travaille...")
            
            try:
                result = await agent_executor.ainvoke({
                    "messages": [system_message, HumanMessage(content=user_input)]
                })
                print(f"\n✅ Réponse : {result['messages'][-1].content}\n")
            except Exception as e:
                print(f"\n❌ Erreur pendant l'action : {str(e)}")
            
            print("-" * 60)

    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation : {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())