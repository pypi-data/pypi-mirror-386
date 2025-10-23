# da4ml: Distributed Arithmetic for Machine Learning

[![LGPLv3](https://img.shields.io/badge/License-LGPLv3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Documentation](https://github.com/calad0i/da4ml/actions/workflows/sphinx-build.yml/badge.svg)](https://calad0i.github.io/da4ml/)
[![PyPI version](https://badge.fury.io/py/da4ml.svg)](https://badge.fury.io/py/da4ml)
[![ArXiv](https://img.shields.io/badge/arXiv-2507.04535-b31b1b.svg)](https://arxiv.org/abs/2507.04535)

da4ml is a library for implementing distributed arithmetic (DA) based algorithms for ultra-low latency machine learning (ML) applications on FPGAs. It as two major components:
 - A fast and performant constant-matrix-vector multiplications (CMVM) optimizer to implement them as
   efficient adder trees. Common sub-expressions elimination (CSE) with graph-based pre-optimization are
   performed to reduce the firmware footprint and improve the performance.
 - Low-level symbolic tracing frameworks for generating combinational/fully pipelined logics in HDL or HLS
   code. For fully pipelined networks, da4ml can generate the firmware for the whole network standalone.
   Alternatively, da4ml be used as a plugin in hls4ml to optimize the CMVM operations in the network.


Key Features
------------

- **Optimized Algorithms**: Comparing to hls4ml's latency strategy, da4ml's CMVM implementation uses no DSO and consumes up to 50% less LUT usage.
- **Fast code generation**: da4ml can generate HDL for a fully pipelined network in seconds. For the same models, high-level synthesis tools like Vivado/Vitis HLS can take up to days to generate the HDL code.
- **Low-level symbolic tracing**: As long as the operation can be expressed by a combination of the low-level operations supported, adding new operations is straightforward by "replaying" the operation on the symbolic tensor provided. In most cases, adding support for a new operation/layer takes just a few lines of code in numpy flavor.
- **Automatic model conversion**: da4ml can automatically convert models trained in `HGQ2 <https://github.com/calad0i/hgq2>`_.
- **Bit-accurate Simulation**: All operation in da4ml is bit-accurate, meaning the generated HDL code will produce the same output as the original model. da4ml's computation is converted to a RISC-like, instruction set level intermediate representation, distributed arithmetic instruction set (DAIS), which can be easily simulated in multiple ways.
- **hls4ml integration**: da4ml can be used as a plugin in hls4ml to optimize the CMVM operations in the network by setting `strategy='distributed_arithmetic'` for the strategy of the Dense, EinsumDense, or Conv1/2D layers.

Installation
------------

```bash
pip install da4ml
```

Getting Started
---------------

See the [Getting Started](https://calad0i.github.io/da4ml/getting_started.html) guide for a quick introduction to using da4ml.
