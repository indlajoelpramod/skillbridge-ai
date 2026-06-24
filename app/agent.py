# ruff: noqa
import logging
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool, McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types

from google.adk.workflow import Workflow, node, START, Edge
from google.adk.events import RequestInput, Event
from app.config import config

logger = logging.getLogger("skillbridge_ai")

# ---------------------------------------------------------------------------
# MCP Toolset Configuration
# ---------------------------------------------------------------------------

mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "app.mcp_server"],
        )
    )
)

# ---------------------------------------------------------------------------
# Specialized Agents
# ---------------------------------------------------------------------------

career_advisor = Agent(
    name="career_advisor",
    model=Gemini(model=config.model),
    instruction="""You are an expert Career Advisor.
    - Analyze the user's current skills, academic background, interests, and career goals.
    - Identify gaps for key industry roles (e.g. Software Developer, Data Analyst, AI Engineer, Cybersecurity Specialist).
    - Recommend certifications, courses, and optimizations for their resume or LinkedIn profile.
    - Provide professional, motivating, and highly personalized advice.
    - Use the MCP tools to fetch actual required skills, certifications, and job market trends.""",
    tools=[mcp_toolset]
)

study_planner = Agent(
    name="study_planner",
    model=Gemini(model=config.model),
    instruction="""You are a structured Learning & Study Planner.
    - Design personalized learning roadmaps, schedules, and practice tasks.
    - Use the student's target timeline and available study hours per week (stored in the session/state) to make the schedule highly realistic.
    - Provide week-by-week learning milestones and resources.
    - Use the MCP tools to generate practice exercises based on topics.""",
    tools=[mcp_toolset]
)

# ---------------------------------------------------------------------------
# Orchestrator Agent
# ---------------------------------------------------------------------------

orchestrator = Agent(
    name="orchestrator",
    model=Gemini(model=config.model),
    instruction="""You are SkillBridge AI, a personalized career and learning mentor.
    Your job is to analyze user queries and delegate tasks to your specialized sub-agents:
    - Delegate career analysis, skill gap identification, and resume review to the career_advisor.
    - Delegate study roadmap generation, schedules, and curriculum planning to the study_planner.
    
    If the user has general inquiries or is just starting, ask them to outline their current skills, interests, and target roles.
    Coordinate between sub-agents to deliver a comprehensive career plan.""",
    tools=[
        AgentTool(agent=career_advisor),
        AgentTool(agent=study_planner)
    ]
)

# ---------------------------------------------------------------------------
# Workflow Nodes
# ---------------------------------------------------------------------------

@node
async def security_checkpoint(ctx, node_input):
    """Workflow security checkpoint for scrubbing PII, checking prompt injection, and enforcing career-only domain rules."""
    import json
    import re
    
    input_str = ""
    if isinstance(node_input, types.Content):
        for part in node_input.parts or []:
            if part.text:
                input_str += part.text
    else:
        input_str = str(node_input)

    # 1. Prompt Injection Detection
    injection_keywords = [
        "ignore previous instructions", 
        "system prompt", 
        "override instructions", 
        "bypass security",
        "dan mode",
        "jailbreak"
    ]
    if any(kw in input_str.lower() for kw in injection_keywords):
        audit_log = {
            "event": "security_violation",
            "type": "prompt_injection",
            "severity": "CRITICAL",
            "input_preview": input_str[:100],
            "action": "BLOCK"
        }
        logger.error(json.dumps(audit_log))
        print(f"AUDIT LOG: {json.dumps(audit_log)}")
        return Event(route="SECURITY_EVENT")

    # 2. Domain-Specific Rule: Filter Out Inappropriate / Off-Topic (Politics, Gossip, Gaming) Queries
    off_topic_patterns = [
        r"\b(politics|politician|democrat|republican|election|candidate|president)\b",
        r"\b(gossip|celebrity|rumor|tabloid)\b",
        r"\b(cheat code|video game hack|exploit)\b"
    ]
    is_off_topic = False
    for pattern in off_topic_patterns:
        if re.search(pattern, input_str.lower()):
            is_off_topic = True
            break
            
    if is_off_topic:
        audit_log = {
            "event": "security_violation",
            "type": "domain_policy_off_topic",
            "severity": "WARNING",
            "input_preview": input_str[:100],
            "action": "BLOCK"
        }
        logger.warning(json.dumps(audit_log))
        print(f"AUDIT LOG: {json.dumps(audit_log)}")
        return Event(route="SECURITY_EVENT")

    # 3. PII Scrubbing (Simple regex scrubbing for phone & emails in resume content)
    cleaned_str = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', input_str)
    cleaned_str = re.sub(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', '[PHONE_REDACTED]', cleaned_str)
    
    pii_scrubbed = cleaned_str != input_str
    if pii_scrubbed:
        # Re-pack into Content if input was Content
        if isinstance(node_input, types.Content):
            node_input.parts = [types.Part(text=cleaned_str)]
        else:
            node_input = cleaned_str

    # 4. Success Case: Audit Log
    audit_log = {
        "event": "security_check_passed",
        "severity": "INFO",
        "pii_scrubbed": pii_scrubbed,
        "input_preview": cleaned_str[:100]
    }
    logger.info(json.dumps(audit_log))
    print(f"AUDIT LOG: {json.dumps(audit_log)}")

    # Save details to state for security auditing in audit log
    ctx.state["last_security_check"] = {
        "status": "PASS",
        "pii_scrubbed": pii_scrubbed
    }
    
    return Event(output=node_input, route="clean")

@node
async def security_error_node(ctx, node_input):
    """Handles prompt injection violations."""
    ctx.state["last_security_check"] = {
        "status": "FAIL",
        "reason": "Prompt Injection Detected"
    }
    return "Security Check Failed: Prompt injection attempt detected. The incident has been logged."

@node(rerun_on_resume=True)
async def orchestrator_node(ctx, node_input):
    """Executes the orchestrator agent and processes delegation."""
    if ctx.state.get("roadmap_requested"):
        return "Resuming roadmap generation..."

    # Convert node_input to types.Content if it isn't
    if not isinstance(node_input, types.Content):
        content_input = types.Content(role="user", parts=[types.Part(text=str(node_input))])
    else:
        content_input = node_input

    # Run the orchestrator agent
    agent_response = await ctx.run_node(orchestrator, content_input)
    
    # Extract text from response to inspect if they want a roadmap
    response_text = ""
    if agent_response and hasattr(agent_response, "content") and agent_response.content:
        for part in agent_response.content.parts or []:
            if part.text:
                response_text += part.text

    # Simple keyword check to trigger roadmap HITL flow
    input_text = ""
    for part in content_input.parts or []:
        if part.text:
            input_text += part.text

    if any(kw in input_text.lower() for kw in ["roadmap", "schedule", "study plan", "curriculum"]):
        ctx.state["roadmap_requested"] = True

    return agent_response

@node(rerun_on_resume=True)
async def hitl_node(ctx, node_input):
    """Interrupts the flow to ask the user for weekly study hour commitment when generating a roadmap."""
    import re
    if ctx.state.get("roadmap_requested") and not ctx.state.get("weekly_hours"):
        # Check if the user's resume input is available in the resume inputs dict
        for key, val in ctx.resume_inputs.items():
            if isinstance(val, dict) and "result" in val:
                val = val["result"]
            
            if val is not None:
                try:
                    # Robust digit extraction
                    digits = re.findall(r'\d+', str(val))
                    if digits:
                        weekly_hours = int(digits[0])
                    else:
                        weekly_hours = int(str(val).strip())
                        
                    ctx.state["weekly_hours"] = weekly_hours
                    ctx.state["roadmap_requested"] = False
                    
                    # Filter out HITL request input call and response events from session events
                    # to avoid ValueError due to framework role=None mapping issues.
                    if hasattr(ctx, "session") and ctx.session and ctx.session.events:
                        ctx.session.events = [
                            e for e in ctx.session.events
                            if not (e.content and e.content.parts and any(
                                (p.function_call and p.function_call.name == 'adk_request_input') or
                                (p.function_response and p.function_response.name == 'adk_request_input')
                                for p in e.content.parts
                            ))
                        ]
                    
                    # Now delegate to the study planner to build the actual roadmap
                    plan_query = types.Content(role="user", parts=[types.Part(text=f"User has confirmed they can commit {weekly_hours} hours per week. Generate their custom study roadmap.")])
                    planner_response = await ctx.run_node(study_planner, plan_query)
                    return planner_response
                except ValueError:
                    pass

        # If not provided, request the weekly hour input
        return RequestInput(
            message="To create a personalized learning roadmap, how many hours per week can you dedicate to study? (e.g. 10)"
        )
    return node_input

# ---------------------------------------------------------------------------
# Workflow and App Instantiation
# ---------------------------------------------------------------------------

wf = Workflow(
    name="skillbridge_wf",
    edges=[
        Edge(from_node=START, to_node=security_checkpoint),
        Edge(from_node=security_checkpoint, to_node=security_error_node, route="SECURITY_EVENT"),
        Edge(from_node=security_checkpoint, to_node=orchestrator_node, route="clean"),
        Edge(from_node=orchestrator_node, to_node=hitl_node),
    ]
)

root_agent = wf

app = App(
    root_agent=root_agent,
    name="app",
)
