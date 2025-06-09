import os
import sys
import argparse
import numpy as np
import torch
import time
import math

# Adiciona o caminho do projeto para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game.config
import pygame

from game.src.entities.rocket import Rocket
from game.src.entities.platform import Platform
from game.src.entities.target import Target

from dqn_agent import DQNAgent
from environment import RocketEnvironment

def play_with_agent(model_path, num_episodes=5, render=True, fps=60, wait=False):
    """
    Faz o agente treinado jogar o jogo
    :param model_path: Caminho para o modelo treinado
    :param num_episodes: Número de episódios para jogar
    :param render: Se deve renderizar o jogo em tempo real
    :param fps: Quadros por segundo para renderização
    :param wait: Se deve esperar um tempo entre episódios
    """
    # Configura o ambiente
    if not render:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    
    pygame.init()
    WIDTH, HEIGHT = game.config.WIDTH, game.config.HEIGHT
    
    if render:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rocket Landing AI")
    else:
        screen = pygame.Surface((WIDTH, HEIGHT))
    
    clock = pygame.time.Clock()
    
    # Carrega as fontes para informações na tela
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_path, "game/src/utils/JetBrainsMono-Regular.ttf")
        font = pygame.font.Font(font_path, 18)
        big_font = pygame.font.Font(font_path, 36)
    except:
        # Fallback para fonte padrão se não encontrar a fonte específica
        font = pygame.font.SysFont(None, 18)
        big_font = pygame.font.SysFont(None, 36)
    
    # Inicializa o ambiente e o agente
    env = RocketEnvironment()
    agent = DQNAgent(state_size=env.state_space_size, action_size=env.action_space_size)
    agent.load(model_path)  # Carrega o modelo treinado
    agent.epsilon = 0  # Desativa exploração para avaliação
    
    print(f"Modelo carregado de {model_path}")
    print(f"Jogando {num_episodes} episódios...")
    
    total_success = 0
    total_target_reached = 0
    
    for episode in range(num_episodes):
        state = env.reset()
        done = False
        episode_reward = 0
        steps = 0
        
        print(f"Episódio {episode+1}/{num_episodes}")
        
        while not done:
            # Seleciona a ação com o modelo treinado
            action = agent.act(state, eval_mode=True)
            
            # Executa a ação
            next_state, reward, done, info = env.step(action)
            episode_reward += reward
            steps += 1
            
            # Atualiza o estado
            state = next_state
            
            # Renderiza o jogo
            if render:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                
                # Limpa a tela
                screen.fill((0, 0, 0))
                
                # Renderiza as plataformas
                pygame.draw.rect(screen, (100, 100, 100), 
                                 (env.initial_platform.posicao[0], HEIGHT - env.initial_platform.posicao[1] - 10, 
                                  env.initial_platform.comprimento, 10))
                pygame.draw.rect(screen, (100, 100, 100), 
                                 (env.landing_platform.posicao[0], HEIGHT - env.landing_platform.posicao[1] - 10, 
                                  env.landing_platform.comprimento, 10))
                
                # Renderiza o target
                pygame.draw.circle(screen, (255, 0, 0), 
                                 (int(env.target.posicao[0]), HEIGHT - int(env.target.posicao[1])), 
                                 int(env.target.altura / 2))
                
                # Renderiza o foguete
                rocket_rect = pygame.Rect(0, 0, 20, 40)
                rocket_rect.center = (env.foguete.posicao[0], HEIGHT - env.foguete.posicao[1])
                
                # Rotaciona o foguete
                rocket_surface = pygame.Surface((20, 40), pygame.SRCALPHA)
                rocket_surface.fill((0, 0, 0, 0))  # Transparente
                pygame.draw.rect(rocket_surface, (200, 200, 200), (0, 0, 20, 40))
                
                # Rotacionar a superfície do foguete
                angle_degrees = 90 - env.foguete.orientacao  # Ajuste para renderização
                rotated_rocket = pygame.transform.rotate(rocket_surface, angle_degrees)
                rotated_rect = rotated_rocket.get_rect(center=rocket_rect.center)
                screen.blit(rotated_rocket, rotated_rect.topleft)
                
                # Efeito de fogo se o motor estiver ligado
                if env.foguete.potencia_motor > 0:
                    fire_length = env.foguete.potencia_motor / 5  # Ajuste para visualização
                    # Posição ajustada para a base do foguete considerando a rotação
                    angle_rad = math.radians(env.foguete.orientacao)
                    fire_pos_x = env.foguete.posicao[0] - math.sin(angle_rad) * 20
                    fire_pos_y = HEIGHT - env.foguete.posicao[1] - math.cos(angle_rad) * 20
                    
                    # Desenhando o fogo como um triângulo
                    fire_points = [
                        (fire_pos_x, fire_pos_y),
                        (fire_pos_x - math.sin(angle_rad - 0.2) * fire_length, 
                         fire_pos_y - math.cos(angle_rad - 0.2) * fire_length),
                        (fire_pos_x - math.sin(angle_rad + 0.2) * fire_length, 
                         fire_pos_y - math.cos(angle_rad + 0.2) * fire_length)
                    ]
                    pygame.draw.polygon(screen, (255, 165, 0), fire_points)
                
                # Informações na tela
                info_text = [
                    f"Passo: {steps}",
                    f"Recompensa: {episode_reward:.1f}",
                    f"Combustível: {100-env.foguete.fuel_consumed:.1f}%",
                    f"Velocidade: ({env.foguete.velocidade[0]:.1f}, {env.foguete.velocidade[1]:.1f})",
                    f"Target atingido: {'Sim' if env.foguete.target_reached else 'Não'}",
                    f"Potência: {env.foguete.potencia_motor:.1f}",
                    f"Orientação: {env.foguete.orientacao:.1f}°"
                ]
                
                for i, text in enumerate(info_text):
                    text_surface = font.render(text, True, (255, 255, 255))
                    screen.blit(text_surface, (10, 10 + i * 22))
                
                # Status do episódio
                if env.foguete.landed:
                    status_text = "POUSO BEM SUCEDIDO" if env.foguete.target_reached else "POUSO SEM TARGET"
                    color = (0, 255, 0) if env.foguete.target_reached else (255, 255, 0)
                elif env.foguete.crashed:
                    status_text = "CRASH!"
                    color = (255, 0, 0)
                else:
                    status_text = ""
                    color = (255, 255, 255)
                
                if status_text:
                    text_surface = big_font.render(status_text, True, color)
                    text_rect = text_surface.get_rect(center=(WIDTH/2, HEIGHT/2))
                    screen.blit(text_surface, text_rect)
                
                pygame.display.flip()
                clock.tick(fps)
        
        # Estatísticas do episódio
        success = info["landed"] and info["target_reached"]
        total_success += 1 if success else 0
        total_target_reached += 1 if info["target_reached"] else 0
        
        print(f"Episódio {episode+1} concluído | Passos: {steps} | Recompensa: {episode_reward:.1f}")
        print(f"Pouso: {'Sucesso' if info['landed'] else 'Falha'} | "
              f"Target: {'Atingido' if info['target_reached'] else 'Não atingido'} | "
              f"Combustível usado: {info['fuel_used']:.1f}%")
        
        # Espera um pouco entre episódios
        if wait and render and episode < num_episodes - 1:
            waiting_text = big_font.render("Próximo episódio...", True, (255, 255, 255))
            waiting_rect = waiting_text.get_rect(center=(WIDTH/2, HEIGHT-50))
            screen.blit(waiting_text, waiting_rect)
            pygame.display.flip()
            time.sleep(2)
    
    # Estatísticas gerais
    print("\nEstatísticas dos Episódios:")
    print(f"Taxa de sucesso completo: {total_success/num_episodes*100:.1f}%")
    print(f"Taxa de alcance do target: {total_target_reached/num_episodes*100:.1f}%")
    
    if render:
        pygame.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Testar o agente DQN para o jogo Rocket')
    parser.add_argument('--model', type=str, required=True, help='Caminho para o modelo treinado')
    parser.add_argument('--episodes', type=int, default=5, help='Número de episódios para jogar')
    parser.add_argument('--no_render', action='store_true', help='Desativar renderização')
    parser.add_argument('--fps', type=int, default=60, help='Quadros por segundo')
    parser.add_argument('--wait', action='store_true', help='Esperar entre episódios')
    
    args = parser.parse_args()
    
    play_with_agent(
        model_path=args.model,
        num_episodes=args.episodes,
        render=not args.no_render,
        fps=args.fps,
        wait=args.wait
    )
