# CDMA Utilities

A collection of utilities related to processing 3D volumetric data and the CDMA group of Rostock University.

## Installation
This project uses [pre-commit](https://pre-commit.com/), please make sure to install it before making any
changes:

```bash
pip install pre-commit
cd cdma-utils
pre-commit install
```

It is a good idea to update the hooks to the latest version::
```bash
pre-commit autoupdate
```
Don't forget to tell your contributors to also install and use pre-commit.

## Styling
### CDMA Color Maps

`cdma_cmaps` can be used to create sequential or diverging color maps based on the colors of the CDMA logo. These palettes
can either be continuous (`as_cmap=True`) or discrete (`as_cmap=False`). The color maps can be reversed by setting the
`reverse` argument to `True`. The color maps can be used in matplotlib by passing them to the `cmap` argument.

#### Sequential
The sequential color maps are either orange or blue. They either fade to white or black, depending on the `kind` argument.
The color maps can also be reversed. Some examples are shown below:

![blue to white](assets/blue_to_white.png)
![](assets/blue_to_black.png)
![](assets/orange_to_white.png)
![](assets/orange_to_black.png)

#### Diverging
The diverging color maps can either start at orange or blue and end at the opposite color. The starting and end color
are _not_ the CDMA colors. The diverging color maps can also be reversed. Some examples are shown below:

![](assets/blue_to_orange.png)
![](assets/orange_to_blue.png)

### Napari Themes
These are two CDMA-themed napari themes. One is more for demonstration purposes, the other can also be used in a normal setting.

## Display
### IPyViewer
You know the problem: You just started a remote programming session, logged into the remote interpreter via SSH and your favorite IDE and then you encounter a bug related to 3D volumetric data. (Okay, maybe a little specific, but at least I have encountered this problem before.)

Now, normally, you would have to start a remote desktop session (just try that on the train!), open Napari, Fiji, or Slicer, and inspect the actual image data. Pretty bothersome.

But fear not! The IPyViewer can show your 3D data directly in the Jupyter notebook. It is basically a very specced down version of one of the above programs, but works with a napari-esque API:

```py
from cdma.display import IPyViewer
from cdma.mock_data import create_fake_stack

image_stack = create_fake_stack()

viewer = IPyViewer()
viewer.add_image(stack)
# viewer.add_mask(some_mask) # optionally add a mask that is blended over the image
viewer.show()
```
You will be able to scroll through 2D slices along a given axis. Also, the current slice intersection is shown:
![](assets/ipyviewer.png)
