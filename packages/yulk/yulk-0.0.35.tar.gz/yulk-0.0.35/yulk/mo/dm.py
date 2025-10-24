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


@app.cell
def _():
    import plotly.express as px
    return (px,)


@app.cell
def _(mo):
    mo.md(r"""##学生作文诊断分析""")
    return


@app.cell
def _(mo, myufeedback):
    df_error = mo.sql(
        f"""
        -- 统计错误分布
        select
            cate as 错误类型,
            count(*) as 频次
        from
            myufeedback
        where
            cate not like 'i_%'
            and cate not like 'w_%'
            and cate != 'confusion'
        group by
            cate
        order by
            频次 desc
        """
    )
    return


@app.cell
def _(mo, myufeedback):
    df_errcate = mo.sql(
        f"""
        select
            rightof (leftof (cate, '.'), '_') topcate,
            cate (topcate) 错误类型,
            count(*) 频次
        from
            myufeedback
        where
            cate like 'e%' or cate like 'w%'
        group by
            topcate
        order by
            频次 desc
        """
    )
    return (df_errcate,)


@app.cell
def _(df_errcate, px):
    px.bar(df_errcate,x='错误类型',y='频次',title='学生错误统计')
    return


@app.cell
def _(mo, myu):
    df_dim = mo.sql(
        f"""
        -- 维度分布
        SELECT
            uid,
            dim.awl as 平均词长,
            dim.ttr1 as 词汇丰富度,
            dim.word_diff_avg as 词汇难度,
            dim.b3 as 学术词汇占比,
            dim.ast as 平均句长,
            dim.cl_sum as 从句数量,
            dim.simple_sent_ri as 简单句占比,
            dim.spell_correct_ratio as 拼写正确率,
            dim.grammar_correct_ri as 语法正确率
        FROM
            myu
        ORDER BY
            uid
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        -- 平均词长分布
        px.bar(df_dim,x=uid,y=平均词长)
        """
    )
    return


if __name__ == "__main__":
    app.run()
