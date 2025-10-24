# CDMA Utilities

A collection of utilities related to processing 3D volumetric data and the CDMA group of Rostock University.

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
This is a very simple orthogonal stack viewer for 3D numpy arrays, to be used in jupyter notebooks. The interface is 
similar to napari:
```py
from cdma.display import IPyViewer
from cdma.mock_data.volumes import create_fake_stack

image_stack = create_fake_stack()

viewer = IPyViewer()
viewer.add_image(image_stack)
# viewer.add_mask(some_mask) # optionally add a mask that is blended over the image
viewer.show()
```
You will be able to scroll through 2D slices along a given axis. Also, the current slice intersection is shown:
![](assets/ipyviewer.png)
