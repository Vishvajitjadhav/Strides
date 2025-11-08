import streamlit as st
# from database_connector import check_user_persona_exists, save_user_persona # (Defined later)

def show_persona_setup_form(user_id:1):
    st.header("👋 Tell Us About Your Day")
    st.info("This one-time setup helps Gemini tailor suggestions just for you.")
    
    with st.form(key='persona_form'):
        st.subheader("1. Your Routine & Goals")
        

        routine = st.text_area(
            "Weekly Routine & Work Style:",
            "E.g., I work Mon-Fri, 9-5. I am most productive in the morning, and I prefer 90-minute deep work blocks.",
            height=100
        )

        goals = st.text_area(
            "Current Goals:",
            "E.g., Prepare for Azure AZ-104 cert; Maintain consistent fitness; Learn Python automation.",
            height=100
        )

        productivity_style = st.text_area(
            "Productivity Style:",
            "E.g., I am most productive in the morning, I prefer working in 90-minute blocks, Meetings drain my energy.",
            height=75
        )

        st.subheader("2. Your Interests")
        interests = st.text_area(
            "Hobbies & Interests:",
            "E.g., AI/ML, web development, reading personal finance, playing guitar.",
            height=75
        )
        
        submit_button = st.form_submit_button(label='Save My Persona')

    if submit_button:
        # Step 2 will handle saving this data
        st.session_state.persona_data = {
            "routine": routine,
            "goals": goals,
            "productivity_style":productivity_style,
            "interests": interests
        }
        st.session_state.persona_submitted=True
        st.success("Persona saved! Gemini is now ready to give personalized insights.")
        st.rerun()


""" 

-I work in night shift from 5.30 PM to 2.30 AM from monday to friday
- saturday and sunday is off.
- I prefer 90 min break 


- Master AI and ML skill
- Weight gain 
- Read Book 

I am most productive in the evenings ,
I prefer working in 90-minute blocks, 
Meetings drain my energy.

- Reading Personal self help. book 
- Exploring New places and Meet new peoples

"""
