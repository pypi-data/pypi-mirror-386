# Alignment and registration

Automatically align, scale, tanslate and rotate or apply full perspective correction.

All constants described below are contained in the object ```constants```, imported as:

```python
from shinestacker.config.constants import constants
```

Alignment actions can be added to a job as follows:

```python
job.add_action(Actions("align", [AlignFrames(*options)])
```
Arguments for the constructor ```AlignFrames``` of are:
* ```feature_config``` (optional, default: ```None```): a dictionary specifying the following parameters, with the corresponding default values:
```python
feature_config = {
    'detector': constants.DETECTOR_SIFT,
    'descriptor': constants.DESCRIPTOR_SIFT
}
```
* ```detector``` (optional, default: ```DETECTOR_SIFT```): the feature detector is used to find matches. See [Feature Detection and Description](https://docs.opencv.org/4.x/db/d27/tutorial_py_table_of_contents_feature2d.html) for more details. Possible values are:
  * ```DETECTOR_SIFT``` (default): [Scale-Invariant Feature Transform](https://docs.opencv.org/4.x/da/df5/tutorial_py_sift_intro.html)]
  * ```DETECTOR_ORB```: [Oriented FAST and Rotated BRIEF](https://docs.opencv.org/4.x/d1/d89/tutorial_py_orb.html)
  * ```DETECTOR_SURF```: [Speeded-Up Robust Features](https://docs.opencv.org/3.4/df/dd2/tutorial_py_surf_intro.html)
  * ```DETECTOR_AKAZE```: [AKAZE local features matching](https://docs.opencv.org/3.4/db/d70/tutorial_akaze_matching.html)
  * ```DETECTOR_BRISK```: [Binary Robust Invariant Scalable Keypoints](https://medium.com/analytics-vidhya/feature-matching-using-brisk-277c47539e8)
* ```descriptor``` (optional, default: ```DESCRIPTOR_SIFT```): the feature descriptor is used to find matches. Possible values are:
  * ```DESCRIPTOR_SIFT``` (default)
  * ```DESCRIPTOR_ORB```
  * ```DESCRIPTOR_AKAZE```
  * ```DESCRIPTPR_BRISK```

  For a more quantitative comparison of performances of the different methods, consult the publication: [S. A. K. Tareen and Z. Saleem, "A comparative analysis of SIFT, SURF, KAZE, AKAZE, ORB, and BRISK", doi:10.1109/ICOMET.2018.8346440](https://ieeexplore.ieee.org/document/8346440)

```matching_config``` (optional, default; ```None```): a dictionary specifying the following parameters, with the corresponding default values:
```python
matching_config= {
    'match_method': constants.MATCHING_KNN,
    'flann_idx_kdtree': 2,
    'flann_trees': 5,
    'flann_checks': 50,
    'threshold': 0.75
}
```
* ```match_method``` (optional, default: ```MATCHING_KNN```): the method used to find matches. See [Feature Matching](https://docs.opencv.org/4.x/dc/dc3/tutorial_py_matcher.html) for more details. Possible values are:
  * ```MATCHING_KNN``` (default): [Feature Matching with FLANN](https://docs.opencv.org/3.4/d5/d6f/tutorial_feature_flann_matcher.html)
  * ```MATCHING_NORM_HAMMING```: [Use Hamming distance](https://docs.opencv.org/4.x/d2/de8/group__core__array.html#ggad12cefbcb5291cf958a85b4b67b6149fa4b063afd04aebb8dd07085a1207da727)
* ```flann_idx_kdtree``` (optional, default: 2): parameter used by the FLANN matching algorithm.
* ```flann_tree``` (optional, default: 5): parameter used by the FLANN matching algorithm.
* ```flann_checks``` (optional, default: 50): parameter used by the FLANN matching algorithm.
* ```threshold``` (optional, default: 0.75): parameter used to select good matches. See [Feature Matching](https://docs.opencv.org/4.x/dc/dc3/tutorial_py_matcher.html) for more details. 

* ```alignment_config``` (optional, default; ```None```): a dictionary specifying the following parameters, with the corresponding default values:
```python
alignment_config = {
    'transform': constants.ALIGN_RIGID,
    'align_methid': constants.RANSAC,
    'rans_threshold': 5.0,
    'refine_iters': 100,
    'align_confidence': 99.9,
    'max_iters': 2000,
    'border_mode': constants.BORDER_REPLICATE_BLUR,
    'border_value': (0, 0, 0, 0),
    'border_blur': 50,
    'subsample': 0,
    'fast_subsampling': False,
    'min_good_matches': 100,
    'phase_corr_fallback': False,
    'abort_abnormal': False
}
```
* ```transform``` (optional, default: ```ALIGN_RIGID```): the transformation applied to register images. Possible values are:
  * ```ALIGN_RIGID``` (default): allow scale, tanslation and rotation correction. This should be used for image acquired with tripode or microscope.
  * ```ALIGN_HOMOGRAPHY```: allow full perspective correction. This should be used for images taken with hand camera.
* ```align_method``` (optional, default: ```RANSAC```): the method used to find matches. Valid options are:
  * ```RANSAC``` (*Random Sample Consensus*, default)
  * ```LMEDS``` (*Least Medians of Squares*)
* ```rans_threshold``` (optional, default: 5.0): parameter used if ```ALIGN_HOMOGRAPHY``` is choosen as tansformation, see [Feature Matching + Homography to find Objects](https://docs.opencv.org/3.4/d1/de0/tutorial_py_feature_homography.html) for more details.
* ```refine_iters``` (optional, default: 100): refinement iterations. Used only if ```transform=ALIGN_RIGID```.
* ```align_confidence``` (optional, default: 99.9): alignment algorithm confidence (%). Used only if ```transform=ALIGN_RIGID```. 
* ```max_iters``` (optional, default: 2000): maximum number of iterations. Used only if ```transform=ALIGN_HOMOGRAPHY```. 
* ```subsample``` (optional, default: 0=automatic): subsample image for faster alignment. Faster, but alignment could be less accurate if only a small portion of the image is focused. It can save time, in particular for large images.
* ```fast_subsampling``` (optional, default: ```False```): perform fast image subsampling without interpolation. Used if ```subsample``` is set to ```True```.
* ```min_good_matches``` (optional, default: 100): if ```subsample```>1 and the number of good matches is below ```min_good_matches```, the alignment is retried without subsampling. This improbes robustness in case a too large subsampling factor is specified. 
* ```phase_corr_fallback``` (optional, default: ```False```): use phase correlation alignment in case the number of matches is too low to allow to estimate the transformation. This algorithm is not very precise, and may help only in case of blurred images.
* ```abort_abnormal``` (optional, default: ```False```): abort in case of anormal tansformation. By default, frames where abnormal transformation is found are skipped, and processing continunes to next frame.
* ```border_mode``` (optional, default: ```BORDER_REPLICATE_BLUR```): border mode. See [Adding borders to your images](https://docs.opencv.org/3.4/dc/da3/tutorial_copyMakeBorder.html) for more details.  Possible values are:
  * ```BORDER_CONSTANT```: pad the image with a constant value. The border value is specified with the parameter ```border_value```.
  * ```BORDER_REPLICATE```: the rows and columns at the very edge of the original are replicated to the extra border.
  * ```BORDER_REPLICATE_BLUR``` (default): same as above, but the border is blurred. The amount of blurring is specified by the parameter ```border_blur```.
* ```border_value``` (optional, default: ```(0, 0, 0, 0)```): border value. See [Adding borders to your images](https://docs.opencv.org/3.4/dc/da3/tutorial_copyMakeBorder.html) for more details.
* ```border_blur``` (optional, default: ```50```): amount of border blurring, in pixels. Only applied if ```border_mode``` is set to ```BORDER_REPLICATE_BLUR```, which is the default option.
* ```plot_summary```  (optional, default: ```False```): if ```True```, plot a summary histogram with number of matches in each frame. May be useful for inspection and debugging.
* ```plot_matches```  (optional, default: ```False```): if ```True```, for each image matches with reference frame are drawn. May be useful for inspection and debugging.
* ```enabled``` (optional, default: ```True```): allows to switch on and off this module.

## Parallel processing

A class ```AlignFramesParallel``` implements alignment using parallel processing.
This class has extra parameters, in addition to the above ones:

* ```max_threads``` (optional, default: ```2```): number of parallel processes allowed. The number of actual threads will not be greater than the number of available CPU cores.
* ```chunk_submit``` (optional, default: ```True```): submit at most ```max_threads``` parallel processes. If ```chunk_submit``` is greater than ```max_threads``` a moderate performance gain is achieved at the cost of a possibly large memory occupancy.
* ```bw_matching``` (optional, default: ```False```): perform matches on black and white version of the images in order to save memory. Preliminary tests indicate that the gain with this option is marginal, and this option may be dropped in the future.
* ```delta_max``` (optional, defaut: 2): maximum consecutive frames skipped in case of too few matches found.

## Automatic selection of processing strategy

A class ```AlignFramesAuto``` implements alignment with either sequential or parallel processing, and automatically tunes parallel processing parameters.
This class has extra parameters, in addition to the above ones:

* ```mode``` (optional, default: ```auto```): can be ```auto```, ```sequential``` or ```parallel```.
* ```memory_limit``` (optional, default: 8×1024<sup>3</sup>sup>): memory limit to determine optimal running parameters


## Allowed configurations

⚠️ Not all combinations of detector, descriptor and match methods are allowed. Combinations that are not allowed
give raise to an exception. This is automatically prevented if one works with the GUI, but may occur when using python scripting. Below the table of the allowed combination with a comparison of CPU performances.

## CPU performances

⏳ Below the time performances for alignment of two of the sample images with 2000×1300 resolution for allowed configuration combinations, from fastest to slowest. Note that slower may be more precise.

| Time (s) | Detector | Descriptor | Match method |
|----------|----------|------------|--------------|
| 0.0250   |  SURF    | ORB        | NORM_HAMMING |
| 0.0347   |  SURF    | BRISK      | NORM_HAMMING |
| 0.0469   |  ORB     | ORB        | NORM_HAMMING |
| 0.0471   |  ORB     | BRISK      | NORM_HAMMING |
| 0.1001   |  BRISK   | BRISK      | NORM_HAMMING |
| 0.1199   |  BRISK   | ORB        | NORM_HAMMING |
| 0.1604   |  SURF    | SIFT       | KNN          |
| 0.1966   |  BRISK   | SIFT       | KNN          |
| 0.2121   |  ORB     | SIFT       | KNN          |
| 0.2738   |  AKAZE   | AKAZE      | NORM_HAMMING |
| 0.2863   |  AKAZE   | ORB        | NORM_HAMMING |
| 0.2887   |  AKAZE   | BRISK      | NORM_HAMMING |
| 0.4075   |  AKAZE   | SIFT       | KNN          |
| 0.4397   |  SIFT    | SIFT       | KNN          |

## References

For a detailed review of the various image registration methods, see the publication below:
*  [A Review of Keypoints’ Detection and Feature Description in Image Registration](https://onlinelibrary.wiley.com/doi/10.1155/2021/8509164), Scientific Programming 2021, 8509164, doi:10.1155/2021/8509164


