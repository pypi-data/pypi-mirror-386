# 2025.10.12, called by cikuu/mod/yulk init,  no duckdb inside , totally independent
import requests,os,math,itertools,importlib,hashlib,json,builtins,inspect
import pandas as pd

sntmd5			= lambda text: hashlib.md5(text.strip().encode("utf-8")).hexdigest() #000003fa-c0b1-5d48-5490-ef083f787596
json.get		= lambda cmd, **kwargs :requests.get( f"http://{kwargs.get('host','yulk.net')}/{cmd}").json()  # json.get('pos~book'), return a json 
wget			= lambda filename, **kwargs: requests.get(filename).text if filename.startswith(('http:','https:')) else requests.get( f"http://{kwargs.get('host','file.yulk.net')}/{kwargs.get('folder','')}{filename}").text  #wget('skills.txt') ,folder='py/' 
getdf			= lambda name='sample', **kwargs: pd.DataFrame(requests.get(name).json()) if name.startswith(('http:','https:')) else pd.DataFrame( requests.get(f"http://{kwargs.get('host','file.yulk.net')}/{kwargs.get('folder','df')}/{name}.json").json() )
interlist		= lambda arr1, arr2: [s for s in arr2 if s in arr1]
wdobjvn			= lambda key, **kwargs: pd.DataFrame( requests.get( f"http://{kwargs.get('host','yulk.net')}/dobjvn('{key}',cp='{kwargs.get('cp','en')}')").json() ) #http://yulk.net/dobjvn('book',cp='cn')
wlempos			= lambda key, **kwargs: pd.DataFrame( requests.get( f"http://{kwargs.get('host','yulk.net')}/lempos('{key}',cp='{kwargs.get('cp','en')}')").json() )
checkin			= lambda: [setattr(builtins, k, f) for k, f in globals().items() if not k.startswith("_") and not '.' in k and not hasattr(builtins,k) and callable(f) ]
sntdf			= lambda snt: pd.DataFrame( requests.get(f'http://yulk.net/parse~{snt}').json()) # snt -> df 
scalar			= lambda df: df.values[0, 0] if len(df) > 0 else None  # scalar
pd.DataFrame.asc= lambda self, col=-1: self.sort_values(by=col if isinstance(col, str) else self.columns[col], ascending=False) # more in file.yulk.net/py/df.py

module_exists	= lambda module_name='cikuu.mod.attrdict': importlib.util.find_spec(module_name) is not None
logdice	= lambda common, cnt1, cnt2 : None if common is None or cnt1 is None or cnt2 is None else round(14 + math.log( 2 * int(common) / (int(cnt1) + int(cnt2) )), 2) if isinstance(common, int) else [ logdice(cnt, cnt1[i], cnt2[i]) for i, cnt in enumerate(common) ]
swap	= lambda s :  s[0:-2] + s[-1] + s[-2] # dobjvn -> dobjnv
isdigit	= lambda s:  (s:=s.strip(), False if not s else s[1:].isdigit() if s[0] == '-' else s.isdigit())[-1]
read	= lambda snt: requests.get('http://yulk.net/xgetreadability',params={'snt':snt}).json()
formal	= lambda snt: requests.get('http://yulk.net/xgetformality',params={'snt':snt}).json() #http://yulk.net/xgetformality?snt=It%20is%20ok. |http://yulk.net/xgetreadability?snt=It%20is%20ok.
cola	= lambda snt: requests.get('http://yulk.net/xgetcola',params={'snt':snt}).json()
xget	= lambda name, **kwargs: requests.get(f'http://yulk.net/xget{name}',params=kwargs).json()  # xget('cola', snt='It is ok')
dims	= lambda txt: xget("dsk", snt=txt).get('doc', {})
interlist	= lambda vec1,vec2 : [w for w in vec1 if w in vec2]
permute		= lambda q='on/in/at the train',sepa='/' :	pd.DataFrame( {"chunk": [' '.join([a for a in ar if a]).strip().replace('  ',' ') for ar in itertools.product( *[a.strip().split(sepa) for a in q.strip().split() ])]})
split	= lambda s, inter=';', intra=':', columns=None: pd.DataFrame( [pair.split(intra) for pair in s.split(inter)], columns=columns.strip().split(',') if columns else columns)

def loadpy(name):  ## load duck/yulk..., from pyexec/*.py 
	try:
		dic = {}
		compiled_code = compile(requests.get(f'http://file.yulk.net/py/{name}.py').text, f"{name}.py", 'exec') 
		exec(compiled_code,dic)
		[setattr(builtins, name, obj) for name, obj in dic.items() if not name.startswith("_") and not '.' in name and callable(obj)] # latter will overwrite former : and not hasattr(builtins,name)
	except Exception as e:
		print ("loadpy ex:", name, e, flush=True) 
	return pd.DataFrame([{"name":name, 'function':str(obj)} for name, obj in dic.items() if not name.startswith("_") and callable(obj)])

def loglike(a,b,c,d):  #from: http://ucrel.lancs.ac.uk/llwizard.html
	from math import log as ln
	try:
		if a is None or a <= 0 : a = 0.000001
		if b is None or b <= 0 : b = 0.000001
		if c is None or c <= 0 : c = 0.000001
		if d is None or d <= 0 : d = 0.000001
		E1 = c * (a + b) / (c + d)
		E2 = d * (a + b) / (c + d)
		G2 = round(2 * ((a * ln(a / E1)) + (b * ln(b / E2))), 2)
		if (a * d < b * c): G2 = 0 - G2 #if minus or  (minus is None and a/c < b/d): G2 = 0 - G2
		return round(G2,1)
	except Exception as e:
		print ("likelihood ex:",e, a,b,c,d)
		return 0 #duckdb.create_function("loglike", loglike, [int,int,int,int], float)

def keyness(df1, df2, **kwargs):  # keyness(dfcn, dfen) 
	x1,y1,x2,y2 = kwargs.get('x1',0), kwargs.get('y1',1),kwargs.get('x2',0),kwargs.get('y2',1)
	src		= {row[x1]: int(row[y1]) for index, row in df1.iterrows()} if hasattr(df1, 'iterrows') else {row[x1]: int(row[y1]) for row in df1.iter_rows()} # <class 'polars.dataframe.frame.DataFrame'> of sql
	tgt		= {row[x2]: int(row[y2]) for index, row in df2.iterrows()} if hasattr(df2, 'iterrows') else {row[x2]: int(row[y2]) for row in df2.iter_rows()}
	sum1	= src.get("_sum", sum( [i for s,i in src.items() if not s.startswith('_')]) ) + 0.000001 # read from attrs 
	sum2	= tgt.get("_sum", sum( [i for s,i in tgt.items() if not s.startswith('_')]) ) + 0.000001
	words	= src.keys() if 'leftonly' in kwargs else set( list(src.keys()) + list(tgt.keys()) )
	rows	= [ (w, src.get(w,0), tgt.get(w,0), round(100*src.get(w,0)/sum1,2), round(100*tgt.get(w,0)/sum2,2), loglike(src.get(w,0), tgt.get(w,0), sum1, sum2 )) for w in words if not w.startswith('_sum') ] #_look forward to _VBG
	rows.sort(key=lambda row:row[-1], reverse='asc' in kwargs) 
	return pd.DataFrame(rows, columns=['word','cnt1', 'cnt2', 'perc1','perc2', 'keyness']) #[('two', 72.0, 15, 0, 123, 1233), ('three', -23.8, 0, 125, 123, 1233), ('one', -0.0, 12, 123, 123, 1233)]

def knmap(src:dict={"one":12, "two":15, "_sum": 123}, refer:dict={"one":123, "three":125, "_sum": 1233}, outer:bool = True, reverse:bool=True): 
	''' [('two', 72.0, 15, 0, 123, 1233), ('three', -23.8, 0, 125, 123, 1233), ('one', -0.0, 12, 123, 123, 1233)] | input: two si dic {s:i}, with _sum inside  '''
	if hasattr(src, 'DataFrame'): src = src.DataFrame() #sql.run.resultset.ResultSet    %sql
	if hasattr(refer, 'DataFrame'): refer = refer.DataFrame()
	src		=  { row[0]: row[1] for index, row in src.iterrows()} if isinstance(src, pd.core.frame.DataFrame) else dict(src) 
	refer	=  { row[0]: row[1] for index, row in refer.iterrows()} if isinstance(refer, pd.core.frame.DataFrame) else dict(src)  	#src, refer = dict(src), dict(refer) 
	sum1	= src.get("_sum", sum( [i for s,i in src.items()]) ) + 0.000001
	sum2	= refer.get("_sum", sum( [i for s,i in refer.items()]) ) + 0.000001
	words	= set( list(src.keys()) + list(refer.keys()) ) if outer else src.keys()
	rows	= [ (w, round(100*src.get(w,0)/sum1,2), round(100*refer.get(w,0)/sum2,2), src.get(w,0), refer.get(w,0), likelihood(src.get(w,0), refer.get(w,0), sum1, sum2 )) for w in words if not w.startswith('_sum') ] #_look forward to _VBG
	rows.sort(key=lambda row:row[-1], reverse=reverse) 
	return pd.DataFrame(rows, columns=['word','src%','refer%','src','refer','keyness']) #[('two', 72.0, 15, 0, 123, 1233), ('three', -23.8, 0, 125, 123, 1233), ('one', -0.0, 12, 123, 123, 1233)]

def kmeans(words=['one','two','three','apple','orange','banana'], n_clusters=3, **kwargs):  # added 2025.8.1
	from sklearn.cluster import KMeans 
	pairs = [(w, vec(w)) for w in words]
	return dict(zip( [w for w,v in pairs if v], KMeans(n_clusters,** kwargs).fit_predict([v for w,v in pairs if v]) ))
	#return pd.DataFrame({'word': [w for w,v in pairs if v], 'group': KMeans(n_clusters,** kwargs).fit_predict([v for w,v in pairs if v])})

pd.DataFrame.kmeans	= lambda self, n=3, col=0,  topk=128, **kwargs: (
    words	:= [ row[col] for index, row in self.iterrows()][0:topk],
	dic		:= kmeans(words, n), 
	self.insert(len(self.columns),column='kmeans' if 'kmeans' not in self.columns else f'kmeans_{col}', value=[ dic.get(row[col],-1) for index, row in self.iterrows() ]),
	self )[-1]   

fourattrs = lambda *args, **kwargs: ( #dobjvn,open,close,raise,increase
	arr:= [ wordattr(w, args[0]) for w in args[1:] ],
	cnt:= len(args) -1, 
	{ args[idx+1]: ','.join( [k for k in arr[idx].keys() if all([ k not in arr[i] for i in range(cnt) if i != idx ]) ][0:4]) for idx in range(cnt)}
	)[-1]

# http://yulk.net/xgetsntscos?snt=It%20is%20ok.|It%20is%20great.|It%20is%20very%20great.
def topicsnt( snts=["it is ok", "It is great.","It is very great."]):
	''' permute every two sents cos score '''
	allsnts	= '|'.join( [s.strip() for s in snts if s.strip()])
	lensnts = len(snts)
	rows = []
	for i ,snt in enumerate(snts): 
		res = requests.get("http://yulk.net/xgetsntscos", params={"snt": snt + '|' + allsnts}).json()
		if isinstance(res, dict) and 'data' in res: 
			scores = list(res.get('data',{}).values())
			if len(scores) == lensnts: 
				for j,score in enumerate(scores): 
					rows.append( {"src": i, "tgt":j , "cos": score} ) #, 'snt-i': snts[i], 'snt-j': snts[j]
	return pd.DataFrame(rows)

def sntscos( src, refers:str='It is ok.\nIt is great.\nIt is good.', sepa:str='\n'):
	res = xget('sntscos', snt='|'.join([src] + [s.strip() for s in refers.strip().split(sepa) if s.strip()] ) )
	return pd.DataFrame([ {"src": src, "snt": snt, "score": round(score,4) } for snt, score in res.get('data',{}).items()])

cloze	= lambda snt, **kwargs: pd.DataFrame( xget('cloze', snt=snt, **kwargs))
#aes		= lambda text, **kwargs: pd.DataFrame([{'id':i+1, 'text':s} | xget('aes', text=s, **kwargs) for i,s in enumerate([text] if isinstance(text, str) else text) ])
def aes(text, **kwargs): #aes(['It is ok.','It is great.'])
	if isinstance(text, str): text = [text]
	res  = xget('aes',text=text[0])
	df	 = pd.DataFrame(res.items(), columns=['dim','text1'])
	for i, s in enumerate(text[1:]): 
		df[f"text{i+2}"] = list(xget('aes',text=s).values())
	return df

icall		= lambda name: globals().get(name,  getattr(builtins, name) if hasattr(builtins, name) else eval(name) )  # en.framehas
is_builtin	= lambda func:  hasattr(func, '__name__') and getattr(builtins, func.__name__, None) is func 
allfuncs	= lambda :  {name +'|' + str(inspect.signature(obj)) : str(getattr(obj, '__code__')) for name, obj in vars(builtins).items() if not name.startswith('_') and callable(obj) and hasattr(obj, '__code__')}
which		= lambda fname='icall': ( f :=icall(fname), 
	{ "globals()": fname in globals(), 
	"builtins": hasattr(builtins, fname), 
	"parameters": str(inspect.signature(f)), 
	"code": str(getattr(f, '__code__')) if hasattr(f, '__code__') else 'no code',
	} )[-1]
	
if __name__ == "__main__":
	pass

'''
xget('sntscos', snt='It is ok.|It is great.|It is good.')
{
"src":"It is ok."
"snts":[
"It is ok."
"It is great."
"It is good."
]
"sntscos-input":{
"snt":"It is ok.|It is great.|It is good."
}
"data":{
"It is great.":0.8041319324645375
"It is good.":0.8836191263324187
}
}

[E 251023 21:49:47 middleware:496] Failed to connect to ws://localhost:3119/lsp/pylsp?file=sntscos.py after 3 attempts. Final error: [Errno 111] Connect call failed ('127.0.0.1', 3119)
[E 251023 21:49:47 middleware:575] WebSocket proxy error for ws://localhost:3119/lsp/pylsp?file=sntscos.py: [Errno 111] Connect call failed ('127.0.0.1', 3119)
[E 251023 21:49:47 middleware:580] LSP server appears to be down at ws://localhost:3119/lsp/pylsp?file=sntscos.py. Check if the LSP server started successfully.
[E 251023 21:49:47 middleware:415] Error proxying websocket: Cannot call "send" once a close message has been sent.
'''