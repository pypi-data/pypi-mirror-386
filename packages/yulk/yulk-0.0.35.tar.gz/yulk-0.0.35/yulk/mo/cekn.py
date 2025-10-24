import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk 
    return


@app.cell
def _(txtdf):
    toks = txtdf("It is a market share. I open the possibility.")
    toks
    return (toks,)


@app.cell
def _(mo, toks):
    dfsnt = mo.sql(
        f"""
        -- extract snts from toks 
        select
            sntbeg,
            GROUP_CONCAT(textws, '') snt
        from
            toks
        group by
            sntbeg
        """
    )
    return


@app.cell
def _(mo, toks):
    _df = mo.sql(
        f"""
        --单词词性少用（待学）
        select
            i,
            lem || ':POS:' || pos as term,
            cekn (term) kn
        from
            toks
        where
            kn < -3.84
        """
    )
    return


@app.cell
def _(mo, toks):
    _df = mo.sql(
        f"""
        --搭配少用
        select
            i,
            glem || ':' || dep || shortpos(gpos) || shortpos(pos) || ':' || lem as term,   --dobjvn
            cekn (term) kn
        from
            toks
        where
            kn < -3.84
        """
    )
    return


@app.cell
def _(shortpos):
    shortpos('NOUN')
    return


@app.cell
def _(cekn):
    cekn('share:POS:NOUN')
    return


@app.cell
def _(cekn, mo):
    _df = mo.sql(
        f"""
        from cekn where key like 'share:POS:%'
        """
    )
    return


@app.cell
def _(cekn):
    cekn('open:dobjvn:possibility')
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
