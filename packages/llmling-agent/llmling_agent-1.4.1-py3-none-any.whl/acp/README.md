## ACP Protocol Features

### JSON-RPC 2.0 Communication

ACP uses JSON-RPC 2.0 over newline-delimited JSON streams:

```json
// Initialize request
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":1},"id":1}

// Initialize response
{"jsonrpc":"2.0","result":{"protocolVersion":1,"agentCapabilities":{...}},"id":1}

// Create session
{"jsonrpc":"2.0","method":"session/new","params":{"cwd":"/tmp"},"id":2}

// Session response
{"jsonrpc":"2.0","result":{"sessionId":"sess_abc123"},"id":2}

// Send prompt
{"jsonrpc":"2.0","method":"session/prompt","params":{
  "sessionId":"sess_abc123",
  "prompt":[{"type":"text","text":"Hello!"}]
},"id":3}

// Streaming responses via session updates
{"jsonrpc":"2.0","method":"session/update","params":{
  "sessionId":"sess_abc123",
  "update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"Hi there!"}}
}}
```

### Content Blocks

ACP supports rich content blocks:

```python
# Text content
TextContent(text="Hello world")

# Image content
ImageContent(type="image", data="base64...", mimeType="image/png")

# Audio content
AudioContent(type="audio", data="base64...", mimeType="audio/wav")

# Resource links
ResourceLink(type="resource_link", uri="file:///path/to/file", name="document.pdf")

# Embedded resources
EmbeddedResource(type="resource", resource=TextResourceContents(uri="...", text="..."))
```


### MCP Server Integration

ACP provides seamless integration with MCP (Model Context Protocol) servers, allowing agents to access external tools and data sources. MCP servers are automatically connected when creating sessions.

#### How MCP Integration Works

1. **Session Creation**: Client provides MCP server configurations in `session/new`
2. **Automatic Connection**: ACP server connects to all specified MCP servers
3. **Tool Integration**: MCP tools become available to the agent automatically
4. **Transparent Usage**: Agent can use MCP tools just like built-in tools
