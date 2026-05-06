"""
蒙特卡洛树搜索 (MCTS) - AlphaZero 风格
使用神经网络指导搜索
"""

import numpy as np
import math
from collections import defaultdict


class MCTSNode:
    """MCTS 节点"""
    
    def __init__(self, parent=None, prior_p=1.0):
        self.parent = parent
        self.children = {}
        self.n_visits = 0
        self.Q = 0.0
        self.P = prior_p
        self.u = 0.0
    
    def expand(self, action_priors):
        """扩展节点"""
        for action, prob in action_priors:
            if action not in self.children:
                self.children[action] = MCTSNode(parent=self, prior_p=prob)
    
    def select(self, c_puct=5.0):
        """选择最佳子节点"""
        return max(self.children.items(), 
                   key=lambda item: item[1].get_value(c_puct))
    
    def get_value(self, c_puct):
        """计算 UCB 值"""
        self.u = c_puct * self.P * math.sqrt(self.parent.n_visits) / (1 + self.n_visits)
        return self.Q + self.u
    
    def update(self, leaf_value):
        """更新节点值"""
        self.n_visits += 1
        self.Q += (leaf_value - self.Q) / self.n_visits
    
    def update_recursive(self, leaf_value):
        """递归更新所有祖先节点"""
        if self.parent:
            self.parent.update_recursive(-leaf_value)
        self.update(leaf_value)
    
    def is_leaf(self):
        """是否为叶子节点"""
        return len(self.children) == 0
    
    def is_root(self):
        """是否为根节点"""
        return self.parent is None


class MCTS:
    """蒙特卡洛树搜索"""
    
    def __init__(self, policy_value_fn, c_puct=5.0, n_simulations=400):
        """
        policy_value_fn: 函数，输入状态，输出 (action_probs, value)
        c_puct: 探索常数
        n_simulations: 模拟次数
        """
        self.root = MCTSNode()
        self.policy_value_fn = policy_value_fn
        self.c_puct = c_puct
        self.n_simulations = n_simulations
    
    def search(self, state, env, temperature=1.0):
        """
        执行 MCTS 搜索
        返回: action_probs (动作概率分布)
        """
        for _ in range(self.n_simulations):
            env_copy = self._copy_env(env)
            self._search_recursive(self.root, state, env_copy)
        
        # 根据访问次数计算动作概率
        action_visits = [(action, node.n_visits) 
                         for action, node in self.root.children.items()]
        
        if temperature == 0:
            # 选择访问次数最多的动作
            max_visits = max(v for _, v in action_visits)
            best_actions = [a for a, v in action_visits if v == max_visits]
            action = np.random.choice(best_actions)
            probs = np.zeros(env.board_size * env.board_size)
            probs[action] = 1.0
            return probs
        
        # 使用温度参数计算概率
        visits = np.array([v for _, v in action_visits])
        visits = visits ** (1.0 / temperature)
        probs = visits / visits.sum()
        
        action_probs = np.zeros(env.board_size * env.board_size)
        for (action, _), p in zip(action_visits, probs):
            action_probs[action] = p
        
        return action_probs
    
    def _search_recursive(self, node, state, env):
        """递归搜索"""
        if env.game_over:
            if env.winner == 0:
                return 0.0
            return 1.0 if env.winner == env.current_player else -1.0
        
        if node.is_leaf():
            # 使用神经网络评估叶子节点
            action_probs, value = self.policy_value_fn(state)
            
            # 获取合法动作
            legal_moves = env.get_legal_moves()
            legal_actions = [r * env.board_size + c for r, c in legal_moves]
            
            # 扩展节点
            action_probs = action_probs[legal_actions]
            if action_probs.sum() > 0:
                action_probs = action_probs / action_probs.sum()
            else:
                action_probs = np.ones(len(legal_actions)) / len(legal_actions)
            
            node.expand(zip(legal_actions, action_probs))
            return -value
        
        # 选择最佳动作
        action, child = node.select(self.c_puct)
        
        # 执行动作
        row, col = action // env.board_size, action % env.board_size
        next_state, _, _, _ = env.step((row, col))
        
        # 递归搜索
        value = self._search_recursive(child, next_state, env)
        
        # 更新节点
        child.update_recursive(-value)
        
        return value
    
    def _copy_env(self, env):
        """复制环境"""
        import copy
        new_env = GomokuEnv.__new__(GomokuEnv)
        new_env.board_size = env.board_size
        new_env.board = env.board.copy()
        new_env.current_player = env.current_player
        new_env.last_move = env.last_move
        new_env.game_over = env.game_over
        new_env.winner = env.winner
        return new_env
    
    def update_with_move(self, last_move):
        """根据对手落子更新树"""
        if last_move in self.root.children:
            self.root = self.root.children[last_move]
            self.root.parent = None
        else:
            self.root = MCTSNode()


class MCTSPlayer:
    """MCTS 玩家"""
    
    def __init__(self, policy_value_fn, c_puct=5.0, n_simulations=400, is_selfplay=False):
        self.mcts = MCTS(policy_value_fn, c_puct, n_simulations)
        self.is_selfplay = is_selfplay
    
    def get_action(self, env, temperature=1.0, return_prob=False):
        """获取动作"""
        if env.game_over:
            return None
        
        state = env.get_state()
        action_probs = self.mcts.search(state, env, temperature)
        
        if self.is_selfplay:
            # 自我对弈时添加噪声
            action = np.random.choice(len(action_probs), p=action_probs)
            self.mcts.update_with_move(action)
        else:
            # 对战时选择最佳动作
            action = np.argmax(action_probs)
            self.mcts.update_with_move(action)
        
        if return_prob:
            return action, action_probs
        return action
    
    def reset(self):
        """重置 MCTS"""
        self.mcts = MCTS(self.mcts.policy_value_fn, 
                        self.mcts.c_puct, 
                        self.mcts.n_simulations)


# 导入 GomokuEnv（避免循环导入）
from model import GomokuEnv


if __name__ == "__main__":
    # 测试 MCTS
    from model import GomokuNet
    
    net = GomokuNet(board_size=13)
    
    def policy_value_fn(state):
        """简单的策略价值函数"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            log_policy, value = net(state_tensor)
            policy = torch.exp(log_policy).numpy()[0]
        return policy, value.item()
    
    player = MCTSPlayer(policy_value_fn, n_simulations=100)
    env = GomokuEnv(13)
    
    print("测试 MCTS 玩家...")
    for i in range(10):
        action = player.get_action(env, temperature=0.1)
        row, col = action // 13, action % 13
        print(f"第 {i+1} 步: ({row}, {col})")
        env.step(action)
        env.render()
        if env.game_over:
            break
