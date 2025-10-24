import traceback
import warnings
warnings.simplefilter("always")

from syned.storage_ring.electron_beam import ElectronBeam

try:
    a = ElectronBeam.initialize_as_pencil_beam(energy_in_GeV=6.0,
                                               current=0.2,
                                               energy_spread=0.00095,
                                               moment_xx =1.0,
                                               moment_xxp =1.0,
                                               moment_xpxp =1.0,
                                               moment_yy =1.0,
                                               moment_yyp =1.0,
                                               moment_ypyp =1.0,
                                               dispersion_x =1.0,
                                               dispersion_y =1.0,
                                               dispersionp_x=1.0,
                                               dispersionp_y=1.0)
    a.set_twiss_horizontal  (0, 0, 0)
    a.set_twiss_vertical    (0, 1, 1, eta_y=2.0, etap_y=3.0)

    print(a.info())

    print(a.get_twiss_no_dispersion_all())
except:
    traceback.print_exc()
