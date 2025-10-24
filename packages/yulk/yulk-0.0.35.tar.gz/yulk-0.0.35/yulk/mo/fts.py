import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _(sntso):
    df = sntso('overcome', limit=20)
    df
    return (df,)


@app.cell
def _(cola):
    cola.__qualname__
    return


@app.cell
def _(df):
    df.attrs 
    return


if __name__ == "__main__":
    app.run()
