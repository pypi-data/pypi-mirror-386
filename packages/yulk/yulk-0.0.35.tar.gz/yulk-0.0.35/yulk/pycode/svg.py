#2025.10.19 cp file/py/svg.py  | https://www.pygal.org/en/stable/  | pygal.Bar()(1, 3, 3, 7)(1, 6, 6, 4).render()
import os, json, pygal 
import pandas as pd, marimo as mo

pd.DataFrame.svgline = lambda self, xcol=0, ycol=1, **kwargs: (
	line_chart := pygal.Line(width=kwargs.get('width',640), height=kwargs.get('height',240)),
	setattr(line_chart, 'title',  kwargs.get('title','') ),
	line_chart.add(self.columns[ycol], [ row[ycol] for _, row in self.iterrows()] ),  # when ycol is a list 
	mo.Html(line_chart.render(is_unicode=True))
	)[-1]

pd.DataFrame.svgbar = lambda self, xcol=0, ycol=1, **kwargs: (
	chart := pygal.Bar(width=kwargs.get('width',640), height=kwargs.get('height',240)), 
	setattr(chart, 'title',  kwargs.get('title','') ),
	setattr(chart, 'x_labels',  [ row[xcol] for index, row in self.iterrows()]),
	ycols := ycol if isinstance(ycol, list) else [ycol], 
	[chart.add(self.columns[y], [ row[y] for index, row in self.iterrows()]) for y in ycols], 
	mo.Html(chart.render(is_unicode=True)),
	)[-1]

pd.DataFrame.svgpie = lambda self, xcol=0, ycol=1, **kwargs: (
	chart := pygal.Pie(width=kwargs.get('width',200), height=kwargs.get('height',100)),
	setattr(chart, 'title',  kwargs.get('title','') ),
	[ chart.add(row[xcol], row[ycol]) for index, row in self.iterrows()],
	mo.Html(chart.render(is_unicode=True)) 
	)[-1]

pd.DataFrame.gauge = lambda self, xcol=0, ycol=1, **kwargs: (
	chart := pygal.Gauge(human_readable=True), 
	setattr(chart, 'title',  kwargs.get('title','') ),
	setattr(chart, 'range',  [0,100] ), 	#gauge_chart.range = [0, 10000]
	[ chart.add(row[xcol], row[ycol]) for _, row in self.iterrows()],
	mo.Html(chart.render(is_unicode=True))
	)[-1]

# https://www.pygal.org/en/stable/documentation/types/radar.html
pd.DataFrame.radar = lambda self, y=None, x=0,**kwargs: ( # or y is a list: [1,'col3'] 
	chart := pygal.Radar(), 
	setattr(chart, 'title',  kwargs.get('title','') ),
	setattr(chart, 'x_labels',  [ str(row[x]) for _, row in self.iterrows() ] ), 	
	cols := [ col for col in self.columns if pd.api.types.is_numeric_dtype(self[col])] if y is None else [ self.columns[col] if isinstance(col, int) else col for col in y], 
	[ chart.add(col, self[col].tolist() ) for col in cols ],
	mo.Html(chart.render(is_unicode=True))
	)[-1]

# synonym of wordmf 
pd.DataFrame.dot = lambda self, y=None, x=0,**kwargs: (
	chart := pygal.Dot(x_label_rotation=kwargs.get('rotation',30),width=kwargs.get('width',640),height=kwargs.get('height',350)), 
	setattr(chart, 'title',  kwargs.get('title','') ),
	setattr(chart, 'x_labels',  [ str(row[x]) for _, row in self.iterrows() ] ), 	
	cols := [ col for col in self.columns if pd.api.types.is_numeric_dtype(self[col])] if y is None else [ self.columns[col] if isinstance(col, int) else col for col in y], 
	[ chart.add(col, self[col].tolist() ) for col in cols ],
	mo.Html(chart.render(is_unicode=True))
	)[-1]

# sql("select word,cn,en from dobjvn where key='open' order by cn desc limit 30").pyramid()
pd.DataFrame.pyramid = lambda self, x=0, y1=1, y2=2, **kwargs: (
	chart := pygal.Pyramid(human_readable=True,height=kwargs.get('height',400)),  #, legend_at_bottom=True
	setattr(chart, 'title',  kwargs.get('title','') ),
	setattr(chart, 'x_labels',  [ str(row[x]) for _, row in self.iterrows() ] ), 	
	y1 := y1 if isinstance(y1, str) else self.columns[y1],
	y2 := y2 if isinstance(y2, str) else self.columns[y2],
	chart.add(y1, self[y1].tolist()),
	chart.add(y2, self[y2].tolist()),
	mo.Html(chart.render(is_unicode=True))
	)[-1]
