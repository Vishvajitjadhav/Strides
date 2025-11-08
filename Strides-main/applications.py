from google import genai 
from google.genai import types
from dotenv import load_dotenv
import os
import requests
import datetime
from calander_connector import get_calendar_service
import streamlit as st
import datetime


load_dotenv()
gemini_api_key = os.getenv("GOOGLE_API_KEY")


client = genai.Client(api_key=gemini_api_key)


def prompt_for_quote():
    base_prompt = """
    **Goal:** Generate an original "Quote for the Day".

    **Instructions:**
    -   **Length:** The quote must be concise, ideally between 10 and 20 words.
    -   **Theme:** Focus on topics like inspiration, motivation, perseverance, or personal growth.
    -   **Tone:** The quote should have a positive, uplifting, and insightful tone.
    -   **Style:** It must be an original, impactful, and easy-to-understand statement. Do not use famous or existing quotes.
    """

    return base_prompt


def get_random_quotes():
    response=client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt_for_quote()],
    )
    return response.text


def get_weather_info(city: str):
    """
    Fetches weather data for a given city by first getting its coordinates.
    """
    try:
        api_key = os.getenv("openweathermapapi")
        if not api_key:
            return {"error": "OpenWeatherMap API key not set."}

        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()

        geo_data = geo_response.json()
        if not geo_data:
            return {"error": f"Could not find location for city: {city}"}
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()

        return weather_response.json()

    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error: {http_err}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"A network error occurred: {e}"}
    except (IndexError, KeyError):
        return {"error": "Failed to parse location data. The city may be invalid."}
   

def get_weather_report_using_gemini(city:str):
     system_instructions="""
    You are given weather data in JSON format from the OpenWeather API.
    Your job is to convert it into a clear, human-friendly weather update.
    Guidelines:
    1. Always mention the city and country.
    2. Convert temperature from Kelvin to Celsius (°C), rounded to 1 decimal.
    3. Include: current temperature, feels-like temperature, main weather description, humidity, wind speed, and sunrise/sunset times (converted from UNIX timestamp).
    4. Use natural, conversational language.
    5. Based on the current conditions, suggest what the person should carry or wear.
    - If rain/clouds: suggest umbrella/raincoat.
    - If very hot (>30°C): suggest light cotton clothes, sunglasses, stay hydrated.
    - If cold (<15°C): suggest warm clothes, jacket.
    - If windy: suggest windbreaker, secure loose items.
    - If humid: suggest breathable clothes, water bottle.
    6. If any field is missing, gracefully ignore

    """
   
     response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Generate a clear lfriendly weather report with temperatures in °C, humidity, wind, sunrise/sunset for the {city} and practical suggestions on what to wear or carry.",
        config=types.GenerateContentConfig(system_instruction=system_instructions,tools=[get_weather_info])
     )
     return response.text


def format_events_for_streamlit(google_events):
    """
    Transforms Google Calendar API event format into the format
    required by the streamlit-calendar component.
    """
    formatted_events = []
    # ... (Your existing formatting logic) ...
    for event in google_events:
        if 'start' not in event or 'end' not in event:
            continue
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        end_time = event['end'].get('dateTime', event['end'].get('date'))
        formatted_events.append({
            "title": event.get('summary', 'Busy'),
            "start": start_time,
            "end": end_time,
            "id": event.get('id')
        })
    return formatted_events


# 2. CALENDAR FETCHING FUNCTION (Must now call the local formatting function)
def fetch_and_format_calendar_events():
    try:
        service = get_calendar_service()
        
        # Calculate time range (e.g., fetch events from 'now' for the next 20 events)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        google_events = events_result.get("items", [])
        
        return format_events_for_streamlit(google_events) # Calls the function defined above

    except Exception as e:
        st.error(f"Authentication Error: {e}. Please ensure credentials.json and token.json are present and valid.")
        return []

def get_daily_summary(events: list,persona_data):
    """
    Uses Gemini to summarize the day's plan, free time, and suggestions.
    """
    if not events:
        return "Your calendar is clear for the selected period! What an opportunity for extra productivity or relaxation!"

    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date() 

    today_events = []
    for event in events:
        try:
            # Handle both 'dateTime' (with T) and 'date' (without T)
            event_date_str = event['start'].split('T')[0]
            if datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date() == today:
                 today_events.append(event)
        except:
             continue


    event_list_string = "\n".join([
        f"- {e['title']} from {e['start'].split('T')[1][:5]} to {e['end'].split('T')[1][:5]}" 
        for e in today_events if 'T' in e['start'] # Only summarize timed events for scheduling
    ])


    prompt = f"""
    You are a highly efficient personal time management assistant. Your goal is to help me optimize my day for productivity, well-being, and personal growth.

Analyze the following schedule for today ({today.strftime('%A, %B %d')}) and provide a comprehensive summary and plan.

**My Personal Context:**
*   **Weekly Routine:** { st.session_state.persona_data["routine"]}.
*   **Current Goals:** [{ st.session_state.persona_data["goals"]}]
*   **Productivity Style:** [{ st.session_state.persona_data["productivity_style"]}]
*   **Interests:** [{ st.session_state.persona_data["interests"]}]

**Today's Planned Schedule (Events and Times):**
{event_list_string if event_list_string else "No timed events found on the calendar."}

**Your Report Must Include the Following Sections:**

1.  **Day Overview:** Summarize the main focus of the day in one sentence.
2.  **Time Blocking & Free Time:** Estimate the total planned time and identify the largest contiguous block of free time between 9:00 AM and 5:00 PM.
3.  **Productivity Suggestion:** Based on my free time and current goals, suggest ONE productive activity for the largest free block.
4.  **Wellbeing & Recovery Suggestion:** Considering my physical activities, suggest ONE well-being activity (e.g., stretching, a power nap, or a healthy meal) and the best time to fit it in. Explain why this will help with recovery.
5.  **Learning & Growth Suggestion:** Based on my interests and the available free time, recommend ONE learning activity. If possible, provide a link to a relevant YouTube video, article, or resource.
6.  **Weekend/Weekday Contextual Suggestion:** Since today is a {today.strftime('%A')}, suggest one activity that I can do at home/in the office that aligns with my personal interests or helps me prepare for the week ahead.

By providing this additional context, the AI can generate a much more personalized and useful daily plan.

### Tech Stack for a Learning AI Model

To build an AI assistant that learns from past interactions and provides increasingly personalized suggestions, you need to implement a system with long-term memory. Here’s a breakdown of the concepts and a recommended tech stack:

#### Conceptual Architecture

An AI with long-term memory typically works in a few steps[13]:
*   **Fact Extraction:** After each interaction, the system identifies and extracts key pieces of information (facts) about you, such as your preferences, goals, and habits[13].
*   **Vector Storage:** These facts are converted into a numerical format (embeddings) and stored in a specialized database called a vector database. This allows for efficient searching based on meaning and context, not just keywords[13].
*   **Contextual Retrieval:** When you start a new conversation, the system searches the vector database for relevant past facts and provides them to the AI model as context. This enables the AI to "remember" previous conversations and tailor its responses accordingly[17].

#### Recommended Tech Stack

Here is a potential tech stack to build such a system, focusing on open-source tools:

*   **Memory Management Layer: `mem0`**
    This open-source tool is designed to manage both short-term and long-term memory for AI applications[12][13]. It can automatically handle the context from conversations, so you don't have to track it manually. It simplifies the process of sending and receiving messages while maintaining a persistent memory of the user[12].

*   **Vector Database: `Qdrant`**
    Qdrant is a vector database used for storing the "memories" or "facts" extracted from conversations[13]. It's designed for fast and scalable semantic search, which means it can quickly find the most relevant information to provide as context for new interactions[13].

*   **Large Language Model (LLM): `Google Gemini` or other models**
    You would use a powerful LLM like Gemini for the core conversational AI and for the fact-extraction process[21]. You can fine-tune a model or use advanced prompting techniques to teach it how to identify and pull out important information from your conversations[11].

*   **Application Framework: `FastAPI` (Backend) and `React` (Frontend)**
    You can use FastAPI, a modern Python web framework, to build the backend that integrates the LLM, memory layer, and vector database. For the user interface, a framework like React.js would allow you to create a dynamic and responsive chat application.

By combining these technologies, you can create a sophisticated AI assistant that not only manages your daily schedule but also learns and adapts to your needs over time, providing a truly personalized experience.

    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )
        return response.text
   
    except Exception as e:
        return f"Gemini Summarization Error: {e}"
    




