import numpy as np
import os, sys
import cPickle
import time
import gzip
import theano
import theano.tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from theano.tensor.nnet.conv import conv2d
from theano.tensor.signal.downsample import max_pool_2d

srng = RandomStreams()

import pdb

def shared_data(np_data, borrow=True):
    return theano.shared(np.asarray(np_data, dtype=theano.config.floatX), borrow=borrow)
def shared_data_int32(np_data, borrow=True):
    return theano.shared(np.asarray(np_data, dtype='int32'), borrow=borrow)

def floatX(X):
    return np.asarray(X,dtype=theano.config.floatX)

def init_weights(shape):
    return theano.shared(floatX(np.random.randn(*shape) * 0.01))

def rectify(X):
    return T.maximum(X, 0.)

def softmax(X):
    e_x = T.exp(X - X.max(axis=1).dimshuffle(0, 'x'))
    return e_x / e_x.sum(axis=1).dimshuffle(0, 'x')

def dropout(X, p= 0.):
    if p > 0:
        retain_prob = 1 - p
        X *= srng.binomial(X.shape, p=retain_prob, dtype=theano.config.floatX)
        x /= retain_prob
        return X

def RMSprop(cost, params, lr=0.001, rho=0.9, epsilon=1e-6):
    grads = T.grad(cost=cost, wrt=params)
    udpates = []
    for p, g in zip(params, grads):
        acc = theano.shared(p.get_value() * 0.)
        acc_new = rho * acc + (1 - rho) * g **2
        gradient_scaling = T.sqrt(acc_new + epsilon)
        g = g / gradient_scaling
        updates.append((acc, acc_new))
        updates.append((p, p - lr * g))

    return updates


def model(X, w, w2, w3, w4, w_o, p_drop_conv, p_drop_hidden):
    l1a = rectify(conv2d(X, w, border_mode = 'full'))
    l1  = max_pool_2d(l1a, (2,2))
    l1  = dropout(l1, p_drop_conv)

    l2a = rectify(conv2d(l1, w2))
    l2  = max_pool_2d(l2a, (2,2))
    l2  = dropout(l2, p_drop_conv)

    l3a = rectify(conv2d(l2, w3))
    l3b = max_pool_2d(l3a, (2,2))
    l3  = T.flatten(l3b, outdim=2)
    l3  = dropout(l3, p_drop_conv)

    l4  = rectify(T.dot(l4, w4))
    l4 = dropout(l4, p_drop_hidden)

    pyx = softmax(T.dot(l4, w_o))
    return l1, l2, l3, l4, pyx







def to_categorical(y, nb_classes=None):
    """
    convert class vector (int: 0 to num_classes)
    to one-hot presentation
    Input:
        - y: np array, N x 1
        - nb_classes: int, number of classes
    Output:
        - Y: theano.shared(dtype='int32'), one-hot presentation
    """
    N = len(y)
    y = np.asarray(y, dtype='int32')
    if nb_classes is None:
        nb_classes = 1 + np.max(y)
    Y = np.zeros((N,nb_classes))
    Y[np.arange(N),y] = 1.
    return Y


def load_mnist(dataset):
    """
    dataset: string, the path to dataset (MNIST)
    """
    data_dir, data_file = os.path.split(dataset)
    
    # download MNIST if not found
    if not os.path.isfile(dataset):
        import urllib
        origin = (
                'http://www.iro.umontreal.ca/~lisa/deep/data/mnist/mnist.pkl.gz'
        )
        print 'Downloading MNIST from %s' % origin
        assert urllib.urlretrieve(origin, dataset)
            
    print "Loading Data ..."

    with gzip.open(dataset, 'rb') as handle:
        train_set, valid_set, test_set = cPickle.load(handle)
    pdb.set_trace()   
    train_X, train_y = shared_data(train_set[0]),shared_data_int32(to_categorical(train_set[1]))
    valid_X, valid_y = shared_data(valid_set[0]),shared_data_int32(to_categorical(valid_set[1]))
    test_X, test_y   = shared_data(test_set[0]),shared_data_int32(to_categorical(test_set[1]))
    
    rval = [(train_X, train_y), (valid_X, valid_y), (test_X, test_y)]

    return rval


datasets = load_mnist('mnist.pkl.gz')

