import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _():
    word = 'book'
    return (word,)


@app.cell
def _(mo, word):
    dfcn = mo.sql(
        f"""
        SELECT
           label,
            cnt
        FROM
            cn.lempos
        where
            key = '{word}'
        """
    )
    return (dfcn,)


@app.cell
def _(mo, word):
    dfen = mo.sql(
        f"""
        SELECT
            label,
            cnt
        FROM
            en.lempos
        where
            key = '{word}'
        """
    )
    return (dfen,)


@app.cell
def _(dfcn, dfen, keyness):
    keyness(dfcn, dfen)
    return


if __name__ == "__main__":
    app.run()
