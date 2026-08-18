import uuid

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app


st.set_page_config(page_title="Real-World Multi-Agent Travel Planner", layout="wide")

st.title("Real-World Multi-Agent Travel Planner")

with st.sidebar:
    st.subheader("Session")
    user_id = st.text_input("User ID", value="demo_user")
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
    if st.button("New Thread"):
        st.session_state.thread_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        st.session_state.pop("waiting_for_approval", None)
        st.session_state.pop("latest_result", None)

    st.caption(f"Thread: {st.session_state.thread_id}")


query = st.text_area(
    "Travel request",
    placeholder="Plan a 7-day Japan trip under Rs. 2 lakh. I prefer budget hotels and no overnight flights.",
    height=110,
)

config = {"configurable": {"thread_id": st.session_state.thread_id}}


if st.button("Create Draft Plan", type="primary"):
    if not query.strip():
        st.warning("Enter a travel request first.")
    else:
        with st.spinner("Agents are planning..."):
            result = app.invoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "user_id": user_id,
                    "user_query": query,
                    "flight_results": "",
                    "hotel_results": "",
                    "weather_results": "",
                    "budget_results": "",
                    "itinerary": "",
                    "final_response": "",
                    "llm_calls": 0,
                },
                config=config,
            )

        st.session_state.latest_result = result
        st.session_state.waiting_for_approval = "__interrupt__" in result


result = st.session_state.get("latest_result")

if result:
    st.subheader("Supervisor Plan")
    st.write(result.get("supervisor_reasoning", ""))
    st.write("Selected agents:", result.get("selected_agents", []))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Flight")
        st.markdown(result.get("flight_results", ""))
        st.subheader("Weather")
        st.markdown(result.get("weather_results", ""))
    with col2:
        st.subheader("Hotels")
        st.markdown(result.get("hotel_results", ""))
        st.subheader("Budget")
        st.markdown(result.get("budget_results", ""))

    st.subheader("Draft Itinerary")
    if "__interrupt__" in result:
        draft = result["__interrupt__"][0].value.get("draft_itinerary", "")
    else:
        draft = result.get("itinerary", "")
    st.markdown(draft)


if st.session_state.get("waiting_for_approval"):
    st.divider()
    st.subheader("Human Approval")

    approved = st.radio("Approve this draft?", ["Yes", "No, revise it"], horizontal=True)
    feedback = st.text_area("Feedback", disabled=approved == "Yes")

    if st.button("Submit Approval"):
        with st.spinner("Creating final response..."):
            final_result = app.invoke(
                Command(
                    resume={
                        "approved": approved == "Yes",
                        "feedback": feedback,
                    }
                ),
                config=config,
            )
        st.session_state.latest_result = final_result
        st.session_state.waiting_for_approval = False
        st.rerun()


final_result = st.session_state.get("latest_result")
if final_result and final_result.get("final_response"):
    st.divider()
    st.subheader("Final Travel Plan")
    st.markdown(final_result["final_response"])

