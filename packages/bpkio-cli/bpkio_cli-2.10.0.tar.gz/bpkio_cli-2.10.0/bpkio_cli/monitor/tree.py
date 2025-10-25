from datetime import datetime, timedelta

from bpkio_cli.writers.scte35 import summarize, summarize_xml
from media_muncher.handlers import DASHHandler
from mpd_inspector import MPDInspector
from mpd_inspector.inspector import (
    Scte35BinaryEventInspector,
    Scte35EventInspector,
    Scte35XmlEventInspector,
)
from mpd_inspector.parser.enums import PresentationType
from rich.console import Console
from rich.text import Text
from rich.theme import Theme
from rich.tree import Tree

theme = Theme(
    {
        "id": "yellow",
        "date": "bold magenta",
        "date2": "magenta",
        "dur": "cyan",
        "lang": "green",
        "codec": "cyan",
        "url": "yellow italic",
        "ad-url": "green italic",
        "index": "bold black",
        "count": "bold blue",
        "warning": "red",
    }
)
console = Console(theme=theme, force_terminal=True)


def print_mpd_tree(
    handler: DASHHandler,
    level: int,
    selected_periods: range = None,
    selected_adaptation_set: str = None,
    selected_representation: int = None,
    selected_segments: int = None,
    include_events: bool = True,
    ad_pattern: str = None,
):
    mpdi = MPDInspector(handler.document)

    s_mpd = f"MPD {mpdi.type.value} - "

    # TODO - Add treatment of STATIC
    if mpdi.type == PresentationType.DYNAMIC:
        s_mpd += (
            f"@PT: [date]{fmt_dt(mpdi.publish_time) or '-'}[/date], "
            f"@AST: [date]{fmt_dt(mpdi.availability_start_time) or '-'}[/date]"
        )
    t_mpd = Tree(s_mpd)

    if level >= 1:
        for period in mpdi.select_periods(selected_periods):
            t_period = t_mpd.add(
                f"Period [index]({period.sequence}/{len(mpdi.periods)})[/index]"
                + f" [[id]{period.id}[/id]] from [date]{fmt_dt(period.start_time)}[/date]"
                + f" to [date]{fmt_dt(period.end_time) if period.end_time else '(no-end)'}[/date]"
                + f" = [dur]{period.duration or '(unlimited)'}[/dur]"
            )

            if include_events:
                for event_stream in period.event_streams:
                    t_event_stream = t_period.add(
                        f"EventStream [dim yellow]{event_stream.scheme_id_uri} - [count]{len(event_stream.events)} events[/count]"
                    )
                    if level >= 3:
                        for event in event_stream.events:
                            if isinstance(event, Scte35BinaryEventInspector):
                                descriptor_info = Text.from_markup(
                                    "\n".join(summarize(event.content))
                                )
                            elif isinstance(event, Scte35XmlEventInspector):
                                descriptor_info = Text.from_markup(
                                    "\n".join(summarize_xml(event.content.element))
                                )
                            else:
                                descriptor_info = "[warning]unknown[/warning]"

                            t_event_stream.add(
                                f"Event [[id]{event.id}[/id]] "
                                f"@ [date2]{fmt_dt(event.presentation_time)}[/date2] "
                                f"([date2]δ {fmt_rel_timedelta(event.relative_presentation_time)}[/date2])"
                                + (
                                    f" = [dur]{event.duration}[/dur]"
                                    if event.duration
                                    else ""
                                )
                                + (f"\n{descriptor_info}" if descriptor_info else "")
                            )

            if level >= 2:
                for adapset in period.select_adaptation_sets(selected_adaptation_set):
                    t_adaptationset = t_period.add(
                        f"AdaptationSet [[id]{adapset.id}[/id]] - [type]{adapset.mime_type}[/type] - "
                        f"[lang]{adapset.lang or ''}[/lang]"
                    )

                    if level >= 3:
                        for rep in adapset.select_representations(
                            selected_representation
                        ):
                            t_representation = t_adaptationset.add(
                                f"Representation [[id]{rep.id}[/id]] - [codec]{rep.codecs or '(unspecified)'}[/codec]"
                                + f" - [dim yellow]{rep.segment_information.addressing_mode}"
                                f"/{rep.segment_information.addressing_template}[/dim yellow]"
                            )

                            if level >= 4:
                                # Segment span
                                segments = list(rep.segment_information.segments)
                                first_segment = segments[0]
                                last_segment = segments[-1]
                                first_number = (
                                    f"[count]{first_segment.number}[/count]="
                                    if first_segment.number is not None
                                    else ""
                                )
                                last_number = (
                                    f"[count]{last_segment.number}[/count]="
                                    if last_segment.number is not None
                                    else ""
                                )
                                t_representation.add(
                                    f"Segments: [count]{len(segments)}[/count] "
                                    f"from {first_number}[date2]{fmt_dt(first_segment.start_time)}[/date2] "
                                    f"to {last_number}[date2]{fmt_dt(last_segment.end_time)}[/date2]"
                                )

                                # Segments (summary)
                                if level < 5:
                                    url = rep.segment_information.full_urls("media")[0]
                                    style = "ad-url" if ad_pattern in url else "url"
                                    t_representation.add(
                                        f"Segment URL template: [{style}]{url}[/{style}]"
                                    )

                                # Full list of segments
                                else:
                                    t_seglist = t_representation.add("Segments")
                                    for i, segment in enumerate(segments):
                                        if (
                                            selected_segments is None
                                            or i < selected_segments
                                            or i >= len(segments) - selected_segments
                                        ):
                                            url = segment.urls[0]
                                            style = (
                                                "ad-url" if ad_pattern in url else "url"
                                            )

                                            t_seglist.add(
                                                f"[index]({i + 1})[/index] "
                                                f"[date2]{fmt_dt(segment.start_time)}[/date2]"
                                                f" - [dur]{segment.duration:.5f}[/dur] "
                                                f"(Σ {segment.duration_cumulative:.5f})"
                                                f"\n[{style}]{segment.urls[0]}[/{style}]"
                                            )
                                        else:
                                            if i == selected_segments:
                                                t_seglist.add("...")
    # with console.pager(styles=True):
    console.print(t_mpd)


def fmt_dt(dt: datetime | timedelta):
    if dt is None:
        return "-"

    if isinstance(dt, timedelta):
        return str(dt)

    # formats a datetime to show time only if the date is today
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M:%S.%f")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def fmt_rel_timedelta(td: timedelta) -> str:
    total_seconds = td.total_seconds()
    abs_seconds = abs(total_seconds)

    hours, remainder = divmod(abs_seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds, milliseconds = divmod(remainder, 1)

    sign = "-" if total_seconds < 0 else ""
    return f"{sign}{int(hours):0}:{int(minutes):02}:{int(seconds):02}.{int(milliseconds * 1000):03}"
