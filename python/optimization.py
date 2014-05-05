__author__ = 'Martin Lichtman'


#current believed motor position
x0=np.zeros(axes)

#make a function to get a datapoint at a certain position
def datapoint(x):
    global x0
    #move to position
    dx=(x-x0).astype(np.int)
    for i in range(axes):
        if dx[i] != 0:
            channel = int(i/2)+1 #channels 1,2,3,4
            axis = int(i % 2)+1 #axes 1,2
            AGILIS_move(channel, axis, dx[i])
    x0 += dx #set current position vector
    #read data
    data = AI_read()
    coupling = -data[2] #/data[1]
    print 'coupling =', coupling
    return coupling

#setup motor position array
x = np.zeros((n, axes))

#take a reading at the initial point
x[0] = x0
data[0] = datapoint(x[0])

#take a reading at offsets of 1 on each cardinal axis
for i in range(axes):
    x[i+1] = x[0]
    x[i+1,i] += 100
    data[i+1] = datapoint(x[i+1])

#Nelder-Mead downhill simplex method
def simplex(x, y):
    # order the values
    order = np.argsort(y)
    x[:] = x[order]
    y[:] = y[order]

    #find the mean of all except the worst point
    x0=np.mean(x[:-1], axis=0)

    #reflection
    a = 1
    xr = x0+a*(x0-x[-1])
    yr = datapoint(xr)
    if y[0] <= yr < data[-2]:
        print 'reflecting'
        x[-1,:] = xr[:]
        y[-1] = yr
        return x, y

    #expansion
    b = 2
    if yr < y[0]:
        xe = x0+b*(x0-x[-1])
        ye = datapoint(xe)
        if ye < yr:
            print 'expanding'
            x[-1, :] = xe[:]
            y[-1] = ye
        else:
            print 'reflecting (after expansion)'
            x[-1, :] = xr[:]
            y[-1] = yr
        return x, y

    #contraction
    c=-0.5
    xc=x0+c*(x0-x[-1])
    datac=datapoint(xc)
    if datac<data[-1]:
        print 'contracting'
        x[-1,:]=xc[:]
        data[-1]=datac
        return x,data

    #reduction
    print 'reducing'
    d=0.5
    for i in range(1,len(x)):
        x[i]=x[0]+d*(x[i]-x[0])
    return x,data

#set up plot window
pylab.ion() #interactive on
pylab.ylim([-1,1])
pylab.show()

#setup looping
firstloop=True
time1=time.time()
fps=0
print "Press ctrl+C to stop"

while True:
    x,data = simplex(x,data)

    datalist.append(data[0]) #add the best point to the plot

    #update the plot
    if firstloop:
        firstloop=False
        line,=pylab.plot(datalist)
        fps_text=pylab.text(1,0.5,'FPS = {}'.format(fps))
    else:
        line.set_xdata(np.arange(len(datalist)))
        pylab.xlim([0,len(datalist)-1])
        line.set_ydata(datalist)
        pylab.ylim([min(datalist),max(datalist)])
        fps_text.set_text('FPS = {}'.format(fps))
    pylab.draw()

    #calculate run time
    time2=time.time()
    if time2!=time1: #prevent divide by zero
        fps=1.0/(time2-time1)
    else:
        fps=float('Inf')
    time1=time2

    #time.sleep(1)

    #check for keyboard press
    if os.name != 'nt':
        keyPressed=select.select([sys.stdin],[],[],0)
        if len(keyPressed[0])>0:
            break

