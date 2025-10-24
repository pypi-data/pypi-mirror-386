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
{%- if cookiecutter.agent_name == "adk_live" %}

import json
import logging
import time

from locust import User, between, task
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketUser(User):
    """Simulates a user making websocket requests to the remote agent engine."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    abstract = True

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        if self.host.startswith("https://"):
            self.ws_url = self.host.replace("https://", "wss://", 1) + "/ws"
        elif self.host.startswith("http://"):
            self.ws_url = self.host.replace("http://", "ws://", 1) + "/ws"
        else:
            self.ws_url = self.host + "/ws"

    @task
    def websocket_audio_conversation(self) -> None:
        """Test a full websocket conversation with audio input."""
        start_time = time.time()
        response_count = 0
        exception = None

        try:
            response_count = self._websocket_interaction()

            # Mark as failure if we got no valid responses
            if response_count == 0:
                exception = Exception("No responses received from agent")

        except WebSocketException as e:
            exception = e
            logger.error(f"WebSocket error: {e}")
        except Exception as e:
            exception = e
            logger.error(f"Unexpected error: {e}")
        finally:
            total_time = int((time.time() - start_time) * 1000)

            # Report the request metrics to Locust
            self.environment.events.request.fire(
                request_type="WS",
                name="websocket_conversation",
                response_time=total_time,
                response_length=response_count * 100,  # Approximate response size
                response=None,
                context={},
                exception=exception,
            )

    def _websocket_interaction(self) -> int:
        """Handle the websocket interaction and return response count."""
        response_count = 0

        with connect(self.ws_url, open_timeout=10, close_timeout=20) as websocket:
            # Wait for setupComplete
            setup_response = websocket.recv(timeout=10.0)
            setup_data = json.loads(setup_response)
            assert "setupComplete" in setup_data, (
                f"Expected setupComplete, got {setup_data}"
            )
            logger.info("Received setupComplete")

            # Send dummy audio chunk with user_id
            dummy_audio = bytes([0] * 1024)
            audio_msg = {
                "user_id": "load-test-user",
                "realtimeInput": {
                    "mediaChunks": [
                        {
                            "mimeType": "audio/pcm;rate=16000",
                            "data": dummy_audio.hex(),
                        }
                    ]
                },
            }
            websocket.send(json.dumps(audio_msg))
            logger.info("Sent audio chunk")

            # Send text message to complete the turn
            text_msg = {
                "content": {
                    "role": "user",
                    "parts": [{"text": "Hello!"}],
                }
            }
            websocket.send(json.dumps(text_msg))
            logger.info("Sent text completion")

            # Collect responses until turn_complete or timeout
            for _ in range(20):  # Max 20 responses
                try:
                    response = websocket.recv(timeout=10.0)
                    response_data = json.loads(response)
                    response_count += 1
                    logger.debug(f"Received response: {response_data}")

                    if isinstance(response_data, dict) and response_data.get(
                        "turn_complete"
                    ):
                        logger.info(f"Turn complete after {response_count} responses")
                        break
                except TimeoutError:
                    logger.info(f"Timeout after {response_count} responses")
                    break

        return response_count


class RemoteAgentUser(WebSocketUser):
    """User for testing remote agent engine deployment."""

    # Set the host via command line: locust -f load_test.py --host=https://your-deployed-service.run.app
    host = "http://localhost:8000"  # Default for local testing
{%- else %}

import json
import logging
import os
import time

from locust import HttpUser, between, task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Vertex AI and load agent config
with open("deployment_metadata.json") as f:
    remote_agent_engine_id = json.load(f)["remote_agent_engine_id"]

parts = remote_agent_engine_id.split("/")
project_id = parts[1]
location = parts[3]
engine_id = parts[5]

# Convert remote agent engine ID to streaming URL.
base_url = f"https://{location}-aiplatform.googleapis.com"
url_path = f"/v1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}:streamQuery"

logger.info("Using remote agent engine ID: %s", remote_agent_engine_id)
logger.info("Using base URL: %s", base_url)
logger.info("Using URL path: %s", url_path)


class ChatStreamUser(HttpUser):
    """Simulates a user interacting with the chat stream API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = base_url  # Set the base host URL for Locust

    @task
    def chat_stream(self) -> None:
        """Simulates a chat stream interaction."""
        headers = {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {os.environ['_AUTH_TOKEN']}"
{% if cookiecutter.is_adk %}
        data = {
            "class_method": "async_stream_query",
            "input": {
                "user_id": "test",
                "message": "What's the weather in San Francisco?",
            },
        }
{% else %}
        data = {
            "input": {
                "input": {
                    "messages": [
                        {"type": "human", "content": "Hello, AI!"},
                        {"type": "ai", "content": "Hello!"},
                        {"type": "human", "content": "How are you?"},
                    ]
                },
                "config": {
                    "metadata": {"user_id": "test-user", "session_id": "test-session"}
                },
            }
        }
{% endif %}
        start_time = time.time()
        with self.client.post(
            url_path,
            headers=headers,
            json=data,
            catch_response=True,
{%- if cookiecutter.is_adk %}
            name="/streamQuery async_stream_query",
{%- else %}
            name="/stream_messages first message",
{%- endif %}
            stream=True,
            params={"alt": "sse"},
        ) as response:
            if response.status_code == 200:
                events = []
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        events.append(line_str)

                        if "429 Too Many Requests" in line_str:
                            self.environment.events.request.fire(
                                request_type="POST",
                                name=f"{url_path} rate_limited 429s",
                                response_time=0,
                                response_length=len(line),
                                response=response,
                                context={},
                            )
                end_time = time.time()
                total_time = end_time - start_time
                self.environment.events.request.fire(
                    request_type="POST",
{%- if cookiecutter.is_adk %}
                    name="/streamQuery end",
{%- else %}
                    name="/stream_messages end",
{%- endif %}
                    response_time=total_time * 1000,  # Convert to milliseconds
                    response_length=len(events),
                    response=response,
                    context={},
                )
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
{%- endif %}
