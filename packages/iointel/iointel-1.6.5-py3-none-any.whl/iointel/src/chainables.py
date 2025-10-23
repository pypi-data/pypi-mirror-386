from typing import List, Optional, Dict

# from .task import CUSTOM_WORKFLOW_REGISTRY
from .utilities.runners import run_agents
from .utilities.decorators import register_custom_task
from .utilities.registries import CHAINABLE_METHODS, CUSTOM_WORKFLOW_REGISTRY
from .agents import Agent

##############################################
# Example Executor Functions
##############################################
"""
The executor functions below are examples of how to implement custom tasks.
These functions are registered with the @register_custom_task decorator.
The decorator takes a string argument that is the name of the custom task.
The function should take the following arguments:
    - task_metadata: A dictionary of metadata for the task. This can include any additional information needed for the task.
    - objective: The text to process. This is the input to the task.
    - agents: A list of agents to use for the task. These agents can be used to run sub-tasks.
    - execution_metadata: A dictionary of metadata for the execution. This can include any additional information needed for the execution like client mode, etc.

"""


@register_custom_task("schedule_reminder")
def execute_schedule_reminder(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from ..client.client import schedule_task

    client_mode = execution_metadata.get("client_mode", False)
    if client_mode:
        return schedule_task(command=objective)
    else:
        response = run_agents(
            objective="Schedule a reminder",
            instructions="Schedule a reminder and track the time.",
            agents=agents,
            context={"command": objective},
            output_type=str,
        )
        return response.execute()


@register_custom_task("solve_with_reasoning")
async def execute_solve_with_reasoning(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from .agent_methods.prompts.instructions import REASONING_INSTRUCTIONS
    from .agent_methods.data_models.datamodels import ReasoningStep

    client_mode = execution_metadata.get("client_mode", False)
    if client_mode:
        from ..client.client import run_reasoning_task

        return run_reasoning_task(objective)
    else:
        # For example, loop until a validated solution is found.
        while True:
            response: ReasoningStep = await run_agents(
                objective=REASONING_INSTRUCTIONS,
                output_type=ReasoningStep,
                agents=agents,
                context={"goal": objective},
            ).execute()
            if response.found_validated_solution:
                # Optionally, double-check the solution.
                if run_agents(
                    objective="""
                            Check your solution to be absolutely sure that it is correct and meets all requirements of the goal. Return True if it does.
                            """,
                    output_type=bool,
                    context={"goal": objective},
                    agents=agents,
                ).execute():
                    return response.proposed_solution


@register_custom_task("summarize_text")
def execute_summarize_text(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from ..client.client import summarize_task
    from .agent_methods.data_models.datamodels import SummaryResult

    max_words = task_metadata.get("max_words")
    client_mode = execution_metadata.get("client_mode", False)
    if client_mode:
        return summarize_task(text=objective, max_words=max_words)
    else:
        summary = run_agents(
            objective=f"Summarize the given text: {objective}\n into no more than {max_words} words and list key points",
            output_type=SummaryResult,
            # context={"text": text},
            agents=agents,
        )
        return summary.execute()


@register_custom_task("sentiment")
async def execute_sentiment(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from ..client.client import sentiment_analysis

    client_mode = execution_metadata.get("client_mode", False)

    if client_mode:
        return sentiment_analysis(text=objective)
    else:
        sentiment_val = await run_agents(
            objective=f"Classify the sentiment of the text as a value between 0 and 1.\nText: {objective}",
            agents=agents,
            output_type=float,
            # result_validator=between(0, 1),
            # context={"text": text},
        ).execute()
        if not isinstance(sentiment_val, float):
            try:
                return float(sentiment_val)
            except ValueError:
                pass
        return sentiment_val


@register_custom_task("extract_categorized_entities")
def execute_extract_entities(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from ..client.client import extract_entities

    client_mode = execution_metadata.get("client_mode", False)
    if client_mode:
        return extract_entities(text=objective)
    else:
        extracted = run_agents(
            objective=f"""from this text: {objective}

                        Extract named entities from the text above and categorize them,
                            Return a JSON dictionary with the following keys:
                            - 'persons': List of person names
                            - 'organizations': List of organization names
                            - 'locations': List of location names
                            - 'dates': List of date references
                            - 'events': List of event names
                            Only include keys if entities of that type are found in the text.
                            """,
            agents=agents,
            output_type=Dict[str, List[str]],
            # context={"text": text},
        )
        return extracted.execute()


@register_custom_task("translate_text")
def execute_translate_text(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    target_lang = task_metadata["target_language"]
    from ..client.client import translate_text_task

    client_mode = execution_metadata.get("client_mode", False)
    if client_mode:
        return translate_text_task(text=objective, target_language=target_lang)
    else:
        translated = run_agents(
            objective=f"Translate the given text:{objective} into {target_lang}",
            # output_type=TranslationResult,
            # context={"text": text, "target_language": target_lang},
            agents=agents,
        )
        result = translated.execute()
        # Assuming the model has an attribute 'translated'
        return result


@register_custom_task("classify")
def execute_classify(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from ..client.client import classify_text

    client_mode = execution_metadata.get("client_mode", False)
    classify_by = task_metadata.get("classify_by")

    if client_mode:
        return classify_text(text=objective, classify_by=classify_by)
    else:
        classification = run_agents(
            objective=f"""Take this text: {objective}

            Classify it into the appropriate category.
            Category must be one of: {", ".join(classify_by)}.
            Return only the determined category, omit the thoughts.""",
            agents=agents,
            output_type=str,
            # context={"text": text},
        )
        return classification.execute()


@register_custom_task("moderation")
async def execute_moderation(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    from .agent_methods.data_models.datamodels import (
        ViolationActivation,
        ModerationException,
    )
    from ..client.client import moderation_task

    client_mode = execution_metadata.get("client_mode", False)
    threshold = task_metadata["threshold"]

    if client_mode:
        result = moderation_task(text=objective, threshold=threshold)
        # Raise exceptions based on result thresholds if necessary.
        return result
    else:
        result: ViolationActivation = await run_agents(
            objective=f" from the text: {objective}:\n Check the text for violations and return activation levels",
            agents=agents,
            output_type=ViolationActivation,
            # context={"text": text},
        ).execute()

        if result["extreme_profanity"] > threshold:
            raise ModerationException("Extreme profanity detected", violations=result)
        elif result["sexually_explicit"] > threshold:
            raise ModerationException(
                "Sexually explicit content detected", violations=result
            )
        elif result["hate_speech"] > threshold:
            raise ModerationException("Hate speech detected", violations=result)
        elif result["harassment"] > threshold:
            raise ModerationException("Harassment detected", violations=result)
        elif result["self_harm"] > threshold:
            raise ModerationException("Self harm detected", violations=result)
        elif result["dangerous_content"] > threshold:
            raise ModerationException("Dangeme profanity detected", violations=result)

        return result


@register_custom_task("custom")
def execute_custom(
    task_metadata: dict, objective: str, agents: List[Agent], execution_metadata: dict
):
    client_mode = execution_metadata.get("client_mode", False)
    name = task_metadata["name"]

    if name in CUSTOM_WORKFLOW_REGISTRY:
        custom_fn = CUSTOM_WORKFLOW_REGISTRY[name]
        result = custom_fn(task_metadata, run_agents, objective)
        if hasattr(result, "execute") and callable(result.execute):
            result = result.execute()
        return result
    else:
        if client_mode:
            from ..client.client import custom_workflow

            return custom_workflow(
                name=name,
                objective=objective,
                agents=agents,
                context=task_metadata.get("kwargs", {}),
            )
        else:
            response = run_agents(
                name=name,
                objective=objective,
                agents=agents,
                context=task_metadata.get("kwargs", {}),
                output_type=str,
            )
            return response.execute()


##############################################
# CHAINABLES
##############################################
"""
The chainable methods below are used to chain tasks together in a workflow.
Each method takes a 'self' argument, which is the task object being chained.
The method should return the 'self' object with the task appended to the 'tasks' list.
The 'tasks' list is used to store the tasks in the workflow.

"""


def schedule_reminder(self, delay: int = 0, agents: Optional[List[Agent]] = None):
    # WIP
    self.tasks.append(
        {
            "type": "schedule_reminder",
            "command": self.objective,
            "task_metadata": {"delay": delay},
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


def solve_with_reasoning(self, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "solve_with_reasoning",
            "objective": self.objective,
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


def summarize_text(self, max_words: int = 100, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "summarize_text",
            "objective": self.objective,
            "agents": self.agents if agents is None else agents,
            "task_metadata": {"max_words": max_words},
        }
    )
    return self


def sentiment(self, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "sentiment",
            "objective": self.objective,
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


def extract_categorized_entities(self, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "extract_categorized_entities",
            "objective": self.objective,
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


def translate_text(self, target_language: str, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "translate_text",
            "objective": self.objective,
            "task_metadata": {"target_language": target_language},
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


def classify(self, classify_by: list, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "classify",
            "task_metadata": {"classify_by": classify_by},
            "objective": self.objective,
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


def moderation(self, threshold: float, agents: Optional[List[Agent]] = None):
    self.tasks.append(
        {
            "type": "moderation",
            "objective": self.objective,
            "task_metadata": {"threshold": threshold},
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


# def custom(self, name: str, objective: str, agents: Optional[List[Agent]] = None, instructions: str = "", **kwargs):
def custom(
    self, name: str, objective: str, agents: Optional[List[Agent]] = None, **kwargs
):
    """
    Allows users to define a custom workflow (or step) that can be chained
    like the built-in tasks. 'name' can help identify the custom workflow
    in run_tasks().

    :param name: Unique identifier for this custom workflow step.
    :param objective: The main objective or prompt for run_agents.
    :param agents: List of agents used (if None, a default can be used).
    :param kwargs: Additional data needed for this custom workflow.
    """
    self.tasks.append(
        {
            "type": "custom",
            "objective": objective,
            "task_metadata": {"name": name, "kwargs": kwargs},
            "agents": self.agents if agents is None else agents,
        }
    )
    return self


# Dictionary mapping method names to functions
CHAINABLE_METHODS.update(
    {
        "schedule_reminder": schedule_reminder,
        "solve_with_reasoning": solve_with_reasoning,
        "summarize_text": summarize_text,
        "sentiment": sentiment,
        "extract_categorized_entities": extract_categorized_entities,
        "translate_text": translate_text,
        "classify": classify,
        "moderation": moderation,
        "custom": custom,
    }
)
