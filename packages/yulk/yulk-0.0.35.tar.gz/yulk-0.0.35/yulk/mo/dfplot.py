import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np

    df = pd.DataFrame({
        'x': range(1, 101),
        'y': np.random.randn(100).cumsum(),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })

    df.plot(x='x', y='y', title='Pandas')
    return (pd,)


@app.cell
def _(pd):
    import plotly.express as px
    df1 = pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D', 'E'],
        'Value': [23, 45, 56, 12, 67],
        'Group': ['X', 'X', 'Y', 'Y', 'Z']
    })

    # 基本柱状图
    px.bar(df1, x='Category', y='Value', title='基本柱状图')

    return df1, px


@app.cell
def _(pd):
    pd.DataFrame.bar  = lambda self, xcol=0, ycol=1, **kwargs: self.plot(x=self.columns[xcol], y=self.columns[ycol], kind='bar', **kwargs)
    return


@app.cell
def _(df1):
    df1.bar()
    return


@app.cell
def _(pd, px):
    px.bar(pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D'],
        'Value1': [23, 45, 56, 12],
        'Value2': [34, 28, 49, 18]
    }), 
           x='Category', y=['Value1', 'Value2'],
                 title='双柱对比图',
                 barmode='group',  
                 labels={'value': '数值', 'variable': '数据系列'})

    return


@app.cell
def _(pd):
    df2 = pd.DataFrame({
        'word': ['A', 'B', 'C', 'D'],
        'Value1': [23, 45, 56, 12],
        'Value2': [34, 28, 49, 18]
    })
    df2.plot(x='word', y=['Value1','Value2'], kind='bar')
    return (df2,)


@app.cell
def _(df2):
    df2.columns[-1]
    return


@app.cell
def _(df2):
    df2.count

    return


if __name__ == "__main__":
    app.run()
