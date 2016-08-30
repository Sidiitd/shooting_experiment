from SIMKit import RobotScript, Event
import PyPR2
import time
#import positions
import sys
import random
numpy_path      = '/usr/lib/python2.7/dist-packages/'
sympy_path      = '/usr/local/lib/python2.7/dist-packages/'
pyinterval_path = '/usr/local/lib/python2.7/dist-packages/pyinterval-1.0b21-py2.7-linux-x86_64.egg/'
mtpltlib_path   = '/usr/lib/pymodules/python2.7'


sys.path.append(sympy_path)
sys.path.append(numpy_path)
sys.path.append(pyinterval_path)
sys.path.append(mtpltlib_path)
sys.path.append('/home/demoshare/shooting_experiment/Magiks/')

from magiks.specific_geometries.pr2 import skilled_pr2 as spr


right_shooting = {'r_elbow_flex_joint': -1.5668266161421789, 'r_shoulder_lift_joint': -0.07156730494636866, 'r_upper_arm_roll_joint': -1.1195578453851402, 'r_wrist_roll_joint': -3.1823834614790147, 'r_shoulder_pan_joint': -0.3396092818684876, 'r_forearm_roll_joint': -1.5066273796273486, 'r_wrist_flex_joint': -1.5071675013893124}

right_pullback = {'r_elbow_flex_joint': -1.8827163083810365, 'r_shoulder_lift_joint': -0.1377205348140522, 'r_upper_arm_roll_joint': -1.1378382955913073, 'r_wrist_roll_joint': -2.8935712498579074, 'r_shoulder_pan_joint': -0.395405435349739, 'r_forearm_roll_joint': -1.3948668076388655, 'r_wrist_flex_joint': -1.6445253315659132,'time_to_reach' : 0.2}

left_shooting = {'l_wrist_roll_joint': -2.6133570702164812, 'l_forearm_roll_joint': -1.205012668267126, 'l_elbow_flex_joint': -0.4263229518627475, 'l_shoulder_lift_joint': 0.21368677576185252, 'l_upper_arm_roll_joint': 0.7678997111559798, 'l_wrist_flex_joint': -0.09263466648021362, 'l_shoulder_pan_joint': -0.17482627883160928}

right_pullback_alt = {'r_elbow_flex_joint': -2.119271650781721, 'r_shoulder_lift_joint': -0.15269383620354068, 'r_upper_arm_roll_joint': -0.9991313707813558, 'r_wrist_roll_joint': -2.479583875110267, 'r_shoulder_pan_joint': -0.33853149584284675, 'r_forearm_roll_joint': -1.2974523132141216, 'r_wrist_flex_joint': -1.6922546169151684, 'time_to_reach' : 0.5}

best_pullback = {'r_elbow_flex_joint': -2.119561192204488, 'r_shoulder_lift_joint': -0.25683018654512435, 'r_upper_arm_roll_joint': -0.9635325993272411, 'r_wrist_roll_joint': -2.242225981766941, 'r_shoulder_pan_joint': -0.30528594228269534, 'r_forearm_roll_joint': -1.1978974765722068, 'r_wrist_flex_joint': -1.605912838397527, 'time_to_reach' : 0.3}

right_up = {'r_elbow_flex_joint': -2.0722211695820745, 'r_shoulder_lift_joint': -0.35157650042211364, 'r_upper_arm_roll_joint': -0.7414411648049486, 'r_wrist_roll_joint': -2.2757713591637283, 'r_shoulder_pan_joint': -0.2699677232886195, 'r_forearm_roll_joint': -1.0189764366341232, 'r_wrist_flex_joint': -1.7970475243950452,'time_to_reach' : 0.2}


def generate():
	
	
	rs = RobotScript()
	channel_head_id = rs.addChannel("moveHeadTo")
	channel_torso_id = rs.addChannel("moveTorsoBy")
	channel_speech_id = rs.addChannel("say")
	#channel_hands_id = rs.addChannel("moveArmWithJointPos")
	
	asset_torso_id = rs.addAssetToChannel(channel_torso_id, [0], (0.2,10))
	
	asset_speech_id1 = rs.addAssetToChannel(channel_speech_id, [2], ("Initial lising",))
	#asset_hands_id1 = rs.addAssetToChannel(channel_hands_id, [2.0], {'r_elbow_flex_joint': 0.0, 'r_shoulder_lift_joint': 0.0, 'r_upper_arm_roll_joint': 0.0, 'r_wrist_roll_joint': 0.0, 'r_shoulder_pan_joint': 0.0, 'r_forearm_roll_joint': 0.0, 'r_wrist_flex_joint': 0.0})
	#asset_hands_id2 = rs.addAssetToChannel(channel_hands_id, [4],({'l_wrist_roll_joint': -0.0007893761161641422, 'l_forearm_roll_joint': -5.784708695053728e-05, 'l_elbow_flex_joint': -0.1483631860063741, 'l_shoulder_lift_joint': 0.356638539879416, 'l_upper_arm_roll_joint': 0.15967385473500117, 'l_wrist_flex_joint': -0.07863929718151064, 'l_shoulder_pan_joint': 0.0035887617206241673}))
	#asset_hands_id3 = rs.addAssetToChannel(channel_hands_id, [6], ({'l_wrist_roll_joint': 3.0377253864391696, 'l_forearm_roll_joint': 3.0636974190755852, 'l_elbow_flex_joint': -2.045293817264738, 'l_shoulder_lift_joint': 0.7999295928757233, 'l_upper_arm_roll_joint': 0.11734018057335116, 'l_wrist_flex_joint': -0.6073161853116821, 'l_shoulder_pan_joint': -0.024019141859252136}))
	#asset_hands_id4 = rs.addAssetToChannel(channel_hands_id, [8], ({'r_elbow_flex_joint': -0.6838700474140432, 'r_shoulder_lift_joint': -0.2795862208602225, 'r_upper_arm_roll_joint': -0.7924339995905723, 'r_wrist_roll_joint': -0.2403805679846016, 'r_shoulder_pan_joint': -2.37771742738202e-05, 'r_forearm_roll_joint': 5.099914879735316, 'r_wrist_flex_joint': -1.7826226439620259}))
	asset_speech_id2 = rs.addAssetToChannel(channel_speech_id, [13], ("Will Kill you,   Soon",))
	asset_head_id1 = rs.addAssetToChannel(channel_head_id, [10], (2.0,0.5))
	asset_head_id2 = rs.addAssetToChannel(channel_head_id, [20], (0.0,0.0))
	rs.play()


	


def run():
	time.sleep(10)

	PyPR2.moveTorsoBy(0.2,10)
	PyPR2.say("Initial lising")
	PyPR2.moveHeadTo(0.0,-0.5)
	
	
	time.sleep(2)
	##PyPR2.moveArmWithJointPos(**right_home)
	
	time.sleep(10)
	#PyPR2.moveArmWithJointPos(**left_shooting)
	#PyPR2.moveArmWithJointPos(**right_shooting)
	PyPR2.say("License to Kill")
	PyPR2.moveHeadTo(0.0,0.0)


def arm_back():
	obj1 = spr.Skilled_PR2()
	obj1.larm_reference = False

	obj2 = spr.Skilled_PR2()
	obj2.larm_reference = True
	
	time.sleep(10)
	obj1.arm_back()
	PyPR2.closeGripper(2)
	#obj2.arm_forward(dx=0.03)


def head_hand_follower(hand_joint_list):
	
	

	n = len(hand_joint_list)
	for i in range(0,n):
		PyPR2.moveArmWithJointPos(**hand_joint_list[i])
		x = PyPR2.getArmPose(False)
		(a,b,c) = x['position']
		PyPR2.pointHeadTo("base_footprint",a,b,c)
		time.sleep(5)


def revolve():
	x = random.randint(10,15)
	i = 0
	for i in range(0,x):
		y = PyPR2.getRobotPose()
		(a,b,c) = y['position']
		PyPR2.moveBodyTo(a,b,1.0,10)

def bow_arrow():
	PyPR2.moveArmWithJointPos(**right_shooting)
	PyPR2.moveArmWithJointPos(**left_shooting)
	time.sleep(10)
	PyPR2.closeGripper(2)
	time.sleep(3)
	PyPR2.moveArmWithJointPos(**best_pullback)
	time.sleep(1)
	PyPR2.openGripper(2)
	PyPR2.moveArmWithJointPos(**right_up)
		

def onHumanDetected(objtype, trackid, nameid, status):	
	PyPR2.say("hi")
	PyPR2.moveTorsoBy(0.1,10)
	

def onHumanTracking(tracking_objs):		
	focus_obj = tracking_obj[0]
	if focus_obj:
      		mid_x = focus_obj['bound'][0] + focus_obj['bound'][2] / 2
      		mid_y = focus_obj['bound'][1] + focus_obj['bound'][3] / 2
      		#print "track obj {} mid pt ({}.{})".format(focus_obj['track_id'],mid_x,mid_y)
      		ofs_x = mid_x - 320
      		ofs_y = mid_y - 240
      		chx = chy = 0.0
      		if math.fabs(ofs_x) > 10:
       			chx = -ofs_x * 90.0 / 640 * 0.01745329252
      		if math.fabs(ofs_y) > 10:
        		chy = ofs_y * 90.0 / 640 * 0.01745329252
      		PyPR2.updateHeadPos( chx, chy )


