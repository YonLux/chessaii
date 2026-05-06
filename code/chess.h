#pragma once
#include <vector>
using namespace std;
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h> // 用于加载 PNG/JPG 图片

// extern SDL_Window* gWindow;  // 假设这是你的全局窗口和渲染器指针（通常在 main.cpp 定义， extern 引用）
// extern SDL_Renderer* gRenderer;

// 表示落子位置
struct ChessPos
{
	int row;
	int col;
	ChessPos(int r = 0, int c = 0) :row(r), col(c) {};
};

// 表示棋子的种类
typedef enum
{
	CHESS_WHITE = -1, // 白棋
	CHESS_BLACK = 1 // 黑棋
}chess_kind;

class Chess
{
public:

	// 构造棋盘
	Chess(int gradeSize, int maiginX, int marginY, float chessSize);

	// 棋盘初始化：加载棋盘的图片资源，初始化棋盘的相关数据
	void init();

	/*
		判断在指定坐标(x,y)位置，是否是有效点击，
		如果是有效点击，把有效点击的位置(行，列）保存在参数pos中
	*/
	bool clickBoard(int x, int y, ChessPos *pos);

	// 在棋盘的指定位置（pos）, 落子（chess）
	void chessDown(ChessPos *pos, chess_kind chess);

	// 获取棋盘的大小（13线、15线、19线）
	int getGradeSize();

	// 获取指定位置是黑棋，还是白棋，还是空白
	int getChessData(ChessPos *pos);
	int getChessData(int row, int col);


	// 检查棋局是否结束
	bool checkOver();

	void printmap(vector<vector<int>> map);
	vector<vector<int>> chessMap;

	
private:
	SDL_Window* window = nullptr;
	SDL_Texture* gBoardTexture = nullptr;  // 加载图片
	SDL_Surface* screenSurface = nullptr;  // window的表面
	SDL_Surface* imageSurface = nullptr;   

	SDL_Surface* chessBlackImg = nullptr;  // 加载棋子
	SDL_Surface* chessWhiteImg = nullptr;

	SDL_Surface* winpic = nullptr;  // 输赢
	SDL_Surface* losepic = nullptr;



	int gradeSize; // 棋盘的大小（13线、15线、17线、19线）
	int margin_x; // 棋盘的左侧边界
	int margin_y; // 棋盘的顶部边界
	float chessSize; // 棋子的大小（棋盘的小方格的大小）
	/*
		存储当前棋局的棋子分布数据
		例如：chessMap[3][5]表示棋盘的第3行第5列的落子情况（0：空白；1：黑子；-1：白子）
	*/

	/*
		表示现在该谁下棋（落子）
		true：该黑子走；false：该白子走
	*/
	bool playerFlag;

	// 将落子信息存储到二维数组中
	void updateGameMap(ChessPos* pos);

	// 检查当前谁嬴谁输，如果胜负已分就返回true，否则返回false
	bool checkWin();

	// 某一落子点的位置
	ChessPos lastPos;

};