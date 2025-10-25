#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏实现 (Gomoku)
支持双人对战，玩家轮流在15*15的棋盘上下棋，率先连成五子者获胜。
"""

class Gomoku:
    def __init__(self, size=15):
        """
        初始化游戏。
        :param size: 棋盘大小，默认为15。
        """
        self.size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        self.current_player = 1  # 1代表黑子，2代表白子
        self.game_over = False
        self.winner = None

    def print_board(self):
        """打印当前棋盘状态。"""
        print("  ", end="")
        for i in range(self.size):
            print(f"{i:2}", end=" ")
        print()
        for i, row in enumerate(self.board):
            print(f"{i:2}", end=" ")
            for cell in row:
                if cell == 0:
                    print(" .", end=" ")
                elif cell == 1:
                    print(" ●", end=" ") # 黑子
                else:
                    print(" ○", end=" ") # 白子
            print()

    def is_valid_move(self, x, y):
        """
        判断落子是否合法。
        :param x: 行坐标
        :param y: 列坐标
        :return: 布尔值，合法为True，否则为False。
        """
        return 0 <= x < self.size and 0 <= y < self.size and self.board[x][y] == 0

    def make_move(self, x, y):
        """
        在指定位置落子。
        :param x: 行坐标
        :param y: 列坐标
        :return: 布尔值，成功为True，失败为False。
        """
        if self.is_valid_move(x, y) and not self.game_over:
            self.board[x][y] = self.current_player
            if self._check_winner(x, y):
                self.game_over = True
                self.winner = self.current_player
            else:
                self.current_player = 3 - self.current_player # 切换玩家 (1->2, 2->1)
            return True
        return False

    def _check_winner(self, x, y):
        """
        检查在(x, y)位置落子后是否获胜。
        :param x: 最后落子的行坐标
        :param y: 最后落子的列坐标
        :return: 布尔值，获胜为True，否则为False。
        """
        player = self.board[x][y]
        directions = [
            (0, 1),  # 水平
            (1, 0),  # 垂直
            (1, 1),  # 主对角线
            (1, -1)  # 副对角线
        ]
        for dx, dy in directions:
            count = 1  # 包含当前落子
            # 向一个方向检查
            tx, ty = x + dx, y + dy
            while 0 <= tx < self.size and 0 <= ty < self.size and self.board[tx][ty] == player:
                count += 1
                tx, ty = tx + dx, ty + dy
            # 向相反方向检查
            tx, ty = x - dx, y - dy
            while 0 <= tx < self.size and 0 <= ty < self.size and self.board[tx][ty] == player:
                count += 1
                tx, ty = tx - dx, ty - dy
            if count >= 5:
                return True
        return False

    def play(self):
        """游戏主循环。"""
        print("欢迎来到五子棋游戏！")
        print("玩家1: ● (黑子)")
        print("玩家2: ○ (白子)")
        print("输入坐标格式为 '行 列' (例如: '7 7')。")
        
        while not self.game_over:
            self.print_board()
            try:
                move = input(f"玩家 {self.current_player} 请输入落子坐标: ").split()
                if len(move) != 2:
                    print("输入格式错误，请输入两个数字。")
                    continue
                x, y = int(move[0]), int(move[1])
                if not self.make_move(x, y):
                    print("无效的落子位置，请重试。")
            except ValueError:
                print("请输入有效的数字。")

        self.print_board()
        if self.winner:
            print(f"游戏结束！玩家 {self.winner} 获胜！")
        else:
            print("游戏结束！平局。")


if __name__ == "__main__":
    game = Gomoku()
    game.play()