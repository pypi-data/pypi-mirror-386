from typing import Any, Protocol, Unpack

from pulse.html.elements import GenericHTMLElement
from pulse.html.props import (
	HTMLAnchorProps,
	HTMLAreaProps,
	HTMLAudioProps,
	HTMLBaseProps,
	HTMLBlockquoteProps,
	HTMLButtonProps,
	HTMLCanvasProps,
	HTMLColgroupProps,
	HTMLColProps,
	HTMLDataProps,
	HTMLDelProps,
	HTMLDetailsProps,
	HTMLDialogProps,
	HTMLEmbedProps,
	HTMLFieldsetProps,
	HTMLFormProps,
	HTMLHtmlProps,
	HTMLIframeProps,
	HTMLImgProps,
	HTMLInputProps,
	HTMLInsProps,
	HTMLLabelProps,
	HTMLLinkProps,
	HTMLLiProps,
	HTMLMapProps,
	HTMLMenuProps,
	HTMLMetaProps,
	HTMLMeterProps,
	HTMLObjectProps,
	HTMLOlProps,
	HTMLOptgroupProps,
	HTMLOptionProps,
	HTMLOutputProps,
	HTMLParamProps,
	HTMLProgressProps,
	HTMLProps,
	HTMLQuoteProps,
	HTMLScriptProps,
	HTMLSelectProps,
	HTMLSourceProps,
	HTMLStyleProps,
	HTMLSVGProps,
	HTMLTableProps,
	HTMLTdProps,
	HTMLTextareaProps,
	HTMLThProps,
	HTMLTimeProps,
	HTMLTrackProps,
	HTMLVideoProps,
)
from pulse.vdom import Child, Node

class Tag(Protocol):
	def __call__(self, *children: Child, **props: Any) -> Node: ...

def define_tag(
	name: str,
	default_props: dict[str, Any] | None = None,
) -> Tag: ...
def define_self_closing_tag(
	name: str,
	default_props: dict[str, Any] | None = None,
) -> Tag: ...

# --- Self-closing tags ----
def area(*, key: str | None = None, **props: Unpack[HTMLAreaProps]) -> Node: ...
def base(*, key: str | None = None, **props: Unpack[HTMLBaseProps]) -> Node: ...
def br(*, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def col(*, key: str | None = None, **props: Unpack[HTMLColProps]) -> Node: ...
def embed(*, key: str | None = None, **props: Unpack[HTMLEmbedProps]) -> Node: ...
def hr(*, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def img(*, key: str | None = None, **props: Unpack[HTMLImgProps]) -> Node: ...
def input(*, key: str | None = None, **props: Unpack[HTMLInputProps]) -> Node: ...
def link(*, key: str | None = None, **props: Unpack[HTMLLinkProps]) -> Node: ...
def meta(*, key: str | None = None, **props: Unpack[HTMLMetaProps]) -> Node: ...
def param(*, key: str | None = None, **props: Unpack[HTMLParamProps]) -> Node: ...
def source(*, key: str | None = None, **props: Unpack[HTMLSourceProps]) -> Node: ...
def track(*, key: str | None = None, **props: Unpack[HTMLTrackProps]) -> Node: ...
def wbr(*, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...

# --- Regular tags ---

def a(
	*children: Child, key: str | None = None, **props: Unpack[HTMLAnchorProps]
) -> Node: ...
def abbr(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def address(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def article(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def aside(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def audio(
	*children: Child, key: str | None = None, **props: Unpack[HTMLAudioProps]
) -> Node: ...
def b(*children: Child, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def bdi(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def bdo(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def blockquote(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLBlockquoteProps],
) -> Node: ...
def body(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def button(
	*children: Child, key: str | None = None, **props: Unpack[HTMLButtonProps]
) -> Node: ...
def canvas(
	*children: Child, key: str | None = None, **props: Unpack[HTMLCanvasProps]
) -> Node: ...
def caption(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def cite(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def code(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def colgroup(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLColgroupProps],
) -> Node: ...
def data(
	*children: Child, key: str | None = None, **props: Unpack[HTMLDataProps]
) -> Node: ...
def datalist(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def dd(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def del_(
	*children: Child, key: str | None = None, **props: Unpack[HTMLDelProps]
) -> Node: ...
def details(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLDetailsProps],
) -> Node: ...
def dfn(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def dialog(
	*children: Child, key: str | None = None, **props: Unpack[HTMLDialogProps]
) -> Node: ...
def div(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def dl(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def dt(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def em(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def fieldset(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLFieldsetProps],
) -> Node: ...
def figcaption(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def figure(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def footer(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def form(
	*children: Child, key: str | None = None, **props: Unpack[HTMLFormProps]
) -> Node: ...
def h1(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def h2(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def h3(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def h4(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def h5(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def h6(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def head(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def header(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def hgroup(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def html(
	*children: Child, key: str | None = None, **props: Unpack[HTMLHtmlProps]
) -> Node: ...
def i(*children: Child, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def iframe(
	*children: Child, key: str | None = None, **props: Unpack[HTMLIframeProps]
) -> Node: ...
def ins(
	*children: Child, key: str | None = None, **props: Unpack[HTMLInsProps]
) -> Node: ...
def kbd(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def label(
	*children: Child, key: str | None = None, **props: Unpack[HTMLLabelProps]
) -> Node: ...
def legend(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def li(
	*children: Child, key: str | None = None, **props: Unpack[HTMLLiProps]
) -> Node: ...
def main(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def map_(
	*children: Child, key: str | None = None, **props: Unpack[HTMLMapProps]
) -> Node: ...
def mark(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def menu(
	*children: Child, key: str | None = None, **props: Unpack[HTMLMenuProps]
) -> Node: ...
def meter(
	*children: Child, key: str | None = None, **props: Unpack[HTMLMeterProps]
) -> Node: ...
def nav(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def noscript(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def object_(
	*children: Child, key: str | None = None, **props: Unpack[HTMLObjectProps]
) -> Node: ...
def ol(
	*children: Child, key: str | None = None, **props: Unpack[HTMLOlProps]
) -> Node: ...
def optgroup(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLOptgroupProps],
) -> Node: ...
def option(
	*children: Child, key: str | None = None, **props: Unpack[HTMLOptionProps]
) -> Node: ...
def output(
	*children: Child, key: str | None = None, **props: Unpack[HTMLOutputProps]
) -> Node: ...
def p(*children: Child, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def picture(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def pre(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def progress(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLProgressProps],
) -> Node: ...
def q(
	*children: Child, key: str | None = None, **props: Unpack[HTMLQuoteProps]
) -> Node: ...
def rp(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def rt(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def ruby(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def s(*children: Child, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def samp(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def script(
	*children: Child, key: str | None = None, **props: Unpack[HTMLScriptProps]
) -> Node: ...
def section(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def select(
	*children: Child, key: str | None = None, **props: Unpack[HTMLSelectProps]
) -> Node: ...
def small(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def span(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def strong(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def style(
	*children: Child, key: str | None = None, **props: Unpack[HTMLStyleProps]
) -> Node: ...
def sub(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def summary(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def sup(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def table(
	*children: Child, key: str | None = None, **props: Unpack[HTMLTableProps]
) -> Node: ...
def tbody(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def td(
	*children: Child, key: str | None = None, **props: Unpack[HTMLTdProps]
) -> Node: ...
def template(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def textarea(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLTextareaProps],
) -> Node: ...
def tfoot(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def th(
	*children: Child, key: str | None = None, **props: Unpack[HTMLThProps]
) -> Node: ...
def thead(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def time(
	*children: Child, key: str | None = None, **props: Unpack[HTMLTimeProps]
) -> Node: ...
def title(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def tr(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def u(*children: Child, key: str | None = None, **props: Unpack[HTMLProps]) -> Node: ...
def ul(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def var(
	*children: Child, key: str | None = None, **props: Unpack[HTMLProps]
) -> Node: ...
def video(
	*children: Child, key: str | None = None, **props: Unpack[HTMLVideoProps]
) -> Node: ...

# -- React Fragment ---
def fragment(*children: Child, key: str | None = None) -> Node: ...

# -- SVG --
def svg(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def circle(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def ellipse(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def g(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def line(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def path(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def polygon(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def polyline(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def rect(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def text(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def tspan(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def defs(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def clipPath(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def mask(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def pattern(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
def use(
	*children: Child,
	key: str | None = None,
	**props: Unpack[HTMLSVGProps[GenericHTMLElement]],
) -> Node: ...
