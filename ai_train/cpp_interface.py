"""
C++ 接口模块
提供与现有 C++ 代码对接的方法
"""

import torch
import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model import GomokuNet


class AIInterface:
    """
    AI 接口类
    用于与 C++ 代码通过文件或管道通信
    """
    
    def __init__(self, model_path, board_size=13):
        self.board_size = board_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.net = GomokuNet(board_size)
        checkpoint = torch.load(model_path, map_location=self.device)
        self.net.load_state_dict(checkpoint['model_state_dict'])
        self.net.to(self.device)
        self.net.eval()
        
        self.board = np.zeros((board_size, board_size), dtype=np.int8)
    
    def get_state_from_chess_map(self, chess_map):
        """
        从 chessMap 获取状态
        chess_map: 二维数组，0=空，1=黑棋，-1=白棋
        返回: 神经网络输入状态 (4通道)
        """
        chess_map = np.array(chess_map)
        
        # 假设当前是白棋回合（AI）
        current_player = -1
        
        state = np.zeros((4, self.board_size, self.board_size), dtype=np.float32)
        state[0] = (chess_map == current_player).astype(np.float32)
        state[1] = (chess_map == -current_player).astype(np.float32)
        state[3] = np.zeros((self.board_size, self.board_size), dtype=np.float32)
        
        return state
    
    def get_move_from_chess_map(self, chess_map):
        """
        从 chessMap 获取 AI 落子位置
        返回: (row, col)
        """
        state = self.get_state_from_chess_map(chess_map)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            log_policy, value = self.net(state_tensor)
            policy = torch.exp(log_policy).cpu().numpy()[0]
        
        # 屏蔽非法落子
        legal_mask = np.array(chess_map).flatten() == 0
        policy = policy * legal_mask
        if policy.sum() > 0:
            policy = policy / policy.sum()
        else:
            # 如果没有合法落子，随机选择
            policy = legal_mask.astype(np.float32) / legal_mask.sum()
        
        # 选择最佳落子
        action = np.argmax(policy)
        row = action // self.board_size
        col = action % self.board_size
        
        return int(row), int(col), float(value.item())


def file_based_communication(model_path, input_file="ai_input.json", output_file="ai_output.json"):
    """
    基于文件的通信方式
    C++ 写入 chessMap 到 ai_input.json
    Python 读取并计算，结果写入 ai_output.json
    """
    ai = AIInterface(model_path)
    
    print("AI 接口已启动，等待输入...")
    
    while True:
        # 等待输入文件
        while not os.path.exists(input_file):
            import time
            time.sleep(0.1)
        
        # 读取输入
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # 删除输入文件
        os.remove(input_file)
        
        # 检查是否退出
        if data.get('command') == 'exit':
            print("收到退出命令")
            break
        
        # 获取 chessMap
        chess_map = data.get('chess_map')
        if chess_map is None:
            continue
        
        # 计算 AI 落子
        row, col, value = ai.get_move_from_chess_map(chess_map)
        
        # 写入输出
        result = {
            'row': row,
            'col': col,
            'value': value
        }
        with open(output_file, 'w') as f:
            json.dump(result, f)
        
        print(f"AI 落子: ({row}, {col}), 评估值: {value:.4f}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="五子棋 AI C++ 接口")
    parser.add_argument('--model', type=str, default="checkpoints/best_model.pt",
                        help='模型路径')
    parser.add_argument('--input', type=str, default="ai_input.json",
                        help='输入文件路径')
    parser.add_argument('--output', type=str, default="ai_output.json",
                        help='输出文件路径')
    
    args = parser.parse_args()
    
    file_based_communication(args.model, args.input, args.output)


if __name__ == "__main__":
    main()
