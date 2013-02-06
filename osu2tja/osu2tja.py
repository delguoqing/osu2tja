# -*- coding: gbk -*-
import sys
import optparse
import copy

OSU_VER_STR_PREFIX = "osu file format v"
OSU_VER_SUPPORT = range(8, 12)

def get_section_name(str):
	if str is None: return ""
	if str.startswith('[') and str.endswith(']'):
		return str[1:-1]

def gcd(a, b):
	if a % b != 0:
		return gcd(b, a % b)
	return b


def format_time(t):
	return t//60000*100000+t%60000

def gcd_of_list(l):
	ret = None
	for n in l:
		if n == 0: continue
		if ret == None:
			ret = n
			continue
		ret = gcd(ret, n)
	return ret

def get_var(str):
	if str is None: return "", ""
	try:
		idx = str.index(':')
		var_name = str[:idx].strip()
		var_value = str[idx+1:].strip()
	except:
		return "", ""
	return var_name, var_value

def get_timing_point(str, prev_timing_point=None):
	if str is None: return {}
	ps = str.split(',')
	# in case new items are added to osu format
	if len(ps) < 8:
		return {}

	ret = {}
	try:
		ret["offset"] = int(ps[0]) # time 
		if float(ps[1]) > 0:	   # BPM change or SCROLL speed change
			bpm = ret["bpm"] = 60 * 1000.0 / float(ps[1])
			ret["scroll"] = 1.0
			ret["redline"] = True
		elif float(ps[1]) < 0:
			ret["bpm"] = prev_timing_point.get("bpm", None)
			ret["scroll"] = -100.0 / float(ps[1])
			ret["redline"] = False
			ret["offset"] = get_real_offset(ret["offset"])
		else:
			assert False
		ret["beats"] = int(ps[2]) # measure change
		ret["GGT"] = (ps[7] != '0')
	except:
		print "Osu file Error, at [TimingPoints] section, please check"
		return {}

	return ret




DON = 1
KA = 2
BIG_DON = 3
BIG_KA = 4
YELLOW = 5
BALLON = 7
BIG_YELLOW = 6 # ??
END = 8

SCROLLCHANGE = 9
BPMCHANGE = 10
GOGOSTART = 11
GOGOEND = 12
MEASURECHANGE = 13
DELAY = 14

# global variables
timingpoints = []
ballons = []
slider_velocity = None
commands = []
delays = []
tail_fix = False
slider_break_limit = None
taiko_mode = False

# debug args
show_head_info = False
ignore_format_ver = False
combo_cnt = 0

def get_tm_at(t):
	assert len(timingpoints) > 0, "Need at least one timing point"
	#assert int(t) >= timingpoints[0]["offset"], "t before first timing point"
	if int(t) < timingpoints[0]["offset"]:
		return timingpoints[0]
	ret_tm = timingpoints[0]
	for tm in timingpoints:
		if tm["offset"] > t:
			break
		ret_tm = tm
	return ret_tm

def get_red_tm_at(t):
	assert len(timingpoints) > 0
	assert timingpoints[0]["redline"]
	if int(t) < timingpoints[0]["offset"]:
		return timingpoints[0]
	ret_tm = timingpoints[0]
	for tm in timingpoints:
		if tm["offset"] > int(t):
			break
		if tm["redline"]:
			ret_tm = tm
	return ret_tm

def get_real_beat_cnt(tm, beat_cnt):
	return round(beat_cnt * 24, 2) / 24

def get_real_offset(int_offset):
#	print "INTOffset", int_offset
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


def get_slider_time(l, tm):
	global slider_velocity
	tpb = 60.0 * 1000 / tm["bpm"]
	sv = slider_velocity
	scroll = tm["scroll"]
	return 1.0 * l * tpb / (100 * sv * scroll)

def get_slider_beat_cnt(l, tm):
	global slider_velocity
	tpb = 60.0 * 1000 / tm["bpm"]
	sv = slider_velocity
	scroll = tm["scroll"]
	return get_real_beat_cnt(tm, 1.0 * l / (100 * sv * scroll))

def get_slider_sound(str):
	ret = []
	ps = str.split(',')
	reverse_cnt = int(ps[6])
	if len(ps) == 8:
		return [int(ps[4])] * (reverse_cnt + 1)
	else:
		return map(lambda x:int(x), ps[8].split('|'))

def get_donkatsu_by_sound(sound):
	# 4 - finish
	# 8 - clap
	# 2 - whistle
	if sound == 0:
		return DON
	elif sound in (2, 8, 10):
		return KA
	elif sound == 4:
		return BIG_DON
	elif sound in (12, 6, 14):
		return BIG_KA
	else:
		assert False, "don't know what note"

slider_combo_cnt_240 = 0
slider_combo_cnt_less = 0

def get_note(str):
	global slider_break_limit, taiko_mode
	ret = []

	if str is None: return ret 
	ps = str.split(',')
	if len(ps) < 5: return ret 

	type = int(ps[3])
	sound = int(ps[4])
	offset = get_real_offset(int(ps[2]))
	type &= (~4) # remove new combo flag
	if type == 1: # circle
		ret.append((get_donkatsu_by_sound(sound), offset))
	elif type == 2: # slider, reverse??

		global slider_combo_cnt_240, slider_combo_cnt_less
		if int(float(ps[7])) * int(ps[6]) >= 480:
			slider_combo_cnt_240 += int(ps[6]) + 1
		else:
			slider_combo_cnt_less += int(ps[6]) + 1

		curve_len = float(ps[7])
		reverse_cnt = int(ps[6])
		total_len = curve_len * reverse_cnt
		tm = get_tm_at(offset)
		tpb = 60000.0 / tm["bpm"]

		beat_cnt = get_slider_beat_cnt(curve_len, tm)
		if int(offset) in ():
			print "SLIDER BEAT CNT", offset, beat_cnt
			print get_slider_beat_cnt(curve_len * 2, tm)
			print "bpm= %f" % tm["bpm"]
			print offset + get_slider_beat_cnt(curve_len * 2, tm) * tpb
			print beat_cnt <= 1.09
			print len(get_slider_sound(str))
		t_noreverse = get_slider_time(curve_len, tm)
		#if t_noreverse / tpb < 1: # special rool
		assert reverse_cnt + 1 == len(get_slider_sound(str))
		if (taiko_mode and beat_cnt < 1.0) or \
				(not taiko_mode and beat_cnt * reverse_cnt < 2.0):
			for i, snd in enumerate((get_slider_sound(str))):
				point_offset = offset + get_slider_time(curve_len * i, tm)
				point_offset = get_real_offset(int(point_offset))
				#beat_cnt = get_slider_beat_cnt(curve_len * i, tm)
				#point_offset = offset + beat_cnt * tpb
				#point_offset = get_real_offset(int(point_offset))
				ret.append((get_donkatsu_by_sound(snd), point_offset))
		else:
			if sound == 0:
				ret.append((YELLOW, offset))
			else:
				ret.append((BIG_YELLOW, offset))
			ret.append((END, offset + t_noreverse * reverse_cnt))

	elif type == 8: # spinner
		ret.append((BALLON, offset))
		ret.append((END, get_real_offset(int(ps[5]))))
		# how many hit will break a ballon
		# TODO: according to length of the spinner
		global ballons
		ballons.append(int((ret[-1][1]-ret[-2][1])/122))

	return ret

# BEAT - MEASURE TABLE
measure_table = (
	(0.25, "1/16"),
	(1, "1/4"),
	(1.25, "5/16"),
	(1.5, "3/8"),
	(2, "2/4"),
	(2.25, "9/16"),
	(2.5, "5/8"),
	(3, "3/4"),
	(3.75, "15/16"),
	(4, "4/4"),
	(4.5, "9/8"),
	(5, "5/4"),
	(6, "6/4"),
	(7, "7/4"),
	(8, "8/4"),
	(9, "9/4"),
)
def write_incomplete_bar(tm, bar_data, begin, end):
	#print "INCOMPLET BAR", format_time(int(begin))
	global commands
	if len(bar_data) == 0 and int(begin) == int(end):
		return
	if len(bar_data) == 0: # 利用DELAY指令忽悠过去
		commands.append((DELAY, int(begin), end-begin))
		#delays.append("#DELAY %f" % (commands[-1][2]/1000.0))
		print "#DELAY", commands[-1][2]/1000.0
		return
	tpb = 60000 / tm["bpm"]
	my_beat_cnt = (end - begin) * tm["bpm"] / 60000.0

	#print "CALC_MIN_BEAT", bar_data, begin, end
	#print get_real_offset(bar_data[-1][1])

	# this is accurate
	min_beat_cnt = get_real_beat_cnt(tm, tm["bpm"] * (bar_data[-1][1]-begin) /60000.0) + 1.0/24

	#print "MY_BEAT_CNT", my_beat_cnt
	for beat_cnt, str in measure_table:
		#print "FIND A CLOSEST MEASURE", beat_cnt, min_beat_cnt
		#print int(begin + beat_cnt * 60000.0 / tm["bpm"]), end
		if beat_cnt >= min_beat_cnt and \
				int(begin + beat_cnt * 60000.0 / tm["bpm"]) <= end:
			commands.append((MEASURECHANGE, int(begin), str))			   
			print "#MEASURE", commands[-1][2]
			write_bar_data(tm, bar_data, begin, begin + beat_cnt * tpb)
			commands.append((DELAY, bar_data[-1][1], 
				end - int(begin + beat_cnt * 60000.0 / tm["bpm"])))
			assert commands[-1][2] >= 0, "DELAY FAULT %f" % commands[-1][2]

			# jiro will ignore delays short than 0.001s
			if commands[-1][2] >= 1:
				#delays.append("#DELAY %f" % (commands[-1][2]/1000.0))
				print "#DELAY", commands[-1][2]/1000.0
			return

	assert False, "Not Handled incomplete bar."
	print "IB", format_time(int(begin)), format_time(int(end)), bar_data

has_written_once = False
def write_bar_data(tm, bar_data, begin, end):
	global show_head_info
	global has_written_once, combo_cnt, delays, tail_fix
	if has_written_once:
		return

	if len(delays) > 0:
		for delay in delays:
			print delay
		delays = []

	t_unit = 60.0 * 1000 / tm["bpm"] / 24
	offset_list = [int(begin)] + map(lambda datum: datum[1], bar_data) + \
			[int(end)]
	#print offset_list
	delta_list = []
	for offset1, offset2 in zip(offset_list[:-1], offset_list[1:]):
		delta = (offset2-offset1)/t_unit
		t_unit_cnt = int(round(delta))
		delta_list.append(t_unit_cnt)

	if abs(delta_list[-1]) < 1:
		tail_fix = True
		#print "before tail fix", bar_data
		#print "after tail fix", bar_data[:-1]
		write_bar_data(tm, bar_data[:-1], begin, end)
		return

	delta_gcd = gcd_of_list(delta_list)
	ret_str = "0"*(delta_list[0]/delta_gcd)
	empty_t_unit = map(lambda x:"0"*(x/delta_gcd-1), delta_list[1:])

	for empty_t_unit_cnt, (note, offset) in zip(empty_t_unit, bar_data):
		ret_str += repr(note) + empty_t_unit_cnt
	   
	head = "%4d %6d %.2f %2d " % (combo_cnt, int(begin)//60000*100000+int(begin)%60000, delta_gcd/24.0, len(ret_str))
	print (show_head_info and head or '') + ret_str + ','

	#print head, map(lambda x:((x[0], int(x[1]))), bar_data)
	for note, offset in bar_data:
		if note in (DON, KA, BIG_DON, BIG_KA):
			combo_cnt += 1

	#has_written_once = True
	#print bar_data
	#print format_time(int(begin)), map(lambda datum: datum[0], bar_data)
	if True and format_time(int(begin)) in (): 
		print "begin=",begin
		print "end=", end
		print format_time(int(begin)), bar_data
		print t_unit
		print delta_list
		print offset_list
		print empty_t_unit
		print delta_gcd
		print ret_str
# debug code
is_debug_mode = False
def debug(func, *args, **kwargs):
	global is_debug_mode
	if is_debug_mode:
		func(*args, **kwargs)

def debug_timing_point():
	global timingpoints
	for tm in timingpoints:
		print tm

def osu2tja(filename):
	global slider_velocity, timingpoints, ballons, commands, tail_fix, ignore_format_ver

	# check filename
	if not filename.lower().endswith(".osu"):
		print "Input file should be Osu file!(*.osu): \n\t[[ %s ]]" % filename
		return False
	
	# try to open file
	try:
		fp = open(filename)
	except IOError:
		print "Can't open file `%s`" % filename
		return False
	
	# data structures to hold information
	audio = ""
	title = ""
	subtitle = ""
	creator = ""
	artist = ""
	version = ""
	preview = 0
	hitobjects = []

	# state vars
	osu_ver_str = ""
	curr_sec = ""
	# read data
	for line in fp:
		line = line.strip()
		if line == "":
			continue

		# check osu file format version
		if osu_ver_str == "":
			osu_ver_str = line
			if not ignore_format_ver:
				ver = int(osu_ver_str[len(OSU_VER_STR_PREFIX):])
				if ver not in OSU_VER_SUPPORT:
					print "Only support osu file format v%s at the moment. You may try option -i to force convert if you will." % ("/".join([str(i) for i in OSU_VER_SUPPORT]))
					return False

		# new section?
		new_sec = get_section_name(line)
		if new_sec:
			curr_sec = new_sec
			continue
		# varible?
		vname, vval = get_var(line)

		# read in useful infomation in following sections
		if curr_sec == "General":
			if vname == "AudioFilename":
				audio = vval
			elif vname == "PreviewTime":
				preview = int(vval)
			elif vname == "Mode":
				global taiko_mode
				if int(vval) == 1:
					taiko_mode = True
					global slider_break_limit
					slider_break_limit = 1.05
				else:
					taiko_mode = False
					slider_break_limit = 2.05
		elif curr_sec == "Metadata":
			if vname == "Title":
				title = vval
			elif vname == "Creator":
				creator = vval
			elif vname == "Version":
				version = vval
			elif vname == "Source":
				subtitle = vval
			elif vname == "Artist":
				artist = vval
		elif curr_sec == "Difficulty":
			if vname == "SliderMultiplier":
				slider_velocity = float(vval)
		elif curr_sec == "TimingPoints":
			prev_timing_point = timingpoints and timingpoints[-1] or None
			data = get_timing_point(line, prev_timing_point)
			if data:
				timingpoints.append(data)
		elif curr_sec == "HitObjects":
			data = get_note(line)
			if data:
				hitobjects.extend(data)

	debug(debug_timing_point)

	assert len(hitobjects) > 0

	# check if there is note before first timing point
	if int(hitobjects[0][1]) < timingpoints[0]["offset"]:
		new_tm_first = dict(timingpoints[0])
		new_tm_first["offset"] = int(hitobjects[0][1])
		timingpoints = [new_tm_first] + timingpoints
		
	BPM = timingpoints[0]["bpm"]
	OFFSET = timingpoints[0]["offset"] / 1000.0
	PREVIEW = preview

	scroll = timingpoints[0]["scroll"] 
	tm_idx = 0 # current timing point index
	obj_idx = 0 # current hit object index
	chap_idx = 0 # current chapter index
	measure = timingpoints[0]["beats"] # current measure
	curr_bpm = BPM # current bpm
	jiro_data = [] # jiro fumen data

	bar_data = [] # current bar data
	last_tm = 0 # last hit object offset

	bar_offset_begin = timingpoints[0]["offset"] 
	time_per_beat = (60 * 1000) / curr_bpm
	bar_max_length = measure * time_per_beat 
		
	#print "bar_offset_begin=", bar_offset_begin
	#print "bar_max_length=", bar_max_length
	
#	print "INITIAL MEASURE", measure
#	print "INITIAL BPM", curr_bpm
#	print "INITIAL OFFSET", bar_offset_begin

	bar_cnt = 1
	print "TITLE:%s" % title.decode("utf-8").encode("shift-jis")
	print "SUBTITLE:%s" % (subtitle or artist).decode("utf-8").encode("shift-jis")
	print "WAVE:%s" % audio
	print "BPM:%.2f" % timingpoints[0]["bpm"]
	print "OFFSET:-%.3f" % (timingpoints[0]["offset"] / 1000.0)
	print "DEMOSTART:%.3f" % (preview / 1000.0)

	print
	print "COURSE:3" # TODO: GUESS DIFFICULTY
	print "LEVEL:9"  # TODO: GUESS LEVEL
	print "SCOREINIT:630"
	print "SCOREDIFF:150"
	print "BALLOON:%s" % ','.join(map(repr, ballons))

	print
	print "#START"
	
	def is_new_measure(timing_point):
		bpm = timing_point["bpm"]
		_measure = timing_point["beats"]
		#print "IS_NEW_MEASURE"
		#print curr_bpm, bpm
		#print measure, _measure
		return bpm != curr_bpm or measure != _measure or timing_point["redline"]

	# show all notes
	#for ho in hitobjects:
	#	print ho
	#return
	# check if all notes align ok
	for ho1,ho2 in zip(hitobjects[:-1], hitobjects[1:]):
		if ho2[1] <= ho1[1]:
			print ho1

	while obj_idx < len(hitobjects):
		# get next object to process
		next_obj = hitobjects[obj_idx]
		next_obj_offset = int(next_obj[1])
		next_obj_type = next_obj[0]

		# get next measure offset to compare
		if tm_idx < len(timingpoints):
			next_measure_offset = timingpoints[tm_idx]["offset"]
		else:
			next_measure_offset = bar_offset_begin + bar_max_length + 1 

		# skip volumn change and kiai
		if tm_idx < len(timingpoints) and \
				not is_new_measure(timingpoints[tm_idx]):
			tm_idx += 1
			continue

		tpb = 60000 / curr_bpm
		# check if this object falls into this measure
		end = min(bar_offset_begin + bar_max_length, next_measure_offset)
		if next_obj_offset in ():
			print "MINOR MISS", next_obj[1], next_obj_offset
			print "END", end, int(end)
			print "MEASURE END", bar_offset_begin + bar_max_length
			print "NEW MEASURE END", next_measure_offset
		if next_obj_offset + tpb / 24 >= int(end):
#			write_a_measure()
			if int(end) == int(bar_offset_begin + bar_max_length):
				tm = get_tm_at(bar_offset_begin)
				write_bar_data(tm, bar_data, bar_offset_begin, end)
				bar_data = []
				bar_cnt += 1
				bar_offset_begin = get_real_offset(end)
				bar_max_length = measure * time_per_beat								
			elif int(end) == next_measure_offset: # collect an incomplete bar?
				write_incomplete_bar(get_tm_at(bar_offset_begin), \
						bar_data, bar_offset_begin, end)
				bar_data = []
				measure = timingpoints[tm_idx]["beats"]
				if timingpoints[tm_idx]["redline"]:
					curr_bpm = timingpoints[tm_idx]["bpm"]				
					bar_offset_begin = next_measure_offset
					print "#BPMCHANGE %f" % curr_bpm					
				else:
					bar_offset_begin = end
				time_per_beat = (60 * 1000) / curr_bpm
				bar_max_length = measure * time_per_beat				 
								
				if tail_fix:
					tail_fix = False
					obj_idx -= 1
					new_obj = (hitobjects[obj_idx][0], bar_offset_begin)
					hitobjects[obj_idx] = new_obj 

				# add new commands
				
				print "#MEASURE %d/4" % measure 
				
				#commands.append(BPMCHANGE, bar_offset_begin)
				#commands.append(MEASURECHANGE, bar_offset_begin)
				tm_idx += 1
			else:
				assert False, "BAR END POS ERROR"


		else:
			if next_obj[1] < bar_offset_begin:
				bar_data.append((next_obj[0], bar_offset_begin))
			else:
				bar_data.append(next_obj)
			obj_idx += 1

	# flush buffer
	if len(bar_data) > 0:
		write_bar_data(get_tm_at(bar_offset_begin),
				bar_data, bar_offset_begin, end)


	print "#END"
	print "//Auto generated by osu2tja"
	
if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("-i", "--ignore_version", action="store_const", 
		const=True, dest="ignore_version", default=False)
	parser.add_option("-d", "--debug", action="store_const", 
		const=True, dest="debug", default=False)
	(options, args) = parser.parse_args()
	
	show_head_info = options.debug
	ignore_format_ver = options.ignore_version
	osu2tja(args[0])

	if show_head_info:
		print slider_combo_cnt_240
		print slider_combo_cnt_less
