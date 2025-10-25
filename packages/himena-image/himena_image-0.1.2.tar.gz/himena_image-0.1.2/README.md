# himena-image

[![PyPI - Version](https://img.shields.io/pypi/v/himena-image.svg)](https://pypi.org/project/himena-image)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/himena-image.svg)](https://pypi.org/project/himena-image)
[![codecov](https://codecov.io/gh/hanjinliu/himena-image/graph/badge.svg?token=Eifn4N21SV)](https://codecov.io/gh/hanjinliu/himena-image)

-----

![](images/window.png)

A [himena](https://github.com/hanjinliu/himena) plugin for image processing and image
analysis.

## Installation

```console
pip install himena-image[all]
```

To install this plugin to application, manually edit the setting from `Ctrl+,` or run:

```console
himena --install himena-image  # install the the default profile
himena <my-profile> --install himena-image  # install to <my-profile> profile
```

## Contents

This plugin contains following components:

1. Image IO (`himena_image.io`): Reading and writing TIFF, MRC, ND2 etc.
2. New and Samples (`himena_image.new`): Fetching [`scikit-image`](https://github.com/scikit-image/scikit-image) sample images.
3. Image Processing and Analysis (`himena_image.processing`): filtering, segmentation, feature extraction, etc.
4. Image Viewer Widgets (`himena_image.widgets`): 3D Image viewer widget from [`ndv`](https://github.com/pyapp-kit/ndv)
