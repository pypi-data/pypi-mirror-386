import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _(mo):
    mo.md(r"""CEFR（欧洲语言共同参考框架）将英语能力分为六个等级（A1-C2），每个等级对应不同的词汇量和语言运用能力。""")
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT * FROM cefr limit 10 
        """
    )
    return


if __name__ == "__main__":
    app.run()
