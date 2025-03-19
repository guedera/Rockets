import os
import sys
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import math
import time
import random

# Add the game directory to the path so we can import the game modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game.src.entities.rocket import Rocket
from game.src.entities.platform import Platform
from game.src.entities.target import Target
import game.config as config

class RocketEnv(gym.Env):
    """Custom Environment for the rocket landing task that follows gym interface"""
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': config.FPS}

    def __init__(self, render_mode=None, headless=True):
        super(RocketEnv, self).__init__()
        
        # If headless, we set the SDL_VIDEODRIVER to dummy
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            
        # Initialize pygame
        pygame.init()
        
        # Environment dimensions
        self.width = config.WIDTH
        self.height = config.HEIGHT
        self.fps = config.FPS
        self.pixels_per_meter = config.PIXELS_PER_METER
        
        # Action space: [thrust adjustment (-1, 0, 1), rotation torque (-1, 0, 1)]
        self.action_space = spaces.Discrete(9)  # 3x3 combinations
        
        # Observation space: [x, y, orientation, vx, vy, angular_velocity, potencia_motor, 
        #                   target_reached, distance_to_target, angle_difference,
        #                   distance_to_landing_platform_x, distance_to_landing_platform_y]
        self.observation_space = spaces.Box(
            low=np.array([-float('inf')] * 12),
            high=np.array([float('inf')] * 12),
            dtype=np.float32
        )
        
        # Set up rendering
        self.render_mode = render_mode
        if self.render_mode == 'human':
            pygame.display.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Rocket DQN Training")
        else:
            self.screen = pygame.Surface((self.width, self.height))
            
        # Load background
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill((0, 0, 0))
        
        # Clock
        self.clock = pygame.time.Clock()
        
        # Create game objects
        self._create_game_objects()
        
        # Additional variables for scoring
        self.max_simulation_time = 30.0  # seconds
        self.current_time = 0.0
        self.last_distance = float('inf')
        
    def _create_game_objects(self):
        # Platforms
        self.initial_platform = Platform(posicao_x=100, comprimento=200, altura=0)
        self.landing_platform = Platform(posicao_x=self.width - 200 - 100, comprimento=200, altura=0)
        
        # Rocket
        rocket_width, rocket_height = 20, 40
        rocket_initial_x = self.initial_platform.posicao[0] + self.initial_platform.comprimento / 2
        rocket_initial_y = rocket_height / 2
        self.foguete = Rocket(posicao_x=rocket_initial_x, posicao_y=rocket_initial_y, massa=50)
        
        # Target
        TARGET_DIAMETER = 30
        self.target = Target(
            5 * self.pixels_per_meter,
            5 * self.pixels_per_meter,
            TARGET_DIAMETER,
            TARGET_DIAMETER
        )
        
    def _get_obs(self):
        # Create the observation vector
        state = self.foguete.get_state()
        
        # Normalize the values
        # Convert from pixel coordinates to meters for some values
        pos_x = self.foguete.posicao[0] / self.pixels_per_meter
        pos_y = self.foguete.posicao[1] / self.pixels_per_meter
        vel_x = self.foguete.velocidade[0] / self.pixels_per_meter
        vel_y = self.foguete.velocidade[1] / self.pixels_per_meter
        
        # Normalize orientation to [-180, 180] range
        orientation = ((self.foguete.orientacao % 360) + 180) % 360 - 180
        
        # Pack all observations
        observation = np.array([
            pos_x,
            pos_y,
            orientation,
            vel_x,
            vel_y,
            self.foguete.angular_velocity,
            self.foguete.potencia_motor / 100.0,  # normalize to [0, 1]
            1.0 if self.foguete.target_reached else 0.0,
            state['distance_to_target'] / self.pixels_per_meter if state['distance_to_target'] is not None else 0.0,
            state['angle_difference'] / 180.0 if state['angle_difference'] is not None else 0.0,  # normalize to [-1, 1]
            state['distance_to_landing_platform_x'] / self.pixels_per_meter if state['distance_to_landing_platform_x'] is not None else 0.0,
            state['distance_to_landing_platform_y'] / self.pixels_per_meter if state['distance_to_landing_platform_y'] is not None else 0.0
        ], dtype=np.float32)
        
        return observation
    
    def _get_info(self):
        return {
            "fuel_consumed": self.foguete.fuel_consumed,
            "target_reached": self.foguete.target_reached,
            "landed": self.foguete.landed,
            "crashed": self.foguete.crashed,
            "simulation_time": self.current_time
        }
    
    def _decode_action(self, action):
        """Decode action index into thrust and torque adjustments.
        
        Actions:
        0: No thrust change, no torque
        1: No thrust change, CCW torque
        2: No thrust change, CW torque
        3: Increase thrust, no torque
        4: Increase thrust, CCW torque
        5: Increase thrust, CW torque
        6: Decrease thrust, no torque
        7: Decrease thrust, CCW torque
        8: Decrease thrust, CW torque
        """
        # Decode action
        thrust_action = (action // 3) - 1  # -1, 0, 1
        torque_action = (action % 3) - 1   # -1, 0, 1
        
        return thrust_action, torque_action
        
    def step(self, action):
        # Decode action
        thrust_action, torque_action = self._decode_action(action)
        
        # Apply action
        thrust_adjustment = self.foguete.POTENCIA_INCREMENTO * thrust_action
        self.foguete.alterar_potencia(thrust_adjustment)
        
        if torque_action != 0:
            torque = self.foguete.ROTATION_TORQUE * torque_action
            self.foguete.aplicar_torque(torque, 1.0 / self.fps)
        
        # Update simulation
        dt = 1.0 / self.fps
        self.foguete.atualizar(dt)
        self.foguete.compute_metrics(self.target, self.landing_platform)
        self.current_time += dt
        
        # Check if the rocket caught the target
        if not self.foguete.target_reached:
            dx = self.foguete.posicao[0] - self.target.posicao[0]
            dy = self.foguete.posicao[1] - self.target.posicao[1]
            if math.sqrt(dx**2 + dy**2) <= self.target.altura / 2:
                self.foguete.target_reached = True
        
        # Check landing and crash conditions
        rocket_half_height = 20  # From game main.py
        if self.foguete.posicao[1] <= rocket_half_height and self.foguete.velocidade[1] <= 0:
            landing_speed = math.sqrt(self.foguete.velocidade[0]**2 + self.foguete.velocidade[1]**2)
            on_initial = (self.initial_platform.posicao[0] <= self.foguete.posicao[0] <= 
                         self.initial_platform.posicao[0] + self.initial_platform.comprimento)
            on_landing = (self.landing_platform.posicao[0] <= self.foguete.posicao[0] <= 
                         self.landing_platform.posicao[0] + self.landing_platform.comprimento)
            
            if landing_speed > config.LANDING_SPEED_THRESHOLD:
                self.foguete.crashed = True
            else:
                if on_initial or on_landing:
                    self.foguete.posicao[1] = rocket_half_height
                    if self.foguete.potencia_motor == 0:
                        self.foguete.velocidade = [0, 0]
                        self.foguete.angular_velocity = 0
                    else:
                        self.foguete.velocidade[1] = 0
                        self.foguete.angular_velocity = 0
                    if on_landing and self.foguete.target_reached:
                        self.foguete.landed = True
                else:
                    self.foguete.crashed = True
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if episode is done
        terminated = (self.foguete.landed or self.foguete.crashed or 
                      self.current_time >= self.max_simulation_time or 
                      self.foguete.posicao[1] < 0 or 
                      self.foguete.posicao[0] < 0 or 
                      self.foguete.posicao[0] > self.width or 
                      self.foguete.posicao[1] > self.height)
        
        truncated = False
        
        # Get observation and info
        observation = self._get_obs()
        info = self._get_info()
        
        # Save current distance for next reward calculation
        self.last_distance = self.foguete.distance_to_target if self.foguete.distance_to_target is not None else float('inf')
        
        if self.render_mode == "human":
            self.render()
            
        return observation, reward, terminated, truncated, info
    
    def _calculate_reward(self):
        """Calculate the reward based on the current state of the rocket."""
        reward = 0
        
        # Base rewards/penalties
        if self.foguete.landed:
            reward += 500  # Big reward for successful landing
        elif self.foguete.crashed:
            reward -= 100  # Big penalty for crashing
        
        # Reward for reaching target
        if self.foguete.target_reached:
            reward += 200  # One-time reward for reaching target
        
        # Reward for getting closer to target if not reached yet
        if not self.foguete.target_reached and self.foguete.distance_to_target is not None:
            current_distance = self.foguete.distance_to_target
            # Reward for reducing distance to target
            if current_distance < self.last_distance:
                reward += 0.5
        
        # Reward for getting closer to landing platform if target is reached
        if self.foguete.target_reached and not self.foguete.landed:
            # Encourage getting closer to landing platform in x-axis
            if self.foguete.distance_to_landing_platform_x is not None:
                reward += max(0, 0.2 - self.foguete.distance_to_landing_platform_x / self.pixels_per_meter)
            
        # Small penalty for fuel consumption to encourage efficiency
        reward -= self.foguete.potencia_motor / 2000.0  # Small penalty proportional to engine power
        
        # Small penalty for excessive orientation change
        if abs(self.foguete.angular_velocity) > 10:
            reward -= 0.05
        
        # Penalty for bad orientation during landing approach
        if self.foguete.target_reached and self.foguete.posicao[1] < 100:
            # If close to ground, penalize non-vertical orientation
            if abs(self.foguete.orientacao - 90) > 30:
                reward -= 0.2
                
        return reward
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._create_game_objects()
        self.current_time = 0.0
        self.last_distance = float('inf')
        
        observation = self._get_obs()
        info = self._get_info()
        
        return observation, info
    
    def render(self):
        if self.render_mode is None:
            return
            
        self.screen.fill((0, 0, 0))
        
        # Draw platforms
        initial_platform_rect = pygame.Rect(self.initial_platform.posicao[0], 
                                            self.height - 10, 
                                            self.initial_platform.comprimento, 10)
        pygame.draw.rect(self.screen, (100, 100, 100), initial_platform_rect)
        
        landing_platform_rect = pygame.Rect(self.landing_platform.posicao[0], 
                                            self.height - 10, 
                                            self.landing_platform.comprimento, 10)
        pygame.draw.rect(self.screen, (100, 100, 100), landing_platform_rect)
        
        # Draw target if not reached
        if not self.foguete.target_reached:
            pygame.draw.circle(
                self.screen,
                (255, 0, 0),
                (int(self.target.posicao[0]), self.height - int(self.target.posicao[1])),
                int(self.target.altura / 2),
                4
            )
        
        # Draw rocket
        if not self.foguete.crashed:
            rocket_width, rocket_height = 20, 40
            rocket_surf = pygame.Surface((rocket_width, rocket_height), pygame.SRCALPHA)
            body_rect = pygame.Rect(0, 10, rocket_width, rocket_height - 10)
            pygame.draw.rect(rocket_surf, (200, 0, 0), body_rect)
            pygame.draw.polygon(rocket_surf, (255, 0, 0), [(0, 10), (rocket_width, 10), (rocket_width/2, 0)])
            pygame.draw.polygon(rocket_surf, (150, 150, 150), 
                               [(0, rocket_height), (5, rocket_height - 10), (0, rocket_height - 10)])
            pygame.draw.polygon(rocket_surf, (150, 150, 150), 
                               [(rocket_width, rocket_height), (rocket_width - 5, rocket_height - 10), 
                                (rocket_width, rocket_height - 10)])
            rotated_surf = pygame.transform.rotate(rocket_surf, (self.foguete.orientacao - 90))
            rotated_rect = rotated_surf.get_rect(center=(int(self.foguete.posicao[0]), 
                                                         self.height - int(self.foguete.posicao[1])))
            self.screen.blit(rotated_surf, rotated_rect.topleft)
        else:
            # Draw crashed text
            font = pygame.font.SysFont('Arial', 48)
            crash_text = font.render("Crash!", True, (255, 0, 0))
            crash_rect = crash_text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(crash_text, crash_rect)
        
        # Display status info
        font = pygame.font.SysFont('Arial', 18)
        status_text = f"Time: {self.current_time:.1f}s | Fuel: {self.foguete.fuel_consumed:.2f} | Target: {'Yes' if self.foguete.target_reached else 'No'}"
        status_surface = font.render(status_text, True, (255, 255, 255))
        self.screen.blit(status_surface, (10, 10))
        
        if self.foguete.landed:
            landed_text = font.render("LANDED SUCCESSFULLY!", True, (0, 255, 0))
            self.screen.blit(landed_text, (self.width // 2 - landed_text.get_width() // 2, 50))
        
        if self.render_mode == "human":
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        return self.screen
        
    def close(self):
        if self.render_mode == "human":
            pygame.display.quit()
            pygame.quit()