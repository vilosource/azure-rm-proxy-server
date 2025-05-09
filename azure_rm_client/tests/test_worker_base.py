import pytest
from azure_rm_client.workers.worker_base import Worker, WorkerBase

def test_worker_is_abstract():
    """Test that Worker cannot be instantiated directly."""
    with pytest.raises(TypeError, match=r"Can't instantiate abstract class Worker"):
        Worker()

def test_worker_base_alias():
    """Test that WorkerBase is correctly aliased to Worker."""
    assert WorkerBase is Worker, "WorkerBase should be an alias for Worker"

def test_concrete_worker_must_implement_execute():
    """Test that a concrete subclass must implement execute."""
    class IncompleteWorker(Worker):
        pass  # Missing execute implementation

    with pytest.raises(TypeError, match=r"Can't instantiate abstract class IncompleteWorker"):
        IncompleteWorker()

def test_concrete_worker_can_be_instantiated():
    """Test that a concrete subclass with execute implemented can be instantiated."""
    class CompleteWorker(Worker):
        def execute(self, *args, **kwargs):
            return "executed"

    worker = CompleteWorker()
    assert isinstance(worker, Worker)
    assert worker.execute() == "executed"

def test_execute_accepts_args_and_kwargs():
    """Test that execute method can accept both args and kwargs."""
    class TestWorker(Worker):
        def execute(self, *args, **kwargs):
            return {"args": args, "kwargs": kwargs}

    worker = TestWorker()
    result = worker.execute(1, 2, name="test")
    assert result["args"] == (1, 2)
    assert result["kwargs"] == {"name": "test"}