#!/usr/bin/env python
# -*- coding: utf-8 -*-
#====================================================
#          FILE: sdat2img.py
#       AUTHORS: xpirt - luxi78 - howellzhu
#          DATE: 2018-10-27 10:33:21 CEST
#====================================================

from __future__ import print_function
import os,sys,ctypes,errno

lang = hex(ctypes.windll.kernel32.GetSystemDefaultUILanguage())

def printhelp():
    if lang == '0x804':
        print('用法:')
        print('       unpack [参数]')
        print('       unpack [参数] [.transfer.list文件] [.new.dat文件 或 .new.dat.br文件] [输出镜像文件(可选)]')
        print('参数:')
        print('  -h, --help                  展示帮助文件并退出 (默认)')
        print('  -c, --check                 检查环境')
        print('  -r, --run                   开始转换')
        print('示例: unpack system.transfer.list system.new.dat')
        print('示例: unpack -run system.transfer.list system.new.dat.br system.img')
    else:
        print('Usage: unpack [OPTION]')
        print('       unpack [OPTION] [TRANSFER_LIST_FILE] [NEW_DATA_FILE or NEW_DATA_BR_FILE] [OUTPUT_IMAGE_FILE(optional)]')
        print('Options:')
        print('  -h, --help                  display this help and exit (default)')
        print('  -c, --check                 check environment')
        print('  -r, --run                   start translate')
        print('Example: unpack -r system.transfer.list system.new.dat')
        print('Example: unpack -run system.transfer.list system.new.dat.br system.img')

def main(OPTION, TRANSFER_LIST_FILE, NEW_DATA_FILE, OUTPUT_IMAGE_FILE):
    if OPTION=='-h' or OPTION=='--help':
        printhelp()
    if OPTION=='-c' or OPTION=='--check':
        if lang == '0x804':
            print('检查环境...\n')
        else:
            print('Check the Environment...\n')
        if os.path.exists('brotli.exe'):
            if lang == '0x804':
                print('已找到brotli.exe')
                print('成功')
            else:
                print('Found brotli.exe successfully')
                print('ok')
        else:
            if lang == '0x804':
                print('未找到brotli.exe')
                print('失败')
            else:
                print('Could not found brotli.exe')
                print('failed')
    if OPTION=='-r' or OPTION=='--run':
        if str(NEW_DATA_FILE.split('.')[-1]).lower()=='br':
            if os.path.exists(NEW_DATA_FILE[0:-3]):
                os.remove(NEW_DATA_FILE[0:-3])
            with os.popen('brotli -d '+NEW_DATA_FILE, "r") as p:
                if lang == '0x804':
                    print('开始处理')
                else:
                    print('Start processing')
                p.read()
            run(TRANSFER_LIST_FILE, NEW_DATA_FILE[0:-3], OUTPUT_IMAGE_FILE)
            os.remove(NEW_DATA_FILE[0:-3])
        elif str(NEW_DATA_FILE.split('.')[-1]).lower()=='dat':
            run(TRANSFER_LIST_FILE, NEW_DATA_FILE, OUTPUT_IMAGE_FILE)


def run(TRANSFER_LIST_FILE, NEW_DATA_FILE, OUTPUT_IMAGE_FILE):
    def rangeset(src):
        src_set = src.split(',')
        num_set =  [int(item) for item in src_set]
        if len(num_set) != num_set[0]+1:
            print('Error on parsing following data to rangeset:\n{}'.format(src), file=sys.stderr)
            sys.exit(1)

        return tuple ([ (num_set[i], num_set[i+1]) for i in range(1, len(num_set), 2) ])

    def parse_transfer_list_file(path):
        trans_list = open(TRANSFER_LIST_FILE, 'r')

        # First line in transfer list is the version number
        version = int(trans_list.readline())

        # Second line in transfer list is the total number of blocks we expect to write
        new_blocks = int(trans_list.readline())

        if version >= 2:
            # Third line is how many stash entries are needed simultaneously
            trans_list.readline()
            # Fourth line is the maximum number of blocks that will be stashed simultaneously
            trans_list.readline()

        # Subsequent lines are all individual transfer commands
        commands = []
        for line in trans_list:
            line = line.split(' ')
            cmd = line[0]
            if cmd in ['erase', 'new', 'zero']:
                commands.append([cmd, rangeset(line[1])])
            else:
                # Skip lines starting with numbers, they are not commands anyway
                if not cmd[0].isdigit():
                    print('Command "{}" is not valid.'.format(cmd), file=sys.stderr)
                    trans_list.close()
                    sys.exit(1)

        trans_list.close()
        return version, new_blocks, commands

    BLOCK_SIZE = 4096
    
    version, new_blocks, commands = parse_transfer_list_file(TRANSFER_LIST_FILE)

    if version == 1:
        print('Android Lollipop 5.0 detected!\n')
    elif version == 2:
        print('Android Lollipop 5.1 detected!\n')
    elif version == 3:
        print('Android Marshmallow 6.x detected!\n')
    elif version == 4:
        print('Android Nougat 7.x / Oreo 8.x detected!\n')
    else:
        print('Unknown Android version!\n')

    # Don't clobber existing files to avoid accidental data loss
    try:
        output_img = open(OUTPUT_IMAGE_FILE, 'wb')
    except IOError as e:
        if e.errno == errno.EEXIST:
            print('Error: the output file "{}" already exists'.format(e.filename), file=sys.stderr)
            print('Remove it, rename it, or choose a different file name.', file=sys.stderr)
            sys.exit(e.errno)
        else:
            raise

    new_data_file = open(NEW_DATA_FILE, 'rb')
    all_block_sets = [i for command in commands for i in command[1]]
    max_file_size = max(pair[1] for pair in all_block_sets)*BLOCK_SIZE

    for command in commands:
        if command[0] == 'new':
            for block in command[1]:
                begin = block[0]
                end = block[1]
                block_count = end - begin
                print('Copying {} blocks into position {}...'.format(block_count, begin))

                # Position output file
                output_img.seek(begin*BLOCK_SIZE)
                
                # Copy one block at a time
                while(block_count > 0):
                    output_img.write(new_data_file.read(BLOCK_SIZE))
                    block_count -= 1
        else:
            print('Skipping command {}...'.format(command[0]))

    # Make file larger if necessary
    if(output_img.tell() < max_file_size):
        output_img.truncate(max_file_size)

    output_img.close()
    new_data_file.close()
    print('Done! Output image: {}'.format(os.path.realpath(output_img.name)))


if __name__ == '__main__':
    try:
        OPTION = str(sys.argv[1]).lower()
        if OPTION!='-h' and OPTION!='--help' and OPTION!='-c' and OPTION!='--check' and OPTION!='-r' and OPTION!='--run':
            if lang == '0x804':
                print('错误:参数错误\n')
                print('使用 --help 以获取更多信息')
            else:
                print('Error:Error Option\n')
                print('Use --help to get extra information')
            sys.exit()
        if OPTION=='-h' or OPTION=='--help' or OPTION=='-c' or OPTION=='--check':
            TRANSFER_LIST_FILE = NEW_DATA_FILE = OUTPUT_IMAGE_FILE = ''
    except IndexError:
        printhelp()
        sys.exit()

    try:
        TRANSFER_LIST_FILE = str(sys.argv[2])
        if os.path.exists(TRANSFER_LIST_FILE)==False:
            if lang == '0x804':
                print('错误:'+TRANSFER_LIST_FILE+'文件不存在\n')
                print('使用 --help 以获取更多信息')
            else:
                print('Error:Could not found file:'+TRANSFER_LIST_FILE+'\n')
                print('Use --help to get extra information')
            sys.exit()
        NEW_DATA_FILE = str(sys.argv[3])
        if os.path.exists(TRANSFER_LIST_FILE)==False:
            if lang == '0x804':
                print('错误:'+NEW_DATA_FILE+'文件不存在\n')
                print('使用 --help 以获取更多信息')
            else:
                print('Error:Could not found'+NEW_DATA_FILE+'\n')
                print('Use --help to get extra information')
            sys.exit()
    except IndexError:
        if OPTION == '-r' or OPTION == '--run':
            if lang == '0x804':
                print('错误:[.transfer.list文件] [.new.dat文件 或 .new.dat.br文件] 为必输入项\n')
                print('使用 --help 以获取更多信息')
            else:
                print('Error:You must input [TRANSFER_LIST_FILE] [NEW_DATA_FILE or NEW_DATA_BR_FILE]\n')
                print('Use --help to get extra information')
            sys.exit()

    try:
        OUTPUT_IMAGE_FILE = str(sys.argv[4])
    except IndexError:
        OUTPUT_IMAGE_FILE = 'system.img'

    main(OPTION, TRANSFER_LIST_FILE, NEW_DATA_FILE, OUTPUT_IMAGE_FILE)