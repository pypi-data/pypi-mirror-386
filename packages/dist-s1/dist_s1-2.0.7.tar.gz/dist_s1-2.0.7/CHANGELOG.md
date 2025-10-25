# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.7] - 2025-09-08

### Added
* Validation in RunConfigData to ensure that the maximum expected context length is not exceeded within a burst's baseline.
* Validation in RunConfigData to ensure there are not duplicate products in the baseline/preimagery passed via a Runconfig.yml.
* Parameters to localization and prep workflows to ensure model source's maximum sequence length (i.e. temporal context length) is correctly assigned
* Added version floor to `distmetrics` so that this libary includes latest models with `32 x 32` input size and fixes one of the models configurations.
* Exposed all confirmation parameters in confirmation workfows.
* Dynamically set confirmation thresholds using the product metadata (reading gdal tags) so that these parameters to have to be set by the user

### Removed
* `zlevel` from gdal metadata to resolve `WARNING  rasterio._env:rio_tools.py:67 CPLE_NotSupported in driver COG does not support creation option ZLEVEL`.
* Removed manual specification of product tags in `confirm_disturbance_with_prior_product_and_serialize`.

### Fixed
* Issues with specifying `model_source` in runconfig or other entry point and the software incorrectly selecting the model context length.
* Incorrect default values were set for confirmation and therefore disturbances were too conservative in many tests. This is simply fixed by ensuring defaults are set using `src/dist_s1/data_models/defaults.py`.

### Changed
* Updated variables with simply `confidence_thresh` to `confirmation_confidence_threshold` so code was explicit.


## [2.0.6] - 2025-09-08

### Changed
* Changed defaults of n_workers from 8 to 4 for `DEFAULT_N_WORKERS_FOR_NORM_PARAM_ESTIMATION`.
* Floor for dist-s1-enumerator (`>=1.0.2`) so that we use sessions and `tenacity` library for retries.
* Floor for dist-s1-enumerator (`>=1.0.5`) sot that urls in CMR that have not been updated are correctly resolved see: https://github.com/opera-adt/dist-s1/issues/158
* Token OPERA_L3_DIST-ALERT-S1_T{mgrs_tile_id}_{acq_datetime}_{proc_datetime}_{sensor}_{version} needs to have S1A|B|C in sensor token. Golden datasets were updated accordingingly.
* Made the validation for all copol/crosspol data being consistent into it's own validation.
* Updated compression and other georeferencing parameters for COGs to improve the file-size in `serialize_one_2d_ds`.
* Updated compression and other georefencing parameters for general GeoTiff file size in `get_mgrs_profile`. Currently, this only impacts serialization of the water mask.
* Have gitignore properly ignore all temporary files in test suite (even if tests do not run to completion).

### Added
* Test to use .5 degree buffered water mask around sas workflow to illustrate larger water mask is correctly cropped/reprojected during end-to-end run.
* Updated upload to s3 to accept strings and posix paths (issues uploading files).
* Use latest tile-mate that allows for wrapping around the dateline/anti-meridian.
* More descriptive validation errors for RunConfigData model including:
  - consistent jpl burst ids in baseline/pre-image set with post-image/recent acq set.
  - consistent dates between copol and crosspol data
  - ensures provided JPL burst ids occur in correct MGRS tile id.
  - consistent polarizations across jpl-burst-ids.
* Updated to `dist-s1-enumerator` to v1.0.4 which allows for bursts to construct baselines independently within an MGRS tile
* More tokens for product equality including `sensor`, `prior_dist_s1_product`
* Validation and tests to ensure a post data all occurs within 20 minutes of each other.
* For 4326, check +/- 360 longitudes of MGRS tile geometries to ensure water mask is correctly found - the SDS PCM can provide water masks across the globe.
* Added tests for eastern hemisphere antimeridian.

### Fixed
* Regression test instructions were updated for SDS release.
* For s3 upload, upload zip file and png only (no TIF files).
* Better error handling of empty dataframes.
* Fix the CLI entrypoint error in `run_sas_prep` due to missing parameter option for `prior_dist_s1_product` (see Issue #152: https://github.com/opera-adt/dist-s1/issues/152)
* Allow for dateline processing - both when water mask is provided and when localizing from tiles.
  * Ensure windowed reading for water mask is correct across dateline and with larger areas.


## [2.0.5] - 2025-08-15

### Fixed
* Dynamically serving docs and cleanup
* Updated the RunConfigModel so that `src_water_mask_path` is now the input water mask path (not necessarily with proper CRS) and we compute/process the water mask as a property in the data to ensure proper handling. Avoids annoying recursion errors.
  - Also updated `DEFAULT_WATER_MASK_PATH` to `DEFAULT_SRC_WATER_MASK_PATH`.

### Added
* Tests to ensure that defaults and configured parameters are written to product tags correctly.

### Changed
* `water_mask_control_flow` no longer accepts `apply_water_mask` - we assume this is only applied when water masks are required.


## [2.0.4] - 2025-08-15

### Changed
* `dist-s1` has a command line interface for `check_equality` with successful exit code `0` if True and `1` if not.
* Fixed `stride_for_norm_param_estimation`, `low/high_confidence_alert_threshold` in `test_main.py` and `test_workflows.py` so they can be adjusted without impacting the suite.

### Fixed
* The 2_delivery.py was not preserving relative paths for the creation of a golden dataset.
* For the confidence layer (`DIST-GEN-CONF`), the nodata was set to -1 (incorrect) and is now np.nan. The layer not being initialized correctly (filled with -1).
* Regression test correctly calls `dist-s1 check_equality`
 
### Added
* More comprehensive statistics provided for `__eq__` of `DistS1ProductDir`. Also ensures nodata masks are consistent across layers.
* Equality for floats is now 2e-5 rather than 1e-5 (not sure what changed), but it will not impact the final product.

## Changed
* Changed defaults:
  * Defaults of `low/high_confidence_alert_thresholds` lowered to `2.5`/`4.5` from `3.5`/`5.5`.
  * Updated the confirmation threshold accordingly.
  * Updated stride to 7 (from 16) for smoother resolution of disturbance and slightly offset from patch size.


## [2.0.3] - 2025-08-12

### Added
* Regression testing
* profile to aws file uploading for regression testing
* multithreaded boto3 (probably should just use aws s3 sync)

### Changed
* Paths in runconfig are relative to allow for easier reproducibility and regression testing.

### Fixed
* Links to documentation (use stable)
* Serialization of `algo_config_path` -- model_dump() in pydantic works recursively on attributes!
* Serialization and read of `prior_dist_s1_product` - allows for str and paths


## [2.0.2] - 2025-08-12

### Added
* Mkdocs provides documentation for:
   - RunConfigData and AlgoConfigData parameters
   - Product layers and their descriptions
* Mkdocs added to environment.

## [2.0.1] - 2025-08-07

### Changed
* Updated imports of defaults in `runconfig_model.py`

### Added
* More examples for confirmation workflow
* Ability to change all parameters for algorithms from python and CLI entrypoints
* Updated readme for confirmation workflows
* Lower bound for distmetrics to ensure latest models included.

### Fixed
* Browse imagery generation (was scaling dynamic range unnecessarily)
* Sequential confirmation test data.
* Entrypoints to confirmation only entrypoints.
* `dst_dir` attribute of `DistS1ProductDirectory` casting to Path. 


### Fixed
* Exposed all confirmation algorithm parameters into CLI and python interfaces
* Changelog format from major release
* `n_annivesaries` in CLI and workflow (was not properly set in prep workflow)
* Duplicate CLI options (`algo_config_path` and `run_config_path`)
* Ensure for `prep` workflows and `run` workflows (and associated CLI) that if `run_config_path` is provided, then `run_config.yml` and `algo_config.yml` are created and then serialized.


## [2.0.0] - 2025-07-16

### Removed
- `n_lookbacks` (which should have been called `n_baselines`) for computing confirmation within the SAS
   - Removed overly complicated accounting for in SAS confirmation
   - Only confirmation now is either by passing a previous product OR passing a directory of products
- Constant for `BASE_DATE_FOR_CONFIRMATION` and removed from algo config.
- Extra validation for confirmation packaging
- Support for `immediate_lookback` - to add back will need to add logic for calculations of lookbacks, etc.

### Changed
- Multiwindow strategy is now the default in both python API and CLI
- Confirmation_strategy is now simply determined with respect to `prior_dist_s1_product`. If it is `None`, then no confirmation is performed. If it is a path, then it uses this directory and it's tiffs to perform confirmation.
- Now retrieves the umd distance to land and use a water mask that excluded 1 km from ocean.
- `optimize` is now `model_compilation`; also does not work with `device` that is `mps`
- Update validation to occur at assignment and remove algorithm parameters being assigned within localization workflow.
- `base_date` is now `base_date_for_confirmation`.
- Remove algorithm assignments in localization workflows.
- Organized `AlgoConfigData` and `RunConfigData` into seperate files
  - `AlgoConfigData` is an attribute of the `RunConfigData`
  - Retrieval (and serialization) of the Algorithm Parameters can still be obtained via `get_public_attributes`.
- Put data/path utils into `data_utils.py`.
- Variables for confirmation processing (use snake case wherever possible)
- Now have an output product without confirmation and a product with confirmation (for provenance)
- De-couple confirmation and packaging in workflow logic
- Confidence is now float32 (not int16) - this needs to happen because the dist metrics is float32 so casting to integer looses information.
- Updated golden dataset to reflect new changes in this major release.
- `DIST_CMAP` is not `DIST_STATUS_CMAP`.
- To align with dist-hls, we have changed `moderate_confidence_threshold` and `high_confidence_threshold` to now be `low_confidence_alert_threshold` and `high_confidence_alert_threshold`.
- Moved browse imagery generation into workflows.
- Consistent multiprocessing within dist-s1 (ensures consistent useage of `spawn` child processes), closure of pool objects, and configuraiton before imports.
- Handling of model context length to provide maximum number of pre-images (can still be overwritten)
- Removal of defaults using lists! https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
- Use dist-s1-enumerator and updated keyword arguments.
- Golden datasets now use multi-window baselines.

### Added
- Confirmation python API and CLI
- Constants for CLI and `RunConfigData` - allows for consistent data parsing.
- Ability to use algorithm parameters to supplement runconfig for SDS operations.
  - It's now a base class to `RunConfigData` and if an external 
- Updated interface for despeckling to use interpolation to fill nan values within burst area.
  - distmetrics>=1.0.0 - see more details there
- Allows for serialization of yml files during `run_sas_prep_workflow` and associated CLI
  - Also allows for serialization of algorithm parameters to serparate file as well.
- Validation in Runconfig for `model_dtype` with `device` (only `bfloat16` is permitted with `GPU`)
- Validation in Runconfig for external model usage
- Description of Runconfig Variables
- Cloud-optimized Geotiff (COG) Format in Packaging
- Confirmation is now contained inside its own function `confirmation.py`
  - Exposed parameter `consecutive_nodist`, if `True` the `nocount` condition is applied (doesn't allow 2 consecutive misses).
  - Exposed parameter `percent_reset_thresh`, it will apply reset if `percent` below threshold. 
  - Exposed parameter `nocount_reset_thresh`, it will apply reset if `prevnocount` is above threshold.   
- Confirmation CLI
  - Ensuring additional profile keys  for COG in default GTiff are not present.
- Access of Confirmation of Products in main library (i.e. `from dist_s1 import run_sequential_confirmation_of_dist_products_workflow`)
- Use specified model context length from specified model to calculate `max_pre_imgs_per_burst_mw` and `delta_lookback_days_mw` if the latter two are unspecified
- Examples of enumeration of inputs for DIST-S1 triggering with `dist-s1-enumerator>=1.0.0` (used in creation of DIST-S1 time-series and confirmation).

### Fixed
- Sequential Confirmation Workflow and downstream functions
- All the tests with the updates above.
- Correct loading of algo_config.yml in `prep` steps.
  - Only `from_yml` loads the `algo_config` correctly, but when it is assigned in the `prep` workflows (i.e. the attribute `algo_config` is assigned, this yml is not correctly loaded.
- Correctly handle `model_source` as only string value with allowed string values from `distmetrics` or `external`.


## [1.0.1] - 2025-06-05

### Changed
- Now uses the Dockerfile without nvidia base. The image is smaller in size.
- Updated the docker build action to align with the new ASF-based action (which is version-based and permits trunk based development).

### Fixed
- Running pytest in docker image now works (does not require `~/.netrc`) - fixed by mocking credentials.
- PNG generation was not plotting the expected map when using the confirmation_strategy == 'use_prev_product' (Dist-HLS like).
- Duplicate click option for apply water mask (in `__main__.py`)
- Update default `confirmation_strategy` for the creation of runconfig from a dataframe (to `compute_baseline`).
- Update the `run-steps` notebook.
- Ensures pandera>=0.24.0 and removes future warnings from the library.

## [1.0.0] - 2025-06-04

### Fixed
- Major Release for start of confirmation work

## [0.1.0] - 2025-05-27

### Fixed
Minor release - mislabeled

## [0.0.10] - 2025-05-27

### Added
- Implemented confirmation database workflow. 
- Updated `workflows.py`, `__main__.py`, `runconfig_model.py`, `output_models.py` and `processing` to accept confirmation database, `confirmation_strategy` and `lookback_strategy`  
- Updated `workflows.py`, `processing.py`, and `runconfig_model.py` to accept `stride_for_norm_param_estimation`, `batch_size_for_norm_param_estimation`, `optimize` params.
- Updated `workflows.py`, `processing.py`, and `runconfig_model.py` to accept `model_source`, `model_cfg_path`, and `model_wts_path` which allow an external Transformer model to be used.  If not present, the internal models are used as before.


## [0.0.9] - 2025-05-07

### Added
- Updated packaging.py and runconfig_model.py to accept HH and HV polarizations.


## [0.0.8] - 2025-03-05

### Changed
- Defaults to "low" for memory strategy for CPU usage.
- ProductFileData comparison to allow for individual product file comparison (fixes [#51](https://github.com/opera-adt/dist-s1/issues/51)).
- Golden dataset - used CPU and low memory strategy to create the dataset.
- Updated equality testing for DIST-S1 product comparison lowered comparison tolerance to 0.0001 (was 1e-05).
- Forced minimum version of rasterio to 1.4.0 for merging operations.
- Pydantic model updates to ensure `product_dst_dir` is set to `dst_dir` without using `setattr`.
- Updated some example parameters for testing.
- Set minimum number of workers for despeckling and estimation of normal parameters to 8.
- Logic to deal with `n_workers_for_norm_param_estimation` when GPU is available (forcing it to be 1).
- Set `batch_size_for_despeckling` to 25.

### Added
- Exposes runconfig parameter to force use of a device (`cpu`, `cuda`, `mps`, or `best`). `best` will use the best available device.
- Exposes runconfig to control batch size for despeckling (how many arrays are loaded into CPU memory at once).
- Allows for CPU multi-CPU processing (if desired) and exposes runconfig parameter to control number of workers.
   - Validates multiprocessing to use CPU device.
   - Ensures that the number of workers is not greater than the number of vCPUs (via `mp.cpu_count()`).
- If GPU is used, ensure multiprocessing is not used.
- Added a `n_workers_for_norm_param_estimation` parameter to the runconfig to control the number of workers for normal parameter estimation.
- Better instructions for generating a sample product via a docker container.
- Swap out concurrent.futures with torch.multiprocessing for normal parameter estimation for efficient CPU processing.

### Fixed
- Ensures that the number of workers for despeckling is not greater than the number of vCPUs (via `mp.cpu_count()`).
- Updates default number of parameters for CLI to match runconfig (this is what cloud operations utilize if not specified).
- removed extraneous try/except in `normal_param_estimation_workflow` used for debugging.
- Returned allclose absolute tolerance to 1e-05 for golden dataset comparison.
- Ensures Earthdata credentials are provided when localizing data and can be passed as environment variables.


## [0.0.7] - 2025-02-25

### Added
- Water mask ability to read from large water mask.
- Github issue templates (thanks to Scott Staniewicz)
- Tests for the CLI and main python interace tests.
- Minimum for distmetrics to ensure proper target crs is utilized when merging.
- Updated entrypoint for the docker container to allow for CLI arguments to be passed directly to the container.

### Fixed
- Ensures CLI correctly populates `apply_water_mask` and `water_mask_path` arguments.
- Updated the permissions of the `entrypoint.sh` file to be executable.


## [0.0.6] - 2025-02-21

### Fixed
- Issues with test_main.py related to where tmp directory was being created (solution, ensure tmp is made explicitly relative to the test directory as in `test_workflows.py`).
- All dependencies within virtual environment are back to conda-forge from PyPI.
- Product directory parameter is now correctly writing to the specified directory (fixes [#37](https://github.com/opera-adt/dist-s1/issues/37)).
- Fixed the CLI test (bug). The runconfig instance will have different product paths than the one created via the CLI because the product paths have the *processing time* in them, and that is different depending on when the runconfig object is created in the test and within the CLI-run test.

### Added
- Added a `n_workers_for_despeckling` argument to the `RunConfigData` model, CLI, and relevant processing functions.
- A test to ensure that the product directory is being correctly created and used within runconfig (added to test_main.py).


## [0.0.5] - 2025-02-19

### Fixed
- CLI issues with bucket/prefix for S3 upload (resolves [#32](https://github.com/opera-adt/dist-s1/issues/32)).
- Included `__main__.py` testing for the SAS entrypoint of the CLI; uses the cropped dataset to test the workflow.
- Includes `dist-s1 run_sas` testing and golden dataset comparision.
- Updates to README regarding GPU environment setup.

## [0.0.4]

### Added 
- Minimum working example of generation fo the product via `dist-s1 run`
- Integration of `dist-s1-enumerator` to identify/localize the inputs from MGRS tile ID, post-date, and track number
- Notebooks and examples to run end-to-end workflows as well as Science Application Software (SAS) workflows
- Docker image with nvidia compatibility (fixes the cuda version at 11.8)
- Download and application of the water mask (can specify a path or request it to generate from UMD GLAD LCLUC data).
- Extensive instructions in the README for various use-case scenarios.
- Golden dataset test for SAS workflow
- Allow user to specify bucket/prefix for S3 upload - makes library compatible with Hyp3.
- Ensure Earthdata credentials are provided in ~/.netrc and allow for them to be passed as suitable evnironment variables.
- Create a GPU compatible docker image (ongoing) - use nvidia docker image.
- Ensures pyyaml is in the environment (used for serialization of runconfig).
- Update equality testing for DIST-S1 product comparison.

### Fixed
* CLI issues with hyp3 

### Changed
- Pyproject.toml file to handle ruff

## [0.0.3]

### Added

- Python 3.13 support
- Updated dockerimage to ensure on login the conda environment is activated
- Instructions in the README for OPERA delivery.
- A `.Dockerignore` file to remove extraneous files from the docker image
- Allow `/home/ops` directory in Docker image to be open to all users

## [0.0.2]

### Added

- Pypi delivery workflow
- Entrypoint for CLI to localize data via internet (the SAS workflow is assumed not to have internet access)
- Data models for output data and product naming conventions
- Ensures output products follow the product and the tif layers follow the expected naming conventions
  - Provides testing/validation of the structure (via tmp directories)

### Changed

- CLI entrypoints now utilize `dist-s1 run_sas` and `dist-s1 run` rathern than just `dist-s1`. 
  - The `dist-s1 run_sas` is the primary entrypoint for Science Application Software (SAS) for SDS operations. 
  - The `dist-s1 run` is the simplified entrypoint for external users, allowing for the localization of data from publicly available data sources.

## [0.0.1]

### Added

- Initial internal release of the DIST-S1 project. Test github release workflow
