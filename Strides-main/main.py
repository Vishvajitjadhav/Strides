import streamlit as st
from applications import get_random_quotes ,get_weather_report_using_gemini ,fetch_and_format_calendar_events,get_daily_summary
import random 
from streamlit_calendar import calendar
from profile_setup import show_persona_setup_form


if 'generating_summary' not in st.session_state:
    st.session_state['generating_summary'] = False
if 'reset_button_click' not in st.session_state:
   st.session_state.reset_button_click=False

def get_random_image(): 
 image_urls = [
 "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8",
 "https://images.unsplash.com/photo-1500382017468-9049fed747ef",
 "https://images.unsplash.com/photo-1494548162494-384bba4ab999",
 "https://images.unsplash.com/photo-1520038410233-7141be7e6f97",
 "https://images.unsplash.com/photo-1441974231531-c6227db76b6e",
 "https://images.unsplash.com/photo-1503803548695-c2a7b4a5b875?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",

 ]
 return random.choice(image_urls)


def home_page():
    st.title("Your Morning Buddy")
    st.markdown("---")
    st.subheader("A Thought for your Day")
    with st.spinner('Fetching your daily inspirations...'):
     if 'quote' not in st.session_state:
        quote=get_random_quotes()
        st.session_state.quote=quote
    st.info(f"{st.session_state.quote}")
    if 'random_image' not in st.session_state:
       st.session_state.random_image=get_random_image()
    st.image(st.session_state.random_image,caption="A Beautiful Morning to start your day",use_container_width=True)
    st.markdown("---")
    if "persona_submitted" not in st.session_state:
      show_persona_setup_form(1)
      return
    st.info("use the sidebar on the left to get your daily updates")


def weather_page():
   st.header("Get Weather of your city")  
   city=st.text_input("Enter your city name:")
   if st.button("Fetch Information"):
    if city:
        with st.spinner("Fetching your city weather info..."):
          city_weatherInfo_key=get_weather_report_using_gemini(city)
          st.subheader(f"Weather Info:{city_weatherInfo_key}")


def generate_summary_and_rerun():
    """Fetches summary, saves to state, and forces a rerun."""
    with st.spinner("Asking Gemini to analyze your schedule..."): 
        st_events = st.session_state.st_events
        persona_data = st.session_state.persona_data
        
        daily_summary_text = get_daily_summary(st_events, persona_data)
        st.session_state['daily_summary'] = daily_summary_text
        st.rerun() 

def smart_planner():
    st.title("Welcome to Smart Planner 🗓️")
    st.markdown("---")
    

    if st.session_state.get("persona_submitted") is not True:
        st.warning("Please complete your Personal Context setup on the Home page first to enable smart suggestions.")
        return
   

    if "st_events" not in st.session_state:
        with st.spinner('Fetching schedule...'):
            st.session_state.st_events = fetch_and_format_calendar_events()

    if 'daily_summary' not in st.session_state:
        
        if st.session_state.st_events and (st.button("Summarize My Day & Plan Free Time", key="summarize_btn") or st.session_state.reset_button_click):
            generate_summary_and_rerun()
            st.session_state.reset_button_click=False
        elif not st.session_state.st_events:
             st.info("No upcoming events found. Cannot generate a summary.")
    
   
    st.subheader("Google Calendar Events")
            
    calendar_options = {
        "initialView": "timeGridDay",
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "editable": False,
        "height": 650
    }
    

    calendar_result = calendar(
        events=st.session_state.st_events,
        options=calendar_options,
        key="google_calendar"
    )  
            
    
    if 'daily_summary' in st.session_state:
        st.subheader("🤖 Gemini Daily Insight")
        col_insight, col_button = st.columns([0.9, 0.1])
        col_insight.info(st.session_state['daily_summary'])

        if col_button.button('Reset',key="reset_summary",help="generate a new summary immediately."):
           st.session_state.reset_button_click=True
           del st.session_state.daily_summary
       
        
      



st.sidebar.title("Navigations")
st.sidebar.markdown('---')
page_option=st.sidebar.radio("Choose a Page:",("Home","Weather of your City","Smart Planner"))
st.sidebar.markdown('---')

if page_option=="Home":
    home_page()
elif page_option=="Weather of your City":
    weather_page()
elif page_option=="Smart Planner":
    smart_planner()
