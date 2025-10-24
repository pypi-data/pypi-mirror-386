import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell
def _():
    import yulk  #引入数据集和函数
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ##动宾搭配语料库对比分析（CN vs EN）

    ***NOUN*** 前 ***VERB*** 中英分布对比
    """
    )
    return


@app.cell
def _(mo):
    input = mo.ui.text(label="Input a noun:", value='success')
    input
    return (input,)


@app.cell
def _(dobjnv, input, mo):
    df = mo.sql(
        f"""
        SELECT
            word, 
            100 * cn / sum(cn) over() as cnperc,
            100 * en / sum(en) over() as enperc
        FROM
            dobjnv
        where
            key = '{input.value}'
        order by
            cn desc
        limit 8
        """
    )
    return (df,)


@app.cell
def _(df):
    # 数据可视化
    df.bars()
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
