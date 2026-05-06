#include "man.h"

// 棋手初始化
void Man::init(Chess * chess)
{
	this->chess = chess;
}

// 棋手下棋
void Man::go()
{
	SDL_Event event;
	ChessPos pos;
	while (1)
	{
		while (SDL_PollEvent(&event))
		{
			if (event.type == SDL_MOUSEBUTTONDOWN && event.button.button == SDL_BUTTON_LEFT)
			{
				if (chess->clickBoard(event.button.x, event.button.y, &pos))
				{
					chess->chessDown(&pos, CHESS_BLACK);
					return;
				}
			}
			if (event.type == SDL_QUIT)
			{
				exit(0);
			}
		}
	}
}
