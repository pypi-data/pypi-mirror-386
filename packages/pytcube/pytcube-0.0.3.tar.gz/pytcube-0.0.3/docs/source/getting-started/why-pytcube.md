# Overview: Why PytCube?

## Context

In geosciences, many research tasks require the comparison of multiple datasets (analysis, calibration, validation, etc.).

A common preliminary step is to perform a **colocation** between datasets to select only the data surrounding the observation points of interest.

PytCube provides an efficient solution for colocation between a **grid** (multidimensional data array) and a set of **observation points**, allowing the extraction of **mini-cubes** around each point.

![](/_static/pytcube_schema.png)

## Challenges

Performing a colocation for a single observation point is straightforward using `xarray`. The challenge arises when dealing with **thousands or hundreds of thousands of points**. Sequential operations quickly become too slow, and parallelization becomes necessary.

PytCube addresses this challenge by combining **Xarray** and **Dask** to efficiently extract data from large grids in parallel. Furthermore, it leverages **fast_vindex**, a specialized library that optimizes Dask’s `vindex` function for fast and scalable multidimensional indexing. This makes colocation practical even for very large grids and large numbers of points.

## Main Function

PytCube now provides a single, unified method:

* **`grid.pytcube.colocation()`**:
  Extracts sub-cubes from a multidimensional grid around each observation point.

  * Accepts **grid coordinates** and **point coordinates** as inputs.
  * Allows specifying a **search window** along each dimension to define the size of the extracted mini-cube.
  * Supports **cyclic dimensions**, e.g., longitude, where mini-cubes wrap around the grid boundaries.
  * Returns a new grid containing the extracted mini-cubes along with both **grid coordinates** and **point coordinates**.
  * Fully compatible with **lazy evaluation** using Dask for large-scale computations.

With this single method, PytCube simplifies the colocation workflow and removes the need for multiple preparatory functions.







<!-- # Overview: Why PytCube?

## Context

In the field of Geosciences, many research works require the comparison of several datasets (analysis, calibration, qualification, etc.).

To facilitate this operation, a preliminary step involves performing a co-location between the datasets to select only the data of interest useful for subsequent comparisons.

Depending on the input data, there are different methods to achieve this co-location. PytCube aims to provide an efficient solution for co-locating a `DataCube` with a `Dataset` of observation points to obtain co-located data, referred to as `MiniCubes`.

![](/_static/pytcube_schema.png)

## Issues

The co-location between an observation point and a datacube is not complicated to perform in itself. Indeed, `Xarray` provides simple and effective solutions for this operation. The complexity arises when one wishes to scale up and perform co-locations on 1,000, 10,000, or even 100,000 points. At this stage, performing the operations sequentially is no longer feasible. It becomes necessary to parallelize the operation using `Dask`.

This is where `PytCube` comes into play. Based on `Xarray` and `Dask`, PytCube aims to facilitate and optimize the co-location step by parallelizing the extraction of data from the datacube.

To perform these operations, PytCube provides two main functions:

* **`pytcube.prepare_for_colocate`**:
  Prepares point-based indexing by computing the nearest grid cell indices for each observation point within a specified search window. This function performs coordinate alignment, validity checks, domain filtering, and builds the indexing arrays needed for fast subsetting. It returns formatted versions of the input grid and point datasets, ready for colocation.

* **`pytcube.colocate`**:
  Performs the actual extraction of spatio-temporal sub-cubes around each observation point using advanced indexing. This function leverages `fast-vindex` for efficient and parallel-compatible selection, and is suitable for use in larger workflows involving distributed computing or writing to formats like Zarr. -->
