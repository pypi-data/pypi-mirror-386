import json
import os
from gc import enable
from typing import Any, Dict, List, Optional

import rich
from dateutil import parser

from wxo_agentic_evaluation import __file__
from wxo_agentic_evaluation.data_annotator import ERROR_KEYWORDS
from wxo_agentic_evaluation.llm_matching import LLMMatcher
from wxo_agentic_evaluation.llm_rag_eval import LLMJudge
from wxo_agentic_evaluation.llm_safety_eval import LLMSafetyJudge
from wxo_agentic_evaluation.metrics.evaluations import (
    Evaluation,
    Extractor,
    Metric,
)
from wxo_agentic_evaluation.metrics.llm_as_judge import (
    AnswerDerailment,
    AnswerUnsafeTopic,
)
from wxo_agentic_evaluation.metrics.metrics import (
    CustomEvalMetrics,
    KeywordSemanticSearchMetric,
    KnowledgeBaseMetrics,
    TextMatchType,
    ToolCallAndRoutingMetrics,
)
from wxo_agentic_evaluation.prompt.template_render import (
    AnswerRelevancyTemplateRenderer,
    DerailmentTemplateRenderer,
    FaithfulnessTemplateRenderer,
    KeywordMatchingTemplateRenderer,
    SemanticMatchingTemplateRenderer,
    UnsafeTopicTemplateRenderer,
)
from wxo_agentic_evaluation.resource_map import ResourceMap
from wxo_agentic_evaluation.service_instance import tenant_setup
from wxo_agentic_evaluation.service_provider import (
    USE_GATEWAY_MODEL_PROVIDER,
    get_provider,
)
from wxo_agentic_evaluation.service_provider.provider import Provider
from wxo_agentic_evaluation.type import (
    ContentType,
    ConversationalSearch,
    EvaluationData,
    EventTypes,
    ExtendedMessage,
    Message,
)

root_dir = os.path.dirname(__file__)
KEYWORD_MATCHING_PROMPT_PATH = os.path.join(
    root_dir, "prompt", "keyword_matching_prompt.jinja2"
)
SEMANTIC_MATCHING_PROMPT_PATH = os.path.join(
    root_dir, "prompt", "semantic_matching_prompt.jinja2"
)
FAITHFULNESS_PROMPT_PATH = os.path.join(
    root_dir, "prompt", "faithfulness_prompt.jinja2"
)
ANSWER_RELEVANCY_PROMPT_PATH = os.path.join(
    root_dir, "prompt", "answer_relevancy_prompt.jinja2"
)

RESERVED_KEYWORD_FOR_GROUND_TRUTH_ARGS = os.getenv(
    "RESERVED_KEYWORD_FOR_GROUND_TRUTH_ARGS", "<IGNORE>"
)

DERAILMENT_PROMPT_PATH = os.path.join(
    root_dir, "prompt", "derailment_prompt.jinja2"
)

UNSAFE_TOPIC_PROMPT_PATH = os.path.join(
    root_dir, "prompt", "unsafe_topic_prompt.jinja2"
)

"""
- hyphens are not allowed in python function names, so it is safe to use as a dummy function name
- purpose behind `DUMMY_GRAPH_NODE_NAME` is to append
a dummy node to the ground truth and the labelled messages to take into account 
single, summary step goals.
"""
DUMMY_GRAPH_NODE_NAME = "dummy-goal"


class EvaluationPackage:
    def __init__(
        self,
        test_case_name: str,
        ground_truth: EvaluationData,
        messages: list[Message],
        conversational_search_data: List[ConversationalSearch] = None,
        resource_map: ResourceMap = None,
        is_attack_evaluation: bool = False,
        config=None,
        custom_evals: Optional[list[Evaluation]] = None,
        custom_llmaaj_client: Optional[Provider] = None,
        extractors: Optional[list[Extractor]] = None,
        similarity_threshold=0.8,
        enable_fuzzy_matching=False,
    ):
        self.tool_dictionary = (
            {
                goal_detail.name: goal_detail
                for goal_detail in ground_truth.goal_details
                if goal_detail.type == ContentType.tool_call
            }
            if ground_truth.goal_details
            else {}
        )

        self.text_list = (
            [
                goal_detail
                for goal_detail in ground_truth.goal_details
                if goal_detail.type == ContentType.text
            ]
            if ground_truth.goal_details
            else []
        )

        self.messages: List[Message] = messages
        self.conversational_search_data = conversational_search_data
        self.is_attack_evaluation = is_attack_evaluation
        self.ground_truth = ground_truth
        self.test_case_name = test_case_name
        self.resource_map = resource_map
        self.custom_evals = custom_evals
        self.custom_llmaaj_client = custom_llmaaj_client
        self.extractors = extractors
        self.enable_fuzzy_matching = enable_fuzzy_matching

        if not self.is_attack_evaluation:
            self.validate_ground_truth(self.ground_truth, self.test_case_name)

        extra_kwargs = {}

        if USE_GATEWAY_MODEL_PROVIDER:

            if resource_map and hasattr(resource_map, "wxo_client"):
                wxo_client = resource_map.wxo_client

                if hasattr(wxo_client, "service_url"):
                    extra_kwargs["instance_url"] = wxo_client.service_url

                if hasattr(wxo_client, "api_key"):
                    extra_kwargs["token"] = wxo_client.api_key

            elif config:
                auth = getattr(config, "auth_config", None)

                if auth:
                    instance_url = getattr(auth, "url", None)
                    token = getattr(auth, "token", None)

                if instance_url:
                    extra_kwargs["instance_url"] = instance_url

                if token:
                    extra_kwargs["token"] = token
            else:
                token, instance_url, env = tenant_setup(
                    service_url=None, tenant_name="local"
                )
                if instance_url:
                    extra_kwargs["instance_url"] = instance_url

                if token:
                    extra_kwargs["token"] = token

        # output response matching
        self.matcher = LLMMatcher(
            llm_client=get_provider(
                model_id="meta-llama/llama-3-405b-instruct",
                params={
                    "min_new_tokens": 0,
                    "decoding_method": "greedy",
                    "max_new_tokens": 10,
                },
                embedding_model_id="sentence-transformers/all-minilm-l6-v2",
                **extra_kwargs,
            ),
            keyword_template=KeywordMatchingTemplateRenderer(
                KEYWORD_MATCHING_PROMPT_PATH
            ),
            semantic_template=SemanticMatchingTemplateRenderer(
                SEMANTIC_MATCHING_PROMPT_PATH
            ),
            similarity_threshold=similarity_threshold,
            enable_fuzzy_matching=enable_fuzzy_matching,
        )
        # only used for RAG evaluation
        self.rag_llm_as_a_judge = LLMJudge(
            llm_client=get_provider(
                model_id="meta-llama/llama-3-405b-instruct",
                params={
                    "min_new_tokens": 0,
                    "decoding_method": "greedy",
                    "max_new_tokens": 4096,
                },
                **extra_kwargs,
            ),
            faithfulness=FaithfulnessTemplateRenderer(FAITHFULNESS_PROMPT_PATH),
            answer_relevancy=AnswerRelevancyTemplateRenderer(
                ANSWER_RELEVANCY_PROMPT_PATH
            ),
        )
        self.safety_llm_as_a_judge = LLMSafetyJudge(
            llm_client=get_provider(
                model_id="meta-llama/llama-3-405b-instruct",
                params={
                    "min_new_tokens": 0,
                    "decoding_method": "greedy",
                    "max_new_tokens": 4096,
                },
                **extra_kwargs,
            ),
            answer_derailment=DerailmentTemplateRenderer(
                DERAILMENT_PROMPT_PATH
            ),
            answer_unsafe_topic=UnsafeTopicTemplateRenderer(
                UNSAFE_TOPIC_PROMPT_PATH
            ),
        )

    @staticmethod
    def find_ground_node(graph, start_node):
        """Simple implementation. Should be fixed in the future

        Assumes that there is a single graph node that does not have children
        """

        stack = [start_node]
        visited_set = set()

        while stack:
            node = stack.pop()
            if node not in visited_set:
                visited_set.add(node)

                # check for children
                # improvement for future: add the ground nodes here
                # right now, just return the first one
                if not graph.get(node):
                    return node

                stack.extend(graph[node])

        return None

    @staticmethod
    def is_topological_sort(graph, ordering):
        position = {node: i for i, node in enumerate(ordering)}
        ground_node = EvaluationPackage.find_ground_node(
            graph, list(graph.keys())[0]
        )

        if ground_node is not None:
            graph[ground_node] = [DUMMY_GRAPH_NODE_NAME]
            graph[DUMMY_GRAPH_NODE_NAME] = []

            next_idx = len(position)
            position[DUMMY_GRAPH_NODE_NAME] = next_idx

        for u in graph:
            for v in graph[u]:
                if u not in position or v not in position:
                    return False
                if position[u] >= position[v]:
                    return False
        return True

    @staticmethod
    def validate_ground_truth(ground_truth, test_case_name):
        if len(ground_truth.agent) == 0:
            raise ValueError(
                f"No agent provided in the ground truth. test_case_name: {test_case_name}"
            )

        if len(ground_truth.goals) == 0:
            raise ValueError(
                f"No goals provided in the ground truth. test_case_name: {test_case_name}"
            )

        if len(ground_truth.goal_details) == 0:
            raise ValueError(
                f"No goal details provided in the ground truth. test_case_name: {test_case_name}"
            )

        if len(ground_truth.story) == 0:
            raise ValueError(
                f"No story provided in the ground truth. test_case_name: {test_case_name}"
            )

        goals = set()

        for key, value in ground_truth.goals.items():
            goals.add(key)
            if isinstance(value, list):
                goals.update(value)
            else:
                raise ValueError(
                    f"The goal '{key}' is not mapping to a list: {value}. test_case_name: {test_case_name}"
                )

        for goal_detail in ground_truth.goal_details:
            if goal_detail.name not in goals:
                raise ValueError(
                    f"Goal detail '{goal_detail.name}' does not match any goals: {goals}. test_case_name: {test_case_name}"
                )
            if goal_detail.name == "summarize":
                if (
                    not goal_detail.keywords or len(goal_detail.keywords) == 0
                ) and (
                    not goal_detail.response or len(goal_detail.response) == 0
                ):
                    rich.print(
                        f"Summarize goal should have keywords or final response. test_case_name: {test_case_name}"
                    )
                elif len(goal_detail.response) == 0:
                    rich.print(
                        f"⚠️‼️ [bold][yellow] WARNING:[/yellow][/bold] Summarize goal has no final response. test_case_name: {test_case_name}"
                    )
        if len(ground_truth.goal_details) != len(goals):
            raise ValueError(
                f"Goal details count does not match the goals count: {len(ground_truth.goal_details)} != {len(goals)}. test_case_name: {test_case_name}"
            )

    def _print_kw_sm(
        self, keyword_semantic_match_list: List[KeywordSemanticSearchMetric]
    ):
        """Prints the keyword match/mismatch, and semantic match/mismatch results
        Right now only successful matches are printed
        """

        for keyword_semantic_match in keyword_semantic_match_list:
            if (
                keyword_semantic_match.semantic_match
                and keyword_semantic_match.keyword_match
            ):
                rich.print(
                    f"[green][SUCCESS] Text message matched: Summary - {keyword_semantic_match.message}[/green]"
                )

    @staticmethod
    def normalize_args(data):
        if isinstance(data, dict):
            # normalize keys (case-sensitive) and values
            return {
                str(k): EvaluationPackage.normalize_args(v)
                for k, v in data.items()
            }

        elif isinstance(data, list):
            normalized_list = [
                EvaluationPackage.normalize_args(v) for v in data
            ]
            return sorted(
                normalized_list, key=lambda v: json.dumps(v, sort_keys=True)
            )

        else:
            # don’t lowercase reserved keyword
            if str(data) == RESERVED_KEYWORD_FOR_GROUND_TRUTH_ARGS:
                return str(data)
            return str(data).lower()

    @staticmethod
    def _compare_as_date_or_number(normalized_actual, normalized_expected):
        """
        Attempts to compare two normalized values as dates or numbers.

        Args:
            normalized_actual: The actual value from tool call
            normalized_expected: The expected value from ground truth

        Returns:
            tuple: (conversion_succeeded, values_match)
                - conversion_succeeded: True if values could be converted to numbers or dates
                - values_match: True if converted values match
        """
        # Try to convert to numbers
        try:
            num_actual = float(normalized_actual)
            num_expected = float(normalized_expected)
            # Conversion succeeded, check if values match
            return (
                True,
                abs(num_actual - num_expected) <= 0.001,
            )  # Small epsilon for float comparison
        except (ValueError, TypeError):
            pass

        # Try to convert to dates
        try:
            date_actual = parser.parse(normalized_actual)
            date_expected = parser.parse(normalized_expected)
            # Conversion succeeded, check if values match
            return True, date_actual == date_expected
        except (ValueError, TypeError):
            pass

        # If we get here, neither number nor date conversion worked
        return False, False

    def _check_if_args_match_with_ignore(
        self,
        actual_args: dict[str, str],
        expected_args: dict[str, str],
        enable_fuzzy_matching: bool = False,
    ) -> bool:
        """
        This function checks if a registered tool call matches with the goal node when:
            - the arg value marked as wrong is labelled with the "<IGNORE>" value in the corresponding ground truth
        Args:
            actual_args (dict): Made during inference.
            expected_args (dict): Defined in the test case/ground truth.
        Returns:
            bool: True if match with keyword parameters ignored | False otherwise (arguments were not corrected).
        """
        if set(actual_args.keys()) != set(expected_args.keys()):
            return False

        ## now we go through and check each parameter
        for key in actual_args:
            normalized_actual = EvaluationPackage.normalize_args(
                actual_args[key]
            )
            normalized_expected = EvaluationPackage.normalize_args(
                expected_args[key]
            )

            # 1. If the args are an ignored keyword or exactly equal, continue to next parameter
            if (
                normalized_expected == RESERVED_KEYWORD_FOR_GROUND_TRUTH_ARGS
            ) or (normalized_actual == normalized_expected):
                continue
            else:
                # if they're not equal, and fuzzy matching is enabled, do fuzzy.
                if enable_fuzzy_matching:
                    # 3. Check date/number conversion
                    conversion_succeeded, values_match = (
                        EvaluationPackage._compare_as_date_or_number(
                            normalized_actual, normalized_expected
                        )
                    )
                    # If conversion succeeded and values match, continue to next parameter
                    if conversion_succeeded and values_match:
                        continue
                    # If conversion succeeded but values don't match, return False
                    if conversion_succeeded and not values_match:
                        return False
                    # 4. If conversion failed, try cosine matching. If this fails, return false for the function
                    if not self.matcher.cosine_similarity_semantic_match(
                        normalized_actual, normalized_expected
                    ):
                        return False
                else:
                    # If they're not equal and fuzzy matching is not enabled, return false
                    return False

        # If we've made it through all parameters without returning False, return True
        return True

    def traverse(self):
        labelled_messages = []
        message_outcomes = []
        labelled_messages_without_text_step = []
        # Counters for tool-calling related metrics
        tool_call_and_routing_metrics = ToolCallAndRoutingMetrics()
        tool_call_and_routing_metrics.expected_tool_calls = len(
            self.tool_dictionary
        )
        correct_tool_calls = (
            set()
        )  # sometimes, tool with the same signature can be called more than once
        for message in self.messages:
            if message.type == ContentType.tool_call:

                msg_tool_call = json.loads(message.content)
                if (
                    self.resource_map
                    and msg_tool_call["name"] in self.resource_map.agent2tools
                ):
                    tool_call_and_routing_metrics.total_routing_calls += 1
                    relevant = False
                    for tool in self.resource_map.agent2tools[
                        msg_tool_call["name"]
                    ]:
                        for goal_detail in self.tool_dictionary.values():
                            if goal_detail.tool_name == tool:
                                relevant = True
                                break
                        if relevant:
                            break

                    if relevant:
                        tool_call_and_routing_metrics.relevant_routing_calls += (
                            1
                        )
                    else:
                        message_outcome = ExtendedMessage(message=message)
                        message_outcome.reason = {
                            "reason": "irrelevant routing call",
                        }

                    continue

                # TO-DO: re-think how deduplication works in the context of precision & recall
                tool_call_and_routing_metrics.total_tool_calls += 1

                # evaluating more than once is fine
                # agent could make repeated calls with the same function signature
                # in our is_topological_sort algorithm, the most recent occurrence is evaluated
                matching_goal_details = [
                    goal_detail
                    for goal_detail in self.tool_dictionary.values()
                    if goal_detail.tool_name == msg_tool_call["name"]
                ]
                if len(matching_goal_details) > 0:
                    tool_call_and_routing_metrics.relevant_tool_calls += 1  # tool name matches one of the expected tool names, as defined in the ground truth
                    found = False
                    possible_ground_truth_for_analysis = []
                    for goal_detail in matching_goal_details:
                        # {"IGNORE": None} is set in red teaming attack ground truth to ignore parameter matching
                        if goal_detail.args == {"IGNORE": None} or (
                            EvaluationPackage.normalize_args(
                                msg_tool_call["args"]
                            )
                            == EvaluationPackage.normalize_args(
                                goal_detail.args
                            )
                            or self._check_if_args_match_with_ignore(
                                msg_tool_call["args"],
                                goal_detail.args,
                                enable_fuzzy_matching=self.enable_fuzzy_matching,
                            )  # TODO arjun-gupta1 9/29/25: make this also return the method of matching (llm, fuzzy, cosine similarity) so we can write it out to analyze_run.py results
                        ):
                            labelled_messages.append(goal_detail.name)
                            labelled_messages_without_text_step.append(
                                goal_detail.name
                            )
                            correct_tool_calls.add(goal_detail.name)
                            # tool_call_and_routing_metrics.correct_tool_calls += 1  # correct tool call (no erroneous response) + expected arguments, as defined in the ground truth
                            found = True
                            message_outcome = ExtendedMessage(message=message)
                            message_outcomes.append(message_outcome)
                            break
                        else:
                            possible_ground_truth_for_analysis.append(
                                goal_detail.args
                            )

                    if not found:
                        tool_call_and_routing_metrics.tool_calls_with_incorrect_parameter += (
                            1
                        )
                        message_outcome = ExtendedMessage(message=message)
                        message_outcome.reason = {
                            "reason": "incorrect parameter",
                            "actual": msg_tool_call["args"],
                            "expected": possible_ground_truth_for_analysis,
                        }
                        message_outcomes.append(message_outcome)
                        if not self.is_attack_evaluation:
                            rich.print(
                                f"[red][ERROR] Wrong parameters for function: {msg_tool_call['name']}. "
                                f"Expected one of {[g.args for g in matching_goal_details]}, Received={msg_tool_call['args']}[/red]"
                            )
                else:

                    if not self.is_attack_evaluation:
                        rich.print(
                            f"[yellow][WARNING] Unexpected function call: {msg_tool_call['name']}[/yellow]"
                        )
                    # note: this is incorrect after the 1.6 change
                    message_outcome = ExtendedMessage(message=message)
                    message_outcome.reason = {"reason": "irrelevant tool call"}
                    message_outcomes.append(message_outcome)

            elif message.type == ContentType.tool_response:
                found = False
                for keyword in ERROR_KEYWORDS:
                    if keyword in message.content.lower():
                        message_outcome = ExtendedMessage(message=message)
                        message_outcome.reason = {"reason": "runtime error"}
                        message_outcomes.append(message_outcome)
                        found = True
                        break
                if not found:
                    message_outcome = ExtendedMessage(message=message)
                    message_outcomes.append(message_outcome)
            else:
                message_outcome = ExtendedMessage(message=message)
                message_outcomes.append(message_outcome)

        tool_call_and_routing_metrics.correct_tool_calls = len(
            correct_tool_calls
        )

        assistant_responses = [
            message
            for message in self.messages
            if message.event == EventTypes.message_created
            and message.role == "assistant"
        ]

        keyword_semantic_list = []
        for message in assistant_responses:
            for goal_detail in self.text_list:
                if goal_detail.name not in labelled_messages:
                    keyword_match: bool = self.matcher.keywords_match(
                        message.content, goal_detail.keywords
                    )
                    semantic_match: bool = self.matcher.semantic_match(
                        self.messages[0].content,
                        prediction=message.content,
                        ground_truth=goal_detail.response,
                        enable_fuzzy_matching=self.enable_fuzzy_matching,
                    )
                    keyword_semantic_match = KeywordSemanticSearchMetric(
                        keyword_match=keyword_match,
                        semantic_match=semantic_match,
                        message=message.content,
                        goal_detail=goal_detail.name,
                    )
                    if keyword_match and semantic_match:
                        labelled_messages.append(goal_detail.name)
                        keyword_semantic_list.append(keyword_semantic_match)
                        break

        # only prints when the semantic and keyword matched
        self._print_kw_sm(keyword_semantic_list)

        return (
            labelled_messages,
            labelled_messages_without_text_step,
            keyword_semantic_list,
            tool_call_and_routing_metrics,
            message_outcomes,
        )

    def _is_text_match(
        self, keyword_semantic_match_list: List[KeywordSemanticSearchMetric]
    ):

        if len(self.text_list) == 0:
            return TextMatchType.na.value
        elif len(self.text_list) == len(keyword_semantic_match_list):
            return TextMatchType.text_match.value
        else:
            return TextMatchType.text_mismatch.value

    def generate_custom_metrics(
        self, extracted_context: Dict[str, Any]
    ) -> Optional[CustomEvalMetrics]:
        if self.custom_evals is None:
            return None

        results: list[Metric] = []
        for evaluation in self.custom_evals:
            # TODO: cleanup. The compute method returns a Metric but pydantic thinks it is different.
            # Probably because of some path issue when we auto-discover metrics
            evaluate_result = evaluation.evaluate(
                messages=self.messages,
                ground_truth=self.ground_truth,
                extracted_context=extracted_context,
            )
            if evaluate_result is not None:
                results.append(Metric(**evaluate_result.model_dump()))

        custom_eval_results = CustomEvalMetrics(
            dataset_name=self.test_case_name, custom_metrics=results
        )
        return custom_eval_results

    def generate_summary(self):
        llm_steps = 0
        total_step = 0
        metrics: ToolCallAndRoutingMetrics
        (
            labelled_messages,
            labelled_messages_without_text_step,
            matches,
            metrics,
            message_with_reasons,
        ) = self.traverse()

        extracted_context = {}
        if self.extractors is not None and self.custom_evals is not None:
            for extractor in self.extractors:
                context = extractor.extract(
                    messages=self.messages,
                    ground_truth=self.ground_truth,
                    matcher=self.matcher,
                )
                extracted_context[extractor.name] = context

        is_success = self.is_topological_sort(
            self.ground_truth.goals, labelled_messages
        )
        match = self._is_text_match(matches)

        for message in self.messages:
            if message.role == "assistant" and (
                message.type
                in (
                    ContentType.text,
                    ContentType.conversational_search,
                    ContentType.tool_call,
                )
            ):
                llm_steps += 1
            total_step += 1

        knowledge_base_metric_summary = (
            self.generate_knowledge_base_metric_summary()
        )

        custom_metric_summary = self.generate_custom_metrics(
            extracted_context=extracted_context
        )
        # TO-DO: the table is not printing properly anymore with the new columns introduced
        # we need to introduce a separate table for these.

        metrics.total_steps = total_step
        metrics.llm_step = llm_steps
        metrics.text_match = match
        metrics.is_success = is_success

        return (
            matches,
            knowledge_base_metric_summary,
            message_with_reasons,
            metrics,
            custom_metric_summary,
        )

    def _get_messages_by_role_before_cs(
        self, idx_conversational_search: int, role: str, type: str = "text"
    ):
        """Utility method to filter `self.messages` for messages with a given role
        that occur before the conversational search message index
        """

        filtered_messages = [
            message
            for idx, message in enumerate(self.messages)
            if idx < idx_conversational_search
            and message.role == role
            and message.type == type
        ]

        return filtered_messages

    def _weave_user_assistant_messages(self, user_messages, assistant_messages):
        weave = []
        for user, assistant in zip(user_messages, assistant_messages):
            msg = f"User: {user.content}\nAssistant: {assistant.content}\n\n"
            weave.append(msg)

        return " ".join(weave)

    def _find_tool_call_name(self, tool_call_id):
        for message in self.messages:
            if message.type == ContentType.tool_call:
                content = json.loads(message.content)
                """
                - In ADK 1.9, for tool call events, the "tool_call_id" is now "id"
                - still parse out "tool_call_id" for backwards compatibility
                """
                id = content.get("tool_call_id") or content.get("id")
                if id == tool_call_id:
                    return content.get("name")

        raise Exception(f"'{tool_call_id}' not found in messages")

    def generate_knowledge_base_metric_summary(self) -> KnowledgeBaseMetrics:
        idx_conv_search = [
            idx
            for idx, message in enumerate(self.messages)
            if message.type == ContentType.conversational_search
        ]
        metrics = []

        for search_index in idx_conv_search:
            user_messages = self._get_messages_by_role_before_cs(
                role="user", idx_conversational_search=search_index
            )
            assistant_messages = self._get_messages_by_role_before_cs(
                role="assistant",
                idx_conversational_search=search_index,
                type=ContentType.text,
            )

            context = self._weave_user_assistant_messages(
                user_messages, assistant_messages
            )
            most_recent_user_message = user_messages[-1]
            search_message = self.messages[search_index]

            # find the conversational search metadata associated with this message
            conversational_search_data = None
            if self.conversational_search_data:
                for cs_metadata in self.conversational_search_data:
                    if (
                        search_message.conversational_search_metadata.tool_call_id
                        == cs_metadata.metadata.tool_call_id
                    ):
                        conversational_search_data = cs_metadata

            tool_name = self._find_tool_call_name(
                conversational_search_data.metadata.tool_call_id
            )  # name of knowledge base

            search_results = [
                result.body
                for result in conversational_search_data.search_results
            ]
            faithfulness = self.rag_llm_as_a_judge.faithfulness(
                conversational_search_data.text, search_results
            )
            answer_relevancy = self.rag_llm_as_a_judge.answer_relevancy(
                question=most_recent_user_message.content,
                context=context,
                answer=search_message.content,
            )
            knowledge_base_metrics = KnowledgeBaseMetrics(
                dataset_name=self.test_case_name,
                knowledge_base_name=tool_name,
                tool_call_id=search_message.conversational_search_metadata.tool_call_id,
                faithfulness=faithfulness,
                answer_relevancy=answer_relevancy,
                confidence_scores=conversational_search_data.confidence_scores,
            )

            metrics.append(knowledge_base_metrics)

        return metrics

    def evaluate_derailment(
        self, instructions: str = None
    ) -> List[AnswerDerailment]:
        derailments = []
        last_user_message = None
        for message in self.messages:
            if message.role == "user" and message.type == ContentType.text:
                last_user_message = message
            if message.role == "assistant" and message.type == ContentType.text:
                derailment = (
                    self.safety_llm_as_a_judge.judge_derailment_in_answer(
                        question=last_user_message.content,
                        instructions=instructions if instructions else "N/A",
                        answer=message.content,
                    )
                )
                derailments.append(derailment)
                if derailment.in_scope == "no":
                    return (
                        derailments  # short-circuit if any derailment is found
                    )
        return derailments

    def evaluate_unsafe_topics(
        self, instructions: str = None
    ) -> List[AnswerUnsafeTopic]:
        unsafe_topics = []
        last_user_message = None
        for message in self.messages:
            if message.role == "user" and message.type == ContentType.text:
                last_user_message = message
            if message.role == "assistant" and message.type == ContentType.text:
                unsafe_topic = (
                    self.safety_llm_as_a_judge.judge_unsafe_topic_in_answer(
                        question=last_user_message.content,
                        instructions=instructions if instructions else "N/A",
                        answer=message.content,
                    )
                )
                unsafe_topics.append(unsafe_topic)
                if unsafe_topic.is_safe == "no":
                    return unsafe_topics  # short-circuit if any unsafe topic is found

        return unsafe_topics


if __name__ == "__main__":

    messages = []

    with open(
        "./benchmarks/workday_tools/concise/result/llama/messages/data18.messages.json",
        "r",
        encoding="utf-8",
    ) as f:

        temp = json.load(f)

        for message in temp:
            messages.append(Message.model_validate(message))

    for message in messages:
        if message.role == "user":
            rich.print(
                "[yellow]GENERATED_USER_MESSAGE:[/yellow]", message.content
            )
        else:
            rich.print("[orange3]WXO:[/orange3]", message.content)

    with open("./benchmarks/workday_tools/data/data18.json", "r") as f:
        ground_truth = EvaluationData.model_validate(json.load(f))

    evaluate_package = EvaluationPackage(
        test_case_name="data1.messages.json",
        ground_truth=ground_truth,
        messages=messages,
    )
    print(evaluate_package.generate_summary())
    # print(evaluate_package.traverse())
