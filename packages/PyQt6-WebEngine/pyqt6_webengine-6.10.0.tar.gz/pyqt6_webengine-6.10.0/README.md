# PyQt6-WebEngine - Python Bindings for the Qt WebEngine Framework

PyQt6-WebEngine is a set of Python bindings for The Qt Company's Qt WebEngine
framework.  The framework provides the ability to embed web content in
applications and is based on the Chrome browser.  The bindings sit on top of
PyQt6 and are implemented as three separate modules corresponding to the
different libraries that make up the framework.


## Author

PyQt6-WebEngine is copyright (c) Riverbank Computing Limited.  Its homepage is
https://www.riverbankcomputing.com/software/pyqtwebengine/.

Support may be obtained from the PyQt mailing list at
https://www.riverbankcomputing.com/mailman/listinfo/pyqt/.


## License

PyQt6-WebEngine is released under the GPL v3 license and under a commercial
license that allows for the development of proprietary applications.


## Documentation

The documentation for the latest release can be found
[here](https://www.riverbankcomputing.com/static/Docs/PyQt6/).


## Installation

The GPL version of PyQt6-WebEngine can be installed from PyPI:

    pip install PyQt6-WebEngine

`pip` will also build and install the bindings from the sdist package but Qt's
`qmake` tool must be on `PATH`.

The `sip-install` tool will also install the bindings from the sdist package
but will allow you to configure many aspects of the installation.
