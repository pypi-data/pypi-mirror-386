# myCommonLib
![Version 0.8.5](https://img.shields.io/badge/version-0.8.5-blue?style=plastic)
![Language Python 3.13.0](https://img.shields.io/badge/python-3.13.0-orange?style=plastic&logo=python)

Common library used in several project

## Installation

To install you can run the command

```console
python3 -m pip install MyCommonLib
```
or clone the project and install using the command 

```python
python3 -m pip install .
```

If you use the *pyprojext.toml* file you need to add the line 

```toml
"MyCommonLib",
```
in the *dependencies* array.

## Usage

```python
from MyCommonLib import Configure, Vers
```

## Contents

### Vers Class

Class for the manipulation of objects version following the [Semantic Versioning](https://semver.org/)


### Setup the logger Name