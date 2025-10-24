import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT
            *
        FROM
            en.gram4
        limit
            10
        """
    )
    return


@app.cell
def _(mo):
    dfen = mo.sql(
        f"""
        -- comments here 
        SELECT
            lem2,
            count(*) cnt
        FROM
            en.gram4
        where
            lem1 = 'make'
            and pos2 = 'ADJ'
            and lem3 = 'use'
            and lem4 = 'of'
        group by
            lem2
        order by
            cnt desc
        """
    )
    return (dfen,)


@app.cell
def _(mo):
    dfcn = mo.sql(
        f"""
        SELECT
            lem2,
            count(*) cnt
        FROM
            cn.gram4
        where
            lem1 = 'make'
            and pos2 = 'ADJ'
            and lem3 = 'use'
            and lem4 = 'of'
        group by
            lem2
        order by
            cnt desc
        """
    )
    return (dfcn,)


@app.cell
def _(dfcn, dfen, keyness):
    keyness(dfcn,dfen)
    return


if __name__ == "__main__":
    app.run()
