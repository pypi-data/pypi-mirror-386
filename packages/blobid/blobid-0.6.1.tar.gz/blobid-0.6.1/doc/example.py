import numpy as np
from blobid import get_labels

# import a VOF felid, for illustration we'll use a 2D slice
vof = 1.0 - np.load("tests/resources/fs_vof.npy")[:, 0, :]

# calculate labels
labels = get_labels(vof, periodic=[True, False])

# make the plots
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# create a nice coloring for the labels
base = plt.colormaps["tab20"]
colors = [base(i % base.N) for i in np.unique(labels)]
colors[0] = (0, 0, 0, 1)  # unlabeled cells
labels_cmap = ListedColormap(colors)

vof_img = (1.0-vof.transpose()[::-1, :]).astype(np.float32)

fig, ax = plt.subplots(nrows=2)
ax[0].imshow(vof_img, vmin=0, vmax=1, cmap='binary')

ax[1].imshow(labels.transpose()[::-1, :], cmap=labels_cmap, rasterized=True)
ax[1].imshow(np.ones_like(vof_img), vmin=0, vmax=1, cmap='binary', alpha=vof_img)

for a in ax:
    a.set_xticks([])
    a.set_yticks([])
    a.set_aspect('equal')

# ensure deterministic SVG output
plt.rcParams['svg.hashsalt']="blobid-python"

plt.subplots_adjust(hspace=0)
plt.savefig("doc/example.svg", transparent=True, bbox_inches='tight', pad_inches=0, metadata={'Date': None})
