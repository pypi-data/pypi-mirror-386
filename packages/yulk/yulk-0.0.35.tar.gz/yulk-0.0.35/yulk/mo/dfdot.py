import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell
def _():
    import yulk
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ##同义词语体分布

    以 ***damage*** 为例，展示其近义词在不同语体中的频次对比
    """
    )
    return


@app.cell
def _(synonym):
    synonym('damage')
    return


@app.cell
def _(mo, wordmf):
    df = mo.sql(
        f"""
        select
            key,
            news,
            mag,
            fic,
            spok,
            blog,
            sci
        from
            wordmf
        where
            key in synonym ('damage')
        """
    )
    return (df,)


@app.cell
def _(df):
    df.dot()
    return


@app.cell
def _(sql):
    sql("select word,cn,en from dobjvn where key='open' order by en desc limit 30").pyramid()
    return


if __name__ == "__main__":
    app.run()
