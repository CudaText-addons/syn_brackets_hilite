import os
import shutil
from sw import *
from .proc_brackets import *
from .proc_color import *

NAME_INI = 'syn_brackets_hilite.ini'
fn_config = os.path.join(app_ini_dir(), NAME_INI)
fn_config_def = os.path.join(os.path.dirname(__file__), NAME_INI)

if not os.path.isfile(fn_config) and os.path.isfile(fn_config_def):
    shutil.copyfile(fn_config_def, fn_config)

if app_api_version()<'1.0.158':
    msg_box(MSG_ERROR, 'Brackets Hilite plugin needs newer app version')
MARKTAG = 104 #uniq for all search-marks plugins


def log(s):
    pass
    #print('BracketHilite: '+s)

prev_lexer = None
prev_chars = ''

def get_chars():
    global prev_lexer
    global prev_chars

    lex = ed.get_prop(PROP_LEXER_CARET)
    if lex==prev_lexer:
        return prev_chars

    val_def = ini_read(fn_config, 'brackets', 'default', '')
    if not lex:
        val = val_def
    else:
        val = ini_read(fn_config, 'brackets', lex, val_def)

    prev_lexer = lex
    prev_chars = val

    log('chars for "%s": "%s"'%(lex, val))
    return val


class Command:
    entered=False
    allow_with_sel=True
    max_file_size=1

    def __init__(self):
        self.allow_with_sel = ini_read(fn_config, 'op', 'allow_with_selection', '1')=='1'
        self.max_file_size = int(ini_read(fn_config, 'op', 'max_file_size_mb', '1'))


    def config(self):
        if os.path.isfile(fn_config):
            file_open(fn_config)


    def on_caret_move(self, ed_self):
        if self.entered: return log('already in on_caret_move')

        num = ed.get_text_len() // (1024*1024)
        if num>self.max_file_size:
            return log('too big text: %d mb' % num)

        x, y = ed.get_caret_xy()
        npos, nlen = ed.get_sel()
        if not self.allow_with_sel:
            if nlen>0: return log('not allowed with sel')

        #clear prev marks
        ed.marks(MARKS_DELETE_BY_TAG, 0, 0, MARKTAG)

        chars = get_chars()
        if not chars: return log('no bracket-chars set')

        res = find_matching_bracket(ed, x, y, chars)
        if res is None:
            return log('cannot find bracket')
        x1, y1 = res
        npos2 = ed.xy_pos(x1, y1)

        ed.marks(MARKS_ADD, npos, 1, MARKTAG)
        ed.marks(MARKS_ADD, npos2, 1, MARKTAG)


    def jump(self):
        self.do_find(True)
    def select(self):
        self.do_find(False)
    def select_in(self):
        self.do_find(False, True)


    def do_find(self, is_jump, select_inside=False):
        x, y = ed.get_caret_xy()
        npos, nlen = ed.get_sel()
        if nlen>0:
            msg_status('Cannot go to bracket if selection')
            return

        chars = get_chars()
        if not chars: return

        res = find_matching_bracket(ed, x, y, chars)
        if res is None:
            msg_status('Cannot find pair bracket')
            return
        x1, y1 = res

        if is_jump:
            ed.set_caret_xy(x1, y1)
            msg_status('Go to pair bracket')
        else:
            #select from (x,y) to (x1,y1)
            sel_delta = -1 if select_inside else 0
            if (y1>y) or ((y1==y) and (x1>x)):
                #sel down
                n1 = ed.xy_pos(x1+1+sel_delta, y1)
                n2 = ed.xy_pos(x-sel_delta, y)
                ed.set_sel(n1, n2-n1)
            else:
                #sel up
                n1 = ed.xy_pos(x1-sel_delta, y1)
                n2 = ed.xy_pos(x+1+sel_delta, y)
                ed.set_sel(n1, n2-n1)
            msg_status('Selected to pair bracket')
