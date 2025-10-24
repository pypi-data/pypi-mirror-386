import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk 
    return


@app.cell
def _(requests):
    text= requests.get('http://file.yulk.net/skills.txt').text
    text
    return (text,)


@app.cell
def _(sntdf, text):
    df=sntdf(text)
    df
    return (df,)


@app.cell
def _(df, mo):
    _df = mo.sql(
        f"""
        from df
        """
    )
    return


if __name__ == "__main__":
    app.run()
