"""
五子棋神经网络模型 - AlphaZero 风格
包含策略网络（输出落子概率）和价值网络（评估局面价值）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class ResBlock(nn.Module):
    """残差块"""
    def __init__(self, channels):
        super(ResBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        out = F.relu(out)
        return out


class GomokuNet(nn.Module):
    """
    五子棋神经网络
    输入: (batch, 4, board_size, board_size)
        - 通道0: 当前玩家的棋子位置
        - 通道1: 对手的棋子位置
        - 通道2: 上一步落子位置
        - 通道3: 当前玩家标识（全1或全0）
    输出:
        - policy: (batch, board_size * board_size) 落子概率
        - value: (batch, 1) 局面评估值 [-1, 1]
    """
    
    def __init__(self, board_size=13, num_res_blocks=5, channels=64):
        super(GomokuNet, self).__init__()
        self.board_size = board_size
        self.action_size = board_size * board_size
        
        # 共享的卷积层
        self.conv_head = nn.Sequential(
            nn.Conv2d(4, channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(channels),
            nn.ReLU()
        )
        
        # 残差块堆叠
        self.res_blocks = nn.ModuleList([
            ResBlock(channels) for _ in range(num_res_blocks)
        ])
        
        # 策略头
        self.policy_conv = nn.Conv2d(channels, 2, kernel_size=1)
        self.policy_bn = nn.BatchNorm2d(2)
        self.policy_fc = nn.Linear(2 * board_size * board_size, self.action_size)
        
        # 价值头
        self.value_conv = nn.Conv2d(channels, 1, kernel_size=1)
        self.value_bn = nn.BatchNorm2d(1)
        self.value_fc1 = nn.Linear(board_size * board_size, 64)
        self.value_fc2 = nn.Linear(64, 1)
        
    def forward(self, x):
        # 共享层
        out = self.conv_head(x)
        for res_block in self.res_blocks:
            out = res_block(out)
        
        # 策略头
        policy = F.relu(self.policy_bn(self.policy_conv(out)))
        policy = policy.view(policy.size(0), -1)
        policy = self.policy_fc(policy)
        policy = F.log_softmax(policy, dim=1)
        
        # 价值头
        value = F.relu(self.value_bn(self.value_conv(out)))
        value = value.view(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))
        
        return policy, value
    
    def get_policy_value(self, board_tensor):
        """获取策略和价值的便捷方法"""
        self.eval()
        with torch.no_grad():
            if len(board_tensor.shape) == 3:
                board_tensor = board_tensor.unsqueeze(0)
            policy, value = self.forward(board_tensor)
            return torch.exp(policy).cpu().numpy()[0], value.cpu().numpy()[0][0]


class GomokuEnv:
    """五子棋环境，用于训练"""
    
    def __init__(self, board_size=13):
        self.board_size = board_size
        self.reset()
    
    def reset(self):
        """重置棋盘"""
        self.board = np.zeros((self.board_size, self.board_size), dtype=np.int8)
        self.current_player = 1  # 1: 黑棋, -1: 白棋
        self.last_move = None
        self.game_over = False
        self.winner = None
        return self.get_state()
    
    def get_state(self):
        """获取当前状态（4通道张量）"""
        state = np.zeros((4, self.board_size, self.board_size), dtype=np.float32)
        
        # 当前玩家的棋子
        state[0] = (self.board == self.current_player).astype(np.float32)
        # 对手的棋子
        state[1] = (self.board == -self.current_player).astype(np.float32)
        # 上一步落子
        if self.last_move is not None:
            state[2][self.last_move[0], self.last_move[1]] = 1.0
        # 当前玩家标识
        state[3] = np.ones((self.board_size, self.board_size), dtype=np.float32) if self.current_player == 1 else np.zeros((self.board_size, self.board_size), dtype=np.float32)
        
        return state
    
    def get_legal_moves(self):
        """获取合法落子位置"""
        return list(zip(*np.where(self.board == 0)))
    
    def step(self, action):
        """
        执行落子
        action: (row, col) 或 int (row * board_size + col)
        返回: (next_state, reward, done, info)
        """
        if self.game_over:
            return self.get_state(), 0, True, {"winner": self.winner}
        
        if isinstance(action, int):
            row, col = action // self.board_size, action % self.board_size
        else:
            row, col = action
        
        if self.board[row, col] != 0:
            return self.get_state(), -1, True, {"winner": -self.current_player, "error": "illegal move"}
        
        self.board[row, col] = self.current_player
        self.last_move = (row, col)
        
        # 检查胜负
        if self._check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
            return self.get_state(), 1.0, True, {"winner": self.winner}
        
        # 检查平局
        if len(self.get_legal_moves()) == 0:
            self.game_over = True
            self.winner = 0
            return self.get_state(), 0, True, {"winner": 0}
        
        # 切换玩家
        self.current_player = -self.current_player
        return self.get_state(), 0, False, {}
    
    def _check_win(self, row, col):
        """检查是否获胜"""
        player = self.board[row, col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            # 正向
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r, c] == player:
                count += 1
                r += dr
                c += dc
            # 反向
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r, c] == player:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 5:
                return True
        return False
    
    def render(self):
        """打印棋盘"""
        symbols = {0: '.', 1: 'X', -1: 'O'}
        print('  ' + ' '.join(str(i % 10) for i in range(self.board_size)))
        for i, row in enumerate(self.board):
            print(f"{i:2d} " + ' '.join(symbols[x] for x in row))
        print()


if __name__ == "__main__":
    # 测试模型
    net = GomokuNet(board_size=13)
    print(f"模型参数量: {sum(p.numel() for p in net.parameters()):,}")
    
    # 测试前向传播
    x = torch.randn(2, 4, 13, 13)
    policy, value = net(x)
    print(f"Policy shape: {policy.shape}")
    print(f"Value shape: {value.shape}")
    
    # 测试环境
    env = GomokuEnv(13)
    env.render()
