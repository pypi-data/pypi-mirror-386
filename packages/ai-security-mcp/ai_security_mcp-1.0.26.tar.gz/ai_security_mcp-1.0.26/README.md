# AI Security Scanner MCP - Cloud Edition

World's first comprehensive agentic AI security scanner with 27 specialized
agents covering 100% OWASP ASI + LLM vulnerabilities. This thin client
connects to our secure cloud infrastructure where all scanning happens.

## 🏗️ Architecture

This package is a **lightweight cloud proxy** (~50KB) that connects Claude Code
to our cloud-hosted security scanning infrastructure. All 27 security agents
run in our secure Google Cloud environment, not on your local machine.

**Benefits of Cloud Architecture**:
- Always up-to-date security rules
- No local compute resources needed
- Proprietary agent logic protected
- Consistent scanning environment
- Sub-second scan execution

## 🚀 Quick Start

### Step 1: Get Your API Key

1. Visit [https://app.ai-threat-scanner.com/dashboard/api-keys](https://app.ai-threat-scanner.com/dashboard/api-keys)
2. Sign up for free account
3. Generate new API key
4. Copy your key (format: `ciso_live_abc123xyz`)

### Step 2: Install Thin Client

```bash
claude mcp add ai-security-scanner \
  -e AI_SECURITY_API_KEY=ciso_live_abc123xyz \
  -- uvx ai-security-mcp
```

Replace `ciso_live_abc123xyz` with your actual API key.

### Step 3: Start Scanning

Open Claude Code and ask:
```
Scan this repository for AI security vulnerabilities
```

The thin client will connect to our cloud infrastructure, execute all 27
security agents, and return comprehensive vulnerability findings.

## 📊 What You Get

### 27 Cloud-Hosted Security Agents

**OWASP ASI (17 agents)**: Memory Poisoning, Tool Misuse, Privilege Compromise,
Resource Overload, Cascading Hallucination, Intent Breaking, Misaligned Behaviors,
Repudiation, Identity Spoofing, Overwhelming HITL, Unexpected RCE, Agent
Communication Poisoning, Rogue Agents, Human Attacks, Human Manipulation,
Insecure Protocol, Supply Chain

**OWASP LLM Top 10 (10 agents)**: Prompt Injection, Insecure Output Handling,
Training Data Poisoning, Model DoS, Supply Chain, Information Disclosure,
Insecure Plugin Design, Excessive Agency, Overreliance, Model Theft

## 🔒 Security & Privacy

**Cloud Processing**: Your code is analyzed in our secure Google Cloud
infrastructure with enterprise-grade security controls.

**Data Handling**:
- Code analyzed in isolated containers
- Results returned via encrypted HTTPS
- No permanent storage of your code
- Scan metadata tracked for quota management

**Authentication**: API keys use secure Bearer token authentication with
per-user quota tracking and access control.

## 📖 Usage Examples

### Basic Repository Scan
```
Scan this repository for agentic AI vulnerabilities
```

### Check Specific Files
```
Use the AI Security Scanner to check these files for prompt injection:
- src/prompts.py
- src/llm_integration.py
```

### Get Scan History
```
Show my recent AI security scans
```

## 🛠️ Troubleshooting

### "API Key Required" Error

You need to set your API key. Get it from:
https://app.ai-threat-scanner.com/dashboard/api-keys

Then reconfigure:
```bash
claude mcp remove ai-security-scanner
claude mcp add ai-security-scanner \
  -e AI_SECURITY_API_KEY=your_actual_key \
  -- uvx ai-security-mcp
```

### "Connection Failed" Error

Check cloud service status:
```bash
curl https://ai-security-mcp-fastmcp-production-722116092626.us-central1.run.app/health
```

If service is down, check status page: https://status.ai-threat-scanner.com

### "Quota Exceeded" Error

You've reached your scan limit. View usage at:
https://app.ai-threat-scanner.com/dashboard/usage

Upgrade your plan or wait for quota reset.

## 💰 Pricing

- **Free Tier**: 10 scans/day, 100 scans/month
- **Pro Tier**: 100 scans/day, unlimited monthly
- **Enterprise**: Custom quotas and dedicated support

View pricing: https://ai-threat-scanner.com/pricing

## 📚 Documentation

- **Dashboard**: https://app.ai-threat-scanner.com
- **Full Documentation**: https://ai-threat-scanner.com/docs
- **OWASP ASI Specification**: https://owasp.org/www-project-ai-security-and-privacy-guide/
- **Bug Reports**: https://github.com/ai-security-scanner/ai-security-mcp/issues

## 🏢 Architecture Details

This package contains only the thin client proxy. The actual security scanning
happens in our cloud infrastructure:

```
Your Machine          Cloud Infrastructure
┌─────────────┐      ┌──────────────────────┐
│ Claude Code │─────▶│ Cloud MCP Server     │
│             │      │ - 27 Security Agents │
│ Thin Client │◀─────│ - Vulnerability DB   │
│ (~50KB)     │      │ - Analysis Engine    │
└─────────────┘      └──────────────────────┘
```

**Thin Client Responsibilities**:
- MCP protocol (stdio) with Claude Code
- HTTPS proxy to cloud server
- API key authentication
- Request/response forwarding

**Cloud Server Responsibilities**:
- API key validation
- Agent execution (all 27)
- Vulnerability analysis
- Report generation
- Quota tracking

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **Website**: https://ai-threat-scanner.com
- **Dashboard**: https://app.ai-threat-scanner.com
- **GitHub**: https://github.com/ai-security-scanner/ai-security-mcp
- **PyPI**: https://pypi.org/project/ai-security-mcp/
- **Support**: support@ai-threat-scanner.com
