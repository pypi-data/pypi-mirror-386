# protozfits-python

Low-level reading and writing of zfits files using google protocol buffer objects.

To analyze data, you might be more interested in using a [`ctapipe`](https://github.com/cta-observatory/ctapipe)
plugin to load your data into ctapipe. There are currently several plugins using this library as a dependency
for several CTA(O) prototypes:

* `ctapipe_io_lst` to read LST-1 commissioning raw data: https://github.com/cta-observatory/ctapipe_io_lst
* `ctapipe_io_nectarcam` to read NectarCam commissiong raw data: https://github.com/cta-observatory/ctapipe_io_nectarcam/
* `ctapipe_io_zfits` for general reading of CTA zfits data, currently only supports DL0 as written during the ACADA-LST test campaign.

Note: before version 2.4, the protozfits python library was part of the [`adh-apis` Repository](https://gitlab.cta-observatory.org/cta-computing/common/acada-array-elements/adh-apis/).

To improve maintenance, the two repositories were decoupled and this repository now only hosts the python bindings (`protozfits`).
The needed C++ `libZFitsIO` is build from a git submodule of the `adh-apis`.

Table of Contents

* [Installation](#installation)
* [Usage](#usage)
   * [Open a file](#open-a-file)
   * [Get an event](#getting-an-event)
   * [RunHeader](#runHeader)
   * [Table header](#table-header)
   * [Performance](#pure-protobuf-mode)
* [Command-Line Tools](#command-line-tools)

# Installation

## Users

This package is published to [PyPI](https://pypi.org/projects/protozfits) and [conda-forge](https://anaconda.org/conda-forge/protozfits).
PyPI packages include pre-compiled `manylinux` wheels (no macOS wheels though) and conda packages are built for Linux and macOS.

When using conda, it's recommended to use the [`miniforge`](https://github.com/conda-forge/miniforge#miniforge3) conda distribution,
as it is fully open source and comes with the faster mamba package manager.

So install using:
```
pip install protozfits
```
or
```
mamba install protozfits
```

## For development

This project is build using `scikit-build-core`, which supports editable installs recompiling the project on import by setting a couple of `config-options` for pip.
See <https://scikit-build-core.readthedocs.io/en/latest/configuration.html#editable-installs>.

To setup a development environment, create a venv, install the build requirements and then
run the pip install command with the options given below:
```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install 'scikit-build-core[pyproject]' pybind11 'setuptools_scm[toml]'
$ pip install -e '.[all]' --no-build-isolation
```

You can now e.g. run the tests:
```
$ pytest src
```

`scikit-build-core` will automatically recompile the project when importing the library.
Some caveats remain though, see the scikit-build-core documentation linked above.

## Usage

If you are just starting with proto-z-fits files and would like to explore the file contents, try this:

### Open a file
```
>>> from protozfits import File
>>> example_path = 'protozfits/tests/resources/example_9evts_NectarCAM.fits.fz'
>>> file = File(example_path)
>>> file
File({
    'RunHeader': Table(1xDataModel.CameraRunHeader),
    'Events': Table(9xDataModel.CameraEvent)
})
```

From this we learn, the `file` contains two `Table` named `RunHeader` and `Events` which
contains 9 rows of type `CameraEvent`. There might be more tables with
other types of rows in other files. For instance LST has its `RunHeader` called `CameraConfig`.

### Getting an event

Usually people just iterate over a whole `Table` like this:
```python
for event in file.Events:
    # do something with the event
    pass
```

But if you happen to know exactly which event you want, you can also
directly get an event, like this:
```python
event_17 = file.Events[17]
```

You can also get a range of events, like this:
```python
for event in file.Events[100:200]:
    # do something events 100 until 200
    pass
```

It is not yet possible to specify negative indices, like `file.Events[:-10]`
does *not work*.

If you happen to have a list or any iterable or a generator with event ids
you are interested in you can get the events in question like this:

```python
interesting_event_ids = range(100, 200, 3)
for event in file.Events[interesting_event_ids]:
    # do something with intesting events
    pass
```

### RunHeader

Even though there is usually **only one** run header per file, technically
this single run header is stored in a Table. This table could contain multiple
"rows" and to me it is not clear what this would mean... but technically it is
possible.

At the moment I would recommend getting the run header out of the file
we opened above like this (replace RunHeader with CameraConfig for LST data):

```python
assert len(file.RunHeader) == 1
header = file.RunHeader[0]
```


For now, I will just get the next event
```python
event = file.Events[0]
type(event)
<class 'protozfits.CameraEvent'>
event._fields
('telescopeID', 'dateMJD', 'eventType', 'eventNumber', 'arrayEvtNum', 'hiGain', 'loGain', 'trig', 'head', 'muon', 'geometry', 'hilo_offset', 'hilo_scale', 'cameraCounters', 'moduleStatus', 'pixelPresence', 'acquisitionMode', 'uctsDataPresence', 'uctsData', 'tibDataPresence', 'tibData', 'swatDataPresence', 'swatData', 'chipsFlags', 'firstCapacitorIds', 'drsTagsHiGain', 'drsTagsLoGain', 'local_time_nanosec', 'local_time_sec', 'pixels_flags', 'trigger_map', 'event_type', 'trigger_input_traces', 'trigger_output_patch7', 'trigger_output_patch19', 'trigger_output_muon', 'gps_status', 'time_utc', 'time_ns', 'time_s', 'flags', 'ssc', 'pkt_len', 'muon_tag', 'trpdm', 'pdmdt', 'pdmt', 'daqtime', 'ptm', 'trpxlid', 'pdmdac', 'pdmpc', 'pdmhi', 'pdmlo', 'daqmode', 'varsamp', 'pdmsum', 'pdmsumsq', 'pulser', 'ftimeoffset', 'ftimestamp', 'num_gains')
event.hiGain.waveforms.samples
array([241, 245, 248, ..., 218, 214, 215], dtype=int16)
```

An LST event will look something like so:
```python
>>> event
CameraEvent(
    configuration_id=1
    event_id=1
    tel_event_id=1
    trigger_time_s=0
    trigger_time_qns=0
    trigger_type=0
    waveform=array([  0,   0, ..., 288, 263], dtype=uint16)
    pixel_status=array([ 0,  0,  0,  0,  0,  0,  0, 12, 12, 12, 12, 12, 12, 12], dtype=uint8)
    ped_id=0
    nectarcam=NectarCamEvent(
        module_status=array([], dtype=float64)
        extdevices_presence=0
        tib_data=array([], dtype=float64)
        cdts_data=array([], dtype=float64)
        swat_data=array([], dtype=float64)
        counters=array([], dtype=float64))
    lstcam=LstCamEvent(
        module_status=array([0, 1], dtype=uint8)
        extdevices_presence=0
        tib_data=array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=uint8)
        cdts_data=array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0], dtype=uint8)
        swat_data=array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0], dtype=uint8)
        counters=array([  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
                 0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
                 0,   0,   1,   0,   0,   0,  31,   0,   0,   0, 243, 170, 204,
                 0,   0,   0,   0,   0], dtype=uint8)
        chips_flags=array([    0,     0,     0,     0,     0,     0,     0,     0, 61440,
                 245, 61440,   250, 61440,   253, 61440,   249], dtype=uint16)
        first_capacitor_id=array([    0,     0,     0,     0,     0,     0,     0,     0, 61440,
                 251, 61440,   251, 61440,   241, 61440,   245], dtype=uint16)
        drs_tag_status=array([ 0, 12], dtype=uint8)
        drs_tag=array([   0,    0, ..., 2021, 2360], dtype=uint16))
    digicam=DigiCamEvent(
        ))
>>> event.waveform
array([  0,   0,   0, ..., 292, 288, 263], dtype=uint16)
```

`event` supports tab-completion, which I regard as very important while exploring.
It is implemented using [`collections.namedtuple`](https://docs.python.org/3.6/library/collections.html#collections.namedtuple).
I tried to create a useful string representation, it is very long, yes ... but I
hope you can still enjoy it:
```python
>>> event
CameraEvent(
    telescopeID=1
    dateMJD=0.0
    eventType=<eventType.NONE: 0>
    eventNumber=97750287
    arrayEvtNum=0
    hiGain=PixelsChannel(
        waveforms=WaveFormData(
            samples=array([241, 245, ..., 214, 215], dtype=int16)
            pixelsIndices=array([425, 461, ..., 727, 728], dtype=uint16)
            firstSplIdx=array([], dtype=float64)
            num_samples=0
            baselines=array([232, 245, ..., 279, 220], dtype=int16)
            peak_time_pos=array([], dtype=float64)
            time_over_threshold=array([], dtype=float64))
        integrals=IntegralData(
            gains=array([], dtype=float64)
            maximumTimes=array([], dtype=float64)
            tailTimes=array([], dtype=float64)
            raiseTimes=array([], dtype=float64)
            pixelsIndices=array([], dtype=float64)
            firstSplIdx=array([], dtype=float64)))
# [...]
```

### Table header

`fits.fz` files are still normal [FITS files](https://fits.gsfc.nasa.gov/) and
each Table in the file corresponds to a so called "BINTABLE" extension, which has a
header. You can access this header like this:
```
>>> file.Events
Table(100xDataModel.CameraEvent)
>>> file.Events.header
# this is just a sulection of all the contents of the header
XTENSION= 'BINTABLE'           / binary table extension
BITPIX  =                    8 / 8-bit bytes
NAXIS   =                    2 / 2-dimensional binary table
NAXIS1  =                  192 / width of table in bytes
NAXIS2  =                    1 / number of rows in table
TFIELDS =                   12 / number of fields in each row
EXTNAME = 'Events'             / name of extension table
CHECKSUM= 'BnaGDmS9BmYGBmY9'   / Checksum for the whole HDU
DATASUM = '1046602664'         / Checksum for the data block
DATE    = '2017-10-31T02:04:55' / File creation date
ORIGIN  = 'CTA'                / Institution that wrote the file
WORKPKG = 'ACTL'               / Workpackage that wrote the file
DATEEND = '1970-01-01T00:00:00' / File closing date
PBFHEAD = 'DataModel.CameraEvent' / Written message name
CREATOR = 'N4ACTL2IO14ProtobufZOFitsE' / Class that wrote this file
COMPILED= 'Oct 26 2017 16:02:50' / Compile time
TIMESYS = 'UTC'                / Time system
>>> file.Events.header['DATE']
'2017-10-31T02:04:55'
>>> type(file.Events.header)
<class 'astropy.io.fits.header.Header'>
```
The header is provided by [`astropy`](http://docs.astropy.org/en/stable/io/fits/#working-with-fits-headers).

### pure protobuf mode

The library by default converts the protobuf objects into namedtuples and converts the `AnyArray` data type
to numpy arrays. This has some runtime overhead.
In case you for example know exactly what you want
from the file, then you can get a speed-up by passing the `pure_protob=True` option:
```
>>> from protozfits import File
>>> file = File(example_path, pure_protobuf=True)
>>> event = next(file.Events)
>>> type(event)
<class 'ProtoDataModel_pb2.CameraEvent'>
```

Now iterating over the file is faster than before.
But you have no tab-completion and some contents are less useful for you:
```
>>> event.eventNumber
97750288   # <--- just fine
>>> event.hiGain.waveforms.samples

type: S16
data: "\362\000\355\000 ... "   # <---- goes on "forever" .. raw bytes of the array data
>>> type(event.hiGain.waveforms.samples)
<class 'CoreMessages_pb2.AnyArray'>
```

You can convert these `AnyArray`s into numpy arrays like this:
```
>>> from protozfits import any_array_to_numpy
>>> any_array_to_numpy(event.hiGain.waveforms.samples)
array([242, 237, 234, ..., 218, 225, 229], dtype=int16)
```

## Command-Line Tools

This module comes with a command-line tool that can re-compress zfits files using different
options for the default and specific column compressions.
This can also be used to extract the first N events from a large file, e.g. to produce smaller files
for unit tests.

Usage:

```
$ python -m protozfits.recompress_zfits --help
```
