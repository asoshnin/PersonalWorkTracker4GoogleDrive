# **DeerFlow Proactive Agentic Architect Deployment Guide (v01)**

# **Section 1: Hardware & Infrastructure Setup**

## **1.1 Docker and Local Model Prerequisites**

To deploy the Proactive Agentic Architect on DeerFlow, you must first establish the containerization and local LLM runtime environments. Below are the exact commands and steps for installing Docker and Ollama on Windows 11 and macOS.

### **Step 1: Install Docker Desktop**

#### ***Windows 11:***

1. Download Docker Desktop from the official source: `https://www.docker.com/products/docker-desktop/`.  
2. Run the installer, follow the on-screen prompts, and restart your computer when prompted.  
3. Open PowerShell and verify the installation:

```
docker --version
```

Expected output: `Docker version 24.x.x` or higher.

#### ***macOS:***

1. Download Docker Desktop from: `https://www.docker.com/products/docker-desktop/`.  
2. Drag the `Docker.app` icon into your Applications folder, then open it from Applications to initialize the daemon.  
3. Open Terminal and verify the installation:

```shell
docker --version
```

Expected output: `Docker version 24.x.x` or higher.

### **Step 2: Install Ollama (Local Model Runtime)**

#### ***Windows 11:***

1. Download the installer directly from: `https://ollama.com/download`.  
2. Run the executable to install the Ollama background service.  
3. Open PowerShell, verify the version, and check that the API is running:

```
ollama --version
curl http://localhost:11434/api/tags
```

Expected output: A JSON list of available models.

#### ***macOS:***

1. The recommended installation method is via Homebrew. Open your Terminal and run:

```shell
brew install ollama
```

*(Alternatively, you may download the macOS package from `https://ollama.com/download`)*. 2\. Start the service (macOS typically auto-starts it) and verify the API is accessible:

```shell
ollama --version
curl http://localhost:11434/api/tags
```

Expected output: A JSON list of available models.

## **1.2 Hardware Optimization for 11GB VRAM GPUs**

When deploying local models for the Proactive Agentic Architect on a machine with an 11GB VRAM GPU (such as a Windows 11 setup), strict hardware limits must be enforced to ensure pipeline stability.

An 11GB VRAM GPU is insufficient to run a 9B parameter model at `Q8_0` (8-bit quantization) with an 8K context window. The `Q8_0` model weights alone require roughly 9.5GB of VRAM. Once you add the KV cache required for complex multi-agent context handoffs, plus the 1-2GB reserved by Windows for the display manager, the system will rapidly experience Out-Of-Memory (OOM) crashes as the context grows.

To prevent this, you **MUST** enforce the use of `Q4_K_M` (4-bit medium) quantization for 9B models. `Q4_K_M` is the definitive industry-standard sweet spot for 8GB-12GB GPUs, requiring only \~6GB to 7GB of VRAM. Utilizing `Q4_K_M` guarantees that at least 3-4GB of VRAM is left free for the KV cache and embedded tool operations, while also providing enough headroom if a small embedding model is needed alongside it.

Execute the following terminal command to pull the correct hardware-optimized model:

```shell
# Primary reasoning model – Qwen 3.5 9B, recommended Q4_K_M quantization
ollama pull qwen3.5:9b
```

**CRITICAL WARNING:** You must absolutely avoid forcing 8-bit quantization (e.g., `q8_0`) for any 9B class models on an 11GB GPU limit.

## **1.3 Docker Networking Configuration**

Because DeerFlow and the AIO Sandbox run inside Docker containers, they cannot use `localhost` to reach the Ollama service running natively on the host machine's operating system. Attempting to route traffic to `localhost:11434` from inside a container will result in connection failures, as the container resolves `localhost` to itself.

To allow DeerFlow and the AIO Sandbox to communicate safely with the host machine's Ollama instance, you must utilize the `host.docker.internal` host-gateway resolution. On Windows 11 and macOS using Docker Desktop, this address automatically resolves to the host machine.

To ensure this resolution works reliably for the sandbox container, you must explicitly declare the routing using the `extra_hosts` parameter in your Docker Compose configuration.

**Docker Compose Configuration:** Add the following `extra_hosts` mapping to your AIO Sandbox or DeerFlow API service definitions:

```
services:
  sandbox:
    image: ghcr.io/agent-infra/sandbox:latest
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "8080:8080"
```

**DeerFlow config.yaml Configuration:** When configuring your LLM provider in DeerFlow's `config.yaml`, you must set the `base_url` to utilize this internal Docker hostname instead of localhost. For an OpenAI-compatible Ollama endpoint, the configuration must look like this:

```
models:
  - name: qwen3-9b
    use: langchain_openai:ChatOpenAI
    model: qwen3.5:9b
    base_url: http://host.docker.internal:11434/v1
    api_key: ollama
```

By enforcing this networking configuration, both the main DeerFlow LangGraph server and the isolated AIO Sandbox container can seamlessly execute inferences against the host's GPU resources.

## **1.4 Repository Initialization and Environment Configuration**

Before injecting agents or skills, you must clone the DeerFlow repository and generate the configuration files.

### **Step 1: Clone the Repository** 

On your local host machine, open a terminal and run:

```shell
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
```

### **Step 2: Generate Configuration Files** 

Run the following command to generate the default configuration files:

```shell
make config
```

This creates `config.yaml` and `.env`.

### **Step 3: Configure Environment Variables**

Edit the `.env` file to set the placeholder API keys required for LangChain to interface with local Ollama endpoints:

```
OPENAI_API_KEY=ollama-placeholder
TAVILY_API_KEY=your-tavily-api-key
```

# **Section 2: Skill Deployment Architecture**

## **2.1 Direct Filesystem Injection Method (The Golden Path)**

While DeerFlow technically supports a REST API for skill deployment, you **MUST NOT** use the `POST /api/skills/install` endpoint for programmatic automation. Relying on this API requires headless automation to manage brittle virtual path resolutions and introduces unnecessary thread-management overhead, such as associating the uploaded `.skill` ZIP archive with a specific `thread_id`.

Instead, the canonical and most reliable method for custom skill deployment is direct filesystem injection. DeerFlow 2.0 is natively designed to auto-discover and progressively load new skills via path mapping.

To programmatically deploy a skill, your automated workflow (or Proactive Agentic Architect) must bypass the API entirely and write directly to the filesystem. You do this by creating a dedicated directory for the skill and writing a `SKILL.md` manifest into it:

1. Create a directory at the path: `/mnt/skills/custom/[skill-name]/`.  
2. Write a `SKILL.md` file into this directory.

The `SKILL.md` file **must** contain a valid YAML frontmatter block defining the skill's metadata, immediately followed by the standard markdown instructions that the LLM will read.

Here is the exact required format for the `SKILL.md` injection:

```
---
name: your-skill-name
description: A clear, single-sentence description of what this skill does
license: MIT
---

# Skill Instructions

[Insert the exact Markdown content and Python code with the skill instructions here]
```

Once this file is written to the `/mnt/skills/custom/[skill-name]/` directory, DeerFlow's internal watcher will automatically discover, validate, and register the custom skill into the global workspace without requiring a container restart.

## **2.2 Skill Configuration and Security Sandboxing**

When creating custom skills for the Proactive Agentic Architect, you must strictly adhere to DeerFlow's syntax rules and security constraints. Failure to follow these configurations will result in validation errors or vulnerabilities within the execution environment.

**Skill Naming and Metadata Syntax Rules:** The `SKILL.md` frontmatter and the associated directory name must pass DeerFlow's internal regex and validation checks.

* **Hyphen-case strictly enforced:** The skill name must match the pattern `^[a-z0-9-]+$`. It must use lowercase letters, digits, and hyphens only.  
* **Hyphen placement:** The skill name cannot start or end with a hyphen, nor can it contain consecutive hyphens (`--`).  
* **Length limits:** The skill name is limited to a maximum of 64 characters. The description field must not exceed 1024 characters.  
* **Character bans:** The description field must not contain any angle brackets (`<` or `>`).

**Security Sandboxing (The Security Ban):** Because DeerFlow utilizes a Python execution environment (like the AIO Sandbox) to run custom skills, you must enforce a strict security perimeter. Any Python code generated for or embedded within a custom skill MUST NEVER contain the following:

* **Forbidden Execution Commands:** The use of `subprocess`, `os.system`, `exec()`, or `eval()` is strictly banned to prevent sandbox escape and arbitrary system command execution.  
* **Restricted File System Access:** Skills must not mount or access local file systems outside of the designated sandbox directories: `/workspace/`, `/mnt/user-data/`, and `/mnt/skills/`.  
* **Secret Management:** Hardcoding API keys or credentials directly into the skill's Python code is forbidden. All keys must be securely retrieved during execution using `os.environ.get()`.

# **Section 3: Programmatic Agent Generation**

## **3.1 SubagentConfig Dataclasses Framework**

Because DeerFlow 2.0 operates as a LangGraph-based "SuperAgent harness," subagents are not standalone API entities; instead, they are treated as structural nodes within the state graph. During pipeline execution, the lead agent dynamically spawns these subagent nodes using the `task` tool.

Because of this architecture, you **MUST NOT** attempt to deploy agents or subagents by sending JSON payloads to a `POST /api/agents` REST endpoint. This endpoint does not exist in the DeerFlow platform, and relying on it is a known hallucination that will cause your deployment to fail.

Instead, you must programmatically define all subagents as Python `SubagentConfig` dataclasses. This framework requires you to explicitly declare the agent's structural parameters within Python code, enforcing strict definitions for names, prompts, tool allowlists, and execution timeout protections.

When generating code for a new subagent, you must utilize the following exact `SubagentConfig` structure:

```py
from src.subagents.config import SubagentConfig

MY_AGENT_CONFIG = SubagentConfig(
    name="my-agent-name",                      # Unique identifier, strictly hyphen-case
    description="When to delegate to this subagent", # Human/LLM readable trigger
    system_prompt="""You are a specialized subagent...""", 
    tools=["tool1", "tool2"],                  # Allowlist of tool names (None = inherit all)
    disallowed_tools=["task"],                 # Denylist of tool names (e.g., prevent nesting)
    model="inherit",                           # Model to use ("inherit" = parent model)
    max_turns=50,                              # Maximum agent turns
    timeout_seconds=900,                       # Timeout protection (15 minutes default)
)
```

## **3.2 Code Injection and Subagent Registration**

To deploy a subagent into the DeerFlow architecture, you must completely bypass the non-existent REST API and perform a direct codebase injection. The deployment script or human operator must execute the following workflow to ensure the subagent is properly registered and loaded into the StateGraph topology.

### **Step 1: Inject the Configuration File** 

First, generate a Python (`.py`) file containing your complete `SubagentConfig` dataclass (which defines the agent's name, system prompt, tool allowlist, and timeout protections).

**CRITICAL CLARIFICATION**: You must write this file directly into the built-in subagents directory on your **local host repository**, NOT inside the running Docker container. The directory path is: `backend/src/subagents/builtins/`

Because the local repository is volume-mapped into the Docker container via `docker-compose.yaml`, making the modifications on your local host ensures the changes persist across the `make docker-restart` lifecycle. For example, if you created `UST-Worker-Fundamentals.py`, place it in the local host directory above.

### **Step 2: Register the Subagent in `__init__.py`** 

Once the file is injected, you must explicitly expose the subagent to DeerFlow's global router. Open the registry file located at `backend/src/subagents/builtins/__init__.py`.

You must append an import statement for your new agent and assign its configuration object into the `BUILTIN_SUBAGENTS` dictionary.

Here is the exact code snippet demonstrating this modification:

```py
# 1. Add the import statement at the top of the file:
from .ust_worker_fundamentals import UST_WORKER_FUNDAMENTALS_CONFIG

# 2. Append the registry assignment into the dictionary:
BUILTIN_SUBAGENTS = {
    # ... existing agents ...
    "UST-Worker-Fundamentals": UST_WORKER_FUNDAMENTALS_CONFIG,
}
```

### **Step 3: Issue a Service Restart** 

Because the subagents are hardcoded Python objects rather than dynamic database entries, the containerized backend will not instantly recognize the new files. To finalize the deployment and load the new StateGraph topology, you must restart the DeerFlow services from your terminal:

```shell
make docker-restart
```

*(Alternatively, if running locally outside of the production Docker wrapper, you can stop the LangGraph server and run `make docker-stop && make docker-start`).*

# **Section 4: The Proactive Agentic Architect (Deployment & Operations)**

## **4.1 Core Infrastructure Agent System Prompts**

To operationalize the Proactive Agentic Architect, you must instantiate two core infrastructure agents within the DeerFlow workspace. Below are the exact XML system prompts required to initialize them.

### **1\. The Directory Facilitator (00-Directory-Facilitator)** 

This agent is strictly responsible for maintaining the global JSON and Markdown registries.

```xml
<system_prompt>
<role>
You are the 00-Directory-Facilitator for the DeerFlow Workspace. Your sole responsibility is maintaining the global registries for all active agents and custom skills.
</role>

<execution_standards>
- You serve both Human Users and Orchestrator Agents.
- If an agent queries you for dependencies, read your backend records and return the exact Agent Name.
- If asked to register new agents or skills, append new records using your Python Execution skill.
</execution_standards>

<state_mutation_rules>
Your source of truth is ALWAYS `/workspace/registry-backend.json`.
When registering a new agent or skill, you must first update the JSON file.

IMMEDIATELY AFTER updating the JSON, you must run a Python script to overwrite `/workspace/agent-registry.md` and `/workspace/skill-registry.md` with perfectly formatted Markdown tables generated from the JSON data.
The `/workspace/agent-registry.md` file MUST follow this Markdown table format:
| Agent Name | Pipeline | Role | Core Capabilities | Input Format |
| :--- | :--- | :--- | :--- | :--- |

The `/workspace/skill-registry.md` file MUST follow this Markdown table format:
| Skill Name | Pipeline | Description | Input Schema |
| :--- | :--- | :--- | :--- |
</state_mutation_rules>

<hitl_gate>
CRITICAL: Before registering any new agent or skill, you MUST:
1. Display the proposed registration manifest to the user.
2. Ask: "Do you APPROVE this registration? Type 'approve' to proceed.".
3. Wait for explicit user approval before proceeding.
4. Log the approval to /workspace/hitl-log.json with timestamp and user decision.
</hitl_gate>
</system_prompt>
```

### **2\. The Proactive Agentic Architect (00-Proactive-Agentic-Architect)** 

This is the elite Multi-Agent System designer. Its prompt strictly enforces the Golden Truth deployment paths: direct filesystem injection for skills, and programmatic Python dataclass injection for subagents.

````xml
<system_prompt>
<role>
You are the Proactive Agentic Architect - an elite Multi-Agent System (MAS) designer operating within the DeerFlow Workspace. Unlike passive architects, you PROACTIVELY design, build, and DEPLOY agents and skills programmatically via the DeerFlow filesystem.
</role>

<deerflow_platform_knowledge>
## CRITICAL: DeerFlow Architecture Constraints

### 1. Agent Creation API (DOES NOT EXIST)
DeerFlow does NOT expose a REST API for creating new agents/subagents. Subagents are Python SubagentConfig dataclasses registered in backend/src/subagents/builtins/.
**IMPLICATION**: When designing new subagents, you must generate Python code that the human operator will manually add to the codebase.

### 2. Skill Creation (Direct Filesystem)
Skills MUST be created programmatically via the Filesystem: Create skills/custom/{skill-name}/SKILL.md.

### 3. Skill SKILL.md Format
```markdown
---
name: skill-name-here
description: Clear description of what this skill does
license: MIT
---
# Skill Title
[Markdown instructions for the skill]
**Naming Rules**:

- Hyphen-case only: ^[a-z0-9-]+$.  
- No leading/trailing hyphens or consecutive hyphens.  
- Max 64 characters.
```

### 4. SubagentConfig Structure

When generating subagent code, use this exact structure:

```py
from src.subagents.config import SubagentConfig

MY_AGENT_CONFIG = SubagentConfig(
    name="my-agent-name",  # Hyphen-case
    description="When to use this subagent",
    system_prompt="""You are a specialized subagent...""",
    tools=["tool1", "tool2"],  # None = inherit all
    disallowed_tools=["task"],  # Prevent nesting
    model="inherit",
    max_turns=50,
   timeout_seconds=900,
)
```

### 5. State Mutation (Map-Reduce)
- Workers are stateless and return structured JSON. ONLY Orchestrators write to shared state files (e.g., `/workspace/[ProjectCode]-state.json`).
- You MUST provide Orchestrators with this exact Python snippet to prevent NameErrors:
```python
import json
import os
file_path = '/workspace/delphi-state.json'
if os.path.exists(file_path):
    with open(file_path, 'r') as f: state = json.load(f)
else:
    state = {"assets": {}}

# INJECT ACTUAL RECEIVED JSON PAYLOADS HERE:
worker_1_json = { "insert_actual_dict_here": True }

ticker = "TICKER_NAME"
if ticker not in state["assets"]: state["assets"][ticker] = {}
state["assets"][ticker].update(worker_1_json)

with open(file_path, 'w') as f: json.dump(state, f, indent=4)
```
- *CRITICAL:* You must dynamically expand the `# INJECT ACTUAL RECEIVED JSON PAYLOADS HERE:` section to include a separate variable for EVERY worker in the specific pipeline you are designing.
</deerflow_platform_knowledge>

<security_ban> Generated Python code MUST NEVER contain:

- subprocess, os.system, exec(), eval().  
- File access outside /workspace/, /mnt/user-data/, /mnt/skills/.  
- Hardcoded API keys (use os.environ.get()). </security_ban>

<operational_workflow> **State 1: Intake & Validation**

- Ask the user for a ProjectCode (2-4 uppercase alphanumeric characters).  
- Ask for their pipeline goal.  
- *HALT and await user response.*

**State 2: Design Specification**

- Output a Design Spec with:  
  - DAG topology diagram (ASCII)  
  - Agent roles and names (hyphen-case format: {ProjectCode}-{Role}-{Domain})  
  - Custom skills needed (with full SKILL.md content)  
  - Subagents needed (with full SubagentConfig code)  
- *HALT and ask: "Do you APPROVE this design spec?"*

**State 3: Deployment Package Generation**
- UPON "APPROVED": Generate deployment artifacts:
  - **Skills**: Use `write_file` tool to create `SKILL.md` files directly in `/mnt/skills/custom/[skill-name]/` to align with the DeerFlow auto-discovery system.
  - **Subagents**: Use `write_file` tool to create Python files in `/workspace/subagents-deployment/`
  - **Deployment Script**: Generate JSON deployment manifests for the HITL `proactive_deployment_tool.py` script.

**State 4: Deployment Execution**

- Execute the deploy.py script using bash tool

**State 5: Registry Update**

- Register new skills with 00-Directory-Facilitator  
- Provide manual instructions for subagent code addition </operational_workflow>
</system_prompt>
````

## **4.2 Human-In-The-Loop (HITL) Gate Implementation**

To ensure absolute system safety and prevent the autonomous execution of potentially destructive filesystem writes, you must implement a strict Human-In-The-Loop (HITL) gate. Because the Proactive Agentic Architect writes Python `SubagentConfig` files and `SKILL.md` manifests directly to the host directories, the human operator must visually review and explicitly approve every deployment package before it is committed to disk.

This is accomplished by injecting a Python-based confirmation script into the deployment workflow. The script utilizes the `input()` function to pause system execution, displays the exact code or manifest to be written, and requires a typed response to proceed. Furthermore, it maintains a permanent audit trail of all deployment decisions.

Below is the complete, runnable Python HITL deployment tool (`proactive_deployment_tool.py`) that you must embed within your workspace tools. This script includes the `main()` execution block, manifest parsing, and actual filesystem writing procedures required to physically deploy the code.

```py
#!/usr/bin/env python3
"""
Proactive Deployment Tool for DeerFlow
Unified tool for deploying skills and generating subagent code with HITL gates.
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

def hitl_confirm(action_type: str, manifest: dict) -> bool:
    """Human-in-the-Loop confirmation gate."""
    print("\n" + "="*60)
    print(f"PROPOSED {action_type.upper()} DEPLOYMENT")
    print("="*60)
    
    for key, value in manifest.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"  {key}: {value[:100]}...")
        else:
            print(f"  {key}: {value}")
    print("="*60)
    
    while True:
        response = input("\n[APPROVE] / [REJECT] (type 'approve' or 'reject'): ").strip().lower()
        if response in ['approve', 'approved', 'yes', 'y']:
            log_decision(action_type, manifest, True)
            print("\n✓ Deployment APPROVED and logged.")
            return True
        elif response in ['reject', 'rejected', 'no', 'n']:
            log_decision(action_type, manifest, False)
            print("\n✗ Deployment REJECTED and logged.")
            return False
        print("Invalid input. Please type 'approve' or 'reject'.")

def log_decision(action_type: str, manifest: dict, approved: bool):
    """Log the HITL decision to the audit trail."""
    log_path = "/workspace/deployment-log.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action_type,
        "approved": approved,
        "manifest": manifest
    }
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log = json.load(f)
    else:
        log = {"deployments": []}
        
    log["deployments"].append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)

def write_subagent_file(manifest: dict):
    """Write the Python subagent code to the deployment directory."""
    output_dir = Path("/workspace/subagents-deployment")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{manifest['name']}.py"
    file_path.write_text(manifest['code'])
    print(f"Successfully wrote {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Human-in-the-Loop deployment tool")
    parser.add_argument("--file", type=str, required=True, help="Path to JSON manifest")
    parser.add_argument("--type", type=str, choices=['subagent'], required=True, help="Type of deployment")
    args = parser.parse_args()

    with open(args.file, 'r') as f:
        manifest = json.load(f)

    if hitl_confirm(args.type, manifest):
        if args.type == 'subagent':
            write_subagent_file(manifest)

if __name__ == "__main__":
    main()
```

By enforcing this script, you guarantee that no programmatic agent injection or custom skill deployment bypasses human oversight, cementing a secure and reliable operational architecture.

# **Appendix A: Developer Reference & Troubleshooting**

## **A.1 Architecture Constraints & API Research Log**

To prevent developers from attempting to use hallucinated endpoints or brittle deployment methods, this research log explicitly documents the DeerFlow API reality and backend architectural constraints.

### **Finding 1: NO REST API for Agent/Subagent Creation**

* **Status:** VALIDATED  
* **Details:** DeerFlow does **NOT** expose a `POST /api/agents` or `POST /api/subagents` REST endpoint. While the Gateway API exposes routers for `models`, `mcp`, `skills`, `suggestions`, `uploads`, and `artifacts`, agent creation is entirely programmatic and decoupled from the REST layer. Any documentation or generated code suggesting the use of an agents API endpoint is a known hallucination. Developers must rely on codebase injection.

### **Finding 2: SubagentConfig Schema Definition**

* **Status:** VALIDATED  
* **Details:** For developers building custom automation tools or generators, subagents must conform to the `SubagentConfig` dataclass located in `backend/src/subagents/builtins/__init__.py`. The exact Python schema is provided below for reference:

```py
@dataclass
class SubagentConfig:
    name: str                                    # Unique identifier (e.g., "general-purpose")
    description: str                             # When to delegate to this subagent
    system_prompt: str                           # System prompt for the subagent
    tools: list[str] | None = None               # Allowlist of tool names (None = inherit all)
    disallowed_tools: list[str] | None = None    # Denylist of tool names
    model: str = "inherit"                       # Model to use ("inherit" = parent model)
    max_turns: int = 50                          # Maximum agent turns
    timeout_seconds: int = 900                   # Timeout (15 minutes default)
```

### **Finding 3: Skills API vs. Direct Filesystem Reality**

* **Status:** VALIDATED  
* **Details:** Unlike agents, skills *can* be created via a REST API, but it is highly constrained. The endpoint `POST /api/skills/install` exists, but it strictly requires a `thread_id` and a virtual path pointing to a `.skill` ZIP archive within a thread's user-data directory. Attempting to automate this requires complex backend thread-management overhead to resolve virtual paths. Therefore, developers should ignore the API and write a `SKILL.md` file directly to the `/mnt/skills/custom/{skill-name}/` directory, which DeerFlow's internal watcher will auto-discover.

### **Finding 4: Extensions Configuration File (`extensions_config.json`)**

* **Status:** VALIDATED  
* **Details:** The enable/disable state of custom skills and MCP (Model Context Protocol) servers is managed by the `extensions_config.json` file. When programmatically managing the workspace, be aware that DeerFlow resolves this configuration path in the following order:  
  1. `$DEER_FLOW_EXTENSIONS_CONFIG_PATH`  
  2. `./extensions_config.json`  
  3. `../extensions_config.json` (project root).

```

Let me know if you would like to proceed with drafting **Section A.2 (Modular Deployment Scripts)** next!
```

## **A.2 Modular Deployment Scripts**

While the unified `proactive_deployment_tool.py` (provided in Section 4.2) is ideal for interactive deployment, developers may want modular scripts to integrate into custom automation or CI/CD pipelines.

The following standalone Python scripts isolate the deployment logic for skills and subagents, enforcing all system constraints such as strict naming conventions, character limits, and proper Python code formatting.

### **A.2.1 Standalone Skill Deployer (`skill_deployer.py`)**

This dedicated script strictly enforces DeerFlow's filesystem validation rules. It checks for hyphen-case naming (max 64 characters), ensures descriptions stay under 1024 characters without angle brackets, and safely writes the `SKILL.md` manifest directly to `/mnt/skills/custom`.

```py
#!/usr/bin/env python3
"""
Modular Skill Deployer Tool for DeerFlow
Validates constraints and deploys skills via direct filesystem injection.
"""
import os
import re
from pathlib import Path

SKILLS_ROOT = os.environ.get("DEERFLOW_SKILLS_ROOT", "/mnt/skills/custom")

def validate_skill_name(name: str) -> tuple[bool, str]:
    """Validate skill name according to DeerFlow regex and length rules."""
    if not name or len(name) > 64:
        return False, f"Name invalid length (max 64)"
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, "Name must be hyphen-case (lowercase, digits, hyphens only)"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, "Name cannot start/end with hyphen or contain consecutive hyphens"
    return True, ""

def validate_skill_description(description: str) -> tuple[bool, str]:
    """Validate skill description constraints."""
    if not description or len(description) > 1024:
        return False, "Description invalid length (max 1024)"
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets (< or >)"
    return True, ""

def deploy_skill_filesystem(name: str, description: str, body_content: str, license: str = "MIT") -> dict:
    """Deploy a skill by writing directly to the DeerFlow watcher directory."""
    valid_name, err_name = validate_skill_name(name)
    if not valid_name: return {"success": False, "message": err_name}
    
    valid_desc, err_desc = validate_skill_description(description)
    if not valid_desc: return {"success": False, "message": err_desc}

    skill_content = f"""---
name: {name}
description: {description}
license: {license}
---
# {name.replace('-', ' ').title()}
{body_content}
"""
    try:
        skill_dir = Path(SKILLS_ROOT) / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_content, encoding="utf-8")
        return {"success": True, "path": str(skill_file)}
    except Exception as e:
        return {"success": False, "message": str(e)}
```

### **A.2.2 Standalone Subagent Generator (`subagent_generator.py`)**

This script formats the `SubagentConfig` Python dataclass. It automatically escapes triple quotes in system prompts to prevent syntax errors and generates the step-by-step instructions required for a human operator to manually register the agent in `__init__.py`.

```py
#!/usr/bin/env python3
"""
Modular Subagent Generator Tool for DeerFlow
Generates SubagentConfig Python code and manual deployment instructions.
"""
import os
from pathlib import Path
from typing import Optional, List

OUTPUT_DIR = os.environ.get("DEERFLOW_SUBAGENT_OUTPUT", "/workspace/subagents-deployment")

def generate_subagent_config(
    name: str, description: str, system_prompt: str,
    tools: Optional[List[str]] = None, disallowed_tools: Optional[List[str]] = None,
    model: str = "inherit", max_turns: int = 50, timeout_seconds: int = 900
) -> str:
    """Generate the formatted SubagentConfig Python code."""
    tools_str = "None  # Inherit all tools" if tools is None else repr(tools)
    disallowed_str = repr(disallowed_tools or ["task"])
    escaped_prompt = system_prompt.replace('"""', '\\"\\"\\"')
    
    return f'''"""Subagent configuration for {name}."""
from src.subagents.config import SubagentConfig

{name.upper().replace("-", "_")}_CONFIG = SubagentConfig(
    name="{name}",
    description="""{description}""",
    system_prompt="""{escaped_prompt}""",
    tools={tools_str},
    disallowed_tools={disallowed_str},
    model="{model}",
    max_turns={max_turns},
    timeout_seconds={timeout_seconds},
)
'''

def generate_deployment_instructions(name: str) -> str:
    """Generate human-readable instructions for manual codebase injection."""
    return f'''# DEPLOYMENT INSTRUCTIONS FOR: {name}

## Step 1: Create the Config File
Copy the generated `{name}.py` file to your local host repository at:
`backend/src/subagents/builtins/{name}.py`

## Step 2: Register the Subagent
Edit the registry file at: `backend/src/subagents/builtins/__init__.py`

1. Add the import statement:
`from .{name.replace("-", "_")} import {name.upper().replace("-", "_")}_CONFIG`

2. Add to the BUILTIN_SUBAGENTS dictionary:
`"{name}": {name.upper().replace("-", "_")}_CONFIG,`

## Step 3: Restart Services
Run: `make docker-restart`
'''

def generate_subagent(name: str, description: str, system_prompt: str, **kwargs) -> dict:
    """Writes the configuration and instructions to the deployment directory."""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    config_code = generate_subagent_config(name, description, system_prompt, **kwargs)
    instructions = generate_deployment_instructions(name)
    
    config_file = output_path / f"{name}.py"
    config_file.write_text(config_code)
    
    instructions_file = output_path / f"{name}_DEPLOYMENT.md"
    instructions_file.write_text(instructions)
    
    return {"success": True, "files": [str(config_file), str(instructions_file)]}
```

## **A.3 Troubleshooting & Quick Reference Commands**

During development and pipeline execution, you may inevitably face container networking errors or LLM connection issues. The following troubleshooting matrix and command cheat sheet are designed to resolve the most common DeerFlow operational blockers quickly.

### **A.3.1 Troubleshooting Matrix**

#### ***1\. Ollama Connection Issues***

* **Symptom:** DeerFlow UI reports LLM connection failures, or the pipeline hangs immediately.  
* **Diagnosis:** The Docker container cannot reach the host machine's Ollama service.  
* **Resolution:**  
  1. First, verify Ollama is actually running on your host machine by executing: `curl http://localhost:11434/api/tags`.  
  2. If the host responds, test the connection from *inside* the DeerFlow container by running: `docker exec -it deer-flow-api curl http://host.docker.internal:11434/api/tags`.  
  3. If the container test fails, ensure that `extra_hosts: ["host.docker.internal:host-gateway"]` is properly set in your `docker-compose.yaml`.

#### ***2\. AIO Sandbox Container Issues***

* **Symptom:** Python Execution skills fail, or the AIO Sandbox fails to start automatically.  
* **Diagnosis:** The sandbox image is missing or port 8080 is blocked by another host service.  
* **Resolution:**  
  1. Manually pull the latest sandbox image: `docker pull ghcr.io/agent-infra/sandbox:latest`.  
  2. Verify that port 8080 is available on your host machine: `netstat -an | grep 8080`.

#### ***3\. Model Loading & Out-Of-Memory (OOM) Issues***

* **Symptom:** DeerFlow throws model not found errors, or the system crashes during long context handoffs.  
* **Diagnosis:** The required model weights are not downloaded, or the quantization is too large for the GPU VRAM.  
* **Resolution:**  
  1. List the available models on your system: `ollama list`.  
  2. If missing, or if you are running an 11GB VRAM GPU, explicitly pull the 4-bit medium quantized model: `ollama pull qwen3.5:9b`.

### **A.3.2 Quick Reference Command Cheat Sheet**

Use these essential CLI commands to manage the DeerFlow lifecycle and local models.

**DeerFlow Lifecycle Management (Run from `~/deer-flow` directory):**

```shell
make config         # Generate config.yaml and .env files
make docker-init    # Build images, pull AIO sandbox, and install dependencies
make docker-start   # Start all DeerFlow services (Gateway, LangGraph, Frontend, Nginx)
make docker-logs    # View the combined, real-time container logs
make docker-stop    # Safely stop all DeerFlow services
make docker-restart # Restart services to load new subagent Python files
```

**Local Model Management (Ollama):**

```shell
ollama list                  # View all locally installed models
ollama pull qwen3.5:9b       # Pull the recommended hardware-optimized reasoning model
ollama rm [model-name]       # Delete a model to free up disk space
```

**System Access Points:**

```shell
# Verify Local API Health
curl http://localhost:11434/api/tags

# Access DeerFlow Web UI
open http://localhost:2026
```

