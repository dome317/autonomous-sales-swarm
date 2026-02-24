---
description: n8n workflow JSON generation patterns and node type references. Auto-loads when creating or editing n8n workflow files. Contains validated node schemas and connection patterns.
---

# n8n Workflow JSON Patterns

## Core Node Types Used in This Project

### Webhook Trigger
```json
{
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 2,
  "parameters": {
    "httpMethod": "POST",
    "path": "swarm-lead-intake",
    "authentication": "headerAuth",
    "options": { "responseMode": "responseNode" }
  }
}
```

### AI Agent (LangChain)
```json
{
  "type": "@n8n/n8n-nodes-langchain.agent",
  "typeVersion": 2,
  "parameters": {
    "options": {
      "systemMessage": "=Du bist...",
      "maxIterations": 10,
      "returnIntermediateSteps": true
    }
  }
}
```

### Execute Sub-Workflow
```json
{
  "type": "n8n-nodes-base.executeWorkflow",
  "typeVersion": 1,
  "parameters": {
    "source": "database",
    "workflowId": "={{ $json.targetWorkflowId }}"
  }
}
```

### Supabase Vector Store (Insert)
```json
{
  "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
  "typeVersion": 1,
  "parameters": {
    "mode": "insert",
    "tableName": "documents",
    "queryName": "match_documents"
  }
}
```

### Switch Node (Routing)
```json
{
  "type": "n8n-nodes-base.switch",
  "typeVersion": 3,
  "parameters": {
    "rules": {
      "values": [
        { "conditions": { "options": { "version": 2 },
          "combinator": "and",
          "conditions": [
            { "leftValue": "={{ $json.route }}", "rightValue": "qualify", "operator": { "type": "string", "operation": "equals" } }
          ]
        }, "renameOutput": true, "outputKey": "qualify" }
      ]
    }
  }
}
```

### HubSpot (Update Deal)
```json
{
  "type": "n8n-nodes-base.hubspot",
  "typeVersion": 2,
  "parameters": {
    "resource": "deal",
    "operation": "update",
    "dealId": "={{ $json.dealId }}",
    "additionalFields": {
      "lead_score": "={{ $json.score }}",
      "lead_tags": "={{ $json.tags }}"
    }
  }
}
```

### Slack Notification (Error Alert)
```json
{
  "type": "n8n-nodes-base.slack",
  "typeVersion": 2,
  "parameters": {
    "channel": "#swarm-alerts",
    "text": "=Warning: Swarm Error: {{ $json.error }}\nLead: {{ $json.dealId }}\nAgent: {{ $json.agentName }}"
  }
}
```

## Connection Types
- `main` -> standard data flow
- `ai_languageModel` -> LLM connection to AI Agent
- `ai_tool` -> Tool connection to AI Agent
- `ai_memory` -> Memory connection to AI Agent
- `ai_outputParser` -> Output parser connection to AI Agent

## Error Handling Pattern
Wrap critical nodes in a try/catch:
```json
{
  "type": "n8n-nodes-base.errorTrigger",
  "parameters": {}
}
```
Connect error output to Slack + Notion logging node.
