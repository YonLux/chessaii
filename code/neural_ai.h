#pragma once

#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <cstdio>
#include <iostream>
#include <thread>
#include <chrono>
#include <mutex>
#include <condition_variable>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/wait.h>
#include <unistd.h>
#endif

class NeuralAI {
private:
    std::string modelPath;
    std::string pythonPath;
    int boardSize;
    FILE* pythonProcess;
    bool initialized;
    
public:
    NeuralAI(int boardSize = 13, const std::string& modelPath = "checkpoints/best_model.pt")
        : boardSize(boardSize), modelPath(modelPath), pythonProcess(nullptr), initialized(false) {
        pythonPath = "python3";
    }
    
    ~NeuralAI() {
        if (pythonProcess) {
#ifdef _WIN32
            _pclose(pythonProcess);
#else
            pclose(pythonProcess);
#endif
        }
    }
    
    bool init() {
        initialized = true;
        return true;
    }
    
    std::pair<int, int> getMove(const std::vector<std::vector<int>>& chessMap) {
        int bestRow = -1, bestCol = -1;
        float bestScore = -1000.0f;
        
        for (int row = 0; row < boardSize; row++) {
            for (int col = 0; col < boardSize; col++) {
                if (chessMap[row][col] == 0) {
                    float score = evaluatePosition(chessMap, row, col);
                    if (score > bestScore) {
                        bestScore = score;
                        bestRow = row;
                        bestCol = col;
                    }
                }
            }
        }
        
        if (bestRow == -1) {
            for (int row = 0; row < boardSize; row++) {
                for (int col = 0; col < boardSize; col++) {
                    if (chessMap[row][col] == 0) {
                        return {row, col};
                    }
                }
            }
        }
        
        return {bestRow, bestCol};
    }
    
private:
    float evaluatePosition(const std::vector<std::vector<int>>& chessMap, int row, int col) {
        float score = 0.0f;
        int directions[4][2] = {{0, 1}, {1, 0}, {1, 1}, {1, -1}};
        
        for (int d = 0; d < 4; d++) {
            int dr = directions[d][0];
            int dc = directions[d][1];
            
            int myCount = 0;
            int oppCount = 0;
            int emptyCount = 0;
            
            for (int i = -4; i <= 4; i++) {
                if (i == 0) continue;
                int r = row + i * dr;
                int c = col + i * dc;
                if (r >= 0 && r < boardSize && c >= 0 && c < boardSize) {
                    if (chessMap[r][c] == -1) myCount++;
                    else if (chessMap[r][c] == 1) oppCount++;
                    else emptyCount++;
                }
            }
            
            score += myCount * 10.0f;
            score += oppCount * 8.0f;
            
            if (myCount >= 4) score += 10000.0f;
            else if (myCount >= 3) score += 1000.0f;
            else if (myCount >= 2) score += 100.0f;
            
            if (oppCount >= 4) score += 9000.0f;
            else if (oppCount >= 3) score += 900.0f;
            else if (oppCount >= 2) score += 90.0f;
        }
        
        int center = boardSize / 2;
        float distToCenter = std::sqrt((row - center) * (row - center) + (col - center) * (col - center));
        score += (boardSize - distToCenter) * 2.0f;
        
        return score;
    }
    
    std::string execPython(const std::string& cmd) {
#ifdef _WIN32
        FILE* pipe = _popen(cmd.c_str(), "r");
#else
        FILE* pipe = popen(cmd.c_str(), "r");
#endif
        if (!pipe) return "";
        
        char buffer[128];
        std::string result = "";
        while (!feof(pipe)) {
            if (fgets(buffer, 128, pipe) != NULL)
                result += buffer;
        }
#ifdef _WIN32
        _pclose(pipe);
#else
        pclose(pipe);
#endif
        return result;
    }
};
