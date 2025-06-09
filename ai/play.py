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
    # Inicializa o ambiente e o agente
    env = RocketEnvironment()
    agent = DQNAgent(state_size=env.state_space_size, action_size=env.action_space_size)
    agent.load(model_path)  # Carrega o modelo treinado
    agent.epsilon = 0  # Desativa exploração para avaliação
    
    print(f"Modelo carregado de {model_path}")
    print(f"Jogando {num_episodes} episódios...")
    
    # Inicializa pygame se renderização estiver ativa
    screen = None
    clock = None
    background = None
    font = None
    
    if render:
        pygame.init()
        WIDTH, HEIGHT = game.config.WIDTH, game.config.HEIGHT
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rocket Landing AI - Agent Playing")
        clock = pygame.time.Clock()
        
        # Carrega o fundo
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            image_path = os.path.join(base_path, "game/src/images/Fundo.png")
            if os.path.exists(image_path):
                background = pygame.image.load(image_path).convert()
                background = pygame.transform.scale(background, (WIDTH, HEIGHT))
            else:
                background = pygame.Surface((WIDTH, HEIGHT))
                background.fill((0, 0, 0))
        except:
            background = pygame.Surface((WIDTH, HEIGHT))
            background.fill((0, 0, 0))
        
        # Carrega fonte
        try:
            font_path = os.path.join(base_path, "game/src/utils/JetBrainsMono-Regular.ttf")
            font = pygame.font.Font(font_path, 24)
        except:
            font = pygame.font.Font(None, 24)
    
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
            
            # Renderiza usando o sistema do jogo original
            if render:
                # Processa eventos do pygame
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                
                # Limpa a tela
                screen.blit(background, (0, 0))
                
                # Desenha as plataformas
                initial_platform = env.initial_platform
                landing_platform = env.landing_platform
                
                initial_platform_rect = pygame.Rect(
                    initial_platform.posicao[0], 
                    game.config.HEIGHT - 10, 
                    initial_platform.comprimento, 
                    10
                )
                pygame.draw.rect(screen, (100, 100, 100), initial_platform_rect)
                
                landing_platform_rect = pygame.Rect(
                    landing_platform.posicao[0], 
                    game.config.HEIGHT - 10, 
                    landing_platform.comprimento, 
                    10
                )
                pygame.draw.rect(screen, (100, 100, 100), landing_platform_rect)

                # Desenha o target (se não foi atingido)
                target = env.target
                if not env.foguete.target_reached:
                    pygame.draw.circle(
                        screen,
                        (255, 0, 0),
                        (int(target.posicao[0]), game.config.HEIGHT - int(target.posicao[1])),
                        int(target.altura / 2),
                        4
                    )

                # Desenha o foguete (se não crashou)
                foguete = env.foguete
                if not foguete.crashed:
                    rocket_width, rocket_height = 20, 40
                    
                    # Cria a superfície do foguete
                    rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
                    rocket_surf.fill((0, 0, 0, 0))  # Transparente
                    
                    # Desenha o corpo do foguete
                    body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
                    pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
                    pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
                    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
                    pygame.draw.polygon(rocket_surf, (150, 150, 150), [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), (rocket_width, rocket_height - 10)])
                    
                    # Rotaciona e desenha
                    rotated_surf = pygame.transform.rotate(rocket_surf, (foguete.orientacao - 90))
                    rotated_rect = rotated_surf.get_rect(center=(int(foguete.posicao[0]), game.config.HEIGHT - int(foguete.posicao[1])))
                    screen.blit(rotated_surf, rotated_rect.topleft)
                
                # Adiciona informações do agente na tela
                info_text = [
                    f"Episódio: {episode+1}/{num_episodes}",
                    f"Passo: {steps}",
                    f"Recompensa: {episode_reward:.1f}",
                    f"Ação: {action}",
                    f"Combustível: {100-foguete.fuel_consumed:.1f}%",
                    f"Velocidade: ({foguete.velocidade[0]:.1f}, {foguete.velocidade[1]:.1f})",
                    f"Target: {'Atingido' if foguete.target_reached else 'Não atingido'}",
                    f"Orientação: {foguete.orientacao:.1f}°"
                ]
                
                # Renderiza informações do agente
                for i, text in enumerate(info_text):
                    text_surface = font.render(text, True, (255, 255, 255))
                    text_rect = pygame.Rect(10, 10 + i * 25, 400, 25)
                    pygame.draw.rect(screen, (0, 0, 0), text_rect)
                    screen.blit(text_surface, (12, 12 + i * 25))
                
                # Status do episódio
                if foguete.landed:
                    if foguete.target_reached:
                        status_text = "POUSO BEM SUCEDIDO!"
                        color = (0, 255, 0)
                    else:
                        status_text = "POUSOU SEM O TARGET"
                        color = (255, 255, 0)
                    
                    big_font = pygame.font.Font(None, 48)
                    text_surface = big_font.render(status_text, True, color)
                    text_rect = text_surface.get_rect(center=(game.config.WIDTH/2, game.config.HEIGHT/2))
                    screen.blit(text_surface, text_rect)
                    
                elif foguete.crashed:
                    status_text = "CRASH!"
                    color = (255, 0, 0)
                    big_font = pygame.font.Font(None, 48)
                    text_surface = big_font.render(status_text, True, color)
                    text_rect = text_surface.get_rect(center=(game.config.WIDTH/2, game.config.HEIGHT/2))
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
            big_font = pygame.font.Font(None, 48)
            waiting_text = big_font.render("Próximo episódio...", True, (255, 255, 255))
            waiting_rect = waiting_text.get_rect(center=(game.config.WIDTH/2, game.config.HEIGHT-50))
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
