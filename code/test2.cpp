#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <iostream>

// 模拟 EasyX 的 IMAGE 类型，其实就是 SDL_Surface*
typedef SDL_Surface* IMAGE;

/**
 * 加载图片并缩放到指定大小
 * 对应: loadimage(&chessBlackImg, "res/black.png", chessSize, chessSize, true);
 */
IMAGE loadImageScaled(const char* path, int width, int height) {
    // 1. 加载原始图片
    SDL_Surface* loadedSurface = IMG_Load(path);
    if (loadedSurface == nullptr) {
        std::cerr << "无法加载图片: " << path << " - " << IMG_GetError() << std::endl;
        return nullptr;
    }

    // 2. 创建一个新的 Surface 用于存放缩放后的图片
    // 使用与窗口相同的格式可以避免格式转换带来的性能损耗
    SDL_Surface* scaledSurface = SDL_CreateRGBSurface(0, width, height, 32, 0, 0, 0, 0);
    if (scaledSurface == nullptr) {
        std::cerr << "无法创建缩放表面: " << SDL_GetError() << std::endl;
        SDL_FreeSurface(loadedSurface);
        return nullptr;
    }

    // 3. 定义矩形区域
    SDL_Rect srcRect = { 0, 0, loadedSurface->w, loadedSurface->h }; // 源区域（整张图）
    SDL_Rect dstRect = { 0, 0, width, height };                     // 目标区域（指定大小）

    // 4. 执行缩放绘制
    // SDL_BlitScaled 会自动处理拉伸和像素格式转换
    SDL_BlitScaled(loadedSurface, &srcRect, scaledSurface, &dstRect);

    // 5. 释放原始图片（因为我们只需要缩放后的那张）
    SDL_FreeSurface(loadedSurface);

    return scaledSurface;
}

int main(int argc, char* argv[]) {
    // 初始化
    if (SDL_Init(SDL_INIT_VIDEO) < 0) return 1;
    int imgFlags = IMG_INIT_PNG;
    if (!(IMG_Init(imgFlags) & imgFlags)) return 1;

    // 创建窗口 (897x895)
    SDL_Window* window = SDL_CreateWindow("五子棋", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 897, 895, SDL_WINDOW_SHOWN);
    SDL_Surface* screenSurface = SDL_GetWindowSurface(window);

    // --- 模拟你的代码 ---
    int chessSize = 60; // 假设棋子大小是 60x60
    IMAGE chessBlackImg = loadImageScaled("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/black.png", chessSize, chessSize);

    if (chessBlackImg != nullptr) {
        // 在窗口上绘制棋子 (例如画在左上角)
        SDL_BlitSurface(chessBlackImg, NULL, screenSurface, NULL);
        SDL_UpdateWindowSurface(window);

        // 等待 2 秒让你看到效果
        SDL_Delay(20000);
        
        // 释放资源
        SDL_FreeSurface(chessBlackImg);
    }

    SDL_DestroyWindow(window);
    IMG_Quit();
    SDL_Quit();
    return 0;
}