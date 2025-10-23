import brainstate

from canns.analyzer.plotting import PlotConfigs, energy_landscape_1d_animation
from canns.models.basic import CANN1D, CANN1D_SFA
from canns.task.tracking import SmoothTracking1D

brainstate.environ.set(dt=0.1)
cann = CANN1D(num=512)
cann.init_state()

task_st = SmoothTracking1D(
    cann_instance=cann,
    Iext=(1., 0.75, 2., 1.75, 3.),
    duration=(10., 10., 10., 10.),
    time_step=brainstate.environ.get_dt(),
)
task_st.get_data()

def run_step(t, inputs):
    cann(inputs)
    return cann.u.value, cann.inp.value

us, inps = brainstate.compile.for_loop(
    run_step,
    task_st.run_steps,
    task_st.data,
    pbar=brainstate.compile.ProgressBar(10)
)

# Using new config-based approach
config = PlotConfigs.energy_landscape_1d_animation(
    time_steps_per_second=100,
    fps=20,
    title='Smooth Tracking 1D',
    xlabel='State',
    ylabel='Activity',
    repeat=True,
    save_path='test_smooth_tracking_1d.gif',
    show=False
)

energy_landscape_1d_animation(
    data_sets={'u': (cann.x, us), 'Iext': (cann.x, inps)},
    config=config
)

# For comparison, the old-style approach still works:
# energy_landscape_1d_animation(
#     {'u': (cann.x, us), 'Iext': (cann.x, inps)},
#     time_steps_per_second=100,
#     fps=20,
#     title='Smooth Tracking 1D (Old Style)',
#     xlabel='State',
#     ylabel='Activity',
#     repeat=True,
#     save_path='test_smooth_tracking_1d_old.gif',
#     show=False,
# )