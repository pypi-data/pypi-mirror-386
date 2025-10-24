import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 356篇学生同题作文批量分析和数据挖掘
    1. myu： 作文表，key 是作文id， uid 是用户号， dim是作文的维度值， 包括awl, ast, b3, 等维度
    2. myusnt：句子表
    3. myutok: 单词表，用来分析单词分布等；
    4. myufeedback：句子反馈表，用来统计错误分布等；
    """
    )
    return


@app.cell
def _(mo, myu):
    dftxt = mo.sql(
        f"""
        -- 浏览学生作文
        SELECT * FROM myu limit 10
        """
    )
    return (dftxt,)


@app.cell
def _(dftxt, mo):
    # 查看某篇具体的作文
    mo.md(dftxt.essay[0])
    return


@app.cell
def _(mo, myutok):
    dfverb = mo.sql(
        f"""
        -- 查看动词分布
        select lem, count(*) cnt
        from myutok 
        where pos = 'VERB'
        group by lem 
        order by cnt desc
        """
    )
    return (dfverb,)


@app.cell
def _(dfverb, mo):
    dfverbawl = mo.sql(
        f"""
        -- 列出动词中的学术词汇 
        select
            *
        from
            dfverb
        where
            awl (lem) = true
        """
    )
    return


@app.cell
def _(mo, myufeedback):
    dfcate = mo.sql(
        f"""
        -- 统计错误分布
        select
            cate,
            count(*) cnt,
            list(key) as sids
        from
            myufeedback
        where
            cate not like 'i_%'
            and cate not like 'w_%'
            and cate != 'confusion'
        group by
            cate
        order by
            cnt desc
        """
    )
    return


@app.cell
def _(mo, myu):
    _df = mo.sql(
        f"""
        -- 维度分布
        SELECT
            uid,
            dim.awl as 平均词长,
            dim.ast as 平均句长,
            dim.ttr1 as 词汇丰富度,
            dim.b3 as 学术词汇占比,
            dim.cl_sum as 从句数量,
            dim.simple_sent_ri as 简单句占比
        FROM
            myu
        order by
            uid
        """
    )
    return


if __name__ == "__main__":
    app.run()
