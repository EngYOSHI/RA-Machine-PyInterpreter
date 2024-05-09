#!/usr/bin/env python3
import sys
import os
import re

debug = False


def main():
  filename, watch, step = procArg()
  prog = readRAMfile(filename)
  run(prog, watch, step)


def procArg():
  global debug

  filename = None
  watch = False
  step = False
  i = 1
  while(i < len(sys.argv)):
    if sys.argv[i].startswith('-'):
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
        else:
          err("ArgumentError", 'Argument "-'+ arg +'" is unknown.')
    else:
      filename = sys.argv[i]
      dbg("Filename specified: " + filename)
    i += 1
  return filename, watch, step


def run(prog, watch, step):
  prog = removeComment(prog)
  charCheck(prog)
  label, prog = getlabel(prog) #ラベルと行数の対応付け
  prog = removeIndent(prog)
  prog = parseProg(prog)

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
          err("SJOperandError","The first argument of SJ command must specify the address as an integer in line " + str(row + 1))
        
        #第二オペランドは直接アドレス指定か即値のみなのでチェック
        op2_temp = op2
        if op2_temp[0] == "=":
          op2_temp = op2_temp[1:]
        try:
          int(op2_temp)
        except ValueError:
          err("SJOperandError","The second argument of SJ command must specify the address as an integer or an immediate value in line " + str(row + 1))
        
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
        err("SJOperandError","SJ command needs just 3 operands in line " + str(row + 1))
    elif p[0] == "WRITE":
      val, adr = loadVal(p[1], mem, row)
      if adr is None:
        print("WRITE: " + str(val))
      else:
        print("WRITE r" + adr + ": " + str(val))
    else:
      err("UnknownCommandError",'Unknown command "' + p[0] + '" in line ' + str(row + 1))
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
  
def charCheck(prog):
  #文字種チェック
  p = re.compile('[a-zA-Z0-9*=,: \n\t]+')
  for i, l in enumerate(prog):
    if not p.fullmatch(l):
      err("SyntaxError", "Unexpected character in line " + str(i + 1))
  dbg("charCheck Finished")


def getlabel(prog):
  label = {}
  i = 0
  proglen = len(prog)
  while i < proglen:
    if ":" in prog[i]:
      if prog[i].count(':') >= 2: #1行に2回':'が出現したらエラー
        err("LabelError","Label delimiter ':' appears more than 2 times in line " + str(i + 1))
      l = prog[i][0:prog[i].find(":")]
      if " " in l:
        err("LabelError","Label must not contain spaces in line " + str(i + 1)) #ラベルに空白あったらエラー
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
    while prog[i][0] == ' ' or prog[i][0] == '\t':
      prog[i] = prog[i][1:]
    i += 1
  if debug:
    dbg("removeIndent Finished")
    printProg(prog)
  return prog


def parseProg(prog):
  i = 0
  proglen = len(prog)
  while i < proglen:
    #末尾から改行文字を削除し，空白やタブ文字を削除する
    prog[i] = prog[i].rstrip("\n")
    while len(prog[i]) > 0 and prog[i][-1].isspace():
      prog[i] = prog[i].rstrip(" ").rstrip("\t")
    #SJ命令かそうでないかで分岐
    if prog[i].startswith('SJ'):
      p = ['SJ']
      p += prog[i][2:].split(',') #SJ命令なら，カンマでパース
      prog[i] = p
    else:
      prog[i] = prog[i].split(' ') #SJ命令以外なら，そのまま空白文字でパース
    #空白を削除
    j = 0
    progilen = len(prog[i])
    while j < progilen:
      prog[i][j] = prog[i][j].replace(' ','')
      prog[i][j] = prog[i][j].replace('\t','')
      j += 1
    i += 1
  if debug:
    dbg("parseProg Finished")
    printProg2(prog)
  return prog



def loadVal(ope, mem, line, accept = "=*", onlyAddress = False):
  #accept…アドレス指定部の修飾子を制限。修飾子なしは常にあり得るが，例えばSTORE命令に=は使えないのでメソッドコール時にaccept="*"を指定
  #onlyAddress…間接アドレスを解決するのみで，メモリから値を取得しない。STORE命令など
  val, adr = None, None
  if ope[0] == "=":
    if "=" in accept:
      val = ope[1:]
    else:
      err("AddressQualifierError", "Address qualifier '=' is not accepted in line " + str(line + 1))
  elif ope[0] == "*":
    if "*" in accept:
      try:
        adr = ope[1:] #間接アドレス
        adr = str(mem[adr]) #間接アドレスから実効アドレスを取り出す
        if not onlyAddress:
          val = mem[adr] #実効アドレスに含まれる値を取り出す
      except KeyError:
        err("MemoryError","Address r" + adr + " is not initialized in line " + str(line + 1))
    else:
      err("AddressQualifierError", "Address qualifier '*' is not accepted in line " + str(line + 1))
  else:
    adr = ope
    if not onlyAddress:
      try:
        val = mem[adr]
      except KeyError:
        err("MemoryError","Address r" + adr + " is not initialized in line " + str(line + 1))
  if not onlyAddress:
    try:
      val = int(val)
    except ValueError:
      err("ValueError",'value "' + val + '" is not an integer in line ' + str(line + 1))
  return val, adr


def jump(lb, label, line):
  try:
    row = label[lb] - 1 #後ほどインクリメントされるため，敢えて-1しておく
  except KeyError:
    err("LabelError","Label " + lb + " is not defined in line " + str(line + 1))
  return row
  

  

def readRAMfile(filename):
  if filename is None:
    err("RAMFileError","RAMfile is not specified.")
  if not os.path.isfile(filename):
    err("RAMFileError", "RAMfile you specified does not exist or is not a file.")
  #filename.encode("cp437").decode("utf-8") #Shift-JISとして読み込む
  f = open(filename, 'r')
  try:
    prog = f.readlines()
  except UnicodeDecodeError:
    err("RAMFileError", "RAMfile must be encoded in Shift-JIS") #Shift-JISでない場合
  f.close()
  #ファイルの末尾が改行で終わっていない場合，表示上および実行上の問題があるので追加する
  if prog[-1][-1] != "\n":
    prog[-1] += "\n"
  if debug:
    dbg("RAMFileRead")
    printProg(prog)
  return prog


def printProg(prog):
  proglen = len(str(len(prog))) #行数表示桁数を求める。log10は少数で誤差が出る様なので避けた。
  for i, l in enumerate(prog):
    print(f"{i + 1:<{proglen}}| {l}", end='')

def printProg2(prog):
  proglen = len(str(len(prog))) #行数表示桁数を求める。log10は少数で誤差が出る様なので避けた。
  for i, l in enumerate(prog):
    print(f"{i + 1:<{proglen}}| {l}")


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