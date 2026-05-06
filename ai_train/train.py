"""
AlphaZero 风格的自我对弈训练
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import json
import time
from collections import deque
from model import GomokuNet, GomokuEnv
from mcts import MCTSPlayer


class TrainingPipeline:
    """训练流水线"""
    
    def __init__(self, board_size=13, 
                 num_res_blocks=5, channels=64,
                 lr=0.001, weight_decay=1e-4,
                 batch_size=512, buffer_size=100000,
                 n_simulations=400, c_puct=5.0,
                 temperature_threshold=10,
                 save_dir="./checkpoints"):
        
        self.board_size = board_size
        self.save_dir = save_dir
        self.temperature_threshold = temperature_threshold
        
        # 创建模型
        self.net = GomokuNet(board_size, num_res_blocks, channels)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net.to(self.device)
        
        print(f"使用设备: {self.device}")
        print(f"模型参数量: {sum(p.numel() for p in self.net.parameters()):,}")
        
        # 优化器
        self.optimizer = optim.Adam(self.net.parameters(), 
                                    lr=lr, 
                                    weight_decay=weight_decay)
        
        # 学习率调度器
        self.scheduler = optim.lr_scheduler.MultiStepLR(
            self.optimizer, milestones=[100, 200, 300], gamma=0.1)
        
        # 经验回放缓冲区
        self.buffer = deque(maxlen=buffer_size)
        self.batch_size = batch_size
        
        # MCTS 配置
        self.n_simulations = n_simulations
        self.c_puct = c_puct
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
    
    def policy_value_fn(self, state):
        """策略价值函数（用于 MCTS）"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        self.net.eval()
        with torch.no_grad():
            log_policy, value = self.net(state_tensor)
            policy = torch.exp(log_policy).cpu().numpy()[0]
        return policy, value.item()
    
    def self_play(self, game_idx):
        """
        自我对弈一局
        返回: [(state, mcts_probs, winner), ...]
        """
        env = GomokuEnv(self.board_size)
        player = MCTSPlayer(self.policy_value_fn, 
                           self.c_puct, 
                           self.n_simulations, 
                           is_selfplay=True)
        
        states, mcts_probs, current_players = [], [], []
        
        move_count = 0
        while not env.game_over:
            # 设置温度
            temperature = 1.0 if move_count < self.temperature_threshold else 0.1
            
            # 获取动作和概率
            action, action_probs = player.get_action(env, temperature, return_prob=True)
            
            # 保存数据
            states.append(env.get_state())
            mcts_probs.append(action_probs)
            current_players.append(env.current_player)
            
            # 执行动作
            env.step(action)
            move_count += 1
        
        # 计算奖励
        winner = env.winner
        rewards = []
        for player in current_players:
            if winner == 0:
                rewards.append(0.0)
            else:
                rewards.append(1.0 if winner == player else -1.0)
        
        # 打印结果
        result = "平局" if winner == 0 else ("黑棋胜" if winner == 1 else "白棋胜")
        print(f"  游戏 {game_idx}: {move_count} 步, 结果: {result}")
        
        return list(zip(states, mcts_probs, rewards))
    
    def train_step(self):
        """一步训练"""
        if len(self.buffer) < self.batch_size:
            return None
        
        # 采样
        mini_batch = np.random.choice(len(self.buffer), self.batch_size, replace=False)
        batch = [self.buffer[i] for i in mini_batch]
        
        states = torch.FloatTensor(np.array([x[0] for x in batch])).to(self.device)
        mcts_probs = torch.FloatTensor(np.array([x[1] for x in batch])).to(self.device)
        rewards = torch.FloatTensor(np.array([x[2] for x in batch])).unsqueeze(1).to(self.device)
        
        self.net.train()
        
        # 前向传播
        log_policy, value = self.net(states)
        
        # 计算损失
        # 策略损失：交叉熵
        policy_loss = -torch.mean(torch.sum(mcts_probs * log_policy, dim=1))
        # 价值损失：MSE
        value_loss = nn.MSELoss()(value, rewards)
        # 总损失
        total_loss = policy_loss + value_loss
        
        # 反向传播
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'total_loss': total_loss.item()
        }
    
    def evaluate(self, n_games=10):
        """评估当前模型"""
        print("\n评估模型...")
        
        # 创建纯 MCTS 玩家（不使用神经网络）
        def random_policy(state):
            return np.ones(self.board_size ** 2) / (self.board_size ** 2), 0.0
        
        wins = 0
        for i in range(n_games):
            env = GomokuEnv(self.board_size)
            
            # 当前模型作为黑棋
            player = MCTSPlayer(self.policy_value_fn, 
                               self.c_puct, 
                               self.n_simulations // 2)
            
            while not env.game_over:
                if env.current_player == 1:
                    action = player.get_action(env, temperature=0)
                else:
                    legal_moves = env.get_legal_moves()
                    action = np.random.randint(len(legal_moves))
                    action = legal_moves[action][0] * self.board_size + legal_moves[action][1]
                
                env.step(action)
            
            if env.winner == 1:
                wins += 1
        
        win_rate = wins / n_games
        print(f"  胜率: {win_rate:.2%}")
        return win_rate
    
    def save_checkpoint(self, epoch, win_rate):
        """保存检查点"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'win_rate': win_rate,
        }
        path = os.path.join(self.save_dir, f"model_epoch_{epoch}.pt")
        torch.save(checkpoint, path)
        print(f"  模型已保存: {path}")
        
        # 同时保存最佳模型
        best_path = os.path.join(self.save_dir, "best_model.pt")
        torch.save(checkpoint, best_path)
    
    def load_checkpoint(self, path):
        """加载检查点"""
        checkpoint = torch.load(path, map_location=self.device)
        self.net.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"模型已加载: {path}")
        return checkpoint.get('epoch', 0), checkpoint.get('win_rate', 0)
    
    def train(self, n_epochs=100, games_per_epoch=100, 
              train_steps_per_epoch=500, eval_games=20):
        """
        训练主循环
        n_epochs: 训练轮数
        games_per_epoch: 每轮自我对弈游戏数
        train_steps_per_epoch: 每轮训练步数
        eval_games: 评估游戏数
        """
        print(f"\n开始训练...")
        print(f"  训练轮数: {n_epochs}")
        print(f"  每轮游戏数: {games_per_epoch}")
        print(f"  每轮训练步数: {train_steps_per_epoch}")
        
        best_win_rate = 0.0
        
        for epoch in range(1, n_epochs + 1):
            print(f"\n{'='*50}")
            print(f"Epoch {epoch}/{n_epochs}")
            print(f"{'='*50}")
            
            # 自我对弈
            print(f"\n自我对弈 ({games_per_epoch} 局)...")
            for i in range(games_per_epoch):
                game_data = self.self_play(i + 1)
                self.buffer.extend(game_data)
            
            print(f"  缓冲区大小: {len(self.buffer)}")
            
            # 训练
            print(f"\n训练 ({train_steps_per_epoch} 步)...")
            losses = {'policy_loss': [], 'value_loss': [], 'total_loss': []}
            
            for step in range(train_steps_per_epoch):
                loss_dict = self.train_step()
                if loss_dict:
                    for k, v in loss_dict.items():
                        losses[k].append(v)
                
                if (step + 1) % 100 == 0:
                    print(f"  步骤 {step+1}/{train_steps_per_epoch}, "
                          f"Loss: {np.mean(losses['total_loss']):.4f}")
            
            # 更新学习率
            self.scheduler.step()
            current_lr = self.optimizer.param_groups[0]['lr']
            print(f"\n当前学习率: {current_lr}")
            
            # 评估
            win_rate = self.evaluate(eval_games)
            
            # 保存模型
            self.save_checkpoint(epoch, win_rate)
            
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                print(f"  新的最佳胜率: {best_win_rate:.2%}")
            
            # 保存训练日志
            log = {
                'epoch': epoch,
                'policy_loss': np.mean(losses['policy_loss']),
                'value_loss': np.mean(losses['value_loss']),
                'total_loss': np.mean(losses['total_loss']),
                'win_rate': win_rate,
                'buffer_size': len(self.buffer),
                'lr': current_lr
            }
            with open(os.path.join(self.save_dir, 'training_log.json'), 'a') as f:
                f.write(json.dumps(log) + '\n')
        
        print("\n训练完成！")


def main():
    # 创建训练流水线
    pipeline = TrainingPipeline(
        board_size=13,
        num_res_blocks=5,
        channels=64,
        lr=0.001,
        batch_size=512,
        buffer_size=100000,
        n_simulations=400,
        save_dir="./checkpoints"
    )
    
    # 开始训练
    pipeline.train(
        n_epochs=100,
        games_per_epoch=100,
        train_steps_per_epoch=500,
        eval_games=20
    )


if __name__ == "__main__":
    main()
