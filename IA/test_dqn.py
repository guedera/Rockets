import time
import pygame
from stable_baselines3 import DQN
from rocket_env import RocketEnv
import numpy as np
import argparse
import os
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

def parse_args():
    parser = argparse.ArgumentParser(description='Test trained DQN agent on Rocket landing task')
    parser.add_argument('--model', type=str, default='models/final_model', help='Path to the model file')
    parser.add_argument('--normalize', type=str, default='models/vec_normalize.pkl', help='Path to normalization parameters')
    parser.add_argument('--episodes', type=int, default=5, help='Number of episodes to run')
    parser.add_argument('--render', action='store_true', help='Render the environment')
    parser.add_argument('--save-video', action='store_true', help='Save video of the episodes')
    return parser.parse_args()

def make_env(render_mode=None):
    return RocketEnv(render_mode=render_mode, headless=False)

def test_model(model_path, vec_normalize_path, num_episodes=5, render=True, save_video=False):
    # Create environment
    env = make_env(render_mode='human' if render else None)
    
    # Load normalization parameters if available
    if os.path.exists(vec_normalize_path):
        print(f"Loading normalization parameters from {vec_normalize_path}")
        env = DummyVecEnv([lambda: env])
        env = VecNormalize.load(vec_normalize_path, env)
        # Don't update normalization stats during testing
        env.training = False
        env.norm_reward = False
    
    # Load the trained model
    print(f"Loading model from {model_path}")
    model = DQN.load(model_path)
    
    results = []
    for episode in range(num_episodes):
        print(f"Episode {episode+1}/{num_episodes}")
        obs, _ = env.reset()
        done = False
        total_reward = 0
        step = 0
        
        frames = []
        
        while not done:
            # Get action from model
            if isinstance(env, VecNormalize):
                action, _ = model.predict(obs, deterministic=True)
            else:
                action, _ = model.predict(obs, deterministic=True)
            
            # Take action in environment
            obs, reward, terminated, truncated, info = env.step(action if isinstance(env, VecNormalize) else action[0])
            done = terminated or truncated
            total_reward += reward if not isinstance(env, VecNormalize) else reward[0]
            step += 1
            
            # Capture frame if saving video
            if save_video and render:
                frame = pygame.surfarray.array3d(env.render())
                frames.append(frame)
            
            # Slight delay for visualization
            if render:
                time.sleep(0.01)
        
        # Print episode results
        print(f"Episode {episode+1} finished after {step} steps")
        print(f"Total reward: {total_reward}")
        if isinstance(env, VecNormalize):
            info = info[0]
        print(f"Fuel consumed: {info['fuel_consumed']}")
        print(f"Target reached: {info['target_reached']}")
        print(f"Landed successfully: {info['landed']}")
        print(f"Crashed: {info['crashed']}")
        print(f"Simulation time: {info['simulation_time']:.2f} seconds")
        print("-" * 40)
        
        results.append({
            'reward': total_reward,
            'steps': step,
            'fuel_consumed': info['fuel_consumed'],
            'target_reached': info['target_reached'],
            'landed': info['landed'],
            'crashed': info['crashed'],
            'time': info['simulation_time']
        })
        
        # Save video if requested
        if save_video and render and len(frames) > 0:
            try:
                import cv2
                import numpy as np
                
                video_path = f"rocket_episode_{episode}.mp4"
                print(f"Saving video to {video_path}")
                
                # Get video dimensions from the first frame
                height, width, layers = frames[0].shape
                
                # Define the codec and create VideoWriter object
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video = cv2.VideoWriter(video_path, fourcc, 30, (width, height))
                
                for frame in frames:
                    # OpenCV uses BGR, pygame uses RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    video.write(frame)
                
                video.release()
                print(f"Video saved to {video_path}")
            except Exception as e:
                print(f"Error saving video: {e}")
    
    # Print summary
    print("\n===== SUMMARY =====")
    success_rate = sum(r['landed'] for r in results) / len(results) * 100
    print(f"Success rate: {success_rate:.1f}%")
    avg_fuel = sum(r['fuel_consumed'] for r in results) / len(results)
    print(f"Average fuel consumed: {avg_fuel:.2f}")
    target_rate = sum(r['target_reached'] for r in results) / len(results) * 100
    print(f"Target reached rate: {target_rate:.1f}%")
    
    if isinstance(env, VecNormalize):
        env.close()
    else:
        env.close()
    
if __name__ == "__main__":
    args = parse_args()
    test_model(args.model, args.normalize, args.episodes, args.render, args.save_video)
