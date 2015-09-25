import theano
import theano.tensor as T

from .. import activations, initializations
from .. utils.theano_utils import shared_zeros
from .. layers.core import Layer

import pdb

class BatchNormalization(Layer):
    """
    Batch Normalization:
    Published by S. Ioffee and C. Szegedy from Google.Solve the gradient
    divergence and vanish problem by normalizing features.

    http://arxiv.org/pdf/1502.03167v3.pdf

    We can follow this for the convnet: https://gist.github.com/f0k/f1a6bd3c8585c400c190
    """
    def __init__(self, input_shape, 
            activation='linear',epsilon=1e-6,
            ema_lambda=0.9):
        super(BatchNormalization,self).__init__()
        self.init = initializations.get("uniform")
        self.input_shape = input_shape
        self.epsilon = epsilon
        self.ema_lambda = ema_lambda
        self.activation = activations.get(activation)

        self.axes = (0,) + tuple(range(2,len(self.input_shape)))
        
        #element-wise shift
        self.gamma = self.init((self.input_shape))
        self.beta = shared_zeros(self.input_shape)
        
        # online \mu an \std for test pass normalization
        self.running_mean = None
        self.running_std  = None
        
        # two parameters needs to be learned
        self.params = [self.gamma, self.beta]
        
    
    def get_output(self, train):
        """
        This implementation can handle AffineLayer as well as
        Convolutional layer. We assume the second axes is the feature:
        in affinelayer, 2nd axes is number of nodes
        in convolutional layer, 2nd axes is the stack size.

        Detail for conv layer according to section 3.2 
        "Batch-Normalized Convolutional Networks" in reference paper.
        """
        X = self.get_input(train)
        
        if train:
            # first axis is batch samples 
            mean_val = X.mean(axis=self.axes,keepdims=True)
            std_val  = T.mean((X-mean_val)**2 + self.epsilon, axis=self.axes,keepdims=True) ** 0.5
            X_normed = (X - mean_val) / (std_val + self.epsilon)

            if self.running_mean is None:
                self.running_mean = mean_val
                self.running_std  = std_val
            else:
                self.running_mean *= self.ema_lambda
                self.running_mean += (1 - self.ema_lambda) * mean_val
                self.running_std *= self.ema_lambda
                self.running_std += (1 - self.ema_lambda) * std_val

        else:
            X_normed = (X - self.running_mean) / (self.running_std + self.epsilon)
        
        out_val = T.addbroadcast(self.gamma,*self.axes) * X_normed + T.addbroadcast(self.beta,*self.axes)
        #out_val =self.gamma * X_normed + self.beta
        
        return self.activation(out_val)


    def get_config(self):
        return {"name":self.__class__.__name__,
                "input_shape": self.input_shape,
                "epsilon": self.epsilon}
        

