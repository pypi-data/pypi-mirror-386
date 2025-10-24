
duckdb -cmd "INSTALL webmacro FROM community; LOAD webmacro; SELECT load_macro_from_url('http://file.yulk.net/sql/local9855.sql'); INSTALL httpserver FROM community;LOAD httpserver;SELECT httpserve_start('0.0.0.0', 9855, '')" 


