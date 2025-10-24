# 2025.10.19
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

pd.DataFrame.wc = lambda self, x=0, y=1, **kwargs: (
    wc := WordCloud(width=kwargs.get('width',640), height=kwargs.get('height',480), background_color=kwargs.get('bgcolor','white'), max_words=kwargs.get('maxwords',128), font_path=None).generate_from_frequencies({ row[x]:row[y] for _,row in self.iterrows() }),
    plt.figure(figsize=(kwargs.get('figx',10), kwargs.get('figy',5))),
    plt.imshow(wc, interpolation='bilinear'),
    plt.axis('off'), 
	plt.title(kwargs['title']) if 'title' in kwargs else None,
    plt.gcf() )[-1]

pd.DataFrame.wordcloud = lambda self, txt=None, freq=None, title=None, **kwargs: (
    wc := WordCloud(background_color='white',** kwargs).generate(' '.join(self[txt])) if txt else 
          WordCloud(background_color='white', **kwargs).generate_from_frequencies(dict(zip(self.iloc[:,0], self[freq]))) if freq else 
          WordCloud(background_color='white',** kwargs).generate_from_frequencies(dict(zip(self.iloc[:,0], self.iloc[:,1]))) if len(self.columns)>=2 else 
          WordCloud(background_color='white', **kwargs).generate(' '.join(self.iloc[:,0])),
    plt.figure(figsize=kwargs.get('figsize', (10,6))),
    plt.imshow(wc, interpolation='bilinear'),
    plt.axis('off'),
    plt.title(title) if title else None,
    plt.show()
	)[-1]
