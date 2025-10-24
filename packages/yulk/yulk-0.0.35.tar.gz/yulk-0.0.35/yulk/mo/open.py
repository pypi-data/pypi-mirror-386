import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk   #引入数据集和函数
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 误用/待学知识点计算

    以动词 ***open*** 的宾语名词搭配分布为例，计算出误用和待学知识点。
    """
    )
    return


@app.cell
def _(mo):
    dfcn = mo.sql(
        f"""
        SELECT
            word,
            cnt
        FROM
            cn.dobjvn
        where
            key = 'open'
        """
    )
    return (dfcn,)


@app.cell
def _(mo):
    dfen = mo.sql(
        f"""
        SELECT
            word,
            cnt
        FROM
            en.dobjvn
        where
            key = 'open'
        """
    )
    return (dfen,)


@app.cell
def _(dfcn, dfen, keyness):
    res = keyness(dfcn, dfen)
    res
    return (res,)


@app.cell
def _(mo, res):
    _df = mo.sql(
        f"""
        -- 误用部分
        SELECT
            *
        FROM
            res
        where
            cnt2 < 2
        order by
            keyness desc
        """
    )
    return


@app.cell
def _(mo, res):
    _df = mo.sql(
        f"""
        --待学
        SELECT
            *
        FROM
            res
        WHERE
            cnt1 < 2
        order by
            keyness
        """
    )
    return


if __name__ == "__main__":
    app.run()
