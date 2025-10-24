import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk 
    return


@app.cell
def _(mo):
    input = mo.ui.text(label="Input a word:", value='book')
    input
    return (input,)


@app.cell
def _(input, mo):
    mo.md(f"""**{input.value}** is inputted""")
    return


@app.cell
def _(ecdic, input, mo):
    _df = mo.sql(
        f"""
        select
            *
        from
            ecdic
        where
            key = '{input.value}'
        """
    )
    return


@app.cell
def _(ecdic, input):
    trans = ecdic(input.value)
    trans 
    return (trans,)


@app.cell
def _(mo, trans):
    dfchs = mo.sql(
        f"""
        select
            unnest(str_split('{trans}', ';')) as chs
        """
    )
    return (dfchs,)


@app.cell
def _(dfchs, mo):
    _df = mo.sql(
        f"""
        select
            str_split(chs, ':') as pair,
            pair[1] as pos,
            pair[2] as chslist
        from
            dfchs
        """
    )
    return


@app.cell
def _(pd, trans):
    pd.DataFrame( [pair.split(':') for pair in trans.split(';')], columns=['pos','trans'])
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
