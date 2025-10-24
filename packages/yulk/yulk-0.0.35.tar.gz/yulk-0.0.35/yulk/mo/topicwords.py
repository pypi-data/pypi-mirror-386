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
    ##主题词提取

    给定一篇文章，提取出里面的主题词。
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
def _(mo, toks):
    dflem = mo.sql(
        f"""
        select
            lem,
            count(*) cnt
        from
            toks
        where
            pos in ('VERB', 'NOUN', 'ADJ', 'ADV')
        group by
            lem
        order by
            cnt DESC
        """
    )
    return (dflem,)


@app.cell
def _(dflem, mo, toks):
    dfcnt = mo.sql(
        f"""
        select
            *, 
            (select count(*) from toks) as total    
        from
            dflem
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        --添加对函数 logbnc 的解释， 是一个sql 里面的 scalar 函数， 输入三个参数（Word，cnt,total）， 输出一个
        6.6 开发互动页面
        select
            *,
            logbnc (lem, cnt, total) as kn
        from
            dfcnt
        order by
            kn desc
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        -- 单词 one, 在文中出现 12次， 本文一共包括 1234 个单词 
        select logbnc('one',12, 1234)
        """
    )
    return


if __name__ == "__main__":
    app.run()
