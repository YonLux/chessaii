#include "test.h"
#include <SDL2/SDL.h>
#include <iostream>


int main(int argc, char* argv[]) {
    // 1. 初始化 SDL 视频子系统
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "SDL 初始化失败: " << SDL_GetError() << std::endl;
        return 1;
    }

    // 2. 创建窗口
    // 参数依次为：窗口标题, 水平位置, 垂直位置, 宽度, 高度, 窗口属性
    // SDL_WINDOWPOS_CENTERED 让窗口在屏幕中央显示
    // SDL_WINDOW_SHOWN 表示窗口创建后是可见的
    SDL_Window* window = SDL_CreateWindow(
        "My SDL2 Window", 
        SDL_WINDOWPOS_CENTERED, 
        SDL_WINDOWPOS_CENTERED, 
        897,  // 窗口宽度
        895,  // 窗口高度
        SDL_WINDOW_SHOWN
    );

    if (window == nullptr) {
        std::cerr << "窗口创建失败: " << SDL_GetError() << std::endl;
        SDL_Quit();
        return 1;
    }

    // 3. 创建渲染器
    // 参数依次为：窗口指针, 渲染器索引(-1表示自动选择), 渲染器属性
    // SDL_RENDERER_ACCELERATED 表示使用硬件加速
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (renderer == nullptr) {
        std::cerr << "渲染器创建失败: " << SDL_GetError() << std::endl;
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    // 4. 事件循环，保持窗口打开
    bool quit = false;
    SDL_Event event;
    while (!quit) {
        // 检查并处理所有待处理的事件
        while (SDL_PollEvent(&event)) {
            // 如果用户点击了窗口的关闭按钮
            if (event.type == SDL_QUIT) {
                quit = true;
            }
        }
        
        // 在这里可以添加你的绘图代码
        // 例如：清空渲染器
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255); // 设置为黑色
        SDL_RenderClear(renderer);
        
        // 更新屏幕显示
        SDL_RenderPresent(renderer);
    }

    // 5. 清理资源并退出
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();

    return 0;
}