# Changelog

All notable changes to this project will be documented in this file.

## 0.0.3

* Updated code to be more compatible with xarray's standard practices.
* Switched to using the `pytcube` accessor.
* Replaced the old `colocate(grid, point)` method with `grid.pytcube.colocation(point)`.

## 0.0.2

* Added `prepare_for_colocate` and `colocate` methods.
* Removed `extraction` and `compute` methods.
* Replaced `vindex` with `fast-vindex`.

## 0.0.1

* Introduced `extraction` and `compute` methods.
* Opened a large part of the datacube or used the classic `vindex` method.
* Implemented a batching system.
