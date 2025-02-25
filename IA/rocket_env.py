import gym
import numpy as np
from gym import spaces
from stable_baselines3 import DQN

class RocketEnv(gym.Env):
    def __init__(self):
        super(RocketEnv, self).__init__()
        # Exemplo: Estado composto por [pos_x, pos_y, vel_x, vel_y, orientação, angular_velocity, potência]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32)
        # Ações discretas: 0: nenhuma ação, 1: aumentar potência, 2: diminuir potência, 3: girar esquerda, 4: girar direita
        self.action_space = spaces.Discrete(5)
        self.reset()

    def reset(self):
        # Reinicialize seu foguete
        self.foguete = Rocket(rocket_initial_x, rocket_initial_y, massa=50)
        # Retorne o estado inicial
        return self._get_obs()

    def _get_obs(self):
        # Construa o vetor de observação com base no estado do foguete
        return np.array([
            self.foguete.posicao[0],
            self.foguete.posicao[1],
            self.foguete.velocidade[0],
            self.foguete.velocidade[1],
            self.foguete.orientacao,
            self.foguete.angular_velocity,
            self.foguete.potencia_motor
        ], dtype=np.float32)

    def step(self, action):
        # Mapeie a ação para uma alteração no estado
        if action == 1:
            self.foguete.alterar_potencia(Rocket.POTENCIA_INCREMENTO)
        elif action == 2:
            self.foguete.alterar_potencia(-Rocket.POTENCIA_INCREMENTO)
        elif action == 3:
            self.foguete.aplicar_torque(+Rocket.ROTATION_TORQUE, delta_time)
        elif action == 4:
            self.foguete.aplicar_torque(-Rocket.ROTATION_TORQUE, delta_time)
        # Atualize o foguete (não esqueça de definir o delta_time)
        delta_time = 1 / 60.0
        self.foguete.atualizar(delta_time)
        
        # Calcule a recompensa
        reward = - 0.1  # penalidade por passo (para incentivar soluções rápidas)
        done = False
        
        # Se pousou com sucesso
        if pousou_com_sucesso():
            reward += 100
            done = True
        # Se crashou
        elif crashou():
            reward -= 100
            done = True

        return self._get_obs(), reward, done, {}

# Crie e treine o agente:
env = RocketEnv()
model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100000)
