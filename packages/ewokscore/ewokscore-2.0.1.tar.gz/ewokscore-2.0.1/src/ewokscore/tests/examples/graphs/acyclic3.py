from ewokscore import missing_data

from . import graph


@graph
def acyclic3():
    graph = {"id": "acyclic3", "label": "acyclic3", "schema_version": "1.1"}

    task = "ewokscore.tests.examples.tasks.sumtask.SumTask"
    nodes = [
        {
            "id": "task1",
            "default_inputs": [{"name": "a", "value": 1}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task2",
            "default_inputs": [{"name": "a", "value": 2}],
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
            "default_inputs": [{"name": "b", "value": 4}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task5",
            "default_inputs": [{"name": "b", "value": 5}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task6",
            "default_inputs": [{"name": "b", "value": 6}],
            "task_type": "class",
            "task_identifier": task,
        },
        {
            "id": "task7",
            "task_type": "class",
            "task_identifier": "ewokscore.tests.examples.tasks.nooutputtask.NoOutputTask",
        },
        {
            "id": "task8",
            "task_type": "class",
            "task_identifier": "ewokscore.tests.examples.tasks.nooutputtask.NoOutputTask",
        },
    ]

    links = [
        {
            "source": "task1",
            "target": "task3",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task2",
            "target": "task4",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task3",
            "target": "task5",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task4",
            "target": "task5",
            "data_mapping": [{"target_input": "b", "source_output": "result"}],
        },
        {
            "source": "task5",
            "target": "task6",
            "data_mapping": [{"source_output": "result", "target_input": "a"}],
        },
        {
            "source": "task6",
            "target": "task7",
            "map_all_data": True,
        },
        {
            "source": "task7",
            "target": "task8",
        },
    ]

    taskgraph = {"graph": graph, "links": links, "nodes": nodes}

    expected_results = {
        "task1": {"result": 1},
        "task2": {"result": 2},
        "task3": {"result": 4},
        "task4": {"result": 6},
        "task5": {"result": 10},
        "task6": {"result": 16},
        "task7": missing_data.MISSING_DATA,
        "task8": missing_data.MISSING_DATA,
    }

    return taskgraph, expected_results
