import random
import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim
from collections import deque
from model import RocketDQN  # Mudado de '.model' para 'model'

class DQNAgent:
    def __init__(self, state_size, action_size, learning_rate=0.001, 
                 gamma=0.99, batch_size=64, buffer_size=10000, 
                 epsilon_start=1.0, epsilon_end=0.05, epsilon_decay=0.995):
        """
        Agente DQN para controlar o foguete
        :param state_size: Tamanho do vetor de estado
        :param action_size: Número de ações possíveis
        """
        self.state_size = state_size
        self.action_size = action_size
        
        # Hiperparâmetros
        self.gamma = gamma  # Fator de desconto
        self.epsilon = epsilon_start  # Taxa de exploração
        self.epsilon_min = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        # Dispositivo (GPU se disponível)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Rede neural principal e rede alvo
        self.policy_net = RocketDQN(state_size, action_size).to(self.device)
        self.target_net = RocketDQN(state_size, action_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Modo de avaliação (não treinamento)
        
        # Otimizador
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        
        # Buffer de experiência (replay memory)
        self.memory = deque(maxlen=buffer_size)
        
        # Contador para atualização da rede alvo
        self.target_update_counter = 0
        self.target_update_frequency = 10  # Atualiza a rede alvo a cada 10 etapas
    
    def store_experience(self, state, action, reward, next_state, done):
        """
        Armazena uma transição na memória de experiência
        """
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state, eval_mode=False):
        """
        Seleciona uma ação usando epsilon-greedy
        :param state: Estado atual
        :param eval_mode: Se True, sempre escolhe a melhor ação (sem exploração)
        :return: Índice da ação escolhida
        """
        if (not eval_mode) and (random.random() < self.epsilon):
            return random.randrange(self.action_size)
        
        # Converte o estado para tensor
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Obtém os valores Q e escolhe a ação com maior valor
        with torch.no_grad():
            action_values = self.policy_net(state)
        return torch.argmax(action_values).item()
    
    def learn(self):
        """
        Realiza uma etapa de aprendizagem usando um batch aleatório da memória
        :return: Loss, ou None se não houver amostras suficientes
        """
        # Verifica se há amostras suficientes
        if len(self.memory) < self.batch_size:
            return None
        
        # Amostra um batch aleatório
        mini_batch = random.sample(self.memory, self.batch_size)
        
        # Prepara os dados para treinamento
        states = torch.FloatTensor([transition[0] for transition in mini_batch]).to(self.device)
        actions = torch.LongTensor([[transition[1]] for transition in mini_batch]).to(self.device)
        rewards = torch.FloatTensor([transition[2] for transition in mini_batch]).to(self.device)
        next_states = torch.FloatTensor([transition[3] for transition in mini_batch]).to(self.device)
        dones = torch.FloatTensor([transition[4] for transition in mini_batch]).to(self.device)
        
        # Valores Q atual para as ações tomadas
        q_values = self.policy_net(states).gather(1, actions)
        
        # Valores Q alvo: r + γ * max Q(s', a')
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
        target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))
        target_q_values = target_q_values.unsqueeze(1)
        
        # Calcula a perda (loss)
        loss = F.smooth_l1_loss(q_values, target_q_values)
        
        # Atualiza os pesos
        self.optimizer.zero_grad()
        loss.backward()
        
        # Clipagem do gradiente para evitar explosão
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1)
            
        self.optimizer.step()
        
        # Atualização da rede alvo periodicamente
        self.target_update_counter += 1
        if self.target_update_counter % self.target_update_frequency == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Decaimento do epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        return loss.item()
    
    def save(self, path):
        """
        Salva o modelo treinado
        :param path: Caminho para salvar o modelo
        """
        self.policy_net.save(path)
    
    def load(self, path):
        """
        Carrega um modelo salvo
        :param path: Caminho para o modelo
        """
        self.policy_net.load(path)
        self.target_net.load_state_dict(self.policy_net.state_dict())
