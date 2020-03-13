## Variational AutoEncoder in TensorFlow

As a explicit method of fitting given distributions, Variational AutoEncoder ([VAE](https://arxiv.org/abs/1312.6114v10)) attributes all observations `x` obtained so far to a latent variable `Z`. By Bayesian variational inference, VAE actually optimizes a Variational Lower Bound (VLB) and thus achieves huge success in the field of intractable distribution approximation.

This repo gives a TensorFlow-based implementation of VAE, and reproduces the results recorded in original paper.

### Dataset

* [MNIST Handwritten Digits](https://cs.nyu.edu/~roweis/data/mnist_all.mat) is used in this repo.
* The codes are easily revised to run on other datasets.

### Requirement

* Python == 3.7.0
* TensorFlow == 1.14.0

### Results

* Original Input: 

<img src='./results/original_x.png'>

* After 5 epochs: 

<img src='./results/generated_X_epoch_5.png'>

* After 15 epochs: 

  <img src='./results/generated_X_epoch_15.png'>

* After 35 epochs: 

<img src='./results/generated_X_epoch_35.png'>

### Contact

* Email: xfflzl@mail.ustc.edu.cn