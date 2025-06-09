import os
import argparse
import numpy as np
import torch
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import datetime

# Adiciona o caminho do projeto para importar módulos
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game.config

from environment import RocketEnvironment
from dqn_agent import DQNAgent

def train(episodes, save_path="models", render_every=100, plot=True, save_every=100):
    """
    Treina o agente DQN no ambiente RocketEnvironment
    :param episodes: Número de episódios de treinamento
    :param save_path: Diretório para salvar o modelo
    :param render_every: Frequência de renderização para visualização
    :param plot: Se deve plotar os gráficos de treinamento
    :param save_every: Frequência para salvar o modelo
    """
    # Cria o diretório para salvar os modelos se não existir
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    # Inicializa o ambiente e o agente
    env = RocketEnvironment()
    agent = DQNAgent(
        state_size=env.state_space_size, 
        action_size=env.action_space_size,
        learning_rate=0.0005,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995,
        batch_size=64,
        buffer_size=50000
    )
    
    # Métricas para monitorar o treinamento
    rewards_history = []
    success_history = []
    loss_history = []
    epsilon_history = []
    fuel_history = []
    
    # Timestamp para o nome do modelo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Loop principal de treinamento
    for episode in tqdm(range(1, episodes+1)):
        state = env.reset()
        episode_reward = 0
        episode_loss = []
        
        # Executa um episódio
        while True:
            # Escolhe uma ação
            action = agent.act(state)
            
            # Executa a ação
            next_state, reward, done, info = env.step(action)
            
            # Armazena a experiência
            agent.store_experience(state, action, reward, next_state, done)
            
            # Aprendizado
            loss = agent.learn()
            if loss is not None:
                episode_loss.append(loss)
            
            # Atualiza o estado e acumula recompensas
            state = next_state
            episode_reward += reward
            
            if done:
                break
        
        # Registra métricas do episódio
        rewards_history.append(episode_reward)
        success_history.append(1 if info["landed"] and info["target_reached"] else 0)
        if episode_loss:
            loss_history.append(np.mean(episode_loss))
        epsilon_history.append(agent.epsilon)
        fuel_history.append(info["fuel_used"])
        
        # Exibe progresso periodicamente
        if episode % 10 == 0:
            avg_reward = np.mean(rewards_history[-10:])
            avg_success = np.mean(success_history[-10:]) * 100
            print(f"Episódio {episode}/{episodes} | Recompensa: {episode_reward:.2f} | "
                  f"Média (10): {avg_reward:.2f} | Sucesso: {avg_success:.1f}% | "
                  f"Epsilon: {agent.epsilon:.3f} | Combustível: {info['fuel_used']:.1f}%")
        
        # Salva o modelo periodicamente
        if episode % save_every == 0:
            model_path = f"{save_path}/rocket_dqn_{timestamp}_ep{episode}.pt"
            agent.save(model_path)
            print(f"Modelo salvo em {model_path}")
    
    # Salva o modelo final
    final_model_path = f"{save_path}/rocket_dqn_{timestamp}_final.pt"
    agent.save(final_model_path)
    print(f"Modelo final salvo em {final_model_path}")
    
    # Plota gráficos de treinamento
    if plot:
        plt.figure(figsize=(15, 10))
        
        plt.subplot(2, 2, 1)
        plt.plot(rewards_history)
        plt.title('Recompensa por Episódio')
        plt.xlabel('Episódio')
        plt.ylabel('Recompensa')
        
        plt.subplot(2, 2, 2)
        plt.plot(success_history)
        plt.title('Taxa de Sucesso')
        plt.xlabel('Episódio')
        plt.ylabel('Sucesso (0/1)')
        
        plt.subplot(2, 2, 3)
        plt.plot(loss_history)
        plt.title('Loss')
        plt.xlabel('Episódio')
        plt.ylabel('Loss')
        
        plt.subplot(2, 2, 4)
        plt.plot(fuel_history)
        plt.title('Consumo de Combustível')
        plt.xlabel('Episódio')
        plt.ylabel('Combustível usado (%)')
        
        plt.tight_layout()
        plt.savefig(f"{save_path}/training_plots_{timestamp}.png")
        plt.show()
    
    return agent, final_model_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Treinar o agente DQN para o jogo Rocket')
    parser.add_argument('--episodes', type=int, default=1000, help='Número de episódios de treinamento')
    parser.add_argument('--save_path', type=str, default='models', help='Diretório para salvar o modelo')
    parser.add_argument('--save_every', type=int, default=100, help='Frequência para salvar o modelo')
    parser.add_argument('--no_plot', action='store_true', help='Não plotar gráficos de treinamento')
    
    args = parser.parse_args()
    
    print(f"Iniciando treinamento por {args.episodes} episódios...")
    print(f"Dispositivo: {torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')}")
    
    agent, model_path = train(
        episodes=args.episodes,
        save_path=args.save_path,
        plot=not args.no_plot,
        save_every=args.save_every
    )
    
    print("Treinamento concluído!")
    print(f"Modelo final salvo em {model_path}")
