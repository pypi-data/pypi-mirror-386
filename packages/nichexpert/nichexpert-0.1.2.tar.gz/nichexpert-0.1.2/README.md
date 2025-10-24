# NicheXpert

## Multi-view, Multi-omics Integration for  cell niches identification using Mixture-of-Expert (MoE) model from spatial omics data

[![python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-brightgreen)](https://www.python.org/) 

NicheXpert is a deep-learning algorithm to identify and characterize cell niches using Mixture-of-Expert (MoE) model

<!-- ![avatar](images/workflow.jpg) -->


## Requirements and Installation
[![anndata 0.10.9](https://img.shields.io/badge/anndata-0.10.9-success)](https://pypi.org/project/anndata/) [![matplotlib 3.7.3](https://img.shields.io/badge/matplotlib-3.7.3-ff69b4)](https://pypi.org/project/matplotlib/) [![numpy 1.23.4](https://img.shields.io/badge/numpy-1.23.4-ff69b4)](https://pypi.org/project/numpy/) [![pandas 2.1.0](https://img.shields.io/badge/pandas-2.1.0-important)](https://pypi.org/project/pandas/) [![scanpy 1.9.8](https://img.shields.io/badge/scanpy-1.9.8-informational)](https://github.com/scverse/scanpy) [![scikit-learn 1.4.1.post1](https://img.shields.io/badge/scikit--learn-1.4.1.post1-ff69b4)](https://pypi.org/project/scikit-learn/) [![seaborn 0.13.2](https://img.shields.io/badge/seaborn-0.13.2-ff69b4)](https://pypi.org/project/seaborn/) [![squidpy 1.4.1](https://img.shields.io/badge/squidpy-1.4.1-critical)](https://pypi.org/project/squidpy/) [![tqdm 4.67.1](https://img.shields.io/badge/tqdm-4.67.1-ff69b4)](https://pypi.org/project/tqdm/) [![pydantic 2.12.2](https://img.shields.io/badge/pydantic-2.12.2-9cf)](https://pypi.org/project/pydantic/) 

Note: Owing to hardware-specific dependency requirements, deep learning frameworks including PyTorch and DGL are excluded from the explicit dependency list. Unspecified packages comprise: torch, dgl, torchdata, torch-geometric, pyg_lib, torch_cluster, torch_scatter, torch_sparse, and torch_spline_conv.


## Installation Tutorial
### Create and activate conda environment with requirements installed.
For NicheXpert, the Python version need is over 3.11. If you have already installed a lower version of Python, consider installing Anaconda, and then you can create a new environment.
```
conda create -n nichexpert python=3.11
```

If a GPU is not available on your system, please install the CPU versions of PyTorch and DGL instead. You can still proceed by running the commands below to install essential dependencies.

This package is distributed via [uv](https://docs.astral.sh/uv/).

```
conda activate nichexpert
pip install uv
uv pip install nichexpert
```
### Install PyTorch and DGL with CPU version
The primary complexity lies in installing DGL and its associated PyTorch dependencies. Notably,since June 27, 2024, the DGL development team has ceased official support for Windows and macOS platforms. Here I recommend a feasible approach to install these packages.

```
uv pip install  dgl -f https://data.dgl.ai/wheels/torch-2.1/repo.html
uv pip install torch==2.1.0
uv pip install torchdata==0.7.1
uv pip install torch==2.1.0
uv pip install torch_geometric==2.6.1
```

Additional Libraries should be installed, including pyg_lib,torch_cluster, torch_scatter, torch_sparse, and torch_spline_conv.

- **[`pyg-lib`](https://github.com/pyg-team/pyg-lib)**: Heterogeneous GNN operators and graph sampling routines
- **[`torch-scatter`](https://github.com/rusty1s/pytorch_scatter)**: Accelerated and efficient sparse reductions
- **[`torch-sparse`](https://github.com/rusty1s/pytorch_sparse)**: [`SparseTensor`](https://pytorch-geometric.readthedocs.io/en/latest/advanced/sparse_tensor.html) support
- **[`torch-cluster`](https://github.com/rusty1s/pytorch_cluster)**: Graph clustering routines
- **[`torch-spline-conv`](https://github.com/rusty1s/pytorch_spline_conv)**: [`SplineConv`](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.SplineConv.html) support

These packages come with their own CPU and GPU kernel implementations based on the [PyTorch C++/CUDA/hip(ROCm) extension interface](https://github.com/pytorch/extension-cpp). For a basic usage of PyG, these dependencies are **fully optional**. For ease of installation of these extensions, the team of PyG also provides `pip` wheels for all major OS/PyTorch/CUDA combinations, see [here](https://data.pyg.org/whl).

For details, please refer to the PyTorch Geometric GitHub repository: https://github.com/pyg-team/pytorch_geometric/tree/master

In this tutorial, we will use the macOS system and install the CPU version of these packages with the following commands:

```
uv pip install https://data.pyg.org/whl/torch-2.1.0%2Bcpu/pyg_lib-0.3.0+pt21-cp311-cp311-macosx_11_0_universal2.whl
uv pip install https://data.pyg.org/whl/torch-2.1.0%2Bcpu/torch_cluster-1.6.2-cp311-cp311-macosx_10_9_universal2.whl
uv pip install https://data.pyg.org/whl/torch-2.1.0%2Bcpu/torch_scatter-2.1.2-cp311-cp311-macosx_10_9_universal2.whl
uv pip install https://data.pyg.org/whl/torch-2.1.0%2Bcpu/torch_sparse-0.6.18-cp311-cp311-macosx_10_9_universal2.whl
uv pip install https://data.pyg.org/whl/torch-2.1.0%2Bcpu/torch_spline_conv-1.2.2-cp311-cp311-macosx_10_9_universal2.whl

```
### Install PyTorch and DGL with GPU version
Building...




## Tutorials (identify cell niches)
Building...


## Acknowledgements
Building...

## About
NicheXpert is developed by [Jiyuan Yang](https://orcid.org/0000-0001-7709-6088). For any inquiries, please feel free to reach out to me via email at jiyuanyang0828@163.com.

## References
Building...
