# utils.py

import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

def create_bar_chart(data, title):
    """Generates a bar chart and returns it as a base64-encoded string."""
    fig, ax = plt.subplots()
    ax.bar(data.keys(), data.values())
    ax.set_title(title)
    ax.set_ylabel('Values')
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    img.seek(0)
    return base64.b64encode(img.read()).decode('utf-8')
