# vizlab-data-transfer

This package enables easy transferring of data to and from the VizLab! 

## How to set up

To use this package, we need a proper connection to Carnegie's local network. You can do this in a couple ways:

* By using a Carnegie-managed device connected to the CarnegieEmployees network
* By logging in with your Carnegie VPN

You'll need to set the VizLab local IP and appropriate port number - look to internal Carnegie resources for these:

```
from vizlab_data_transfer import vizlab

vizlab.set_ip(IP)
vizlab.set_port(PORT)
```

These values are stored internally by the package and persist between sessions, so set them once and you're good to go!

## How to use

This package is designed to be as straightforward as possible. To send Python data to the system, use the ```vizlab.send()``` method:

```
from vizlab_data_transfer import vizlab

vizlab.send(data) # give a single dataset
vizlab.send([table, fig1, fig2]) # or a list of them...
```

Currently we support a variety of Python objects:
* numpy ndarrays and recarrays
* astropy FITS Table objects
* matplotlib figures
* pandas dataframes
* Pillow images

Feel free to leave an issue on this repository if there's a Python object you'd like support for!

Likewise, to receive data back from the system use ```vizlab.receive()```:

```
from vizlab_data_transfer import vizlab

# NOTE: VizLab must be in 'receive' state before this is run so server is ready to meet this request
data = vizlab.receive() 
```

Currently only numeric data of type ```np.float32``` can be returned.

Please consult the examples folder for more detailed use-cases!