import sys

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output
from oasys2.widget.widget import OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util.widget_util import EmittingStream
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D
from wofry.propagator.wavefront1D.generic_wavefront import GenericWavefront1D

from orangecontrib.wofry.util.wofry_objects import WofryData
from orangecontrib.wofry.widgets.gui.ow_wofry_widget import WofryWidget


class OW2Dto1D(WofryWidget):

    name = "Wavefronts 1D to 2D"
    id = "Wavefronts1Dto2D"
    description = "Wavefronts 1D to 2D"
    icon = "icons/1d_to_2d.png"
    priority = 3

    category = "Wofry Tools"
    keywords = ["data", "file", "load", "read"]


    class Inputs:
        wofry_data_h           = Input("Horizontal Data", WofryData, default=True, auto_summary=False)
        wofry_data_v           = Input("Vertical Data", WofryData, default=True, auto_summary=False)
        generic_wavefront_1D_h = Input("Horizontal Wavefront 1D", GenericWavefront1D, default=True, auto_summary=False)
        generic_wavefront_1D_v = Input("Vertical Wavefront 1D", GenericWavefront1D, default=True, auto_summary=False)

    class Outputs:
        wofry_data           = Output("Wofry Data", WofryData, id="WofryData", default=True, auto_summary=False)
        generic_wavefront_2D = Output("Generic Wavefront 2D", GenericWavefront2D, default=True, auto_summary=False)

    normalize_to = Setting(0)

    wavefront2D = None

    wavefront1D_h = None
    wavefront1D_v = None

    def __init__(self):
        super().__init__(is_automatic=True, show_script_tab=False)

        self.runaction = OWAction("Send Data", self)
        self.runaction.triggered.connect(self.send_data)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Send Data", callback=self.send_data)
        button.setStyleSheet("color: darkblue; font-weight: bold; height: 45px;")

        gui.separator(self.controlArea)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_sou = oasysgui.createTabPage(tabs_setting, "Wavefronts Combination Setting")

        gui.comboBox(self.tab_sou, self, "normalize_to", label="Normalize to", labelWidth=220,
                     items=["Horizontal", "Vertical", "One", "No normalization"],
                     sendSelectedValue=False, orientation="horizontal")

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = ["Wavefront 1D (H)", "Wavefront 1D (V)", "Wavefront 2D"]
        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    @Inputs.wofry_data_h
    def set_wofry_data_h(self, wofry_data):
        self.set_input_h(wofry_data)

    @Inputs.generic_wavefront_1D_h
    def set_generic_wavefront_1D_h(self, generic_wavefront_1D):
        self.set_input_h(generic_wavefront_1D)

    @Inputs.wofry_data_v
    def set_wofry_data_v(self, wofry_data):
        self.set_input_v(wofry_data)

    @Inputs.generic_wavefront_1D_v
    def set_generic_wavefront_1D_v(self, generic_wavefront_1D):
        self.set_input_v(generic_wavefront_1D)

    def set_input_h(self, wofry_data):
        if not wofry_data is None:
            if isinstance(wofry_data, WofryData): self.wavefront1D_h = wofry_data.get_wavefront()
            else: self.wavefront1D_h = wofry_data

            if self.is_automatic_execution:
                self.send_data()

    def set_input_v(self, wofry_data):
        if not wofry_data is None:
            if isinstance(wofry_data, WofryData): self.wavefront1D_v = wofry_data.get_wavefront()
            else: self.wavefront1D_v = wofry_data

            if self.is_automatic_execution:
                self.send_data()

    def send_data(self):
        if not self.wavefront1D_h is None and not self.wavefront1D_v is None:
            self.progressBarInit()

            self.wofry_output.setText("")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.wavefront2D = GenericWavefront2D.combine_1D_wavefronts_into_2D(self.wavefront1D_h,
                                                                                self.wavefront1D_v,
                                                                                normalize_to=self.normalize_to)

            self.plot_results(progressBarValue=50)

            print("input H wavefront intensity: %g " % self.wavefront1D_h.get_integrated_intensity())
            print("input V wavefront intensity: %g " % self.wavefront1D_v.get_integrated_intensity())
            print("output V wavefront intensity: %g " % self.wavefront2D.get_integrated_intensity())

            self.progressBarFinished()

            self.Outputs.wofry_data.send(WofryData(wavefront=self.wavefront2D))
            self.Outputs.generic_wavefront_2D.send(self.wavefront2D)

    def do_plot_results(self, progressBarValue):
        if not self.wavefront2D is None and not self.wavefront1D_h is None and not self.wavefront1D_v is None:

            self.progressBarSet(progressBarValue)

            titles = ["Wavefront 1D (H) Intensity", "Wavefront 1D (V) Intensity", "Wavefront 2D Intensity"]

            self.plot_data1D(x=1e6 * self.wavefront1D_h.get_abscissas(),
                             y=self.wavefront1D_h.get_intensity(),
                             progressBarValue=progressBarValue + 12,
                             tabs_canvas_index=0,
                             plot_canvas_index=0,
                             title=titles[0],
                             xtitle="Horizontal Coordinate [$\\mu$m]",
                             ytitle="Intensity")

            self.plot_data1D(x=1e6 * self.wavefront1D_v.get_abscissas(),
                             y=self.wavefront1D_v.get_intensity(),
                             progressBarValue=progressBarValue + 12,
                             tabs_canvas_index=1,
                             plot_canvas_index=1,
                             title=titles[1],
                             xtitle="Vertical Coordinate [$\\mu$m]",
                             ytitle="Intensity")

            self.plot_data2D(data2D=self.wavefront2D.get_intensity(),
                             dataX=1e6 * self.wavefront2D.get_coordinate_x(),
                             dataY=1e6 * self.wavefront2D.get_coordinate_y(),
                             progressBarValue=progressBarValue + 26,
                             tabs_canvas_index=2,
                             plot_canvas_index=2,
                             title=titles[2],
                             xtitle="Horizontal Coordinate [$\\mu$m]",
                             ytitle="Vertical Coordinate [$\\mu$m]")

add_widget_parameters_to_module(__name__)



