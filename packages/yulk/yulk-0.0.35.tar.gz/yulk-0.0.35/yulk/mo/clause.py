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
    return (text,)


@app.cell
def _(loadpy):
    loadpy('nlpapi')
    return


@app.cell
def _(clause, text):
    clause(text)
    return


if __name__ == "__main__":
    app.run()
