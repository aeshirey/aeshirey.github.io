I recently had the need to read in an adl:// file in some Python code I was working on. [Dask](https://dask.org/) has this capability, and most search results for reading ADL streams in Python point you to Dask itself. But I wanted to avoid using Dask for this.

I couldn't find anything that said how you can do this directly in Python, but it turns out [Dask just wraps fsspec](https://github.com/dask/dask/blob/7f5f7fe49298c2353977b99a081be47dc28bc358/dask/dataframe/io/csv.py#L764), and the code to do it using [fsspec](https://pypi.org/project/fsspec/) directly is pretty easy:


```python
import fsspec

filename = 'adl://path/to/file.csv'

adl_auth = {
	'tenant_id': "<tenant_id>", 
	'client_id': "<client_id>", 
	'client_secret': "PGNsaWVudF9zZWNyZXQ+"
}

fs_file = fsspec.open(filename, **adl_auth)

with fs_file.open() as fh:
   for line in fh:
      print(line)
```
