import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _(loadpy):
    loadpy('api')
    return


@app.cell
def _(parkv):
    parkv('gramcnt','as soon as')
    return


if __name__ == "__main__":
    app.run()
