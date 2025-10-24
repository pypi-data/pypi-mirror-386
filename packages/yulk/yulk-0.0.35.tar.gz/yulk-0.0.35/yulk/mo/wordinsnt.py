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
    # 单词在句子中的对应译文 *wordinsnt*
    单词 **overcome** 有多个译文 （*克服*，*战胜*）等，在一个具体的句子中如“I overcame the difficulty.”， 是“**克服**”的意思。
    """
    )
    return


@app.cell
def _():
    word='overcame'
    sent='I overcame the difficulty.'
    return sent, word


@app.cell
def _(lexlem, word):
    lemma = lexlem(word)
    lemma
    return (lemma,)


@app.cell
def _(eclist, lemma):
    enwords = eclist(lemma)
    enwords
    return (enwords,)


@app.cell
def _(enwords, lemma, mo, word):
    mo.md(
        rf"""
    1. 输入的单词是 **{word}**
    2. 对应的单词原型是: **{lemma}**
    3. 查询词典，得到单词对应的译文 *{enwords}*
    """
    )
    return


@app.cell
def _(enzh, sent):
    zhsent = enzh(sent)
    zhsent
    return (zhsent,)


@app.cell
def _(segchs, zhsent):
    zhwords = segchs(zhsent)
    zhwords
    return (zhwords,)


@app.cell
def _(enwords, interlist, zhwords):
    interlist(enwords, zhwords)
    return


@app.cell
def _():
    return


@app.cell
def _(mo):
    df1 = mo.sql(
        f"""
        select
            'overcame' as word,
            lexlem (word) as lemma,
            'I overcame the difficulty.' as snt,
            enzh (snt) as chsnt
        """
    )
    return (df1,)


@app.cell
def _(df1, mo):
    df2 = mo.sql(
        f"""
        SELECT *, 
            eclist(lemma) as eclist,
            segchs( chsnt) as chslist
            FROM df1
        """
    )
    return (df2,)


@app.cell
def _(df2, mo):
    dfres = mo.sql(
        f"""
        SELECT
            *,
            LIST_INTERSECT(eclist, chslist) as res
        FROM
            df2
        """
    )
    return (dfres,)


@app.cell(hide_code=True)
def _(dfres, mo):
    mo.md(
        rf"""
    ## wordinsnt 的算法流程
    1. 输入的单词是 **{dfres.word[0]}**,句子是 **{dfres.snt[0]}**；
    2. 对应的单词原型是: **{dfres.lemma[0]}**
    3. 查询词典，得到单词对应的译文 *{dfres.eclist[0]}*
    4. 翻译英文句子得到的中文句子是 **{dfres.chsnt[0]}**;
    5. 中文句子分词后的结果是 **{dfres.chslist[0]}**；
    6. 单词译文和分词结果相交后 得到 **{dfres.res[0]}**
    """
    )
    return


if __name__ == "__main__":
    app.run()
