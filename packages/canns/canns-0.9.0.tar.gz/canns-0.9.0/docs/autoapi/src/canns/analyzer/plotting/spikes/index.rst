src.canns.analyzer.plotting.spikes
==================================

.. py:module:: src.canns.analyzer.plotting.spikes

.. autoapi-nested-parse::

   Spike train visualization helpers.



Functions
---------

.. autoapisummary::

   src.canns.analyzer.plotting.spikes.average_firing_rate_plot
   src.canns.analyzer.plotting.spikes.raster_plot


Module Contents
---------------

.. py:function:: average_firing_rate_plot(spike_train, dt, config = None, *, mode = 'population', weights = None, title = 'Average Firing Rate', figsize = (12, 5), save_path = None, show = True, **kwargs)

   Calculate and plot average neural activity from a spike train.

   :param spike_train: Boolean/integer array of shape ``(timesteps, neurons)``.
   :param dt: Simulation time step in seconds.
   :param config: Optional :class:`PlotConfig` with styling overrides.
   :param mode: One of ``"per_neuron"``, ``"population"`` or
                ``"weighted_average"``.
   :param weights: Neuron-wise weights required for ``"weighted_average"``.
   :param title: Plot title when ``config`` is not provided.
   :param figsize: Figure size forwarded to Matplotlib when creating the axes.
   :param save_path: Optional path used to persist the plot.
   :param show: Whether to display the plot interactively.
   :param \*\*kwargs: Additional keyword arguments forwarded to Matplotlib.


.. py:function:: raster_plot(spike_train, config = None, *, mode = 'block', title = 'Raster Plot', xlabel = 'Time Step', ylabel = 'Neuron Index', figsize = (12, 6), color = 'black', save_path = None, show = True, **kwargs)

   Generate a raster plot from a spike train matrix.

   The explanatory text mirrors the former ``visualize`` module so callers see
   the same guidance after the reorganisation.

   :param spike_train: Boolean/integer array of shape ``(timesteps, neurons)``.
   :param config: Optional :class:`PlotConfig` with shared styling options.
   :param mode: Either ``"scatter"`` or ``"block"`` to pick the rendering style.
   :param title: Plot title when ``config`` is not provided.
   :param xlabel: X-axis label when ``config`` is not provided.
   :param ylabel: Y-axis label when ``config`` is not provided.
   :param figsize: Figure size forwarded to Matplotlib when creating the axes.
   :param color: Spike colour (or "on" colour for block mode).
   :param save_path: Optional path used to persist the plot.
   :param show: Whether to display the plot interactively.
   :param \*\*kwargs: Additional keyword arguments passed through to Matplotlib.


