# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.4] - 2025-10-02

### Fixed
* Fixed asf search for notebook examples:
  *  filters out dates with single polarization 
  *  allows users to select which dual polarization to use (`HH+HV` vs. `VV+VH`)
* Baseline curation matches dist-s1.

### Added
* Add models for v0 and v1 that use 32 x 32 input size.
* Dynamically update `input_size` (i.e. the size of the input image) for inference using the corresponding model attribute.
* Expose fill value of model inference (via `fill_value`) that was reminant of old logit transformation and is now explicitly set and can be modified


## [1.0.3] - 2025-08-25

### Changed
* Latest weights for `transformer_anniversary_trained_optimized_fine` and `transformer_anniversary_trained_optimized` the v1 datasets.

## [1.0.2] - 2025-08-6

### Added
* New models from v1 dataset.

## [1.0.1] - 2025-07-20

### Changed
* Load model config and obtain maximum sequence length (context length) of model.
* Decouple loading of config and weights.

### Fixed
- Changelog action

### Added
- tests for external model loading


## [1.0.0] - 2025-03-20

### Added
- Nodata interpolation for interior datapoints (i.e. within pixels collected during acquisition) which are np.nan including:
  - bilinear - an iterative bilinear-like interpolation
  - nearest - nearest neighbor interpolation
- dependabot
- Several models for easier testing
- notebooks that can do both immediate and anniversary selection to establish baseline

### Changed
- Removes logit transformation from normal param estimation
- 4 *new* models for testing
- `estimate_normal_params_of_logits` --> `estimate_normal_params`
- Reorganization of transformer metric code into loading model(s), inference, torch model, and metric.
- Updated notebook so we only download necessary arrays.

### Removed
- Notebook for multiple burst analysis (will add back later)

## [0.0.14] - 2025-03-20

### Fixed
- Version/Changelog


## [0.0.13] - 2025-05-15

### Added
* Added optional compilation for `CPU` via `torch.compile` and `GPU` via `torch_tensorrt.compile`.
* 'external' option for model_token parameter of load_transformer_model.
* And the associated cfg and wts file paths. 

### Fixed
* Fixed order of tensor operations and moving data to 'device' to reduce overhead.

## [0.0.12] - 2025-03-05

### Added
* Test to ensure `cpu` and None interface work correctly for transformer metric.

### Fixed
* The `device` argument for transformer needs to be correctly passed throughout the transformer estimation process and test suite.


## [0.0.11] - 2025-03-05

### Added
* Ability to control `device` for transformer model

## [0.0.10] - 2025-02-20

### Added
* Ensures environment.yml and environment_gpu.yml are up to date with the latest dependencies.
* Requires rasterio>=1.4.0 for merging to be consistent.

## [0.0.9] - 2025-02-20

### Fixed
* Bug in `reproject_arrays_to_target_crs`.

### Added
* Tests for merge categorical arrays using inputs that are in different crs.

## [0.0.8] - 2025-02-20

### Fixed
* Pyproject.toml kept dependencies for mpire and dill (those are now removed)


## [0.0.7] - 2025-02-20

### Fixed
* Pyproject.toml and environment.yml to require python 3.12+
* Pydantic model_config to allow arbitrary types (update for v2)

### Removed 
* `mpire` dependency

### Added
* Test for despeckling of cropped data


## [0.0.6] - 2025-01-18

* Fixed default keyword argument for `merge_categorical_arrays` from `mode` (not possible with rasterio) to `min`.


## [0.0.5] - 2025-01-18

### Added
* Added `rio_tools` for merging float arrays (including burst data such as the computed metric)
    * can be used to average over overlapping areas
    * average using the distance from exterior mask (mask that touches one of the four edges)
    * exterior mask can also be dilated to avoid problematic boundary pixels
    * categorical merging of data
* Added `nd_tools` for getting exterior mask and distance from such mask (wrappers around `scipy.ndimage`)
* A notebook for applying the transformer metric to a large area of interest

### Removed
* Removed torch.compile from transformer model loading

## [0.0.4] - 2025-01-18

### Fixed
* Fixed transformer to ensure last pre-image always has correct index

### Added
* Arxiv link to README
* Installation instructions
* `tqdm` description for despeckling
* Allow user to disable `tqdm` for despeckle

### Changed
* Renamed `load_trained_transformer_model` to `load_transformer_model`
* Renamed inputs to reflect (possible) usage with other polarizations: `vv` -> `copol` and `vh` -> `crosspol`. The APIs don't change, just the variable name inputs.


## [0.0.3] - 2025-01-16

### Fixed
* Fixed ASF calls in landslide transformer notebook - more data is becoming available so static slices do not work

### Added

* Consistent linting of DIST-S1 repositories
* Expose estimation of the normal parameters of the logit images with high/low memory usage.
* Added transformer test based on usage of different strategies of computation.
* Uploaded latest model

### Changed
* Data directory structure
* Only support python 3.12+


## [0.0.2]

### Fixed

* Fixes Changelog format to ensure proper automated release
* Fixes secrets in workflows for proper automated release


## [0.0.1]

This was an initial release of the library.

This is a python library for calculating a variety of generic disturbance metrics from input OPERA RTC-S1 time-series including a transformer-based metric from Hardiman-Mostow et al., 2024.
Generic land disturbances refer to any land disturbances observable with OPERA RTC-S1 including land-use changes, natural disasters, deforestation, etc.
A disturbance metric is a per-pixel function that quantifies via a radiometric or statistical measures such generic land disturbances between a set of baseline images (pre-images) and a new acquisition (post-image).
This library is specific to the dual-polarization OPERA RTC-S1 data and will likely need to be modified for other SAR data.
The user is expected to provide/curate the co-registered baseline imagery (pre-images) and the recent acquisition (post-image) for the computation of the distmetrics.

Provides an interface for the following metrics:

1. transformer - this is metric that uses spatiotemporal context to approximate a per-pixel probability of baseline images. This that was proposed in Hardiman-Mostow, 2024.
2. logratio - this is not a non-negative function just a difference of pre and post images in db, but we transform into a metric by only inspecting the *decrease* in a given polarization
3. Mahalanobis 1d and 2d - based on sample statistics computed in patches around each pixel.
4. CuSum - based on the actual residuals and on a normalized time-series assuming normality.
