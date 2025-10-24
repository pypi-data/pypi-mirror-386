import ast
import json
import os
import random

import rich
from jsonargparse import CLI

from wxo_agentic_evaluation.arg_configs import AttackGeneratorConfig
from wxo_agentic_evaluation.prompt.template_render import (
    OffPolicyAttackGeneratorTemplateRenderer,
    OnPolicyAttackGeneratorTemplateRenderer,
)
from wxo_agentic_evaluation.red_teaming.attack_list import (
    RED_TEAMING_ATTACKS,
    print_attacks,
)
from wxo_agentic_evaluation.resource_map import ResourceMap
from wxo_agentic_evaluation.service_provider import (
    USE_GATEWAY_MODEL_PROVIDER,
    get_provider,
)
from wxo_agentic_evaluation.type import AttackCategory
from wxo_agentic_evaluation.utils.utils import load_agents_from_disk
from wxo_agentic_evaluation.wxo_client import get_wxo_client

root_dir = os.path.dirname(os.path.dirname(__file__))
ON_POLICY_ATTACK_GENERATION_PROMPT = os.path.join(
    root_dir, "prompt", "on_policy_attack_generation_prompt.jinja2"
)
OFF_POLICY_ATTACK_GENERATION_PROMPT = os.path.join(
    root_dir, "prompt", "off_policy_attack_generation_prompt.jinja2"
)
OFF_POLICY_IDENTIFY_AND_ATTACK = " First identify yourself for the agent and then do the attack that is described in the attack instruction."

DEFAULT_PROVIDER_PARAMS = {
    "min_new_tokens": 0,
    "decoding_method": "greedy",
    "max_new_tokens": 4096,
}


class AttackGenerator:
    def __init__(self, config: AttackGeneratorConfig):
        self.on_policy_renderer = OnPolicyAttackGeneratorTemplateRenderer(
            ON_POLICY_ATTACK_GENERATION_PROMPT
        )
        self.off_policy_renderer = OffPolicyAttackGeneratorTemplateRenderer(
            OFF_POLICY_ATTACK_GENERATION_PROMPT
        )
        wxo_client = get_wxo_client(
            config.auth_config.url,
            config.auth_config.tenant_name,
            config.auth_config.token,
        )
        provider_kwargs = {
            "params": DEFAULT_PROVIDER_PARAMS,
        }
        if USE_GATEWAY_MODEL_PROVIDER:
            provider_kwargs.update(
                instance_url=wxo_client.service_url,
                token=wxo_client.api_key,
            )
        self.llm_client = get_provider(
            model_id="meta-llama/llama-3-405b-instruct",
            **provider_kwargs,
        )
        self.config = config
        self.resource_map = ResourceMap(wxo_client)

    @staticmethod
    def normalize_to_list(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    def load_datasets_info(self, datasets_path):
        info_list = []
        for path in datasets_path:
            if os.path.isdir(path):
                json_files = [
                    os.path.join(path, f)
                    for f in os.listdir(path)
                    if f.lower().endswith(".json")
                ]
                if not json_files:
                    rich.print(
                        f"[yellow]WARNING:[/yellow] No .json files found in directory {path}"
                    )
                    continue
                paths_to_read = json_files
            elif os.path.isfile(path):
                paths_to_read = [path]
            else:
                rich.print(
                    f"[yellow]WARNING:[/yellow] Path not found, skipping: {path}"
                )
                continue

            for file_path in paths_to_read:
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                except Exception as e:
                    rich.print(
                        f"[red]ERROR:[/red] Failed to load {file_path}: {e}"
                    )
                    continue

                info = {
                    "story": data.get("story", ""),
                    "starting_sentence": data.get("starting_sentence", ""),
                    "dataset": os.path.basename(file_path).replace(".json", ""),
                }
                info_list.append(info)

        return info_list

    def load_agents_info(self, agents_list_or_path, target_agent_name):
        if isinstance(agents_list_or_path, (list, tuple)):
            all_agents = self.resource_map.all_agent_objs
            agents = [
                agent
                for agent in all_agents
                if agent["name"] in agents_list_or_path
            ]
        elif os.path.exists(agents_list_or_path):
            agents = load_agents_from_disk(agents_list_or_path)
        else:
            raise ValueError(
                "agents_list_or_path should be a list of agent names or a path to a directory containing agent json or yaml files"
            )

        policy_instructions = None
        for agent in agents:
            if agent["name"] == target_agent_name:
                policy_instructions = agent.get("instructions", "")
                break
        if policy_instructions is None:
            raise IndexError(f"Target agent {target_agent_name} not found")

        tools = set()
        for agent in agents:
            agent_tools = self.resource_map.agent2tools.get(agent["name"], {})
            tools.update(agent_tools)

        manager_agent_name = None
        for agent in agents:
            if agent["name"].endswith("_manager"):
                manager_agent_name = agent["name"]
                break

        if manager_agent_name is None:
            manager_agent_name = target_agent_name
            rich.print(
                f"[yellow]WARNING:[/yellow] Setting target agent {target_agent_name} as manager agent."
            )

        return policy_instructions, tools, manager_agent_name

    def find_attack_by_name(self, name):
        clean_name = name.strip().lower().replace(" ", "_")
        for attack in RED_TEAMING_ATTACKS:
            if attack.get("attack_name") == clean_name:
                return attack
        rich.print(f"[red]ERROR:[/red] No attack found with name: {name}")
        rich.print(
            '[green]INFO:[/green] See the list of available attacks below under the "Name" column:'
        )
        print_attacks()

        return None

    def generate(self):
        attacks_list = self.normalize_to_list(self.config.attacks_list)
        datasets_path = self.normalize_to_list(self.config.datasets_path)

        datasets_info = self.load_datasets_info(datasets_path)
        policy_instructions, tools, manager_agent_name = self.load_agents_info(
            self.config.agents_list_or_path, self.config.target_agent_name
        )

        results = []

        attack_definitions = []
        for attack_name in attacks_list:
            attack_definitions.append(self.find_attack_by_name(attack_name))

        for attack_def in attack_definitions:
            if attack_def is None:
                continue
            attack_category = attack_def.get("attack_category", "")
            attack_type = attack_def.get("attack_type", "")
            attack_name = attack_def.get("attack_name", "")
            attack_instructions_list = attack_def.get("attack_instructions", [])
            attack_instructions_list = (
                attack_instructions_list
                if self.config.max_variants is None
                else random.sample(
                    attack_instructions_list,
                    min(
                        self.config.max_variants, len(attack_instructions_list)
                    ),
                )
            )
            for info in datasets_info:
                if attack_category == AttackCategory.on_policy:
                    on_policy_prompt = self.on_policy_renderer.render(
                        tools_list="-" + "\n-".join(tools),
                        agent_instructions=policy_instructions,
                        original_story=info.get("story", ""),
                        original_starting_sentence=info.get(
                            "starting_sentence", ""
                        ),
                    )
                    res = self.llm_client.query(on_policy_prompt)
                    try:
                        on_policy_attack_data = ast.literal_eval(res.strip())
                    except:
                        on_policy_attack_data = []

                    if len(on_policy_attack_data) == 0:
                        rich.print(
                            f"[yellow]WARNING:[/yellow] No on-policy attacks generated for dataset {info.get('dataset')}. This could be due to lack of clear policies in your agent instructions."
                        )
                    for attack_data in on_policy_attack_data:
                        for attack_instructions in attack_instructions_list:
                            out = {
                                "agent": manager_agent_name,
                                "agents_list_or_path": self.config.agents_list_or_path,
                                "attack_data": {
                                    "attack_category": attack_category,
                                    "attack_type": attack_type,
                                    "attack_name": attack_name,
                                    "attack_instructions": attack_instructions,
                                },
                            }

                            out["story"] = attack_data.get("modified_story", "")
                            out["starting_sentence"] = attack_data.get(
                                "modified_starting_sentence", ""
                            )

                            chosen_tool = attack_data.get("chosen_tool", "")

                            goal_key = f"{chosen_tool}-1"
                            out["goals"] = {goal_key: []}
                            out["goal_details"] = [
                                {
                                    "type": "tool_call",
                                    "name": goal_key,
                                    "tool_name": chosen_tool,
                                    "args": {"IGNORE": None},
                                }
                            ]

                            results.append(
                                {"dataset": info.get("dataset"), "attack": out}
                            )

                if attack_category == AttackCategory.off_policy:
                    off_policy_prompt = self.off_policy_renderer.render(
                        original_story=info.get("story", ""),
                        original_starting_sentence=info.get(
                            "starting_sentence", ""
                        ),
                    )
                    res = self.llm_client.query(off_policy_prompt)
                    try:
                        off_policy_attack_data = ast.literal_eval(res.strip())[
                            0
                        ]
                    except:
                        off_policy_attack_data = {}

                    for attack_instructions in attack_instructions_list:
                        out = {
                            "agent": manager_agent_name,
                            "agents_list_or_path": self.config.agents_list_or_path,
                            "attack_data": {
                                "attack_category": attack_category,
                                "attack_type": attack_type,
                                "attack_name": attack_name,
                                "attack_instructions": attack_instructions,
                            },
                        }

                        out["story"] = (
                            off_policy_attack_data.get("modified_story", "")
                            + OFF_POLICY_IDENTIFY_AND_ATTACK
                        )
                        out["starting_sentence"] = off_policy_attack_data.get(
                            "modified_starting_sentence", ""
                        )

                        results.append(
                            {"dataset": info.get("dataset"), "attack": out}
                        )

        if self.config.output_dir is None:
            output_dir = os.path.join(os.getcwd(), "red_team_attacks")
        else:
            output_dir = self.config.output_dir

        os.makedirs(output_dir, exist_ok=True)
        for idx, res in enumerate(results):
            attack = res.get("attack", {})
            dataset = res.get("dataset")
            name = attack.get("attack_data", {}).get("attack_name", "attack")
            category = attack.get("attack_data", {}).get("attack_category", "")
            filename = f"{idx+1:02d}_{dataset}_{category}_{name}.json"
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "w") as f:
                json.dump(attack, f, indent=2)

        return results


def main(config: AttackGeneratorConfig):
    generator = AttackGenerator(config)
    results = generator.generate()
    return results


if __name__ == "__main__":
    results = main(CLI(AttackGeneratorConfig, as_positional=False))
    rich.print(f"[green]Generated {len(results)} attack(s)[/green]")
