
from syned.beamline.beamline import Beamline

class WidgetDecorator(object):
    """
    Definition of a widget decorator (to be used by widget implementations).

    """

    @classmethod
    def syned_input_data(cls, multi_input=False):
        """
        A string to help defining SYNED data in OASYS.

        Returns
        -------
        list
            [("SynedData", Beamline, "receive_syned_data")]

        """
        try: # OASYS2
            import oasys2

            if not multi_input:
                from orangewidget.widget import Input

                return Input(name="Syned Data",
                             type=Beamline,
                             id="SynedData",
                             default=True, auto_summary=False)
            else:
                from orangewidget.widget import MultiInput

                return MultiInput(name="Syned Data",
                                  type=Beamline,
                                  id="SynedData",
                                  default=True, auto_summary=False)
        except:
            return [("SynedData", Beamline, "receive_syned_data")]

    @classmethod
    def append_syned_input_data(cls, inputs):
        """

        Parameters
        ----------
        inputs


        """
        for input in WidgetDecorator.syned_input_data():
            inputs.append(input)

    def receive_syned_data(self, data):
        """
        To be implemented in the main object.

        Parameters
        ----------
        data

        Raises
        ------
        NotImplementedError

        """
        raise NotImplementedError("Should be implemented")