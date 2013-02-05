# $Id$
import sys
import copy

# jiro data
TITLE = "NO TITILE"
SUBTITLE = "NO SUB TITLE"
BPM = 0.0
WAVE = "NO WAVE FILE"
OFFSET = 0.0
DEMOSTART = 0.0
COURSE = "Oni"

# osu data
AudioFilename = ""
Title = ""
Source = ""
Tags = "taiko jiro tja"
Artist = "unknown"
Creator = "unknown"
Version = "Oni"
AudioLeadIn = 2000
CountDown = 0
SampleSet = "Normal"
StackLeniency = 0.7
Mode = 1
LetterboxInBreaks = 1
PreviewTime = 0.0
TimingPoints = []
HitObjects = []
HPDrainRate = 3
CircleSize = 5
OverallDifficulty = 3
ApproachRate = 5
SliderMultiplier = 1.4
SliderTickRate = 4
CircleX = 416
CircleY = 176

# const_data
BRANCH = "BRANCH"
END = "END"
START = "START"
BPMCHANGE = "BPMCHANGE"
MEASURE = "MEASURE"
GOGOSTART = "GOGOSTART"
GOGOEND = "GOGOEND"
DELAY = "DELAY"
SCROLL = "SCROLL"

# guess str
def convert_str(str):
    try:
        ret1 = str.decode("gbk").encode("utf-8")
    except:
        ret1 = None

    try:
        ret2 = str.decode("shift-jis").encode("utf-8")
    except:
        ret2 = None

    try:
        ret3 = str.decode("big5").encode("utf-8")
    except:
        ret3 = None    
    
    ret = []
    if ret1: ret.append(ret1);print len(ret1)
    if ret2: ret.append(ret2);print len(ret2)
    if ret3: ret.append(ret3);print len(ret3)
    if not ret:
        return str
    else:
        ans = None
        for ret0 in ret:
            if ans is None or len(ret0) < len(ans):
                ans = ret0
        return ans


def check_unsupported(filename):
    return
    assert isinstance(filename, basestring)
    rtassert(filename.endswith(".tja"), "filename should ends with .tja")
    try: fobj = open(filename)
    except IOError: rtassert(False, "can't open tja file.")
    END_cnt = 0
    for line in fobj:
        rtassert(("#"+BRANCH) not in line, "don't support branch")
        END_cnt += (("#"+END) in line)
        rtassert(END_cnt <= 1, "don't support multiple fumen.")

def rm_jiro_comment(str):
    assert isinstance(str, basestring)
    try: i = str.index('//')
    except : return str
    return str[:i]

def get_meta_data(filename):
    global TITLE, SUBTITILE, WAVE, OFFSET, DEMOSTART, COURSE, BPM
    assert isinstance(filename, basestring)
    rtassert(filename.endswith(".tja"), "filename should ends with .tja")
    try: fobj = open(filename)
    except IOError: rtassert(False, "can't open tja file.")
    for line in fobj:
        line = line.strip()
        try: i = line.index(":")
        except ValueError: continue
        vname = line[:i].strip()
        vval = line[i+1:].strip()
        if vname == "TITLE": TITLE = vval
        elif vname == "SUBTITLE": SUBTITILE = vval
        elif vname == "BPM": BPM = float(vval)
        elif vname == "WAVE": WAVE = vval
        elif vname == "OFFSET": OFFSET = float(vval)
        elif vname == "DEMOSTART": DEMOSTART = float(vval)
        elif vname == "COURSE": COURSE = vval

def add_default_timing_point():
    global TimingPoints
    tm = {}
    tm["offset"] = -OFFSET * 1000.0
    tm["redline"] = True
    tm["scroll"] = 1.0
    tm["measure"] = 4.0
    tm["GGT"] = False
    tm["bpm"] = BPM

    TimingPoints.append(tm)

CIRCLE = 1
SLIDER = 2
SPINNER = 12 
SLIDER_END = -2
SPINNER_END = -12 

EMPTY = 0
CLAP = 8
FINISH = 4
WHISTLE = 2 

def get_osu_type(snd):
    snd = int(snd)
    assert snd != 0
    if snd in (1, 2, 3, 4): return CIRCLE
    if snd in (5, 6): return SLIDER
    if snd in (7, 9): return SPINNER
    if snd == 8:
        if lasting_note == SLIDER:
            return SLIDER_END
        elif lasting_note == SPINNER:
            return SPINNER_END
    assert False, repr(snd) + repr(lasting_note)

def get_osu_sound(snd):
    snd = int(snd)
    assert snd != 0
    if snd == 1: return EMPTY
    elif snd == 2: return CLAP
    elif snd == 3: return FINISH
    elif snd == 4: return FINISH+CLAP
    elif snd == 5: return EMPTY
    elif snd == 6: return FINISH
    elif snd == 7: return EMPTY
    elif snd == 8: return EMPTY
    elif snd == 9: return EMPTY
    else: assert False


has_started = False 
curr_time = 0.0
bar_data = []
lasting_note = None

def get_all(filename):
    global has_started, curr_time
    try: fobj = open(filename)
    except IOError: rtassert(False, "can't open tja file.")

    has_started = False
    curr_time = -OFFSET * 1000
    add_default_timing_point()
    for line in fobj:
        line = line.strip()
        line = rm_jiro_comment(line)
        if not has_started and ("#"+START) in line:
            has_started = True
            continue
        if not has_started: continue
        if ("#"+END) in line: break
        if ("#" in line): handle_cmd(line)
        else: handle_note(line)

def get_real_offset(int_offset):
#    print "INTOffset", int_offset
    tm = get_red_tm_at(int_offset)
    tpb = 60000 / tm["bpm"]
    int_delta = abs(int_offset - tm["offset"])
    sign = (int_offset - tm["offset"] > 0 and 1 or -1)

    t_unit_cnt = round(int_delta * tm["bpm"] * 24 / 60000)

    beat_cnt = t_unit_cnt / 24
    ret = tm["offset"] + beat_cnt * 60000 * sign / tm["bpm"]
    
    if int(ret) in ():
		print tm
		print t_unit_cnt
		print "DELAT = ", int_delta
		print "GET BEAT CNT", int_delta/tpb, t_unit_cnt/24
		print int_offset, "-->", tm["offset"] + beat_cnt * 60000 / tm["bpm"]
		print int(tm["offset"] + beat_cnt * 60000 / tm["bpm"])

		print "CMP", int(tm["offset"]+beat_cnt * 60000 * sign / tm["bpm"]), int(2663+60000/tm["bpm"]*beat_cnt)
		
    return ret     
   
def handle_cmd(line):
    cmd = None
    if ("#"+BPMCHANGE) in line:
        i = line.index('#'+BPMCHANGE)
        bpm = float(line[i+1+len('#'+BPMCHANGE):].strip())
        cmd = (BPMCHANGE, bpm)
    elif ("#"+MEASURE) in line:
        i = line.index('#'+MEASURE)
        arg_str = line[i+1+len('#'+MEASURE):].strip()
        arg1, arg2 = arg_str.split('/')
        cmd = (MEASURE, 4.0*int(arg1.strip()) / int(arg2.strip()))
    elif ("#"+SCROLL) in line:
        i = line.index('#'+SCROLL)
        arg_str = line[i+1+len('#'+SCROLL):].strip()
        cmd = (SCROLL, float(arg_str))        
    elif ("#"+GOGOSTART) in line:
        cmd = (GOGOSTART,)
    elif ("#"+GOGOEND) in line:
        cmd = (GOGOEND,)
    elif ("#"+DELAY) in line:
        i = line.index('#'+DELAY)
        arg_str = line[i+1+len('#'+DELAY):].strip()        
        cmd = (DELAY, float(arg_str))
    else:
        return

    if bar_data == []:
        real_do_cmd(cmd)
    else:
        bar_data.append(cmd)

def real_do_cmd(cmd):
    global curr_time

#    print "handle cmd", cmd
    
    # handle delay, no timing point change
    if cmd[0] == DELAY:
        curr_time += cmd[1] * 1000
        return
    
    # handel timing point change command    
    if cmd[0] == BPMCHANGE:
        tm = get_last_red_tm()
        if int(curr_time) == tm["offset"]:
            tm["bpm"] = cmd[1]
        else:
            new_tm = create_new_tm()
            new_tm["redline"] = True
            new_tm["bpm"] = cmd[1]
            TimingPoints.append(new_tm)
            curr_time = int(new_tm["offset"])

            tmg = get_last_green_tm()
            last_scroll = tmg and tmg["scroll"] or 1.0
            if last_scroll != 1.0:
                real_do_cmd((SCROLL, last_scroll))
    elif cmd[0] == MEASURE:
        assert len(bar_data) == 0, "can't change measure within a bar"
        tm = get_last_red_tm()
        if int(curr_time) == tm["offset"]:
            tm["measure"] = cmd[1]
        else:
            new_tm = create_new_tm()
            new_tm["redline"] = True
            new_tm["measure"] = cmd[1]
            TimingPoints.append(new_tm)
            curr_time = int(new_tm["offset"])            

            tmg = get_last_green_tm()
            last_scroll = tmg and tmg["scroll"] or 1.0
            if last_scroll != 1.0:
                real_do_cmd((SCROLL, last_scroll))
    elif cmd[0] == SCROLL:
        tm = get_last_green_tm()
        if tm and int(curr_time) == tm["offset"]:
            tm["scroll"] = cmd[1]
        else:
            new_tm = create_new_tm()
            new_tm["redline"] = False
            new_tm["scroll"] = cmd[1]
            TimingPoints.append(new_tm)
    elif cmd[0] == GOGOSTART:
        tm = get_last_tm()
        if int(curr_time) == tm["offset"]:
            tm["GGT"] = True
        else:
            new_tm = create_new_tm()
            new_tm["redline"] = False
            new_tm["GGT"] = True
            TimingPoints.append(new_tm)                 
    elif cmd[0] == GOGOEND:
        tm = get_last_tm()
        if int(curr_time) == tm["offset"]:
            tm["GGT"] = False
        else:
            new_tm = create_new_tm()
            new_tm["redline"] = False
            new_tm["GGT"] = False
            TimingPoints.append(new_tm)        
    else:
        assert False, "unknown or unsupported command"

def add_a_note(snd, offset):
    global lasting_note
    snd = int(snd)
    HitObjects.append((get_osu_type(snd), get_osu_sound(snd), offset))
    if get_osu_type(snd) in (SLIDER, SPINNER):
        lasting_note = get_osu_type(snd)
    if get_osu_type(snd) in (SLIDER_END, SPINNER_END):
        lasting_note = None
#    print HitObjects[-1]

def get_last_tm():
    return TimingPoints[-1]

def get_last_green_tm():
    for i in range(len(TimingPoints)-1, -1, -1):
        if not TimingPoints[i]["redline"]:
            return TimingPoints[i]
    return None

def get_last_red_tm():
    for i in range(len(TimingPoints)-1, -1, -1):
        if TimingPoints[i]["redline"]:
            return TimingPoints[i]
    assert False
        
def get_tm_at(t):
    assert len(TimingPoints) > 0, "Need at least one timing point"
    if int(t) < TimingPoints[0]["offset"]:
        return TimingPoints[0]
    ret_tm = TimingPoints[0]
    for tm in TimingPoints:
        if tm["offset"] > t:
            break
        ret_tm = tm
    return ret_tm

def get_red_tm_at(t):
    assert len(TimingPoints) > 0
    assert TimingPoints[0]["redline"]
    if int(t) < TimingPoints[0]["offset"]:
        return TimingPoints[0]
    ret_tm = TimingPoints[0]
    for tm in TimingPoints:
        if tm["offset"] > int(t):
            break
        if tm["redline"]:
            ret_tm = tm
    return ret_tm
   
def create_new_tm():
    last_tm = get_last_tm()
    last_green_tm = get_last_green_tm()
    last_red_tm = get_last_red_tm()
    
    tm = {}
    tm["offset"] = int(curr_time)
#    print "GREATE NEW TM", tm["offset"] 
    tm["redline"] = None
    tm["scroll"] = last_green_tm and last_green_tm["scroll"] or 1.0 
    tm["measure"] = last_tm["measure"]
    tm["GGT"] = last_tm["GGT"]
    tm["bpm"] = last_red_tm["bpm"]
    
    return tm
    

def get_t_unit(tm, tot_note):
    #print tm["bpm"], tot_note
    return tm["measure"] * 60000.0 / (tm["bpm"] * tot_note)

debug_mode = False
last_debug = None
def handle_a_bar():
    global bar_data, curr_time
    if not bar_data: return
    
    #debug
    global last_debug
    if last_debug is None:
        last_debug = -OFFSET * 1000
    #debug

    tot_note = 0
    for data in bar_data:
        if isinstance(data, basestring):
            tot_note += 1
    #print "TOT_NOTE", tot_note
    
    if False and debug_mode:
        pure_data = filter(lambda x:x[0].isdigit(), bar_data)
        p1= "%6d %2.1f %2d %s" % (int(curr_time), \
                get_last_tm()["measure"], len(pure_data), \
                "".join(pure_data))

        p2= "%.4f %.2f" % (get_last_tm()["bpm"], \
                get_t_unit(get_last_tm(), tot_note) * tot_note)
        print p1

	#debug
    last_debug = curr_time
    print_each_note = False #(int(curr_time) == 112814)
    bak_curr_time = curr_time
    note_cnt = -1
	#debug
	
    for data in bar_data:
        if isinstance(data, basestring): #note
            note_cnt += 1
            if data == "0" or \
                (lasting_note != None and data != '8'):
                curr_time += get_t_unit(get_last_tm(), tot_note)
                continue
            add_a_note(data, curr_time)
            if print_each_note:
                print note_cnt, data, curr_time, bak_curr_time + note_cnt * get_t_unit(get_last_tm(), tot_note), get_t_unit(get_last_tm(), tot_note) 
            curr_time += get_t_unit(get_last_tm(), tot_note)           
        else: #cmd
            real_do_cmd(data)
    bar_data = [] 
    
    if print_each_note:
        print "after bar, curr_time= %f", curr_time
    # check x.x measure, casue it's not compatible in osu
    tm = get_last_tm()
    if abs(round(tm["measure"]) - tm["measure"]) > 0.001:
        print "unsupported measure", tm["measure"]
        bak = tm["measure"]
        tm["measure"] = 20 # a big measure for osu
        real_do_cmd((MEASURE, bak)) # remeasure, for tja

def handle_note(line):
    global bar_data
    for ch in line:
        if ch.isdigit():
            bar_data.append(ch)
        elif ch == ",":
            handle_a_bar()

def write_fmt_ver_str():
    print "osu file format v9"
    print

def write_General():
    global Title, Source, AudioFilename, PreviewTime
    Title = TITLE
    Source = SUBTITLE
    AudioFilename = WAVE
    PreviewTime = DEMOSTART * 1000

    print "[General]"
    print "AudioFilename:", AudioFilename
    print "AudioLeadIn:", AudioLeadIn
    print "PreviewTime:", int(PreviewTime)
    print "CountDown:", CountDown
    print "SampleSet:", SampleSet
    print "StackLeniency:", StackLeniency
    print "Mode:", Mode
    print "LetterboxInBreaks:", LetterboxInBreaks
    print

# no use, but required by osu
def write_Editor():
    print "[Editor]"
    print "DistanceSpacing: 0.8"
    print "BeatDivisor: 4"
    print "GridSize: 4"
    print

def write_Metadata():
    global Title, Source, AudioFilename, PreviewTime, Version
    Title = TITLE
    Source = SUBTITLE    
    Version = COURSE
    print "[Metadata]"
    print "Title:", convert_str(Title)
    print "Artist:", convert_str(Artist)
    print "Creator:", convert_str(Creator)
    print "Version:", convert_str(Version)
    print "Source:", convert_str(Source)
    print "Tags:", Tags
    print

def write_Difficulty():
    print "[Difficulty]"
    print "HPDrainRate:", HPDrainRate
    print "CircleSize:", CircleSize
    print "OverallDifficulty:", OverallDifficulty
    print "ApproachRate:", ApproachRate
    print "SliderMultiplier:", SliderMultiplier
    print "SliderTickRate:", SliderTickRate
    print 

def write_TimingPoints():
    print "[TimingPoints]"
    for tm in TimingPoints:
        if tm["redline"]: str = 60000.0/tm["bpm"]
        else: str = -100/tm["scroll"]
        print "%d,%f,%d,1,0,100,%d,%d" % (int(tm["offset"]), str, \
            int(round(tm["measure"])), tm["redline"], tm["GGT"])
        tm["offset"] = int(tm["offset"])
    print

def write_HitObjects():
    print "[HitObjects]"
    lasting_note = None
    for ho in HitObjects:
    	beg_offset = get_real_offset(ho[2])
        if int(beg_offset) != int(ho[2]):
#            print "OFFSET FIXED", int(beg_offset), int(ho[2])
            pass
        if ho[0] == CIRCLE:
            rtassert(lasting_note is None, "this is no science")
            print "%d,%d,%d,%d,%d" % (CircleX, CircleY, beg_offset, ho[0],
                    ho[1])
        elif ho[0] == SLIDER:
            rtassert(lasting_note is None, "this is no science")            
            lasting_note = ho
        elif ho[0] == SPINNER:
            rtassert(lasting_note is None, "this is no science")            
            lasting_note = ho
        elif ho[0] == SLIDER_END:
            rtassert(lasting_note is not None and \
                    lasting_note[0] == SLIDER)
            ln = lasting_note
            tm = get_tm_at(int(ln[2]))
            curve_len = 100 * (ho[2] - ln[2]) * tm["bpm"]  * SliderMultiplier * tm["scroll"] / 60000
            print "%d,%d,%d,%d,%d,L|%d:%d,%d,%f" % (CircleX, CircleY, \
                    int(get_real_offset(ln[2])), ln[0], ln[1], \
                    int(CircleX+curve_len), CircleY, 1, curve_len)
            lasting_note = None
        elif ho[0] == SPINNER_END:
            rtassert(lasting_note is not None and \
                    lasting_note[0] == SPINNER, "this is no science")
            ln = lasting_note
            print "%d,%d,%d,%d,%d,%d" % (CircleX, CircleY, int(get_real_offset(ln[2])), \
                    ln[0], ln[1], int(get_real_offset(ho[2])))
            lasting_note = None
    print

def tja2osu(filename):
    assert isinstance(filename, basestring)
    rtassert(filename.endswith(".tja"), "filename should ends with .tja")
    check_unsupported(filename)

    # real work
    get_meta_data(filename)
    write_fmt_ver_str()
    write_General()
    write_Editor()
    write_Metadata()
    write_Difficulty()
    get_all(filename)
    if not debug_mode:
        write_TimingPoints()
        write_HitObjects()


def rtassert(b, str=""):
    if not b:
        print >> sys.stderr, str
        exit()

def get_help_str():
    return "HELP STRING"

if __name__ == "__main__":
    rtassert(len(sys.argv) >= 2, "need a filename\n" +get_help_str())
    global debug_mode
    debug_mode = (len(sys.argv) >= 3 and ("debug" in sys.argv))
    tja2osu(sys.argv[1])
