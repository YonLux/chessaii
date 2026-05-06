
#include "chess.h"
#include <math.h>
#include <alsa/asoundlib.h>  //音频
#include <ncurses.h>         //控制输入输出
#include <stdio.h>
#include <iostream>
#include <SDL2/SDL.h>

// 这里不用解决Easyx不支持png格式图片的函数  SDL2对png支持还不错



// 构造棋盘
Chess::Chess(int gradeSize, int marginX, int marginY, float chessSize)
{
	this->gradeSize = gradeSize;
	this->margin_x = marginX;
	this->margin_y = marginY;
	this->chessSize = chessSize;
	playerFlag = CHESS_BLACK;
	for (int i = 0; i < gradeSize; i++)
	{
		vector<int> row;
		for (int j = 0; j < gradeSize; j++)
		{
			row.push_back(0);
		}
		chessMap.push_back(row);
	}
}


// 棋盘初始化
void Chess::init()
{
	if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO) < 0)
	{
		std::cerr << "SDL初始化失败: " << SDL_GetError() << std::endl;
		return;
	}
	if (!(IMG_Init(IMG_INIT_JPG | IMG_INIT_PNG) & (IMG_INIT_JPG | IMG_INIT_PNG)))
	{
		std::cerr << "SDL_image初始化失败: " << IMG_GetError() << std::endl;
		return;
	}
	Chess::window = SDL_CreateWindow("五子棋", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 897, 895, SDL_WINDOW_SHOWN);
	if (!Chess::window)
	{
		std::cerr << "窗口创建失败: " << SDL_GetError() << std::endl;
		return;
	}
	Chess::screenSurface = SDL_GetWindowSurface(Chess::window);
	Chess::imageSurface = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/棋盘2.jpg");
	if (!Chess::imageSurface)
	{
		std::cerr << "棋盘图片加载失败: " << IMG_GetError() << std::endl;
	}
	else
	{
		SDL_BlitSurface(Chess::imageSurface, NULL, Chess::screenSurface, NULL);
		SDL_UpdateWindowSurface(Chess::window);
	}
	std::cout << "请开始下棋" << std::endl;
	Chess::chessBlackImg = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/blackmin.png");
	Chess::chessWhiteImg = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/whitemin.png");
	Chess::winpic = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/胜利.jpg");
	Chess::losepic = IMG_Load("/mnt/d/new/github/wrok/wsl/cplus/ZGomoku/resource/失败.jpg");
	for (int i = 0; i < gradeSize; i++)
	{
		for (int j = 0; j < gradeSize; j++)
		{
			chessMap[i][j] = 0;
		}
	}
	playerFlag = true;
}

// 判断落子是否有效
bool Chess::clickBoard(int x, int y, ChessPos * pos)
{
	// 真实的落子列坐标
	int col = (x - margin_x) / chessSize;
	// 真实的落子行坐标
	int row = (y - margin_y) / chessSize;
	// 落子的左上角列坐标
	int leftTopPosX = margin_x + chessSize * col ;
	// 落子的左上角行坐标
	int leftTopPosY = margin_y + chessSize * row ;
	// 鼠标点击位置距离真实落子位置的阈值
	int offset = chessSize * 0.4;
	// 落子距离四个角的距离
	int len;
	// 落子是否有效
	bool res = false;
	do
	{
		// 落子距离左上角的距离
		len = sqrt((x - leftTopPosX) * (x - leftTopPosX) + (y - leftTopPosY) * (y - leftTopPosY));
		// 如果落子距离左上角的距离小于阈值并且当前位置没有棋子，就保存当前落子位置，并设置落子有效
		if (len < offset)
		{
			pos->row = row;
			pos->col = col;
			if (chessMap[pos->row][pos->col] == 0)
			{
				res = true;
			}
			break;
		}
		// 落子距离右上角的距离
		int x2 = leftTopPosX + chessSize;
		int y2 = leftTopPosY;
		len = sqrt((x - x2) * (x - x2) + (y - y2) * (y - y2));
		// 如果落子距离右上角的距离小于阈值并且当前位置没有棋子，就保存当前落子位置，并设置落子有效
		if (len < offset)
		{
			pos->row = row;
			pos->col = col + 1;
			if (chessMap[pos->row][pos->col] == 0)
			{
				res = true;
			}
			break;
		}
		// 落子距离左下角的距离
		x2 = leftTopPosX;
		y2 = leftTopPosY + chessSize;
		len = sqrt((x - x2) * (x - x2) + (y - y2) * (y - y2));
		// 如果落子距离右上角的距离小于阈值并且当前位置没有棋子，就保存当前落子位置，并设置落子有效
		if (len < offset)
		{
			pos->row = row + 1;
			pos->col = col;
			if (chessMap[pos->row][pos->col] == 0)
			{
				res = true;
			}
			break;
		}
		// 落子距离右下角的距离
		x2 = leftTopPosX + chessSize;
		y2 = leftTopPosY + chessSize;
		len = sqrt((x - x2) * (x - x2) + (y - y2) * (y - y2));
		// 如果落子距离右上角的距离小于阈值并且当前位置没有棋子，就保存当前落子位置，并设置落子有效
		if (len < offset)
		{
			pos->row = row + 1;
			pos->col = col + 1;
			if (chessMap[pos->row][pos->col] == 0)
			{
				res = true;
			}
			break;
		}
	} while (0);
	// 返回落子是否有效的判断结果
	return res;
}

// 棋盘落子
void Chess::chessDown(ChessPos * pos, chess_kind chess)
{
	int x = margin_x + chessSize * pos->col - 0.5 * chessSize ;
	int y = margin_y + chessSize * pos->row - 0.5 * chessSize ;
	SDL_Rect _pos;
	_pos.x = x;
	_pos.y = y;
	if (chess == CHESS_WHITE)
	{
		SDL_BlitSurface(chessWhiteImg, NULL, screenSurface, &_pos);
	}
	else
	{
		SDL_BlitSurface(chessBlackImg, NULL, screenSurface, &_pos);
	}
	SDL_UpdateWindowSurface(window);
	updateGameMap(pos);
}

// 返回棋盘大小
int Chess::getGradeSize()
{
	return gradeSize;
}

// 返回棋子数据
int Chess::getChessData(ChessPos * pos)
{
	return chessMap[pos->row][pos->col];
}

// 返回棋子数据
int Chess::getChessData(int row, int col)
{
	return chessMap[row][col];
}


// 胜负判定
bool Chess::checkOver()
{
	if (checkWin())
	{
		if (playerFlag == false)
		{
			SDL_BlitSurface(winpic, NULL, screenSurface, NULL);
		}
		else
		{
			SDL_BlitSurface(losepic, NULL, screenSurface, NULL);
		}
		SDL_UpdateWindowSurface(window);
		for (int i = 0; i < 50; i++)
		{
			SDL_Event event;
			while (SDL_PollEvent(&event))
			{
				if (event.type == SDL_QUIT)
				{
					exit(0);
				}
			}
			SDL_Delay(100);
		}
		return true;
	}
	return false;
}

// 将落子信息存储在二维数组中
void Chess::updateGameMap(ChessPos * pos)
{
	// 存储某一落子点的位置
	lastPos = *pos;
	// 存储落子信息
	chessMap[pos->row][pos->col] = playerFlag ? CHESS_BLACK : CHESS_WHITE;
	// 黑白方交换行棋
	playerFlag = !playerFlag;
}

// 检查当前谁嬴谁输，如果胜负已分就返回true，否则返回false
bool Chess::checkWin()
{
	// 某一落子点的位置
	int row = lastPos.row;
	int col = lastPos.col;
	// 落子点的水平方向
	for (int i = 0; i < 5; i++)
	{
		if (((col - i) >= 0) && ((col - i + 4) < gradeSize) && (chessMap[row][col - i] == chessMap[row][col - i + 1]) && (chessMap[row][col - i] == chessMap[row][col - i + 2]) && (chessMap[row][col - i] == chessMap[row][col - i + 3]) && (chessMap[row][col - i] == chessMap[row][col - i + 4]))
		{
			return true;
		}
	}
	// 落子点的垂直方向
	for (int i = 0; i < 5; i++)
	{
		if (((row - i) >= 0) && ((row - i + 4) < gradeSize) && (chessMap[row - i][col] == chessMap[row - i + 1][col]) && (chessMap[row - i][col] == chessMap[row - i + 2][col]) && (chessMap[row - i][col] == chessMap[row - i + 3][col]) && (chessMap[row - i][col] == chessMap[row - i + 4][col]))
		{
			return true;
		}
	}
	// 落子点的右斜方向
	for (int i = 0; i < 5; i++)
	{
		if (((row + i) < gradeSize) && (row + i - 4 >= 0) && (col - i >= 0) && ((col - i + 4) < gradeSize) && (chessMap[row + i][col - i] == chessMap[row + i - 1][col - i + 1]) && (chessMap[row + i][col - i] == chessMap[row + i - 2][col - i + 2]) && (chessMap[row + i][col - i] == chessMap[row + i - 3][col - i + 3]) && (chessMap[row + i][col - i] == chessMap[row + i - 4][col - i + 4]))
		{
			return true;
		}
	}
	// 落子点的左斜方向
	for (int i = 0; i < 5; i++)
	{
		if (((row - i + 4) < gradeSize) && (row - i >= 0) && (col - i >= 0) && ((col - i + 4) < gradeSize) && (chessMap[row - i][col - i] == chessMap[row - i + 1][col - i + 1]) && (chessMap[row - i][col - i] == chessMap[row - i + 2][col - i + 2]) && (chessMap[row - i][col - i] == chessMap[row - i + 3][col - i + 3]) && (chessMap[row - i][col - i] == chessMap[row - i + 4][col - i + 4]))
		{
			return true;
		}
	}
	return false;
}


void Chess::printmap(vector<vector<int>>  map)
{
	// 1. 遍历外层 vector (每一行)
	for (const auto& row : map) {
		// 2. 遍历内层 vector (每一个具体的数字)
		for (int val : row) {
			// 打印数字，并用制表符 "\t" 隔开，保持对齐
			std::cout << val << "\t"; 
		}
		// 3. 每一行打印完后，输出一个换行符
		std::cout << std::endl; 
	}
	// 可选：为了美观，矩阵打印完后多输出一行空行
	std::cout << std::endl; 
}
