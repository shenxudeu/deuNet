"""
Example of train a 2-layers Neural Network classifier on CIFAR-10 dataset
"""
import numpy as np
import sys

sys.path.append("../../deuNet/")

from deuNet.utils import np_utils
from deuNet.datasets import cifar10
from deuNet.models import NN
from deuNet.layers.core import AffineLayer, Dropout
from deuNet.layers.convolutional import Convolution2D,Flatten,MaxPooling2D
from deuNet.layers.batch_normalization import BatchNormalization

import pdb
np.random.seed(1984)

batch_size = 128
nb_classes = 10
nb_epoch = 100
learning_rate = .5
w_scale = 1e-2
momentum = 0.9
lr_decay = 1e-7
w_decay = 5e-4
epoch_step = 25
lr_drop_rate = 0.5
nesterov = True
rho = 0.9
reg_W = 0.

checkpoint_fn = '.trained_cifar10_cnn.h5'
log_fn = '.cifar_my_vgg.log'

(train_X, train_y), (test_X, test_y) = cifar10.load_data()
valid_X,valid_y = test_X, test_y


# convert data_y to one-hot
train_y = np_utils.one_hot(train_y, nb_classes)
valid_y = np_utils.one_hot(valid_y, nb_classes)
test_y = np_utils.one_hot(test_y, nb_classes)

train_X = train_X.astype("float32")
valid_X = valid_X.astype("float32")
test_X = test_X.astype("float32")
train_X /= 255
valid_X /= 255
test_X  /= 255


pool  = lambda x, y, kernel, stride: ((x-kernel)/stride+1, (y-kernel)/stride+1) 

def ConvSame(nInputFilters,nOutputFilters, model):
    model.add(Convolution2D(nOutputFilters,nInputFilters,3,3, border_mode='full',
        init='glorot_uniform',activation='relu', reg_W=reg_W))
    model.add(Convolution2D(nOutputFilters,nOutputFilters,3,3, border_mode='valid',
        init='glorot_uniform',activation='relu', reg_W=reg_W))
    return model

def ConvSameBN(nInputFilters,nOutputFilters, model):
    model.add(Convolution2D(nOutputFilters,nInputFilters,3,3, border_mode='full',
        init='glorot_uniform',activation='linear', reg_W=reg_W))
    model.add(Convolution2D(nOutputFilters,nOutputFilters,3,3, border_mode='valid',
        init='glorot_uniform',activation='linear', reg_W=reg_W))
    model.add(BatchNormalization((1,nOutputFilters,1,1),activation='relu'))
    return model


ignore_border = True

# NN architecture
model = NN(checkpoint_fn, log_fn)

nh, nw = (32, 32)

BN = False
if BN:
    ConvS = ConvSameBN
else:
    ConvS = ConvSame

model = ConvS(3,32, model)
model.add(Dropout(0.25, uncertainty=False)) 
model = ConvS(32,32, model)
model.add(MaxPooling2D(pool_size=(2,2),ignore_border=ignore_border))
nh, nw = pool(nh, nw, 2,2)
#model.add(Dropout(0.25, uncertainty=False)) 


model = ConvS(32,64, model)
model.add(Dropout(0.25,uncertainty=False))
model = ConvSame(64,64, model)
model.add(MaxPooling2D(pool_size=(2,2),ignore_border=ignore_border))
nh, nw = pool(nh, nw, 2,2)
#model.add(Dropout(0.25,uncertainty=False))

model = ConvS(64,128, model)
model.add(Dropout(0.25,uncertainty=False))
model = ConvSame(128,128, model)
model.add(MaxPooling2D(pool_size=(2,2),ignore_border=ignore_border))
nh, nw = pool(nh, nw, 2,2)


model = ConvS(128,256, model)
model.add(Dropout(0.25,uncertainty=False))
model = ConvSame(256,256, model)
model.add(MaxPooling2D(pool_size=(2,2),ignore_border=ignore_border))
nh, nw = pool(nh, nw, 2,2)

model = ConvS(256,512, model)
model.add(Dropout(0.25,uncertainty=False))
model = ConvSameBN(512,512, model)
model.add(MaxPooling2D(pool_size=(2,2),ignore_border=ignore_border))
nh, nw = pool(nh, nw, 2,2)


model.add(Flatten())
model.add(AffineLayer(nh*nw*512, 512,activation='relu',reg_W=reg_W, init='glorot_uniform'))
model.add(Dropout(0.5, uncertainty=False))
model.add(AffineLayer(512, nb_classes,activation='softmax',reg_W=reg_W,init='glorot_uniform'))


# Compile NN
print 'Compile NN ...'
model.compile(optimizer='SGD', loss='categorical_crossentropy',
        reg_type='L2', learning_rate = learning_rate, momentum=momentum,
        lr_decay=lr_decay, nesterov=nesterov, rho=rho, w_decay=w_decay)

# Train NN
model.fit(train_X, train_y, valid_X, valid_y,
        batch_size=batch_size, nb_epoch=nb_epoch, verbose=True,
        epoch_step=epoch_step,lr_drop_rate=lr_drop_rate)

# Test NN
model.get_test_accuracy(test_X, test_y)

