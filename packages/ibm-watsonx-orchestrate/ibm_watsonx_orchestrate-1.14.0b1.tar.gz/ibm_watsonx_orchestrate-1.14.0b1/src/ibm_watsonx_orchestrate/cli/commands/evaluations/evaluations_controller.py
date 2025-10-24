import logging
import os.path
from typing import List, Dict, Optional, Tuple
from enum import StrEnum
import csv
from pathlib import Path
import sys
from wxo_agentic_evaluation import main as evaluate
from wxo_agentic_evaluation import quick_eval
from wxo_agentic_evaluation.tool_planner import build_snapshot
from wxo_agentic_evaluation.analyze_run import run as run_analyze
from wxo_agentic_evaluation.batch_annotate import generate_test_cases_from_stories
from wxo_agentic_evaluation.arg_configs import TestConfig, AuthConfig, LLMUserConfig, ChatRecordingConfig, AnalyzeConfig, ProviderConfig, AttackConfig, QuickEvalConfig, AnalyzeMode
from wxo_agentic_evaluation.record_chat import record_chats
from wxo_agentic_evaluation.external_agent.external_validate import ExternalAgentValidation
from wxo_agentic_evaluation.external_agent.performance_test import ExternalAgentPerformanceTest
from wxo_agentic_evaluation.red_teaming.attack_list import print_attacks
from wxo_agentic_evaluation.red_teaming import attack_generator
from wxo_agentic_evaluation.red_teaming.attack_runner import run_attacks
from wxo_agentic_evaluation.arg_configs import AttackGeneratorConfig
from ibm_watsonx_orchestrate import __version__
from ibm_watsonx_orchestrate.cli.config import (
    Config,
    ENV_WXO_URL_OPT,
    AUTH_CONFIG_FILE,
    AUTH_CONFIG_FILE_FOLDER,
    AUTH_SECTION_HEADER,
    AUTH_MCSP_TOKEN_OPT,
    PROTECTED_ENV_NAME,
    DEFAULT_LOCAL_SERVICE_URL,
)
from ibm_watsonx_orchestrate.utils.utils import yaml_safe_load
from ibm_watsonx_orchestrate.cli.commands.agents.agents_controller import AgentsController
from ibm_watsonx_orchestrate.agent_builder.agents import AgentKind
from ibm_watsonx_orchestrate.utils.file_manager import safe_open
import uuid

logger = logging.getLogger(__name__)

class EvaluateMode(StrEnum):
    default = "default" # referenceFUL evaluation
    referenceless = "referenceless"

class EvaluationsController:
    def __init__(self):
        pass

    def _get_env_config(self) -> tuple[str, str, str | None]:
        cfg = Config()

        try:
            url = cfg.get_active_env_config(ENV_WXO_URL_OPT)
        except Exception as e:
            logger.error(f"Error retrieving service url: {e}")
            url = None

        try:
            tenant_name = cfg.get_active_env()
        except Exception as e:
            logger.error(f"Error retrieving active environment: {e}")
            tenant_name = None
        
        if url is None:
            logger.warning(
                "No active service URL found in config. Falling back to local URL '%s'.",
                DEFAULT_LOCAL_SERVICE_URL,
            )
            url = DEFAULT_LOCAL_SERVICE_URL
        if tenant_name is None:
            logger.warning(
                "No active tenant/environment found in config. Falling back to local environment '%s'.",
                PROTECTED_ENV_NAME,
            )
            tenant_name = PROTECTED_ENV_NAME

        auth_cfg = Config(AUTH_CONFIG_FILE_FOLDER, AUTH_CONFIG_FILE)
        existing_auth_config = auth_cfg.get(AUTH_SECTION_HEADER).get(tenant_name, {})
        token = existing_auth_config.get(AUTH_MCSP_TOKEN_OPT) if existing_auth_config else None

        return url, tenant_name, token

    def evaluate(self, config_file: Optional[str] = None, test_paths: Optional[str] = None, output_dir: Optional[str] = None, tools_path: str = None, mode: str = EvaluateMode.default) -> None:
        url, tenant_name, token = self._get_env_config()

        if "WATSONX_SPACE_ID" in os.environ and "WATSONX_APIKEY" in os.environ:
            provider = "watsonx"
        elif "WO_INSTANCE" in os.environ and ("WO_API_KEY" in os.environ or "WO_PASSWORD" in os.environ):
            provider = "model_proxy"
        else:
            logger.error(
                "No provider found. Please either provide a config_file or set either WATSONX_SPACE_ID and WATSONX_APIKEY or WO_INSTANCE and WO_API_KEY in your system environment variables."
            )
            sys.exit(1)
        
        config_data = {
            "wxo_lite_version": __version__,
            "auth_config": AuthConfig(
                url=url,
                tenant_name=tenant_name,
                token=token
            ),
            "provider_config": ProviderConfig(
                provider=provider,
                model_id="meta-llama/llama-3-405b-instruct",
            )
        }

        if config_file:
            logger.info(f"Loading configuration from {config_file}")
            with safe_open(config_file, 'r') as f:
                file_config = yaml_safe_load(f) or {}
                
                if "auth_config" in file_config:
                    auth_config_data = file_config.pop("auth_config")
                    config_data["auth_config"] = AuthConfig(**auth_config_data)
                
                if "llm_user_config" in file_config:
                    llm_config_data = file_config.pop("llm_user_config")
                    config_data["llm_user_config"] = LLMUserConfig(**llm_config_data)

                if "provider_config" in file_config:
                    provider_config_data = file_config.pop("provider_config")
                    config_data["provider_config"] = ProviderConfig(**provider_config_data)
                
                config_data.update(file_config)

        if test_paths:
            config_data["test_paths"] = test_paths.split(",")
            logger.info(f"Using test paths: {config_data['test_paths']}")
        if output_dir:
            config_data["output_dir"] = output_dir
            logger.info(f"Using output directory: {config_data['output_dir']}")

        if mode == EvaluateMode.default:
            config = TestConfig(**config_data)
            evaluate.main(config)
        elif mode == EvaluateMode.referenceless:
            config_data["tools_path"] = tools_path
            config = QuickEvalConfig(**config_data)
            quick_eval.main(config)

    def record(self, output_dir) -> None:


        random_uuid = str(uuid.uuid4())

        url, tenant_name, token = self._get_env_config()
        config_data = {
            "output_dir": Path(os.path.join(Path.cwd(), random_uuid)) if output_dir is None else Path(os.path.join(output_dir,random_uuid)),
            "service_url": url,
            "tenant_name": tenant_name,
            "token": token
        }

        config_data["output_dir"].mkdir(parents=True, exist_ok=True)
        logger.info(f"Recording chat sessions to {config_data['output_dir']}")

        record_chats(ChatRecordingConfig(**config_data))

    def generate(self, stories_path: str, tools_path: str, output_dir: str) -> None:
        stories_path = Path(stories_path)
        tools_path = Path(tools_path)

        if output_dir is None:
            output_dir = stories_path.parent
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        stories_by_agent = {}
        with stories_path.open("r", encoding="utf-8", newline='') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                agent_name = row["agent"]
                if agent_name not in stories_by_agent:
                    stories_by_agent[agent_name] = []
                stories_by_agent[agent_name].append(row["story"])

        for agent_name, stories in stories_by_agent.items():
            logger.info(f"Found {len(stories)} stories for agent '{agent_name}'")
            try:
                agent_controller = AgentsController()
                agent = agent_controller.get_agent(agent_name, AgentKind.NATIVE)
                allowed_tools = agent_controller.get_agent_tool_names(agent.tools)
            except Exception as e:
                logger.warning(f"Could not get tools for agent {agent_name}: {str(e)}")
                allowed_tools = []


            logger.info(f"Running tool planner for agent {agent_name}")
            agent_snapshot_path = output_dir / f"{agent_name}_snapshot_llm.json"
            build_snapshot(agent_name, tools_path, stories, agent_snapshot_path)

            logger.info(f"Running batch annotate for agent {agent_name}")
            generate_test_cases_from_stories(
                agent_name=agent_name,
                stories=stories,
                tools_path=tools_path,
                snapshot_path=agent_snapshot_path,
                output_dir=output_dir / f"{agent_name}_test_cases",
                allowed_tools=allowed_tools,
                num_variants=2
            )

        logger.info("Test cases stored at: %s", output_dir)

    def analyze(self, data_path: str, tool_definition_path: str, mode: AnalyzeMode) -> None:
        if mode not in AnalyzeMode.__members__:
            logger.error(
                f"Invalid mode '{mode}' passed. `mode` must be either `enhanced` or `default`."
            )
            sys.exit(1)

        config = AnalyzeConfig(
            data_path=data_path,
            tool_definition_path=tool_definition_path,
            mode=mode
        )
        run_analyze(config)

    def summarize(self) -> None:
        pass

    def external_validate(self, config: Dict, data: List[str], credential:str, add_context: bool = False):
        validator = ExternalAgentValidation(credential=credential,
                                auth_scheme=config["auth_scheme"],
                                service_url=config["api_url"])
        
        summary = []
        for entry in data:
            results = validator.call_validation(entry, add_context)
            summary.append(results)

        return summary
    
    def generate_performance_test(self, agent_name: str, test_data: List[Tuple[str, str]]):
        performance_test = ExternalAgentPerformanceTest(
            agent_name=agent_name,
            test_data=test_data
        )
        generated_performance_tests = performance_test.generate_tests()

        return generated_performance_tests
    
    def list_red_teaming_attacks(self):
        print_attacks()

    def generate_red_teaming_attacks(
        self,
        attacks_list: str,
        datasets_path: str,
        agents_list_or_path: str,
        target_agent_name: str,
        output_dir: Optional[str] = None,
        max_variants: Optional[int] = None,
    ):
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "red_teaming_attacks")
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"No output directory specified. Using default: {output_dir}")

        url, tenant_name, token = self._get_env_config()

        results = attack_generator.main(
            AttackGeneratorConfig(
                attacks_list=attacks_list.split(","),
                datasets_path=datasets_path.split(","),
                agents_list_or_path=agents_list_or_path
                if os.path.exists(agents_list_or_path)
                else agents_list_or_path.split(","),
                target_agent_name=target_agent_name,
                output_dir=output_dir,
                max_variants=max_variants,
                auth_config=AuthConfig(
                    url=url,
                    tenant_name=tenant_name,
                    token=token,
                ),
            )
        )
        logger.info(f"Generated {len(results)} attacks and saved to {output_dir}")

    def run_red_teaming_attacks(self, attack_paths: str, output_dir: Optional[str] = None) -> None:
        url, tenant_name, token = self._get_env_config()

        if "WATSONX_SPACE_ID" in os.environ and "WATSONX_APIKEY" in os.environ:
            provider = "watsonx"
        elif "WO_INSTANCE" in os.environ and "WO_API_KEY" in os.environ:
            provider = "model_proxy"
        else:
            logger.error(
                "No provider found. Please either provide a config_file or set either WATSONX_SPACE_ID and WATSONX_APIKEY or WO_INSTANCE and WO_API_KEY in your system environment variables."
            )
            sys.exit(1)

        config_data = {
            "auth_config": AuthConfig(
                url=url,
                tenant_name=tenant_name,
                token=token,
            ),
            "provider_config": ProviderConfig(
                provider=provider,
                model_id="meta-llama/llama-3-405b-instruct",
            ),
        }

        config_data["attack_paths"] = attack_paths.split(",")
        if output_dir:
            config_data["output_dir"] = output_dir
        else:
            config_data["output_dir"] = os.path.join(os.getcwd(), "red_teaming_results")
            os.makedirs(config_data["output_dir"], exist_ok=True)
            logger.info(f"No output directory specified. Using default: {config_data['output_dir']}")
            

        config = AttackConfig(**config_data)

        run_attacks(config)
