# Season - Reports
def stats_graph(self):
    fig = plt.figure(
        constrained_layout = True,
    )

    ax = plt.axes(
    
    )
    ax2 = ax.twinx(
    
    )
    self._hd2.ax = ax
    self._hd2.ax2 = ax2
    # Primary
    ax.plot_date(
        [entry.entrytime for entry in self.entry],
        [entry.wind for entry in self.entry],
        "-",
        color = "blue",
    )
    ax.xaxis.set_major_locator(_dates.DayLocator())
    ax.tick_params("x", labelrotation=90)
    ax.yaxis.set_major_locator(
        _ticker.MaxNLocator(
            nbins = 11,
            steps = [5,10],
            integer = True,
            min_n_ticks = 5
        )
    )
    # Secondary
    for attr, hue in [("TS", "green"), ("TS50", "lime"), ("HU", "red")]:
        ax2.plot_date(
            [entry.entrytime for entry in self.entry],
            [
                statistics.mean(
                    filter(
                        lambda ext: ext is not None,
                        getattr(entry, "extent_" + attr)
                    )
                ) if len(list(filter(lambda ext: ext is not None, getattr(entry, "extent_" + attr)))) > 1 else 0 for entry in self.entry
            ],
            "-",
            color = hue,
        )
    # ax2.yaxis.set_major_locator(
        # _ticker.MaxNLocator(
            # nbins = 11,
            # steps = [5,10],
            # integer = True,
            # min_n_ticks = 5
        # )
    # )
    # 917.5 
    # Make graph even
    ax.set_ylim(
        math.floor(ax.get_ylim()[0]) - math.floor(ax.get_ylim()[0]) % 10,
        math.ceil(ax.get_ylim()[1]) + math.ceil(ax.get_ylim()[1]) % 10
    )
    # ax2.set_ylim(bottom=math.floor(ax2.get_ylim()[0]) - math.floor(ax2.get_ylim()[0]) % 10)
    ax2.set_ylim(
        math.floor(ax2.get_ylim()[0]) - math.floor(ax2.get_ylim()[0]) % 10,
        math.ceil(ax2.get_ylim()[1]) + math.ceil(ax2.get_ylim()[1]) % 10
    )
    while operator.sub(*(list(reversed(ax2.get_ylim())))) % len(ax.get_yticks()) != 0:
        if (ax2.get_ylim()[1]-ax2.get_ylim()[0]) % 10 != 0:
            ax2.set_ylim(bottom=ax2.get_ylim()[0] - 1)
        else:
            ax2.set_ylim(top=ax2.get_ylim()[1] + 1)
    ax2.yaxis.set_major_locator(
        _ticker.LinearLocator(
            len(ax.get_yticks())
        )
    )

    ax.grid(True)
    ax2.grid(True)
    plt.show(block=False)