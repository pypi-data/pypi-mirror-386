import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import cikuu.mod.yulk
    return


@app.cell
def _(root):
    root
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        from cloze('It * ok.')
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        _df
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        from cloze('it * ok.')
        """
    )
    return


@app.cell
def _(ce, mo):
    dfopen = mo.sql(
        f"""
        select  label, en from  ce where key='open:dobjvn' and en > 0
        """
    )
    return (dfopen,)


@app.cell
def _(dfopen):
    dfopen.head(10)
    return


@app.cell
def _(dfopen):
    # replace _df with your data source
    import altair as alt
    import matplotlib.pyplot as plt  
    _chart = (
        alt.Chart(dfopen)
        .mark_bar()
        .encode(
            x=alt.X(field='label', type='nominal'),
            y=alt.Y(field='en', type='quantitative', aggregate='mean'),
            tooltip=[
                alt.Tooltip(field='label'),
                alt.Tooltip(field='en', aggregate='mean', format=',.0f')
            ]
        )
        .properties(
            height=290,
            width='container',
            config={
                'axis': {
                    'grid': False
                }
            }
        )
    )
    _chart
    return


@app.cell
def _(dfopen):
    type(dfopen)
    return


@app.cell
def _(df2):
    type(df2)
    return


@app.cell
def _(e, mo):
    _df = mo.sql(
        f"""
        from e where key='open:dobjvn'
        """
    )
    return


@app.cell
def _(df2, dfopen, keyness):
    keyness(dfopen, df2)
    return


@app.cell
def _(sql):
    type(sql("select version()"))
    return


@app.cell
def _(mo):
    import plotly.express as px
    plot = mo.ui.plotly(
      px.scatter(x=[0, 1, 4, 9, 16], y=[0, 1, 2, 3, 4], width=600, height=300)
    )
    plot
    return


@app.cell
def _(dobjvn):
    df2 = dobjvn('open',cp='cn')
    df2
    return (df2,)


@app.cell
def _(df1, df2, keyness):
    keyness(df1, df2)
    return


@app.cell
def _(sntdf):
    df = sntdf('This is a test.')
    df
    return (df,)


@app.cell
def _(df):
    import duckdb 
    duckdb.sql("select * from df").fetchdf()
    return


@app.cell
def _(lemlex):
    lemlex('book')
    return


@app.cell
def _():
    globals()
    return


@app.cell
def _():
    import marimo

    # 通过下拉选择框选择不同的数据集
    dataset_selector = marimo.ui.dropdown(
        options={
            'Dataset 1': {'A': 10, 'B': 20, 'C': 15},
            'Dataset 2': {'A': 5, 'B': 25, 'C': 30},
            'Dataset 3': {'A': 15, 'B': 10, 'C': 35}
        },
        value = {'A': 5, 'B': 25, 'C': 30}, 
        label="Choose a Dataset"
    )

    # 显示选择器
    dataset_selector
    return (dataset_selector,)


@app.cell
def _(dataset_selector):
    dataset_selector.value
    return


if __name__ == "__main__":
    app.run()
