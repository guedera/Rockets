import torch
import torch.nn as nn
import torch.nn.functional as F

class RocketDQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        """
        Rede neural para o agente DQN
        :param input_dim: dimensão do estado (entradas)
        :param output_dim: dimensão das ações (saídas)
        """
        super(RocketDQN, self).__init__()
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, output_dim)
    
    def forward(self, x):
        """
        Forward pass pela rede
        :param x: tensor de estados
        :return: Q-values para cada ação
        """
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
    
    def save(self, path):
        """
        Salva o modelo
        :param path: caminho para salvar
        """
        torch.save(self.state_dict(), path)
    
    def load(self, path):
        """
        Carrega o modelo
        :param path: caminho para carregar
        """
        self.load_state_dict(torch.load(path))
