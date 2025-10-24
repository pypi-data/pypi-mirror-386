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
    ##学术词汇统计

    给定一篇文章，把文中的学术词汇awl(Academic Word List)高亮出来，统计学术词汇占比。
    """
    )
    return


@app.cell
def _(wget):
    text= wget('skills.txt')
    text
    return (text,)


@app.cell
def _(text, txtdf):
    toks =txtdf(text)
    toks
    return (toks,)


@app.cell
def _(level):
    level('apple')
    return


@app.cell
def _(mo, toks):
    dftok = mo.sql(
        f"""
        select
            i,
            textws,
            if( level(lem) == 'awl', '**'||textws||'**', textws) as word 
        from
            toks
        """
    )
    return (dftok,)


@app.cell
def _(dftok, mo):
    mo.md("".join(dftok.word))
    return


@app.cell
def _(mo, toks):
    dfcnt = mo.sql(
        f"""
        select
            level (lem) as level,
            count(*) cnt
        from
            toks
        group by
            level
        """
    )
    return (dfcnt,)


@app.cell
def _(dfcnt, mo):
    _df = mo.sql(
        f"""
        SELECT
            *,
            round((cnt / sum(cnt) over ()) * 100, 2) as perc
        FROM
            dfcnt
        """
    )
    return


if __name__ == "__main__":
    app.run()
