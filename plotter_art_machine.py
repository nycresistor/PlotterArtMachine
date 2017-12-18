#!/usr/bin/python3

from apple410 import Apple410
from tinydb import TinyDB, Query
from argparse import ArgumentParser
import sys
import os
import subprocess

def add_new_script(db, args):
    "Add a new artwork script to the database."
    q = Query()
    l = db.search(q.name == args.NAME)
    if len(l) > 0:
        if args.force:
            print("Replacing existing art.")
            db.remove(q.name == args.NAME)
        else:
            print("Existing art with same name, aborting.")
            sys.exit(1)
    record = {'name':args.NAME, 'path':args.PATH,
            'author':args.author,
            'max_editions': args.editions,
            'released_editions': 0,
            'description' : args.comment }
    db.insert(record)
    print("Successfully inserted {}".format(record['name']))

def list_scripts(db, args):
    "Get all art scripts, optionally specifying availability."
    l = db.all()
    if not args.all:
        if args.exhausted:
            l = list(filter(lambda s: s['released_editions'] >= s['max_editions'], l))
        else:
            l = list(filter(lambda s: s['released_editions'] < s['max_editions'], l))
    if len(l) == 0:
        print("No scripts found.")
    else:
        for s in l:
            d = ""
            if s['description']: d = d + s['description'] + " "
            if s['author']: d = d + "(" + s['author'] + ")"
            print("{:20s} {:20s} {:3>d}/{:3<d}   {}".format(
                s['name'],s['path'],s['released_editions'],s['max_editions'],d))


def script_ok(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

art_width = 2150
art_height = 1700
from datetime import date

def text_width(text, size):
    return len(text)*size

def draw_frame(a, author, ed, ed_max):
    if author:
        author = author + "/nycresistor"
    else:
        author = "nycresistor"
    datestr = date.today().strftime("%m/%d/%Y")
    sz=30
    a.send("PV10")
    a.send("VP0,0,2394,1700")
    a.send("WD0,0,2394,1700")
    a.send("LR90")
    a.send("LS{}".format(sz))
    a.send("PS1")
    baseline=2394-40
    a.send("MA{},{}".format(baseline,0))
    a.send("PL{}".format(author))
    edition = "#{}/{}".format(' '*len(str(ed_max)), ed_max)
    s = 1700 - text_width(edition,sz)
    a.send("MA{},{}".format(baseline,s))
    a.send("PL{}".format(edition))

    left = text_width(author,sz)
    right = s
    s = left + ((right-left) - text_width(datestr,sz))/2
    a.send("PS2")
    a.send("MA{},{}".format(baseline,s))
    a.send("PL{}".format(datestr))
    s = 1700 - text_width("{}/{}".format(ed,ed_max),sz)
    a.send("MA{},{}".format(baseline,s))
    a.send("PL{}".format(ed))
    a.send("CH")


def draw_art(db, args):
    "Attempt to draw the given art, keeping an eye out for failed prints."
    q = Query()
    l = list(filter(lambda s: s['released_editions'] < s['max_editions'], db.search(q.name == args.NAME)))
    if len(l) == 0:
        print("Could not find {}".format(args.NAME))
    elif len(l) > 1:
        print("Multiple scripts named {}!".format(args.NAME))
    else:
        art = l[0]
        path = art['path']
        ed = art['released_editions'] + 1
        if script_ok(path):
            print("Executing {}".format(art['path']))
            result = subprocess.run(args=[path, str(art_width), str(art_height)], stdout=subprocess.PIPE)
            if result.returncode != 0:
                print("Failed to execute")
            else:
                a = Apple410(args.device)
                msg = ""
                for c in result.stdout:
                    c = chr(c)
                    if c == '\x03' or c == '\n':
                        msg = msg.strip()
                        if msg:
                            a.send(msg)
                        msg = ""
                    else:
                        msg = msg + c
                msg = msg.strip()
                if msg:
                    a.send(msg)
                draw_frame(a,art['author'],ed,art['max_editions'])
                db.update({'released_editions': ed}, q.name == args.NAME)
                print("Released edition {} of {}".format(ed,args.NAME))
        else:
            print("Could not execute {}".format(path))
    pass

def run_test(db, args):
    "Run the test pattern to check the pens"
    a = Apple410(args.device)
    print("Running test.")
    t = open('test.plot')
    for l in t.readlines():
        l = l.strip()
        if not l or l.startswith('#'):
            continue
        a.send(l)
    a.close()
    print("Test sent.")

def exercise_pen(db,args):
    "Exercise a pen for a while and see if it improves"
    a = Apple410(args.device)
    pen = args.PEN
    print("Exercising pen {}".format(pen))
    a.send("PS{}".format(pen))
    a.send("MA100,100")
    a.send("PV5")
    iters = args.iterations
    for i in range(iters):
        a.send("DR10,250,10,-250")
    a.send("PV7")
    a.send("RS")



def main():
    "Parse arguments and perform specified command."
    p = ArgumentParser(
            description="Script for managing and running the NYCR Art Plotter.",)
    p.add_argument('-d','--device', default='/dev/ttyUSB0', 
        help='Path to serial port for Apple 410 Color Plotter')
    subs = p.add_subparsers()
    parser_add = subs.add_parser('add', help='Add new art script to the roster')
    parser_add.add_argument('-e','--editions',type=int,default=100,
            help='number of editions to produce of this artwork')
    parser_add.add_argument('-f','--force', action='store_true',
            help='replace existing art with name')
    parser_add.add_argument('-a','--author',
            help='name of author to sign; if not specified just credited to group.')
    parser_add.add_argument('NAME', help='name of artwork')
    parser_add.add_argument('PATH', help='path to art script')
    parser_add.add_argument('-m', '--comment',
            help='brief description of artwork')
    parser_add.set_defaults(func=add_new_script)

    parser_list = subs.add_parser('list', help='List available artworks')
    parser_list.add_argument('-a','--all', action='store_true', help='Include exhausted editions')
    parser_list.add_argument('-e','--exhausted', action='store_true', help='Only show exhausted editions')
    parser_list.set_defaults(func=list_scripts)

    parser_draw = subs.add_parser('draw', help='draw an artwork')
    parser_draw.add_argument('NAME', nargs='?', help='specify which artwork to draw')
    parser_draw.add_argument('-t','--test', action='store_true', help='run in testing mode')
    parser_draw.set_defaults(func=draw_art)

    parser_test = subs.add_parser('test', help='run test pattern')
    parser_test.set_defaults(func=run_test)

    parser_exercise = subs.add_parser('exercise', help='exercise a particular pen')
    parser_exercise.add_argument('PEN', help='The pen to exercise')
    parser_exercise.add_argument('-i','--iterations',type=int,default=30,help='number of cycles')
    parser_exercise.set_defaults(func=exercise_pen)

    args = p.parse_args()
    db = TinyDB('art_editions.json')
    args.func(db,args)


if __name__=='__main__':
    main()

