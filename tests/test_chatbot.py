"""
Unit Tests for Rule-Based Chatbot
=================================
Runs with pytest to verify:
1. Intent matching (greetings, jokes, capabilities).
2. Name extraction and session memory persistence.
3. Time/Date dynamic calculations.
4. Keyword overlap scoring mechanism.
5. Fallback behavior for unrecognized inputs.
"""

import pytest
from datetime import datetime
from src.chatbot import RuleBasedChatbot


@pytest.fixture
def bot():
    """Fixture providing a fresh chatbot instance for each test."""
    return RuleBasedChatbot(intents_path="data/intents.json")


def test_greeting_intent_matching(bot):
    """Test 1: Verify that greetings map to the 'greeting' intent."""
    test_inputs = ["hello", "hi there", "hey", "good morning"]
    for phrase in test_inputs:
        result = bot.get_response(phrase)
        assert result["intent"] == "greeting", f"Failed for input: {phrase}"
        assert result["score"] > 0.3
        assert len(result["response"]) > 0


def test_name_extraction_and_session_memory(bot):
    """Test 2: Verify user name extraction and memory persistence across turns."""
    # Initially name should be None
    assert bot.user_name is None

    # User introduces themselves
    intro_result = bot.get_response("Hello, my name is Alex")
    assert bot.user_name == "Alex"
    assert "Alex" in intro_result["response"]

    # In next turn, user says thanks and bot should use remembered name
    thanks_result = bot.get_response("Thank you very much")
    assert "Alex" in thanks_result["response"]

    # User asks bot for their own name
    ask_name_result = bot.get_response("What is my name?")
    assert "Alex" in ask_name_result["response"]


def test_time_and_date_dynamic_reply(bot):
    """Test 3: Verify dynamic date/time resolution based on current system time."""
    result = bot.get_response("what time is it right now?")
    assert result["intent"] == "time_date"

    # Current year or month should appear dynamically in the formatted string
    current_year = str(datetime.now().year)
    response_text = result["response"]
    
    # Check that either the year or an AM/PM clock indicator is in response
    assert (current_year in response_text) or ("AM" in response_text or "PM" in response_text), \
        f"Expected datetime components in response: {response_text}"


def test_keyword_overlap_scoring(bot):
    """Test 4: Verify keyword overlap scoring identifies correct intent even with extra words."""
    # Pattern contains "tell me a joke" or "make me laugh"
    result = bot.get_response("Could you please tell me a funny joke to make me laugh?")
    assert result["intent"] == "jokes"
    assert result["score"] >= 0.5


def test_fallback_intent_on_gibberish(bot):
    """Test 5: Verify that unrecognized inputs trigger the fallback intent."""
    gibberish = "zxcvbnmasdfghjk 998877 qwerty"
    result = bot.get_response(gibberish)
    assert result["intent"] == "fallback"
    assert "didn't quite catch" in result["response"].lower() or "not sure" in result["response"].lower() or "rule base" in result["response"].lower()
