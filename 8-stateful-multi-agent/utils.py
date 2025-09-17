# utils.py

from datetime import datetime
from google.genai import types

# It's good practice to keep the Colors class if you use it for formatting
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    # ... (rest of the color codes) ...
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLUE = "\033[44m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    YELLOW = "\033[33m"
    BLACK = "\033[30m"

# 👇 FIX: All these functions must be 'async def' and use 'await' internally
async def update_interaction_history(
    session_service, app_name, user_id, session_id, entry
):
    """Add an entry to the interaction history in state."""
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        interaction_history = session.state.get("interaction_history", [])
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        interaction_history.append(entry)
        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=updated_state,
        )
    except Exception as e:
        print(f"Error updating interaction history: {e}")

async def add_user_query_to_history(
    session_service, app_name, user_id, session_id, query
):
    """Add a user query to the interaction history."""
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {"action": "user_query", "query": query},
    )

async def add_agent_response_to_history(
    session_service, app_name, user_id, session_id, agent_name, response
):
    """Add an agent response to the interaction history."""
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {"action": "agent_response", "agent": agent_name, "response": response},
    )

async def display_state(
    session_service, app_name, user_id, session_id, label="Current State"
):
    """Display the current session state in a formatted way."""
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        # Format the output with clear sections
        print(f"\n{'-' * 10} {label} {'-' * 10}")

        # Handle the user name
        user_name = session.state.get("user_name", "Unknown")
        print(f"👤 User: {user_name}")

        # Handle purchased courses
        purchased_courses = session.state.get("purchased_courses", [])
        if purchased_courses and any(purchased_courses):
            print("📚 Courses:")
            for course in purchased_courses:
                if isinstance(course, dict):
                    course_id = course.get("id", "Unknown")
                    purchase_date = course.get("purchase_date", "Unknown date")
                    print(f"  - {course_id} (purchased on {purchase_date})")
                elif course:  # Handle simple string format
                    print(f"  - {course}")
        else:
            print("📚 Courses: None")

        # Handle interaction history in a more readable way
        interaction_history = session.state.get("interaction_history", [])
        if interaction_history:
            print("📝 Interaction History:")
            for idx, interaction in enumerate(interaction_history, 1):
                if isinstance(interaction, dict):
                    action = interaction.get("action", "interaction")
                    timestamp = interaction.get("timestamp", "unknown time")

                    if action == "user_query":
                        query = interaction.get("query", "")
                        print(f'  {idx}. User query at {timestamp}: "{query}"')
                    elif action == "agent_response":
                        agent = interaction.get("agent", "unknown")
                        response = interaction.get("response", "")
                        # Truncate long responses for display
                        if len(response) > 70:
                            response = response[:67] + "..."
                        print(f'  {idx}. {agent} response at {timestamp}: "{response}"')
                else:
                    print(f"  {idx}. {interaction}")
        else:
            print("📝 Interaction History: None")

        print("-" * (22 + len(label)))
    except Exception as e:
        print(f"Error displaying state: {e}")

async def process_agent_response(event):
    """Process and display agent response events."""
    # This function should print intermediate text parts if they exist
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                # You can uncomment the next line for more verbose, step-by-step output
                # print(f"  Text Chunk: '{part.text.strip()}'")
                pass

    final_response = None
    # Check if this is the final event in the stream
    if event.is_final_response():
        # Check if the final event contains text content to display
        if (
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
            and event.content.parts[0].text
        ):
            # Extract the final response text
            final_response = event.content.parts[0].text.strip()
            
            # 👇 THIS IS THE MISSING PART: Print the formatted final response
            print(
                f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╔══ AGENT RESPONSE ═════════════════════════════════════════{Colors.RESET}"
            )
            print(f"{Colors.CYAN}{Colors.BOLD}{final_response}{Colors.RESET}")
            print(
                f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╚═════════════════════════════════════════════════════════════{Colors.RESET}\n"
            )
        else:
            # Handle cases where the agent finishes without a text response
            print(
                f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}==> Agent finished without a text response.{Colors.RESET}\n"
            )

    return final_response


async def call_agent_async(runner, user_id, session_id, query):
    """Call the agent asynchronously with the user's query."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Running Query: {query} ---{Colors.RESET}"
    )
    final_response_text = None
    agent_name = None

    # 👇 FIX: Calls to async functions need 'await'
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State BEFORE processing",
    )
    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            if event.author:
                agent_name = event.author
            response = await process_agent_response(event) # This function doesn't need to be displayed fully here
            if response:
                final_response_text = response
    except Exception as e:
        print(f"{Colors.BG_RED}{Colors.WHITE}ERROR during agent run: {e}{Colors.RESET}")

    if final_response_text and agent_name:
        await add_agent_response_to_history(
            runner.session_service,
            runner.app_name,
            user_id,
            session_id,
            agent_name,
            final_response_text,
        )
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State AFTER processing",
    )
    print(f"{Colors.YELLOW}{'-' * 30}{Colors.RESET}")
    return final_response_text