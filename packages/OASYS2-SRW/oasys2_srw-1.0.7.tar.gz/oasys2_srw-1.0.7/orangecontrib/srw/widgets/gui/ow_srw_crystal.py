import os, numpy

from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QMessageBox, QLabel, QSizePolicy
from AnyQt.QtGui import QPixmap

import orangecanvas.resources as resources

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import MultiInput

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.util.exchange import DataExchangeObject

from syned.beamline.optical_elements.crystals.crystal import Crystal
from wofrysrw.beamline.optical_elements.crystals.srw_crystal import SRWCrystal

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement

class OWSRWCrystal(OWSRWOpticalElement):

    class Inputs:
        srw_data      = OWSRWOpticalElement.Inputs.srw_data
        trigger       = OWSRWOpticalElement.Inputs.trigger
        exchange_data = MultiInput("Exchange Data", DataExchangeObject, default=True, auto_summary=False)
        syned_data    = OWSRWOpticalElement.Inputs.syned_data

    d_spacing       = Setting(3.1355)
    asymmetry_angle = Setting(0.0)
    thickness       = Setting(0.001)
    psi_0r          = Setting(-1.5127e-05)
    psi_0i          = Setting(3.4955e-07)
    psi_hr          = Setting(7.9955e-06)
    psi_hi          = Setting(2.4361e-07)
    psi_hbr         = Setting(7.0304e-06)
    psi_hbi         = Setting(2.1315e-07)
    diffraction_geometry = Setting(0)

    notes = Setting("")

    usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "crystal_usage.png")

    def __init__(self):
        super().__init__(azimuth_hor_vert=True)

    def draw_specific_box(self):
        self.crystal_box = oasysgui.widgetBox(self.tab_bas, "Crystal Setting", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.crystal_box, self, "d_spacing", "d-spacing [Å]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.crystal_box, self, "asymmetry_angle", "Asymmetry Angle [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.crystal_box, self, "thickness", "Crystal Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")

        polarization_box = oasysgui.widgetBox(self.crystal_box, "Crystal Polarizability", addSpace=False, orientation="horizontal")

        polarization_box_l = oasysgui.widgetBox(polarization_box, "", addSpace=False, orientation="vertical", width=200)
        polarization_box_r = oasysgui.widgetBox(polarization_box, "", addSpace=False, orientation="vartical")

        gui.label(polarization_box_l, self, "               Real Part")
        oasysgui.lineEdit(polarization_box_l, self, "psi_0r" , "X0", labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(polarization_box_l, self, "psi_hr" , "Xh \u03c3", labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(polarization_box_l, self, "psi_hbr", "Xh \u03c0", labelWidth=50, valueType=float, orientation="horizontal")

        gui.label(polarization_box_r, self, "Imaginary Part")
        oasysgui.lineEdit(polarization_box_r, self, "psi_0i",  "", labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(polarization_box_r, self, "psi_hi",  "", labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(polarization_box_r, self, "psi_hbi", "", labelWidth=50, valueType=float, orientation="horizontal")

        self.notes_area = oasysgui.textArea(height=40, width=370)
        self.notes_area.setText(self.notes)

        self.crystal_box.layout().addWidget(self.notes_area)

        tab_usa = oasysgui.createTabPage(self.tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

    def get_optical_element(self):
        return SRWCrystal(orientation_of_reflection_plane = self.orientation_azimuthal,
                          invert_tangent_component        = self.invert_tangent_component == 1,
                          d_spacing                       = self.d_spacing,
                          asymmetry_angle                 = self.asymmetry_angle,
                          thickness                       = self.thickness,
                          psi_0r                          = self.psi_0r,
                          psi_0i                          = self.psi_0i,
                          psi_hr                          = self.psi_hr,
                          psi_hi                          = self.psi_hi,
                          psi_hbr                         = self.psi_hbr,
                          psi_hbi                         = self.psi_hbi,
                          incident_angle                  = numpy.radians(90-self.angle_radial))

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if isinstance(optical_element, Crystal):
                self.asymmetry_angle      = optical_element._asymmetry_angle,
                self.thickness            = optical_element._thickness,
                self.diffraction_geometry = optical_element._diffraction_geometry

                self.receive_shape_specific_syned_data(optical_element)
            else:
                raise Exception("Syned Data not correct: Optical Element is not a Crystal")
        else:
            raise Exception("Syned Data not correct: Empty Optical Element")

    def receive_shape_specific_syned_data(self, optical_element): raise NotImplementedError

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.d_spacing, "d-spacing")

    @Inputs.exchange_data
    def set_exchange_data(self, index, exchange_data):
        self.acceptExchangeData(exchange_data)

    @Inputs.exchange_data.insert
    def insert_exchange_data(self, index, exchange_data):
        self.acceptExchangeData(exchange_data)

    @Inputs.exchange_data.remove
    def remove_exchange_data(self, index):
        pass

    def acceptExchangeData(self, exchangeData):
        if not exchangeData is None:
            try:
                if exchangeData.get_program_name() == "XRAYSERVER":
                    if exchangeData.get_widget_name() == "X0H":
                        self.notes = "Data from X-Ray Server: " + exchangeData.get_content("structure") + "(" + \
                                     str(exchangeData.get_content("h")) + "," + str(exchangeData.get_content("k")) + "," + str(exchangeData.get_content("l")) + ")" +  \
                                     " at " + str(round(exchangeData.get_content("energy")*1000, 4)) + " eV"
                        self.notes_area.setText(self.notes)

                        self.angle_radial = 90 - exchangeData.get_content("bragg_angle")
                        self.d_spacing = exchangeData.get_content("d_spacing")
                        self.psi_0r    = exchangeData.get_content("xr0")
                        self.psi_0i    = exchangeData.get_content("xi0")
                        self.psi_hr    = exchangeData.get_content("xrh_s")
                        self.psi_hi    = exchangeData.get_content("xih_s")
                        self.psi_hbr   = exchangeData.get_content("xrh_p")
                        self.psi_hbi   = exchangeData.get_content("xih_p")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

