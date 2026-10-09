"""
ai_helpers.py

This module contains the ONLY "AI" logic in the app, and it is intentionally
non-agentic:
    - Each function takes text in, returns a result, and does nothing else.
    - No planning, no tool-calling, no multi-step decision loops, no memory
      of past calls, no autonomous actions on the system.
That keeps it squarely in "uses AI" territory rather than "agentic AI".

Sentiment: TextBlob's built-in polarity classifier (a pretrained, static model).
Keyword extraction: simple frequency counting after stopword removal.
"""

from textblob import TextBlob
import re
from collections import Counter

STOPWORDS = set("""
a an the this that these those is are was were be been being have has had
do does did will would shall should can could may might must i you he she
it we they me him her us them my your his its our their and or but if then
so because as of in on at to for with without into onto from by about
class lab facility very really just quite also not no
""".split())


def analyze_sentiment(text: str):
    """
    Single-shot sentiment classification.
    Returns (label, polarity_score) where label is Positive / Neutral / Negative
    and polarity_score is a float between -1 (very negative) and 1 (very positive).
    """
    if not text or not text.strip():
        return "Neutral", 0.0

    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.15:
        label = "Positive"
    elif polarity < -0.15:
        label = "Negative"
    else:
        label = "Neutral"

    return label, round(polarity, 3)


def extract_keywords(comments: list, top_n: int = 10):
    """
    Very simple, deterministic keyword frequency extraction across a list
    of feedback comments. Helps admins spot recurring themes/issues at a
    glance without reading every comment individually.
    """
    words = []
    for comment in comments:
        if not comment:
            continue
        tokens = re.findall(r"[a-zA-Z']+", comment.lower())
        words.extend([t for t in tokens if t not in STOPWORDS and len(t) > 2])

    return Counter(words).most_common(top_n)
