import torch
import torch.nn as nn

class LogisticsRegressions(nn.Module):
    def __init__(self, n_feature):
        super().__init__()
        
        # initialize the parameters
        self.w = nn.Parameter(torch.zeros((n_feature, 1)), requires_grad= True)
        self.b = nn.Parameter(torch.zeros(1), requires_grad= True) 

    def forward(self, x_train):
        z = x_train @ self.w + self.b
        return z.squeeze(1)



