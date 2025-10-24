from ewoksutils.import_utils import qualname

from ewokscore import Task
from ewokscore import execute_graph


class SumTask(
    Task,
    input_names=["a"],
    optional_input_names=["b"],
    output_names=["result", "inputs", "label"],
):
    def run(self):
        result = self.inputs.a
        if self.inputs.b:
            result += self.inputs.b
        self.outputs.result = result
        self.outputs.inputs = {k: v for k, v in self.get_input_values().items() if v}
        self.outputs.label = self.label


def create_graph():
    task = qualname(SumTask)
    graph = {"id": "testgraph", "schema_version": "1.1"}
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
            "data_mapping": [{"source_output": "result", "target_input": "b"}],
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
    ]

    return {"graph": graph, "links": links, "nodes": nodes}


def test_execute_graph_outputs():
    # All task instances
    results = execute_graph(create_graph(), output_tasks=True)
    results = {k: v.get_output_values() for k, v in results.items()}
    expected = {
        "task1": {"inputs": {"a": 1}, "result": 1, "label": "task1"},
        "task3": {"inputs": {"a": 1, "b": 3}, "result": 4, "label": "task3"},
        "task2": {"inputs": {"a": 2}, "result": 2, "label": "task2"},
        "task4": {"inputs": {"a": 2, "b": 4}, "result": 6, "label": "task4"},
        "task5": {"inputs": {"a": 4, "b": 6}, "result": 10, "label": "task5"},
        "task6": {"inputs": {"a": 10, "b": 6}, "result": 16, "label": "task6"},
        "task7": {},
    }
    assert results == expected

    # The results of all tasks
    results = execute_graph(
        create_graph(), outputs=[{"all": True}], merge_outputs=False
    )
    assert results == expected

    # Merge the results of all tasks
    results = execute_graph(create_graph(), outputs=[{"all": True}])
    expected = {"inputs": {"a": 10, "b": 6}, "result": 16, "label": "task6"}
    assert results == expected

    # The results of selected tasks
    results = execute_graph(
        create_graph(), outputs=[{"id": "task5"}], merge_outputs=False
    )
    expected = {"task5": {"inputs": {"a": 4, "b": 6}, "result": 10, "label": "task5"}}
    assert results == expected

    # Merge the results of selected tasks
    results = execute_graph(create_graph(), outputs=[{"id": "task5"}])
    expected = {"inputs": {"a": 4, "b": 6}, "result": 10, "label": "task5"}
    assert results == expected

    # The results of selected tasks
    results = execute_graph(
        create_graph(),
        outputs=[
            {"id": "task1", "name": "inputs"},
            {"id": "task4", "name": "result"},
        ],
        merge_outputs=False,
    )
    expected = {"task1": {"inputs": {"a": 1}}, "task4": {"result": 6}}
    assert results == expected

    # Merge the results of selected tasks
    results = execute_graph(
        create_graph(),
        outputs=[
            {"id": "task1", "name": "inputs"},
            {"id": "task4", "name": "result"},
        ],
    )
    expected = {"inputs": {"a": 1}, "result": 6}
    assert results == expected

    # The results of selected tasks
    results = execute_graph(
        create_graph(),
        outputs=[
            {"id": "task1", "name": "inputs", "new_name": "a"},
            {"id": "task4", "name": "result"},
        ],
        merge_outputs=False,
    )
    expected = {"task1": {"a": {"a": 1}}, "task4": {"result": 6}}
    assert results == expected

    # Merge the results of selected tasks
    results = execute_graph(
        create_graph(),
        outputs=[
            {"id": "task1", "name": "inputs", "new_name": "a"},
            {"id": "task4", "name": "result"},
        ],
    )
    expected = {"a": {"a": 1}, "result": 6}
    assert results == expected


def test_execute_graph_inputs():
    results = execute_graph(
        create_graph(),
        inputs=[{"id": "task1", "name": "b", "value": 1}],
        output_tasks=True,
    )
    results = {k: v.get_output_values() for k, v in results.items()}
    expected = {
        "task1": {"inputs": {"a": 1, "b": 1}, "result": 2, "label": "task1"},
        "task3": {"inputs": {"a": 2, "b": 3}, "result": 5, "label": "task3"},
        "task2": {"inputs": {"a": 2}, "result": 2, "label": "task2"},
        "task4": {"inputs": {"a": 2, "b": 4}, "result": 6, "label": "task4"},
        "task5": {"inputs": {"a": 5, "b": 6}, "result": 11, "label": "task5"},
        "task6": {"inputs": {"a": 11, "b": 6}, "result": 17, "label": "task6"},
        "task7": {},
    }
    assert results == expected

    results = execute_graph(
        create_graph(),
        inputs=[{"name": "b", "value": 1}],
        output_tasks=True,
    )
    results = {k: v.get_output_values() for k, v in results.items()}
    expected = {
        "task1": {"inputs": {"a": 1, "b": 1}, "result": 2, "label": "task1"},
        "task3": {"inputs": {"a": 2, "b": 3}, "result": 5, "label": "task3"},
        "task2": {"inputs": {"a": 2, "b": 1}, "result": 3, "label": "task2"},
        "task4": {"inputs": {"a": 3, "b": 4}, "result": 7, "label": "task4"},
        "task5": {"inputs": {"a": 5, "b": 7}, "result": 12, "label": "task5"},
        "task6": {"inputs": {"a": 12, "b": 6}, "result": 18, "label": "task6"},
        "task7": {},
    }
    assert results == expected
