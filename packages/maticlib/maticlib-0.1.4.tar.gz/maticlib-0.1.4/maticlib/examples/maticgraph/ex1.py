from maticlib.graph import MaticGraph
from pydantic import BaseModel
import time

class AnalysisState(BaseModel):
    text: str = ""
    sentiment: str = ""
    entities: list = []
    summary: str = ""
    final_report: str = ""

def extract_text(state: AnalysisState) -> dict:
    print("Extracting text...")
    return {"text": "This is a sample document about AI and machine learning."}

def analyze_sentiment(state: AnalysisState) -> dict:
    print("  [Sentiment] Analyzing...")
    time.sleep(2)  # Simulate API call
    return {"sentiment": "positive"}

def extract_entities(state: AnalysisState) -> dict:
    print("  [Entities] Extracting...")
    time.sleep(2)  # Simulate API call
    return {"entities": ["AI", "machine learning"]}

def generate_summary(state: AnalysisState) -> dict:
    print("  [Summary] Generating...")
    time.sleep(2)  # Simulate API call
    return {"summary": "Document discusses AI topics"}

def create_report(state: AnalysisState) -> dict:
    print("Creating final report...")
    report = f"""
    Sentiment: {state.sentiment}
    Entities: {', '.join(state.entities)}
    Summary: {state.summary}
    """
    return {"final_report": report}

# Build graph
graph = MaticGraph(stateful=True, state_schema=AnalysisState, max_workers=3)

graph.add_node("extract", extract_text)
graph.add_node("sentiment", analyze_sentiment)
graph.add_node("entities", extract_entities)
graph.add_node("summary", generate_summary)
graph.add_node("report", create_report)

graph.set_entry("extract")

# After extract, run sentiment, entities, and summary IN PARALLEL
graph.parallel_group(
    from_node="extract",
    parallel_nodes=["sentiment", "entities", "summary"],
    join_node="report"  # Continue here after all complete
)

graph.set_exit("report")

# Visualize
print(graph.visualize())

# Run - will execute 3 analysis tasks in parallel!
result = graph.run(verbose=True)
print(result.final_report)