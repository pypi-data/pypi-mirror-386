"""
serialconfig_frame.py

Generic serial port configuration Frame subclass
for use in tkinter applications which require a
serial port configuration facility.

Exposes the serial port settings as properties.

Application icons from https://iconmonstr.com/license/.

Created on 24 Dec 2020

:author: semuadmin (Steve Smith)
:copyright: 2020 semuadmin
:license: BSD 3-Clause
"""

from tkinter import (
    DISABLED,
    HORIZONTAL,
    LEFT,
    NORMAL,
    VERTICAL,
    Button,
    Checkbutton,
    DoubleVar,
    E,
    Entry,
    Frame,
    IntVar,
    Label,
    Listbox,
    N,
    S,
    Scrollbar,
    Spinbox,
    StringVar,
    TclError,
    W,
)

from PIL import Image, ImageTk
from pyubx2 import GET, POLL, SET, SETPOLL
from serial import PARITY_EVEN, PARITY_MARK, PARITY_NONE, PARITY_ODD, PARITY_SPACE
from serial.tools.list_ports import comports

from pygpsclient.globals import (
    ICON_CONTRACT,
    ICON_EXPAND,
    ICON_REFRESH,
    LBAND,
    READONLY,
)
from pygpsclient.strings import LBLSPORT, LBLUDPORT

ADVOFF = "\u25bc"
ADVON = "\u25b2"
BGCOL = "azure"
BPSRATE_RNG = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1000000, 4800)
CONNECTED = 1
CONNECTED_FILE = 2
DATABITS_RNG = (8, 5, 6, 7)
DISCONNECTED = 0
MSGMODED = {
    GET: "GET",
    SET: "SET",
    POLL: "POLL",
    SETPOLL: "SETPOLL",
}
MSGMODE_RNG = list(MSGMODED.values())
NOPORTS = 3
PARITIES = {
    PARITY_NONE: "None",
    PARITY_EVEN: "Even",
    PARITY_ODD: "Odd",
    PARITY_MARK: "Mark",
    PARITY_SPACE: "Space",
}
PARITY_RNG = list(PARITIES.values())
STOPBITS_RNG = (1, 1.5, 2)
TIMEOUT_RNG = ("0", "1", "2", "5", "10", "20")


class SerialConfigFrame(Frame):
    """
    Serial port configuration frame class.
    """

    def __init__(self, app, container, context, *args, **kwargs):
        """
        Constructor.

        :param Frame app: reference to main tkinter application
        :param tkinter.Frame container: reference to container frame
        :param str context: serial port context (GNSS or LBAND)
        :param args: optional args to pass to Frame parent class
        :param kwargs: optional kwargs for value ranges, or to pass to Frame parent class
        """

        self._bpsrate_rng = kwargs.pop("bpsrates", BPSRATE_RNG)
        self._databits_rng = kwargs.pop("databits", DATABITS_RNG)
        self._stopbits_rng = kwargs.pop("stopbits", STOPBITS_RNG)
        self._parity_rng = kwargs.pop("parities", PARITY_RNG)
        self._timeout_rng = kwargs.pop("timeouts", TIMEOUT_RNG)
        self._msgmode_name_rng = kwargs.pop("msgmodes", MSGMODE_RNG)
        self._preselect = kwargs.pop("preselect", ())
        self._context = context

        Frame.__init__(self, container, *args, **kwargs)

        self.__app = app
        self._show_advanced = False
        self._status = DISCONNECTED
        self._ports = ()
        self._port = StringVar()
        self.user_defined_port = StringVar()
        self.user_defined_port.set(self.__app.configuration.get("userport_s"))
        self._port_desc = StringVar()
        self._bpsrate = IntVar()
        self._databits = IntVar()
        self._stopbits = DoubleVar()
        self._parity_name = StringVar()
        self._rtscts = IntVar()
        self._xonxoff = IntVar()
        self._timeout = DoubleVar()
        self._msgmode_name = StringVar()
        self._inactivity_timeout = IntVar()
        self._img_refresh = ImageTk.PhotoImage(Image.open(ICON_REFRESH))
        self._img_expand = ImageTk.PhotoImage(Image.open(ICON_EXPAND))
        self._img_contract = ImageTk.PhotoImage(Image.open(ICON_CONTRACT))

        self._body()
        self._do_layout()
        self._attach_events()
        self.reset()

    def _body(self):
        """
        Set up widgets.
        """

        self._frm_basic = Frame(self)
        self._lbl_port = Label(self._frm_basic, text="Serial\nPort  ")
        self._lbx_port = Listbox(
            self._frm_basic,
            border=2,
            relief="sunken",
            width=38,
            height=5,
            justify=LEFT,
            exportselection=False,
        )
        self._scr_portv = Scrollbar(self._frm_basic, orient=VERTICAL)
        self._scr_porth = Scrollbar(self._frm_basic, orient=HORIZONTAL)
        self._lbx_port.config(yscrollcommand=self._scr_portv.set)
        self._lbx_port.config(xscrollcommand=self._scr_porth.set)
        self._scr_portv.config(command=self._lbx_port.yview)
        self._scr_porth.config(command=self._lbx_port.xview)
        self._lbl_bpsrate = Label(self._frm_basic, text="Rate bps")
        self._spn_bpsrate = Spinbox(
            self._frm_basic,
            values=self._bpsrate_rng,
            width=8,
            state=READONLY,
            wrap=True,
            textvariable=self._bpsrate,
        )
        self._btn_refresh = Button(
            self._frm_basic,
            command=self._on_refresh,
            image=self._img_refresh,
            width=28,
            height=22,
        )
        self._btn_toggle = Button(
            self._frm_basic,
            command=self._on_toggle_advanced,
            image=self._img_expand,
            width=28,
            height=22,
        )

        self._frm_advanced = Frame(self)
        self._lbl_databits = Label(self._frm_advanced, text="Data Bits")
        self._spn_databits = Spinbox(
            self._frm_advanced,
            values=self._databits_rng,
            width=3,
            state=READONLY,
            wrap=True,
            textvariable=self._databits,
        )
        self._lbl_stopbits = Label(self._frm_advanced, text="Stop Bits")
        self._spn_stopbits = Spinbox(
            self._frm_advanced,
            values=self._stopbits_rng,
            width=3,
            state=READONLY,
            wrap=True,
            textvariable=self._stopbits,
        )
        self._lbl_parity_name = Label(self._frm_advanced, text="Parity")
        self._spn_parity_name = Spinbox(
            self._frm_advanced,
            values=self._parity_rng,
            width=6,
            state=READONLY,
            wrap=True,
            textvariable=self._parity_name,
        )
        self._chk_rts = Checkbutton(
            self._frm_advanced, text="RTS/CTS", variable=self._rtscts
        )
        self._chk_xon = Checkbutton(
            self._frm_advanced, text="Xon/Xoff", variable=self._xonxoff
        )
        self._lbl_timeout = Label(self._frm_advanced, text="Timeout (s)")
        self._spn_timeout = Spinbox(
            self._frm_advanced,
            values=self._timeout_rng,
            width=4,
            state=READONLY,
            wrap=True,
            textvariable=self._timeout,
        )
        self._lbl_msgmode_name = Label(self._frm_advanced, text="Msg Mode")
        self._spn_msgmode_name = Spinbox(
            self._frm_advanced,
            values=self._msgmode_name_rng,
            width=7,
            state=READONLY,
            wrap=True,
            textvariable=self._msgmode_name,
        )
        self._lbl_userport = Label(
            self._frm_advanced, text="User-defined\nPort               "
        )
        self._ent_userport = Entry(
            self._frm_advanced,
            textvariable=self.user_defined_port,
            relief="sunken",
            width=30,
        )
        self._lbl_inactivity = Label(self._frm_advanced, text="Inactivity Timeout (s)")
        self._spn_inactivity = Spinbox(
            self._frm_advanced,
            values=(0, 1, 5, 10, 30, 60, 300),
            width=4,
            state=READONLY,
            wrap=True,
            textvariable=self._inactivity_timeout,
        )

    def _do_layout(self):
        """
        Layout widgets.
        """

        self._frm_basic.grid(column=0, row=0, columnspan=4, sticky=(W, E))
        self._lbl_port.grid(column=0, row=0, sticky=W)
        self._lbx_port.grid(
            column=1, row=0, columnspan=3, sticky=(W, E), padx=3, pady=2
        )
        self._scr_portv.grid(column=4, row=0, sticky=(N, S))
        self._scr_porth.grid(column=1, row=1, columnspan=3, sticky=(E, W))
        self._lbl_bpsrate.grid(column=0, row=2, sticky=W)
        self._spn_bpsrate.grid(column=1, row=2, sticky=W, padx=3, pady=2)
        self._btn_refresh.grid(column=3, row=2, sticky=E)
        self._btn_toggle.grid(column=4, row=2, sticky=E)

        self._frm_advanced.grid_forget()
        self._lbl_databits.grid(column=0, row=0, sticky=W)
        self._spn_databits.grid(column=1, row=0, sticky=W, padx=3, pady=2)
        self._lbl_stopbits.grid(column=2, row=0, sticky=W)
        self._spn_stopbits.grid(column=3, row=0, sticky=W, padx=3, pady=2)
        self._lbl_parity_name.grid(column=0, row=1, sticky=W)
        self._spn_parity_name.grid(column=1, row=1, sticky=W, padx=3, pady=2)
        self._chk_rts.grid(column=2, row=1, sticky=W)
        self._chk_xon.grid(column=3, row=1, sticky=W, padx=3, pady=2)
        self._lbl_timeout.grid(column=0, row=2, sticky=W)
        self._spn_timeout.grid(column=1, row=2, sticky=W, padx=3, pady=2)
        if len(self._msgmode_name_rng) > 0:
            self._lbl_msgmode_name.grid(column=2, row=2, sticky=W)
            self._spn_msgmode_name.grid(column=3, row=2, sticky=W, padx=3, pady=2)
        self._lbl_userport.grid(column=0, row=3, sticky=W)
        self._ent_userport.grid(column=1, row=3, columnspan=3, sticky=W, padx=3, pady=2)
        self._lbl_inactivity.grid(column=0, row=4, columnspan=2, sticky=W)
        self._spn_inactivity.grid(
            column=2, row=4, columnspan=3, sticky=W, padx=3, pady=2
        )

    def _attach_events(self):
        """
        Bind events to frame.
        """

        self.bind("<Configure>", self._on_resize)
        self._lbx_port.bind("<<ListboxSelect>>", self._on_select_port)

    def _bind_events(self, add: bool = True):
        """
        Add or remove event bindings to/from widgets.

        :param bool add: add or remove binding
        """

        tracemode = "write"
        for setting in (
            self._port,
            self.user_defined_port,
            self._bpsrate,
            self._databits,
            self._stopbits,
            self._parity_name,
            self._rtscts,
            self._xonxoff,
            self._timeout,
            self._msgmode_name,
            self._inactivity_timeout,
        ):
            if add:
                setting.trace_add(tracemode, self._on_update_config)
            else:
                if len(setting.trace_info()) > 0:
                    setting.trace_remove(tracemode, setting.trace_info()[0][1])

    def reset(self):
        """
        Reset settings to saved configuration.
        """

        self._bind_events(False)
        cfg = self.__app.configuration
        if self._context == LBAND:
            self._port.set(cfg.get("lbandclientserialport_s"))
            self._bpsrate.set(cfg.get("lbandclientbpsrate_n"))
            self._databits.set(cfg.get("lbandclientdatabits_n"))
            self._stopbits.set(cfg.get("lbandclientstopbits_f"))
            self._parity_name.set(PARITIES[cfg.get("lbandclientparity_s")])
            self._rtscts.set(cfg.get("lbandclientrtscts_b"))
            self._xonxoff.set(cfg.get("lbandclientxonxoff_b"))
            self._timeout.set(cfg.get("lbandclienttimeout_f"))
            self._msgmode_name.set(MSGMODED[cfg.get("lbandclientmsgmode_n")])
            self._inactivity_timeout.set(cfg.get("lbandclientinactivity_timeout_n"))
            self.user_defined_port.set(cfg.get("spartnport_s"))
        else:  # GNSS
            self._port.set(cfg.get("serialport_s"))
            self._bpsrate.set(cfg.get("bpsrate_n"))
            self._databits.set(cfg.get("databits_n"))
            self._stopbits.set(cfg.get("stopbits_f"))
            self._parity_name.set(PARITIES[cfg.get("parity_s")])
            self._rtscts.set(cfg.get("rtscts_b"))
            self._xonxoff.set(cfg.get("xonxoff_b"))
            self._timeout.set(cfg.get("timeout_f"))
            self._msgmode_name.set(MSGMODED[cfg.get("msgmode_n")])
            self._inactivity_timeout.set(cfg.get("inactivity_timeout_n"))
            self.user_defined_port.set(cfg.get("userport_s"))
        self._on_refresh()
        self._bind_events(True)

    def _on_update_config(self, var, index, mode):  # pylint: disable=unused-argument
        """
        Update in-memory configuration if setting is changed.
        """

        try:
            self.update()
            cfg = self.__app.configuration
            if self._context == LBAND:
                cfg.set("lbandclientserialport_s", self.port)
                cfg.set("spartnport_s", self.userport)
                cfg.set("lbandclientbpsrate_n", int(self.bpsrate))
                cfg.set("lbandclientdatabits_n", int(self.databits))
                cfg.set("lbandclientstopbits_f", float(self.stopbits))
                cfg.set("lbandclientparity_s", self.parity)
                cfg.set("lbandclientrtscts_b", int(self.rtscts))
                cfg.set("lbandclientxonxoff_b", int(self.xonxoff))
                cfg.set("lbandclienttimeout_f", float(self.timeout))
                cfg.set("lbandclientmsgmode_n", int(self.msgmode))
                cfg.set("lbandclientinactivity_timeout_n", int(self.inactivity_timeout))
            else:  # GNSS
                cfg.set("serialport_s", self.port)
                cfg.set("userport_s", self.userport)
                cfg.set("bpsrate_n", int(self.bpsrate))
                cfg.set("databits_n", int(self.databits))
                cfg.set("stopbits_f", float(self.stopbits))
                cfg.set("parity_s", self.parity)
                cfg.set("rtscts_b", int(self.rtscts))
                cfg.set("xonxoff_b", int(self.xonxoff))
                cfg.set("timeout_f", float(self.timeout))
                cfg.set("msgmode_n", int(self.msgmode))
                cfg.set("inactivity_timeout_n", int(self.inactivity_timeout))
        except (ValueError, TclError):
            pass

    def _on_refresh(self):
        """
        Refresh list of ports.
        """

        if self._status in (CONNECTED, CONNECTED_FILE):
            return
        self.set_status(DISCONNECTED)
        self._lbx_port.delete(0, "end")
        self._get_ports()

    def _get_ports(self):
        """
        Populate list of available serial ports using pyserial comports tool.

        User-defined serial port can be passed as command line keyword argument,
        in which case this takes precedence.

        Attempt to automatically select a serial device matching
        a list of 'preselect' devices (only works on platforms
        which parse UART device desc or HWID e.g. Posix).
        """

        self._ports = sorted(comports())
        init_idx = 0
        recognised = False
        pnames = [p[0] for p in self._ports]
        userp = self.user_defined_port.get()
        if self._port.get() != "" and self._port.get() not in pnames:
            self._ports.insert(0, (self._port.get(), LBLSPORT, None))
        if userp != "" and userp not in pnames:
            self._ports.insert(0, (userp, LBLUDPORT, None))

        if len(self._ports) > 0:
            # default to first item in list
            port, desc, _ = self._ports[0]
            if desc == "":
                desc = "device"
            self._port.set(port)
            self._port_desc.set(desc)
            for idx, (port, desc, _) in enumerate(self._ports):
                self._lbx_port.insert(idx, f"{port}: {desc}")
                # default selection to recognised GNSS device if possible
                if not recognised:
                    for dev in self._preselect:
                        if dev.lower() in desc.lower():
                            init_idx = idx
                            self._port.set(port)
                            self._port_desc.set(desc)
                            recognised = True
                            break
            self.set_status(DISCONNECTED)
            self._lbx_port.activate(init_idx)
            self._lbx_port.selection_set(first=init_idx)
        else:
            self.set_status(NOPORTS)

    def _on_select_port(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get selected port from listbox and set global variable.
        """

        idx = self._lbx_port.curselection()
        if idx == "":
            idx = 0
        port_orig = self._lbx_port.get(idx)
        port = port_orig[0 : port_orig.find(":")]
        desc = port_orig[port_orig.find(":") + 1 :]
        if desc == "":
            desc = "device"
        self._port.set(port)
        self._port_desc.set(desc)

    def _on_toggle_advanced(self):
        """
        Toggle advanced serial port settings panel on or off.
        """

        self._show_advanced = not self._show_advanced
        if self._show_advanced:
            self._frm_advanced.grid(column=0, row=1, columnspan=3, sticky=(W, E))
            self._btn_toggle.config(image=self._img_contract)
        else:
            self._frm_advanced.grid_forget()
            self._btn_toggle.config(image=self._img_expand)

    def set_status(self, status: int = DISCONNECTED):
        """
        Set connection status, which determines whether controls
        are enabled or not: 0=DISCONNECTED, 1=CONNECTED,
        2=CONNECTED_FILE, 3=NOPORTS.

        :param int status: status (0,1,2,3)
        """

        self._status = status
        for widget in (
            self._lbl_port,
            self._lbl_bpsrate,
            self._lbl_databits,
            self._lbl_stopbits,
            self._lbl_parity_name,
            self._lbl_timeout,
            self._chk_rts,
            self._chk_xon,
            self._lbx_port,
            self._lbl_msgmode_name,
            self._lbl_userport,
            self._ent_userport,
            self._lbl_inactivity,
        ):
            widget.configure(state=(NORMAL if status == DISCONNECTED else DISABLED))
        for widget in (
            self._spn_bpsrate,
            self._spn_databits,
            self._spn_stopbits,
            self._spn_parity_name,
            self._spn_timeout,
            self._spn_msgmode_name,
            self._spn_inactivity,
        ):
            widget.configure(state=(READONLY if status == DISCONNECTED else DISABLED))

    @property
    def status(self) -> int:
        """
        Getter for status flag: 0=DISCONNECTED, 1=CONNECTED,
        2=CONNECTED_FILE, 3=NOPORTS.

        :return: status flag (0,1,2,3)
        :rtype: int
        """

        return self._status

    @property
    def port(self) -> str:
        """
        Getter for port.

        :return: selected port
        :rtype: str
        """

        return self._port.get()

    @property
    def port_desc(self) -> str:
        """
        Getter for port description.

        :return: selected port description
        :rtype: str
        """

        return self._port_desc.get()

    @property
    def bpsrate(self) -> int:
        """
        Getter for bps rate (commonly but incorrectly referred to as baud rate).

        :return: selected baudrate
        :rtype: int
        """

        return self._bpsrate.get()

    @property
    def databits(self) -> int:
        """
        Getter for databits.

        :return: selected databits
        :rtype: int
        """

        return self._databits.get()

    @property
    def stopbits(self) -> float:
        """
        Getter for stopbits.

        :return: selected stopbits
        :rtype: float
        """

        return self._stopbits.get()

    @property
    def parity(self) -> str:
        """
        Getter for parity.

        :return: selected parity
        :rtype: str
        """

        if self._parity_name.get() == PARITIES[PARITY_EVEN]:
            return PARITY_EVEN
        if self._parity_name.get() == PARITIES[PARITY_ODD]:
            return PARITY_ODD
        if self._parity_name.get() == PARITIES[PARITY_MARK]:
            return PARITY_MARK
        if self._parity_name.get() == PARITIES[PARITY_SPACE]:
            return PARITY_SPACE
        return PARITY_NONE

    @property
    def rtscts(self) -> bool:
        """
        Getter for rts/cts.

        :return: selected rts/cts
        :rtype: bool
        """

        return self._rtscts.get()

    @property
    def xonxoff(self) -> bool:
        """
        Getter for xon/xoff.

        :return: selected xon/xoff
        :rtype: bool
        """

        return self._xonxoff.get()

    @property
    def timeout(self) -> float:
        """
        Getter for timeout.

        :return: selected timeout
        :rtype: float (or None)
        """

        if self._timeout.get() == "None":
            return None
        return float(self._timeout.get())

    @property
    def msgmode(self) -> int:
        """
        Return message parsing mode
        Default is GET i.e. input from receiver.

        :return: message mode 0 = POLL 1 = SET, 2 = POLL, 3 = SETPOLL
        :rtype: int
        """

        if self._msgmode_name.get() == MSGMODED[SET]:
            return SET
        if self._msgmode_name.get() == MSGMODED[POLL]:
            return POLL
        if self._msgmode_name.get() == MSGMODED[SETPOLL]:
            return SETPOLL
        return GET

    @property
    def userport(self) -> str:
        """
        Return user-defined port

        :return: user-defined serial port
        :rtype: str
        """

        return self.user_defined_port.get()

    @property
    def inactivity_timeout(self) -> int:
        """
        Return inactivity timeout

        :return: timeout in seconds
        :rtype: int
        """

        return self._inactivity_timeout.get()

    def _on_resize(self, event):  # pylint: disable=unused-argument
        """
        Resize frame.

        :param event event: resize event
        """

        self.__app.frm_settings.on_expand()
