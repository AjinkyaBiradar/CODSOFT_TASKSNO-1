"""
Rule-Based Chatbot Engine
=========================
This module handles:
1. Loading intent rules from a JSON file.
2. Regex pattern matching & entity extraction (e.g., user name).
3. Keyword-overlap scoring for intent classification.
4. Dynamic response generation (personalization, time/date formatting).
"""

import os
import re
import json
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class RuleBasedChatbot:
    """A rule-based chatbot utilizing regex matching, keyword overlap, and session memory."""

    # Common English stop words to ignore during keyword scoring for better accuracy
    STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "to", "for", "in", "on",
        "at", "of", "do", "does", "did", "can", "could", "would", "should", "it"
    }

    # Regex patterns to detect when a user is introducing themselves
    NAME_PATTERNS = [
        re.compile(r"\bmy name is\s+([A-Za-z]+)\b", re.IGNORECASE),
        re.compile(r"\bi am called\s+([A-Za-z]+)\b", re.IGNORECASE),
        re.compile(r"\bcall me\s+([A-Za-z]+)\b", re.IGNORECASE),
        re.compile(r"\bi am\s+([A-Za-z]+)\b", re.IGNORECASE),
        re.compile(r"\bthis is\s+([A-Za-z]+)\b", re.IGNORECASE),
    ]

    # Regex patterns for asking the bot to recall the user's name
    ASK_USER_NAME_PATTERN = re.compile(
        r"\b(?:what is my name|who am i|do you know my name|remember my name)\b",
        re.IGNORECASE
    )

    def __init__(self, intents_path: str = "data/intents.json", user_name: Optional[str] = None):
        """
        Initialize chatbot with intent definitions and optional user name.

        Args:
            intents_path: Relative or absolute path to the intents JSON file.
            user_name: Initial user name if known.
        """
        self.intents_path = intents_path
        self.user_name = user_name
        self.intents = self._load_intents()

    def _load_intents(self) -> List[Dict[str, Any]]:
        """Load intent rules from the JSON file."""
        if not os.path.exists(self.intents_path):
            raise FileNotFoundError(f"Intents file not found at: {self.intents_path}")

        with open(self.intents_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("intents", [])

    def tokenize(self, text: str) -> List[str]:
        """
        Clean and split input string into individual word tokens.
        
        Args:
            text: Raw input string.
            
        Returns:
            List of lowercased alphanumeric word tokens without stop words.
        """
        clean_text = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [token for token in clean_text.split() if token not in self.STOP_WORDS]
        return tokens

    def calculate_keyword_overlap(self, user_tokens: List[str], pattern_tokens: List[str]) -> float:
        """
        Calculate the keyword overlap score between user tokens and a pattern.

        Formula:
            Overlap = (Matching Tokens) / (Total Pattern Tokens)

        Args:
            user_tokens: Tokens from user input.
            pattern_tokens: Tokens from the intent pattern.

        Returns:
            Float score between 0.0 and 1.0.
        """
        if not pattern_tokens or not user_tokens:
            return 0.0

        user_set = set(user_tokens)
        pattern_set = set(pattern_tokens)
        intersection = user_set.intersection(pattern_set)

        # Ratio of matched pattern keywords
        score = len(intersection) / len(pattern_set)
        return score

    def extract_name(self, text: str) -> Optional[str]:
        """
        Extract user's name from text using regular expressions.

        Args:
            text: User input string.

        Returns:
            Extracted name capitalized, or None if no match.
        """
        for pattern in self.NAME_PATTERNS:
            match = pattern.search(text)
            if match:
                candidate_name = match.group(1).strip()
                # Ignore common words that follow 'i am' like 'fine', 'good', 'happy', 'sad'
                excluded = {"fine", "good", "happy", "sad", "here", "ready", "sorry", "tired", "back", "hungry"}
                if candidate_name.lower() not in excluded and len(candidate_name) > 1:
                    return candidate_name.capitalize()
        return None

    def match_intent(self, user_input: str) -> Tuple[str, float]:
        """
        Determine the best matching intent using regex matching and keyword-overlap scoring.

        Args:
            user_input: Cleaned user message.

        Returns:
            Tuple of (best_intent_tag, confidence_score).
        """
        user_tokens = self.tokenize(user_input)
        best_tag = "fallback"
        best_score = 0.0

        # Confidence threshold below which fallback is triggered
        MIN_CONFIDENCE_THRESHOLD = 0.35

        for intent in self.intents:
            tag = intent.get("tag")
            patterns = intent.get("patterns", [])

            if tag == "fallback":
                continue

            for pattern in patterns:
                # 1. Regex Match: Check for exact phrase or boundary match
                # Gives high confidence if the exact pattern phrase is found in input
                regex_pattern = r"\b" + re.escape(pattern.lower()) + r"\b"
                if re.search(regex_pattern, user_input.lower()):
                    regex_score = 1.0
                    if regex_score > best_score:
                        best_score = regex_score
                        best_tag = tag
                        continue

                # 2. Keyword Overlap Scoring
                pattern_tokens = self.tokenize(pattern)
                overlap_score = self.calculate_keyword_overlap(user_tokens, pattern_tokens)

                if overlap_score > best_score:
                    best_score = overlap_score
                    best_tag = tag

        # Check threshold
        if best_score < MIN_CONFIDENCE_THRESHOLD:
            return "fallback", best_score

        return best_tag, best_score

    def _format_response(self, template: str) -> str:
        """
        Replace template placeholders with session-specific values.

        Placeholders:
            {name}: User's stored name or polite greeting
            {datetime}: Full date and time
            {time}: Current time
            {date}: Current date
        """
        now = datetime.now()
        name_placeholder = self.user_name if self.user_name else "there"

        formatted = template.replace("{name}", name_placeholder)
        formatted = formatted.replace("{datetime}", now.strftime("%A, %B %d, %Y at %I:%M %p"))
        formatted = formatted.replace("{time}", now.strftime("%I:%M %p"))
        formatted = formatted.replace("{date}", now.strftime("%B %d, %Y"))

        # Clean up any awkward double spaces if name is empty
        formatted = re.sub(r"\s+", " ", formatted).strip()
        return formatted

    def get_response(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input, maintain session state, and generate a reply.

        Args:
            user_input: The message sent by the user.

        Returns:
            Dictionary containing:
                - 'response': Generated reply text
                - 'intent': Matched intent tag
                - 'score': Confidence score
                - 'user_name': Current session user name
        """
        text = user_input.strip()
        if not text:
            return {
                "response": "Please type something so I can help you!",
                "intent": "empty",
                "score": 1.0,
                "user_name": self.user_name
            }

        # Check if user introduced their name
        extracted_name = self.extract_name(text)
        if extracted_name:
            self.user_name = extracted_name
            return {
                "response": f"Nice to meet you, {self.user_name}! I have remembered your name.",
                "intent": "name",
                "score": 1.0,
                "user_name": self.user_name
            }

        # Check if user is asking what their stored name is
        if self.ASK_USER_NAME_PATTERN.search(text):
            if self.user_name:
                reply = f"Your name is {self.user_name}! I remember our conversation."
            else:
                reply = "I don't know your name yet! You can tell me by saying 'My name is [your name]'."
            return {
                "response": reply,
                "intent": "name",
                "score": 1.0,
                "user_name": self.user_name
            }

        # Match intent using regex and keyword overlap
        tag, score = self.match_intent(text)

        # Retrieve intent definition
        matched_intent = next((item for item in self.intents if item.get("tag") == tag), None)
        
        # Fallback if tag is not found
        if not matched_intent:
            matched_intent = next((item for item in self.intents if item.get("tag") == "fallback"), {
                "responses": ["I am sorry, I am not sure how to answer that."]
            })

        # Select random response template and format it
        responses = matched_intent.get("responses", ["Hello!"])
        chosen_template = random.choice(responses)
        response_text = self._format_response(chosen_template)

        return {
            "response": response_text,
            "intent": tag,
            "score": round(score, 2),
            "user_name": self.user_name
        }
