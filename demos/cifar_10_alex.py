"""
Example of train a 2-layers Neural Network classifier on CIFAR-10 dataset
"""
import numpy as np
import sys

sys.path.append("../../deuNN/")

from deuNN.utils import np_utils
from deuNN.datasets import cifar_10
from deuNN.models import NN
from deuNN.layers.core import AffineLayer, Dropout
from deuNN.layers.convolutional import Convolution2D,Flatten,MaxPooling2D

import pdb

batch_size = 25
nb_classes = 10
nb_epoch = 100
learning_rate = 0.001
w_scale = 0.01
momentum = 0.9
lr_decay = 0.0001
nesterov = False
rho = 0.9
reg_W = 1e-4

checkpoint_fn = '.trained_cifar10_convnet.h5'

[train_X, train_y,valid_X, valid_y, test_X, test_y] = cifar_10.load_data()


# convert data_y to one-hot
train_y = np_utils.one_hot(train_y, nb_classes)
valid_y = np_utils.one_hot(valid_y, nb_classes)
test_y = np_utils.one_hot(test_y, nb_classes)

# NN architecture
model = NN(checkpoint_fn)
model.add(Convolution2D(32,3,5,5, border_mode='full',
    init='normal',activation='relu', reg_W=reg_W, w_scale=0.001))
model.add(MaxPooling2D(pool_size=(2,2)))
#model.add(Dropout(0.2, uncertainty=False))

model.add(Convolution2D(32,32,5,5, border_mode='full',
    init='normal',activation='relu', reg_W=reg_W, w_scale=0.01))
model.add(MaxPooling2D(pool_size=(2,2)))
#model.add(Dropout(0.5, uncertainty=False))

model.add(Convolution2D(64,32,5,5, border_mode='full',
    init='normal',activation='relu', reg_W=reg_W, w_scale=0.01))
model.add(MaxPooling2D(pool_size=(2,2)))
#model.add(Dropout(0.5, uncertainty=False))

model.add(Flatten())
model.add(AffineLayer(8*8*64, 64,activation='relu',reg_W=0.1))
model.add(Dropout(0.5, uncertainty=False))
model.add(AffineLayer(64, nb_classes,activation='softmax',reg_W=0.1))


# Compile NN
print 'Compile NN ...'
model.compile(optimizer='RMSprop', loss='categorical_crossentropy',
        reg_type='L2', learning_rate = learning_rate, momentum=momentum,
        lr_decay=lr_decay, nesterov=nesterov, rho=rho)

# Train NN
model.fit(train_X, train_y, valid_X, valid_y,
        batch_size=batch_size, nb_epoch=nb_epoch, verbose=True)

# Test NN
model.get_test_accuracy(test_X, test_y)
