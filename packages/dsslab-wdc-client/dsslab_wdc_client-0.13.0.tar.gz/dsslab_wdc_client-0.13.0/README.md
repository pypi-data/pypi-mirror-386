# Description
This project includes a *very* small client to access data form 
the WebDataCollector-API. It is meant to provide a simple means 
of accessing the data in Json or as Panda-DataFrames.

# Usage

```
from dsslab.wdc_client import *

# Somehow initialize environment variables for 
# "WDC_HOST" and "WDC_TOKEN". 
load_dotenv()

client = WDCClient.fromEnv()
df = client.loadAsDataFrame(
	'api/endpoint...', {'param1', 'value will be encoded'})
```

For more information about the client and usable endpoints, 
see the project homepage of WDC or directly consult the Documentation.

# Changelog
- 0.13.0	Add method WDCClient.loadAsDF(endpoint: str, **params) for brevity
- 0.12.0	Fix minor bug for Rate-Limiting.
- 0.11.0	Transparently handle Rate-Limiting from server.
- 0.10.0	Moved to new package structure with the namespace dsslab.

# Old changelog 
- 0.9.1		Make package obsolete.
- 0.9.0		Add method WDCClient#put to create PUT-Requests
- 0.8.2		Fix for duplicate parameters when paging.
- 0.8.1		Simplify new methods for loading a DomainGraph.
- 0.8.0		Added new methods for loading DomainGraphs.
- 0.7.3		Fix README
- 0.7.2		Include link for generated documentation
- 0.7.1 	Added generated documentation
- 0.7.0		Added new method WDCClient.loadDomainGraph for loading a DomainGraph as NetworkX-Object
- 0.6.0		WDCClient throws an WDCException if a request to the server fails
- 0.5.0		New signatures and methods taking care of encodings and working on large results
- 0.4.3		Add dependencies pandas["excel, plot"] as they are likely to be used.
- 0.4.2		Enhance README with Changelog and code-example.
- 0.4.1		Include a preferred variant for creating WDCClients from the Environment	