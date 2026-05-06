#include <math.h>
#include "chess.h"
#include <stdio.h>
#include <ncurses.h>
#include <alsa/asoundlib.h>
#include "chessgame.h"
/*****************************************
*   #include <mmsystem.h>  多媒体媒体音频库 使用alsa代替
*   --------------------------------------
*   #include <conio.h>提供了一些标准库（如 stdio.h）所不具备的、更底层的控制台操作功能，尤其适合制作简单的文本游戏或交互式菜单。
*   使用ncurses代替
*   --------------------------------------
*   使用SDL2 来代替EasyX
*
*
*****************************************/


int main(void)
{
	Man man;
	// Chess chess;
	Chess chess(13, 44, 43, 67.3);
	//Chess chess(13, 44, 43, 84);
	AI ai;
	ChessGame game(&man, &ai, &chess);

	game.play();

	return 0;

}