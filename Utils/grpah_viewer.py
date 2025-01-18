import io
from PIL import Image
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

def show_graph_flow(graph):
    image = Image.open(io.BytesIO(graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API
    )))
    image.show()