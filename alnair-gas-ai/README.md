# Project: GPU-Centered AI System

### Background information
  
AI jobs (training and inferencing) in the cloud are normally handled by the collaboration of CPU and GPU to get the best performance. There are 4 major tasks in the AI workflow:  
  1.  preparation  
  2.  data feeding  
  3.  model computing  
  4.  result retrieving/reporting.  

CPU is responsible for task 1. 2. 4. GPU only focuses on task 3: computing.  
## CPU-centered AI data flow diagram:
<img src="./docs/alnair-cpu-centered.jpg">

Computing technology has been improved dramatically over years. Taking Nvidia GPU as an example, the computing capacity is increased 450x from G80 to A100. Meanwhile, the memory onboard of GPU is creased by 50x. In order to run GPU with full capacity, the data transfering from system memory into GPU memory becomes a critical task. On a system with multiple A100s, CPU has a heavy duty to prepare the data in time for all GPUs.

If we can reduce the workload of data transferring on CPU, it not only removes the potential bottleneck of the whole AI process, but also increases the parallelism and resourc sharing possibility.

There are some new technologies in hardware and software to support a possible GPU-centered system architecture, which includes NVMe SSD, gpudirect. THis project will explore a novel solution to provide a GPU-centered AI-training System (GAS) to offload CPU in the process. 

## GPU-centered AI-training System (GAS) data flow diagram:
<img src="./docs/alnair-gpu-centered.JPG">

GAS tries to achieve the following goals:
1.  Efficiency improvements by the resource sharing in the cloud
2.  Performance improvements in generic AI training and inference applications by the highly parallel computing

### Goal: Offloading CPU by GPU-centered AI system

1. NVMe-SSD for training data storage
2. store and read kernels from NVMe SSD as a share lib storage
3. sharing NVMe-SSD between GPUs on one node
4. gpudirect data among GPU in the cloud

<img src="./docs/alnair-GAS-pipeline.JPG">

### Project Planning
1. Stage I (architecture research)  
  . Explore the research papers for side-band SSD accessible.  
  . Setup GPU + SSD environment  
  . Develop a test program to analyze the architecture behaviors  
2. Stage II (performance research)  
  . Implement a set of API to support benchmark  
  . Implement an application to demo the capability  
  . Benchmark the performance of the new architecture with applications of native operations  
3. Stage III (Production implementation)  
  . Explore the API for complex applications like TF or Ptorch  
  . Define the CPU-Offload application field  
  . Implement API and infrastructure  

### sub tasks : 

1. Read the papers about the current work in NVMe-SSD in HPC  
  <a id="1">[1]</a> 
  Zaid Qureshi (2022) BaM: A Case for Enabling Fine-grain High Throughput GPU-Orchestrated Access to Storage  
  <a id="2">[2]</a> 
  Shweta Pandey (2022) GPM: Leveraging Persistent Memory from a GPU  
  <a id="3">[3]</a> 
  Samyam Rajbhandari (2021) ZeRO-Infinity: Breaking the GPU Memory Wall for Extreme Scale Deep Learning    
3. Setup the development/experiment environment on v100   
  a. SATA NVMe drive  
  b. M2 NVMe drive  
  c. customized M2. NVMe drive to get 26Gbps performance  
3. Explore gpu-SSD direct API  
  a. gpudirect API from the paper (1)  
  b. GPM API from the paper (2)  
4. CPU-Offload package  
  a. a lib to contain supporting functions.   
  b. working example to support gpudirect in cuda  
  c. a working example to do AI training in Cuda completely with SSD  
  d. a working example to benchmark the performance  
5. Performance Probe and improvements

### GPU direct profiling procedure :  

Start the docker image (test on V100):  
   sudo docker run --gpus all -it --rm -v $PWD:/root/test -v /mnt/gds-data:/root/data -v /mnt/data:/data --shm-size=1024m nvcr.io/nvidia/pytorch:21.09-py3  
   cd /root/test
   
NOTE: make sure that share memory is large enough.      

1. run training on imagenet without GPU-direct:  
    python test/dali_imagenet_train.py --epochs 1  
2. run training on imagenet with GPU-direct:  
    python test/dali_imagenet_train.py --epochs 1 --dali  
3. run nsys profile training on imagenet with GPU-direct:  
    nsys nvprof -o dali-imgnet-train python test/dali_imagenet_train.py --epochs 1 --dali  
    
    NOTE: 1 epoch has too much data. if you run nsys nvprof, please stop the training after 20 seconds.  
    
### GPU direct installation procedure :  
1.  Install supporting library:  
  Here is installation guild: https://docs.nvidia.com/gpudirect-storage/troubleshooting-guide/index.html#install-prereqs%3E. It is required to install MOFED (Mellanox OpenFabrics Enterprise Distribution). MOFED is available at https://www.mellanox.com/products/infiniband-drivers/linux/mlnx_ofed.
2.  To verify the hardware configuration, there should be a set of tools installed at /usr/local/cuda/gds/tools:  (e.g on V100) 
   /usr/local/cuda/gds/tools/gdscheck -p  
   ================  
     ENVIRONMENT:  
   ================  
 =====================  
 DRIVER CONFIGURATION:  
 =====================  
 NVMe               : Unsupported  
 NVMeOF             : Unsupported  
 SCSI               : Unsupported  
 ScaleFlux CSD      : Unsupported  
 NVMesh             : Unsupported  
 DDN EXAScaler      : Unsupported  
 IBM Spectrum Scale : Unsupported  
 NFS                : Unsupported  
 WekaFS             : Unsupported  
 Userspace RDMA     : Unsupported  
 --Mellanox PeerDirect : Disabled  
 --rdma library        : Not Loaded  (libcufile_rdma.so)  
 --rdma devices        : Not configured  
 --rdma_device_status  : Up: 0 Down: 0  
 =====================  
 CUFILE CONFIGURATION:  
 =====================  
 properties.use_compat_mode : true  
 properties.gds_rdma_write_support : true  
 properties.use_poll_mode : false  
 properties.poll_mode_max_size_kb : 4  
 properties.max_batch_io_timeout_msecs : 5  
 properties.max_direct_io_size_kb : 16384  
 properties.max_device_cache_size_kb : 131072  
 properties.max_device_pinned_mem_size_kb : 33554432  
 properties.posix_pool_slab_size_kb : 4 1024 16384  
 properties.posix_pool_slab_count : 128 64 32  
 properties.rdma_peer_affinity_policy : RoundRobin  
 properties.rdma_dynamic_routing : 0  
 fs.generic.posix_unaligned_writes : false  
 fs.lustre.posix_gds_min_kb: 0  
 fs.weka.rdma_write_support: false  
 profile.nvtx : false  
 profile.cufile_stats : 0  
 miscellaneous.api_check_aggressive : false  
 =========  
 GPU INFO:  
 =========  
 GPU index 0 Tesla V100-SXM3-32GB bar:1 bar size (MiB):32768 supports GDS  
 GPU index 1 Tesla V100-SXM3-32GB bar:1 bar size (MiB):32768 supports GDS  
   
### CUDA code samples :
advance features requires SMS="80"
https://github.com/nvidia/cuda-samples