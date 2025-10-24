from . import graph


@graph
def cyclic1():
    graph = {"id": "cyclic1", "label": "cyclic1", "schema_version": "1.1"}

    task = "ewokscore.tests.examples.tasks.condsumtask.CondSumTask"
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task3",
            "default_inputs": [{"name": "b", "value": 3}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task4",
            "default_inputs": [{"name": "b", "value": -1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task5",
            "default_inputs": [{"name": "b", "value": -1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task6",
            "default_inputs": [{"name": "b", "value": 0}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task7",
            "default_inputs": [{"name": "b", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task2",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task2",
            "target": "task3",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task3",
            "target": "task4",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task4",
            "target": "task2",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
            "conditions": [{"source_output": "too_small", "value": True}],
        },
        {
            "source": "task4",
            "target": "task5",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
            "conditions": [{"source_output": "too_small", "value": False}],
        },
        {
            "source": "task5",
            "target": "task6",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task6",
            "target": "task2",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
            "conditions": [{"source_output": "too_small", "value": True}],
        },
        {
            "source": "task6",
            "target": "task7",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
            "conditions": [{"source_output": "too_small", "value": False}],
        },
    ]

    expected = {"task7": {"result": 12, "too_small": False}}

    taskgraph = {"graph": graph, "links": links, "nodes": nodes}

    return taskgraph, expected
