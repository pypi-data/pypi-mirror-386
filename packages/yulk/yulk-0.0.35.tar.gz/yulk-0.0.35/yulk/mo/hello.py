import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import cikuu.mod.yulk
    return


@app.cell
def _(root):
    root
    return


@app.cell
def _(segchs):
    segchs('是伟大的。')
    return


@app.cell
def _(enzh):
    enzh("It is great.")
    return


@app.cell
def _(mo):
    dfone = mo.sql(
        f"""
        from
           cn.dobjvn
        where
            key = 'open'
        """
    )
    return (dfone,)


@app.cell
def _(duckdb):
    def myfunc(s): return s.upper() + 'xxxx'
    duckdb.create_function('myfunc', myfunc, [str], str)
    return


@app.cell
def _(dfone, mo):
    _df = mo.sql(
        f"""
        select * , myfunc(key) from dfone
        """
    )
    return


@app.cell
def _(dfone):
    dfone.sort
    return


@app.cell
def _(dfone):
    dfone.sort(by='keyness')
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(lempos):
    lempos('book:pos')
    return


@app.cell
def _(dfone, mo):
    mo.ui.table(dfone)
    return


@app.cell
def _(lempos, mo):
    dfx = mo.sql(
        f"""
        SELECT * FROM lempos limit 10
        """
    )
    return


@app.cell
def _(dobjnv):
    df = dobjnv('problem')
    df
    return (df,)


@app.cell
def _(df):
    df.columns[-1]
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        create schema IF NOT EXISTS en
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        CREATE OR REPLACE VIEW en.dobjnv AS (SELECT key, label, en AS cnt, keyness FROM dobjnv WHERE en > 0 ORDER BY cnt desc);
        """
    )
    return (dobjnv,)


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT * FROM en.dobjnv limit 10
        """
    )
    return


@app.cell
def _(mo):
    dropdown = mo.ui.dropdown(
        options=['选项A', '选项B', '选项C'],
        value='选项A',
        label="请选择"
    )
    dropdown
    return


@app.cell
def _(mo):
    mo.sql("select version()")
    return


@app.cell
def _(mo):

    # 创建左右面板内容
    left_panel = mo.md("""
    # 左侧面板

    这里是左侧的内容区域，可以放置：
    - 数据表格
    - 输入控件
    - 说明文档
    - 代码示例
    """)

    right_panel = mo.md("""
    # 右侧面板

    这里是右侧的内容区域，可以放置：
    - 可视化图表
    - 分析结果
    - 实时预览
    - 交互组件
    """)

    # 创建可调整的分割布局
    resizable_split = mo.split(
        [left_panel, right_panel],
        initial_sizes=[0.4, 0.6],  # 初始比例 40% : 60%
        direction="horizontal"
    )

    resizable_split
    return


if __name__ == "__main__":
    app.run()
