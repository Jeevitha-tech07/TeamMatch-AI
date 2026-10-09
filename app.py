"""
app.py
Feedback Bot - Streamlit application.

Two views:
  1. Student View  -> submit anonymous feedback, take active quick polls
  2. Admin View    -> password-protected dashboard with AI-derived insights
                       (sentiment breakdown, top keywords, ratings by category)
                       plus poll creation/results and a CSV export.
"""

import streamlit as st
import pandas as pd

import db
from ai_helpers import analyze_sentiment, extract_keywords

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Campus Feedback Bot", page_icon="💬", layout="wide")
db.init_db()

ADMIN_PASSWORD = "admin123"  # change this before deploying for real use

CATEGORIES = ["Class", "Lab", "Facility"]


def star_rating_input(label):
    return st.slider(label, min_value=1, max_value=5, value=3, format="%d ⭐")


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("💬 Feedback Bot")
view = st.sidebar.radio("Go to", ["Student View", "Admin View"])

# ---------------------------------------------------------------------------
# STUDENT VIEW
# ---------------------------------------------------------------------------
if view == "Student View":
    st.title("🎓 Anonymous Student Feedback")
    st.caption("Your feedback is 100% anonymous — we never store your name, email, or login.")

    tab1, tab2 = st.tabs(["📝 Give Feedback", "📊 Quick Polls"])

    # --- Feedback form ---
    with tab1:
        with st.form("feedback_form", clear_on_submit=True):
            category = st.selectbox("What is this feedback about?", CATEGORIES)
            subject = st.text_input(
                "Course / Lab / Facility name",
                placeholder="e.g. Data Structures, Physics Lab, Library",
            )
            rating = star_rating_input("Overall rating")
            comment = st.text_area(
                "Your comments",
                placeholder="What went well? What could be improved?",
                height=120,
            )
            submitted = st.form_submit_button("Submit Feedback")

            if submitted:
                if not subject.strip():
                    st.warning("Please enter a course/lab/facility name.")
                else:
                    sentiment, score = analyze_sentiment(comment)
                    db.add_feedback(category, subject.strip(), rating, comment.strip(), sentiment, score)
                    st.success("Thanks! Your anonymous feedback has been recorded. ✅")

    # --- Polls ---
    with tab2:
        active_polls = db.get_active_polls()
        if not active_polls:
            st.info("No active polls right now. Check back later!")
        else:
            for poll in active_polls:
                st.subheader(poll["question"])
                options = [poll["option_a"], poll["option_b"]]
                if poll["option_c"]:
                    options.append(poll["option_c"])
                if poll["option_d"]:
                    options.append(poll["option_d"])

                choice = st.radio(
                    "Choose one:", options, key=f"poll_{poll['id']}", label_visibility="collapsed"
                )
                if st.button("Vote", key=f"vote_{poll['id']}"):
                    db.cast_vote(poll["id"], choice)
                    st.success("Vote recorded — thanks!")
                st.divider()

# ---------------------------------------------------------------------------
# ADMIN VIEW
# ---------------------------------------------------------------------------
else:
    st.title("🔒 Admin / Faculty Dashboard")

    if "admin_authed" not in st.session_state:
        st.session_state.admin_authed = False

    if not st.session_state.admin_authed:
        pwd = st.text_input("Enter admin password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()

    feedback = db.get_all_feedback()
    df = pd.DataFrame(feedback)

    tab_insights, tab_feedback, tab_polls = st.tabs(
        ["📈 Insights", "🗂️ All Feedback", "📊 Manage Polls"]
    )

    # --- Insights ---
    with tab_insights:
        if df.empty:
            st.info("No feedback submitted yet.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Responses", len(df))
            col2.metric("Average Rating", f"{df['rating'].mean():.2f} ⭐")
            neg_pct = (df["sentiment"] == "Negative").mean() * 100
            col3.metric("% Negative Sentiment", f"{neg_pct:.0f}%")

            st.subheader("Sentiment Breakdown")
            sentiment_counts = df["sentiment"].value_counts()
            st.bar_chart(sentiment_counts)

            st.subheader("Average Rating by Category")
            st.bar_chart(df.groupby("category")["rating"].mean())

            st.subheader("Top Keywords in Comments")
            keywords = extract_keywords(df["comment"].tolist())
            if keywords:
                kw_df = pd.DataFrame(keywords, columns=["Keyword", "Frequency"])
                st.dataframe(kw_df, use_container_width=True, hide_index=True)
            else:
                st.write("Not enough comment text yet to extract keywords.")

    # --- Raw feedback + export ---
    with tab_feedback:
        if df.empty:
            st.info("No feedback submitted yet.")
        else:
            category_filter = st.multiselect("Filter by category", CATEGORIES, default=CATEGORIES)
            sentiment_filter = st.multiselect(
                "Filter by sentiment", ["Positive", "Neutral", "Negative"],
                default=["Positive", "Neutral", "Negative"],
            )
            filtered = df[
                df["category"].isin(category_filter) & df["sentiment"].isin(sentiment_filter)
            ]
            st.dataframe(
                filtered[["created_at", "category", "subject", "rating", "sentiment", "comment"]],
                use_container_width=True,
                hide_index=True,
            )
            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export CSV", csv, "feedback_export.csv", "text/csv")

    # --- Poll management ---
    with tab_polls:
        st.subheader("Create a new poll")
        with st.form("new_poll_form", clear_on_submit=True):
            question = st.text_input("Poll question")
            a = st.text_input("Option A")
            b = st.text_input("Option B")
            c = st.text_input("Option C (optional)")
            d = st.text_input("Option D (optional)")
            create = st.form_submit_button("Create Poll")
            if create:
                if question and a and b:
                    db.create_poll(question, a, b, c or None, d or None)
                    st.success("Poll created!")
                else:
                    st.warning("Question, Option A, and Option B are required.")

        st.subheader("Existing polls")
        for poll in db.get_all_polls():
            with st.expander(f"{'🟢' if poll['is_active'] else '⚪'} {poll['question']}"):
                results = db.get_poll_results(poll["id"])
                if results:
                    st.bar_chart(pd.Series(results))
                else:
                    st.write("No votes yet.")
                if poll["is_active"]:
                    if st.button("Close poll", key=f"close_{poll['id']}"):
                        db.close_poll(poll["id"])
                        st.rerun()
