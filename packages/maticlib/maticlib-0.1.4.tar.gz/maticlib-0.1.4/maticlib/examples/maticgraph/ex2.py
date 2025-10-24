from maticlib.graph import MaticGraph
from pydantic import BaseModel
import time

class ProcessingState(BaseModel):
    data_size: int = 0
    use_parallel: bool = False
    result_a: str = ""
    result_b: str = ""

def check_size(state: ProcessingState) -> dict:
    # Simulate checking data size
    size = 5000
    use_parallel = size > 1000
    return {"data_size": size, "use_parallel": use_parallel}

def process_large_a(state: ProcessingState) -> dict:
    print("  Processing large dataset A...")
    time.sleep(2)
    return {"result_a": "Large dataset A processed"}

def process_large_b(state: ProcessingState) -> dict:
    print("  Processing large dataset B...")
    time.sleep(2)
    return {"result_b": "Large dataset B processed"}

def merge_results(state: ProcessingState) -> dict:
    return {"final": f"{state.result_a} + {state.result_b}"}

# Build graph with conditional parallelism
graph = MaticGraph(stateful=True, state_schema=ProcessingState)

graph.add_node("check", check_size)
graph.add_node("process_a", process_large_a)
graph.add_node("process_b", process_large_b)
graph.add_node("merge", merge_results)

graph.set_entry("check")

# Only parallelize if data size > 1000
graph.parallel_group(
    from_node="check",
    parallel_nodes=["process_a", "process_b"],
    join_node="merge",
    condition=lambda state: state.use_parallel  # ← Conditional!
)

graph.set_exit("merge")

result = graph.run(verbose=True)
# If use_parallel=True: Both processes run in parallel
# If use_parallel=False: Only process_a runs sequentially