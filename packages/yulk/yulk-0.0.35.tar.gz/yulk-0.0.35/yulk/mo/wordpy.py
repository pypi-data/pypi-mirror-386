import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import  yulk
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT * FROM wordpy where key = 'demon'
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT *, lemmf(key) mf FROM wordlist where key like '%rupt' order by mf desc 
        """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        create OR REPLACE view spellerr as (from read_parquet('http://file.yulk.net/parkv/spellerr.parquet'));
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        create OR REPLACE view gramcnt as (from read_parquet('http://file.yulk.net/parkv/gramcnt.parquet'));
        SELECT * FROM gramcnt limit 10 
        """
    )
    return


@app.cell
def _(requests):
    xget	= lambda name, **kwargs: requests.get(f'http://yulk.net/xget{name}',params=kwargs).json()
    xget('cloze',snt='It * ok.')
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""

        """
    )
    return


if __name__ == "__main__":
    app.run()
