#!/usr/bin/env python3

from datetime import datetime
from time import sleep
import pexpect
import threading
import wx

if 'spawn' not in dir(pexpect):
    import wexpect as pexpect

# Handles the current VPN connection
class vpnConnection():
    # Required variables
    prot = None
    host = None
    user = None
    pw = None
    populated = False
    command = None
    status = False
    process = None
    log = ''
    
    # Initialise class
    def __init__(self, prot=None, host=None, user=None, pw=None):
        # Update variables with any input
        self.update(prot, host, user, pw)
    
    # Update object with any provided values
    def update(self, prot=None, host=None, user=None, pw=None):
        # Import provided variables
        if prot != None:
            protocols = { 0: 'anyconnect', 1: 'nc', 2: 'gp' }
            if prot in protocols.keys():
                self.prot = protocols[prot]
        if host != None:
            self.host = host
        if user != None:
            self.user = user
        if pw != None:
            self.pw = pw
        # Validate current data
        if None not in (self.prot, self.host, self.user, self.pw):
            if len(self.prot) > 1 and len(self.host) > 1 and len(self.user) > 1 and len(self.pw) > 1:
                self.populated = True
    
    # Import connection settings and initiate connection
    def connect(self, prot=None, host=None, user=None, pw=None):
        # Update object with any provided values
        self.update(prot, host, user, pw)
        # Check whether connection safe to make
        if not self.populated:
            self.log = 'Cannot connect without all parameters'
            return False
        # Command to feed pexpect
        self.command = ' '.join([
                'echo "' + self.pw + '" | ',
                'sudo openconnect',
                '--protocol="' + self.prot + '"',
                '--user="' + self.user + '"',
                '--passwd-on-stdin',
                self.host
            ])
        # Initialise pexpect
        #self.command = 'cmd.exe /C "for /L %i in (1,1,20) do @echo Log entry %i && @timeout /t 2 > nul"'

# Customised wx.Frame
class customFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(customFrame, self).__init__(*args, **kwargs)
        self.initUI()
    
    def onQuit(self, e):
        self.Close()

class mainFrame(customFrame):
    def initUI(self):
        # Create empty connection object
        self.vpn = vpnConnection()
        # Begin background thread
        thread = threading.Thread(target=self.bgThread)
        thread.setDaemon(True)
        thread.start()
        # Create toolbar
        toolbar = wx.ToolBar(self, style=wx.TB_VERTICAL)
        tbConn = toolbar.AddTool(wx.ID_OPEN, '', wx.Bitmap('lib/connect.png'), shortHelp='Connect')
        tbDisc = toolbar.AddTool(wx.ID_CLOSE, '', wx.Bitmap('lib/disconnect.png'), shortHelp='Disconnect')
        tbClear = toolbar.AddTool(wx.ID_CLEAR, '', wx.Bitmap('lib/clear.png'), shortHelp='Clear Log')
        tbExit = toolbar.AddTool(wx.ID_EXIT, '', wx.Bitmap('lib/exit.png'), shortHelp='Exit')
        toolbar.Realize()
        self.log = wx.TextCtrl(self, style = wx.TE_MULTILINE | wx.TE_READONLY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(toolbar, 0, wx.EXPAND)
        sizer.Add(self.log, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.Bind(wx.EVT_TOOL, self.onConnect, tbConn)
        self.Bind(wx.EVT_TOOL, self.onDisconnect, tbDisc)
        self.Bind(wx.EVT_TOOL, self.onClear, tbClear)
        self.Bind(wx.EVT_TOOL, self.onQuit, tbExit)
        self.SetSizer(sizer)
        self.SetSize((500,400))
        self.SetTitle('OpenConnect SSL VPN Client')
        self.Centre()
        self.Show()
    
    def onConnect(self, e):
        connectFrame(self, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
    
    def onDisconnect(self, e):
        self.vpn.log += "\nDisconnecting from VPN..."
        sleep(0.5)
        self.vpn.status = False
    
    def onClear(self, e):
        self.vpn.log = ''
        self.onUpdate()
    
    def bgThread(self):
        while self:
            timestamp = datetime.now().strftime('%H:%M:%S')
            if self.vpn.command:
                self.vpn.process = pexpect.spawn(self.vpn.command, timeout=60, ignore_sighup=False)
                if len(self.vpn.log) > 1:
                    self.vpn.log += '\n'
                self.vpn.log += timestamp + ': Connecting to ' + self.vpn.prot.upper() + ' VPN ' + self.vpn.host + ' as ' + self.vpn.user
                self.vpn.command = None
                wx.CallAfter(self.onUpdate)
            elif self.vpn.process:
                line = str(self.vpn.process.readline()).strip()
                if not self.vpn.process:
                    self.vpn.process = None
                    self.vpn.log += '\n' + timestamp + ': Process ended'
                elif not line:
                    self.vpn.process = None
                    self.vpn.log += '\n' + timestamp + ': Process returned blank'
                else:
                    self.vpn.log += '\n' + timestamp + ': ' + line
                wx.CallAfter(self.onUpdate)
            else:
                sleep(1)

    def onUpdate(self):
        self.log.SetValue(self.vpn.log)
        self.log.SetScrollPos(wx.VERTICAL, self.log.GetScrollRange(wx.VERTICAL))
        self.log.SetInsertionPoint(-1)

class connectFrame(customFrame):
    def initUI(self):
        label1 = wx.StaticText(self, label='Pick the type of VPN:')
        self.vpnProt = wx.Choice(self, choices=[
                'Cisco AnyConnect',
                'Pulse Secure / Juniper Network Connect',
                'Palo Alto Networks (PAN) GlobalProtect'
            ])
        self.vpnProt.SetSelection(1)
        label2 = wx.StaticText(self, label='Enter host to connect to:')
        self.vpnHost = wx.TextCtrl(self)
        label3 = wx.StaticText(self, label='Enter username:')
        self.vpnUser = wx.TextCtrl(self)
        label4 = wx.StaticText(self, label='Enter password:')
        self.vpnPass = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        btnConnect = wx.Button(self, label='Connect')
        btnCancel = wx.Button(self, label='Cancel')
        # Position elements
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label1, 0, wx.EXPAND)
        sizer.Add(self.vpnProt, 0, wx.EXPAND)
        sizer.Add(label2, 0, wx.EXPAND)
        sizer.Add(self.vpnHost, 0, wx.EXPAND)
        sizer.Add(label3, 0, wx.EXPAND)
        sizer.Add(self.vpnUser, 0, wx.EXPAND)
        sizer.Add(label4, 0, wx.EXPAND)
        sizer.Add(self.vpnPass, 0, wx.EXPAND)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(btnConnect, 0)
        btnSizer.Add(btnCancel, 0)
        sizer.Add(btnSizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.SetSizeHints(self)
        self.Bind(wx.EVT_BUTTON, self.onConnect, btnConnect)
        self.Bind(wx.EVT_BUTTON, self.onQuit, btnCancel)
        self.SetSizer(sizer)
        self.SetTitle('Connect')
        self.Centre()
        self.Show()
    
    def onConnect(self, e):
        prot = self.vpnProt.GetCurrentSelection()
        host = self.vpnHost.GetValue()
        user = self.vpnUser.GetValue()
        pw = self.vpnPass.GetValue()
        self.GetParent().vpn.connect(prot, host, user, pw)
        self.Close()

if __name__ == '__main__':
    app = wx.App()
    frame = mainFrame(None)
    app.MainLoop()