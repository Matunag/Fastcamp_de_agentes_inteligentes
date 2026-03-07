from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json


stay_agent = Agent(
    name="stay_agent",
    model="gemini-2.5-flash",
    description="Suggests the best accommodation options for the user's destination.",
    instruction=(
        "Given a destination, dates, and budget, suggest 2-3 accommodation options for that location. "
        "For each option, provide the name, type (hotel, hostel, airbnb, etc.), price estimate per night, location/neighborhood, and main highlights. "
        "Respond in plain English. Keep it concise and well-formatted."
    )
)

session_service = InMemorySessionService()
runner = Runner(
    agent=stay_agent,
    app_name="stay_app",
    session_service=session_service
)
USER_ID = "user_stays"
SESSION_ID = "session_stays"

async def execute(request):
    await session_service.create_session(
        app_name="stay_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    prompt = (
        f"User is traveling to {request['destination']} from {request['start_date']} to {request['end_date']}, "
        f"with a budget of {request['budget']}. Suggest 2-3 accommodation options, each with name, type, price estimate per night, location/neighborhood, and main highlights. "
        f"Respond in JSON format using the key 'stays' with a list of stay objects."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            response_text = event.content.parts[0].text
            try:
                parsed = json.loads(response_text)
                if "stays" in parsed and isinstance(parsed["stays"], list):
                    return {"stays": parsed["stays"]}
                else:
                    print("'stays' key missing or not a list in response JSON")
                    return {"stays": response_text}  # fallback to raw text
            except json.JSONDecodeError as e:
                print("JSON parsing failed:", e)
                print("Response content:", response_text)
                return {"stays": response_text}  # fallback to raw text
