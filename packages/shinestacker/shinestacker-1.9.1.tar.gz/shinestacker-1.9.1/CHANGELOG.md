# Changelog

This page reports the main releases only and the main changes therein.

## [v1.9.1] - 2025-10-23
** Improved EXIF data handling GUI refinements **

### Added
- missing actions "Show EXIF Data" and "Delete EXIF Data"

### Fixed
- if saving EXIF data fails, a warning is issued instead of stopping the run
- exif data correctly loaded when opening image file in retouch mode
- removed duplicated parameter from config dialog (FocusStackBunch)
- fixed thread warning when the application quits
- more robust EXIF data code for JPG format prevents possible errors

### Changed
- improved EXIF GUI: more data displayed and improved selection logic

-----

## [v1.9.0] - 2025-10-19
** Added PNG format support and fixed EXIF failure **

### Added
- support of images in PNG format, both in 8 bit and 16 bit depth. Note: EXIF data are not supported for 16 bit PNG because of limitations in the PIL and Open CV python libraries.

### Fixed
- if saving EXIF data fails, a warning is issued instead of stopping the run

-----


## [v1.8.1] - 2025-10-16
** Alignment stability and performance improvements **

### Added
- optional alignment algorithm based on phase correlation as fallback when no feature match is found
- retry limits in parallel alignment, determined by new configurable parameter delta_max
- new configurable parameters in persistent default settings

### Fixed
- reference frame indexing if sequential processing is applied as fallback from multithread run
- job configuration dialog failure if input is aready selected
- preview thumbnail failure for very large images
- minor inaccuracies in logger messages
- minor GUI issues
- computations for vignetting summary plot

### Changed
- improved robustness of alignment strategy for poorly focused images
- better tuning of parallel frame alignment
- consistent handling of noise map output folders
- improved naming scheme for wizard-generated projects
- more reliable default settings persistency
- code refactoring and cleanup

-----

## [v1.8.0] - 2025-10-08
** Minor improvements and accessibility fix **

### Added
- temporary disk space can be cleaned up with a new option to scratch output files at the end of a job 

### Fixed
- new project dialog displays well also with dark background settings

### Changed
- icons now adapt automatically to light or dark desktop theme
- additional alignment parameters added to default settings
- minor GUI stability fix
- redundant macOS .tar.gz installer removed, replaced by .dmg image

-----

## [v1.7.0] - 2025-10-04
** New image adjustment actions and macOS dmg image installer **

### Added
- luminosity and contrast adjustment action
- saturation and vibrance adjustment action
- macOS dmg installer

### Changed
- improved windows installer
- white balance moved from filters to edit > adjust menu
- minor GUI cosmetic improvements
- code refactoring

-----

## [v1.6.1] - 2025-10-01
** Performance improvements **

### Added
- windows installer

### Changed
- improved display update performance by refreshing only the painted area
- multiple frame import now runs in a separate thread, avoiding UI freezes
- reduced dependencies and code refactored for more robust architecture
- dropped examples and test images to reduce distribution file size

-----

## [v1.6.0] -  2025-09-27
**Few more features and several fixes**

### Added
- persistent settings dialog to configure app startup options
- command-line option ```-n``` to prevent opening the "new project" dialog
- zoom factor display in the status bar

### Fixed
- ghost brush gradient no longer appears at cursor transitions
- action and job names are now correctly set in the input dialog
- image centering fixed in viewport for double-view modes
- frame highlight works correctly when clicking on a thumbnail
- exif data is now correctly inserted into stacked output files
- bug in the retouch undo has been fixed

### Changed
- cursor updates are now throttled (~60 fps) to improve responsiveness
- new projects created via dialog save exif data by default

----

## [v1.5.4] - 2025-09-23
**Bug fixes**

### Fixed
- fixed functionality of layer alphabetic sorting
- fixed image centering in zoom operations
- fixed color picker reuse in white-balance filter
- minor fixes and code cleanup

### Changed
- menu actions that require a file are disabled when no file is open 

----

## [v1.5.3] - 2025-09-21
**Bug fixes**

### Fixed
- fixed a critical bug that caused crash at startup in distrubution package due to a relative import in main app scripts
- fixed relative import in main app scripts

### Changed
- implemenrted cursor dynamic color based on background image luminosity

---

## [v1.5.2] - 2025-09-21 (⚠️ DEPRECATED — use 1.5.3)
**Bug fixes**

### Fixed
- fixed white balance filter functionality
- fixed brush preview visiblity in view mode transitions

### Changed
- code refactoring and cleanup

---

## [v1.5.1] - 2025-09-20 (⚠️ DEPRECATED — use 1.5.3)
**Several bug fixes**

### Added
- new command-line arguments -v1, -v2, -v3, allow different view modes at startup

### Fixed
- consistent and restyled cursor for current layer view
- fixed ghost cursors in side-by-side views
- fixed cursor shift at startup
- fixed brush preview at image borders
- fixed lower/upper case GUI labels
- improved help and description text

---

## [v1.5.0] - 2025-09-16
**GUI improvements and fixes**

### Added
- implemented image rotation

### Fixed
- fixed zoom in wheel events for side-by-side views
- restored standard cursor in empty retouch views
- lower/upper case GUI labels

### Changed
- code refactoring and cleanup
- dotted cursor in secondary two-image view

---

## [v1.4.0] - 2025-09-14
**GUI improvements**

### Added
- added retouch view mode with master and frame side by side and top-bottom
- implemented "Open Recent" menu entry for both projects and retouch images
- expert options can be shown with a checkbox in each dialog
- optional summary plots for alignment transformation parameters

### Fixed
- fixed bug in plot generation
- fixes warning due to missing glyph in PDF generation on macOS
- safer parallel plot generation using a thread locks

### Changed
- code refactoring in various areas


## [v1.3.1] - 2025-09-08
**Fixes and optimizations**

### Fixed
- fixed input folder widget in job configuration
- better management of patological alignments
- restored alignment match plots

### Changed
- improved automatic parameters for parallel alignment
- improved pyramid performances by combining two input steps
- improved performances of ORB and SURF feature extraction with key points caching
- improved configuration GUI using tabs and other minor GUI improvements
- code clean up and some fixes

---

## [v1.3.0] - 2025-09-06
**Parallel processing and input flexibility**

### Added
- Parallel processing in alignment feature extraction
- Parallel processing of combined actions
- Job input can now specify a list of files (not only a folder)
- CPU and memory usage monitor widget for running jobs

### Fixed
- Path in example project
- Bug fix in config dialog

### Changed
- Changes some default parameters for better performances
- Some GUI restyling
- Code cleanup

---

## [v1.2.1] - 2025-09-02
**Bug fixes and minor improvements**

### Changes

* alignment is more tolerant in case of failures: frames are skipped and the running job is not stopped
* fixed the -x (--expert) option
* more safety checks prevent crashes for abnormal conditions
* reference frame index improved with a more consistent treatment, a better numbering scheme and GUI widget 
* improved project undo action description text
* some bug fixes and code cleanup

---

## [v1.2.0] - 2025-08-31
**Parallel processing and more improvements**

### Changes

* Implemented parallel processing for pyramid stacking algorithm
* optimized pyramid algorithm: selects automatically the best within the given memory budget to avoid memory issues in case many pictures are selected. Explicit configuration is also possible for specific needs.
* Implemented automatic subsample option for alignment, balancing and vignetting, now default
* HLS and HSV corrections now supported for 16 bit images
* Added luminosity correction in the LAB color space
* Alignment module skips frames if transformation parameters are out of a reasonable ranges
* Multilayer modules sends a warning if the estimated output file size is > 1GB
* "Run all jobs" action is enabled only if more than one job are present
* Updated default module names in project genereated by "new project" dialog
* Code refactoring
* Some GUI fixes

---

## [v1.1.0] - 2025-08-28
**New Pyramids algorithm, some improvements and more fixes**

### Changes

* added Pyramids Tiles, that requires less RAM by fusing images in tiles
* the alignment module now tolerates images of different shapes
* noisy pixel mask verifies that the mask has the same shape as input images
* minor changes to default alignment parameters
* some improvements to the GUI
* some bug fixes
---

## [v1.0.4.pre2] - 2025-08-26
**Bug fixes**

### Changes

* fixed release build script changing format from zip to tar.gz for macOs and Linux

---

## [v1.0.4] - 2025-08-26
**Bug fixes**

### Changes

* extensions are treated in lower case (e.g.: both jpg and JPG)
* added missing retouch menu action: import frames from current project

---
## [v1.0.3] - 2025-08-26
**Bug fixes**

### Changes

* fixed menu text
* fixed crash multilayer module
* fixed multilayer module
* code cleanup

---

## [v1.0.2] - 2025-08-25
**Bug fixes**

### Changes

* fixed context menu
* fixed retouch callback for shiestacker-project app
* fixed double image loading

---

## [v1.0.1] - 2025-08-25
**First stable release**

### Changes

* added source file missing by mistake in v1.0.0

---

## [v1.0.0] - 2025-08-25
**First stable release**

### Changes

* implemented vignetting correction filter
* improved vignetting performance using subsampling
* implemented fast subsample option in balance algorithms
* implemented hex color line editin white balance filter
* new application logo
* interface improvements: implemented master/layer toggle
* more informative GUI messages and colors
* code refactoring and various cleanup 
* bug fixes

Note

A source file was missing in this tag, and was added in v1.0.1

---

## [v0.5.0] - 2025-08-20
**GUI and robustness improvements**

### Changes

* layer selection highlightted with a blue border
* improved font rendering in brush preview
* fixed thumbnail spacing
* fixed and improved save strategy for retouched images
* added checks for updated version in about dialog
* disable "Save" and "Save As..." menus if do not apply to current status

---

## [v0.4.0] - 2025-08-19
**Support touchpad navigation**

### Changes

* implemented touchpad image navigation (pan, zoom with pinch)
* alignment robustness: retry without subsampling if number of bood matches is below a threshold parameter
* added more robust path management in retouch area
* added frame count display in "New Project" dialog
* more unifrom color code in GUI run log
* code clanup, removed remnants of obsolete code
* various fixes

---

## [v0.3.6] - 2025-08-18
**Bug fixes**

### Changes

* fixed a bug that prevented a complete clean up when "New Project" action is called
* fixed the management of project file path while loading and saving
* removed duplicated code
* some code clean up

---

## [v0.3.5] - 2025-08-17
**Bug fixes**

### Changes

* fixed a bug that prevented to add sub-actions
* vignetting constrains model parameter in order to prevent searching for dark areas at the center of the image instead of at periphery
* updated sample images and documentation

---

## [v0.3.4] - 2025-08-16
**Code consolidation and fixes**

### Changes

* code consolidation with support of pylint code checking
* some bug fixes
* new project dialog shows the number of bunches, if selected
* updated sample images, examples and documentation

---

## [v0.3.3] - 2025-08-13
**Fixed PyPI distribution**

This release is equivalent to v0.3.2, but resolves a problem for PyPI distribution.

### Changes

* examples and tests removed from PyPI distribution in order to fix file size limit

---

## [v0.3.2] - 2025-08-13
**Fixes and code refactoring**

### Changes

* fixed ```from shinestacker import *```
* restored jupyter support and updated examples
* several bug fixes
* several code refactoring reduces interclass dependencies
* updated documentation
* added new sample images and project files
* examples removed from PyPI distribution

---

## [v0.3.1] - 2025-08-12
**Fixes and code refactoring**

### Changes

* some GUI fixes
* some code refactoring and cleanup

---

## [v0.3.0] - 2025-08-11
**Filters added to retouch GUI**

### Changes

* added filters for sharpening, denoise and white balance
* updated documentation
* some bug fixes

---

## [v0.2.2] - 2025-07-28
**More stability and improved tests**

### Changes

* improved test suite and enhanced test coverage
* updated documentation
* some stability improvements

---

## [v0.2.1] - 2025-07-27
**Icon location fix**

### Changes

* icon location fixed, compatibly with PyPI and bundle release build

---

## [v0.2.0] - 2025-07-27
**Stability improvements and new package name**

### Changes

* first release with new name ShineStacker
* added BRISK detector/descriptor alignment method
* improved stability by adding more validation controls to alignment configuration
* some bug fixes
* minor restyling

---

## [v0.1.4] - 2025-07-23
**Bug fixes and alignment improvements**

### Changes

* fixed recently introduced bugs in the alignment module
* disabled ECC refinement, too unstable
* improvement rigid alignment with more precise matrix
* some minor bug fixes
* removed dependence on termcolor external module
* some internal code cleanup

---

## [v0.1.1] - 2025-07-20
**Optimized image alignment**

### Changes

* Faster alignment with image subsample enables
* Alignment refinement via ECC transform enabled
* GUI opens new project dialog at startup
* fixed color logging for windowed app
*  bug fixes

---

## [v0.1.0] - 2025-07-19
**First relatively stable and usable GUI release**

### Changes
- several stability improvements
- several bug fixes

---