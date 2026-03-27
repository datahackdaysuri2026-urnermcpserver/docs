# Urner MCP Server

This is the repo for the challenge [Urner MCP Server](https://hack.digital-cluster-uri.ch/project/50) of the [Data Hackdays Uri 2026](https://erp.digital-cluster-uri.ch/hackdays-uri-2026).

![Cover - Urner MCP Server](cover.png)

## MCP Host

To start the MCP Host consisting of the Open Web UI, run the following command. It's available at [http://localhost:3000](http://localhost:3000).

```bash
cd mcphost
docker compose up -d
```

Go to the connections [http://localhost:3000/admin/settings/connections](http://localhost:3000/admin/settings/connections) and use the **Manage Ollama** option to add a new model to the Ollama server. You can use the following model `llama3.1:8b` or any other model available in the [Ollama Registry](https://ollama.com/registry).
