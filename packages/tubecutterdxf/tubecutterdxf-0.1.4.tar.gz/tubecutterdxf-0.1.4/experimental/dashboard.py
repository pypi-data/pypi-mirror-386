import panel as pn
import src.tubecutterdxf as tc
import pandas as pd

pn.extension(design='material', sizing_mode='stretch_width')

pattern = tc.CutPattern()
pattern.add(tc.CutPartline(1))


def plot_line(old, new):
    if old == 0:
        return new

def get_plot():
    cuts = pattern.getCuts()
    for cut in cuts:
        lines = cut.getLines()
    
    p = ''
    for start, end in lines:
        line_data = pd([start[0], end[0]], [start[1], end[1]])
        p = plot_line(p, line_data)


    print("test")

bound_plot = pn.bind(
    get_plot
)


pn.template.MaterialTemplate(
    site='TubeCutterDXF',
    title='Getting Started App',
    sidebar=[],
    main=[get_plot]
).servable()
