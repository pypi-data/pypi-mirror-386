# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="union-attr"
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import create_react_agent

LOCATION = "global"
LLM = "gemini-2.5-flash"

llm = ChatVertexAI(model=LLM, location=LOCATION, temperature=0)


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather"""
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


agent = create_react_agent(
    model=llm, tools=[get_weather], prompt="You are a helpful assistant"
)
