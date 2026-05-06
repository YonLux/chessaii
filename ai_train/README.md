# 五子棋 AI 训练框架 (AlphaZero 风格)

## 目录结构

```
ai_train/
├── model.py          # 神经网络模型定义
├── mcts.py           # 蒙特卡洛树搜索
├── train.py          # 训练脚本
├── play.py           # 与 AI 对战
├── cpp_interface.py  # C++ 接口
└── checkpoints/      # 模型保存目录
```

## 安装依赖

```bash
pip install torch numpy
```

## 使用方法

### 1. 开始训练

```bash
cd ai_train
python train.py
```

训练参数可以在 `train.py` 中修改：
- `n_epochs`: 训练轮数（默认 100）
- `games_per_epoch`: 每轮自我对弈游戏数（默认 100）
- `n_simulations`: MCTS 模拟次数（默认 400）

### 2. 与训练好的 AI 对战

```bash
python play.py --model checkpoints/best_model.pt
```

### 3. 与 C++ 代码对接

方式一：文件通信
```bash
# 启动 AI 接口
python cpp_interface.py --model checkpoints/best_model.pt
```

然后在 C++ 代码中：
1. 将 chessMap 写入 `ai_input.json`
2. 从 `ai_output.json` 读取 AI 落子位置

方式二：直接使用 NeuralAI 类
```cpp
#include "neural_ai.h"

NeuralAI ai(13);  // 13x13 棋盘
ai.init();

// 获取 AI 落子
auto [row, col] = ai.getMove(chessMap);
```

## 神经网络架构

```
输入: (4, board_size, board_size)
├── 通道 0: 当前玩家棋子位置
├── 通道 1: 对手棋子位置
├── 通道 2: 上一步落子位置
└── 通道 3: 当前玩家标识

网络结构:
├── 卷积头 (Conv2d -> BatchNorm -> ReLU)
├── 残差块 x N
├── 策略头 -> 落子概率分布
└── 价值头 -> 局面评估值 [-1, 1]
```

## 训练流程

```
┌─────────────────────────────────────────────────────┐
│                    训练循环                          │
├─────────────────────────────────────────────────────┤
│  1. 自我对弈                                        │
│     ├── 使用 MCTS + 神经网络搜索                    │
│     ├── 生成训练数据 (state, mcts_probs, reward)   │
│     └── 存入经验回放缓冲区                          │
│                                                     │
│  2. 神经网络训练                                    │
│     ├── 策略损失: 交叉熵                            │
│     ├── 价值损失: MSE                               │
│     └── 反向传播更新参数                            │
│                                                     │
│  3. 评估 & 保存                                     │
│     ├── 与随机玩家对战评估                          │
│     └── 保存最佳模型                                │
└─────────────────────────────────────────────────────┘
```

## 参数调优建议

| 参数 | 小棋盘 (9x9) | 中棋盘 (13x13) | 大棋盘 (15x15+) |
|------|-------------|----------------|-----------------|
| 残差块数 | 3-5 | 5-7 | 7-10 |
| 通道数 | 32-64 | 64-128 | 128-256 |
| MCTS 模拟次数 | 200-400 | 400-800 | 800-1600 |
| 自我对弈局数 | 100-200 | 100-200 | 50-100 |

## 与现有代码整合

修改 `ai.cpp` 使用神经网络 AI：

```cpp
#include "neural_ai.h"

class AI {
private:
    NeuralAI neuralAI;
    bool useNeuralNet;
    
public:
    void init(Chess* chess) {
        this->chess = chess;
        useNeuralNet = neuralAI.init();
    }
    
    void go() {
        ChessPos pos;
        
        if (useNeuralNet) {
            // 使用神经网络 AI
            auto [row, col] = neuralAI.getMove(chess->chessMap);
            pos.row = row;
            pos.col = col;
        } else {
            // 使用传统 AI
            pos = think();
        }
        
        chess->chessDown(&pos, CHESS_WHITE);
    }
};
```
