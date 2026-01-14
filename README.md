# NanoEdgeAI Reproduction: Transparent IMU Gesture Classification

This repo is a testbed for **on-device IMU gesture recognition** and for comparing:

* **NanoEdgeAI** “auto-generated” classifiers (as delivered by the tool)
  vs.
* **Fully transparent** pipelines using **scikit-learn** (training/validation) + **emlearn** (C export) deployed to a **microcontroller**

The core question: *Can NanoEdgeAI’s top-performing SVM / Random Forest / MLP models be reproduced or closely approximated using open tooling where features + hyperparameters + model structure are visible and maintainable?*

## What’s in this project

### Models

We evaluate three lightweight classifier families that are realistic for MCUs and commonly surfaced by NanoEdgeAI:

* **SVM**
* **Random Forest (RF)**
  *  sweep: `n_estimators`, `max_depth`
* **MLP**
  * sweep: hidden layer width and number of hidden layers (secondary training knobs handled with standard early stopping / reasonable defaults)

### Hardware

We used the following hardware for the project:
* NUCLEO-F411
  * ARM Cortex-M4 STM32F411RE Microcontroller IC 32-Bit 100MHz 512KB (512K x 8) FLASH
* MPU9250
  * 16-bit resolution
  * Accelerometer range up to ±16 g
  * Gyroscope range up to ±2000 degrees per second
  * Magnetometer fixed range ±4800 microTesla

### Dataset

A custom gesture dataset recorded with an **MPU9250** mounted on a pointing stick (~10 cm from the grip).

* **Signals used:** accelerometer + gyroscope only (6-DoF per sample)
  (magnetometer omitted; gesture start/end orientation is constrained)
* **Gestures:** 6 classes
* **Samples:** 200 per gesture (collected by 4 people, across multiple orientations)
* **Split:** 80/20 train/test

### Metrics (matched to NanoEdgeAI outputs)

For comparison, evaluation reports:

* **Balanced accuracy**
* **Confusion matrices**
* **Latency** (on-device timing where applicable)
* **RAM usage**
* **Flash footprint**

## Repo structure

Folder structure:
* `data/` raw CSVs
* `firmware/` MCU project that runs inference + measures latency/memory
* `Python/` data collection + preprocessing + plotting + export steps
* `home-made/` notebooks for develeopment of home-made models using scikit
* `report.pdf` is the final report submitted for our open-ended "Intro to AI" class project
