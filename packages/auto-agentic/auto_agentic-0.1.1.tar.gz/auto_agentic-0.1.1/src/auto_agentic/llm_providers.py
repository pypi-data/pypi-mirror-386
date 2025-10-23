"""
OpenAI LLM provider implementation.
"""

import json
import logging
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .interfaces import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o-mini)
        """
        self.llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompt templates."""
        self.intent_prompt = ChatPromptTemplate.from_template("""
You are an intent classifier.
Decide if this user message is:
1. A **casual greeting/small talk**
2. A **data-related task/query** about a database
3. A **recall/follow-up** where the user refers to previous responses or facts, identify pronouns like these, his, her, them, etc.
4. A **combination** of both task and recall (e.g., asking for new data but referencing previous results like lists, names, numbers, etc., identify pronouns like these, his, her, them, etc.)

You have full conversation context below:
{history}

Respond with exactly one word: "greeting", "task", "recall", or "task+recall".

User message: {message}
""")

        self.sql_prompt = ChatPromptTemplate.from_template("""
You are a SQL generation agent.
You have full conversation context below for reference:
{history}

Database schema:
{schema}

User question:
{question}

Generate a valid SQLite SQL query only. No explanations or markdown. Do not make up table or column names. Always use the schema provided.
""")

        self.summarizer_prompt = ChatPromptTemplate.from_template("""
You are a summarizer agent.
You have full conversation history for reference:
{history}

User question:
{user_question}

Retrieved data (JSON):
{data}

Summarize the retrieved data clearly using Markdown. Use your knowledge to identify the entities in the data. Never return in Tabular format. Use bullet points and list items to make it more readable.
If the data is not found, say an appropriate message.
""")

        self.greeting_prompt = ChatPromptTemplate.from_template("""
You are a friendly conversational agent.
Conversation context:
{history}

Respond naturally and concisely to:
{message}
""")

        self.recall_prompt = ChatPromptTemplate.from_template("""
You are a reasoning agent.
Using the full conversation history and any available structured data, answer the user's follow-up question directly.
If previous data exists (like lists, names, numbers), use it.
If current data is provided below, analyze it and use it to answer the question.
If the information isn't found in history or current data, say "I don't have that information yet."

Conversation history:
{history}

Current data (if any):
{data}

User question:
{message}

IMPORTANT: If current data is provided, analyze it carefully and use it to answer the user's question. Do not ignore the current data.

Answer concisely and factually.
""")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def generate_sql(self, schema: str, question: str, history: List[Dict]) -> str:
        """Generate SQL query from natural language."""
        chain = self.sql_prompt | self.llm
        response = chain.invoke({
            "schema": schema,
            "question": question,
            "history": json.dumps(history, indent=2)
        })
        return response.content.strip()
    
    def summarize_data(self, question: str, data: List[Dict], history: List[Dict]) -> str:
        """Summarize query results into natural language."""
        chain = self.summarizer_prompt | self.llm
        response = chain.invoke({
            "user_question": question,
            "data": json.dumps(data, indent=2),
            "history": json.dumps(history, indent=2)
        })
        return response.content.strip()
    
    def classify_intent(self, message: str, history: List[Dict]) -> str:
        """Classify user intent (greeting, task, recall, task+recall)."""
        chain = self.intent_prompt | self.llm
        result = chain.invoke({"message": message, "history": json.dumps(history, indent=2)})
        content = result.content.strip().lower()
        
        if "task+recall" in content:
            return "task+recall"
        if "recall" in content:
            return "recall"
        if "greeting" in content:
            return "greeting"
        return "task"
    
    def chat_response(self, message: str, history: List[Dict]) -> str:
        """Generate chat response for greetings."""
        chain = self.greeting_prompt | self.llm
        response = chain.invoke({
            "message": message,
            "history": json.dumps(history, indent=2)
        })
        return response.content.strip()
    
    def recall_response(self, message: str, history: List[Dict], new_data: List[Dict] = None) -> str:
        """Generate recall response."""
        # Extract latest structured data, if any
        last_data = None
        for entry in reversed(history):
            if "retrieved_data" in entry and entry["retrieved_data"]:
                last_data = entry["retrieved_data"]
                break
        
        # Use new_data if provided, otherwise use last_data from history
        data_to_use = new_data if new_data is not None else last_data
        
        logger.info(f"Recall agent - new_data provided: {new_data is not None}")
        logger.info(f"Recall agent - data_to_use: {json.dumps(data_to_use, indent=2) if data_to_use else 'None'}")

        chain = self.recall_prompt | self.llm
        response = chain.invoke({
            "message": message,
            "history": json.dumps(history, indent=2),
            "data": json.dumps(data_to_use, indent=2) if data_to_use else "None"
        })
        return response.content.strip()
