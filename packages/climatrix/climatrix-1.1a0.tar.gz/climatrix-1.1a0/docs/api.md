# 🧪 API Reference

Welcome to the `climatrix` API reference. Below you'll find details on key modules, classes, and methods — with examples and usage tips to help you integrate it smoothly into your climate data workflows.

---

!!! abstract
    The main module `climatrix` provides tools to extend `xarray` datasets for climate subsetting, sampling, reconstruction. It is accessible via **accessor**.

---

The library contains a few public classes:

| Class name | Description |
| -----------| ----------- |
| [`AxisType`](#climatrix.dataset.axis.AxisType) | Enumerator class for type of spatio-temporal axes |
| [`Axis`](#climatrix.dataset.axis.Axis) | Class managing spatio-temporal axes |
| [`BaseClimatrixDataset`](#climatrix.dataset.base.BaseClimatrixDataset) | Base class for managing `xarray` data |
| [`Domain`](#climatrix.dataset.domain.Domain) | Base class for domain-specific operations |
| [`SparseDomain`](#climatrix.dataset.domain.SparseDomain) | Subclass of `Domain` aim at managing sparse representations | 
| [`DenseDomain`](#climatrix.dataset.domain.DenseDomain) |  Subclass of `Domain` aim at managing dense representations |
| [`Plot`](#climatrix.plot.core.Plot) | Interactive plotting utility for climate datasets | 


## 📈 Axes 

::: climatrix.dataset.axis.AxisType
    handler: python
    options:    
      members:
        - get
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false    

::: climatrix.dataset.axis.Axis
    handler: python
    options:    
      members:
        - matches
        - size
        - get_all_axes
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false  

::: climatrix.dataset.axis.Latitude
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false  

::: climatrix.dataset.axis.Longitude
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false        

::: climatrix.dataset.axis.Time
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false        

::: climatrix.dataset.axis.Point
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false  

::: climatrix.dataset.axis.Vertical
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false  

## 📇 Data

::: climatrix.dataset.base.BaseClimatrixDataset
    handler: python
    options:
      members:
        - domain
        - subset
        - to_signed_longitude
        - to_positive_longitude
        - squeeze
        - profile_along_axes
        - mask_nan
        - time
        - itime
        - sample_uniform
        - sample_normal
        - reconstruct
        - plot
        - transpose
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false


## 🌍 Domain 

::: climatrix.dataset.domain.Domain
    handler: python
    options:
      members:
        - from_lat_lon
        - from_axes
        - dims
        - latitude
        - longitude
        - time
        - point
        - vertical
        - get_size
        - has_axis
        - get_axis
        - is_dynamic
        - is_sparse
        - size
        - all_axes_types
        - get_all_spatial_points
        - to_xarray
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false      


::: climatrix.dataset.domain.SparseDomain
    handler: python
    options:    
      members:
        - to_xarray   
        - get_all_spatial_points       
      inherited_members: 
        - from_lat_lon
        - latitude
        - longitude
        - time
        - point
        - vertical
        - get_size
        - has_axis
        - get_axis
        - is_dynamic
        - is_sparse
        - size
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false      

::: climatrix.dataset.domain.DenseDomain
    handler: python
    options:    
      members:
        - to_xarray   
        - get_all_spatial_points       
      inherited_members: 
        - from_lat_lon
        - latitude
        - longitude
        - time
        - point
        - vertical
        - get_size
        - has_axis
        - get_axis
        - is_dynamic
        - is_sparse
        - size
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false            

## 📈 Interactive Plotting

::: climatrix.plot.core.Plot
    handler: python
    options:   
      scoped_crossrefs: true 
      show_root_heading: true
      show_source: false
      members:
        - show

## 🌐 Reconstructors

::: climatrix.reconstruct.base.BaseReconstructor
    handler: python
    options:   
      scoped_crossrefs: true 
      show_root_heading: true
      show_source: false   

::: climatrix.reconstruct.idw.IDWReconstructor
    handler: python
    options:   
      scoped_crossrefs: true 
      show_root_heading: true
      show_source: false    

::: climatrix.reconstruct.kriging.OrdinaryKrigingReconstructor
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false          

::: climatrix.reconstruct.siren.siren.SIRENReconstructor
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false         

## ⚖️ Evaluation

::: climatrix.comparison.Comparison
    handler: python
    options:    
      members:
        - plot_diff
        - plot_signed_diff_hist
        - compute_rmse
        - compute_mae
        - compute_r2
        - compute_max_abs_error
        - compute_report
        - save_report
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false

## 🔧 Hyperparameter Optimization

Climatrix provides automated hyperparameter optimization for all reconstruction methods using Bayesian optimization.

### Installation

To use hyperparameter optimization, install climatrix with the optimization extras:

```bash
pip install climatrix[optim]
```

This installs the required `bayesian-optimization` package dependency.

### HParamFinder

::: climatrix.optim.HParamFinder
    handler: python
    options:    
      scoped_crossrefs: true
      show_root_heading: true
      show_source: false

### Supported Methods and Parameters

The hyperparameter optimizer supports all reconstruction methods available in Climatrix. For detailed information about each method's hyperparameters, including their types, bounds, and default values, see the [Reference](reference.md) documentation for each reconstruction class:

- [IDWReconstructor](reference.md#idwreconstructor) - Inverse Distance Weighting
- [OrdinaryKrigingReconstructor](reference.md#ordinarykrigingreconstructor) - Ordinary Kriging  
- [SiNETReconstructor](reference.md#sinetreconstructor) - Spatial Interpolation NET
- [SIRENReconstructor](reference.md#sirenreconstructor) - Sinusoidal INR   
