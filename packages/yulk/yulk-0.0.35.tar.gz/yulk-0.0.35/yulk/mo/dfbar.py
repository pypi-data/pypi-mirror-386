import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk 
    return


@app.cell
def _(en):
    df = en.dobjvn('open')
    df
    return (df,)


@app.cell
def _(df):
    df['cnt2'] = df.cnt 
    df
    return


@app.cell
def _(df):
    df.head(10).bars()
    return


@app.cell
def _(df):
    df.head(20).bar()
    return


if __name__ == "__main__":
    app.run()
