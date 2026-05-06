#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h> // 需要这个库来加载 JPG/PNG
#include <iostream>

int main(int argc, char* argv[]) {
    // 1. 初始化 SDL 和 SDL_image
    if (SDL_Init(SDL_INIT_VIDEO) < 0) return 1;
    // 初始化解码器支持 JPG
    if (!(IMG_Init(IMG_INIT_JPG) & IMG_INIT_JPG)) return 1;

    // 2. 创建窗口
    SDL_Window* window = SDL_CreateWindow("简易图片显示", 
        SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 
        897, 895, 
        SDL_WINDOW_SHOWN);
    
    // 3. 【关键】获取窗口的“表面” (Surface)
    // Surface 就是一块内存区域，我们可以直接往里面写像素
    SDL_Surface* screenSurface = SDL_GetWindowSurface(window);

    // 4. 加载图片
    // 使用 IMG_Load 加载 JPG，返回一个 Surface
    SDL_Surface* imageSurface = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/棋盘2.jpg");
    SDL_Surface* chessWhiteImg = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/black.png");
    if (imageSurface == nullptr) {
        std::cerr << "图片加载失败: " << IMG_GetError() << std::endl;
        // 这里记得退出，否则后面会崩溃
        SDL_DestroyWindow(window);
        IMG_Quit();
        SDL_Quit();
        return 1;
    }

    // 5. 显示图片的主循环
    bool quit = false;
    SDL_Event event;
    while (!quit) {
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) quit = true;
        }

        // --- 绘图开始 ---
        
        // A. 把图片 Surface 的内容“复制”到窗口 Surface 上
        // 参数: 源图片, 裁剪区域(空), 目标窗口, 目标位置(空)
        SDL_Rect pos;
        pos.x = 120; // 横坐标
        pos.y = 200; // 纵坐标
        SDL_BlitSurface(imageSurface, NULL, screenSurface, NULL);
        SDL_BlitSurface(chessWhiteImg,NULL,screenSurface,&pos);

        // B. 告诉系统：“我画完了，请更新窗口显示”
        SDL_UpdateWindowSurface(window);
        
        // --- 绘图结束 ---
    }

    // 6. 清理资源
    SDL_FreeSurface(imageSurface); // 释放图片内存
    SDL_DestroyWindow(window);
    IMG_Quit();
    SDL_Quit();

    return 0;
}