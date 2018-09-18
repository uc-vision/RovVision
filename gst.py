# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
############# gst ########
#to watch
#gst-launch-1.0 -e -v udpsrc port=5700 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
#gst-launch-1.0 -e -v udpsrc port=5701 ! application/x-rtp, payload=96 ! rtph264depay ! avdec_h264 ! autovideosink
from subprocess import Popen,PIPE
import sys,time,select,os
import numpy as np
import config
############# gst wirite #########
gst_pipes=None
def init_gst(sx,sy,npipes):
    global gst_pipes
    #cmd="gst-launch-1.0 {}! x264enc tune=zerolatency  bitrate=500 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
    if 0: #h264 stream
        cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=300 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
        gstsrc = 'fdsrc ! videoparse width={} height={} framerate=30/1 format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
    
    if 1:
        #cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=500 key-int-max=15 ! rtph264pay ! udpsink host=127.0.0.1 port={}"
        cmd="gst-launch-1.0 {}! x264enc threads=1 tune=zerolatency  bitrate=500 key-int-max=50 ! tcpserversink port={}"
        gstsrc = 'fdsrc ! videoparse width={} height={} format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
    if 0:
        gstsrc = 'fdsrc ! videoparse width={} height={} framerate=30/1 format=15 ! videoconvert ! video/x-raw, format=I420'.format(sx,sy) #! autovideosink'
       
        cmd="gst-launch-1.0 {} ! jpegenc quality=20 ! rtpjpegpay ! udpsink host=192.168.2.1 port={}"

    gst_pipes=[]
    for i in range(npipes):
        gcmd = cmd.format(gstsrc,config.gst_ports[i])
        p = Popen(gcmd, shell=True, bufsize=0,stdin=PIPE, stdout=sys.stdout, close_fds=False)
        gst_pipes.append(p)

def send_gst(imgs):
    global gst_pipes
    for i,im in enumerate(imgs):
        time.sleep(0.001)
        if len(select.select([],[gst_pipes[i].stdin],[],0)[1])>0:
            gst_pipes[i].stdin.write(im.tostring())

def init_gst_files(sx,sy):
   pass


############# gst read #########
gst_pipes_264=None
sx,sy=config.pixelwidthx, config.pixelwidthy
shape = (sx, sy, 3)

def init_gst_reader(npipes):
    global gst_pipes,gst_pipes_264
    if 1: #h264
        cmd='gst-launch-1.0 tcpclientsrc port={} ! identity sync=true  ! tee name=t ! queue ! filesink location=fifo_264_{}  sync=false  t. ! queue !'+\
        ' h264parse ! decodebin ! videoconvert ! video/x-raw,height={},width={},format=RGB ! filesink location=fifo_raw_{}  sync=false'
    if 0:
        cmd='gst-launch-1.0 -q udpsrc port={} ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,height={},width={},format=RGB ! fdsink'
    
    gst_pipes=[]
    gst_pipes_264=[]
    os.system('rm fifo_*')
    cmds=[]
    for i in range(npipes):
        fname_264='fifo_264_'+'lr'[i]
        os.mkfifo(fname_264)
        r = os.open(fname_264,os.O_RDONLY | os.O_NONBLOCK)
        fname_raw='fifo_raw_'+'lr'[i]
        os.mkfifo(fname_raw)
        r1 = os.open(fname_raw,os.O_RDONLY | os.O_NONBLOCK)
        gcmd = cmd.format(config.gst_ports[i],'lr'[i],sy,sx,'lr'[i])
        print(gcmd)
        cmds.append(gcmd)
        gst_pipes_264.append(r)
        gst_pipes.append(r1)
    for cmd in cmds: #start together 
        Popen(cmd, shell=True, bufsize=0)

images=[None,None]
save_files_fds=[None,None,None]

def get_imgs():
    global images
    for i in range(len(images)):
        if len(select.select([ gst_pipes[i] ],[],[],0.001)[0])>0 :
            data=os.read(gst_pipes[i],sx*sy*3)
            images[i]=np.fromstring(data,'uint8').reshape([sy,sx,3])
        if len(select.select([ gst_pipes_264[i] ],[],[],0.001)[0])>0:
            data=os.read(gst_pipes_264[i],1*1000*1000)
            if save_files_fds[0] is not None:
                save_files_fds[i].write(data)
    return images


#############################


