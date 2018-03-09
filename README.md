# Energy-Experiments-Data-Processing

An organized collection of scripts and notebooks for processing data obtained from [energy measurement scripts](https://github.com/danilomo/energy_measurement_scripts).

Organize your experimental design in a folder hierarchy, then use the [logprocessing](python/logprocessing.py) module for extracting a pandas dataframe for the obtained data.

Usage:

```
# creates a meta-data dictionary for a server with 32 cores
meta =  lp.MetadataBuilder().load_cpu_cores(32).build()

# creates a query dictionary based on the meta-data dictionary 
query = {
        "header": "timestamp cpu1 io_write io_read net_down net_up memory power",
        "columns": "cpu0.timestamp, 100 - cpu0.idle, io.writet, io.readt, net.download, net.upload, memory.used, mean( energy.power_active )"
}

df = lp.get_dataframe_from_folder(x, meta, query)
```
