#!/usr/bin/env python3
import sys
import os
import re

debug = False


def main():
  filename, tapefilename, watch, step = procArg()
  prog = readRAMfile(filename)
  tape = readTapefile(tapefilename)
  run(prog, tape, watch, step)


def procArg():
  global debug

  filename = None
  tapefilename = None
  watch = False
  step = False
  i = 1
  while(i < len(sys.argv)):
    if sys.argv[i].startswith('-'):
      if len(sys.argv[i][1:]) == 0: #引数未指定時
        err("ArgumentError", 'Argument is not specified.')
      elif len(sys.argv[i][1:]) == 1 and (sys.argv[i][1:] == 't'): #単独指定専用（追加引数必要）引数指定時
        if i + 1 >= len(sys.argv) or sys.argv[i + 1].startswith('-'): #追加引数未指定時
          err("ArgumentError", 'Argument "-'+ sys.argv[i][1:] +'" requires additional argument.')
        elif sys.argv[i][1:] == 't':
          tapefilename = sys.argv[i + 1]
          dbg("Tape Filename specified: " + tapefilename)
        i += 1
      else: #引数複数指定時
        for arg in sys.argv[i][1:]:
          if arg == "d":
            debug = True
            dbg("Argument specified: debug")
          elif arg == "w":
            watch = True
            dbg("Argument specified: watch")
          elif arg == "s":
            step = True
            dbg("Argument specified: step")
          elif arg == "t": #単独指定専用引数を複数指定時に指定した場合
            err("ArgumentError", 'Argument "-'+ arg +'" must be specified alone.')
          else:
            err("ArgumentError", 'Argument "-'+ arg +'" is unknown.')
    else:
      filename = sys.argv[i]
      dbg("Filename specified: " + filename)
    i += 1
  return filename, tapefilename, watch, step


def run(prog, tape, watch, step):
  prog = removeComment(prog)
  charCheck1(prog) #コメントを除去した後に文字種チェック
  label, prog = getlabel(prog) #ラベルと行数の対応付け
  prog = removeIndent(prog)
  prog = parseProg(prog)
  commandCheck(prog) #リストにパースした後に文字種チェック

  count = 0
  mem = {} #メモリ効率をよくするため辞書型。リスト型は大きい番地を使用した際に効率が悪い
  proglen = len(prog)
  row = 0
  while row < proglen:
    p = prog[row]
    if p[0] == '':
      row += 1
      continue

    dbg("Exec " + str(count+1) + ":  line " + str(row + 1) + ":" + str(p))
    if p[0] == 'HALT':
      count += 1
      print("Execution finished in " + str(count) + " step(s).")
      memkeys = list(mem.keys())
      for i in range(len(memkeys)):
        memkeys[i] = int(memkeys[i])
      print("Max memory used " + str(max(memkeys)))
      exit()
    elif p[0] == "LOAD": #accpet = "*="
      val, adr = loadVal(p[1], mem, row)
      mem['0'] = val
      if adr is None:
        dbg("  LOAD: r0 <- " + str(mem['0']))
      else:
        dbg("  LOAD: r0 <- r" + adr + " (" + str(mem['0']) + ")")
    elif p[0] == "STORE": #accpet = "*"
      val, adr = loadVal(p[1], mem, row, accept="*", onlyAddress=True)
      mem[adr] = mem['0']
      dbg("  STORE: r" + adr + " <- r0 (" + str(mem[adr]) + ")")
    elif p[0] == "ADD": #accpet = "*="
      val, adr = loadVal(p[1], mem, row)
      mem['0'] += val
      if adr is None:
        dbg("  ADD: r0 <- r0 + " + str(val) + " (" + str(mem['0']) + ")")
      else:
        dbg("  ADD: r0 <- r0 + r" + adr + " (" + str(mem['0']) + ")")
    elif p[0] == "SUB": #accpet = "*="
      val, adr = loadVal(p[1], mem, row)
      mem['0'] -= val
      if adr is None:
        dbg("  SUB: r0 <- r0 - " + str(val) + " (" + str(mem['0']) + ")")
      else:
        dbg("  SUB: r0 <- r0 - r" + adr + " (" + str(mem['0']) + ")")
    elif p[0] == "MULT": #accpet = "*="
      val, adr = loadVal(p[1], mem, row)
      mem['0'] *= val
      if adr is None:
        dbg("  MULT: r0 <- r0 * " + str(val) + " (" + str(mem['0']) + ")")
      else:
        dbg("  MULT: r0 <- r0 * r" + adr + " (" + str(mem['0']) + ")")
    elif p[0] == "DIV": #accpet = "*="
      val, adr = loadVal(p[1], mem, row)
      mem['0'] /= val
      if adr is None:
        dbg("  DIV: r0 <- r0 / " + str(val) + " (" + str(mem['0']) + ")")
      else:
        dbg("  DIV: r0 <- r0 / r" + adr + " (" + str(mem['0']) + ")")
    elif p[0] == "JUMP":
      row = jump(p[1], label, row) #インクリメントが考慮されているため，-1した行が返る
      dbg('  JUMP: Jump to Label "' + p[1] + '" (line ' + str(row + 2) + ')')
    elif p[0] == "JZERO":
      val = mem['0']
      dbg('  JZERO: r0 = ' + str(val))
      if val == 0:
        row = jump(p[1], label, row)
        dbg('  JZERO: Jump to Label "' + p[1] + '" (line ' + str(row + 2) + ')')
    elif p[0] == "JGTZ":
      val = mem['0']
      dbg('  JGTZ: r0 = ' + str(val))
      if val > 0:
        row = jump(p[1], label, row)
        dbg('  JGTZ: Jump to Label "' + p[1] + '" (line ' + str(row + 2) + ')')
    elif p[0] == "SJ":
      if len(p[1:]) == 3:
        op1, op2, lb = p[1:]
        #第一オペランドは直接アドレス指定のみなので数字のみかどうかチェック
        try:
          int(op1)
        except ValueError:
          err("SJOperandError","The first argument of SJ command must specify the address as an integer" + line(row))
        
        #第二オペランドは直接アドレス指定か即値のみなのでチェック
        op2_temp = op2
        if op2_temp[0] == "=":
          op2_temp = op2_temp[1:]
        try:
          int(op2_temp)
        except ValueError:
          err("SJOperandError","The second argument of SJ command must specify the address as an integer or an immediate value" + line(row))
        
        if(op1 == op2): #op1とop2が同一。op1は必ず0で初期化される
          mem[op1] = 0
          dbg('  SJ: r' + op1 + " <- 0")
        elif(op2[0] == "="): #op2が即値
          val, adr = loadVal(op1, mem, row) #メモリに値が入っているかチェックするため，敢えて呼び出す
          mem[adr] = val - int(op2[1:])
          dbg('  SJ: r' + adr + " <- r" + adr + " - " + op2[1:] + " (" + str(mem[adr]) + ")")
        else:
          val1, adr1 = loadVal(op1, mem, row)
          val2, adr2 = loadVal(op2, mem, row)
          mem[adr1] = val1 - val2
          dbg('  SJ: r' + adr1 + " <- r" + adr1 + " - r" + adr2 + " (" + str(mem[adr1]) + ")")
        #op1の値が0ならjump
        if mem[op1] == 0:
          row = jump(lb, label, row)
          dbg('  SJ: Jump to Label "' + lb + '" (line ' + str(row + 2) + ')')
      else:
        err("SJOperandError","SJ command needs just 3 operands" + line(row))
    elif p[0] == "WRITE":
      val, adr = loadVal(p[1], mem, row)
      if adr is None:
        print("WRITE: " + str(val))
      else:
        print("WRITE r" + adr + ": " + str(val))
    elif p[0] == "READ":
      if tape is None:
        err("READCommandError",'Commad "READ" is executed but Tapefile is not specified.')
      else:
        val, adr = loadVal(p[1], mem, row, accept="*", onlyAddress=True)
        try:
          mem[adr] = tape.pop(0)
        except:
          err("READCommandError",'End of the Tapefile data has been reached.')
        dbg("  READ: r" + adr + " <- " + str(mem[adr]))
    else:
      err("UnknownCommandError",'Unknown command "' + p[0] + line(row))
    count += 1
    row += 1


def removeComment(prog):
  i = 0
  proglen = len(prog)
  while i < proglen:
    if ";" in prog[i]:
      prog[i] = prog[i][0:prog[i].find(';')]
      prog[i] += '\n'
    i += 1
  if debug:
    dbg("removeComment Finished")
    printProg(prog)
  return prog
  
def charCheck1(prog):
  #コメント除去後の文字種チェック
  p = re.compile('[-_:,=*a-zA-Z0-9 \n\t]+')
  for i, l in enumerate(prog):
    if not p.fullmatch(l):
      err("SyntaxError", "Unexpected character" + line(i))
  dbg("charCheck1 Finished")


def commandCheck(prog):
  #リストにパースした後のアドレスチェック
  p = re.compile(r'(=-?\d+)|(\*?\d+)') #即値は-を許可。アドレスは*を許可
  for i, l in enumerate(prog):
    if l[0] == '': #コマンドなし
      continue
    elif l[0] == 'HALT': #引数0
      if len(l) == 1:
        continue
      else:
        err("SyntaxError",'The command "HALT" should not have parameters' + line(i))
    elif l[0] == 'JUMP' or l[0] == 'JGTZ' or l[0] == 'JZERO': #ジャンプ命令
      if len(l) == 2:
        continue
      else:
        err("SyntaxError",'The command "' + l[0] + '" should have only 1 parameter' + line(i))
    #引数1
    elif l[0] == 'LOAD' or l[0] == 'STORE' or l[0] == 'READ' or l[0] == 'WRITE' or l[0] == 'ADD' or l[0] == 'SUB' or l[0] == 'MULT' or l[0] == 'DIV':
      if not (p.fullmatch(l[1])):
        err("SyntaxError", "The address you specified is not a valid foramt address or immediate value" + line(i))
      elif len(l) == 2:
        continue
      else:
        err("SyntaxError",'The command "' + l[0] + '" should have only 1 parameter' + line(i))
    elif l[0] == 'SJ': #SJ命令
      if not (p.fullmatch(l[1]) and p.fullmatch(l[2])):
        err("SyntaxError", "The address you specified is not a valid foramt address or immediate value" + line(i))
      elif len(l) == 4:
        continue
      else:
        err("SyntaxError",'The command "SJ" should have only 3 parameter' + line(i))
    else:
      err("UnknownCommandError",'Unknown command "' + l[0] + line(i))
      
  dbg("commandCheck Finished")


def getlabel(prog):
  label = {}
  i = 0
  proglen = len(prog)
  while i < proglen:
    if ":" in prog[i]:
      if prog[i].count(':') >= 2: #1行に2回':'が出現したらエラー
        err("LabelError","Label delimiter ':' appears more than 2 times" + line(i))
      l = prog[i][0:prog[i].find(":")]
      l = l.lstrip(" \t") #先頭から空白とタブ文字を削除
      if " " in l:
        err("LabelError","Label must not contain spaces" + line(i)) #ラベルに空白あったらエラー
      if l in label:
        err("LabelError",'Label "' + l + '" is already defined before' + line(i)) #ラベルに空白あったらエラー
      label[l] = i
      prog[i] = prog[i][prog[i].find(":") + 1:]
      dbg("LabelAllocated: " + l + " -> line " + str(label[l] + 1))
    i += 1
  if debug:
    dbg("getLabel Finished")
    printProg(prog)
  return label, prog


def removeIndent(prog):
  i = 0
  proglen = len(prog)
  while i < proglen:
    prog[i] = prog[i].lstrip(" \t") #先頭から空白とタブ文字を削除
    
    #末尾から改行文字を削除し，空白やタブ文字を削除する
    prog[i] = prog[i].rstrip("\n")
    prog[i] = prog[i].rstrip(" \t")
    i += 1
  if debug:
    dbg("removeIndent Finished")
    printProg(prog, end = "\n")
  return prog


def parseProg(prog):
  #区切り文字の前後に空白やタブ文字が混入していても動作するように正規表現
  p_norm = re.compile(r'[ \t]+')
  p_sj = re.compile(r'[ \t]*\,[ \t]*')
  
  i = 0
  proglen = len(prog)
  while i < proglen:
    #SJ命令かそうでないかで分岐
    if p_norm.split(prog[i])[0] == "SJ":
      p = ['SJ']
      p += p_sj.split(prog[i][3:].lstrip(" \t")) #SJ命令なら，カンマでパース SJ命令のときのみ第一アドレス部の前の空文字を除去できないので除去
      prog[i] = p
    else:
      prog[i] = p_norm.split(prog[i]) #SJ命令以外なら，そのまま空白文字でパース
    i += 1
  if debug:
    dbg("parseProg Finished")
    printProg(prog, end = "\n")
  return prog



def loadVal(ope, mem, row, accept = "=*", onlyAddress = False):
  #accept…アドレス指定部の修飾子を制限。修飾子なしは常にあり得るが，例えばSTORE命令に=は使えないのでメソッドコール時にaccept="*"を指定
  #onlyAddress…間接アドレスを解決するのみで，メモリから値を取得しない。STORE命令など
  val, adr = None, None
  if ope[0] == "=":
    if "=" in accept:
      val = ope[1:]
    else:
      err("AddressQualifierError", "Address qualifier '=' is not accepted" + line(row))
  elif ope[0] == "*":
    if "*" in accept:
      try:
        adr = ope[1:] #間接アドレス
        adr = str(mem[adr]) #間接アドレスから実効アドレスを取り出す
        if not onlyAddress:
          val = mem[adr] #実効アドレスに含まれる値を取り出す
      except KeyError:
        err("MemoryError","Address r" + adr + " is not initialized" + line(row))
    else:
      err("AddressQualifierError", "Address qualifier '*' is not accepted" + line(row))
  else:
    adr = ope
    if not onlyAddress:
      try:
        val = mem[adr]
      except KeyError:
        err("MemoryError","Address r" + adr + " is not initialized" + line(row))
  if not onlyAddress:
    try:
      val = int(val)
    except ValueError:
      err("ValueError",'value "' + val + '" is not an integer' + line(row))
  return val, adr


def jump(lb, label, row):
  try:
    jumprow = label[lb] - 1 #後ほどインクリメントされるため，敢えて-1しておく
  except KeyError:
    err("LabelError","Label " + lb + " is not defined" + line(row))
  return jumprow
  

  

def readRAMfile(filename):
  if filename is None:
    err("RAMFileError","RAMfile is not specified.")
  if not os.path.isfile(filename):
    err("RAMFileError", "RAMfile you specified does not exist or is not a file.")
  try:
    with open(filename, 'r', encoding='utf-8') as f:
      prog = f.readlines()
      dbg("RAMFile encoding mode: UTF-8")
  except UnicodeDecodeError:
    try:
      with open(filename, 'r', encoding='cp932') as f:
        prog = f.readlines()
        dbg("RAMFile encoding mode: Shift-JIS")
    except UnicodeDecodeError:
      err("RAMFileError", "RAMfile must be encoded in UTF-8 or Shift-JIS") #Shift-JISかUTF-8でない場合
  #ファイルの末尾が改行で終わっていない場合，表示上および実行上の問題があるので追加する
  if prog[-1][-1] != "\n":
    prog[-1] += "\n"
  if debug:
    dbg("RAMFileRead")
    printProg(prog)
  return prog


def readTapefile(tapefilename):
  if tapefilename is None:
    return None
  else:
    if not os.path.isfile(tapefilename):
      err("TapeFileError", "Tapefile you specified does not exist or is not a file.")
    f = open(tapefilename, 'r')
    tape = f.readlines()
    f.close()
    for i in range(len(tape) - 1, -1, -1):
      if tape[i].lstrip(" \t") == '\n':
        tape.pop(i)
      else:
        break
    for i in range(len(tape)):
      try:
        tape[i] = int(tape[i])
      except ValueError:
        err("TapeFileError", "Each line of the Tapefile must be an integer.")
    if debug:
      dbg("TapeFileRead")
      print(tape)
    return tape


def line(i):
  return "  (line " + str(i+1) + ")"

def printProg(prog, end = ''):
  proglen = len(str(len(prog))) #行数表示桁数を求める。log10は少数で誤差が出る様なので避けた。
  for i, l in enumerate(prog):
    print(f"{i + 1:<{proglen}}| {l}", end=end)


def dbg(msg, banner=True, end='\n'):
  if debug:
    if banner:
      print("\033[45m(DEBUG)\033[0m " + msg, end=end)
    else:
      print(msg, end=end)

def err(errtype, errmsg):
  print("\033[31m" + errtype + ": " + errmsg + "\033[0m")
  exit()


if __name__=="__main__":
  main()