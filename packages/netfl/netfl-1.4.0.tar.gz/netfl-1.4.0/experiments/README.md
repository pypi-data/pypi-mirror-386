# General Specifications

## 1. Configuration

  - Host: AMD EPYC 7B12, 64-Core 2.25 GHz, 128 GB
  - Server: 14-Core 2.0 GHz, 2 GB, 1 Gbps
  - Dataset: CIFAR-10 (Train size: 50000 / Test size: 10000)
  - Partitions: 64
  - Model: CNN3
  - Optimizer: SGD (Learning rate: 0.01)
  - Aggregation Function: FedAvg
  - Batch Size: 16
  - Local Epochs: 2
  - Global Rounds: 500

## 2. Data Partitioning Strategies

### 2.1 IID

IID partitioner:

  ![IID Partitioning](./images/CIFAR10-IID.png)

### 2.2 Non-IID

Pathological partitioner with:

  - Classes per partition: 4
  - Class assignment mode: deterministic

  ![Non-IID Partitioning](./images/CIFAR10-Non-IID.png)

# Experiment Specifications

## 1 Baseline

#### 1.1.1

  - Devices: 8 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

#### 1.1.2

  - Devices: 8 × Raspberry Pi 4 (4-Core 1.5 GHz, 4 GB)
  - Bandwidth: 1 Gbps
  - Partitioning: IID

## 2. Resources

### 2.1 Device Allocation

#### 2.1.1 identical to 1.1.1

#### 2.1.2

  - Devices: 16 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

#### 2.1.3

  - Devices: 32 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

#### 2.1.4

  - Devices: 64 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

### 2.2 Network Bandwidth

#### 2.2.1

  - Devices: 32 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 25 Mbps
  - Partitioning: IID

#### 2.2.2

  - Devices: 32 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 50 Mbps
  - Partitioning: IID

#### 2.2.3 identical to 2.1.3

## 3. Heterogeneity

### 3.1 Device Heterogeneity

#### 3.1.1

  - Devices: 4 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Devices: 4 × Raspberry Pi 4 (4-Core 1.5 GHz, 4 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

#### 3.1.2

  - Devices: 8 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Devices: 8 × Raspberry Pi 4 (4-Core 1.5 GHz, 4 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

#### 3.1.3

  - Devices: 16 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Devices: 16 × Raspberry Pi 4 (4-Core 1.5 GHz, 4 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: IID

### 3.2 Data Heterogeneity

#### 3.2.1

  - Devices: 8 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: Non-IID

#### 3.2.2

  - Devices: 16 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: Non-IID

#### 3.2.3

  - Devices: 32 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: Non-IID

#### 3.2.4

  - Devices: 64 × Raspberry Pi 3 (4-Core 1.2 GHz, 1 GB)
  - Bandwidth: 100 Mbps
  - Partitioning: Non-IID
