import os, sys
import numpy
import scipy.constants as codata


from syned.storage_ring.magnetic_structures.undulator import Undulator
from syned.storage_ring.magnetic_structures.wiggler import Wiggler
from syned.storage_ring.light_source import LightSource, ElectronBeam
from syned.beamline.beamline import Beamline

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QRect

from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

import orangecanvas.resources as resources

import at #accelerator toolbox

from orangecontrib.wofry.widgets.gui.python_script import PythonScript # TODO: it is illegal that syned imports from wofry.


m2ev = codata.c * codata.h / codata.e

VERTICAL = 1
HORIZONTAL = 2
BOTH = 3

lattice_file = os.path.join(resources.package_dirname("orangecontrib.esrf.syned.data"), 'S28F_all_BM.mat')
AT_LATTICE = at.load_lattice(lattice_file)

def get_electron_beam_parameters_from_at(id=1, verbose=0):

    if verbose: print("Retrieving electron beam parameters at the center of the ID%02d straight section" % id)

    cell_length = (AT_LATTICE.get_s_pos(at.End) / 32)[0]

    ID = f'ID{id:02d}'
    IDind = AT_LATTICE.get_uint32_index(ID)
    s_locs = AT_LATTICE.get_s_pos(IDind)
    if verbose: print("%s s: %f m" % (ID, s_locs))

    # get circumference
    Circumference = AT_LATTICE.get_s_pos(at.End)
    if verbose: print("Circumference, Cell", Circumference, Circumference / 32)

    # define break locations
    if verbose: print("Lattice location s_locs: ", s_locs)

    if type(s_locs) != numpy.ndarray: # todo: not needed, remove?
        npoints = 1 + int(Circumference[0] * 1)
        s_locs = numpy.linspace(0.0, Circumference, npoints)[:, 0]  # all locations along lattice

    npoints = s_locs.shape[0]

    # insert markers at break locations
    r = AT_LATTICE.sbreak(break_s=list(s_locs))

    # indexes of s locations
    s_ind = r.get_uint32_index('sbreak')

    # get lattice parameters with radiation
    if verbose: print('get lattice parameters')
    r.enable_6d()
    p0 = r.envelope_parameters()

    epsilonX = p0.emittances[0];
    epsilonY = 10 * 1e-12;  # tuned to this value during operation
    delta = p0.sigma_e;

    # gert optics
    if verbose: print('get orbit, dispersion, beta functions')
    _, _, l = AT_LATTICE.linopt6(refpts=s_ind)

    # get geometry
    if verbose: print('get geomtery')
    geom, _ = AT_LATTICE.get_geometry(refpts=s_ind)

    data = []
    for i in range(0, npoints):
        s = s_locs[i]
        s0 = s_locs[i]

        alpha = l[i].alpha
        alphaX = alpha[0]
        alphaY = alpha[1]

        beta = l[i].beta
        betaX = beta[0]
        betaY = beta[1]

        gammaX = (1.0 + alpha[0] * alpha[0]) / beta[0]
        gammaY = (1.0 + alpha[1] * alpha[1]) / beta[1]

        eta = l[i].dispersion
        etaX = eta[0]
        etaXp = eta[1]
        etaY = eta[2]
        etaYp = eta[3]

        xx = betaX * epsilonX + (etaX * delta) ** 2
        yy = betaY * epsilonY + (etaY * delta) ** 2
        xxp = -alphaX * epsilonX + etaX * etaXp * delta ** 2
        yyp = -alphaY * epsilonY + etaY * etaYp * delta ** 2
        xpxp = gammaX * epsilonX + (etaXp * delta) ** 2
        ypyp = gammaY * epsilonY + (etaYp * delta) ** 2

        lab_x = geom[i].x
        lab_y = geom[i].y
        angle = geom[i].angle

        tmp = [s0,  # 0
               s,  # 1
               lab_x,  # 2
               lab_y,  # 3
               angle,  # 4
               alphaX,  # 5
               alphaY,  # 6
               betaX,  # 7
               betaY,  # 8
               gammaX, gammaY,  # 9,10
               etaX, etaY, etaXp, etaYp,  # 11-14
               xx, yy, xxp, yyp, xpxp, ypyp,  # 15-20
               1e6 * numpy.sqrt(xx), 1e6 * numpy.sqrt(yy), 1e6 * numpy.sqrt(xpxp),  # 21-23
               1e6 * numpy.sqrt(ypyp), numpy.sqrt(xx * xpxp), numpy.sqrt(yy * ypyp),  # 24-26
               ]

        data.append(tmp)

    return numpy.array(data), epsilonX, epsilonY

class OWEBS(OWWidget):

    name = "ESRF-EBS ID Light Source"
    description = "Syned: ESRF-EBS ID Light Source"
    icon = "icons/id_ebs.png"
    priority = 1


    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    category = "ESRF-EBS Syned Light Sources"
    keywords = ["data", "file", "load", "read"]

    outputs = [{"name":"SynedData",
                "type":Beamline,
                "doc":"Syned Beamline",
                "id":"data"}]


    want_main_area = 1


    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 645

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 650

    TABS_AREA_HEIGHT = 625
    CONTROL_AREA_WIDTH = 450


    electron_energy_in_GeV = Setting(6.0)
    electron_energy_spread = Setting(0.001)
    ring_current           = Setting(0.2)
    number_of_bunches      = Setting(0.0)

    moment_xx           = Setting(0.0)
    moment_xxp          = Setting(0.0)
    moment_xpxp         = Setting(0.0)
    moment_yy           = Setting(0.0)
    moment_yyp          = Setting(0.0)
    moment_ypyp         = Setting(0.0)

    electron_beam_size_h       = Setting(0.0)
    electron_beam_divergence_h = Setting(0.0)
    electron_beam_size_v       = Setting(0.0)
    electron_beam_divergence_v = Setting(0.0)

    electron_beam_emittance_h = Setting(0.0)
    electron_beam_emittance_v = Setting(0.0)
    electron_beam_beta_h = Setting(0.0)
    electron_beam_beta_v = Setting(0.0)
    electron_beam_alpha_h = Setting(0.0)
    electron_beam_alpha_v = Setting(0.0)
    electron_beam_eta_h = Setting(0.0)
    electron_beam_eta_v = Setting(0.0)
    electron_beam_etap_h = Setting(0.0)
    electron_beam_etap_v = Setting(0.0)

    type_of_properties = Setting(1)
    type_of_properties_initial_selection = type_of_properties # this is a backup value as type_of_properties is changed by the code

    auto_energy = Setting(0.0)
    auto_harmonic_number = Setting(1)

    K_horizontal       = Setting(0.5)
    K_vertical         = Setting(0.5)
    period_length      = Setting(0.018)
    number_of_periods  = Setting(10)

    ebs_id_index = Setting(0)
    gap_mm = Setting(0.0)

    gap_min = Setting(5.0)
    gap_max = Setting(30.0)
    harmonic_max = Setting(3)

    a0 = Setting('2.083')
    a1 = Setting('1.0054')
    a2 = Setting('')
    a3 = Setting('')
    a4 = Setting('')
    a5 = Setting('')
    a6 = Setting('')

    pow_dens_screen = Setting(30.0)

    # data_url = 'ftp://ftp.esrf.eu/pub/scisoft/syned/resources/jsrund.csv'
    # create it in nice with the ID app: /segfs/tango/bin/jsrund
    data_url = os.path.join(resources.package_dirname("orangecontrib.esrf.syned.data"), 'jsrund.csv')

    data_dict = None

    def __init__(self):

        self.get_data_dictionary_csv()

        # OLD FORMAT
        # self.data_url = "https://raw.githubusercontent.com/srio/shadow3-scripts/master/ESRF-LIGHTSOURCES-EBS/ebs_ids.json"
        # self.get_data_dictionary()

        self.runaction = widget.OWAction("Send Data", self)
        self.runaction.triggered.connect(self.send_data)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Send Data", callback=self.send_data)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.MAX_WIDTH)),
                               round(min(geom.height() * 0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_sou = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        gui.comboBox(self.tab_sou, self, "ebs_id_index", label="Load ID parameters from database list: ", labelWidth=350,
                     items=self.get_id_list(), callback=self.set_id, sendSelectedValue=False, orientation="horizontal")

        self.electron_beam_box = oasysgui.widgetBox(self.tab_sou, "Electron Beam/Machine Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_in_GeV", "Energy [GeV]",  labelWidth=260, valueType=float, orientation="horizontal", callback=self.update)
        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal", callback=self.update)
        oasysgui.lineEdit(self.electron_beam_box, self, "ring_current", "Ring Current [A]",        labelWidth=260, valueType=float, orientation="horizontal", callback=self.update)

        gui.comboBox(self.electron_beam_box, self, "type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence", "From Twiss papameters","Zero emittance",
                            "EBS (S28D 135pm H, 5pm V)", "EBS (S28D 135pm H, 10pm V)", "EBS (S28F 140pm H, 10pm V)"],
                     callback=self.update_electron_beam,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)
        tmp0 = oasysgui.widgetBox(self.left_box_2_1, "", addSpace=False, orientation="horizontal")
        tmp1 = oasysgui.widgetBox(tmp0, "", addSpace=False, orientation="vertical")
        tmp2 = oasysgui.widgetBox(tmp0, "", addSpace=False, orientation="vertical")


        oasysgui.lineEdit(tmp1, self, "moment_xx",   "<x x>   [m^2]",   labelWidth=100, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(tmp1, self, "moment_xxp",  "<x x'>  [m.rad]", labelWidth=100, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(tmp1, self, "moment_xpxp", "<x' x'> [rad^2]", labelWidth=100, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(tmp2, self, "moment_yy",   "<y y>   [m^2]",   labelWidth=100, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(tmp2, self, "moment_yyp",  "<y y'>  [m.rad]", labelWidth=100, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(tmp2, self, "moment_ypyp", "<y' y'> [rad^2]", labelWidth=100, valueType=float, orientation="horizontal",  callback=self.update)
        gui.separator(self.left_box_2_1)
        lbl = oasysgui.widgetLabel(self.left_box_2_1, "Note: 2nd Moments do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_2 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=150)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size \u03c3x [m]",          labelWidth=260, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size \u03c3y [m]",            labelWidth=260, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence \u03c3'x [rad]", labelWidth=260, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence \u03c3'y [rad]",   labelWidth=260, valueType=float, orientation="horizontal",  callback=self.update)
        gui.separator(self.left_box_2_2)
        lbl = oasysgui.widgetLabel(self.left_box_2_2, "Note: Size/Divergence do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_3 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=150)
        self.left_box_2_3_l = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        self.left_box_2_3_r = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_emittance_h", "\u03B5x [m.rad]",labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_alpha_h",     "\u03B1x",        labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_beta_h",      "\u03B2x [m]",    labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_eta_h",       "\u03B7x",        labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_etap_h",      "\u03B7'x",       labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)


        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_emittance_v", "\u03B5y [m.rad]",labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_alpha_v",     "\u03B1y",        labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_beta_v",      "\u03B2y [m]",    labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_eta_v",       "\u03B7y",        labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_etap_v",      "\u03B7'y",       labelWidth=75, valueType=float, orientation="horizontal",  callback=self.update)

        gui.rubber(self.controlArea)

        ###################

        left_box_1 = oasysgui.widgetBox(self.tab_sou, "ID Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "period_length", "Period Length [m]", labelWidth=260,
                          valueType=float, orientation="horizontal", callback=self.update)
        oasysgui.lineEdit(left_box_1, self, "number_of_periods", "Number of Periods", labelWidth=260,
                          valueType=float, orientation="horizontal", callback=self.update)



        left_box_1 = oasysgui.widgetBox(self.tab_sou, "Setting", addSpace=True, orientation="vertical")

        # oasysgui.lineEdit(left_box_1, self, "K_horizontal", "Horizontal K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "K_vertical", "Vertical K", labelWidth=260,
                          valueType=float, orientation="horizontal", callback=self.set_K)

        oasysgui.lineEdit(left_box_1, self, "gap_mm", "Undulator Gap [mm]",
                          labelWidth=250, valueType=float, orientation="horizontal",
                          callback=self.set_gap)

        left_box_2 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_2, self, "auto_energy", "Photon Energy [eV]",
                          labelWidth=250, valueType=float, orientation="horizontal",
                          callback=self.auto_set_undulator_V)
        oasysgui.lineEdit(left_box_2, self, "auto_harmonic_number", "Harmonic",
                          labelWidth=250, valueType=int, orientation="horizontal",
                          callback=self.auto_set_undulator_V)

        ####################################################


        tab_util = oasysgui.createTabPage(self.tabs_setting, "Settings")

        left_box_0 = oasysgui.widgetBox(tab_util, "Advanced settings",
                        addSpace=False, orientation="vertical", height=450)

        oasysgui.lineEdit(left_box_0, self, "gap_min",  "minimum gap",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          callback=self.update)

        oasysgui.lineEdit(left_box_0, self, "gap_max",  "maximum gap (for plots)",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          callback=self.update)

        oasysgui.lineEdit(left_box_0, self, "harmonic_max",  "maximum harmonic (for plots)",
                          labelWidth=260, valueType=int, orientation="horizontal",
                          callback=self.update)

        left_box_00 = oasysgui.widgetBox(left_box_0, "Gap parametrization", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(left_box_00, self, "a0", "a0", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)
        oasysgui.lineEdit(left_box_00, self, "a1", "a1", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)
        oasysgui.lineEdit(left_box_00, self, "a2", "a2", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)
        oasysgui.lineEdit(left_box_00, self, "a3", "a3", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)
        oasysgui.lineEdit(left_box_00, self, "a4", "a4", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)
        oasysgui.lineEdit(left_box_00, self, "a5", "a5", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)
        oasysgui.lineEdit(left_box_00, self, "a6", "a6", labelWidth=260, valueType=str, orientation="horizontal", callback=self.set_K)

        oasysgui.lineEdit(left_box_0, self, "pow_dens_screen",  "Distance to power density screen (m)",
                          labelWidth=260, valueType=float, orientation="horizontal",
                          callback=self.update)

        self.initializeTabs()

        # self.populate_gap_parametrization()
        # self.populate_electron_beam()
        # self.populate_magnetic_structure()
        # self.set_ebs_electron_beam()

        self.populate_settings_after_setting_K()
        self.set_visible()
        self.update()


    def get_id_list(self):
        out_list = [("ID%02d %s" % (self.data_dict["straight_section"][i], self.data_dict["id_name"][i])) for i in
                    range(len(self.data_dict["id_name"]))]

        out_list.insert(0,"<None>") # We add None at the beginning: ebs_id_index is the dict index plus one
        return out_list

    def titles(self):
        return ["K vs Gap", "B vs Gap", "Gap vs resonance energy", "Power vs Gap", "Power density peak at screen vs Gap"]

    def xtitles(self):
        return ['Gap [mm]'] * len(self.titles())

    def ytitles(self):
        return ['K', 'B [T]', 'Photon energy [eV]', 'Power [W]', 'Power density peak at %2d m [W/mm$^2$]'%(self.pow_dens_screen)]

    def initializeTabs(self):
        self.tabs = oasysgui.tabWidget(self.mainArea)

        self.tab = [oasysgui.createTabPage(self.tabs, "Info",),
                    oasysgui.createTabPage(self.tabs, "K vs Gap"),
                    oasysgui.createTabPage(self.tabs, "B vs Gap"),
                    oasysgui.createTabPage(self.tabs, "Resonance vs Gap"),
                    oasysgui.createTabPage(self.tabs, "Power vs Gap"),
                    oasysgui.createTabPage(self.tabs, "Pow_dens_peak vs Gap"),
                    oasysgui.createTabPage(self.tabs, "Script")
                    ]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        # info widget
        self.info_id = oasysgui.textArea(height=self.IMAGE_HEIGHT-5, width=self.IMAGE_WIDTH-5)
        profile_box = oasysgui.widgetBox(self.tab[0], "", addSpace=True, orientation="horizontal",
                                         height = self.IMAGE_HEIGHT, width=self.IMAGE_WIDTH-5)
        profile_box.layout().addWidget(self.info_id)

        # plot widgets
        n_plots = len(self.titles())
        self.plot_canvas = [None] * (1 + n_plots)

        for i in range(n_plots):
            self.plot_canvas[i] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.plot_canvas[i].setDefaultPlotLines(True)
            self.plot_canvas[i].setActiveCurveColor(color='blue')
            self.plot_canvas[i].setGraphXLabel(self.xtitles()[i])
            self.plot_canvas[i].setGraphYLabel(self.ytitles()[i])
            self.plot_canvas[i].setGraphTitle(self.titles()[i])
            self.plot_canvas[i].setInteractiveMode(mode='zoom')

        for index in range(0, 5):
            self.tab[index + 1].layout().addWidget(self.plot_canvas[index])

        # script widget

        # script_tab = oasysgui.createTabPage(self.main_tabs, "Script")
        self.python_script = PythonScript()
        self.python_script.code_area.setFixedHeight(400)
        script_box = gui.widgetBox(self.tab[6], "Python script", addSpace=True, orientation="horizontal")
        script_box.layout().addWidget(self.python_script)

        #
        self.tabs.setCurrentIndex(1)

    def check_magnetic_structure(self):
        congruence.checkPositiveNumber(self.K_horizontal, "Horizontal K")
        congruence.checkPositiveNumber(self.K_vertical, "Vertical K")
        congruence.checkStrictlyPositiveNumber(self.period_length, "Period Length")
        congruence.checkStrictlyPositiveNumber(self.number_of_periods, "Number of Periods")

    def set_ebs_electron_beam_S28D_5pmV(self):
        self.type_of_properties = 1
        self.electron_beam_size_h = 30.1836e-6
        self.electron_beam_size_v = 3.63641e-6
        self.electron_beam_divergence_h = 4.36821e-6
        self.electron_beam_divergence_v = 1.37498e-6

        #
        eb = self.get_electron_beam()

        moment_xx, moment_xxp, moment_xpxp, moment_yy, moment_yyp, moment_ypyp = eb.get_moments_all()
        self.moment_xx   = moment_xx
        self.moment_yy   = moment_yy
        self.moment_xxp  = moment_xxp
        self.moment_yyp  = moment_yyp
        self.moment_xpxp = moment_xpxp
        self.moment_ypyp = moment_ypyp

        ex, ax, bx, ey, ay, by = eb.get_twiss_no_dispersion_all()
        self.electron_beam_beta_h = bx
        self.electron_beam_beta_v = by
        self.electron_beam_alpha_h = ax
        self.electron_beam_alpha_v = ay
        self.electron_beam_eta_h = ex
        self.electron_beam_eta_v = ey
        self.electron_beam_etap_h = 0.0
        self.electron_beam_etap_v = 0.0
        self.electron_beam_emittance_h = 1.3166e-10
        self.electron_beam_emittance_v = 5e-12


    def set_ebs_electron_beam_S28D_10pmV(self):
        self.type_of_properties = 1
        self.electron_beam_size_h = 30.1836e-6
        self.electron_beam_size_v = 5.14266e-06 # 3.63641e-6
        self.electron_beam_divergence_h = 4.36821e-6
        self.electron_beam_divergence_v = 1.94452e-06 # 1.37498e-6

        #
        eb = self.get_electron_beam()

        moment_xx, moment_xxp, moment_xpxp, moment_yy, moment_yyp, moment_ypyp = eb.get_moments_all()
        self.moment_xx   = moment_xx
        self.moment_yy   = moment_yy
        self.moment_xxp  = moment_xxp
        self.moment_yyp  = moment_yyp
        self.moment_xpxp = moment_xpxp
        self.moment_ypyp = moment_ypyp

        ex, ax, bx, ey, ay, by = eb.get_twiss_no_dispersion_all()
        self.electron_beam_beta_h = bx
        self.electron_beam_beta_v = by
        self.electron_beam_alpha_h = ax
        self.electron_beam_alpha_v = ay
        self.electron_beam_eta_h = ex
        self.electron_beam_eta_v = ey
        self.electron_beam_etap_h = 0.0
        self.electron_beam_etap_v = 0.0
        self.electron_beam_emittance_h = 1.3166e-10
        self.electron_beam_emittance_v = 10e-12

    def get_id_number(self):
        if self.ebs_id_index == 0: # <None>
            id = 1 # this is by convention, zero would give errors
        else:
            label = self.get_id_list()[self.ebs_id_index]
            id = int(label[2:4])
        return id

    def set_ebs_electron_beam_S28F(self):
        self.type_of_properties = 1

        data, epsilonX, epsilonY = get_electron_beam_parameters_from_at(id=self.get_id_number())

        self.electron_beam_size_h       = numpy.round(1e-6 * data[0, 21], 11)
        self.electron_beam_size_v       = numpy.round(1e-6 * data[0, 22], 11)
        self.electron_beam_divergence_h = numpy.round(1e-6 * data[0, 23], 11)
        self.electron_beam_divergence_v = numpy.round(1e-6 * data[0, 24], 11)

        self.moment_xx   = data[0, 15]
        self.moment_yy   = data[0, 16]
        self.moment_xxp  = data[0, 17]
        self.moment_yyp  = data[0, 18]
        self.moment_xpxp = data[0, 19]
        self.moment_ypyp = data[0, 20]

        self.electron_beam_beta_h      = data[0, 7]
        self.electron_beam_beta_v      = data[0, 8]
        self.electron_beam_alpha_h     = data[0, 5]
        self.electron_beam_alpha_v     = data[0, 6]
        self.electron_beam_eta_h       = data[0, 11]
        self.electron_beam_eta_v       = data[0, 12]
        self.electron_beam_etap_h      = data[0, 13]
        self.electron_beam_etap_v      = data[0, 14]
        self.electron_beam_emittance_h = epsilonX
        self.electron_beam_emittance_v = epsilonY


    def update_electron_beam(self):
        self.type_of_properties_initial_selection = self.type_of_properties

        if self.type_of_properties_initial_selection == 4:
            self.set_ebs_electron_beam_S28D_5pmV()  # will change self.type_of_properties
        elif self.type_of_properties_initial_selection == 5:
            self.set_ebs_electron_beam_S28D_10pmV() # will change self.type_of_properties
        elif self.type_of_properties_initial_selection == 6:
            self.set_ebs_electron_beam_S28F() # will change self.type_of_properties

        self.set_visible()
        self.update()

    def update(self):
        self.check_data()
        self.update_info()
        self.update_plots()
        self.update_script()

    def update_info(self):

        syned_electron_beam = self.get_electron_beam()
        syned_undulator = self.get_magnetic_structure()

        gamma = self.gamma()

        if self.ebs_id_index == 0:
            id = "<None>"
        else:
            id = "ID%02d %s" % (self.data_dict["straight_section"][self.ebs_id_index-1], self.data_dict["id_name"][self.ebs_id_index-1])

        info_parameters = {
            "electron_energy_in_GeV":self.electron_energy_in_GeV,
            "gamma":"%8.3f"%self.gamma(),
            "ring_current":"%4.3f "%syned_electron_beam.current(),
            "K_horizontal":syned_undulator.K_horizontal(),
            "K_vertical": syned_undulator.K_vertical(),
            "period_length": syned_undulator.period_length(),
            "number_of_periods": syned_undulator.number_of_periods(),
            "undulator_length": syned_undulator.length(),
            "resonance_energy":"%6.3f"%syned_undulator.resonance_energy(gamma,harmonic=1),
            "resonance_energy3": "%6.3f" % syned_undulator.resonance_energy(gamma,harmonic=3),
            "resonance_energy5": "%6.3f" % syned_undulator.resonance_energy(gamma,harmonic=5),
            "B_horizontal":"%4.2F"%syned_undulator.magnetic_field_horizontal(),
            "B_vertical": "%4.2F" % syned_undulator.magnetic_field_vertical(),
            "cc_1": "%4.2f" % (1e6*syned_undulator.gaussian_central_cone_aperture(gamma,1)),
            "cc_3": "%4.2f" % (1e6*syned_undulator.gaussian_central_cone_aperture(gamma,3)),
            "cc_5": "%4.2f" % (1e6*syned_undulator.gaussian_central_cone_aperture(gamma,5)),
            # "cc_7": "%4.2f" % (self.gaussian_central_cone_aperture(7)*1e6),
            "sigma_rad": "%5.2f"        % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=1)[0]),
            "sigma_rad_prime": "%5.2f"  % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=1)[1]),
            "sigma_rad3": "%5.2f"       % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=3)[0]),
            "sigma_rad_prime3": "%5.2f" % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=3)[1]),
            "sigma_rad5": "%5.2f" % (1e6 * syned_undulator.get_sigmas_radiation(gamma, harmonic=5)[0]),
            "sigma_rad_prime5": "%5.2f" % (1e6 * syned_undulator.get_sigmas_radiation(gamma, harmonic=5)[1]),
            "first_ring_1": "%5.2f" % (1e6*syned_undulator.get_resonance_ring(gamma, harmonic=1, ring_order=1)),
            "first_ring_3": "%5.2f" % (1e6*syned_undulator.get_resonance_ring(gamma, harmonic=3, ring_order=1)),
            "first_ring_5": "%5.2f" % (1e6*syned_undulator.get_resonance_ring(gamma, harmonic=5, ring_order=1)),
            "Sx": "%5.2f"  % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[0]),
            "Sy": "%5.2f"  % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[1]),
            "Sxp": "%5.2f" % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[2]),
            "Syp": "%5.2f" % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[3]),
            "und_power": "%5.2f" % syned_undulator.undulator_full_emitted_power(gamma,syned_electron_beam.current()),
            "CF_h": "%4.3f" % syned_undulator.approximated_coherent_fraction_horizontal(syned_electron_beam,harmonic=1),
            "CF_v": "%4.3f" % syned_undulator.approximated_coherent_fraction_vertical(syned_electron_beam,harmonic=1),
            "CF": "%4.3f" % syned_undulator.approximated_coherent_fraction(syned_electron_beam,harmonic=1),
            "url": self.data_url,
            "id": id,
            "gap": "%4.3f" % self.calculate_gap_from_K(),
            "a0": "%s" % str(self.a0),
            "a1": "%s" % str(self.a1),
            "a2": "%s" % str(self.a2),
            "a3": "%s" % str(self.a3),
            "a4": "%s" % str(self.a4),
            "a5": "%s" % str(self.a5),
            "a6": "%s" % str(self.a6),
            }

        self.info_id.setText(self.info_template().format_map(info_parameters))
        # self.tabs[0].setText(self.info_template().format_map(info_parameters))

    def info_electron_beam(self):
        txt = "\n"
        txt += "================ electron parameters ===========\n"
        if self.type_of_properties == 0:
            txt += "from user 2nd Moments\n"
        elif self.type_of_properties == 3:
            txt += "from user Twiss Parameters\n"
        elif self.type_of_properties == 4:
            txt += "Zero emittance "
        else:
            txt += "from Size/Divergence "
            if self.type_of_properties_initial_selection == 4:
                txt += "(retrieved from S28D with V emittance 5 pm: \n"
            elif self.type_of_properties_initial_selection == 5:
                txt += "(retrieved from S28D with vertical emittance 10 pm: \n"
            elif self.type_of_properties_initial_selection == 6:
                txt += "(retrieved from S28F for ID%02d): \n" % (self.get_id_number())
            else:
                txt += ": \n"

            txt += "sigma x: %5.2f um\n"  % (1e6 * self.electron_beam_size_h)
            txt += "sigma y: %5.2f um\n"  % (1e6 * self.electron_beam_size_v)
            txt += "sigma xp: %5.2f urad\n" % (1e6 * self.electron_beam_divergence_h)
            txt += "sigma yp: %5.2f urad\n" % (1e6 * self.electron_beam_divergence_v)
        txt += "================================================\n"

        return txt


    def info_template(self):
        return self.info_electron_beam() + \
"""
ID data url: {url}
id_name: {id}

================ input parameters ===========
Electron beam energy [GeV]: {electron_energy_in_GeV}
Electron current:           {ring_current}
Period Length [m]:          {period_length}
Number of Periods:          {number_of_periods}

Horizontal K:               {K_horizontal}
Vertical K:                 {K_vertical}
==============================================

Electron beam gamma:                {gamma}
Undulator Length [m]:               {undulator_length}
Horizontal Peak Magnetic field [T]: {B_horizontal}
Vertical Peak Magnetic field [T]:   {B_vertical}

Total power radiated by the undulator [W]: {und_power}

Gap in use: {gap} mm
Using gap parametrization: 
    a0: {a0}
    a1: {a1}
    a2: {a2}
    a3: {a3}
    a4: {a4}
    a5: {a5}
    a6: {a6}

Note on calculation: 
A = [a0,a1,a2,...] = [B_1, B_2,..., alpha_1, alpha_2,...]
Bmax = Sum[B_i * exp( -pi * alpha_i * (gap[mm] / id_period[mm]) )] with i from 1 to the semilength of A. 

Resonances:

Photon energy [eV]: 
       for harmonic 1 : {resonance_energy}
       for harmonic 3 : {resonance_energy3}
       for harmonic 5 : {resonance_energy5}

Central cone (RMS urad):
       for harmonic 1 : {cc_1}
       for harmonic 3 : {cc_3}
       for harmonic 5 : {cc_5}

First ring at (urad):
       for harmonic 1 : {first_ring_1}
       for harmonic 3 : {first_ring_3}
       for harmonic 5 : {first_ring_5}

Sizes and divergences of radiation :
    at 1st harmonic: sigma: {sigma_rad} um, sigma': {sigma_rad_prime} urad
    at 3rd harmonic: sigma: {sigma_rad3} um, sigma': {sigma_rad_prime3} urad
    at 5th harmonic: sigma: {sigma_rad5} um, sigma': {sigma_rad_prime5} urad
    
Sizes and divergences of photon source (convolution) at resonance (1st harmonic): :
    Sx: {Sx} um
    Sy: {Sy} um,
    Sx': {Sxp} urad
    Sy': {Syp} urad
    
Approximated coherent fraction at 1st harmonic: 
    Horizontal: {CF_h}
    Vertical: {CF_v} 
    Coherent fraction 2D (HxV): {CF} 

"""

    def get_magnetic_structure(self, check_for_wiggler=False):

        if not(check_for_wiggler):
            return Undulator(K_horizontal=self.K_horizontal,
                             K_vertical=self.K_vertical,
                             period_length=self.period_length,
                             number_of_periods=self.number_of_periods)
        else:
            id_name = self.get_id_list()[self.ebs_id_index]
            if "W" in id_name:
                return Wiggler(K_horizontal=self.K_horizontal,
                                 K_vertical=self.K_vertical,
                                 period_length=self.period_length,
                                 number_of_periods=self.number_of_periods)
            else:
                return Undulator(K_horizontal=self.K_horizontal,
                                 K_vertical=self.K_vertical,
                                 period_length=self.period_length,
                                 number_of_periods=self.number_of_periods)


    def check_magnetic_structure_instance(self, magnetic_structure):
        if not isinstance(magnetic_structure, Undulator):
            raise ValueError("Magnetic Structure is not a Undulator")

    def populate_magnetic_structure(self):
        # if magnetic_structure is None:
        index = self.ebs_id_index - 1
        self.K_horizontal = 0.0
        self.K_vertical = numpy.round(self.data_dict["Kmax"][index],4)
        self.period_length = numpy.round(self.data_dict["id_period"][index],4)
        self.number_of_periods = numpy.round(self.data_dict["id_length"][index] / self.period_length,3)

    def populate_gap_parametrization(self):
        index = self.ebs_id_index - 1
        if self.data_dict["a0"][index] is None:
            self.a0 = ''
        else:
            self.a0 = self.data_dict["a0"][index]


        if self.data_dict["a1"][index] is None:
            self.a1 = ''
        else:
            self.a1 = self.data_dict["a1"][index]

        if self.data_dict["a2"][index] is None:
            self.a2 = ''
        else:
            self.a2 = self.data_dict["a2"][index]

        if self.data_dict["a3"][index] is None:
            self.a3 = ''
        else:
            self.a3 = self.data_dict["a3"][index]

        if self.data_dict["a4"][index] is None:
            self.a4 = ''
        else:
            self.a4 = self.data_dict["a4"][index]

        if self.data_dict["a5"][index] is None:
            self.a5 = ''
        else:
            self.a5= self.data_dict["a5"][index]

        if self.data_dict["a6"][index] is None:
            self.a6 = ''
        else:
            self.a6 = self.data_dict["a6"][index]


        # self.a0 = self.data_dict["a0"][index]
        # self.a1 = self.data_dict["a1"][index]
        # self.a2 = self.data_dict["a2"][index]
        # self.a3 = self.data_dict["a3"][index]
        # self.a4 = self.data_dict["a4"][index]
        # self.a5 = self.data_dict["a5"][index]
        # self.a6 = self.data_dict["a6"][index]

    def populate_settings_after_setting_K(self):

        syned_undulator = self.get_magnetic_structure()
        self.auto_energy = numpy.round(syned_undulator.resonance_energy(self.gamma(),
                                            harmonic=self.auto_harmonic_number),3)

        self.gap_mm = numpy.round(self.calculate_gap_from_K(), 3)

    def set_gap(self, which=VERTICAL):
        if self.gap_mm < self.gap_min:
            if ConfirmDialog.confirmed(self, message="Gap is smaller than minimum. Set to minimum?"):
                self.gap_mm = self.gap_min

        if self.gap_mm > self.gap_max:
            if ConfirmDialog.confirmed(self, message="Gap is larger than maximum. Set to maximum?"):
                self.gap_mm = self.gap_max

        if self.gap_mm < self.gap_min:
            raise Exception("Gap is smaller than minimum")

        if self.gap_mm > self.gap_max:
            raise Exception("Gap is larger than maximum")

        K = numpy.round(self.calculate_K_from_gap(), 3)

        if which == VERTICAL:
            self.K_vertical = K
            self.K_horizontal = 0.0

        if which == BOTH:
            Kboth = round(K / numpy.sqrt(2), 6)
            self.K_vertical =  Kboth
            self.K_horizontal = Kboth

        if which == HORIZONTAL:
            self.K_horizontal = K
            self.K_vertical = 0.0

        self.populate_settings_after_setting_K()
        self.update()

    def set_id(self):
        if self.type_of_properties_initial_selection == 6:
            self.set_ebs_electron_beam_S28F()

        if self.ebs_id_index !=0:
            self.populate_gap_parametrization()
            self.populate_magnetic_structure()
            self.gap_min = self.data_dict["id_minimum_gap_mm"][self.ebs_id_index-1]

        self.populate_settings_after_setting_K()
        self.update()

    def set_K(self):
        self.populate_settings_after_setting_K()
        self.update()

    def auto_set_undulator_V(self):
        self.set_resonance_energy(VERTICAL)

    def auto_set_undulator_H(self):
        self.set_resonance_energy(HORIZONTAL)

    def auto_set_undulator_B(self):
        self.set_resonance_energy(BOTH)

    def set_resonance_energy(self, which=VERTICAL):
        congruence.checkStrictlyPositiveNumber(self.auto_energy, "Set Undulator at Energy")
        congruence.checkStrictlyPositiveNumber(self.auto_harmonic_number, "As Harmonic #")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV, "Energy")
        congruence.checkStrictlyPositiveNumber(self.period_length, "Period Length")

        wavelength = self.auto_harmonic_number*m2ev/self.auto_energy
        K = round(numpy.sqrt(2*(((wavelength*2*self.gamma()**2)/self.period_length)-1)), 6)

        Kmax = self.calculate_K_from_gap(self.gap_min)
        Kmin = self.calculate_K_from_gap(self.gap_max)

        if numpy.isnan(K):
            if ConfirmDialog.confirmed(self, message="Impossible configuration. Set to Kmin=%f?" % (Kmin)):
                K = numpy.round(Kmin, 4)

        if (K > Kmax):
            if ConfirmDialog.confirmed(self, message="Needed K (%f) > Kmax (%f). Reset to Kmax?" % (K, Kmax)):
                K = numpy.round(Kmax, 4)

        if (K < Kmin):
            if ConfirmDialog.confirmed(self, message="Needed K (%f) < Kmin (%f). Reset to Kmin?" % (K, Kmin)):
                K = numpy.round(Kmin, 4)

        if which == VERTICAL:
            self.K_vertical = K
            self.K_horizontal = 0.0

        if which == BOTH:
            Kboth = round(K / numpy.sqrt(2), 6)
            self.K_vertical =  Kboth
            self.K_horizontal = Kboth

        if which == HORIZONTAL:
            self.K_horizontal = K
            self.K_vertical = 0.0

        self.populate_settings_after_setting_K()
        self.update()

    def plot_graph(self, plot_canvas_index, curve_name, x_values, y_values, xtitle="", ytitle="",
                   color='blue', replace=True):
        self.plot_canvas[plot_canvas_index].addCurve(x_values, y_values, curve_name, symbol='', color=color, replace=replace) #'+', '^', ','
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].replot()

    def update_plots(self):

        gap_mm = numpy.linspace(self.gap_min * 0.9, self.gap_max * 1.1, 1000)

        Karray = self.calculate_K_from_gap(gap_mm)
        Karray_horizontal = numpy.zeros_like(Karray)

        Bfield = Karray / (self.period_length * codata.e / (2 * numpy.pi * codata.m_e * codata.c))

        E1_array = self.calculate_resonance_energy(Karray)

        ptot = (self.number_of_periods /6) * codata.value('characteristic impedance of vacuum') * \
               self.ring_current * codata.e * 2 * numpy.pi * codata.c * self.gamma()**2 * \
               (Karray**2 + Karray_horizontal**2) / self.period_length

        ### power density peak at a given distance, not yet implemented for helical undulators ###        
        
        ### From: Undulators, Wigglers and their Applications - H. Onuki & P Elleaume ###
        ### Chapter 3: Undulator radiation eqs. 68 and 69 ###
        g_k = Karray * ((Karray**6) + (24/7)*(Karray**4) + 4*(Karray**2) + (16/7))/((1 + (Karray**2))**(7/2))

        p_dens_peak = ((21 * (self.gamma()**2)) / (16 * numpy.pi * Karray) * ptot * g_k)/((self.pow_dens_screen * 1e3)**2)

        self.plot_graph(0, self.titles()[0], gap_mm, Karray, xtitle=self.xtitles()[0], ytitle=self.ytitles()[0])
        self.plot_graph(1, self.titles()[1], gap_mm, Bfield, xtitle=self.xtitles()[1], ytitle=self.ytitles()[1])
        #
        #
        #
        xtitle = "Photon energy [keV]"
        ytitle = "Gap [mm]"
        colors = ['green', 'black', 'red', 'brown', 'orange', 'pink'] * self.harmonic_max
        for i in range(1, self.harmonic_max+1):
            self.plot_canvas[2].addCurve(E1_array * i* 1e-3, gap_mm,
                                         "harmonic %d" % i,
                                         xlabel=xtitle, ylabel=ytitle,
                                         symbol='', color=colors[i-1])


        self.plot_canvas[2].getLegendsDockWidget().setFixedHeight(150)
        self.plot_canvas[2].getLegendsDockWidget().setVisible(True)
        self.plot_canvas[2].setActiveCurve("harmonic 1")
        self.plot_canvas[2].replot()
        #
        #
        #
        self.plot_graph(3, self.titles()[3], gap_mm, ptot, xtitle=self.xtitles()[3], ytitle=self.ytitles()[3])

        self.plot_graph(4, self.titles()[4], gap_mm, p_dens_peak, xtitle=self.xtitles()[4], ytitle=self.ytitles()[4])

    def update_script(self):



        #

        script = """
import numpy
import scipy.constants as codata
from srxraylib.plot.gol import plot"""

        # inputs
        script += "\n\n#\n# inputs\n#"
        script += "\ngap_min                = %g # mm" % self.gap_min
        script += "\ngap_max                = %g # mm" % self.gap_max
        script += "\nperiod_length          = %g # m" % self.period_length
        script += "\nnumber_of_periods      = %g" % self.number_of_periods
        script += "\nring_current           = %g # A" % self.ring_current
        script += "\nelectron_energy_in_GeV = %g # GeV" % self.electron_energy_in_GeV
        script += "\npow_dens_screen        = %g # distance to screen in m" % self.pow_dens_screen
        script += "\nauto_harmonic_number   = %g" % self.auto_harmonic_number

        a = [self.a0,
             self.a1,
             self.a2,
             self.a3,
             self.a4,
             self.a5,
             self.a6,
             ]

        A = []
        for i in range(7):
            try:
                A.append(float(a[i]))
            except:
                pass

        script += "\nA = " + repr(A)

        script += """

#
# calculations
#
gap_mm = numpy.linspace(gap_min * 0.9, gap_max * 1.1, 1000)
i_half = len(A) // 2

# get K vs gap
Bmax = numpy.zeros_like(gap_mm)
for i in range(i_half):
    Bmax += A[i] * numpy.exp(-numpy.pi * (i + 1) * A[i + i_half] * gap_mm / (period_length * 1e3))

Karray = Bmax * period_length * codata.e / (2 * numpy.pi * codata.m_e * codata.c)

# resonance energy
gamma1 = 1e9 * electron_energy_in_GeV / (codata.m_e *  codata.c**2 / codata.e)
Karray_horizontal = numpy.zeros_like(Karray)
Bfield = Bmax # Karray / (period_length * codata.e / (2 * numpy.pi * codata.m_e * codata.c))

theta_x = 0.0
theta_z = 0.0
wavelength = (period_length / (2.0 * gamma1 ** 2)) * (1 + Karray ** 2 / 2.0 + Karray_horizontal ** 2 / 2.0 + gamma1 ** 2 * (theta_x ** 2 + theta_z ** 2))
energy_in_ev = codata.h * codata.c / wavelength / codata.e
E1_array = energy_in_ev

# power
ptot = (number_of_periods / 6) * codata.value('characteristic impedance of vacuum') * ring_current * codata.e * 2 * numpy.pi * codata.c * gamma1 ** 2 * (Karray ** 2 + Karray_horizontal ** 2) / period_length

### From: Undulators, Wigglers and their Applications - H. Onuki & P Elleaume ###
### Chapter 3: Undulator radiation eqs. 68 and 69 ###
g_k = Karray * ((Karray ** 6) + (24 / 7) * (Karray ** 4) + 4 * (Karray ** 2) + (16 / 7)) / ((1 + (Karray ** 2)) ** (7 / 2))

p_dens_peak = ((21 * (gamma1 ** 2)) / (16 * numpy.pi * Karray) * ptot * g_k) / ((pow_dens_screen * 1e3) ** 2)

#
# plots
#
plot(gap_mm, Karray, title="K vs Gap", xtitle="Gap [mm]", ytitle="K", show=0)
plot(gap_mm, Bfield, title="B vs Gap", xtitle="Gap [mm]", ytitle="B [T]", show=0)
plot(E1_array, gap_mm,
          E1_array * 3, gap_mm,
          E1_array * 5, gap_mm,
          title="Gap vs resonance energy", xtitle="Photon energy [eV]", ytitle="Gap [mm]",
          legend=['harmonic 1', 'harmonic 3', 'harmonic 5'], show=0)
plot(gap_mm, ptot,        title="Power vs Gap", xtitle="Gap [mm]", ytitle="Power [W]", show=0)
plot(gap_mm, p_dens_peak, title="Power density peak at screen vs Gap", xtitle="Gap [mm]", ytitle="Power density peak at screen [W/mm2]", show=1)
"""

        self.python_script.set_code(script)


    def calculate_resonance_energy(self, Karray):

        theta_x = 0.0
        theta_z = 0.0
        K_vertical = Karray
        K_horizontal = numpy.zeros_like(K_vertical)

        wavelength = (self.period_length / (2.0 * self.gamma() ** 2)) * \
                         (1 + K_vertical ** 2 / 2.0 + K_horizontal ** 2 / 2.0 + \
                          self.gamma() ** 2 * (theta_x ** 2 + theta_z ** 2))

        energy_in_ev = codata.h * codata.c / wavelength / codata.e

        return energy_in_ev


    def calculate_K_from_gap(self, gap_mm=None):

        if gap_mm is None: gap_mm = self.gap_mm
        id_period_mm  = self.period_length * 1e3
        id_name = self.get_id_list()[self.ebs_id_index]

        try:
            a0 = float(self.a0)
        except:
            a0 = None

        try:
            a1 = float(self.a1)
        except:
            a1 = None

        try:
            a2 = float(self.a2)
        except:
            a2 = None

        try:
            a3 = float(self.a3)
        except:
            a3 = None

        try:
            a4 = float(self.a4)
        except:
            a4 = None

        try:
            a5 = float(self.a5)
        except:
            a5 = None

        try:
            a6 = float(self.a6)
        except:
            a6 = None


        Bmax = self.calculate_B_from_gap_and_A_vector(
            gap_mm, id_period_mm, id_name,
            a0=a0, a1=a1, a2=a2, a3=a3, a4=a4, a5=a5, a6=a6)

        Kmax = Bmax * (id_period_mm * 1e-3) * codata.e / (2 * numpy.pi * codata.m_e * codata.c)

        return Kmax

    def calculate_gap_from_K(self, Kvalue=None):
        if Kvalue is None: Kvalue = self.K_vertical

        gap_mm_array = numpy.linspace( self.gap_min * 0.9, self.gap_max * 1.1, 1000)
        K_array = self.calculate_K_from_gap(gap_mm_array)

        # if ((Kvalue < K_array.min()) or (Kvalue > K_array.max())):
        #     print("K: %g, gap_max: %g; K_array min:%g, max:%g" % (Kvalue, self.gap_max, K_array.min(), K_array.max()))
        #     raise Exception("Cannot interpolate...")

        if Kvalue < K_array.min():
            if ConfirmDialog.confirmed(self, message="K=%g is smaller than minimum=%g. Set to minimum?" % (Kvalue, K_array.min())):
                Kvalue = K_array.min()
                self.K_vertical = Kvalue
                self.populate_settings_after_setting_K()
                self.update()

        if Kvalue > K_array.max():
            if ConfirmDialog.confirmed(self, message="K=%g is larger than maximum=%g. Set to maximum?" % (Kvalue, K_array.max())):
                Kvalue = K_array.max()
                self.K_vertical = Kvalue
                self.populate_settings_after_setting_K()
                self.update()

        gap_interpolated = numpy.interp(Kvalue, numpy.flip(K_array), numpy.flip(gap_mm_array))

        return gap_interpolated

    def gamma(self):
        return 1e9*self.electron_energy_in_GeV / (codata.m_e *  codata.c**2 / codata.e)

    def set_visible(self):
        self.left_box_2_1.setVisible(self.type_of_properties == 0)
        self.left_box_2_2.setVisible(self.type_of_properties == 1)
        self.left_box_2_3.setVisible(self.type_of_properties == 2)

    def check_data(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV , "Energy")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")
        congruence.checkStrictlyPositiveNumber(self.pow_dens_screen, "Distance to power density screen")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx   , "Moment xx")
            congruence.checkPositiveNumber(self.moment_xpxp , "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy   , "Moment yy")
            congruence.checkPositiveNumber(self.moment_ypyp , "Moment ypyp")
        elif self.type_of_properties == 1:
            congruence.checkPositiveNumber(self.electron_beam_size_h       , "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h , "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_size_v       , "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v , "Vertical Beam Divergence")
        elif self.type_of_properties == 2:
            congruence.checkPositiveNumber(self.electron_beam_emittance_h, "Horizontal Beam Emittance")
            congruence.checkPositiveNumber(self.electron_beam_emittance_v, "Vertical Beam Emittance")
            congruence.checkNumber(self.electron_beam_alpha_h, "Horizontal Beam Alpha")
            congruence.checkNumber(self.electron_beam_alpha_v, "Vertical Beam Alpha")
            congruence.checkNumber(self.electron_beam_beta_h, "Horizontal Beam Beta")
            congruence.checkNumber(self.electron_beam_beta_v, "Vertical Beam Beta")
            congruence.checkNumber(self.electron_beam_eta_h, "Horizontal Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_eta_v, "Vertical Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_etap_h, "Horizontal Beam Dispersion Eta'")
            congruence.checkNumber(self.electron_beam_etap_v, "Vertical Beam Dispersion Eta'")

        self.check_magnetic_structure()

    def send_data(self):
        try:
            self.check_data()
            self.send("SynedData", Beamline(light_source=self.get_light_source(check_for_wiggler=True)))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

    def get_electron_beam(self):
        electron_beam = ElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                     energy_spread=self.electron_energy_spread,
                                     current=self.ring_current,
                                     number_of_bunches=self.number_of_bunches)

        if self.type_of_properties == 0:
            electron_beam.set_moments_horizontal(self.moment_xx, self.moment_xxp, self.moment_xpxp)
            electron_beam.set_moments_vertical(self.moment_yy, self.moment_yyp, self.moment_ypyp)

        elif self.type_of_properties == 1:
            electron_beam.set_sigmas_all(sigma_x=self.electron_beam_size_h,
                                         sigma_y=self.electron_beam_size_v,
                                         sigma_xp=self.electron_beam_divergence_h,
                                         sigma_yp=self.electron_beam_divergence_v)

        elif self.type_of_properties == 2:
            if self.electron_beam_emittance_h == 0: # TODO, remove when fixing syned electron_beam
                electron_beam.set_moments_horizontal(0, 0, 0)
            else:
                electron_beam.set_twiss_horizontal(self.electron_beam_emittance_h,
                                                 self.electron_beam_alpha_h,
                                                 self.electron_beam_beta_h)
            electron_beam.set_dispersion_horizontal(self.electron_beam_eta_h,
                                             self.electron_beam_etap_h)

            if self.electron_beam_emittance_v == 0: # TODO, remove when fixing syned electron_beam
                electron_beam.set_moments_vertical(0, 0, 0)
            else:
                electron_beam.set_twiss_vertical(self.electron_beam_emittance_v,
                                                 self.electron_beam_alpha_v,
                                                 self.electron_beam_beta_v)
            electron_beam.set_dispersion_vertical(self.electron_beam_eta_v,
                                             self.electron_beam_etap_v)

        elif self.type_of_properties == 3:
            electron_beam.set_moments_all(0,0,0,0,0,0)
        else:
            raise NotImplementedError()

        return electron_beam

    def get_light_source(self, check_for_wiggler=False):
        return LightSource(name=self.get_id_list()[self.ebs_id_index],
                           electron_beam = self.get_electron_beam(),
                           magnetic_structure = self.get_magnetic_structure(check_for_wiggler=check_for_wiggler))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    def populate_electron_beam(self, electron_beam=None):
        if electron_beam is None:
            electron_beam = ElectronBeam(
                                        energy_in_GeV = 6.0,
                                        energy_spread = 0.001,
                                        current = 0.2,
                                        number_of_bunches = 1,
                                        moment_xx   = (3.01836e-05)**2,
                                        moment_xxp  = (0.0)**2,
                                        moment_xpxp = (4.36821e-06)**2,
                                        moment_yy   = (3.63641e-06)**2,
                                        moment_yyp  = (0.0)**2,
                                        moment_ypyp = (1.37498e-06)**2,
                                        )

        self.electron_energy_in_GeV = electron_beam._energy_in_GeV
        self.electron_energy_spread = electron_beam._energy_spread
        self.ring_current = electron_beam._current
        self.number_of_bunches = electron_beam._number_of_bunches

        self.type_of_properties = 1

        self.moment_xx   = electron_beam._moment_xx
        self.moment_xxp  = electron_beam._moment_xxp
        self.moment_xpxp = electron_beam._moment_xpxp
        self.moment_yy   = electron_beam._moment_yy
        self.moment_yyp  = electron_beam._moment_yyp
        self.moment_ypyp = electron_beam._moment_ypyp

        x, xp, y, yp = electron_beam.get_sigmas_all()

        self.electron_beam_size_h = x
        self.electron_beam_size_v = y
        self.electron_beam_divergence_h = xp
        self.electron_beam_divergence_v = yp

    def calculate_B_from_gap_and_A_vector(self, id_gap_mm, id_period_mm, id_name,
                       a0=None, a1=None, a2=None, a3=None, a4=None, a5=None, a6=None,
                       check_elliptical=True):

        if check_elliptical:
            if "HU" in id_name:
                ConfirmDialog.confirmed(self, message="Helical/Apple undulators not implemented in this app (wrong results)")

        if "CPMU" in id_name:
            B  = a0 * numpy.exp(-numpy.pi * a3 * 1 * id_gap_mm / id_period_mm)
            B += a1 * numpy.exp(-numpy.pi * a4 * 2 * id_gap_mm / id_period_mm)
            B += a2 * numpy.exp(-numpy.pi * a5 * 3 * id_gap_mm / id_period_mm)

        elif "HU" in id_name:  # this is for apple undulator... It is applied also (WRONG!) to helical undulators
            reference_gap = 20.0
            B = a0 * numpy.exp(-numpy.pi * (id_gap_mm - reference_gap) / id_period_mm)
        else:
            if (a2 is None) and (a3 is None): # only one "harmonic"
                B = a0 * numpy.exp(-numpy.pi * a1 * id_gap_mm / id_period_mm)
            else:
                if (a4 is None) and (a5 is None):  # 2 "harmonics"
                    B =  a0 * numpy.exp(-numpy.pi * a2 * 1 * id_gap_mm / id_period_mm)
                    B += a1 * numpy.exp(-numpy.pi * a3 * 2 * id_gap_mm / id_period_mm)
                else: # 3 harmonics
                    B =  a0 * numpy.exp(-numpy.pi * a3 * 1 * id_gap_mm / id_period_mm)
                    B += a1 * numpy.exp(-numpy.pi * a4 * 2 * id_gap_mm / id_period_mm)
                    B += a2 * numpy.exp(-numpy.pi * a5 * 3 * id_gap_mm / id_period_mm)

        return B

    def get_data_dictionary_csv(self):
        url = self.data_url

        # tofloat = lambda s: numpy.array(['0.0' if v == '' else v for v in s]).astype(float)
        tofloat = lambda s: [None if v == '' else float(v) for v in s]
        try:
            filename = url # 'ftp://ftp.esrf.eu/pub/scisoft/syned/resources/jsrund.csv'
            ishift = 1
            a = numpy.genfromtxt(filename, dtype=str, delimiter=',', skip_header=3, skip_footer=1, converters=None, \
                                 missing_values={0: "11.000"}, filling_values={0: "XXX"}, usecols=None, names=None,
                                 excludelist=None, \
                                 deletechars=" !#$%&'()*+, -./:;<=>?@[\]^{|}~", replace_space='', autostrip=True, \
                                 case_sensitive=True, defaultfmt='f%i', unpack=None, usemask=False, loose=True, \
                                 invalid_raise=True, max_rows=None, encoding='bytes')

            number_of_ids = len(a)
            straight_section = a[:, 0].astype(int)
            id_name = a[:, 1]
            id_period = 1e-3 * a[:, 2 + ishift].astype(float)
            id_period_mm = a[:, 2 + ishift].astype(float)
            id_length = 1e-3 * a[:, 3 + ishift].astype(float)

            id_minimum_gap_mm = tofloat(a[:, 4 + ishift])
            for i in range(number_of_ids):
                if id_minimum_gap_mm[i] is None:
                    id_minimum_gap_mm[i] = 30.0 # set to arbitrary value ** Some values are missing!!!**

            a0 = tofloat(a[:, 5 + ishift])
            a1 = tofloat(a[:, 6 + ishift])
            a2 = tofloat(a[:, 7 + ishift])
            a3 = tofloat(a[:, 8 + ishift])
            a4 = tofloat(a[:, 9 + ishift])
            a5 = tofloat(a[:, 10 + ishift])
            a6 = tofloat(a[:, 11 + ishift])


            Bmax = []
            Kmax = []
            for i in range(number_of_ids):
                Bmax_i = self.calculate_B_from_gap_and_A_vector(
                    id_minimum_gap_mm[i], id_period_mm[i], id_name[i],
                    a0=a0[i], a1=a1[i], a2=a2[i], a3=a3[i], a4=a4[i], a5=a5[i], a6=a5[i],
                    check_elliptical=False)
                Bmax.append(Bmax_i)
                Kmax.append(Bmax_i * id_period[i] * codata.e / (2 * numpy.pi * codata.m_e * codata.c))


            out_dict = {}
            out_dict["straight_section"] = straight_section.tolist()
            out_dict["id_name"] = id_name.tolist()
            out_dict["id_minimum_gap_mm"] = id_minimum_gap_mm
            out_dict["Bmax"] = Bmax
            out_dict["Kmax"] = Kmax
            out_dict["straight_section"] = straight_section.tolist()
            out_dict["id_period"] = id_period.tolist()
            out_dict["id_period_mm"] = id_period_mm.tolist()
            out_dict["id_length"] = id_length.tolist()
            out_dict["a0"] = a0
            out_dict["a1"] = a1
            out_dict["a2"] = a2
            out_dict["a3"] = a3
            out_dict["a4"] = a4
            out_dict["a5"] = a5
            out_dict["a6"] = a6

        except:
            out_dict = {}
            out_dict["straight_section"]  = []
            out_dict["id_name"]           = []
            out_dict["id_minimum_gap_mm"] = []
            out_dict["Bmax"]              = []
            out_dict["Kmax"]              = []
            out_dict["straight_section"]  = []
            out_dict["id_period"]         = []
            out_dict["id_period_mm"]      = []
            out_dict["id_length"]         = []
            out_dict["a0"]                = []
            out_dict["a1"]                = []
            out_dict["a2"]                = []
            out_dict["a3"]                = []
            out_dict["a4"]                = []
            out_dict["a5"]                = []
            out_dict["a6"]                = []

        self.data_dict = out_dict

    # OLD data format...
    def get_data_dictionary(self):
        import json
        from urllib.request import urlopen

        file_url = self.data_url # "https://raw.githubusercontent.com/srio/shadow3-scripts/master/ESRF-LIGHTSOURCES-EBS/ebs_ids.json"

        u = urlopen(file_url)
        ur = u.read()
        url = ur.decode(encoding='UTF-8')

        dictionary = json.loads(url)

        self.data_dict = dictionary

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    a = QApplication(sys.argv)
    ow = OWEBS()
    ow.show()
    a.exec_()


    # data = get_electron_beam_parameters_from_at(id=8)
    # print(data.shape, data[0, [21, 22, 23, 24]])

    # data_dict = get_data_dictionary()
    # out_list = [("ID%02d %s" % (data_dict["straight_section"][i],data_dict["id_name"][i])) for i in range(len(data_dict["id_name"]))]
    # print(out_list)

    # data_dict_old = data_dict
    # data_dict = get_data_dictionary_csv()
    # out_list = [("ID%02d %s" % (data_dict["straight_section"][i],data_dict["id_name"][i])) for i in range(len(data_dict["id_name"]))]
    # print(out_list)

    # for key in data_dict.keys():
    #     if key != "id_name":
    #         print(numpy.array(data_dict[key]) - numpy.array(data_dict_old[key]))

    # print(data_dict["id_name"])
    # print(data_dict_old["id_name"])
