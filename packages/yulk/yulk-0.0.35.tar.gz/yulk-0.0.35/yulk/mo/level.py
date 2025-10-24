import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk 
    return


@app.cell
def _(freq):
    freq('one')
    return


@app.cell
def _(requests):
    text= requests.get('http://file.yulk.net/skills.txt').text
    return (text,)


@app.cell
def _(sntdf, text):
    toks=sntdf(text)
    toks
    return


@app.cell
def _(mo):
    dflem = mo.sql(
        f"""
        SELECT lem, count(*) cnt, freq(lem) freq FROM toks group by lem order by cnt desc
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT * FROM ecdic limit 10 
        """
    )
    return


if __name__ == "__main__":
    app.run()
