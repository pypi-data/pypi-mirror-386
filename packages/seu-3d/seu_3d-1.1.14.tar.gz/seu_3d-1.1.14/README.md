# SEU-3D

## description

3d visualization and analysis plugin for spatial transcription embryo base on napari

## updata log

[1.1.14] fix buge

[1.1.13] add button to read colormap json file

[1.1.12]

[1.1.11] fix buges

[1.1.10] Fix buges and optimize SelectXYZ

[1.1.9] Multi-gene analysis adjusts image contrast by channel

[1.1.8] 1.A Z-axis control slider has been added
        2.A color bar was added to a single gene analysis
        3.Contrast adjustment has been added in moran's I
        4.Convert all contrast adjustment logic to quantiles
        5.Select tissue by legend tab available

[1.1.7] fix bug of one gene adjust contrast darker,expand adjust contrast function to 1/2/3gene analyse

[1.1.6] Expand select XY to select XYZ

[1.1.5] 1.Fixed the bug where visible cells decreased with the number of operations
        2.When creating a flatten layer, the visibility inherits from the original visibility
        3.Unify the length of the mask variable when calculating and plotting
        4.The original situation where the threshold constraints of each gene were mutually inherited has been changed. Now, they are all inherited from tissue_filter

[1.1.4] 1.Fixed the bug related to multi-gene screening 
        2.The calculation and plotting of moran's I have been optimized

[1.1.3] fix buges

[1.1.2] enrich function

[1.1.1] change color_map

[1.1.0] rebuild whole package

## acknowledge

https://github.com/GuignardLab/sc3D
https://github.com/GuignardLab/napari-sc3D-viewer

## environment
