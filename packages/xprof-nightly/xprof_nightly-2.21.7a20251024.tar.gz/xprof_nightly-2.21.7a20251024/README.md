# XProf (+ Tensorboard Profiler Plugin)
XProf includes a suite of profiling tools for [JAX](https://jax.readthedocs.io/), [TensorFlow](https://www.tensorflow.org/), and [PyTorch/XLA](https://github.com/pytorch/xla). These tools help you understand, debug and optimize machine learning programs to run on CPUs, GPUs and TPUs.

XProf offers a number of tools to analyse and visualize the
performance of your model across multiple devices. Some of the tools include:

*   **Overview**: A high-level overview of the performance of your model. This
    is an aggregated overview for your host and all devices. It includes:
    *   Performance summary and breakdown of step times.
    *   A graph of individual step times.
    *   High level details of the run environment.
*   **Trace Viewer**: Displays a timeline of the execution of your model that shows:
    *   The duration of each op.
    *   Which part of the system (host or device) executed an op.
    *   The communication between devices.
*   **Memory Profile Viewer**: Monitors the memory usage of your model.
*   **Graph Viewer**: A visualization of the graph structure of HLOs of your model.

To learn more about the various XProf tools, check out the [XProf documentation](https://openxla.org/xprof)

## Demo
First time user? Come and check out this [Colab Demo](https://docs.jaxstack.ai/en/latest/JAX_for_LLM_pretraining.html).

## Quick Start

### Prerequisites

* xprof >= 2.20.0
* (optional) TensorBoard >= 2.20.0

Note: XProf requires access to the Internet to load the [Google Chart library](https://developers.google.com/chart/interactive/docs/basic_load_libs#basic-library-loading).
Some charts and tables may be missing if you run XProf entirely offline on
your local machine, behind a corporate firewall, or in a datacenter.

If you use Google Cloud to run your workloads, we recommend the
[xprofiler tool](https://github.com/AI-Hypercomputer/cloud-diagnostics-xprof).
It provides a streamlined profile collection and viewing experience using VMs
running XProf.

### Installation

To get the most recent release version of XProf, install it via pip:

```
$ pip install xprof
```

Without TensorBoard:

```
$ xprof --logdir=profiler/demo --port=6006
```

With TensorBoard:

```
$ tensorboard --logdir=profiler/demo
```
If you are behind a corporate firewall, you may need to include the `--bind_all`
tensorboard flag.

Go to `localhost:6006/#profile` of your browser, you should now see the demo
overview page show up.
Congratulations! You're now ready to capture a profile.

## Nightlies

Every night, a nightly version of the package is released under the name of
`xprof-nightly`. This package contains the latest changes made by the XProf
developers.

To install the nightly version of profiler:

```
$ pip uninstall xprof tensorboard-plugin-profile
$ pip install xprof-nightly
```

## Next Steps

* [JAX Profiling Guide](https://jax.readthedocs.io/en/latest/profiling.html#xprof-tensorboard-profiling)
* [PyTorch/XLA Profiling Guide](https://cloud.google.com/tpu/docs/pytorch-xla-performance-profiling-tpu-vm)
* [TensorFlow Profiling Guide](https://tensorflow.org/guide/profiler)
* [Cloud TPU Profiling Guide](https://cloud.google.com/tpu/docs/cloud-tpu-tools)
* [Colab Tutorial](https://www.tensorflow.org/tensorboard/tensorboard_profiling_keras)
* [Tensorflow Colab](https://www.tensorflow.org/tensorboard/tensorboard_profiling_keras)
