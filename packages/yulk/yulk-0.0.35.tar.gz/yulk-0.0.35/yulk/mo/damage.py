import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    #论文仿写：“damage”与“destroy”
    *详细说明 https://sentbase.feishu.cn/file/Ff7kbeZaSo3WcZxwfmYc0Wc8nig*
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## synonym 近义词""")
    return


@app.cell
def _(mo, simv):
    _df = mo.sql(
        f"""
        -- 查询相似动词synonym(word, score, mf) ，参数为word, score和mf  
        SELECT
            *,                       -- 选择所有原始字段
            lemmf(word) AS mf        -- 新增计算字段：对word字段应用lemmf词频函数（在语料库中每百万频次结果），结果命名为mf
        FROM
            simv                     -- 在simv相似动词查询数据
        WHERE
            key = 'damage'           -- 筛选条件：key字段值为'damage'的记录
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## word freq 词频""")
    return


@app.cell
def _(lemmf, mo):
    _df = mo.sql(
        f"""
        -- 查询词频word freq
        SELECT *   -- 选择所有原始字段
        FROM 
            lemmf  --在lemmf词频查询数据
        WHERE 
            key IN ('damage', 'destroy')  
            -- 筛选条件：key字段值为'damage'和'destroy'的记录
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        -- 查询词性分布lempos
        SELECT * -- 选择所有原始字段
        FROM 
            en.lempos  -- 在en.lempos词性分布中查询数据 
        WHERE 
            key = 'damage'  
            -- 筛选条件：仅返回key字段值为'damage'的记录
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## style 语体""")
    return


@app.cell
def _(mo, wordmf):
    _df = mo.sql(
        f"""
        -- 查询语体分布style
        SELECT *  -- 选择所有原始字段
        FROM 
            wordmf  -- 在wordmf语体分布查询数据（news新闻/mag杂志/fic小说/spok口语/blog博客/sci论文）
        WHERE 
            key IN ('damage', 'destroy')  
            -- 筛选条件：返回key字段值为'damage'或'destroy'的所有记录
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## trp logdice 词汇搭配强度 
    *logDice用于衡量词语共现显著性,值越大关联越强,结果范围通常在[0,14]之间（14为最大值）*
    """
    )
    return


@app.cell
def _(en):
    df = en.dobjvn('damage') # 在en表调用dobjvn动宾搭配函数，传入参数'damage'，结果赋值给df(DataFrame)变量
    df #返回df
    return (df,)


@app.cell
def _(df, en):
    # 对df进行操作，添加两个新的汇总列
    df['sum1'] = en.dobjvn_sum(df.word)  # 对df的word列应用dobjnv_sum方法，结果存入sum1列,即计算每个label的动宾搭配总数
    df['sum2'] = en.dobjvn_sum('damage')    # 对固定字符串'open'应用dobjvn_sum方法，结果存入sum2列
    df  # 返回修改后的df
    return


@app.cell
def _(df, mo):
    _df = mo.sql(
        f"""
        -- 计算词汇搭配强度的logDice指标,用于衡量词语共现显著性,值越大关联越强,结果范围通常在[0,14]之间（14为最大值）
        SELECT
            *,  -- 选择所有原始字段
            logdice(cnt, sum1, sum2) AS logdice  -- 新增计算字段：基于cnt/sum1/sum2计算logdice值
        FROM
            df  -- 上述生成的df变量数据
        ORDER BY
            logdice DESC  -- 按logdice值降序排列
        """
    )
    return


@app.cell
def _(en):
    en.dobjvn_sum('damage')
    # 在en表调用dobjvn_sum动宾搭配统计函数，传入参数'damage',即计算damage的动宾搭配总数
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## trp type 动词模式""")
    return


@app.cell
def _(mo):
    dfword = mo.sql(
        f"""
        -- 创建包含两个单词的临时结果集
        SELECT
            'damage' AS word  -- 第一行数据：固定值'damage'，列名为word
        UNION  -- 集合操作符：合并两个SELECT的结果集(自动去重)
        SELECT
            'destroy' AS word  -- 第二行数据：固定值'destroy'，列名为word
        """
    )
    return (dfword,)


@app.cell
def _(dfword, mo):
    dftrp = mo.sql(
        f"""
        -- 动词模式分析查询 trp  type 
        SELECT
            word,  -- 原始单词字段
            en.dobjvn_sum(word) AS object,      -- 计算动词的直接宾语频数
            en.nsubjvn_sum(word) AS subject,    -- 计算动词的名词主语频数 
            en.advmodvd_sum(word) AS modifier,  -- 计算动词的状语修饰频数 
            en.prepvp_sum(word) AS phraseprep   -- 计算动词的介词短语频数 
        FROM
            dfword  -- 上述生成的dfword变量数据
        """
    )
    return (dftrp,)


@app.cell
def _(dftrp, mo):
    dftrpsum = mo.sql(
        f"""
        -- 动词关系模式综合分析查询
        SELECT
            *,  -- 选择所有原始字段
            object + subject + modifier + phraseprep AS sum  -- 新增计算字段：计算动词直接宾语+名词主语+状语修饰语+介词短语总频数，结果命名为sum
        FROM
            dftrp  -- 上述生成的dftrp变量数据
        """
    )
    return (dftrpsum,)


@app.cell
def _(dftrpsum, mo):
    _df = mo.sql(
        f"""
        -- 动词关系模式百分比分析查询
        SELECT 
            word,  -- 动词原形
            round(100 * object / sum, 2) AS obj,    -- 动词直接宾语关系占比(（动词的直接宾语频数/总频数）*100，ROUND函数用于对数值进行四舍五入。它接受两个参数：第一个参数是要四舍五入的数值，第二个参数是保留的小数位数)
            round(100 * subject / sum, 2) AS sub,   -- 名词主语关系占比  
            round(100 * modifier / sum, 2) AS modi, -- 状语修饰关系占比
            round(100 * phraseprep / sum, 2) AS prep -- 介词短语关系占比
        FROM 
            dftrpsum  -- 上述生成的dftrpsum变量数据
        """
    )
    return


if __name__ == "__main__":
    app.run()
