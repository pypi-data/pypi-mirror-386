import abc

class Quarantine:
    """
    Base class that handles quarantining of data points before they are eligible for processing.

    Parameters
    ----------
    horizon : int
        The number of time steps into the future that predictions should be made for.
    """

    def __init__(self, horizon: int):
        self.horizon = horizon
        self.quarantine = [] # Stores tuples of (release_time, value)

    def add_to_quarantine(self, time, value):
        """ 
        Adds a new value to the quarantine list. 
        The value will become available for prediction processing at `time + self.horizon`.
        """
        self.quarantine.append((time + self.horizon, value))

    def pop_from_quarantine(self, current_time):
        """ Returns the most recent valid data point from quarantine, if available. """
        valid = [(j, (ti, xi)) for (j, (ti, xi)) in enumerate(self.quarantine) if ti <= current_time]
        if valid:
            prev_ndx, (ti, prev_x) = valid[-1]
            self.quarantine = self.quarantine[prev_ndx:]  # Trim the quarantine list
            return prev_x
        return None


class TrackerBase(Quarantine):
    """
    Abstract base class for tracking and predicting the dove's future location.
    Implements quarantine handling and provides methods for running test scenarios.

    Parameters
    ----------
    horizon : int
        The look ahead time for tracker predictions. Trackers try to predict the horizon.
    """

    def __init__(self, horizon: int):
        super().__init__(horizon)
        self.count = 0 # Keeps track of the number of processed dove locations

    @abc.abstractmethod
    def tick(self, payload: dict, performance_metrics: dict):
        """
        Process the payload and update internal state.
        """
        pass

    @abc.abstractmethod
    def predict(self) -> dict:
        """
        Generate a prediction for the dove's future location.
        """
        pass

    def tick_and_predict(self, payload: dict, performance_metrics: dict) -> dict:
        """
        Combines the `tick` and `predict` methods.
        """
        self.tick(payload, performance_metrics)
        return self.predict()

    @staticmethod
    def report_relative_likelihood(log_like, bmark_log_like):
        if not log_like or not bmark_log_like:
            return

        print(
            f"My log-likelihood score: {log_like:.4f} VS Benchmark log-likelihood score: {bmark_log_like:.4f}")
        if log_like > bmark_log_like:
            print(
                f'     .... and mine is better. Ratio is {log_like / bmark_log_like:.5f}')
        else:
            print(
                f'     .... and mine is worse. Ratio is {log_like / bmark_log_like:.5f}'
            )

    def test_run(self, live=True, step_print=1000, max_rows=None):
        """
        Run a test simulation using either live or static remote test data.
        Compare the performance of the current tracker with a benchmark model.
        """
        from birdgame.model_benchmark.emwavartracker import EMWAVarTracker
        from birdgame.trackers.tracker_evaluator import TrackerEvaluator
        from birdgame.datasources.livedata import live_data_generator
        from birdgame.datasources.remotetestdata import remote_test_data_generator
        from tqdm.auto import tqdm
        
        benchmark_tracker = EMWAVarTracker(horizon=self.horizon)
        my_run, bmark_run = TrackerEvaluator(self), TrackerEvaluator(benchmark_tracker)

        gen = live_data_generator(max_rows=max_rows) if live else remote_test_data_generator(max_rows=max_rows)
        try:
            for i, payload in enumerate(tqdm(gen)):

                my_run.tick_and_predict(payload, {})
                bmark_run.tick_and_predict(payload, {})

                if (i + 1) % step_print == 0:
                    TrackerBase.report_relative_likelihood(log_like=my_run.overall_likelihood_score(),
                                                    bmark_log_like=bmark_run.overall_likelihood_score())
            self.report_relative_likelihood(log_like=my_run.overall_likelihood_score(),
                                            bmark_log_like=bmark_run.overall_likelihood_score())


        except KeyboardInterrupt:
            print("Interrupted")

    def test_run_animated(self, live=True, n_data_points=50, recent_score_window_size=100, interval_animation=100, from_notebook=False, max_rows=None):
        """
        Run a test simulation with an animated visualization of predictions.
        """
        from birdgame.model_benchmark.emwavartracker import EMWAVarTracker
        from birdgame.trackers.tracker_evaluator import TrackerEvaluator
        from birdgame.visualization.animated_viz_predictions import animated_predictions_graph
        from birdgame.datasources.livedata import live_data_generator
        from birdgame.datasources.remotetestdata import remote_test_data_generator

        benchmark_tracker = EMWAVarTracker(horizon=self.horizon)
        my_run, bmark_run = TrackerEvaluator(self, recent_score_window_size), TrackerEvaluator(benchmark_tracker, recent_score_window_size)

        gen = live_data_generator(max_rows=max_rows) if live else remote_test_data_generator(max_rows=max_rows)

        use_plt_show = True if not from_notebook else False
        animated = animated_predictions_graph(gen, my_run, bmark_run, n_data_points=n_data_points, 
                                              interval_animation=interval_animation, use_plt_show=use_plt_show)

        return animated
