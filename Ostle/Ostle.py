#
# Ostle.py 2022/9/14
#
RELEASE_CANDIDATE = True
TENSORFLOW = False
SAVE_TRAIN  = False
if TENSORFLOW:
    import os
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import tensorflow as tf
    import numpy as np
if SAVE_TRAIN:
    import csv
from operator import itemgetter
import random
import pyxel
import mofont

WIDTH, HEIGHT = 168, 140
BOARD_X, BOARD_Y = 31, 5
P1_X, P1_Y = 5, 5
P2_X, P2_Y = 142, 107
DROP_X, DROP_Y = 142, 5
MSG_X, MSG_Y, MSG_WIDTH, MSG_LINE = 30, 116, 108, 2
SPC, P1, P2, HOLE, OUT = 0, 1, 2, 3, 4
OPP = {P1:P2, P2:P1}
REPEAT_MOVE = 100
LEVEL_NAME = ('Lv.1', 'Lv.2', 'Lv.3', 'Lv.4', 'Lv.5', 'Lv.6', 'Boss', 'GOAT', 'Boss', 'GOAT', 'Auto', 'Auto')
RULE1_P1, RULE2_P1, RULE3_P1, AI1_P1, AI2_P1, AI3_P1 = 0,1,2,3,4,5 
AI_BOSS_P1, AI_AUTO_P1, RULE_BOSS_P1, RULE_AUTO_P1, AI_AUTO_P2, RULE_AUTO_P2 = 6,7,8,9,10,11
EVAL_BOARD = ( 0,  0,  0,  0, 0, 0,
               1,  2,  3,  2, 1, 0,
               2, 16,  9, 16, 2, 0,
               3,  9, 16,  9, 3, 0,
               2, 16,  9, 16, 2, 0,
               1,  2,  3,  2, 1, 0,
               0,  0,  0,  0, 0 )
DIR2DX = {-6: 0, -1:-1, 1:1, 6:0}
DIR2DY = {-6:-1, -1: 0, 1:0, 6:1}
ST_TITLE, ST_CHECKDROPPED, ST_SELECT, ST_PUT, ST_MOVE, ST_END = 101, 102, 103, 104, 105, 106

class OstMsg:
    MSG_GREET, MSG_WIN, MSG_LOSE, MSG_TIE_OPP, MSG_TIE_OWN, MSG_OWN, MSG_OWN_OPP, MSG_OPP, MSG_PREV = 0,1,2,3,4,5,6,7,8
    MSG_TEXT = (
            ('よろしくお願いします', 'お願いします', 'さあ始めましょう', '始めましょう', 'お手柔らかに'),
            ('私の勝ちですね', '楽しかったです', 'もう一度やりましょう', 'ありがとうございました'),
            ('私の負けですね', '負けました', '次は勝ちますよ', '次こそは勝ちたい'),
            ('追いつかれた', 'まだまだ勝負はこれから', '勝負はこれから', 'ミスしました', '失敗です'),
            ('追いつきました', 'これで１対１ですね', '取り返しました', 'この調子で続けます', '逆転しますよ'),
            ('まずは１つ目', 'いい調子です', '狙い通りです', '思い通りです', '勝利に近づきました', '順調です'),
            ('取って取られて', '取られるのは分かっています', '勝負は互角'), 
            ('取られても仕方ない', '取られてもあきらめません', '仕方ない', 'それはいい手ですね', 'あきらめません'),
            ('１つ前に戻せません',),
            )
    @classmethod
    def msg(cls, id):
        return cls.MSG_TEXT[id][random.randrange(len(cls.MSG_TEXT[id]))]

class Message:
    def __init__(self, x, y, width, line, frcol=7, bgcol=0, height=0):
        self.msg_x = x
        self.msg_y = y
        self.msg_width = width
        self.msg_line = line
        self.msg_frcol = frcol
        self.msg_bgcol = bgcol
        if height < line*8+3:
            self.msg_height = line*8+3
        else:
            self.msg_height = height
        self.msg_scrl = 0
        self.msg_col = 7
        self.clr()
    
    def clr(self):
        self.msg_str = ['']*self.msg_line

    def in_message(self, new_msg, col=7, keep=False):
        self.msg_col = col
        if keep or self.msg_str[0]=='':
            self.msg_str[0] = new_msg
        elif new_msg:
            for i in reversed(range(self.msg_line-1)):
                self.msg_str[i+1] = self.msg_str[i]
            self.msg_str[0] = new_msg
            self.msg_scrl = 8
    
    def draw_message(self):
        pyxel.rectb(self.msg_x, self.msg_y, self.msg_width, self.msg_height, self.msg_frcol)
        pyxel.rect(self.msg_x+1, self.msg_y+1, self.msg_width-2, self.msg_height-2, self.msg_bgcol)
        for i in range(1, self.msg_line):
            mofont.text(self.msg_x+2, self.msg_y+2+(self.msg_line-i-1)*8+self.msg_scrl, self.msg_str[i], 5)
        if self.msg_scrl==0:
            mofont.text(self.msg_x+2, self.msg_y+2+(self.msg_line-1)*8, self.msg_str[0], self.msg_col)

    def scroll(self):
        if self.msg_scrl > 0:
            self.msg_scrl -= 1
            return True
        return False

class Param:
    def __init__(self):
        self.rate           = 0
        self.bestmove       = 0
        self.dropopp        = 0
        self.nextdropopp    = 0
        self.nextnotdropown = 0

class App:
    def restart(self, msg_clr=True):
        if msg_clr:
            self.msg.clr()
        self.board = [OUT, OUT, OUT,  OUT, OUT, OUT,
                      P1,  P1,  P1,   P1,  P1,  OUT,
                      SPC, SPC, SPC,  SPC, SPC, OUT,
                      SPC, SPC, HOLE, SPC, SPC, OUT,
                      SPC, SPC, SPC,  SPC, SPC, OUT,
                      P2,  P2,  P2,   P2,  P2,  OUT,
                      OUT, OUT, OUT,  OUT, OUT]
        self.turn = random.choice((P1, P2))
        self.win = 0  # 0:Draw, 1:P1, 2:P2
        self.drop_piece = []
        self.select_pos, self.select_piece = 0, 0
        self.canmove_pos = []
        self.dir = 0
        self.move_pos, self.move_piece, self.move_count = [], [], 0
        self.prev1, self.prev2 = self.board[:], self.board[:]
        self.drop_own = []
        self.p1_move, self.p2_move = [], []
        self.p12_opt = [[0]*5, [0]*5]
        self.p12_select = [0, 0]
    
    def greet(self):
        if self.is_man_com or (self.is_com_com and not SAVE_TRAIN):
            txt = OstMsg.msg(OstMsg.MSG_GREET)
            self.msg.in_message(txt, 7)  # P1
        if self.is_com_com and not SAVE_TRAIN:
            txt = OstMsg.msg(OstMsg.MSG_GREET)
            txt = ' '*(2*(13-len(txt))) + txt
            self.msg.in_message(txt, 14)  # P2
        if self.is_man_com and self.level[0] in (AI_BOSS_P1, RULE_BOSS_P1):
            self.msg.in_message('     ボスとの対戦です', 10, True)
    
    def set_param(self):
        if self.level[0]==RULE1_P1:
            self.prm[0].bestmove, self.prm[0].dropopp, self.prm[0].nextdropopp, self.prm[0].nextnotdropown = 3, 100, 30, 30
        elif self.level[0]==RULE2_P1:
            self.prm[0].bestmove, self.prm[0].dropopp, self.prm[0].nextdropopp, self.prm[0].nextnotdropown = 2, 150, 60, 40
        elif self.level[0]==RULE3_P1:
            self.prm[0].bestmove, self.prm[0].dropopp, self.prm[0].nextdropopp, self.prm[0].nextnotdropown = 1, 200, 40, 60
        elif self.level[0]==AI1_P1:
            self.prm[0].rate = 0.05
        elif self.level[0]==AI2_P1:
            self.prm[0].rate = 0.03
        elif self.level[0]==AI3_P1:
            self.prm[0].rate = 0.01
        elif self.level[0] in (AI_BOSS_P1, AI_AUTO_P1):
            self.prm[0].rate = random.uniform(0, 0.02)
        elif self.level[0] in (RULE_BOSS_P1, RULE_AUTO_P1):
            self.prm[0].bestmove       = random.randrange(3)          # BestMove:1-3
            self.prm[0].dropopp        = random.randrange(30)*10+200  # DropOpp:
            self.prm[0].nextdropopp    = random.randrange(30)*10+10   # NextDropOpp
            self.prm[0].nextnotdropown = random.randrange(30)*10+10   # NextNotDropOwn
        
        if self.level[1]==AI_AUTO_P2:
            self.prm[1].rate = random.uniform(0, 0.02)
        elif self.level[1]==RULE_AUTO_P2:
            self.prm[1].bestmove       = random.randrange(3)          # BestMove:1-3
            self.prm[1].dropopp        = random.randrange(30)*10+200  # DropOpp:
            self.prm[1].nextdropopp    = random.randrange(30)*10+10   # NextDropOpp
            self.prm[1].nextnotdropown = random.randrange(30)*10+10   # NextNotDropOwn

    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title='Ostle')
        pyxel.load('assets/Ostle.pyxres')
        pyxel.mouse(True)
        if TENSORFLOW:
            self.model00_6 = tf.keras.models.load_model('models/model00_6.h5')
            self.model01_6 = tf.keras.models.load_model('models/model01_6.h5')
            self.model10_6 = tf.keras.models.load_model('models/model10_6.h5')
            self.model11_6 = tf.keras.models.load_model('models/model11_6.h5')
        self.is_man_man  = False
        self.is_man_com  = False
        self.is_com_com  = False
        self.is_continue = False
        self.is_quit     = False
        self.level = [RULE1_P1, RULE_AUTO_P2]
        self.msg = Message(MSG_X, MSG_Y, MSG_WIDTH, MSG_LINE)
        self.prm = [Param(), Param()]
        self.restart()
        self.status = ST_TITLE
        pyxel.run(self.update, self.draw)
    
    def mvpiece(self, bd, from_pos, to_pos):
        dir = to_pos - from_pos
        piece1 = bd[from_pos]
        bd[from_pos] = SPC
        pos = to_pos
        while P1 <= bd[pos] <= P2:
            piece2 = bd[pos]
            bd[pos] = piece1
            piece1 = piece2
            pos += dir
        if bd[pos] == SPC:
            bd[pos] = piece1
            piece1 = SPC
        return bd, piece1, pos-dir  # After_Board, Dropped_Piece, Dropped_Piece_Pos
    
    def mvhole(self, bd, from_pos, to_pos):
        bd[from_pos] = SPC
        bd[to_pos] = HOLE
        return bd
    
    def canmove(self, bd, turn):
        ret = []
        for i in range(6, 35):
            if bd[i]==turn:
                for diff in (-6, -1, 1, 6):
                    copy_bd = bd[:]
                    new_bd, piece, pos = self.mvpiece(copy_bd, i, i+diff)
                    if piece != turn:
                        ret.append([i, i+diff, piece, new_bd, pos])
            elif bd[i]==HOLE:
                for diff in (-6, -1, 1, 6):
                    if bd[i+diff] == SPC:
                        copy_bd = bd[:]
                        new_bd = self.mvhole(copy_bd, i, i+diff)
                        ret.append([i, i+diff, 0, new_bd, 0])
        for i in range(len(ret)):
            if self.prev2==ret[i][3]:  # ひとつ前の盤面に戻すのは禁止
                del ret[i]
                break
        return ret  # From_Piece_Pos, To_Piece_Pos, Dropped_Piece, New_Board[], Dropped_Piece_Pos

    def append_move(self, bd, turn):
        if turn==P1:
            self.p1_move.append(list(itemgetter(6,7,8,9,10, 12,13,14,15,16, 18,19,20,21,22, 
                    24,25,26,27,28, 30,31,32,33,34)(bd)))
        elif turn==P2:
            self.p2_move.append(list(itemgetter(6,7,8,9,10, 12,13,14,15,16, 18,19,20,21,22, 
                    24,25,26,27,28, 30,31,32,33,34)(bd)))

    def flip(self, src_move):
        ret_move = src_move[:]
        for y in range(5):
            for x in range(5):
                ret_move[y*5+(4-x)] = src_move[y*5+x]
        return ret_move

    def rot(self, src_move):
        ret_move = src_move[:]
        for y in range(5):
            for x in range(5):
                ret_move[(4-x)*5+y] = src_move[y*5+x]
        return ret_move

    def flush_move(self, save_last_move, num_drop, win23, win1):
        write_p1_move = []
        #print('P1', list(range(max(0, len(self.p1_move)-save_last_move) ,len(self.p1_move))))
        for y in range(max(0, len(self.p1_move)-save_last_move) ,len(self.p1_move)):
            one_move = self.p1_move[y][:]
            one_move.append(1 if win23==P1 else 0)
            
            write_p1_move.append(one_move)
            write_p1_move.append(self.flip(one_move))
            
            one_move = self.rot(one_move)
            write_p1_move.append(one_move)
            write_p1_move.append(self.flip(one_move))
            
            one_move = self.rot(one_move)
            write_p1_move.append(one_move)
            write_p1_move.append(self.flip(one_move))
            
            one_move = self.rot(one_move)
            write_p1_move.append(one_move)
            write_p1_move.append(self.flip(one_move))
            
        write_p2_move = []
        #print('P2', list(range(max(0, len(self.p2_move)-save_last_move) ,len(self.p2_move))))
        for y in range(max(0, len(self.p2_move)-save_last_move) ,len(self.p2_move)):
            one_move = [2 if v==1 else 1 if v==2 else v for v in self.p2_move[y]]  # 1<->2
            one_move.append(1 if win23==P2 else 0)
            
            write_p2_move.append(one_move)
            write_p2_move.append(self.flip(one_move))
            
            one_move = self.rot(one_move)
            write_p2_move.append(one_move)
            write_p2_move.append(self.flip(one_move))
            
            one_move = self.rot(one_move)
            write_p2_move.append(one_move)
            write_p2_move.append(self.flip(one_move))
            
            one_move = self.rot(one_move)
            write_p2_move.append(one_move)
            write_p2_move.append(self.flip(one_move))
        
        fname1 = f'moves/00_{save_last_move}.txt'
        fname2 = f'moves/00_{save_last_move}.txt'
        if num_drop == 2:
            fname1 = f'moves/10_{save_last_move}.txt' if win1 == P1 else f'moves/01_{save_last_move}.txt'
            fname2 = f'moves/01_{save_last_move}.txt' if win1 == P1 else f'moves/10_{save_last_move}.txt'
        elif num_drop == 3:
            fname1 = f'moves/11_{save_last_move}.txt'
            fname2 = f'moves/11_{save_last_move}.txt'
        with open(fname1, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(write_p1_move)
        with open(fname2, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(write_p2_move)
    
    def update(self):
        if self.msg.scroll():
            return
        if self.is_com_com and pyxel.btnr(pyxel.MOUSE_BUTTON_RIGHT):  # RIGHT_BUTTON_UP
            self.restart()
            self.status = ST_TITLE
        elif self.status==ST_TITLE:
            self.is_man_man = (BOARD_X+12<pyxel.mouse_x<BOARD_X+94 and BOARD_Y+34<pyxel.mouse_y<BOARD_Y+44)
            self.is_man_com = (BOARD_X+12<pyxel.mouse_x<BOARD_X+94 and BOARD_Y+47<pyxel.mouse_y<BOARD_Y+57)
            self.is_com_com = (BOARD_X+12<pyxel.mouse_x<BOARD_X+94 and BOARD_Y+60<pyxel.mouse_y<BOARD_Y+70)
            self.level = [RULE1_P1, RULE_AUTO_P2]
            if self.is_com_com:
                if TENSORFLOW:
                    #self.level = [random.choice((AI_AUTO_P1, RULE_AUTO_P1)), AI_AUTO_P2]
                    self.level = [AI_AUTO_P1, random.choice((AI_AUTO_P2, RULE_AUTO_P2))]
                else:
                    self.level = [RULE_AUTO_P1, RULE_AUTO_P2]
            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):  # LEFT_UP
                if self.is_man_man or self.is_man_com or self.is_com_com:
                    self.set_param()
                    self.greet()
                    self.status = ST_CHECKDROPPED
        elif self.status==ST_CHECKDROPPED:  # そのままでは落とされる駒の確認
            next_move = self.canmove(self.board, OPP[self.turn])  # 動かせる全ての手
            self.drop_own = []
            for i in range(len(next_move)):
                if next_move[i][2]:  # 落とされる駒
                    self.drop_own.append(next_move[i][4])  # そのままでは落とされる駒の位置
            self.status = ST_SELECT
        elif self.status==ST_SELECT:
            if self.is_com_com or (self.turn==P1 and self.is_man_com):
                score_11 = (len(self.drop_piece)==2)
                score_10 = (len(self.drop_piece)==1 and OPP[self.turn] in self.drop_piece)
                score_01 = (len(self.drop_piece)==1 and     self.turn  in self.drop_piece)
                score_00 = (len(self.drop_piece)==0)
                next_move = self.canmove(self.board, self.turn)  # 動かせる全ての手
                num_next_move = len(next_move)
                eval_move              = [0]*num_next_move  # 総合評価
                eval_drop_opp          = [0]*num_next_move  # 相手の駒を落とせる
                eval_next_drop_opp     = [0]*num_next_move  # 次に相手の駒を落とせる
                eval_next_drop_own     = [0]*num_next_move  # 次に自分の駒が落とされる
                eval_next_not_drop_own = [0]*num_next_move  # 次に自分の駒が落とされない
                eval_pos               = [0]*num_next_move  # 駒の位置
                for i in range(num_next_move):
                    if next_move[i][2]:
                        eval_drop_opp[i] += 1
                    next2own = self.canmove(next_move[i][3], self.turn)
                    for j in range(len(next2own)):
                        if next2own[j][2]:
                            eval_next_drop_opp[i] += 1  # 次に相手の駒を落とせる
                    next2opp = self.canmove(next_move[i][3], OPP[self.turn])
                    for j in range(len(next2opp)):
                        if next2opp[j][2]:
                            eval_next_drop_own[i] += 1  # 次に自分の駒が落とされる
                    for j in [x for x, e in enumerate(next_move[i][3]) if e==self.turn]:
                        eval_pos[i] += EVAL_BOARD[j]
                        for k in (j-6, j-1, j+1, j+6):
                            if next_move[i][3][k]==self.turn:  # 隣が自分の駒
                                eval_pos[i] += 1
                    hole_pos = next_move[i][3].index(HOLE)
                    for j in (hole_pos-6, hole_pos-1, hole_pos+1, hole_pos+6):
                        if next_move[i][3][j]==self.turn:
                            pass
                        elif next_move[i][3][j]==OPP[self.turn]:
                            eval_pos[i] += 2
                        else:
                            eval_pos[i] += 1
                
                if self.level[self.turn-1] in (AI1_P1, AI2_P1, AI3_P1, AI_BOSS_P1, AI_AUTO_P1, AI_AUTO_P2):
                    bd24 = []
                    for i in range(num_next_move):
                        bd = list(itemgetter(6,7,8,9,10, 12,13,14,15,16, 18,19,20,21,22, 
                                24,25,26,27,28, 30,31,32,33,34)(next_move[i][3]))
                        if self.turn==P2:
                            bd = [2 if v==1 else 1 if v==2 else v for v in bd]  # 1<->2
                        bd24.append(bd)
                    for _ in range(24-num_next_move):
                        bd24.append([0]*25)
                    if score_00:
                        prob24 = self.model00_6.predict_on_batch(np.array(bd24))
                    elif score_01:
                        prob24 = self.model01_6.predict_on_batch(np.array(bd24))
                    elif score_10:
                        prob24 = self.model10_6.predict_on_batch(np.array(bd24))
                    else:
                        prob24 = self.model11_6.predict_on_batch(np.array(bd24))
                    eval24 = [p[0] for p in prob24]
                    eval_move = eval24[0:num_next_move]
                else:
                    for i in range(num_next_move):
                        eval_next_not_drop_own[i] = max(eval_next_drop_own)-eval_next_drop_own[i]  # 次に落とされない
                        eval_move[i] += eval_drop_opp[i]         *self.prm[self.turn-1].dropopp
                        eval_move[i] += eval_next_drop_opp[i]    *self.prm[self.turn-1].nextdropopp
                        eval_move[i] += eval_next_not_drop_own[i]*self.prm[self.turn-1].nextnotdropown
                        eval_move[i] += eval_pos[i]
                self.p12_opt[self.turn-1] = sorted(eval_move, reverse=True)
                
                if (score_11 or score_10) and max(eval_drop_opp):  # 落とせる【勝ち】
                    if not (self.is_com_com and SAVE_TRAIN):
                        txt = OstMsg.msg(OstMsg.MSG_WIN)
                        spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                        txt = spc + txt
                        self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                    for i in range(num_next_move):
                        if not eval_drop_opp[i]:
                            eval_move[i] = 0
                elif (score_11 or score_01) and min(eval_next_drop_own):  # 必ず落される【負け】
                    if not (self.is_com_com and SAVE_TRAIN):
                        txt = OstMsg.msg(OstMsg.MSG_LOSE)
                        spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                        txt = spc + txt
                        self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                elif score_11:
                    for i in range(num_next_move):  # 次に落されない【絶対条件】
                        if eval_next_drop_own[i]:
                            eval_move[i] = 0
                elif score_10:
                    if not min(eval_next_drop_own):  # 次に落されない
                        for i in range(num_next_move):
                            if eval_next_drop_own[i]:
                                eval_move[i] = 0
                    else:
                        if not (self.is_com_com and SAVE_TRAIN):
                            txt = OstMsg.msg(OstMsg.MSG_TIE_OPP)
                            spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                            txt = spc + txt
                            self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                elif score_01:
                    for i in range(num_next_move):  # 次に落されない【絶対条件】
                        if eval_next_drop_own[i]:
                            eval_move[i] = 0
                            eval_drop_opp[i] = 0
                    if max(eval_drop_opp):  # 落とせる
                        if not (self.is_com_com and SAVE_TRAIN):
                            txt = OstMsg.msg(OstMsg.MSG_TIE_OWN)
                            spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                            txt = spc + txt
                            self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                        for i in range(num_next_move):
                            if eval_drop_opp[i]==0:
                                eval_move[i] = 0
                elif score_00:
                    if max(eval_drop_opp):  # 落とせる
                        for i in range(num_next_move):
                            if eval_drop_opp[i]==0:
                                eval_move[i] = 0
                                eval_next_drop_own[i] = 1
                        if not min(eval_next_drop_own):  # 次に落されない
                            if not (self.is_com_com and SAVE_TRAIN):
                                txt = OstMsg.msg(OstMsg.MSG_OWN)
                                spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                                txt = spc + txt
                                self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                            for i in range(num_next_move):
                                if eval_next_drop_own[i]:
                                    eval_move[i] = 0
                        else:  # 次に落とされる
                            if not (self.is_com_com and SAVE_TRAIN):
                                txt = OstMsg.msg(OstMsg.MSG_OWN_OPP)
                                spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                                txt = spc + txt
                                self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                    else:  # 落とせない
                        if not min(eval_next_drop_own):  # 次に落されない
                            for i in range(num_next_move):
                                if eval_next_drop_own[i]:
                                    eval_move[i] = 0
                        else:  # 次に落とされる
                            if not (self.is_com_com and SAVE_TRAIN):
                                txt = OstMsg.msg(OstMsg.MSG_OPP)
                                spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                                txt = spc + txt
                                self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                
                add_rate = 0
                bd = list(itemgetter(6,7,8,9,10, 12,13,14,15,16, 18,19,20,21,22, 24,25,26,27,28, 
                        30,31,32,33,34)(next_move[eval_move.index(max(eval_move))][3]))
                if self.turn==P1 and self.p1_move.count(bd) > 0:  # P1振り子防止
                    if self.level[0] in (AI1_P1, AI2_P1, AI3_P1, AI_BOSS_P1, AI_AUTO_P1):
                        add_rate = self.p1_move.count(bd)*0.1
                    else:
                        add_rate = self.p1_move.count(bd)
                    #print(f'P1:{self.p1_move.count(bd):2}/{len(self.p1_move):2}, Add:{add_rate:.1f}')
                if self.turn==P2 and self.p2_move.count(bd) > 0:  # P2振り子防止
                    if self.level[1]==AI_AUTO_P2:
                        add_rate = self.p2_move.count(bd)*0.1
                    else:
                        add_rate = self.p2_move.count(bd)
                    #print(f'P2:{self.p2_move.count(bd):2}/{len(self.p2_move):2}, Add:{add_rate:.1f}')
                
                if self.level[self.turn-1] in (AI1_P1, AI2_P1, AI3_P1, AI_BOSS_P1, AI_AUTO_P1, AI_AUTO_P2):
                    best_move = sorted(eval_move, reverse=True)[0]
                    for i in range(num_next_move):
                        if eval_move[i] < best_move-(self.prm[self.turn-1].rate+add_rate):
                            eval_move[i] = 0
                else:
                    thrshld_move = sorted(eval_move, reverse=True)[min(self.prm[self.turn-1].bestmove+add_rate, len(eval_move)-1)]
                    for i in range(num_next_move):
                        if eval_move[i] < thrshld_move:
                            eval_move[i] = 0
                
                com_move = random.choices(list(range(num_next_move)), weights=eval_move)[0]
                self.p12_select[self.turn-1] = eval_move[com_move]
                
                self.select_pos = next_move[com_move][0]
                self.select_piece = self.board[self.select_pos]
                put_pos = next_move[com_move][1]
                
                self.dir = put_pos - self.select_pos
                pos = self.select_pos
                self.move_pos.clear()
                self.move_piece.clear()
                if P1 <= self.select_piece <= P2:
                    while P1 <= self.board[pos]  <= P2:
                        self.move_pos.append(pos)
                        self.move_piece.append(self.board[pos])
                        self.board[pos] = SPC
                        pos += self.dir
                else:
                    self.move_pos.append(pos)
                    self.move_piece.append(self.board[pos])
                    self.board[pos] = SPC
                self.move_count = 0
                self.status = ST_MOVE
                
            elif pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):  # LEFT_BUTTON_UP
                select_x = (pyxel.mouse_x-BOARD_X)//21
                select_y = (pyxel.mouse_y-BOARD_Y)//21
                if 0 <= select_x < 5 and 0 <= select_y < 5:
                    self.select_pos = select_y*6+select_x+6
                    self.select_piece = self.board[self.select_pos]
                    if self.select_piece==HOLE or self.turn==self.select_piece:
                        self.canmove_pos.clear()
                        if self.select_piece==HOLE:
                            for diff in (-6, -1, 1, 6):
                                if self.board[self.select_pos+diff]==SPC:
                                    self.canmove_pos.append(self.select_pos+diff)
                        else:
                            for diff in (-6, -1, 1, 6):
                                if self.board[self.select_pos+diff]!=OUT:
                                    self.canmove_pos.append(self.select_pos+diff)
                        self.status = ST_PUT
                    else:
                        self.select_pos = 0
                        self.select_piece = SPC
        elif self.status==ST_PUT:
            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):  # LEFT_BUTTON_UP
                select_x = (pyxel.mouse_x-BOARD_X)//21
                select_y = (pyxel.mouse_y-BOARD_Y)//21
                put_pos = select_y*6+select_x+6
                if put_pos in self.canmove_pos:
                    self.dir = put_pos - self.select_pos
                    pos = self.select_pos
                    self.move_pos.clear()
                    self.move_piece.clear()
                    if P1 <= self.select_piece <= P2:
                        while P1 <= self.board[pos] <= P2:
                            self.move_pos.append(pos)
                            self.move_piece.append(self.board[pos])
                            self.board[pos] = SPC
                            pos += self.dir
                    else:
                        self.move_pos.append(pos)
                        self.move_piece.append(self.board[pos])
                        self.board[pos] = SPC
                    self.move_count = 0
                    self.status = ST_MOVE
                else:
                    self.select_pos = 0
                    self.status = ST_CHECKDROPPED
        elif self.status==ST_MOVE:
            self.move_count += 2
            if self.move_count > 21 or (self.is_com_com and SAVE_TRAIN):
                drop_num = len(self.drop_piece)
                for i in reversed(range(len(self.move_pos))):
                    if self.board[self.move_pos[i]+self.dir]==SPC:
                        self.board[self.move_pos[i]+self.dir] = self.move_piece[i]
                    elif HOLE <= self.board[self.move_pos[i]+self.dir] <= OUT:
                        self.drop_piece.append(self.move_piece[i])
                if self.prev2==self.board:  # ひとつ前の盤面に戻すのは禁止
                    self.board = self.prev1[:]
                    txt = OstMsg.msg(OstMsg.MSG_PREV)
                    spc = ' ' * (0 if self.turn==P1 else 2*(13-len(txt)))
                    txt = spc + txt
                    self.msg.in_message(txt, 7 if self.turn==P1 else 14)
                else:
                    self.prev2 = self.prev1[:]
                    self.prev1 = self.board[:]
                    self.turn = OPP[self.turn]
                    if len(self.drop_piece)>=2 and self.drop_piece[0]==self.drop_piece[1]:
                        self.win = OPP[self.drop_piece[0]]
                    if len(self.drop_piece)==3:
                        if self.drop_piece[0]==self.drop_piece[2]:
                            self.win = OPP[self.drop_piece[0]]
                        else:
                            self.win = OPP[self.drop_piece[1]]
                    if len(self.drop_piece)==drop_num+1:
                        if SAVE_TRAIN:
                            self.flush_move(6, drop_num+1, OPP[self.drop_piece[drop_num]], OPP[self.drop_piece[0]])
                        self.p1_move = []
                        self.p2_move = []
                    self.append_move(self.board, OPP[self.turn])
                self.select_pos = 0
                self.status = ST_CHECKDROPPED
                
                if self.win > 0 or len(self.p1_move)+len(self.p2_move)>=REPEAT_MOVE:
                    self.status = ST_END
                elif not (self.is_com_com and SAVE_TRAIN) and len(self.p1_move)+len(self.p2_move)==REPEAT_MOVE-9:
                    self.msg.in_message('あと９手で落ちないと引分け', 15)
                elif not (self.is_com_com and SAVE_TRAIN) and len(self.p1_move)+len(self.p2_move)==REPEAT_MOVE-3:
                    self.msg.in_message('あと３手で落ちないと引分け', 15)

        elif self.status==ST_END:
            if self.is_com_com and SAVE_TRAIN:
                if self.win==P1:
                    self.msg.in_message('勝ち', 7)
                elif self.win==P2:
                    self.msg.in_message('                      勝ち', 14)
                else:
                    self.msg.in_message('         引き分け', 15)
                self.restart(msg_clr=False)
                if TENSORFLOW:
                    #self.level = [random.choice((AI_AUTO_P1, RULE_AUTO_P1)), AI_AUTO_P2]
                    self.level = [AI_AUTO_P1, random.choice((AI_AUTO_P2, RULE_AUTO_P2))]
                self.set_param()
                self.status = ST_CHECKDROPPED
            else:
                self.is_continue = (BOARD_X+12<pyxel.mouse_x<BOARD_X+94 and BOARD_Y+65<pyxel.mouse_y<BOARD_Y+75)
                self.is_quit     = (BOARD_X+12<pyxel.mouse_x<BOARD_X+94 and BOARD_Y+77<pyxel.mouse_y<BOARD_Y+87)
                if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT) and (self.is_continue or self.is_quit):  # LEFT_UP
                    if not self.is_com_com and self.win==P2:
                        if TENSORFLOW:
                            if self.level[0] < AI_AUTO_P1:
                                self.level[0] += 1
                        else:
                            if self.level[0] < RULE3_P1:
                                self.level[0] += 1
                            elif self.level[0]==RULE3_P1:
                                self.level[0] = RULE_BOSS_P1
                            elif self.level[0]==RULE_BOSS_P1:
                                self.level[0] = RULE_AUTO_P1
                    if self.is_continue:
                        if self.is_man_com and self.win==P1:
                            self.level[0] = RULE1_P1
                        self.restart()
                        self.greet()
                        self.set_param()
                        self.status = ST_CHECKDROPPED
                    else:
                        self.restart()
                        self.status = ST_TITLE
    
    def draw_board(self):
        pyxel.rect(BOARD_X, BOARD_Y, 21*5, 21*5, 5)
        for i in range(6):
            pyxel.line(BOARD_X     , BOARD_Y+i*21, BOARD_X+5*21, BOARD_Y+i*21, 0)
            pyxel.line(BOARD_X+i*21, BOARD_Y,      BOARD_X+i*21, BOARD_Y+5*21, 0)
    
    def draw_piece(self):
        for i in range(5):
            for j in range(5):
                p = self.board[i*6+j+6]
                if self.board[i*6+j+6] == HOLE:
                    pyxel.blt(BOARD_X+3+j*21, BOARD_Y+3+i*21, 0, 16, 0, 16, 16, 1)
                if self.board[i*6+j+6] == P1 or self.board[i*6+j+6] == P2:
                    pyxel.blt(BOARD_X+3+j*21, BOARD_Y+3+i*21, 0, 16+self.board[i*6+j+6]*16, 0, 16, 16, 1)

    def draw_rnd_param_p1(self):
        pyxel.text(P1_X-1 , P1_Y+29, f'{self.prm[0].bestmove+1:3}', 7)
        pyxel.text(P1_X+12, P1_Y+29, f'{self.prm[0].dropopp:3}', 7)
        pyxel.text(P1_X-1 , P1_Y+35, f'{self.prm[0].nextdropopp:3}', 7)
        pyxel.text(P1_X+12, P1_Y+35, f'{self.prm[0].nextnotdropown:3}', 7)
        for i in range(min(4, len(self.p12_opt[0]))):
            pyxel.text(P1_X, P1_Y+43+i*6, f'{self.p12_opt[0][i]:6}', 7)
        pyxel.text(P1_X, P1_Y+69, f'{self.p12_select[0]:6}', 10 if self.p12_select[0]==self.p12_opt[0][0] else 1)
    
    def draw_rnd_param_p2(self):
        pyxel.text(P2_X-1 , P2_Y-36, f'{self.prm[1].bestmove+1:3}', 14)
        pyxel.text(P2_X+12, P2_Y-36, f'{self.prm[1].dropopp:3}', 14)
        pyxel.text(P2_X-1 , P2_Y-30, f'{self.prm[1].nextdropopp:3}', 14)
        pyxel.text(P2_X+12, P2_Y-30, f'{self.prm[1].nextnotdropown:3}', 14)
        for i in range(min(2, len(self.p12_opt[1]))):
            pyxel.text(P2_X, P2_Y-22+i*6, f'{self.p12_opt[1][i]:6}', 14)
        pyxel.text(P2_X, P2_Y-8, f'{self.p12_select[1]:6}', 10 if self.p12_select[1]==self.p12_opt[1][0] else 1)
    
    def draw_ai_param_p1(self):
        pyxel.text(P1_X-1, P1_Y+30, f'{self.prm[0].rate:.4f}', 7)
        for i in range(min(5, len(self.p12_opt[0]))):
            pyxel.text(P1_X-1, P1_Y+38+i*6, f'{self.p12_opt[0][i]:.4f}', 7)
        pyxel.text(P1_X-1, P1_Y+40+5*6, f'{self.p12_select[0]:.4f}', 
                10 if self.p12_select[0]==self.p12_opt[0][0] else 1)
    
    def draw_ai_param_p2(self):
        pyxel.text(P2_X-1, P2_Y-36, f'{self.prm[1].rate:.4f}', 14)
        for i in range(min(3, len(self.p12_opt[1]))):
            pyxel.text(P2_X-1, P2_Y-28+i*6, f'{self.p12_opt[1][i]:.4f}', 14)
        pyxel.text(P2_X-1, P2_Y-8, f'{self.p12_select[1]:.4f}', 10 if self.p12_select[1]==self.p12_opt[1][0] else 1)
    
    def draw(self):
        pyxel.cls(3)
        self.draw_board()
        
        pyxel.rectb(DROP_X, DROP_Y, 21, 63, 15)
        pyxel.text(DROP_X+3, DROP_Y+3, 'Drop', 15)
        for i, piece in enumerate(self.drop_piece):
            pyxel.blt(DROP_X+2, DROP_Y+9+17*i, 0, 16+piece*16, 0, 16, 16, 1)
        
        pyxel.rectb(P1_X, P1_Y, 21, 28, 7)
        if self.win==P1:
            mofont.text(P1_X+3, P1_Y+2, '勝ち', pyxel.frame_count//4%4+3)
        elif self.status==ST_END and self.win==0:
            pyxel.text(P1_X+3, P1_Y+2, 'Draw', 10)
        else:
            if self.turn==P1 and not self.is_com_com:
                pyxel.text(P1_X+3, P1_Y+3, 'Turn', 7)
            else:
                pyxel.text(P1_X+3, P1_Y+3, ' P1' if self.is_man_man else LEVEL_NAME[self.level[0]], 7)
        pyxel.blt(P1_X+2, P1_Y+10, 0, 32 if self.is_man_man else self.level[0]*16, 
                0 if self.is_man_man else 16, -16, 16, 1)
        
        pyxel.rectb(P2_X, P2_Y, 21, 28, 14)
        if self.win==P2:
            mofont.text(P2_X+3, P2_Y+2, '勝ち', pyxel.frame_count//4%4+3)
        elif self.status==ST_END and self.win==0:
            pyxel.text(P2_X+3, P2_Y+2, 'Draw', 10)
        elif self.turn==P2 and not self.is_com_com:
            pyxel.text(P2_X+3, P2_Y+3, 'Turn', 14)
        elif self.is_man_man:
            pyxel.text(P2_X+7, P2_Y+3, 'P2', 14)
        elif self.is_com_com:
            pyxel.text(P2_X+3, P2_Y+3, LEVEL_NAME[self.level[1]], 14)
        else:
            pyxel.text(P2_X+5, P2_Y+3, 'You', 14)
        pyxel.blt(P2_X+2, P2_Y+10, 0, self.level[1]*16 if self.is_com_com else 48, 
                16 if self.is_com_com else 0, 16, 16, 1)
        
        if (self.is_man_com or self.is_com_com) and not self.status==ST_TITLE and not RELEASE_CANDIDATE:
            if self.level[0] in (AI1_P1, AI2_P1, AI3_P1, AI_BOSS_P1, AI_AUTO_P1):
                self.draw_ai_param_p1()
            else:
                self.draw_rnd_param_p1()
        if self.is_com_com and not self.status==ST_TITLE and not RELEASE_CANDIDATE:
            if self.level[1]==AI_AUTO_P2:
                self.draw_ai_param_p2()
            else:
                self.draw_rnd_param_p2()

        self.msg.draw_message()

        if self.status==ST_SELECT and (self.is_man_man or (self.turn==P2 and self.is_man_com)):
            if self.select_pos:
                pyxel.rect(BOARD_X+((self.select_pos-6)%6)*21+1, BOARD_Y+((self.select_pos-6)//6)*21+1, 20, 20, 12)
            else:
                for i in range(6, 35):
                    if self.board[i]==HOLE or self.turn==self.board[i]:
                        if i in self.drop_own:
                            pyxel.rect(BOARD_X+((i-6)%6)*21+1, BOARD_Y+((i-6)//6)*21+1, 20, 20, 10)
                        else:
                            pyxel.rect(BOARD_X+((i-6)%6)*21+1, BOARD_Y+((i-6)//6)*21+1, 20, 20, 12)
        
        if self.status==ST_PUT and (self.is_man_man or (self.turn==P2 and self.is_man_com)):
            pyxel.rect(BOARD_X+((self.select_pos-6)%6)*21+1, BOARD_Y+((self.select_pos-6)//6)*21+1, 20, 20, 12)
            for i in self.canmove_pos:
                pyxel.rect(BOARD_X+((i-6)%6)*21+1, BOARD_Y+((i-6)//6)*21+1, 20, 20, 9)
        
        self.draw_piece()
        
        if self.status==ST_TITLE:
            man_man = ' ひと  対  ひと'
            man_com = 'ＣＰＵ 対 あなた'
            com_com = 'ＣＰＵ 対 ＣＰＵ'
            for y in range(3):
                for x in range(3):
                    mofont.text(BOARD_X+20+x, BOARD_Y+35+y, man_man, 0)
                    mofont.text(BOARD_X+20+x, BOARD_Y+48+y, man_com, 0)
                    mofont.text(BOARD_X+20+x, BOARD_Y+61+y, com_com, 0)
            mofont.text(BOARD_X+21, BOARD_Y+36, man_man, 7 if self.is_man_man else 1)
            mofont.text(BOARD_X+21, BOARD_Y+49, man_com, 7 if self.is_man_com else 1)
            mofont.text(BOARD_X+21, BOARD_Y+62, com_com, 7 if self.is_com_com else 1)
            
        elif self.status==ST_END and not (self.is_com_com and SAVE_TRAIN):
            if self.is_man_com and self.win==P1:
                msg_result = 'ＣＰＵの勝ち!'
                for y in range(3):
                    for x in range(3):
                        mofont.text(BOARD_X+25+x, BOARD_Y+49+y, msg_result, 0)
                mofont.text(BOARD_X+26, BOARD_Y+50, msg_result, 10)
            elif self.is_man_com and self.win==P2:
                if self.level[0] in (AI_BOSS_P1, RULE_BOSS_P1):
                    msg_result1 = 'おめでとう!!'
                    msg_result2 = 'ボスに勝利しました!!'
                else:
                    msg_result1 = msg_result2 = '' 
                msg_result3 = 'あなたの勝ち!!'
                for y in range(3):
                    for x in range(3):
                        mofont.text(BOARD_X+28+x, BOARD_Y+23+y, msg_result1, 0)
                        mofont.text(BOARD_X+12+x, BOARD_Y+36+y, msg_result2, 0)
                        mofont.text(BOARD_X+25+x, BOARD_Y+49+y, msg_result3, 0)
                mofont.text(BOARD_X+29, BOARD_Y+24, msg_result1, 10)
                mofont.text(BOARD_X+13, BOARD_Y+37, msg_result2, 10)
                mofont.text(BOARD_X+26, BOARD_Y+50, msg_result3, 10)

            elif self.is_man_com:
                msg_result = '引き分け'
                for y in range(3):
                    for x in range(3):
                        mofont.text(BOARD_X+36+x, BOARD_Y+49+y, msg_result, 0)
                mofont.text(BOARD_X+37, BOARD_Y+50, msg_result, 10)

            if self.is_man_com and self.win==P1:  # Computer Win
                msg_continue = 'やり直す'  # restart
            else:
                msg_continue = ' 続ける'  # continue
            msg_quit = 'やめる'  # quit
            for y in range(3):
                for x in range(3):
                    mofont.text(BOARD_X+36+x, BOARD_Y+66+y, msg_continue, 0)
                    mofont.text(BOARD_X+40+x, BOARD_Y+78+y, msg_quit, 0)
            mofont.text(BOARD_X+37, BOARD_Y+67, msg_continue, 7 if self.is_continue else 1)
            mofont.text(BOARD_X+41, BOARD_Y+79, msg_quit, 7 if self.is_quit else 1)
        
        if self.status==ST_MOVE:
            dx = DIR2DX[self.dir]
            dy = DIR2DY[self.dir]
            for i in range(len(self.move_pos)):
                if self.move_piece[i]==HOLE:
                    pyxel.blt(BOARD_X+((self.move_pos[i]-6)%6)*21+3+dx*self.move_count, \
                            BOARD_Y+((self.move_pos[i]-6)//6)*21+3+dy*self.move_count, 0, 16, 0, 16, 16, 1)
                elif self.move_piece[i]==P1 or self.move_piece[i]==P2:
                    pyxel.blt(BOARD_X+((self.move_pos[i]-6)%6)*21+3+dx*self.move_count, \
                            BOARD_Y+((self.move_pos[i]-6)//6)*21+3+dy*self.move_count, 0, 16+self.move_piece[i]*16, 0, 16, 16, 1)

App()
