import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import random
from collections import deque
import matplotlib.pyplot as plt

# Garantir que o diretório atual está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.environment import RocketEnvironment

# Configura o TensorFlow para usar a GPU e mostrar informações sobre o dispositivo
print("Verificando dispositivos disponíveis para TensorFlow:")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        # Configura o TensorFlow para usar a memória da GPU de forma dinâmica
        # Isso evita que o TensorFlow aloque toda a memória da GPU de uma vez
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"Dispositivos GPU disponíveis: {len(gpus)}")
        print(f"Utilizando GPU: {gpus[0].name}")
    except RuntimeError as e:
        print(f"Erro ao configurar GPU: {e}")
else:
    print("Nenhuma GPU encontrada. Treinamento será executado na CPU.")

# Força o modo headless para treinamento mais rápido
os.environ["SDL_VIDEODRIVER"] = "dummy"

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.gamma = 0.99    # fator de desconto
        self.epsilon = 1.0   # taxa de exploração inicial
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        
    def _build_model(self):
        # Rede neural para aproximar a função Q-valor
        model = Sequential()
        model.add(Dense(64, input_dim=self.state_size, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model
    
    def update_target_model(self):
        # Copia os pesos para o target_model
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return np.argmax(act_values[0])
    
    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        
        minibatch = random.sample(self.memory, batch_size)
        states = np.array([experience[0] for experience in minibatch])
        actions = np.array([experience[1] for experience in minibatch])
        rewards = np.array([experience[2] for experience in minibatch])
        next_states = np.array([experience[3] for experience in minibatch])
        dones = np.array([experience[4] for experience in minibatch])
        
        # Predição do modelo atual
        state_values = self.model.predict(states, verbose=0)
        
        # Double DQN: Usamos o modelo atual para selecionar a ação
        # e o modelo alvo para obter o valor Q
        next_action_values = self.model.predict(next_states, verbose=0)
        next_actions = np.argmax(next_action_values, axis=1)
        
        target_next_state_values = self.target_model.predict(next_states, verbose=0)
        
        for i in range(len(minibatch)):
            if dones[i]:
                state_values[i][actions[i]] = rewards[i]
            else:
                # Double Q-Learning
                state_values[i][actions[i]] = rewards[i] + self.gamma * target_next_state_values[i][next_actions[i]]
        
        # Treina o modelo
        self.model.fit(states, state_values, epochs=1, verbose=0)
        
        # Decai a taxa de exploração
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

def train_dqn(batch_size=64, episodes=1000, use_gpu=True):
    """
    Treina um agente DQN para o ambiente RocketEnvironment
    
    Args:
        batch_size: Tamanho do lote de dados para treinamento (maior = melhor utilização da GPU)
        episodes: Número de episódios de treinamento
        use_gpu: Define se deve utilizar GPU (quando disponível)
    """
    # Se o usuário não quiser usar GPU
    if not use_gpu:
        print("Desabilitando GPU por configuração do usuário.")
        tf.config.set_visible_devices([], 'GPU')
    
    # Log do dispositivo que será usado para o treinamento
    devices = tf.config.list_physical_devices()
    print(f"Dispositivos disponíveis: {[d.name for d in devices]}")
    print(f"Dispositivo que será usado: {tf.config.get_visible_devices()}")
    
    # Configurações do ambiente e treinamento
    env = RocketEnvironment(render_mode=None)  # Modo headless
    state_size = env.get_state_size()
    action_size = env.ACTION_SPACE_SIZE
    agent = DQNAgent(state_size, action_size)
    max_steps = 2000
    
    # Para salvar os dados de desempenho
    scores = []
    epsilons = []
    avg_scores = []
    
    # Tempo de execução
    import time
    start_time = time.time()
    last_time = start_time
    
    for e in range(episodes):
        state = env.reset()
        total_reward = 0
        
        for step in range(max_steps):
            action = agent.act(state)
            next_state, reward, done, info = env.step(action)
            
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            
            if done:
                break
                
        # Treina com replay após cada episódio    
        agent.replay(batch_size)
        
        # Atualiza o modelo alvo periodicamente
        if e % 10 == 0:
            agent.update_target_model()
        
        # Salva métricas
        scores.append(total_reward)
        epsilons.append(agent.epsilon)
        avg_score = np.mean(scores[-100:]) if len(scores) >= 100 else np.mean(scores)
        avg_scores.append(avg_score)
        
        # Exibe estatísticas a cada episódio
        current_time = time.time()
        elapsed = current_time - last_time
        total_elapsed = current_time - start_time
        last_time = current_time
        
        print(f"Episode: {e+1}/{episodes}, Score: {total_reward:.2f}, Epsilon: {agent.epsilon:.2f}, " +
              f"Avg Score: {avg_score:.2f}, Time: {elapsed:.2f}s, Total: {total_elapsed:.2f}s")
        
        # Salva o modelo a cada 100 episódios
        if (e+1) % 100 == 0:
            agent.model.save(f"dqn_model_ep{e+1}.h5")
            
            # Plota gráficos
            plt.figure(figsize=(12, 5))
            
            plt.subplot(1, 2, 1)
            plt.plot(scores)
            plt.plot(avg_scores)
            plt.title('Recompensas por Episódio')
            plt.xlabel('Episódio')
            plt.ylabel('Recompensa')
            plt.legend(['Recompensa', 'Média 100 episódios'])
            
            plt.subplot(1, 2, 2)
            plt.plot(epsilons)
            plt.title('Epsilon por Episódio')
            plt.xlabel('Episódio')
            plt.ylabel('Epsilon')
            
            plt.tight_layout()
            plt.savefig(f"training_progress_ep{e+1}.png")
            plt.close()
    
    # Salva o modelo final
    agent.model.save("dqn_model_final.h5")
    
    print(f"Treinamento concluído em {time.time() - start_time:.2f} segundos.")
    return agent

if __name__ == "__main__":
    # Processa argumentos de linha de comando, se houver
    import argparse
    parser = argparse.ArgumentParser(description='Treinamento de DQN para Rockets')
    parser.add_argument('--batch-size', type=int, default=64, help='Tamanho do batch (padrão: 64)')
    parser.add_argument('--episodes', type=int, default=1000, help='Número de episódios (padrão: 1000)')
    parser.add_argument('--no-gpu', action='store_true', help='Desabilita uso da GPU')
    args = parser.parse_args()
    
    # Treina o modelo com os parâmetros especificados
    agent = train_dqn(
        batch_size=args.batch_size,
        episodes=args.episodes,
        use_gpu=not args.no_gpu
    )
