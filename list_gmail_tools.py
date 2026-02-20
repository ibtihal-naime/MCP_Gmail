import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")

mcp_servers = {
    "google-workspace": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "google_workspace_mcp", "--credentials", credentials_path],
        "env": {
            "GOOGLE_APPLICATION_CREDENTIALS": credentials_path
        }
    }
}

async def main():
    client = MultiServerMCPClient(mcp_servers)
    tools = await client.get_tools()
    gmail_tools = [t for t in tools if "gmail" in t.name.lower()]
    print(f"✅ {len(gmail_tools)} outils Gmail trouvés :")
    for i, t in enumerate(gmail_tools, 1):
        print(f"{i}. {t.name} - {t.description}")
    if hasattr(client, "close"):
        await client.close()

asyncio.run(main())
