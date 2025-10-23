# magic-import

Import python object from string and return the reference of the object. The object can be a class, instance, variable and anything else, and can be from class, instance, module, global/local environment.

## Install

```
pip install magic-import
```

## Test Passed On Python Versions

- 2.7
- 3.2
- 3.3
- 3.4
- 3.5
- 3.6
- 3.7
- 3.8
- 3.9
- 3.10
- 3.11

## Usage

```
from magic_import import import_from_string

listdir = import_from_string("os.listdir")
files = listdir(".")
```


## Release

### 0.1.0

- First release

### 0.1.1
### 0.1.2
### 0.1.3
### 0.2.0

- Some updates.

### 0.2.2

- Test passed on all python versions.

### 0.2.3

- Doc update.
