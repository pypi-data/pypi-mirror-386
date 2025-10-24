from maticlib.graph import MaticGraph
from pydantic import BaseModel

class MultiStageState(BaseModel):
    stage1_a: str = ""
    stage1_b: str = ""
    stage2_a: str = ""
    stage2_b: str = ""
    stage2_c: str = ""

# Stage 1: Preprocessing
def preprocess(state): 
    return {}

def clean_a(state): 
    return {"stage1_a": "cleaned A"}

def clean_b(state): 
    return {"stage1_b": "cleaned B"}

def merge_stage1(state):
    print(f"Merged: {state.stage1_a}, {state.stage1_b}")
    return {}

# Stage 2: Analysis
def analyze_a(state): 
    return {"stage2_a": "analysis A"}

def analyze_b(state): 
    return {"stage2_b": "analysis B"}

def analyze_c(state): 
    return {"stage2_c": "analysis C"}

def final_report(state):
    return {"final": "All done!"}

# Build multi-stage parallel graph
graph = MaticGraph(stateful=True, state_schema=MultiStageState, max_workers=4)

graph.add_node("preprocess", preprocess)
graph.add_node("clean_a", clean_a)
graph.add_node("clean_b", clean_b)
graph.add_node("merge1", merge_stage1)
graph.add_node("analyze_a", analyze_a)
graph.add_node("analyze_b", analyze_b)
graph.add_node("analyze_c", analyze_c)
graph.add_node("final", final_report)

graph.set_entry("preprocess")

# First parallel group: Cleaning
graph.parallel_group(
    "preprocess",
    ["clean_a", "clean_b"],
    join_node="merge1"
)

# Second parallel group: Analysis
graph.parallel_group(
    "merge1",
    ["analyze_a", "analyze_b", "analyze_c"],
    join_node="final"
)

graph.set_exit("final")

print(graph.visualize())

result = graph.run(verbose=True)