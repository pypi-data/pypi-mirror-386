import warnings
from importlib import resources
from math import ceil
from pprint import pformat
from typing import List, Optional, Union

from dominate import tags
from dominate.dom_tag import dom_tag
from markupsafe import Markup

from .asset import CachedAsset, ExternalAsset
from .modular_page import AudioPrompt, ModularPage
from .timeline import (
    CodeBlock,
    Event,
    Module,
    Page,
    PageMaker,
    get_template,
    join,
    while_loop,
)
from .utils import get_logger

logger = get_logger()
warnings.simplefilter("always", DeprecationWarning)


class InfoPage(ModularPage):
    """
    This page displays some content to the user alongside a button
    with which to advance to the next page.

    Parameters
    ----------

    content:
        The content to display to the user. Use :class:`markupsafe.Markup`
        to display raw HTML.

    time_estimate:
        Time estimated for the page.

    **kwargs:
        Further arguments to pass to :class:`psynet.modular_page.ModularPage`.
    """

    def __init__(
        self,
        content: Union[str, Markup, dom_tag],
        time_estimate: Optional[float] = None,
        **kwargs,
    ):
        self.content = content
        super().__init__(
            label="info",
            prompt=content,
            time_estimate=time_estimate,
            save_answer=False,
            **kwargs,
        )

    def get_bot_response(self, experiment, bot):
        from .bot import BotResponse

        return BotResponse(
            answer=None,
            metadata=self.metadata(),
        )


class UnityPage(Page):
    """
    This is the main page when conducting Unity experiments. Its attributes ``contents`` and ``attributes`` can be accessed through the JavaScript variable ``psynet.page`` inside the page template.

    Ín order to conclude this page call the ``psynet.nextPage`` function which has following parameters:

    * ``rawAnswer``: The main answer that the page returns.

    * ``metadata``: Additional information that might be useful for debugging or other exploration, e.g. time taken on the page.

    * ``blobs``: Use this for large binaries, e.g. audio recordings.

    Once the ``psynet.nextPage`` function is called, PsyNet will navigate to a new page if the new page has a different session_id compared to the current page, otherwise it will update the page while preserving the ongoing Unity session, specifically updating ``psynet.page`` and triggering the JavaScript event ``pageUpdated`` in the ``window`` object.

    Parameters
    ----------

    title:
        The title of the experiment to be rendered in the HTML title-tag of the page.

    game_container_width:
        The width of the game container, e.g. '960px'.

    game_container_height:
        The height of the game container, e.g. '600px'.

    resources:
        The path to the directory containing the Unity files residing inside the "static" directory. The path should start with "/static" and should comply with following basic structure:

        static/
        ├── css/
        └── scripts/

        css: Contains stylesheets
        scripts: Contains JavaScript files

    contents:
        A dictionary containing experiment specific data.

    time_estimate:
        Time estimated for the page (seconds).

    session_id:
        If session_id is not None, then it must be a string. If two consecutive pages occur with the same session_id, then when it’s time to move to the second page, the browser will not navigate to a new page, but will instead update the JavaScript variable psynet.page with metadata for the new page, and will trigger an event called pageUpdated. This event can be listened for with JavaScript code like window.addEventListener(”pageUpdated”, ...).

    debug:
        Specifies if we are in debug mode and use `unity-debug-page.html` as template instead of the standard `unity-page.html`.

    **kwargs:
        Further arguments to pass to :class:`psynet.timeline.Page`.
    """

    dynamically_update_progress_bar_and_reward = True

    def __init__(
        self,
        title: str,
        resources: str,
        contents: dict,
        session_id: str,
        game_container_width: str = "960px",
        game_container_height: str = "600px",
        time_estimate: Optional[float] = None,
        debug: bool = False,
        **kwargs,
    ):
        self.title = title
        self.resources = resources
        self.contents = contents
        self.game_container_width = game_container_width
        self.game_container_height = game_container_height
        self.session_id = session_id

        template = "unity-debug-page.html" if debug else "unity-page.html"

        super().__init__(
            contents=self.contents,
            time_estimate=time_estimate,
            template_str=get_template(template),
            template_arg={
                "title": self.title,
                "resources": "" if self.resources is None else self.resources,
                "contents": {} if self.contents is None else self.contents,
                "game_container_width": self.game_container_width,
                "game_container_height": self.game_container_height,
                "session_id": self.session_id,
            },
            session_id=session_id,
            **kwargs,
        )

    def metadata(self, **kwargs):
        return {
            "resources": self.resources,
            "contents": self.contents,
            "session_id": self.session_id,
            "time_taken": None,
        }


class WaitPage(Page):
    """
    This page makes the user wait for a specified amount of time
    before automatically continuing to the next page.

    Parameters
    ----------

    wait_time:
        Time that the user should wait.

    content:
        Message to display to the participant while they wait.
        Default: "Please wait, the experiment should continue shortly..."

    **kwargs:
        Further arguments to pass to :class:`psynet.timeline.Page`.
    """

    content = "Please wait, the experiment should continue shortly..."

    def __init__(self, wait_time: float, content=None, **kwargs):
        assert wait_time >= 0
        self.wait_time = wait_time
        if content is not None:
            self.content = content
        super().__init__(
            label="wait",
            time_estimate=wait_time,
            template_str=get_template("wait-page.html"),
            template_arg={"content": self.content, "wait_time": self.wait_time},
            **kwargs,
        )

    def metadata(self, **kwargs):
        return {"wait_time": self.wait_time}

    def get_bot_response(self, experiment, bot):
        return None

    def on_complete(self, experiment, participant):
        participant.total_wait_page_time += self.wait_time
        super().on_complete(experiment, participant)


def wait_while(
    condition,
    expected_wait: float,
    check_interval: float = 2.0,
    max_wait_time: float = 20.0,
    wait_page=WaitPage,
    log_message: Optional[str] = None,
    fail_on_timeout=True,
):
    """
    Displays the participant a waiting page while a given condition
    remains satisfied.

    Parameters
    ----------

    condition
        The condition to be checked;
        the participant will keep waiting while this condition returns True.
        This argument should be a function receiving the following arguments:
        ``participant`` (corresponding to the current participant)
        and ``experiment`` (corresponding to the current experiments).
        If one of this arguments is not needed, it can be omitted from the
        argument list.

    expected_wait
        How long the participant is likely to wait, in seconds.

    check_interval
        How often should the browser check the condition, in seconds.

    max_wait_time
        The participant's maximum waiting time in seconds. Default: 20.0.

    wait_page
        The wait page that should be displayed to the participant;
        defaults to :class:`~psynet.page.WaitPage`.

    log_message
        Optional message to display in the log.

    fail_on_timeout
        Whether the participants should be failed when the ``max_loop_time`` is reached.
        Setting this to ``False`` will not return the ``UnsuccessfulEndPage`` when maximum time has elapsed
        but allow them to proceed to the next page.

    Returns
    -------

    list :
        A list of test elts suitable for inclusion in a PsyNet timeline.
    """
    assert expected_wait >= 0
    assert check_interval > 0
    expected_repetitions = ceil(expected_wait / check_interval)

    _wait_page = wait_page(wait_time=check_interval)

    def log(participant):
        logger.info(f"Participant {participant.id}: {log_message}")

    if log_message is None:
        logic = _wait_page
    else:
        logic = join(CodeBlock(log), _wait_page)

    label = "wait_while"

    return join(
        while_loop(
            label,
            condition,
            logic=logic,
            expected_repetitions=expected_repetitions,
            max_loop_time=max_wait_time,
            fail_on_timeout=fail_on_timeout,
        ),
    )


# At some point we might make deprecation warnings for these classes
class SuccessfulEndPage(PageMaker):
    def __init__(self):
        super().__init__(
            lambda experiment: experiment.SuccessfulEndLogic(), time_estimate=0.0
        )


class UnsuccessfulEndPage(PageMaker):
    def __init__(self, failure_tags: Optional[List] = None, **kwargs):
        super().__init__(
            lambda experiment: experiment.UnsuccessfulEndLogic(
                failure_tags=failure_tags, **kwargs
            ),
            time_estimate=0.0,
        )


class RejectedConsentPage(PageMaker):
    def __init__(self, failure_tags: Optional[List] = None, **kwargs):
        super().__init__(
            lambda experiment: experiment.RejectedConsentLogic(
                failure_tags=failure_tags, **kwargs
            ),
            time_estimate=0.0,
        )


class DebugResponsePage(PageMaker):
    """
    Implements a debugging page for responses.
    Displays a page to the user with information about the
    last response received from the participant.
    """

    def __init__(self):
        super().__init__(self.summarize_last_response, time_estimate=0)

    @staticmethod
    def summarize_last_response(participant):
        response = participant.response
        if response is None:
            return InfoPage("No response found to display.")
        page_type = response.page_type
        answer = pformat(response.answer, indent=4)
        metadata = pformat(response.metadata, indent=4)

        html = tags.span()
        with html:
            tags.h3("Page type")
            tags.p(page_type)
            tags.p(cls="vspace")
            tags.h3("Answer")
            tags.pre(answer, style="background-color: #f0f0f0; padding: 10px;")
            tags.p(cls="vspace")
            tags.h3("Metadata")
            tags.pre(
                tags.html(metadata),
                style="max-height: 400px; overflow: scroll; background-color: #f0f0f0; padding: 10px;",
            )

        return InfoPage(html)


class VolumeCalibration(Module):
    def __init__(
        self,
        url=str(resources.files("psynet") / "resources/audio/brown_noise.wav"),
        min_time=2.5,
        time_estimate=5.0,
        id_="volume_calibration",
    ):
        super().__init__(
            id_,
            self.page(min_time, time_estimate, id_),
            assets={
                "volume_calibration_audio": self.asset(url),
            },
        )

    def asset(self, url):
        if str(url).startswith("http"):
            return ExternalAsset(url=url)
        else:
            return CachedAsset(input_path=url)

    def page(self, min_time, time_estimate, id_):
        return PageMaker(
            lambda assets: ModularPage(
                id_,
                AudioPrompt(assets["volume_calibration_audio"], self.text(), loop=True),
                events={
                    "submitEnable": Event(is_triggered_by="trialStart", delay=min_time)
                },
            ),
            time_estimate=time_estimate,
        )

    def text(self):
        return Markup(
            """
            <p>
                Please listen to the following sound and adjust your
                computer's output volume until it is at a comfortable level.
            </p>
            <p>
                If you can't hear anything, there may be a problem with your
                playback configuration or your internet connection.
                You can refresh the page to try loading the audio again.
            </p>
            """
        )


class JsPsychPage(Page):
    """
    A page that embeds a jsPsych experiment. See ``demos/jspsych`` for example usage.

    label :
        Label for the page.

    timeline :
        A path to an HTML file that defines the jsPsych experiment's timeline.
        The timeline should be saved as an object called ``timeline``.
        See ``demos/jspsych`` for an example.

    js_links :
        A list of links to JavaScript files to include in the page. Typically this would include
        a link to the required jsPsych version as well as links to the required plug-ins.
        It is recommended to include these files in the ``static`` directory and refer to them
        using relative paths; alternatively it is possible to link to these files via a CDN.

    css_links :
        A list of links to CSS stylesheets to include. Typically this would include the standard
        jsPsych stylesheet.

    js_vars :
        An optional dictionary of variables to pass to the front-end. These can then be accessed
        in the timeline template, writing for example ``psynet.var["my_variable"]``.
    """

    def __init__(
        self,
        label: str,
        timeline: str,
        time_estimate: float,
        js_links: Union[str, List[str]],
        css_links: Union[str, List[str]],
        js_vars: Optional[dict] = None,
        **kwargs,
    ):
        if isinstance(js_links, str):
            js_links = [js_links]
        if isinstance(css_links, str):
            css_links = [css_links]

        super().__init__(
            time_estimate=time_estimate,
            template_path=timeline,
            label=label,
            js_vars=js_vars,
            js_links=js_links,
            css_links=css_links,
            **kwargs,
        )


class ExecuteFrontEndJS(InfoPage):
    def __init__(self, js: str, message: str = ""):
        super().__init__(
            content=message,
            time_estimate=0.0,
            scripts=[js],
            show_next_button=False,
        )
