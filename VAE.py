import time
import numpy as np
import tensorflow as tf
import tensorflow.nn as tfn
import tensorflow.layers as tfl
import tensorflow.train as tft
import tensorflow.contrib as tfc
import scipy.special as scs
import matplotlib.pyplot as plt

from DataLoader import DataLoader

flags = tf.app.flags
flags.DEFINE_string('datafile', 'mnist_all.mat', 'Name of data file')
flags.DEFINE_string('decoder', 'Bernoulli', 'optional, Bernoulli or Gaussian')
flags.DEFINE_integer('hidden_layer_neurons', 500, 'Number of hidden layer neurons')
flags.DEFINE_integer('z_dim', 10, 'Latent variable dimension')
flags.DEFINE_integer('batch_size', 64, 'Minibatch size')
flags.DEFINE_integer('num_epoch', 150, 'Number of epochs')
flags.DEFINE_integer('side_length', 8, 'Side length of output pictures')
flags.DEFINE_float('learning_rate', 0.001, 'Learning rate')
flags.DEFINE_float('reg_coef', 0.01, 'Regularization coefficient')

FLAGS = flags.FLAGS

def encoding_network(X, hidden_layer_neurons, latent_dim, reg_coef):
    r"""This network encodes input X into latent z.

    Args:
      X: A pixel matrix.
      hidden_layer_neurons: Number of hidden layer neurons.
      latent_dim: Latent variable dimension.
      reg_coef: Regularization coefficient.

    Returns:
      KL_divergence: Distribution distance between the posterior and the prior, 
                     which can be analytically computed.
      sampled_z: Latent variables sampled by reparameterization trick.
    """
    dense1 = tfl.dense(X, hidden_layer_neurons, activation=tfn.relu, 
                       kernel_initializer=tfc.layers.variance_scaling_initializer(),
                       kernel_regularizer=tfc.layers.l2_regularizer(reg_coef))
    dense2 = tfl.dense(dense1, hidden_layer_neurons, activation=tfn.relu, 
                       kernel_initializer=tfc.layers.variance_scaling_initializer(),
                       kernel_regularizer=tfc.layers.l2_regularizer(reg_coef))

    GuassianParameters = tfl.dense(dense2, 2 * latent_dim,  
                                   kernel_initializer=tfc.layers.variance_scaling_initializer())
    mean_vector = GuassianParameters[: ,: latent_dim]
    var_vector = tf.nn.softplus(GuassianParameters[: , latent_dim: ])
    KL_divergence = 0.5 * tf.reduce_sum(1 + tf.log(var_vector) - var_vector - tf.square(mean_vector))

    # reparameterization trick
    sampled_z = tf.multiply(tf.sqrt(var_vector), tf.random_normal(mean_vector.shape)) + mean_vector
    return KL_divergence, sampled_z

def Bernoulli_decoding_network(X, z, hidden_layer_neurons, reg_coef):
    r"""This network decodes z into X (Bernoulli version).

    Args:
      X: A pixel matrix.
      z: Latent variables generated by encoder.
      hidden_layer_neurons: Number of hidden layer neurons.
      reg_coef: Regularization coefficient.

    Returns:
      generated_X: Generated X by decoding z.
      marginal_likelihood: Reconstruction error estimation, 
                           which is computed in a form of cross entropy.
    """
    dense1 = tfl.dense(z, hidden_layer_neurons, activation=tfn.relu, 
                       kernel_initializer=tfc.layers.variance_scaling_initializer(),
                       kernel_regularizer=tfc.layers.l2_regularizer(reg_coef))

    dense2 = tfl.dense(dense1, hidden_layer_neurons, activation=tfn.relu,
                       kernel_initializer=tfc.layers.variance_scaling_initializer(),
                       kernel_regularizer=tfc.layers.l2_regularizer(reg_coef))

    generated_X = tfl.dense(dense2, X.shape[1], 
                            kernel_initializer=tfc.layers.variance_scaling_initializer())

    xent = tfn.sigmoid_cross_entropy_with_logits(logits=generated_X, labels=X)
    marginal_likelihood = -tf.reduce_sum(xent)
    return generated_X, marginal_likelihood

def Gaussian_decoding_network(X, z, hidden_layer_neurons, reg_coef):
    r"""This network decodes z into X (Guassian version).

    Args:
      X: A pixel matrix.
      z: Latent variables generated by encoder.
      hidden_layer_neurons: Number of hidden layer neurons.
      reg_coef: Regularization coefficient.

    Returns:
      generated_X: Generated X by decoding z.
      marginal_likelihood: Reconstruction error estimation.
    """
    h = tfl.dense(z, hidden_layer_neurons, activation=tf.tanh, 
                  kernel_initializer=tfc.layers.variance_scaling_initializer(),
                  kernel_regularizer=tfc.layers.l2_regularizer(reg_coef))

    GuassianParameters = tfl.dense(h, 2 * X.shape[1],  
                                   kernel_initializer=tfc.layers.variance_scaling_initializer())
    mean_vector = GuassianParameters[: ,: X.shape[1]]
    var_vector = tf.nn.softplus(GuassianParameters[: , X.shape[1]: ])

    generated_X = tf.multiply(tf.sqrt(var_vector), tf.random_normal(mean_vector.shape)) + mean_vector
    marginal_likelihood = -0.5 * tf.reduce_sum(tf.log(2 * np.pi * var_vector) + tf.square(X - mean_vector) / var_vector)
    return generated_X, marginal_likelihood

def train(X):
    r"""Optimization over variational lower bound.

    Args:
      X: A pixel matrix.

    Returns:
      KL_divergence: Distribution distance between the posterior and the prior, 
                     which can be analytically computed.
      generated_X: Generated X by decoding z.
      marginal_likelihood: Distribution similarity of X and Generated X, 
                           which is computed in a form of cross entropy.
      VLB: Variational lower bound.
      train_step: Optimization step.
    """
    if FLAGS.decoder == 'Bernoulli':
        decoding_network = Bernoulli_decoding_network
    elif FLAGS.decoder == 'Gaussian':
        decoding_network = Gaussian_decoding_network
    KL_divergence, sampled_z = encoding_network(X, FLAGS.hidden_layer_neurons, 
                                                FLAGS.z_dim, FLAGS.reg_coef)
    generated_X, marginal_likelihood = decoding_network(X, sampled_z, 
                                                                 FLAGS.hidden_layer_neurons, 
                                                                 FLAGS.reg_coef)
    VLB = KL_divergence + marginal_likelihood
    train_step = tft.AdamOptimizer(FLAGS.learning_rate).minimize(-VLB)
    return KL_divergence, generated_X, marginal_likelihood, VLB, train_step

def combine(X, image_size, num_column, num_row):
    r"""Combine all test picture together.

    Args:
      X: A pixel matrix.
      image_size: Pixel-measured side length of one picture.
      num_column: Number of pictures per row.
      num_row: Number of pictures per column.

    Returns:
      X_image: A pixel matrix.
    """
    X_image = np.empty([image_size * num_row, image_size * num_column])
    for index in range(num_column * num_row):
        position = [(index // num_row) * image_size, (index % num_row) * image_size]
        X_image[position[0]: position[0] + image_size, position[1]: position[1] + image_size] = X[index].reshape(-1, image_size)
    return X_image

if __name__ == '__main__':
    _train_images, _test_images, _image_size = DataLoader('mnist_all.mat').obtain_data()
    _num_train_images, _num_test_images = _train_images.shape[0], _test_images.shape[0]
    _test_batch = _test_images[np.random.choice(_num_test_images, size=FLAGS.batch_size, replace=False)]

    _X = tf.placeholder(dtype=tf.float32, 
                        shape=[FLAGS.batch_size, _image_size ** 2], 
                        name='Input_X')
    _KL_divergence, _generated_X, _marginal_likelihood, _VLB, train_step = train(_X)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for epoch in range(FLAGS.num_epoch):
            if epoch % 5 == 0:
                if epoch ==0:
                    plt.imshow(combine(_test_batch, _image_size, FLAGS.side_length, FLAGS.side_length), cmap='gray')
                    plt.savefig('.\\results\\original_X.png')
                else:
                    # Note that _generated_X should be "sigmoided" before mapped into a picture.
                    _generated_batch = scs.expit(sess.run(_generated_X, feed_dict={_X: _test_batch}))
                    plt.imshow(combine(_generated_batch, _image_size, FLAGS.side_length, FLAGS.side_length), cmap='gray')
                    plt.savefig('.\\results\\generated_X_epoch_' + str(epoch) + '.png')

            t1 = time.time()
            A_KL_divergence = 0.0
            A_marginal_likelihood = 0.0
            A_VLB = 0.0
            for _ in range(_num_train_images // FLAGS.batch_size):
                _train_batch= _train_images[np.random.choice(_num_train_images, 
                                                             size=FLAGS.batch_size, 
                                                             replace=False)]
                _train_step, _A_KL_divergence, _A_marginal_likelihood, _A_VLB = sess.run([train_step, 
                                                                                          _KL_divergence, 
                                                                                          _marginal_likelihood, 
                                                                                          _VLB], feed_dict={_X: _train_batch})
                A_KL_divergence = A_KL_divergence + _A_KL_divergence
                A_marginal_likelihood = A_marginal_likelihood + _A_marginal_likelihood
                A_VLB = A_VLB + _A_VLB
            t2 = time.time()
            print('Epoch {}[{:.2f} s]: KL Divergence={:.2f} Marginal Likelihood={:.2f} Variational Lower Bound={:.2f}'.format(
                  epoch, t2 - t1, A_KL_divergence / _num_train_images, A_marginal_likelihood / _num_train_images, A_VLB / _num_train_images))
                  