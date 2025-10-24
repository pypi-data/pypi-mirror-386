# 2025.10.19, cp from file/py/echart.py | https://gallery.pyecharts.org/#/Table/table_base
import requests,os,math,builtins,pyecharts
import pandas as pd, numpy as np, marimo as mo
import pyecharts.options as opts
from pyecharts.charts import Bar,Pie,Gauge,WordCloud,PictorialBar,Line,Radar,Polar,Page,Liquid,Grid,Tree
from pyecharts.commons.utils import JsCode
from pyecharts.globals import SymbolType
from pyecharts.components import Table
from pyecharts.options import ComponentTitleOpts
from pyecharts.faker import Faker
from pyecharts import charts #, options as opts
from collections import Counter,defaultdict
from pyecharts.globals import CurrentConfig, NotebookType

pd.DataFrame.ebar = lambda self, xcol=0, ycol=1, **kwargs: mo.Html((
	bar := (Bar()
			.add_xaxis( [ row[xcol] for index, row in self.iterrows()])
			.add_yaxis(self.columns[ycol], [ row[ycol] for index, row in self.iterrows()] )
		    .set_global_opts(title_opts=opts.TitleOpts(title=kwargs.get('title','')))),
	bar.render_embed() )[-1])

pd.DataFrame.ewc = lambda self, xcol=0, ycol=1, **kwargs: mo.Html((
	topk := int(kwargs.get('topk',128)),
	c := WordCloud(init_opts=opts.InitOpts(width=kwargs.get('width','50vw'), height=kwargs.get('height','47vh'))).add(series_name=kwargs.get('title',''), data_pair=[ (row[xcol],float(row[ycol])) for index, row in self.iterrows()][0:topk]
		, word_size_range=[6, 66]).set_global_opts( title_opts=opts.TitleOpts(title=kwargs.get('title',''), title_textstyle_opts=opts.TextStyleOpts(font_size=23)),
        tooltip_opts=opts.TooltipOpts(is_show=True),
    ), 
	c.render_embed() )[-1])

pd.DataFrame.epie = lambda self, xcol=0, ycol=1, **kwargs: (Pie()
	.add("", [ (row[xcol], float(row[ycol])) for index, row in self.iterrows()])
	.set_global_opts(title_opts=opts.TitleOpts(title=kwargs.get('title','')))
	.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{c}"))).render_embed()

pd.DataFrame.donut = lambda self, xcol=0, ycol=1, **kwargs: (Pie()
	.add("", data_pair=[ (row[xcol], float(row[ycol])) for index, row in self.iterrows()], radius=["50%", "70%"], label_opts=opts.LabelOpts(is_show=False, position="center"),)
	.set_global_opts(title_opts=opts.TitleOpts(title=kwargs.get('title','')))
	.set_global_opts(legend_opts=opts.LegendOpts(pos_left="legft", orient="vertical"))
    .set_series_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
        ),
    )).render_embed()

pd.DataFrame.table = lambda self, **kwargs: (Table()
	.add(self.columns, [ list(row) for index, row in self.iterrows()])
	.set_global_opts(title_opts=ComponentTitleOpts(title=kwargs.get('title',''), subtitle=kwargs.get('subtitle','')))).render_embed()

pd.DataFrame.gauge = lambda self,xcol=0, ycol=1, **kwargs: (Gauge()
    .add(series_name= kwargs.get('label',""), data_pair=[[self.iloc[0, xcol], float(self.iloc[0, ycol])]])
    .set_global_opts(
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(is_show=True, formatter="{a} <br/>{b} : {c}%"),
    )).render_embed()

pd.DataFrame.eline = lambda self,xcol=0, ycol=1, **kwargs: (Line()
    .add_xaxis( [ row[xcol] for index, row in self.iterrows()] )
    .add_yaxis(self.columns[ycol], [ float(row[ycol]) for index, row in self.iterrows()])
    .set_global_opts(title_opts=opts.TitleOpts(title=kwargs.get('title',''))) ).render_embed()

pd.DataFrame.line2 = lambda self,xcol=0, **kwargs: (Line()
    .add_xaxis( [ row[xcol] for index, row in self.iterrows()] )
    .add_yaxis(self.columns[1], [ float(row[1]) for index, row in self.iterrows()])
	.add_yaxis(self.columns[2], [ float(row[2]) for index, row in self.iterrows()])
    .set_global_opts(title_opts=opts.TitleOpts(title=kwargs.get('title',''))) ).render_embed()

if __name__ == "__main__":
	pass
