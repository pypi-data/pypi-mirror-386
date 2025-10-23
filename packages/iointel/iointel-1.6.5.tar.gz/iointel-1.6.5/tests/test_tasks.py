# tests/test_tasks.py
from iointel.src.workflow import Workflow


def test_tasks_chain_basic():
    """
    Ensure that calling chainable methods appends tasks correctly.
    """
    f = Workflow(objective="Sample text", client_mode=False)
    f.schedule_reminder(delay=10).sentiment()
    assert len(f.tasks) == 2

    assert f.tasks[0]["type"] == "schedule_reminder"
    assert f.tasks[0]["task_metadata"]["delay"] == 10
    assert f.tasks[1]["type"] == "sentiment"
    # We won't actually run tasks.run_tasks().
    # Instead, we just confirm the tasks are appended.


def test_tasks_custom():
    """
    Test that adding a custom step sets the correct fields.
    """
    flows = Workflow(objective="Analyze this text", client_mode=True)
    flows.custom(
        name="my-custom-step",
        objective="Custom objective",
        my_extra="something",
    )
    assert flows.objective == "Analyze this text"
    assert len(flows.tasks) == 1
    c = flows.tasks[0]
    assert c["type"] == "custom"
    assert c["objective"] == "Custom objective"
    assert c["task_metadata"]["name"] == "my-custom-step"
    assert c["task_metadata"]["kwargs"]["my_extra"] == "something"
