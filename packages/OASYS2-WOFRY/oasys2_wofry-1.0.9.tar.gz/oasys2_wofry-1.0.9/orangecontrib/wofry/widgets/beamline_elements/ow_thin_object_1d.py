import numpy

from AnyQt.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
from oasys2.widget.util.widget_objects import TriggerOut

from syned.widget.widget_decorator import WidgetDecorator

from orangecontrib.wofry.widgets.gui.ow_optical_element_1d import OWWOOpticalElement1D
from wofryimpl.beamline.optical_elements.refractors.thin_object import WOThinObject1D #TODO from wofryimpl....


class OWWOThinObject1D(OWWOOpticalElement1D):

    name = "ThinObject1D"
    description = "Wofry: Thin Object 1D"
    icon = "icons/thinb1d.png"
    priority = 27

    class Inputs:
        wofry_data           = OWWOOpticalElement1D.Inputs.wofry_data
        dabam_profile        = Input("DABAM 1D Profile", numpy.ndarray, default=True, auto_summary=False)
        trigger              = Input("Trigger", TriggerOut, id="Trigger", default=True, auto_summary=False)
        syned_data           = WidgetDecorator.syned_input_data(multi_input=True)

    material = Setting(1)
    refraction_index_delta = Setting(5.3e-7)
    att_coefficient = Setting(0.00357382)

    aperture_shape = Setting(0)
    aperture_dimension_v = Setting(100e-6)
    aperture_dimension_h = Setting(200e-6)


    write_profile_flag = Setting(0)
    write_profile = Setting("thin_object_profile_2D.h5")

    file_with_thickness_mesh = Setting("<none>")

    def __init__(self):

        super().__init__(is_automatic=True, show_view_options=True, show_script_tab=True)

    def draw_specific_box(self):

        self.thinobject_box = oasysgui.widgetBox(self.tab_bas, "Thin Object 1D Setting", addSpace=False, orientation="vertical",
                                           height=350)

        gui.comboBox(self.thinobject_box, self, "material", label="Lens material",
                     items=self.get_material_name(),callback=self.set_visible,
                     sendSelectedValue=False, orientation="horizontal")

        self.box_refraction_index_id = oasysgui.widgetBox(self.thinobject_box, "", addSpace=False, orientation="vertical")
        tmp = oasysgui.lineEdit(self.box_refraction_index_id, self, "refraction_index_delta", "Refraction index delta",
                          labelWidth=250, valueType=float, orientation="horizontal")
        tmp.setToolTip("refraction_index_delta")

        self.box_att_coefficient_id = oasysgui.widgetBox(self.thinobject_box, "", addSpace=False, orientation="horizontal")
        tmp = oasysgui.lineEdit(self.box_att_coefficient_id, self, "att_coefficient", "Attenuation coefficient [m-1]",
                          labelWidth=250, valueType=float, orientation="horizontal")
        tmp.setToolTip("att_coefficient")



        filein_box = oasysgui.widgetBox(self.thinobject_box, "", addSpace=True,
                                        orientation="horizontal")  # width=550, height=50)
        self.le_beam_file_name = oasysgui.lineEdit(filein_box, self, "file_with_thickness_mesh",
                                                   "File with thickness mesh",
                                                   labelWidth=90, valueType=str, orientation="horizontal")
        gui.button(filein_box, self, "...", callback=self.selectFile)


        self.set_visible()

    def set_visible(self):
        self.box_refraction_index_id.setVisible(self.material in [0])
        self.box_att_coefficient_id.setVisible(self.material in [0])

    def selectFile(self):
        filename = oasysgui.selectFileFromDialog(self,
                previous_file_path=self.file_with_thickness_mesh, message="HDF5 Files (*.hdf5 *.h5 *.hdf)",
                start_directory=".", file_extension_filter="*.*")

        self.le_beam_file_name.setText(filename)

    def get_material_name(self, index=None):
        materials_list = ["External", "Be", "Al", "Diamond"]
        if index is None:
            return materials_list
        else:
            return materials_list[index]

    def get_optical_element(self):
        return WOThinObject1D(name=self.oe_name,
                    file_with_thickness_mesh=self.file_with_thickness_mesh,
                    material=self.get_material_name(self.material),
                    refraction_index_delta=self.refraction_index_delta,
                    att_coefficient=self.att_coefficient)

    def check_data(self):
        super().check_data()
        congruence.checkFileName(self.file_with_thickness_mesh)

    @Inputs.wofry_data
    def set_wofry_data(self, wofry_data):
        super(OWWOThinObject1D, self).set_input(wofry_data)

    @Inputs.syned_data
    def set_syned_data(self, index, syned_data):
        super(OWWOThinObject1D, self).receive_syned_data(syned_data)

    @Inputs.syned_data.insert
    def insert_syned_data(self, index, syned_data):
        super(OWWOThinObject1D, self).receive_syned_data(syned_data)

    @Inputs.syned_data.remove
    def remove_syned_data(self, index):
        pass

    def receive_specific_syned_data(self, optical_element):
        pass

    @Inputs.dabam_profile
    def receive_dabam_profile(self, dabam_profile):
        if not dabam_profile is None:
            try:
                file_name = "dabam_profile_" + str(id(self)) + ".dat"

                file = open(file_name, "w")

                for element in dabam_profile:
                    file.write(str(element[0]) + " " + str(element[1]) + "\n")

                file.flush()
                file.close()

                self.file_with_thickness_mesh = file_name

            except Exception as exception:
                QMessageBox.critical(self, "Error", exception.args[0], QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

    @Inputs.trigger
    def receive_trigger_signal(self, trigger):
        if trigger and trigger.new_object == True:
            if trigger.has_additional_parameter("variable_name"):
                variable_name = trigger.get_additional_parameter("variable_name").strip()
                variable_display_name = trigger.get_additional_parameter("variable_display_name").strip()
                variable_value = trigger.get_additional_parameter("variable_value")
                variable_um = trigger.get_additional_parameter("variable_um")

                if "," in variable_name:
                    variable_names = variable_name.split(",")

                    for variable_name in variable_names:
                        setattr(self, variable_name.strip(), variable_value)
                else:
                    setattr(self, variable_name, variable_value)

                self.propagate_wavefront()

    #
    # overwritten methods to append profile plot
    #

    def get_titles(self):
        titles = super().get_titles()
        titles.append("O.E. Profile")
        return titles

    def do_plot_results(self, progressBarValue=80): # OVERWRITTEN

        super().do_plot_results(progressBarValue)
        if not self.view_type == 0:
            if not self.wavefront_to_plot is None:

                self.progressBarSet(progressBarValue)

                wo_lens = self.get_optical_element()
                abscissas_on_lens, lens_thickness = wo_lens.get_surface_thickness_mesh(self.input_data.get_wavefront())

                self.plot_data1D(x=abscissas_on_lens*1e6, #TODO check how is possible to plot both refractive surfaces
                                 y=lens_thickness*1e6, # in microns
                                 progressBarValue=progressBarValue + 10,
                                 tabs_canvas_index=4,
                                 plot_canvas_index=4,
                                 calculate_fwhm=False,
                                 title=self.get_titles()[4],
                                 xtitle="Spatial Coordinate along o.e. [$\\mu$m]",
                                 ytitle="Total lens thickness [$\\mu$m]")

                self.progressBarFinished()

add_widget_parameters_to_module(__name__)