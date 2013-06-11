from Tkinter import *
from PIL import Image, ImageTk
from math import hypot
from glob import glob

#**************************EXECUTION FUNCTIONS************************

def run():
    """
    Advance the fetch/execute cycle a step further
    """
    global pc, mar, mbr, operator, operand, acc, add1, add2, memory, state, waitforinput, playing
    
    #FETCH
    if state == 0:
        mar = pc
    elif state == 1:    
        pc += 1
        mbr = memory[mar]
    elif state == 2:
        operator = mbr[0:2]
        operand = mbr[2:]
        state = 10+int(operator)*10-1
        
    #EXECUTE
    elif state == 10:
        #HALT
        runHandler()
        return
    
    elif state == 20:
        #INPUT
        mar = operand
    elif state == 21:
        #highlight the input field and put a cursor in it, prompting the user to
        #enter a number
        inputfield.focus_set()
        inputfield.configure(bg="white")
        #clear the field of any existing values
        inputfield.delete(0,END)
        #make sure the execution of the program does not continue until a number
        #is entered
        waitforinput = True
    elif state == 22:
        inp = link_input
        #format will validate the input, returning a five digit string whatever the input
        inp = format(inp)
        mbr = inp
    elif state == 23:
        memory[int(mar)] = mbr
        state = -1

    elif state == 30:
        #OUTPUT
        mar = operand
    elif state == 31:
        mbr = memory[int(mar)]
    elif state == 32:
        pass
        state = -1
        
    elif state == 40:
        #STORE ACCUMULATOR
        mar = operand
    elif state == 41:
        mbr = acc
    elif state == 42:
        memory[int(mar)] = mbr
        state = -1

    elif state == 50:
        #NEGATE ACCUMULATOR
        if acc[0] == "0":
            acc = "1"+acc[1:]
        else:
            acc = "0"+acc[1:]
        state = -1

    elif state == 60:
        #LOAD THE ACCUMULATOR FROM MEMORY
        mar = operand
    elif state == 61:
        mbr = memory[int(mar)]
    elif state == 62:
        acc = mbr
        state = -1

    elif state == 70:
        #ADD A NUMBER TO THE ACCUMULATOR
        add1 = format(acc,1)
        add2 = format(operand,1)
    elif state == 71:
        acc = format(add1+add2)
        state = -1

    elif state == 80:
        #ADD THE NUMBER AT A MEMORY LOCATION TO THE ACCUMULATOR
        mar = operand
    elif state == 81:
        mbr = memory[int(mar)]
    elif state == 82:
        add1 = format(acc,1)
        add2 = format(mbr,1)
    elif state == 83:
        acc = format(add1+add2)
        state = -1

    elif state == 90:
        #SUBTRACT THE NUMBER AT A MEMORY LOCATION FROM THE ACCUMULATOR
        mar = operand
    elif state == 91:
        mbr = memory[int(mar)]
    elif state == 92:
        add1 = format(acc,1)
        add2 = format(mbr,1)
    elif state == 93:
        add2 = -add2
    elif state == 94:
        acc = format(add1+add2)
        state = -1

    elif state == 100:
        #JUMP UNCONDITIONALLY TO AN INSTRUCTION
        pc = int(operand)
        state = -1

    elif state == 110:
        #JUMP TO AN INSTRUCTION IF THE ACCUMULATOR IS NEGATIVE
        if acc[0] != "0":
            pc = int(operand)
        state = -1

    elif state == 120:
        #JUMP TO AN INSTRUCTION IF THE ACCUMULATOR IS ZERO
        if format(acc,1) == 0:
            pc = int(operand)
        state = -1

    state += 1

def format(x,direction=0):
    """
    Formats a value so that it can be stored in memory correctly, or decodes a memory number so it can be added
    """
    if direction == 0:
        negative = 0
        try:
            #if the input contains any illegal characters (not - sign or digits),
            #int(x) will raise an exception, triggering the except: code
            x = int(x)
            #makes sure the number is a string, not an int or a float
            x = str(x)
            if x[0] == "-":
                negative = True
                x = x[1:]
                #makes any negative numbers positive, so they don't get rejected for
                #containing non digit characters. Also marks them as negative, so
                #that the correct format can be applied later.
        except:
            #return a valid value if the input contained illegal characters (e.g. letters)
            return "00000"

        if len(x) < 5:
            #apply leading zeros if the user entered < 5 characters
            x = "0"*(5-len(x))+x
        elif len(x) > 5:
            #truncate the number if it is longer than 5 digits
            x = x[-5:]
        if negative:
            x = "1" + x[1:]
        return x
    else:
        #a number's most significant digit indicates its sign. 0 is positive, 1 is negative
        #the digits after the first digit make up the number itself
        if x[0] == "1":
            x = -int(x[1:])
        else:
            x = int(x[1:])
        return x
            

def get_input():
    global waitforinput, link_input
    """
    Accepts input via the inputfield entry widget, as long as the CPU is waiting
    for input.
    """
    
    s = inputfield.get()
    if s != "":
        link_input = s
        waitforinput = False
        inputfield.configure(bg="grey")
        canvas.focus_set()
        return True

def inputfield_handler(event):
    global waitforinput, link_input
    
    if waitforinput == False:
        canvas.focus_set()
    else:
        if get_input():
            if playing == True:
                #pause the simulation then play it soon after, so the entered 
                #value goes straight to the MBR with no delay
                runHandler()
                canvas.after(speedSlider.get(),runHandler)


#*******************************CLASSES*******************************

class Signal(object):
    """
    Originally created to store variables relating to a signal, so they wouldn't
    have to be passed to signalLoop as parameters or global variables. Much of the
    code that was going to be in signalLoop is now here, as it's slightly easier
    to make sense of this way.
    """
    def __init__(self,ID):
        self.name = canvas.create_oval(0,0,14,14,fill="yellow",outline="",state=HIDDEN)
        self.x = 0
        self.y = 0
        self.path = []
        #next waypoint
        self.next = 1
        self.speed = 0
        #store the signal's ID (1 or 2), so that it knows which path to follow
        #when state == 1
        self.ID = ID
        
    def computePath(self,state):
        #compute the path of the signal. This consists of a set of waypoints and 
        #the signal's speed.
        #the possible values for source and dest each correspond to different
        #coordinate pairs.
        #this method also sets the explanation for the explanation box
        global explanation, red1, red2

        self.state = state
        self.path = []
        for number in [valuePC,valueMAR,valueOPERAND,valueOPERATOR,valueACC,valueADD1,valueADD2,valueMBR]:
            canvas.itemconfig(number,fill="black")
        red1 = None
        red2 = None
        h = getWireHeight(move=False)

        if state == 0:
            #signal starts at PC, ends at MAR
            self.path = [(195,78),(497,78)]
            explanation = explanations[0]
            red1 = valueMAR
        elif state == 1:
            explanation = explanations[1]
            if self.ID == 1:
                #signal starts at PC, ends at PC
                self.path = [(195,78),(281,78),(281,53),(195,53)]
            else:
                #signal starts at memory, ends at MBR
                self.path = [(466,h),(431,h),(432,416),(495,416)]
            red1 = valuePC
            red2 = valueMBR
        elif state == 2:
            #signal starts at MBR, ends at CIR
            self.path = [(495,416),(393,416),(316,338),(316,101),(156,101),(156,110)]
            explanation = explanations[2]
            red1 = valueOPERATOR
            red2 = valueOPERAND
        elif state in [20,30,40,60,80,90]:
            #signal starts at OPPERAND, ends at MAR
            self.path = [(258,171),(279,171),(372,78),(497,78)]
            explanation = explanations[3]
            red1 = valueMAR
        elif state == 21 or state == 93:
            #no values are actually copied between registers at this stage, so
            #the signal shouldn't be visible
            self.path = [(-100,-100),(-100,-100)]
            if state == 21:
                explanation = explanations[4]
            else:
                explanation = explanations[5]
                red1 = valueADD2
        elif state == 22:
            #signal starts at input box, ends at MBR
            self.path = [(538,480),(538,429)]
            explanation = explanations[6]
            red1 = valueMBR
        elif state == 23 or state == 42:
            #signal starts at MBR, ends at memory
            self.path = [(495,416),(432,416),(431,h),(466,h)]
            explanation = explanations[7]
        elif state == 32:
            #signal starts at MBR, ends at output box
            self.path = [(578,416),(640,416)]
            explanation = explanations[8]
            if speedSlider.get() < 200:
                outputlb.insert(END,mbr)
        elif state in [31,61,81,91]:
            #signal starts at memory, ends at MBR
            self.path = [(466,h),(431,h),(432,416),(495,416)]
            explanation = explanations[9]
            red1 = valueMBR
        elif state == 41:
            #signal starts at ACC, ends at MBR
            self.path = [(197,416),(495,416)]
            explanation = explanations[10]
            red1 = valueMBR
        elif state == 50:
            #no signal movement, so signals are not shown
            self.path = [(-100,-100),(-100,-100)]
            explanation = explanations[11]
            red1 = valueACC
        elif state == 62:
            #signal starts at MBR, ends at ACC
            self.path = [(495,416),(197,416)]
            explanation = explanations[12]
            red1 = valueACC
        elif state == 70:
            if self.ID == 1:
                #signal starts at ACC, ends at ADD1
                self.path = [(109,416),(86,416),(86,351)]
            else:
                #signal starts at OPPERAND, ends at ADD2
                self.path = [(258,171),(279,171),(279,338),(259,338)]
            explanation = explanations[13]
            red1 = valueADD1
            red2 = valueADD2
        elif state == 92 or state == 82:
            if self.ID == 1:
                #signal starts at ACC, ends at ADD1
                self.path = [(109,416),(86,416),(86,351)]
            else:
                #signal starts at MBR, ends at ADD2
                self.path = [(495,416),(393,416),(316,338),(259,338)]
            explanation = explanations[14]
            red1 = ADD1
            red2 = ADD2
        elif state == 94 or state == 71 or state == 83:
            #signal starts at adders, ends at ACC
            self.path = [(155,351),(155,379)]
            explanation = explanations[15]
            red1 = valueACC
        elif state == 100:
            #signal starts at OPERAND, ends at PC
            self.path = [(258,171),(279,171),(279,209),(36,209),(36,78),(112,78)]
            explanation = explanations[16]
            red1 = valuePC
        elif state == 110:
            if acc[0] != "0":
                #signal starts at OPPERAND, ends at PC
                self.path = [(258,171),(279,171),(279,209),(36,209),(36,78),(112,78)]
                explanation = explanations[16]
                red1 = valuePC
            else:
                #no signals moving
                self.path = [(-100,-100),(-100,-100)]
                explanation = explanations[17]
        elif state == 120:
            if format(acc,1) == 0:
                #signal starts at OPPERAND, ends at PC
                self.path = [(258,171),(279,171),(279,209),(36,209),(36,78),(112,78)]
                explanation = explanations[16]
                red1 = valuePC
            else:
                #no signals moving
                self.path = [(-100,-100),(-100,-100)]
                explanation = explanations[18]
        else:
            #a halt instruction has been reached
            self.path = [(-100,-100),(-100,-100)]
            explanation = "Program has ended."
                
        #ready to move towards waypoint 1
        self.next = 1

        #move to the start of the path and make self visible, ready for journey
        canvas.coords(self.name,self.getCoords(0))
        self.x = self.path[0][0]
        self.y = self.path[0][1]
        canvas.itemconfig(self.name,state=NORMAL)

        #update the explanation box now that the explanation has been decided
        #i put the explanation deciding code here because it is dependent on
        #exactly the same conditions that the signal's path is dependent on, so
        #this saves me having to write out another identical if elif loop
        updateExplanation()

    def getCoords(self,waypoint):
        """
        Returns a 4 length tuple containing the coordinates for the circle's
        top-left and bottom-right bounding box corners at a given waypoint, as required by canvas.coords
        """
        return (self.path[waypoint][0]-7,self.path[waypoint][1]-7,
                self.path[waypoint][0]+7,self.path[waypoint][1]+7)

    def setCoords(self,x=None,y=None):
        """
        Calls canvas.coords to reposition the circle, based on centre coordinates
        """
        if x==None:
            x,y = self.x, self.y
        canvas.coords(self.name,x-7,y-7,x+7,y+7)
        self.x = x
        self.y = y

    def pathLength(self):
        """
        Returns the total path length
        """
        l = 0
        for i in range(1,len(self.path)):
            l += hypot(self.path[i][0]-self.path[i-1][0],
                       self.path[i][1]-self.path[i-1][1])
        return l

    def travel(self):
        """
        Move the signal along its path a bit. Returns true when the signal
        reaches its destination.
        """
        done = self.hasReachedDest()
        if done != False:
            #make sure the signal moves from one waypoint to the next correctly
            if done == 2:
                #hide the circle and stop signalLoop if the destination is reached
                canvas.itemconfig(self.name,state=HIDDEN)
                updateRegisters()
                updateMemory()
                if self.state == 32:
                    outputlb.insert(END,mbr)
                return True
            return False
        
        #calculate the speed so that the signal arrives at its destination
        #halfway through the step period
        #speed = distance travelled every signalLoop (pixels)
        self.speed = self.pathLength()/(speedSlider.get()/85)

        #the translation vector for the current leg of the path
        self.legVec = (self.path[self.next][0]-self.x,
                  self.path[self.next][1]-self.y)
        #limit the speed so that the signal doesn't overshoot its next waypoint
        if self.speed > hypot(self.legVec[0],self.legVec[1]):
            self.speed = hypot(self.legVec[0],self.legVec[1])
        #the factor by which legVec must be multiplied to get the distance
        #travelled in one step
        self.factor = self.speed/hypot(self.legVec[0],self.legVec[1])
        self.vectorX = self.legVec[0]*self.factor
        self.vectorY = self.legVec[1]*self.factor
        self.setCoords(self.x+self.vectorX,self.y+self.vectorY)

        return False

    def hasReachedDest(self):
        """
        Snaps the signal to its destination waypoint if it's near enough, and
        sets it on its way to the next waypoint. Also returns whether the signal
        has reached its destination yet.
        """
        dist = hypot(self.path[self.next][0]-self.x,
                 self.path[self.next][1]-self.y)
        if dist < self.speed:
            #if it's near to the next waypoint, snap to it
            self.setCoords(self.path[self.next][0],
                           self.path[self.next][1])
            if self.next == len(self.path)-1:
                #this comparison ensures that the signal will be shown at its
                #destination before dissapearing
                if dist == 0:
                    #signal has reached its final waypoint
                    return 2
                else:
                    return True
            else:
                self.next += 1
                if hypot(self.path[self.next][0]-self.x,
                 self.path[self.next][1]-self.y) > self.speed/2:
                    return True
            
        return False

class memoryListbox(Listbox):
    def yview(self,arg1,arg2,arg3=None):
        if arg3==None:
            Listbox.yview(self,arg1,arg2)
        else:
            Listbox.yview(self,arg1,arg2,arg3)
        getWireHeight()

class Placeholder(object):
    def __init__(self):
        self.widget = bEdit

#**************************DISPLAY FUNCTIONS**************************

def runLoop():
    global runAlarmId
    """
    A function which causes the simulation to run and keep running
    """
    step(None)
    
    if playing == True:
        #set a timer which will call runLoop again after speedslider milliseconds
        runAlarmId = canvas.after(speedSlider.get(),runLoop)

def runHandler():
    """
    Initiates the runLoop and sets it to continue, or stops it if it's already running
    """
    global playing
    if playing == True:
        bRun["image"] = runImage
        playing = False
        canvas.after_cancel(runAlarmId)
    else:
        bRun["image"] = pauseImage
        playing = True
        runLoop()

def printCoords(event):
    #this event handler displays the coordinates of the point in the window that
    #the mouse clicks on. I used it to position canvas items easily
    s = "%d, %d" % (event.x, event.y)
    lbl["text"] = s

def resetHandler():
    #resets the simulation to the state it was in with the program freshly loaded
    global memory, state, waitforinput, stateState, playing, signalAlarmId, cycle
    global state, pc, mar, mbr, operator, operand, acc, add1, add2
    
    memory = eval(startState)
    state = 0
    waitforinput = False
    cycle = 0
    canvas.focus_set()
    canvas.itemconfig(inputfield,bg="grey")
    if playing == True:
        runHandler()
    
    pc = 0
    mar = 0
    mbr = "00000"
    operator = "00"
    operand = "000"
    acc = "00000"
    add1 = "00000"
    add2 = "00000"
    updateMemory()
    updateRegisters()
    updateExplanation()

    #hide the signal objects and stop them from doing anything
    try:
        canvas.after_cancel(signalAlarmId)
    except:
        pass
    canvas.itemconfig(signal1.name,state=HIDDEN)
    canvas.itemconfig(signal2.name,state=HIDDEN)

def clearOutput():
    outputlb.delete(0,END)

def bStepHandler():
    #bStep cannot be command bound to the step function, as step expects an
    #argument, which can only be supplied by an event bind. I could event bind
    #bStep to the step function via the left mouse press event, but then the
    #button would be invoked as soon as the user clicked the button, without
    #waiting until the mouse button was released.
    if playing == True:
        #pausing then instantly playing makes the simulator skip the current
        #step, if the step button is pressed while the simulation is still running
        runHandler()
        runHandler()
    else:
        step(None)


def step(event):
    global cycle
    if waitforinput == True or bEdit["command"] == "":
        return

    if state == 0:
        cycle += 1
    print red1, red2
    updateRegisters()
    updateMemory()
    memorylb.see(int(mar))
    
    print "executing state",state
    laststate = state
    run()       
    
    signalLoop(laststate,start=True)
    updateExplanation()
    print state, "next"

def signalLoop(state,start=False):
    global signalAlarmId, t, explanation
    """
    A function which updates the position of one or two signal objects on the
    screen until they reach their destinations.
    """
    if signalAlarmId != None:
        canvas.after_cancel(signalAlarmId)
        
    if start == True:
        canvas.itemconfig(signal2.name,state=HIDDEN)
        signal1.computePath(state)
        if state in [1,70,82,92]:
            signal2.computePath(state)
        else:
            signal2.path = []
        signalAlarmId = canvas.after(25,signalLoop,state)
    else:
        if signal2.path != []:
            signal2.travel()
        if signal1.travel() == False:
            signalAlarmId = canvas.after(25,signalLoop,state)
        else:
            canvas.itemconfig(signal2.name,state=HIDDEN)

    if speedSlider.get() < 200:
        #don't show any signals moving at this speed, just update the registers
        #instantly
        #i put the abort code at the bottom of this function so that computePath
        #is still executed by the signal, so that explanation will still be set
        canvas.itemconfig(signal1.name,state=HIDDEN)
        canvas.itemconfig(signal2.name,state=HIDDEN)
        if playing: explanation = "Simulation is running very fast"
        updateExplanation()
        updateRegisters()
        updateMemory()
        canvas.after_cancel(signalAlarmId)
        return

def getWireHeight(event=None,move=True):
    """
    Positions the MBR <-> memory wire and returns the y coordinate of the top of
    it.
    """
    h = 110+(int(mar)-Listbox.yview(memorylb)[0]*128)*266/19.0
    if h < 110:
        h = 110
    if h > 363:
        h = 363
    if move:
        canvas.coords(vertWire,430,h,432,417)
        canvas.coords(horWire,430,h,470,h+2)
    return h

def clear(event):
    memorylb.select_clear(0,END)

def updateMemory():
    #update the memory display and make sure the cell indicated by the MAR is
    #highlighted
    global memory
    memorylb.delete(0,END)
    for i in range(128):
        s = str(i)+" "*(8-2*len(str(i)))+memory[i]
        memorylb.insert(END,s)
    memorylb.selection_set(int(mar))

def updateRegisters():
    #update registers on the screen
    print "pc: ", pc
    
    canvas.itemconfig(valuePC,text=str(pc))
    canvas.itemconfig(valueMAR,text=mar)
    canvas.itemconfig(valueMBR,text=mbr)
    canvas.itemconfig(valueOPERATOR,text=operator)
    canvas.itemconfig(valueOPERAND,text=operand)
    canvas.itemconfig(valueACC,text=acc)
    canvas.itemconfig(valueADD1,text=add1)
    canvas.itemconfig(valueADD2,text=add2)
    print red1, red2
    if red1:
        canvas.itemconfig(red1,fill="red")
    if red2:
        canvas.itemconfig(red2,fill="red")
    getWireHeight()

def updateExplanation():
    global explanation
    #update the explanation box so that all the text in it is up to date
    if state < 3:
        phase = "FETCH"
    else:
        phase = "EXECUTE"
    c = cycle
    if c < 0:
        c = 0
        
    s = "CYCLE %d: %s\nExplanation: %s" % (c,phase,explanation)
    
    expLabel["text"] = s

#*************************PROGRAM EDIT FUNCTIONS**********************

def editHandler():
    global lino
    global linoFrame
    global textbox
    #lino and textbox have been made global so they can be refered to by other
    #functions, e.g. textboxClickHandler
    
    #pause the simulator if it isn't paused already
    if playing == True:
        runHandler()
    #unbind the run control buttons, making them unresponsive
    bRun["command"]=""
    bReset["command"]=""
    bStep["command"]=""
    #grey them out too
    bRun.config(state=DISABLED)
    bReset.config(state=DISABLED)
    bStep.config(state=DISABLED)
    root.bind("<Return>","")
    #make the edit button a finish edit button
    bEdit["text"] = "Finish editing"
    bEdit["command"] = finishHandler

    #create a small frame underneath the textbox to display the line number the
    #text cursor is currently at
    memScroll.pack_forget()
    linoFrame = Frame(memframe,borderwidth=2,relief=SUNKEN)
    linoFrame.pack(side=BOTTOM,anchor=W,fill=X)
    lino = Label(linoFrame,text="Line:0")
    lino.pack(side=LEFT)
    memScroll.pack(side=RIGHT,fill=Y)
    
    #remove the memory listbox and replace it with a text widget (textbox)
    memorylb.pack_forget()
    textbox = Text(memframe,width=18,yscrollcommand=memScroll.set,
                   spacing1=1,maxundo=32)
    textbox.pack(side=RIGHT)
    #now reassign the scrollbar to the textbox
    memScroll.config(command=textbox.yview)
    #place the memory's current contents into the textbox
    for cell in memory:
        textbox.insert(END,cell+"\n")
    #bind the textbox's left click event to a handler that updates the lino
    textbox.bind("<ButtonRelease-1>",textboxCursorHandler)
    textbox.bind("<KeyRelease>",textboxCursorHandler)

    #update the explanation for this button
    enterButton(Placeholder())
    #enable assembly
    bConvert.config(state=NORMAL)

def textboxCursorHandler(event):
    line = textbox.index(INSERT)
    line = line[:line.index(".")]
    lino["text"] = "Line:"+str(int(line)-1)

def finishHandler():
    global memory, startState
    #decode any assembly code into machine code
    bConvert["text"] = "Assemble"
    code = bConvertHandler()
    if isinstance(code,list):
        #decoding was successful, no errors were detected
        #make the finish edit button an edit button
        bEdit["text"] = "Edit program"
        bEdit["command"] = editHandler

        #now undo all the changes made by editHandler
        linoFrame.pack_forget()
        textbox.pack_forget()
        memorylb.pack(side=RIGHT,fill=Y)
        #re-bind the scrollbar to the memory listbox
        memScroll.config(command=memorylb.yview)
        #now load the new program into memory
        memory = []
        for line in code:
            memory.append(line)
        checkLength()
        updateMemory()
        
        #re-bind the run control buttons
        bRun["command"]=runHandler
        bReset["command"]=resetHandler
        bStep["command"]=bStepHandler
        #enable run buttons
        bRun.config(state=NORMAL)
        bReset.config(state=NORMAL)
        bStep.config(state=NORMAL)
        
        #reset button will now return the simulator to the correct state
        startState = str(memory)
        #update the explanation for this button
        enterButton(Placeholder())
        #disable assembly
        bConvert.config(state=DISABLED)
        
def save():
    global saveFrame
    global saveField
    if bEdit["command"] == "":
        #simulation is in edit mode, get program from textbox
        program = textbox.get().split("\n")
    else:
        #simulation is in run mode, get program from memory list
        program = memory

    #prompt the user to enter a name for the save file
    bEdit.grid_forget()
    bSave.grid_forget()
    bLoad.grid_forget()
    bConvert.grid_forget()
    saveFrame = Frame(controlFrame)
    saveFrame.grid(row=6,columnspan=2)
    Label(saveFrame,text="Save program as:").grid(row=0,columnspan=2,sticky=W)
    saveField = Entry(saveFrame)
    saveField.grid(row=1,columnspan=2,sticky=W)
    saveField.bind("<Return>",store)
    saveField.focus_set()
    Button(saveFrame,text="Cancel",command=cancelSave).grid(row=2,sticky=E+W)
    
def cancelSave():
    """
    Removes the save "dialogue" widgets and brings back the normal file widgets
    """
    saveFrame.grid_forget()
    bEdit.grid(row=5,columnspan=2,sticky=E+W,padx=5,pady=5)
    bSave.grid(row=6,sticky=E+W,padx=5,pady=5)
    bLoad.grid(row=6,column=1,sticky=E+W,padx=5,pady=5)
    bConvert.grid(row=7,columnspan=2,sticky=E+W,padx=5,pady=5)

def store(event):
    name = saveField.get()
    if name[-4:] != ".txt":
        name += ".txt"
    fout = open(name,"w")
    fout.write("PROGRAM FILE\n")
    if bEdit["command"] == "":
        fout.write(textbox.get())
    else:
        for cell in memory:
            fout.write(str(cell)+"\n")
    cancelSave()

def load():
    global fileslb, bLoadCancel
    #first, dissable the file buttons
    bEdit["command"]=""
    bSave["command"]=""
    bLoad["command"]=""

    #now gather a list of all program text files in the same directory
    #glob("*.txt") returns a list of the names of all text files in this directory
    names = []
    for name in glob("*.txt"):
        if open(name).readline().strip() == "PROGRAM FILE":
            names.append(name)
    print names

    #replace the lino box with a cancel button
    if bEdit["text"] == "Finish editing":
        textbox.pack_forget()
        linoFrame.pack_forget()
    bLoadCancel = Button(memframe,text="Cancel",command=cancelLoad)
    bLoadCancel.pack(side=BOTTOM,fill=X) 
    
    #remove the memory listbox and replace it with a new one to display the
    #available program files
    memorylb.pack_forget()
    
    fileslb = Listbox(memframe,width=20,yscrollcommand=memScroll.set)
    fileslb.pack(side=RIGHT,fill=Y)
    memScroll.config(command=fileslb.yview)
    fileslb.bind("<Double-Button-1>",read)
    for name in names:
        fileslb.insert(END,name)
    
def cancelLoad():
    if bEdit["text"] == "Edit program":
        #simulator is in run mode
        #remove the files listbox and put the memory listbox back
        fileslb.pack_forget()
        bLoadCancel.pack_forget()
        memorylb.pack(side=LEFT,fill=Y)
        canvas.itemconfig(memorylb,yscrollcommand=memScroll)
        memScroll.config(command=memorylb.yview)
    else:
        #remove the files listbox and put the textbox and linoFrame back
        fileslb.pack_forget()
        bLoadCancel.pack_forget()
        linoFrame.pack(side=BOTTOM,fill=X)
        textbox.pack(side=LEFT,fill=Y)
        canvas.itemconfig(textbox,yscrollcommand=memScroll)
        memScroll.config(command=textbox.yview)

    #reactivate the edit and save buttons
    if bEdit["text"] == "Edit program":
        bEdit["command"]=editHandler
    else:
        bEdit["command"]=finishHandler
    bSave["command"]=save
    bLoad["command"]=load
        
def read(event):
    global memory, textbox, startState
    name = fileslb.get(ACTIVE)
    fin = open(name)
    #read the program into a list, but ommit the first line which is a marker
    #and not part of the program
    lines = fin.readlines()[1:]
    startstate = []
    
    if bEdit["text"] == "Edit program":
        #simulator is in run mode, so put the program into memory
        memory = []
        for line in lines:
            memory.append(format(line.strip()))
        checkLength()
        updateMemory()
        #now put the old widgets back in place
        cancelLoad()
        startState = str(memory)
    else:
        #simulator is in edit mode, so put the program into the textbox
        textbox.delete("0.0",END)
        for line in lines:
            textbox.insert(END,line)
        #now put the old widgets back in place
        cancelLoad()

def checkLength(numbers=None):
    global memory
    if numbers == None:
        numbers = memory
    #make sure the memory has 128 data in it
    numbers = numbers[:128-numbers.count("")]
    if len(numbers) < 128:
        numbers += ["00000"]*(128-len(numbers))
    elif len(numbers) > 128:
        numbers = numbers[:128]
    memory = numbers
    return numbers

def bConvertHandler():
    #first get a list containing all the lines of text in the textbox
    #for some reason this list has two "" elements at the end of it, so those
    #are removed
    code = textbox.get("0.0",END).split("\n")[:-2]
    code = checkLength(code)
    code = convert(code,bConvert["text"]=="Convert to assembly")
    if isinstance(code,list):
        #put the translated code into the textbox
        textbox.delete("0.0",END)
        for line in code:
            textbox.insert(END,line+"\n")
        if bConvert["text"] == "Assemble":
            bConvert["text"] = "Convert to assembly"
        else:
            bConvert["text"] = "Assemble"
    else:
        #if convert didn't return a list then an error must have been encountered,
        #and it has returned the line number of that error. So flag the error
        #Tkinter line indexes start at 1
        code += 1
        textbox.tag_add("error","%d.0" % code,"%d.end" % code)
        textbox.tag_config("error",background="#FF5555")
        print textbox.tag_ranges("error")
    return code

def convert(code,direction=0):
    result = []
    #if direction=0, convert to machine code, otherwise convert to assembly
    mnemonics = ["HLT","INP","OUT","STA","NEG","LDA","ADN","ADL","SUB","JMP","JPN","JPZ","DAT"]
    if direction == 0:
        for i in range(len(code)):
            if code[i].isdigit():
                #any instructions already in machine code pass straight through
                if code[i] == format(code[i]):
                    result.append(code[i])
                else:
                    #unless it's invalid machine code, in which case it's flagged
                    return i
                continue
            #get the mnemonic part of the instruction
            mnemonic = code[i][:3]
            try:
                #translate the mnemonic into an operator
                operator = str(mnemonics.index(mnemonic))
                if len(operator) < 2:
                    operator = "0"+operator
                result.append(operator)
            except:
                #if an error occured then it's because something was wrong with
                #the mnemonic, i.e. programmer made a syntax error
                #so return the line index, so the calling function will know
                #there was a problem
                print ">>>"+code[i]
                print i
                return i
            #append the operand part to the instruction and format it to protect against syntax errors
            result[-1] += code[i][4:]
            result[-1] = format(result[-1])
    else:
        for i in range(len(code)):
            if not code[i].isdigit():
                #if the line contains non-digit characters, then assume that it's
                #already in assembly language. It might not be, it might be due
                #to mistake such as a letter accidentally entered, but this is
                #simpler than checking to make sure it is a valid assembly
                #instruction. If it isn't, then it'll be flagged when the user
                #tries to run the program anyway.
                result.append(code[i])
                continue
            if code[i] != format(code[i]):
                #if the value doesn't contain letters but still isn't a valid
                #memory value, then it's definately an error and should be flagged
                return i
            #get the operator part of the instruction
            operator = code[i][:2]
            try:
                #translate the operator into a mnemonic
                result.append(mnemonics[int(operator)]+" ")
            except:
                #if the above line can't identify the correct mnemonic then the
                #first two characters of the instruction were not a valid
                #operator. This must be because the value was intended to be
                #data stored in memory, not an instruction. It cannot be because
                #the first two characters contained a non-digit, because if they
                #did then the value would be treated as assembly and passed
                #straight through. Therefore translate it into a DAT mnemonic.
                result.append("DAT "+code[i])
                continue
            result[-1] += code[i][2:]
    #no errors found, so remove any red error flags
    textbox.tag_delete("error")
    return result

def enterButton(event):
    if event.widget == bRun:
        if bEdit["text"] == "Edit program":
            infoMessage["text"] = "Run the program currently held in memory."
        else:
            infoMessage["text"] = "This button is dissabled while in edit mode."
    elif event.widget == bReset:
        if bEdit["text"] == "Edit program":
            infoMessage["text"] = "Reset memory and all registers, ready to re-run the program."
        else:
            infoMessage["text"] = "This button is dissabled while in edit mode."
    elif event.widget == bStep:
        if bEdit["text"] == "Edit program":
            infoMessage["text"] = "Advance through the execution by a small step."
        else:
            infoMessage["text"] = "This button is disabled while in edit mode."
    elif event.widget == bEdit:
        if bEdit["text"] == "Edit program":
            infoMessage["text"] = "Edit the program currently held in memory."
        else:
            infoMessage["text"] = "Transfer the current program into memory."
    elif event.widget == bSave:
        infoMessage["text"] = "Save the current program as a text file."
    elif event.widget == bLoad:
        infoMessage["text"] = "Load a program from a text file in the same directory."
    elif event.widget == bConvert:
        if bEdit["text"] == "Edit program":
            infoMessage["text"] = "This button can only be used in edit mode."
        elif bConvert["text"] == "Convert to assembly":
            infoMessage["text"] = "Convert the current program to assembly code."
        else:
            infoMessage["text"] = "Convert the current program to machine code."
            

def leaveButton(event):
    if bEdit["text"] == "Edit program":
        infoMessage["text"] = "Simulator is in run mode."
    else:
        infoMessage["text"] = "Simulator is in edit mode."

#****************************MAIN CODE BODY***************************


#INITIALISE

#initialise registers
pc = 0
mar = 0
mbr = "00000"
operator = "00"
operand = "000"
acc = "00000"
add1 = "00000"
add2 = "00000"

#initialise memory with a simple countdown program
memory = ["00000"]*128
memory[0] = "01016"
memory[1] = "05016"
memory[2] = "02016"
memory[3] = "06101"
memory[4] = "03016"
memory[5] = "11007"
memory[6] = "09002"
memory[7] = "02016"

"""
I've kept the previous program here so I don't have to write it out again.
memory[0] = "01016"
memory[1] = "01017"
memory[2] = "05016"
memory[3] = "08017"
memory[4] = "10007"
memory[5] = "02016"
memory[6] = "00000"
memory[7] = "02017"
memory[8] = "00000"
"""

#store a reference of what memory was at the start, so the simulation can be reset
#it is necessary to store it a string, as startState = memory would produce a
#list that was linked to memory and would be modified whenever memory was.
startState = str(memory)

#I put this docstring here to show my instruction set, so I can program in machine code easier
"""
0	HLT	N/A
1	INP	MemoryMAR  [MBR]
2	OUT	MBR  [Memory]MAR
3	STA	MBR  [ACC]
                MemoryMAR  [MBR]
4	NEG     ACC  -[ACC]
5	LDA	MBR  [Memory]MAR
                ACC  [MBR]
6	ADN	ADD1  [ACC]
                ADD2  [OPERAND]
                ACC  [ADD1] + [ADD2]
7	ADL	ADD1  [ACC]
                MBR  [Memory]MAR 
                ADD2  [MBR]
                ACC  [ADD1] + [ADD2]
8       SUB     MAR  [OPERAND]
                ADD1  [ACC]
                MBR  [Memory]MAR
                ADD2  [MBR]
                ADD2  -[ADD2]
                ACC  [ADD1] + [ADD2]
9	JMP	PC  [OPERAND]
10	JPN	If ACC < 0:
                   PC  [OPERAND]
11	JPZ	If ACC == 0:
                   PC  [OPERAND]
<data>	DAT	N/A
"""

#CREATE GRAPHICAL OBJECTS

#CREATE WINDOW AND CANVAS
root = Tk()
root.title("CPU Simulator")
root.geometry("790x560")
root.resizable(0,0)

canvas = Canvas(root)
canvas.pack(expand=YES,fill=BOTH)
canvas.configure(bg="grey")

#CREATE CANVAS ITEMS
#create background image
background = Image.open("CPU background Mk3.bmp")
background = ImageTk.PhotoImage(background)
canvas.create_image(0,0,image=background,anchor=NW)

#program counter
valuePC = canvas.create_text(155,79,font=("Ariel",16))
canvas.itemconfig(valuePC,text="0")

#opcode register
valueOPERATOR = canvas.create_text(101,173,font=("Ariel",16))
canvas.itemconfig(valueOPERATOR,text="00")

#operand register
valueOPERAND = canvas.create_text(206,173,font=("Ariel",16))
canvas.itemconfig(valueOPERAND,text="000")

#memory address register
valueMAR = canvas.create_text(539,80,font=("Ariel",16))
canvas.itemconfig(valueMAR,text="000")

#memory buffer register
valueMBR = canvas.create_text(537,417,font=("Ariel",16))
canvas.itemconfig(valueMBR,text="00000")

#add1
valueADD1 = canvas.create_text(97,338,font=("Ariel",16))
canvas.itemconfig(valueADD1,text="00000")

#add2
valueADD2 = canvas.create_text(213,338,font=("Ariel",16))
canvas.itemconfig(valueADD2,text="00000")

#accumulator
valueACC = canvas.create_text(154,416,font=("Ariel",16))
canvas.itemconfig(valueACC,text="00000")


#a listbox to display the memory contents
#it must be put in a frame, so that the scrollbar can be packed next to it easily
memframe = Frame(canvas)
memframe.place(x=466,y=100,height=270)
memorylb = memoryListbox(memframe)
memorylb.pack(side=LEFT,fill=Y)
updateMemory()

#a scrollbar must be created and attached to the listbox, so that all 128 cells
#can be viewed
memScroll = Scrollbar(memframe)
#make sure the scrollbar will adjust if the listbox scrolls for any other reason
memorylb.config(yscrollcommand=memScroll.set)
memScroll.config(command=memorylb.yview)
memScroll.pack(side=RIGHT,fill=Y)
#create the MBR <-> memory wire rectangles
vertWire = canvas.create_rectangle(0,0,0,0,fill="#EBE741",outline="")
horWire = canvas.create_rectangle(0,0,0,0,fill="#EBE741",outline="")
getWireHeight()

#explanation box
expFrame = Frame(canvas,width=450,height=80,bg="#CCCC66",relief=RIDGE,borderwidth=5)
expFrame.propagate(False)
expFrame.pack(side=LEFT,anchor=S)
expLabel = Message(expFrame,bg="#CCCC66",justify=LEFT,padx=2,width=450)
expLabel.pack(anchor=W)


#put a frame at the bottom of the window to act as an input module
inputframe = Frame(canvas,width=190,height=80,bg="cyan",relief=RIDGE,borderwidth=5)
inputframe.pack(side=LEFT,anchor=S)
inputframe.propagate(False)
#inputbuffer does the job that internal padding in the frame should do but doesn't
inputbuffer = Label(inputframe,text="    ",bg="cyan")
inputbuffer.pack(side=RIGHT)
#this field allows users to enter numbers requested by the CPU
inputfield = Entry(inputframe,bg="grey",width=20)
inputfield.pack(side=RIGHT)
inputfield.bind("<Return>",inputfield_handler)
inputlabel = Label(inputframe,text="Input:",bg="cyan")
inputlabel.pack(side=RIGHT)


#output box
outputframe = Frame(canvas,width=150,height=200,bg="blue",relief=RIDGE,borderwidth=5)
outputframe.pack(side=BOTTOM,anchor=S)
outputframe.propagate(False)
outputlabel = Label(outputframe,text="OUTPUT:",bg="blue",font=("Ariel",10))
outputlabel.grid(sticky=W)

#put a scroll bar next to the output box, in case someone's program produces lots
#of output.

outputlb = Listbox(outputframe)
outputlb.grid(row=1,column=0)

outScroll = Scrollbar(outputframe)
outScroll.grid(row=1,column=1,sticky=N+S)

#bind the scroll bar and the listbox to each other
outputlb.config(yscrollcommand=outScroll.set)
outScroll.config(command=outputlb.yview)

#place a clear button undernear the listbox
outputClearButton = Button(outputframe,text="Clear",foreground="red",command=clearOutput)
outputClearButton.grid(row=2,column=0,columnspan=2,sticky=E+W)

#CONTROL PANEL
controlFrame = Frame(canvas,width=150,bg="lightgrey",relief=RIDGE,borderwidth=5)
controlFrame.pack(side=RIGHT,expand=YES,fill=BOTH)
#create run control buttons
#load button images
runImage = Image.open("Run button.bmp")
runImage = ImageTk.PhotoImage(runImage)
pauseImage = Image.open("Pause button.bmp")
pauseImage = ImageTk.PhotoImage(pauseImage)
resetImage = Image.open("Reset button.bmp")
resetImage = ImageTk.PhotoImage(resetImage)
stepImage = Image.open("Step button.bmp")
stepImage = ImageTk.PhotoImage(stepImage)

bRun = Button(controlFrame,image=runImage,width=18,command=runHandler)
bRun.grid(row=0,column=0,padx=5,pady=5,columnspan=2,sticky=E+W)

bReset = Button(controlFrame,image=resetImage,width=49,command=resetHandler)
bReset.grid(row=1,column=0,padx=5,pady=5,sticky=W)

bStep = Button(controlFrame,image=stepImage,width=49,command=bStepHandler)
bStep.grid(row=1,column=1,padx=5,pady=5,sticky=E)

#create a slider to control the running speed
speedSlider = Scale(controlFrame,from_=4000,to=5,orient=HORIZONTAL,length=120,
                    sliderlength=12,showvalue=False,label="Speed",repeatinterval=1)
speedSlider.grid(columnspan=2)
speedSlider.set(4000)
Label(controlFrame,text="Slow",bg="#D3D3D3").grid(sticky=W)
Label(controlFrame,text="Fast",bg="#D3D3D3").grid(row=3,column=1,sticky=E)

#create edit buttons
#a partition between the two sets of buttons:
Frame(controlFrame,height=2,borderwidth=1,relief=SUNKEN).grid(row=4,columnspan=2,sticky=E+W,pady=8)

bEdit = Button(controlFrame,text="Edit program",command=editHandler)
bEdit.grid(row=5,columnspan=2,sticky=E+W,padx=5,pady=5)

bSave = Button(controlFrame,text="Save",command=save)
bSave.grid(row=6,sticky=E+W,padx=5,pady=5)

bLoad = Button(controlFrame,text="Load",command=load)
bLoad.grid(row=6,column=1,sticky=E+W,padx=5,pady=5)

bConvert = Button(controlFrame,text="Convert to assembly",command=bConvertHandler,state=DISABLED)
bConvert.grid(row=7,column=0,columnspan=2,sticky=E+W,padx=5,pady=5)

#make a frame to display a brief explanation of whichever button the mouse is
#hovering over
infoFrame = Frame(controlFrame,background="lightgrey",borderwidth=3,
                  relief=SUNKEN,height=50)
infoFrame.propagate(False)
infoMessage = Message(infoFrame,text="Simulator is in run mode.",anchor=NW,aspect=220)
infoFrame.grid(row=8,columnspan=2,sticky=E+W,padx=5,pady=5)
infoMessage.pack(expand=YES,fill=BOTH)

#bind each button to a handler that will make the correct explanation appear
bRun.bind("<Enter>",enterButton)
bRun.bind("<Leave>",leaveButton)
bReset.bind("<Enter>",enterButton)
bReset.bind("<Leave>",leaveButton)
bStep.bind("<Enter>",enterButton)
bStep.bind("<Leave>",leaveButton)
bEdit.bind("<Enter>",enterButton)
bEdit.bind("<Leave>",leaveButton)
bSave.bind("<Enter>",enterButton)
bSave.bind("<Leave>",leaveButton)
bLoad.bind("<Enter>",enterButton)
bLoad.bind("<Leave>",leaveButton)
bConvert.bind("<Enter>",enterButton)
bConvert.bind("<Leave>",leaveButton)

#bind an event handler to the enter key, allowing the simulator to respond by
#proceeding another step with the run function and updating the registers
#appropriately:
root.bind("<Return>",step)

#create two signal objects that can be referenced later
signal1 = Signal(1)
signal2 = Signal(2)

#initialise the execution state as 0:
state = 0
#if this variable is True, the step function will abort when it is called
#if it is false, the inputfield's event handler will abort when it is called
waitforinput = False
#this variable is used to transfer an inputted string from get_input to run
link_input = ""
#a variable to indicate whether the simulation should be running or not
playing = False
#stores the id of the alarm that will eventually call runLoop again, so that it
#can be cancelled if necessary
runAlarmId = None
#stores the id of the alarm that will trigger the signals to move, so that it
#can be cancelled if necessary
signalAlarmId = None
#the program must remember which cycle it's on, so the exlpanation box can
#dislpay it
cycle = -1
#these variables indicate which number should be highlighted in red once the
#signal(s) reach their destinations
red1 = None
red2 = None

#load the explanations file so the explanations are available
fin = open("explanations.txt")
precursor = fin.readlines()
fin.close()
explanations = []
#remove \n characters and comments and blank lines
for i in range(len(precursor)):
    precursor[i] = precursor[i].strip()
    if precursor[i] != "":
        if precursor[i][0] != "#":
            explanations.append(precursor[i])
#put some text in the explanation box
explanation = "The simulation isn't running yet."
updateExplanation()

#start Tkinter's mainloop
root.mainloop()
