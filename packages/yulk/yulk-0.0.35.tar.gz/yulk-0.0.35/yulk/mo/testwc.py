import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell
def _():
    import yulk
    return


@app.cell
def _(en):
    df = en.dobjvn('open').head(10)
    df
    return (df,)


@app.cell
def _(df):
    df.epie() 
    return


@app.cell
def _(mo):
    mo.Html
    return


@app.cell
def _(df, mo, pd):
    import pygal
    pd.DataFrame.eline = lambda self, xcol=0, ycol=1, **kwargs: (
    	line_chart := pygal.Line(width=kwargs.get('width',640), height=kwargs.get('height',240)),
    	setattr(line_chart, 'title',  kwargs.get('title','') ),
    	line_chart.add(self.columns[ycol], [ row[ycol] for index, row in self.iterrows()] ),  # when ycol is a list 
    	mo.Html(line_chart.render(is_unicode=True))
    	)[-1]
    df.eline()
    return


@app.cell
def _(pd, plt):
    from wordcloud import WordCloud

    pd.DataFrame.wc = lambda self, x=0, y=1, **kwargs: (
        wc := WordCloud(width=800, height=400, background_color='white', max_words=100, font_path=None).generate_from_frequencies({ row[x]:row[y] for _,row in self.iterrows() }),
        plt.figure(figsize=(10, 5)),
        plt.imshow(wc, interpolation='bilinear'),
        plt.axis('off'), 
        plt.gcf() )[-1]

    return


if __name__ == "__main__":
    app.run()
