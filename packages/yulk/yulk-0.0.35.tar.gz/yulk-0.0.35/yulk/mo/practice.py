import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# 论文仿写 damage与destroy辨析""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## synonym近义词""")
    return


@app.cell
def _(mo, simv):
    _df = mo.sql(
        f"""
        SELECT 
            *,
            lemmf(word) AS mf
        FROM
        	simv
        WHERE
        	key = 'damage'
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""##word freq 词频""")
    return


@app.cell
def _(lemmf, mo):
    _df = mo.sql(
        f"""
        SELECT 
            * 
        FROM
        	lemmf
        WHERE
        	key IN ('damage','destroy')
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT 
            * 
        FROM
        	en.lempos
        WHERE
        	key IN ('damage','destroy')
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""##style语体""")
    return


@app.cell
def _(mo, wordmf):
    _df = mo.sql(
        f"""
        SELECT 
            * 
        FROM
        	wordmf
        WHERE 
        	key IN ('damage','destroy')
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## trp logdice搭配强度""")
    return


@app.cell
def _(en):
    df=en.dobjvn('damage')
    df
    return (df,)


@app.cell
def _(df, en):
    df['sum1']=en.dobjvn_sum(df.word)
    df['sum2']=en.dobjvn_sum('damage')
    df
    return


@app.cell
def _(en):
    en.dobjvn_sum('damage')
    return


@app.cell
def _(df, mo):
    _df = mo.sql(
        f"""
        SELECT
            *,
        	logdice(cnt,sum2,sum1) AS logdice
        FROM
        	df
        ORDER BY
        	logdice DESC
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## trp type 动词模式 """)
    return


@app.cell
def _(mo):
    dfword = mo.sql(
        f"""
        SELECT 
            'damage' AS word
        UNION
        SELECT
        	'destroy' AS word
        """
    )
    return (dfword,)


@app.cell
def _(dfword, mo):
    dftrp = mo.sql(
        f"""
        SELECT 
            *,
            en.dobjvn_sum(word) AS object,
            en.nsubjvn_sum(word) AS subject,
            en.advmodvd_sum(word) AS modifier,
            en.prepvp_sum(word) AS phraseprep
    
        FROM
        	dfword
        """
    )
    return (dftrp,)


@app.cell
def _(dftrp, mo):
    dftrpsum = mo.sql(
        f"""
        SELECT 
            *,
            object + subject + modifier + phraseprep AS sum
        FROM
        	dftrp
        """
    )
    return (dftrpsum,)


@app.cell
def _(dftrpsum, mo):
    _df = mo.sql(
        f"""
        SELECT 
            *,
            round(100*object/sum,2) AS obj,
            round(100*subject/sum,2) AS sub,
            round(100*modifier/sum,2) AS modi,
            round(100*phraseprep/sum,2) AS prep
        FROM
        	dftrpsum
        """
    )
    return


if __name__ == "__main__":
    app.run()
