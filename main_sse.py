import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

async def main():
    # Récupération du token
    mcp_token = os.getenv("MCP_API_TOKEN")
    
    if not mcp_token:
        print("❌ MCP_API_TOKEN non trouvé dans .env")
        return
    
    print(f"🔑 Token chargé : {mcp_token[:15]}...")
    
    mcp_servers = {
        "google-workspace": {
            "url": "http://localhost:8000/sse",
            "transport": "sse",
            "headers": {"Authorization": f"Bearer {mcp_token}"}
        }
    }
    
    try:
        print("🔐 Connexion au serveur SSE avec authentification...")
        
        # Initialisation du client avec timeout plus long
        client = MultiServerMCPClient(mcp_servers)
        
        # Récupération des outils
        print("⏳ Récupération des outils distants...")
        tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
        
        print(f"✅ {len(tools)} outils récupérés via SSE sécurisé")
        
        for tool in tools:
            print(f"   🔧 {tool.name}")

        # Configuration de l'agent
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        system_message = SystemMessage(
            content="Tu es un assistant expert Gmail. Utilise tes outils pour gérer les mails de l'utilisateur."
        )
        
        agent_executor = create_react_agent(llm, tools)
        
        print("\n🤖 Agent prêt ! (Tapez 'exit' pour quitter)")
        print("="*60)

        # Boucle interactive
        while True:
            user_input = input("\n👤 Vous : ")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Au revoir !")
                break
                
            if not user_input.strip():
                continue
            
            print("\n🤖 Agent travaille...")
            
            try:
                result = await agent_executor.ainvoke({
                    "messages": [system_message, HumanMessage(content=user_input)]
                })
                
                final_message = result['messages'][-1].content
                print(f"\n✅ IA : {final_message}")
            
            except Exception as e:
                print(f"❌ Erreur pendant l'action : {str(e)}")
            
            print("-" * 60)

    except asyncio.TimeoutError:
        print("❌ Timeout : Le serveur SSE ne répond pas")
        print("💡 Vérifiez que le serveur est démarré : python server_sse.py")
        
    except Exception as e:
        print(f"❌ Erreur de connexion SSE : {e}")
        print("\n💡 Vérifications :")
        print("   1. Le serveur SSE est-il démarré ? (python server_sse.py)")
        print("   2. Le token dans .env est-il correct ?")
        print("   3. Le port 8000 est-il disponible ?")
        
        # Afficher la trace complète pour debug
        import traceback
        print("\n🔍 Trace complète :")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
