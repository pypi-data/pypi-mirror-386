import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import yulk
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT
            *
        FROM
            en.svo
        where
            v = 'hit'
        """
    )
    return


if __name__ == "__main__":
    app.run()
