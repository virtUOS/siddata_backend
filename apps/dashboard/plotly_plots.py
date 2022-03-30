from plotly.io import to_html
import plotly.graph_objects as go


def pichart_plot(labels, values, colors):
    chart = go.Pie(labels=labels, values=values, hoverinfo='label+percent', textinfo='value',
                   marker=dict(colors=colors))
    fig = go.Figure(data=[chart])
    fig.update_layout(autosize=True)
    html = to_html(fig, full_html=False)
    return html


def grouped_barplot(degree_sem_cnt, title=None, show_legend=True):
    fig = go.Figure()
    for degree, semester in degree_sem_cnt.items():
        fig.add_trace(go.Bar(
            x=[[degree] * len(semester),
               list(semester.keys())],
            y=list(semester.values()),
            name=degree,
            text=list(semester.values()),
            textposition='auto',
        ))
    if title:
        fig.update_layout(title_text=title)
    fig.update_layout(showlegend=show_legend)
    fig.update_layout(margin=dict(l=10, r=10))
    html = to_html(fig, full_html=False)
    return html


def hbars_plot(top_labels, colors, x_data, y_data):
    # see https://plotly.com/python/horizontal-bar-charts/
    fig = go.Figure()
    for i in range(0, len(x_data[0])):
        for xd, yd in zip(x_data, y_data):
            fig.add_trace(go.Bar(
                x=[xd[i]], y=[yd],
                orientation='h',
                marker=dict(
                    color=colors[i],
                    line=dict(color='rgb(248, 248, 249)', width=1)
                )
            ))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0.15, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        barmode='stack',
        paper_bgcolor='rgb(248, 248, 255)',
        plot_bgcolor='rgb(248, 248, 255)',
        margin=dict(l=120, r=10, t=140, b=80),
        showlegend=False,
    )
    annotations = []
    for yd, xd in zip(y_data, x_data):
        # labeling the y-axis
        annotations.append(dict(xref='paper', yref='y',
                                x=0.14, y=yd,
                                xanchor='right',
                                text=str(yd),
                                font=dict(family='Arial', size=14,
                                          color='rgb(67, 67, 67)'),
                                showarrow=False, align='right'))
        # labeling the first percentage of each bar (x_axis)
        annotations.append(dict(xref='x', yref='y',
                                x=xd[0] / 2, y=yd,
                                text=str(xd[0]), #+ '%',
                                font=dict(family='Arial', size=14,
                                          color='rgb(248, 248, 255)'),
                                showarrow=False))
        # labeling the first Likert scale (on the top)
        if yd == y_data[-1]:
            annotations.append(dict(xref='x', yref='paper',
                                    x=xd[0] / 2, y=1.1,
                                    text=top_labels[0],
                                    font=dict(family='Arial', size=14,
                                              color='rgb(67, 67, 67)'),
                                    showarrow=False))
        space = xd[0]
        for i in range(1, len(xd)):
            # labeling the rest of percentages for each bar (x_axis)
            annotations.append(dict(xref='x', yref='y',
                                    x=space + (xd[i] / 2), y=yd,
                                    text=str(xd[i]),# + '%',
                                    font=dict(family='Arial', size=14,
                                              color='rgb(248, 248, 255)'),
                                    showarrow=False))
            # labeling the Likert scale
            if yd == y_data[-1]:
                annotations.append(dict(xref='x', yref='paper',
                                        x=space + (xd[i] / 2), y=1.1,
                                        text=top_labels[i],
                                        font=dict(family='Arial', size=14,
                                                  color='rgb(67, 67, 67)'),
                                        showarrow=False))
            space += xd[i]
    fig.update_layout(annotations=annotations)
    fig.update_layout(autosize=True)
    html = to_html(fig, full_html=False)
    return html
