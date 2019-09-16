# -*- coding: utf-8 -*-
"""

Uses a Nexus trial to create a PDF of EMG traces. Open Nexus and navigate to
the Eclipse database of interest before use. 

To run:-
python -m EMGtoPDF.py

@author: S Marchant 2019

"""

import sys

sys.path.append( 'C:\\Anaconda32\\Lib\\site-packages' )
sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.3\\SDK\\Python' )
sys.path.append( 'C:\\Program Files (x86)\\Vicon\\Nexus2.3\\SDK\\Win32' )
sys.path.append( 'C:\\Program Files\\Vicon\\Nexus2.8\\SDK\\Python' )
sys.path.append( 'C:\\Program Files\\Vicon\\Nexus2.8\\SDK\\Win32' )

import ViconNexus
vicon = ViconNexus.ViconNexus()
import Tkinter as tk
import tkFileDialog
import os
import numpy as np
from functools import partial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

root = tk.Tk()
    
class App():
    def __init__(self, root, trials):
        #tk.Frame.__init__(self, root)
        self.trials = trials
        self.sides_available = ['Left', 'Right']
        self.chan_list = trials[0].allchannels
        self.linenum = 1 #to add new lines after existing, because gridding inside new frames is a nightmare
        self.channels = []
        self.nameentry = []
        self.temp = []
        self.temp2 = []
        self.update_functions = []
        self.selectorwindow()
    
    def update_entry(self, line, channame):
        self.temp2[line].set(channame)
        
    #Select & name channels, called from selectorwindow
    def add_channel(self):
        #Select channel
        self.linenum += 1
        self.label1 = tk.Label(self.selectframe, text="Channel:")
        self.label1.grid(row=self.linenum, column=0)
        self.temp.append(tk.StringVar())
        self.temp2.append(tk.StringVar())   
        
        #Select channel
        self.update_functions.append(partial(self.update_entry, self.linenum-2))
        self.channels.append(tk.OptionMenu(self.selectframe, 
            self.temp[self.linenum-2], 
            *self.chan_list,
            command = self.update_functions[self.linenum-2]))
        self.channels[self.linenum-2].config(width = 15)
        self.channels[self.linenum-2].grid(row=self.linenum, column=1)
        
        #Write channel name
        self.label2 = tk.Label(self.selectframe, text="Name:")
        self.label2.grid(row=self.linenum, column=2)
        
        self.nameentry.append(tk.Entry(self.selectframe, 
            textvariable = self.temp2[self.linenum-2],
            width = 15))
        self.nameentry[self.linenum-2].grid(row=self.linenum, column=3)
        self.nameentry[self.linenum-2].focus_force() #otherwise you cant focus it
        
    #Exit window & write out choices, called from selectorwindow
    def leave(self):
        channelsout = [x.get() for x in self.temp]
        channelnamesout = [x.get() for x in self.temp2]
        footer = self.footer.get(1.0, tk.END)
        sideit = self.side.get()
        Trial.side = property(lambda self: sideit) #stackoverflow.com/questions/1325673
        Trial.channels_chosen = property(lambda self: channelsout)
        Trial.channel_names = property(lambda self: channelnamesout)
        Trial.footer = property(lambda self: footer)
        self.selectframe.destroy() #clear root. root.destroy closes window
        #self.emg = emg_glommer(self.chan_list, self.channelsout, self.allemg)
        Plots(root, self.trials)
    
    #Menu for selecting side & button to add channel selector
    def selectorwindow(self):
        self.selectframe = tk.Frame(root)
        self.selectframe.grid(row=0, column=0)
        self.side = tk.StringVar(self.selectframe)
        self.side_label = tk.Label(self.selectframe, text='Side:')
        self.side_menu = tk.OptionMenu(self.selectframe, self.side, *self.sides_available)
        self.side_label.grid(row=0, column=0)
        self.side_menu.grid(row=0, column=1, columnspan=2)
        
        self.add_button = tk.Button(self.selectframe, text='Add channel', command=self.add_channel)
        self.add_button.grid(row=0, column=3, padx=20)
        
        tk.Label(self.selectframe, text="Patient details:").grid(row=98, column=0)
        self.footer = tk.Text(self.selectframe, width = 30, height = 6)
        self.footer.grid(row=98, column=1, columnspan=3)
        
        self.leave_button = tk.Button(self.selectframe, text='OK', command=self.leave)
        self.leave_button.grid(row=99,column=3)
            
class Plots():
    def __init__(self, root, trials):
        self.root = root #???Jack
        self.names = trials[0].channels_chosen
        self.namesgiven = trials[0].channel_names
        
        self.plotterwindow(trials, 0)
        
    # Called from plotterwindow    
    def multiplot(self, fig, emgs, lims, strikes, footoff):
        '''
        Plots multiple EMG traces as subplots on a tkinter canvas
        '''
        x_seconds = [float(n)/2000 for n in range(self.emg_range[0], self.emg_range[1])]
        self.limits = lims
        
        for index, emg in enumerate(emgs):
            ax = fig.add_subplot(self.nofplots, 1, index+1)
            y = [n*1e6 for n in emg[self.emg_range[0] : self.emg_range[1]]]

            ax.plot(x_seconds,y,self.colour)
            plt.axis('tight')
            print(str('strikes: '+str(strikes)+' footoff: '+str(footoff)))
            for n in strikes:
                plt.axvline(x=n, color='k', linewidth=2)
            for n in footoff:
                plt.axvline(x=n, color='k', linewidth=2, linestyle='--')
            
            ax.set_ylim(-lims[index], lims[index])
            ax.set_ylabel(str(self.namesgiven[index]) + r' $\mu$V')
            if index == 0:
                ax.set_title('EMG')
            if index == len(emgs)-1:
                ax.set_xlabel('seconds')
        self.canvas.draw()
        
    def leave(self, fig, trialnumber, trials):
        fig.set_size_inches(12, 3*self.nofplots)
        fig.savefig(str('emg-plot-'+str(trialnumber)+'.png'), dpi=250)
        pdf_maker(trialnumber, trials[0].patientname, trials[0].footer)
        root.destroy()
        
    def nextwindow(self, fig, trialnumber):
        fig.set_size_inches(12, 3*self.nofplots)
        fig.savefig(str('emg-plot-'+str(trialnumber)+'.png'), dpi=250)
        self.plotterframe.destroy()
        self.plotterwindow(trials, trialnumber+1)
        print('nextwindow ran')
    
    def plotterwindow(self, trials, trialnumber):
        print('trial number: '+ str(trialnumber))
        self.emg = emg_glommer(trials[trialnumber].allchannels, 
                               trials[trialnumber].channels_chosen, 
                               trials[trialnumber].allemg)
        self.emg_range = [int(n)*20 for n in trials[trialnumber].start_end]
        
        self.axis_entry = []
        self.axes = []
        self.labels = []
        self.emgplot = []  
        
        if trials[trialnumber].side == 'Left':
            self.colour = 'r'
            trials[trialnumber].strikes = [float(n)/100 for n in trials[trialnumber].strikes[0]]
            trials[trialnumber].footoff = [float(n)/100 for n in trials[trialnumber].footoff[0]]
        elif trials[trialnumber].side == 'Right':
            self.colour = 'g'
            trials[trialnumber].strikes = [float(n)/100 for n in trials[trialnumber].strikes[1]]
            trials[trialnumber].footoff = [float(n)/100 for n in trials[trialnumber].footoff[1]]
        else:
            self.colour='k'
        
        #https://matplotlib.org/gallery/user_interfaces/embedding_in_tk_sgskip.html
        self.plotterframe = tk.Frame(root)
        self.plotterframe.grid(row=0, column=0)
        self.nofplots = len(self.names)
        self.limits = [int(n*200) for n in np.ones(self.nofplots)]
        fig = plt.figure(figsize=[8,2*self.nofplots])
        self.canvas = FigureCanvasTkAgg(fig, self.plotterframe)
        
        for index, chan in enumerate(self.names):
            self.labels.append(tk.Label(self.plotterframe, text=str(self.namesgiven[index])+' axis limits:-'))
            self.labels[index].grid(row=2*index, column=0, sticky='SW')
            
            self.axes.append(tk.IntVar())
            self.axes[index].set(200)
            self.axis_entry.append(tk.Entry(self.plotterframe, textvariable=self.axes[index]))
            self.axis_entry[index].grid(row=(2*index)+1, column=0, sticky='N')
          
        self.multiplot(fig, self.emg, self.limits, trials[trialnumber].strikes, trials[trialnumber].footoff)
        
        self.canvas.get_tk_widget().grid(row=0, column=1, rowspan=2*len(self.names))
     
        self.replot = tk.Button(self.plotterframe, 
                                text="Replot", 
                                command=lambda: self.multiplot(fig, 
                                                               self.emg, 
                                                               [n.get() for n in self.axes], 
                                                                trials[trialnumber].strikes, 
                                                                trials[trialnumber].footoff))
        self.replot.grid(row=(2*self.nofplots)+3, column=0)
        
        if trialnumber < len(trials)-1:
            print(trialnumber)
            self.gotonext = tk.Button(self.plotterframe, 
                                      text="Next",
                                      command=lambda: self.nextwindow(fig, trialnumber))  #https://mail.python.org/pipermail/tutor/2005-February/035669.html
            self.gotonext.grid(row=(2*self.nofplots)+3, column=1)        
        else:
            print(str('finish'+str(trialnumber)))
            self.quit = tk.Button(self.plotterframe, 
                              text="Finish",
                              command=lambda: self.leave(fig, trialnumber, trials)) 
            self.quit.grid(row=(2*self.nofplots)+3, column=1)
                      
def pull_trial(trialname):
    '''
    Open a trial in Nexus and output some data. Outputs:-
    channels: list of EMG channel names
    emg: list of lists where each list is an EMG channel
    patientname: self-explanatory
    strikes: list of initial contact events (frame numbers)
    foff: list of foot-off events (frame numbers)
    start_end: list of two values: frame number of trial start and of trial end
    '''
    vicon.OpenTrial(os.path.normpath(os.path.splitext(trialname)[0]),10)
    channels, emg = nexus_emg()
    emg = np.array(emg)
    patientname = vicon.GetSubjectNames()[0]
    strikes = ['', '']
    foff = ['', '']
    start_end = list(vicon.GetTrialRegionOfInterest())
    for index, side in enumerate(['Left', 'Right']):
        strikes[index] = vicon.GetEvents(patientname, side, 'Foot Strike')[0]
        foff[index] = vicon.GetEvents(patientname, side, 'Foot Off')[0]
    print(str('pulled '+trialname))
    return channels, emg, patientname, strikes, foff, start_end

def nexus_emg(*channelsReq):
    '''
    Finds and outputs the EMG channels and channel names in the open Nexus trial. 
    Inputs:-
    channelsReq (optional): channels required. If absent, all trials are output.
    '''
    emgChannelNames = []
    emg = []    
    #Slightly hacky way of finding the EMG device ID
    for n in vicon.GetDeviceIDs():
        if vicon.GetDeviceDetails(n)[0] in ("Delsys Digital IMU EMG", "Delsys Digital EMG"):
            deviceID = n
            channels = vicon.GetDeviceDetails(deviceID)[3]
        
            for channel in channels:
                analogueInput = vicon.GetDeviceChannel(deviceID, channel, 1)[0]
                channelname = vicon.GetDeviceOutputDetails(deviceID, channel)[0]
                #check channel named and check channel is in req list, if req list exists!
                if (channelname != vicon.GetDeviceOutputDetails(deviceID, channel)[1]): 
                    if len(channelsReq)==0:
                        emgChannelNames.append(channelname)
                        emg.append(analogueInput)
                    elif channelname in channelsReq: 
                        emgChannelNames.append(channelname)
                        emg.append(analogueInput)
        
    return emgChannelNames, emg    

def emg_glommer(allchannels, channels, emg): 
    '''
    Picks out chosen channels from a list of EMG channels.
    Inputs:-
    allchannels: list of all channel names in order
    channels: list of names of channels desired
    emg: list of EMG signals in the same order as channels
    Outputs a list of lists; each list is an EMG channel from the 'channels' list.
    '''
    picked_emg = np.empty((len(channels), emg.shape[1]))
    for picked_index, picked_name in enumerate(channels):
        channel_index = allchannels.index(picked_name)
        picked_emg[picked_index] = emg[channel_index]
    return picked_emg
    
def pdf_maker(trialnumber, ptname, footer):
    '''
    Makes a PDF with a top text, image, and bottom text.
    Inputs:-
    trialnumber: number of trials to plot (indexing from zero)
    ptname: patient name (string) to put in top text
    footer: text string for bottom text
    '''
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    import reportlab.platypus as platypus
    from reportlab.lib.units import cm
    
    fileprefix = 'emg-plot-'
    filesuffix = '.png'
    toptext = '<font size=14><b>EMG for %s</b></font>' % ptname    
    pdf_path = tkFileDialog.asksaveasfilename(initialdir='C:', 
                                            initialfile='EMG report %s.pdf' %ptname)                                    
    doc = platypus.SimpleDocTemplate(pdf_path,
                                     topMargin = cm, bottomMargin = cm,
                                     rightMargin = cm, leftMargin = cm)
    story = []
    
    # Make new, indented text style.
    style = getSampleStyleSheet()['Normal']
    indented = ParagraphStyle(
        'indented',
        parent=style,
        leftIndent=2*cm
        )
    
    for n in range(trialnumber+1):
        story.append(platypus.Paragraph(toptext, indented))
        story.append(platypus.Spacer(1,0.1*cm))
        graph = platypus.Image(str(fileprefix+str(n)+filesuffix))
        graph._restrictSize(19*cm, 24*cm)
        story.append(graph)
        #story.append(platypus.Spacer(1,0.5*cm))
        footer = footer.replace('\n','<br />\n') #Reportlab's Paragraph ignores newlines
        story.append(platypus.Paragraph(footer, indented))
        story.append(platypus.PageBreak())
        
    print('docbuild ran in %s' %pdf_path)
    doc.build(story)
    
if __name__ == "__main__":    
    
    trials = list()
    class Trial(object):
        def __init__(self, datalist):
            self.allchannels = datalist[0]
            self.allemg = datalist[1]
            self.patientname = datalist[2]
            self.strikes = datalist[3]
            self.footoff = datalist[4]
            self.start_end = datalist[5]
    
    trialnames = tkFileDialog.askopenfilenames(initialdir= "C:",
                           filetypes =[("c3d File", "*.c3d")],
                           title = "Select Trial Data")

    for trial in trialnames:                     
        trials.append(Trial(pull_trial(str(trial))))
    
    print('strikes & footoff below')    
    print(trials[0].strikes)
    print(trials[0].footoff)
    app = App(root, trials)
    root.mainloop()
    for n in range(len(trialnames)):
        os.remove(str('emg-plot-'+str(n)+'.png'))
    print('cleanup complete')