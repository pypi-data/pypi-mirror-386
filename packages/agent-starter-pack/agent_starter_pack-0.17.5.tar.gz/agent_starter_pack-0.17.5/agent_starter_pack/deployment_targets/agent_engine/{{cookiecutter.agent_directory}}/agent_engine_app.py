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

# mypy: disable-error-code="attr-defined,arg-type"
{%- if cookiecutter.is_adk %}
import logging
import os
from typing import Any

import click
import google.auth
import vertexai
from google.adk.artifacts import GcsArtifactService
from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export
from vertexai._genai.types import AgentEngine, AgentEngineConfig{%- if cookiecutter.is_adk_live %}, AgentServerMode{%- endif %}
{%- if cookiecutter.is_adk_live %}
from vertexai.preview.reasoning_engines import AdkApp
{%- else %}
from vertexai.agent_engines.templates.adk import AdkApp
{%- endif %}

from {{cookiecutter.agent_directory}}.agent import root_agent
from {{cookiecutter.agent_directory}}.utils.deployment import (
    parse_env_vars,
    print_deployment_success,
    write_deployment_metadata,
)
from {{cookiecutter.agent_directory}}.utils.gcs import create_bucket_if_not_exists
from {{cookiecutter.agent_directory}}.utils.tracing import CloudTraceLoggingSpanExporter
from {{cookiecutter.agent_directory}}.utils.typing import Feedback


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Set up logging and tracing for the agent engine app."""
        import logging

        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        provider = TracerProvider()
        processor = export.BatchSpanProcessor(
            CloudTraceLoggingSpanExporter(
                project_id=os.environ.get("GOOGLE_CLOUD_PROJECT")
            )
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent.

        Extends the base operations to include feedback registration functionality.
        """
        operations = super().register_operations()
        operations[""] = operations.get("", []) + ["register_feedback"]
        return operations

{%- else %}
import logging
import os
from collections.abc import Iterable, Mapping
from typing import (
    Any,
)

import click
import google.auth
import vertexai
from google.cloud import logging as google_cloud_logging
from langchain_core.runnables import RunnableConfig
from traceloop.sdk import Instruments, Traceloop
from vertexai._genai.types import AgentEngine, AgentEngineConfig

from {{cookiecutter.agent_directory}}.utils.deployment import (
    parse_env_vars,
    print_deployment_success,
    write_deployment_metadata,
)
from {{cookiecutter.agent_directory}}.utils.gcs import create_bucket_if_not_exists
from {{cookiecutter.agent_directory}}.utils.tracing import CloudTraceLoggingSpanExporter
from {{cookiecutter.agent_directory}}.utils.typing import Feedback, InputChat, dumpd, ensure_valid_config


class AgentEngineApp:
    """Class for managing agent engine functionality."""

    def __init__(self, project_id: str | None = None) -> None:
        """Initialize the AgentEngineApp variables"""
        self.project_id = project_id

    def set_up(self) -> None:
        """The set_up method is used to define application initialization logic"""
        # Lazy import agent at setup time to avoid deployment dependencies
        from {{cookiecutter.agent_directory}}.agent import agent

        logging_client = google_cloud_logging.Client(project=self.project_id)
        self.logger = logging_client.logger(__name__)

        # Initialize Telemetry
        try:
            Traceloop.init(
                app_name="{{cookiecutter.project_name}}",
                disable_batch=False,
                exporter=CloudTraceLoggingSpanExporter(project_id=self.project_id),
                instruments={Instruments.LANGCHAIN, Instruments.CREW},
            )
        except Exception as e:
            logging.error("Failed to initialize Telemetry: %s", str(e))
        self.runnable = agent

    # Add any additional variables here that should be included in the tracing logs
    def set_tracing_properties(self, config: RunnableConfig | None) -> None:
        """Sets tracing association properties for the current request.

        Args:
            config: Optional RunnableConfig containing request metadata
        """
        config = ensure_valid_config(config)
        Traceloop.set_association_properties(
            {
                "log_type": "tracing",
                "run_id": str(config["run_id"]),
                "user_id": config["metadata"].pop("user_id", "None"),
                "session_id": config["metadata"].pop("session_id", "None"),
                "commit_sha": os.environ.get("COMMIT_SHA", "None"),
            }
        )

    def stream_query(
        self,
        *,
        input: str | Mapping,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """Stream responses from the agent for a given input."""

        config = ensure_valid_config(config)
        self.set_tracing_properties(config=config)
        # Validate input. We assert the input is a list of messages
        input_chat = InputChat.model_validate(input)

        for chunk in self.runnable.stream(
            input=input_chat, config=config, **kwargs, stream_mode="messages"
        ):
            dumped_chunk = dumpd(chunk)
            yield dumped_chunk

    def query(
        self,
        *,
        input: str | Mapping,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        """Process a single input and return the agent's response."""
        config = ensure_valid_config(config)
        self.set_tracing_properties(config=config)
        return dumpd(self.runnable.invoke(input=input, config=config, **kwargs))

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent.

        This mapping defines how different operation modes (e.g., "", "stream")
        are implemented by specific methods of the Agent.  The "default" mode,
        represented by the empty string ``, is associated with the `query` API,
        while the "stream" mode is associated with the `stream_query` API.

        Returns:
            Mapping[str, Sequence[str]]: A mapping of operation modes to a list
            of method names that implement those operation modes.
        """
        return {
            "": ["query", "register_feedback"],
            "stream": ["stream_query"],
        }
{%- endif %}


@click.command()
@click.option(
    "--project",
    default=None,
    help="GCP project ID (defaults to application default credentials)",
)
@click.option(
    "--location",
    default="us-central1",
    help="GCP region (defaults to us-central1)",
)
@click.option(
    "--agent-name",
    default="{{cookiecutter.project_name}}",
    help="Name for the agent engine",
)
@click.option(
    "--requirements-file",
    default=".requirements.txt",
    help="Path to requirements.txt file",
)
@click.option(
    "--extra-packages",
    multiple=True,
    default=["./{{cookiecutter.agent_directory}}"],
    help="Additional packages to include",
)
@click.option(
    "--set-env-vars",
    default=None,
    help="Comma-separated list of environment variables in KEY=VALUE format",
)
@click.option(
    "--service-account",
    default=None,
    help="Service account email to use for the agent engine",
)
@click.option(
    "--staging-bucket-uri",
    default=None,
    help="GCS bucket URI for staging files (defaults to gs://{project}-agent-engine)",
)
@click.option(
    "--artifacts-bucket-name",
    default=None,
    help="GCS bucket name for artifacts (defaults to gs://{project}-agent-engine)",
)
def deploy_agent_engine_app(
    project: str | None,
    location: str,
    agent_name: str,
    requirements_file: str,
    extra_packages: tuple[str, ...],
    set_env_vars: str | None,
    service_account: str | None,
    staging_bucket_uri: str | None,
    artifacts_bucket_name: str | None,
) -> AgentEngine:
    """Deploy the agent engine app to Vertex AI."""

    logging.basicConfig(level=logging.INFO)

    # Parse environment variables if provided
    env_vars = parse_env_vars(set_env_vars)

    if not project:
        _, project = google.auth.default()
    if not staging_bucket_uri:
        staging_bucket_uri = f"gs://{project}-agent-engine"
    if not artifacts_bucket_name:
        artifacts_bucket_name = f"gs://{project}-agent-engine"

{%- if "adk" in cookiecutter.tags %}
    create_bucket_if_not_exists(
        bucket_name=artifacts_bucket_name, project=project, location=location
    )
{%- endif %}
    create_bucket_if_not_exists(
        bucket_name=staging_bucket_uri, project=project, location=location
    )

    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🤖 DEPLOYING AGENT TO VERTEX AI AGENT ENGINE 🤖         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    extra_packages_list = list(extra_packages)

    # Initialize vertexai client
    client = vertexai.Client(
        project=project,
        location=location,
    )
    vertexai.init(project=project, location=location)

    # Read requirements
    with open(requirements_file) as f:
        requirements = f.read().strip().split("\n")
{% if cookiecutter.is_adk %}
    agent_engine = AgentEngineApp(
        agent=root_agent,
        artifact_service_builder=lambda: GcsArtifactService(
            bucket_name=artifacts_bucket_name
        ),
    )
{% else %}
    agent_engine = AgentEngineApp(project_id=project)
{% endif %}
    # Set worker parallelism to 1
    env_vars["NUM_WORKERS"] = "1"

    # Common configuration for both create and update operations
    labels: dict[str, str] = {}
{%- if cookiecutter.agent_garden %}
{%- if cookiecutter.agent_sample_id and cookiecutter.agent_sample_publisher %}
    labels["vertex-agent-sample-id"] = "{{cookiecutter.agent_sample_id}}"
    labels["vertex-agent-sample-publisher"] = "{{cookiecutter.agent_sample_publisher}}"
    labels["deployed-with"] = "agent-garden"
{%- endif %}
{%- endif %}

    config = AgentEngineConfig(
        display_name=agent_name,
        description="{{cookiecutter.agent_description}}",
        extra_packages=extra_packages_list,
        env_vars=env_vars,
        service_account=service_account,
        requirements=requirements,
        staging_bucket=staging_bucket_uri,
        labels=labels,
        gcs_dir_name=agent_name,
{%- if cookiecutter.is_adk_live %}
        agent_server_mode=AgentServerMode.EXPERIMENTAL,  # Enable bidi streaming
        resource_limits={"cpu": "4", "memory": "8Gi"},
{%- endif %}
    )

    agent_config = {
        "agent": agent_engine,
        "config": config,
    }
    logging.info(f"Agent config: {agent_config}")

    # Check if an agent with this name already exists
    existing_agents = list(client.agent_engines.list())
    matching_agents = [
        agent
        for agent in existing_agents
        if agent.api_resource.display_name == agent_name
    ]

    if matching_agents:
        # Update the existing agent with new configuration
        logging.info(f"\n📝 Updating existing agent: {agent_name}")
        remote_agent = client.agent_engines.update(
            name=matching_agents[0].api_resource.name, **agent_config
        )
    else:
        # Create a new agent if none exists
        logging.info(f"\n🚀 Creating new agent: {agent_name}")
        remote_agent = client.agent_engines.create(**agent_config)

    write_deployment_metadata(remote_agent)
    print_deployment_success(remote_agent, location, project)

    return remote_agent


if __name__ == "__main__":
    deploy_agent_engine_app()
