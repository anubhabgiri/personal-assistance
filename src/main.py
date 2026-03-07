from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.tools import tool

# initialize the graph
graph = StateGraph(MessagesState)

# Define the master controller agent node
def master_agent(state: MessagesState):
    """Master controller that routes to appropriate agents or tools"""
    messages = state["messages"]
    response = "add local LLM here"
    return {"messages": messages + [response]}

def summariser_agent(state: MessagesState):
    """Agent that summarizes the conversation"""
    messages = state["messages"]
    summary = "add local LLM here for summarization"
    return {"messages": messages + [summary]}

# Add the master agent to the graph
graph.add_node("master_agent", master_agent)
graph.add_edge(START, "master_agent")
graph.add_edge("master_agent", END)

# Compile the graph
compiled_graph = graph.compile()

if __name__ == "__main__":
    # Initialize the models
    pass