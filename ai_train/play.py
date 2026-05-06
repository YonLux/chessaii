"""
训练好的模型与人对战接口
可以加载训练好的模型，与现有 C++ 代码对接
"""

import torch
import numpy as np
import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model import GomokuNet, GomokuEnv
from mcts import MCTSPlayer


class TrainedAI:
    """训练好的 AI，可与 C++ 代码对接"""
    
    def __init__(self, model_path, board_size=13, n_simulations=200):
        self.board_size = board_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载模型
        self.net = GomokuNet(board_size)
        checkpoint = torch.load(model_path, map_location=self.device)
        self.net.load_state_dict(checkpoint['model_state_dict'])
        self.net.to(self.device)
        self.net.eval()
        
        print(f"模型已加载: {model_path}")
        print(f"设备: {self.device}")
        if 'win_rate' in checkpoint:
            print(f"训练胜率: {checkpoint['win_rate']:.2%}")
        
        # 创建 MCTS 玩家
        self.player = MCTSPlayer(
            self.policy_value_fn,
            c_puct=5.0,
            n_simulations=n_simulations
        )
        
        # 当前棋盘状态
        self.board = np.zeros((board_size, board_size), dtype=np.int8)
        self.current_player = 1  # 1: 黑棋(人), -1: 白棋(AI)
    
    def policy_value_fn(self, state):
        """策略价值函数"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            log_policy, value = self.net(state_tensor)
            policy = torch.exp(log_policy).cpu().numpy()[0]
        return policy, value.item()
    
    def update_opponent_move(self, row, col):
        """
        更新对手落子
        从 C++ 代码调用
        """
        self.board[row, col] = self.current_player
        self.current_player = -self.current_player
        
        # 更新 MCTS 树
        action = row * self.board_size + col
        self.player.mcts.update_with_move(action)
    
    def get_ai_move(self):
        """
        获取 AI 落子
        返回: (row, col)
        """
        # 构建当前状态
        env = GomokuEnv(self.board_size)
        env.board = self.board.copy()
        env.current_player = self.current_player
        
        # 获取动作
        action = self.player.get_action(env, temperature=0)
        row = action // self.board_size
        col = action % self.board_size
        
        # 更新内部状态
        self.board[row, col] = self.current_player
        self.current_player = -self.current_player
        
        # 更新 MCTS 树
        self.player.mcts.update_with_move(action)
        
        return row, col
    
    def reset(self):
        """重置游戏"""
        self.board = np.zeros((self.board_size, self.board_size), dtype=np.int8)
        self.current_player = 1
        self.player.reset()
    
    def print_board(self):
        """打印棋盘"""
        symbols = {0: '.', 1: 'X', -1: 'O'}
        print('  ' + ' '.join(str(i % 10) for i in range(self.board_size)))
        for i, row in enumerate(self.board):
            print(f"{i:2d} " + ' '.join(symbols[x] for x in row))
        print()


def play_against_ai(model_path, board_size=13):
    """与 AI 对战"""
    ai = TrainedAI(model_path, board_size)
    
    print("\n五子棋对战")
    print("你执黑棋 (X)，AI 执白棋 (O)")
    print("输入格式: 行 列 (例如: 6 6)")
    print("输入 'q' 退出\n")
    
    ai.print_board()
    
    while True:
        # 玩家回合
        while True:
            try:
                user_input = input("你的落子 (行 列): ").strip()
                if user_input.lower() == 'q':
                    print("游戏结束")
                    return
                
                row, col = map(int, user_input.split())
                if 0 <= row < board_size and 0 <= col < board_size:
                    if ai.board[row, col] == 0:
                        break
                    else:
                        print("该位置已有棋子，请重新输入")
                else:
                    print(f"坐标超出范围，请输入 0-{board_size-1} 之间的数字")
            except ValueError:
                print("输入格式错误，请输入: 行 列")
        
        # 更新玩家落子
        ai.update_opponent_move(row, col)
        ai.print_board()
        
        # 检查胜负
        if check_win(ai.board, row, col, 1):
            print("恭喜你赢了！")
            break
        
        if np.all(ai.board != 0):
            print("平局！")
            break
        
        # AI 回合
        print("AI 思考中...")
        ai_row, ai_col = ai.get_ai_move()
        print(f"AI 落子: {ai_row} {ai_col}")
        ai.print_board()
        
        # 检查胜负
        if check_win(ai.board, ai_row, ai_col, -1):
            print("AI 获胜！")
            break
        
        if np.all(ai.board != 0):
            print("平局！")
            break


def check_win(board, row, col, player):
    """检查是否获胜"""
    board_size = board.shape[0]
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dr, dc in directions:
        count = 1
        # 正向
        r, c = row + dr, col + dc
        while 0 <= r < board_size and 0 <= c < board_size and board[r, c] == player:
            count += 1
            r += dr
            c += dc
        # 反向
        r, c = row - dr, col - dc
        while 0 <= r < board_size and 0 <= c < board_size and board[r, c] == player:
            count += 1
            r -= dr
            c -= dc
        
        if count >= 5:
            return True
    return False


def export_for_cpp(model_path, output_path="model_weights.json"):
    """导出模型权重供 C++ 使用"""
    net = GomokuNet(13)
    checkpoint = torch.load(model_path, map_location='cpu')
    net.load_state_dict(checkpoint['model_state_dict'])
    
    weights = {}
    for name, param in net.named_parameters():
        weights[name] = param.numpy().tolist()
    
    with open(output_path, 'w') as f:
        json.dump(weights, f)
    
    print(f"权重已导出到: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="五子棋 AI")
    parser.add_argument('--model', type=str, default="checkpoints/best_model.pt",
                        help='模型路径')
    parser.add_argument('--board_size', type=int, default=13,
                        help='棋盘大小')
    parser.add_argument('--export', type=str, default=None,
                        help='导出模型权重到 JSON 文件')
    
    args = parser.parse_args()
    
    if args.export:
        export_for_cpp(args.model, args.export)
    else:
        play_against_ai(args.model, args.board_size)
