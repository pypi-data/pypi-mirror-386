import itertools
from xml.etree import ElementTree
import weakref, numpy as np, copy, textwrap, inspect

__all__ = [
    "HTML",
    "CSS",
    "ContentXML"
]

from ...Misc import mixedmethod
from .Enums import Options
from .WidgetTools import frozendict

class CSS:
    """
    Defines a holder for CSS properties
    """
    def __init__(self, *selectors, **props):
        self.selectors = selectors
        self.props = self.canonicalize_props(props)
    known_properties = set(o.value for o in Options)
    @classmethod
    def construct(cls,
                  *selectors,
                  background=None,
                  background_attachment=None,
                  background_color=None,
                  background_image=None,
                  background_position=None,
                  background_repeat=None,
                  border=None,
                  border_bottom=None,
                  border_bottom_color=None,
                  border_bottom_style=None,
                  border_bottom_width=None,
                  border_color=None,
                  border_left=None,
                  border_left_color=None,
                  border_left_style=None,
                  border_left_width=None,
                  border_right=None,
                  border_right_color=None,
                  border_right_style=None,
                  border_right_width=None,
                  border_style=None,
                  border_top=None,
                  border_top_color=None,
                  border_top_style=None,
                  border_top_width=None,
                  border_width=None,
                  clear=None,
                  clip=None,
                  color=None,
                  cursor=None,
                  display=None,
                  filter=None,
                  float=None,
                  font=None,
                  font_family=None,
                  font_size=None,
                  font_variant=None,
                  font_weight=None,
                  height=None,
                  left=None,
                  letter_spacing=None,
                  line_height=None,
                  list_style=None,
                  list_style_image=None,
                  list_style_position=None,
                  list_style_type=None,
                  margin=None,
                  margin_bottom=None,
                  margin_left=None,
                  margin_right=None,
                  margin_top=None,
                  overflow=None,
                  padding=None,
                  padding_bottom=None,
                  padding_left=None,
                  padding_right=None,
                  padding_top=None,
                  page_break_after=None,
                  page_break_before=None,
                  position=None,
                  text_align=None,
                  text_decoration=None,
                  text_indent=None,
                  text_transform=None,
                  top=None,
                  vertical_align=None,
                  visibility=None,
                  width=None,
                  z_index=None,
                  **props
                  ):
        """
        Provides a convenience constructor for systems with autocompletions

        :param selectors:
        :type selectors:
        :param background:
        :type background:
        :param background_attachment:
        :type background_attachment:
        :param background_color:
        :type background_color:
        :param background_image:
        :type background_image:
        :param background_position:
        :type background_position:
        :param background_repeat:
        :type background_repeat:
        :param border:
        :type border:
        :param border_bottom:
        :type border_bottom:
        :param border_bottom_color:
        :type border_bottom_color:
        :param border_bottom_style:
        :type border_bottom_style:
        :param border_bottom_width:
        :type border_bottom_width:
        :param border_color:
        :type border_color:
        :param border_left:
        :type border_left:
        :param border_left_color:
        :type border_left_color:
        :param border_left_style:
        :type border_left_style:
        :param border_left_width:
        :type border_left_width:
        :param border_right:
        :type border_right:
        :param border_right_color:
        :type border_right_color:
        :param border_right_style:
        :type border_right_style:
        :param border_right_width:
        :type border_right_width:
        :param border_style:
        :type border_style:
        :param border_top:
        :type border_top:
        :param border_top_color:
        :type border_top_color:
        :param border_top_style:
        :type border_top_style:
        :param border_top_width:
        :type border_top_width:
        :param border_width:
        :type border_width:
        :param clear:
        :type clear:
        :param clip:
        :type clip:
        :param color:
        :type color:
        :param cursor:
        :type cursor:
        :param display:
        :type display:
        :param filter:
        :type filter:
        :param float:
        :type float:
        :param font:
        :type font:
        :param font_family:
        :type font_family:
        :param font_size:
        :type font_size:
        :param font_variant:
        :type font_variant:
        :param font_weight:
        :type font_weight:
        :param height:
        :type height:
        :param left:
        :type left:
        :param letter_spacing:
        :type letter_spacing:
        :param line_height:
        :type line_height:
        :param list_style:
        :type list_style:
        :param list_style_image:
        :type list_style_image:
        :param list_style_position:
        :type list_style_position:
        :param list_style_type:
        :type list_style_type:
        :param margin:
        :type margin:
        :param margin_bottom:
        :type margin_bottom:
        :param margin_left:
        :type margin_left:
        :param margin_right:
        :type margin_right:
        :param margin_top:
        :type margin_top:
        :param overflow:
        :type overflow:
        :param padding:
        :type padding:
        :param padding_bottom:
        :type padding_bottom:
        :param padding_left:
        :type padding_left:
        :param padding_right:
        :type padding_right:
        :param padding_top:
        :type padding_top:
        :param page_break_after:
        :type page_break_after:
        :param page_break_before:
        :type page_break_before:
        :param position:
        :type position:
        :param text_align:
        :type text_align:
        :param text_decoration:
        :type text_decoration:
        :param text_indent:
        :type text_indent:
        :param text_transform:
        :type text_transform:
        :param top:
        :type top:
        :param vertical_align:
        :type vertical_align:
        :param visibility:
        :type visibility:
        :param width:
        :type width:
        :param z_index:
        :type z_index:
        :param props:
        :type props:
        :return:
        :rtype:
        """
        common_props = dict(
            background=background,
            background_attachment=background_attachment,
            background_color=background_color,
            background_image=background_image,
            background_position=background_position,
            background_repeat=background_repeat,
            border=border,
            border_bottom=border_bottom,
            border_bottom_color=border_bottom_color,
            border_bottom_style=border_bottom_style,
            border_bottom_width=border_bottom_width,
            border_color=border_color,
            border_left=border_left,
            border_left_color=border_left_color,
            border_left_style=border_left_style,
            border_left_width=border_left_width,
            border_right=border_right,
            border_right_color=border_right_color,
            border_right_style=border_right_style,
            border_right_width=border_right_width,
            border_style=border_style,
            border_top=border_top,
            border_top_color=border_top_color,
            border_top_style=border_top_style,
            border_top_width=border_top_width,
            border_width=border_width,
            clear=clear,
            clip=clip,
            color=color,
            cursor=cursor,
            display=display,
            filter=filter,
            float=float,
            font=font,
            font_family=font_family,
            font_size=font_size,
            font_variant=font_variant,
            font_weight=font_weight,
            height=height,
            left=left,
            letter_spacing=letter_spacing,
            line_height=line_height,
            list_style=list_style,
            list_style_image=list_style_image,
            list_style_position=list_style_position,
            list_style_type=list_style_type,
            margin=margin,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            margin_top=margin_top,
            overflow=overflow,
            padding=padding,
            padding_bottom=padding_bottom,
            padding_left=padding_left,
            padding_right=padding_right,
            padding_top=padding_top,
            page_break_after=page_break_after,
            page_break_before=page_break_before,
            position=position,
            text_align=text_align,
            text_decoration=text_decoration,
            text_indent=text_indent,
            text_transform=text_transform,
            top=top,
            vertical_align=vertical_align,
            visibility=visibility,
            width=width,
            z_index=z_index
        )
        for k, v in common_props.items():
            if v is not None:
                props[k] = v
        return cls(*selectors, **props)
    @classmethod
    def canonicalize_props(cls, props):
        return {k.replace("_", "-"):v for k,v in props.items()}
    @classmethod
    def parse(cls, sty):
        header = sty.split("{", 1)[0]
        if len(header) == len(sty): # inline styles
            chunks = [x.strip() for x in sty.split(";")]
            splits = [x.split(":") for x in chunks if len(x) > 0]
            return cls(**{k.strip(): v.strip() for k, v in splits})
        else:
            splits = [x.split("{") for x in sty.split("}")]
            styles = []
            for key, vals in splits:
                key = [x.strip() for x in key.split(",")]
                chunks = [x.strip() for x in vals.split(";")]
                pairs = [x.split(":") for x in chunks if len(x) > 0]
                styles.append(
                    cls(*key, **{k.strip(): v.strip() for k, v in pairs})
                )
                return styles

    def tostring(self):
        if len(self.selectors) > 0:
            return "{sel} {{\n  {body}\n}}".format(
                sel=",".join(self.selectors),
                body="\n  ".join("{k}:{v};".format(k=k,v=v) for k,v in self.props.items())
            )
        else:
            return " ".join("{k}:{v};".format(k=k,v=v) for k,v in self.props.items())

class HTMLManager:
    @classmethod
    def manage_class(kls, cls):
        if cls is None:
            cls = []
        elif hasattr(cls, 'tostring'):
            cls = cls.tostring
        if isinstance(cls, str):
            cls = cls.split()
        else:
            try:
                iter(cls)
            except TypeError:
                cls = str(cls).split()
        return list(cls)

    @classmethod
    def manage_styles(cls, styles):
        if hasattr(styles, 'items'):
            styles = CSS(**styles)
        elif isinstance(styles, str):
            styles = CSS.parse(styles)
        return styles

    keyword_replacements = {
        'cls': 'class',
        'use_for': 'for',
        'custom_type': 'is'
    }

    @classmethod
    def clean_key(cls, k):
        if k in cls.keyword_replacements:
            return cls.keyword_replacements[k]
        else:
            return k.replace("_", "-")

    @classmethod
    def sanitize_value(cls, val):
        if isinstance(val, np.integer):
            val = int(val)
        elif isinstance(val, np.floating):
            val = float(val)
        return val

    @classmethod
    def manage_attrs(cls, attrs, sanitize=True):
        for k, v in cls.keyword_replacements.items():
            if k in attrs:
                attrs[v] = attrs[k]
                del attrs[k]
        attrs = {k.replace("_", "-"): v for k, v in attrs.items()}
        if sanitize:
            attrs = {k: cls.sanitize_value(v) for k, v in attrs.items()}
        return attrs

    @classmethod
    def extract_styles(cls, attrs, style_props=None, ignored_styles=None):
        if style_props is None:
            style_props = CSS.known_properties
        if ignored_styles is not None:
            style_props = style_props - set(ignored_styles)
        styles = {}
        for k, v in tuple(attrs.items()):
            if k in style_props:
                styles[k] = v
                del attrs[k]
        return styles, attrs

    class ElementModifier:
        def __init__(self, my_el, copy=False):
            self.el = my_el
            self.needs_copy = copy
            self._parents = None
            self._tree_cache = None
        def modify(self):
            if self.needs_copy:
                el = self.el.copy()
            else:
                el = self.el
            return el
        def tostring(self):
            return self.modify().tostring()
        def _repr_html_(self):
            return self.tostring()
        def copy(self):
            import copy
            new = copy.copy(self)
            new.el = new.el.copy()
        def add_class(self, *cls, copy=True):
            return self.el.context.ClassAdder(self, cls=cls, copy=copy)
        def remove_class(self, *cls, copy=True):
            return self.el.ClassRemover(self, cls=cls, copy=copy)
        def add_styles(self, copy=True, **sty):
            return self.el.StyleAdder(self, copy=copy, **sty)
    class ClassAdder(ElementModifier):
        cls = None
        def __init__(self, el, cls=None, copy=True):
            if cls is None:
                cls = self.cls
            if isinstance(cls, str):
                cls = cls.split()
            self.cls = cls
            super().__init__(el, copy=copy)
        def modify(self):
            if hasattr(self.el, 'modify'):
                el = self.el.modify()
            else:
                if self.needs_copy:
                    el = self.el.copy()
                else:
                    el = self.el
            if 'class' in el.attrs:
                if isinstance(el['class'], str):
                    el.make_class_list()
                class_list = list(el['class'])
                for cls in self.cls:
                    cls = str(cls)
                    if cls not in class_list:
                        class_list.append(cls)
                el['class'] = tuple(class_list)
            else:
                el['class'] = self.cls
            return el
        def __repr__(self):
            return "{}({}, {})".format(type(self).__name__, self.el, self.cls)
    class ClassRemover(ElementModifier):
        cls = None
        def __init__(self, el, cls=None, copy=True):
            if cls is None:
                cls = self.cls
            if isinstance(cls, str):
                cls = cls.split()
            self.cls = cls
            super().__init__(el, copy=copy)
        def modify(self):
            if hasattr(self.el, 'modify'):
                el = self.el.modify()
            else:
                if self.needs_copy:
                    el = self.el.copy()
                else:
                    el = self.el
            if 'class' in el.attrs:
                if isinstance(el['class'], str):
                    el.make_class_list()
                class_list = list(el['class'])
                for cls in self.cls:
                    cls = str(cls)
                    try:
                        class_list.remove(cls)
                    except ValueError:
                        pass
                el['class'] = tuple(class_list)
            else:
                el['class'] = self.cls
            return el
        def __repr__(self):
            return "{}({}, {})".format(type(self).__name__, self.el, self.cls)
    class StyleAdder(ElementModifier):
        def __init__(self, el, copy=True, **styles):
            self.styles = styles
            super().__init__(el, copy=copy)
        def modify(self):
            if hasattr(self.el, 'modify'):
                el = self.el.modify()
            else:
                if self.needs_copy:
                    el = self.el.copy()
                else:
                    el = self.el

            if 'style' in el.attrs:
                style = el.attrs['style']
                if isinstance(style, str):
                    style = CSS.parse(style)
                else:
                    style = style.copy()
                style.props = dict(style.props, **self.styles)
                el.attrs['style'] = style
            else:
                el.attrs['style'] = CSS(**self.styles)
            return el
        def __repr__(self):
            return "{}({}, {})".format(type(self).__name__, self.el, self.styles)

    class StyleRemover(ElementModifier):
        def __init__(self, el, *styles, copy=True):
            self.styles = styles
            super().__init__(el, copy=copy)
        def modify(self):
            if hasattr(self.el, 'modify'):
                el = self.el.modify()
            else:
                if self.needs_copy:
                    el = self.el.copy()
                else:
                    el = self.el

            if 'style' in el.attrs:
                style = el.attrs['style']
                if isinstance(style, str):
                    style = CSS.parse(style)
                else:
                    style = style.copy()
                for k in self.styles:
                    if k in style.props:
                        del style.props[k]
                el.attrs['style'] = style
            # else:
            #     el.attrs['style'] = CSS(**self.styles)
            return el
        def __repr__(self):
            return "{}({}, {})".format(type(self).__name__, self.el, self.styles)

    @classmethod
    def xml_to_json(cls, tree:ElementTree.Element):
        children = []
        node = dict(tag=tree.tag, body=tree.text, tail=tree.tail, children=children, attrs=tree.attrib)
        for child in tree.getchildren():
            children.append(cls.xml_to_json(child))
        return node

class XMLBase:

    class ElementBase:
        ...

    @classmethod
    def find_globals(cls):
        for frame in inspect.stack(1):
            globs = frame.frame.f_globals
            if globs['__name__'] == '__main__':
                return globs
        else:
            return inspect.stack(1)[1].frame.f_globals

    @classmethod
    def expose(cls, globs=None):
        if globs is None:
            globs = cls.find_globals()
        for x in cls.get_class_map().values():
            globs[x.__name__] = x

    _cls_map = None
    @classmethod
    def get_class_map(cls):
        if cls._cls_map is None:
            cls._cls_map = {}
            for v in cls.__dict__.values():
                if isinstance(v, type) and hasattr(v, 'tag'):
                    cls._cls_map[v.tag] = v
        return cls._cls_map

    base_element = None
    @classmethod
    def convert(cls, etree:ElementTree.Element, strip=True, converter=None, **extra_attrs):
        import copy

        if converter is None:
            converter = cls.convert
        children = []
        for x in etree:
            if x.tail is not None:
                x = copy.copy(x)
                t = x.tail
                x.tail = None
                children.append(converter(x, strip=strip))
                children.append(t)
            else:
                children.append(converter(x, strip=strip))
        text = etree.text
        if text is not None:
            if isinstance(text, str):
                text = [text]
        else:
            text = []
        tail = etree.tail
        if tail is not None:
            if isinstance(tail, str):
                tail = [tail]
        else:
            tail = []
        tag = etree.tag

        elems = (
                [t.strip("\n") if strip else t for t in text]
                + children
                + [t.strip("\n") if strip else t for t in tail]
        )
        if strip:
            elems = [e for e in elems if not isinstance(e, str) or len(e) > 0]

        map = cls.get_class_map()
        try:
            tag_class = map[tag]
        except KeyError:
            tag_class = lambda *es,**ats:cls.base_element(tag, *es, **ats)

        attrs = {} if etree.attrib is None else etree.attrib

        return tag_class(*elems, **dict(extra_attrs, **attrs))

    @classmethod
    def parse(cls, str, strict=True, strip=True, fallback=None, converter=None):
        if strict:
            etree = ElementTree.fromstring(str)
        else:
            try:
                etree = ElementTree.fromstring(str)
            except ElementTree.ParseError as e:
                # print('no element found' in e.args[0])
                if 'junk after document element' in e.args[0]:
                    try:
                        return cls.parse('<div>\n\n'+str+'\n\n</div>', strict=True, strip=strip, fallback=fallback, converter=converter)
                    except ElementTree.ParseError:
                        if fallback is None:
                            fallback = HTML.Span
                        return fallback(str)
                if fallback is None:
                    fallback = HTML.Span
                return fallback(str)

        if converter is None:
            converter = cls.convert

        return converter(etree, strip=strip)


class HTML(XMLBase):
    """
    A namespace for holding various HTML attributes
    """

    class XMLElement(XMLBase.ElementBase):
        """
        Convenience API for ElementTree
        """

        ignored_styles = None
        style_props = None
        context = HTMLManager

        def __init__(self, tag, *elems, on_update=None, style=None, activator=None, **attrs):
            self.tag = tag
            self._elems = [
                self.context.sanitize_value(v)
                for v in (
                    elems[0]
                        if len(elems) == 1 and isinstance(elems[0], (list, tuple)) else
                    elems
                )
            ]
            self._elem_view = None
            attrs = self.context.manage_attrs(attrs)
            extra_styles, attrs = self.context.extract_styles(attrs, style_props=self.style_props, ignored_styles=self.ignored_styles)
            if style is not None:
                style = self.context.manage_styles(style).props
                for k,v in extra_styles.items():
                    if k in style:
                        raise ValueError("got style {} specified in two different locations".format(k))
                    style[k] = v
            else:
                style = extra_styles
            if len(style) > 0:
                attrs['style'] = style
            self._attrs = attrs
            self._attr_view = None
            self._parents = weakref.WeakSet()
            self._tree_cache = None
            self._json_cache = None
            self._on_update_callbacks = self._canonicalize_callback_dict(on_update)
            self.activator = activator
        class _update_callbacks:
            """
            Simple set of callbacks both weakly keyed and default
            """
            def __init__(self, base_callbacks, weak_callbacks):
                self.base_callbacks = base_callbacks
                self.weak_callbacks = weak_callbacks
            @classmethod
            def from_raw(cls, data):
                if data is None:
                    base = {}
                    weak = None
                elif isinstance(data, dict):
                    if all(k is None or isinstance(k, str) for k in data):
                        base = data
                        weak = None
                    else:
                        base = data.get(None, {})
                        if len(data) > 1:
                            weak = weakref.WeakKeyDictionary(
                                {
                                    k: {None: x if isinstance(x, list) else [x]} if not isinstance(x, dict) else x
                                    for k, x in data.items()
                                    if k is not None
                                }
                            )
                        else:
                            weak = None
                elif isinstance(data, weakref.WeakKeyDictionary):
                    base = {}
                    weak = data
                else:
                    base = {None: [data]}
                    weak = None
                return cls(base, weak)
            def items(self):
                if self.weak_callbacks is not None:
                    for k,v in self.weak_callbacks.items():
                        yield k,v
                yield None,self.base_callbacks
            def __contains__(self, item):
                if item is None:
                    return True
                elif self.weak_callbacks is None:
                    return False
                else:
                    return item in self.weak_callbacks
            def __setitem__(self, key, value):
                if key is None:
                    self.base_callbacks = value
                else:
                    if self.weak_callbacks is None: self.weak_callbacks = weakref.WeakKeyDictionary()
                    self.weak_callbacks[key] = value
            def get(self, item, default):
                if item is None:
                    return self.base_callbacks
                else:
                    if self.weak_callbacks is None:
                        return default
                    else:
                        return self.weak_callbacks.get(item, default)
            def __getitem__(self, item):
                if item is None:
                    return self.base_callbacks
                else:
                    if self.weak_callbacks is None:
                        raise KeyError("key {} not found".format(item))
                    else:
                        return self.weak_callbacks[item]
        def _canonicalize_callback_dict(self, on_update):
            if not isinstance(on_update, self._update_callbacks):
                on_update = self._update_callbacks.from_raw(on_update)
            return on_update
        def on_update(self, key, new_value, old_value, subkey=None):
            for registrant, callback_dict in self._on_update_callbacks.items():
                for f in callback_dict.get(key, []) + callback_dict.get(None, []):
                    sentinel = f(self, key, new_value, old_value, registrant, subkey)
                    # TODO: handle breaks from the sentinel
        def update_callbacks(self, key=None, registrant=None):
            return self._on_update_callbacks.get(registrant, {}).get(key, [])
        def add_update_callback(self, callback, key=None, registrant=None):
            if registrant not in self._on_update_callbacks: self._on_update_callbacks[registrant] = {}
            if key not in self._on_update_callbacks[registrant]: self._on_update_callbacks[registrant][key] = []
            self._on_update_callbacks[registrant][key].append(callback)
        def remove_update_callback(self, callback, key=None, registrant=None):
            if registrant not in self._on_update_callbacks: self._on_update_callbacks[registrant] = {}
            if key not in self._on_update_callbacks[registrant]: self._on_update_callbacks[registrant][key] = []
            self._on_update_callbacks[registrant][key].remove(callback)

        def __call__(self, *elems, **kwargs):
            return type(self)(
                self.tag,
                self._elems + list(elems),
                activator=self.activator,
                on_update=self.on_update,
                **dict(self.attrs, **kwargs)
            )
        @property
        def attrs(self):
            if self._attr_view is None:
                self._attr_view = frozendict(self._attrs)
            return self._attr_view
        @attrs.setter
        def attrs(self, attrs):
            old_attrs = self.attrs
            self._attrs = self.context.manage_attrs(attrs)
            self._attr_view = None
            self.invalidate_cache()
            self.on_update('attributes', attrs, old_attrs)
        @property
        def elems(self):
            if self._elem_view is None:
                self._elem_view = tuple(str(x) if isinstance(x, (int, float, bool)) else x for x in self._elems)
            return self._elem_view
        @elems.setter
        def elems(self, elems):
            self.set_elems(elems)
        def set_elems(self, elems):
            old_elems = self.elems
            self._elems = elems
            self._elem_view = None
            self.invalidate_cache()
            # self.on_update(self)
            self.on_update('elements', elems, old_elems)
        def activate(self):
            return self.activator(self)

        class StyleWrapper: # proxy for style
            def __init__(self, style_dict, obj):
                self.base_dict = style_dict
                self.base_obj = obj
            def __repr__(self):
                return "{}({})".format(type(self).__name__, self.base_dict)
            def __getitem__(self, item):
                return self.base_dict[item]
            def __setitem__(self, key, value):
                self.base_dict = dict(self.base_dict, **{key:value})
                self.base_obj.style = self.base_dict
            def __iter__(self):
                return iter(self.base_dict)
            def items(self):
                return self.base_dict.items()
            def keys(self):
                return self.base_dict.keys()
            def values(self):
                return self.base_dict.values()

        @property
        def style(self):
            if 'style' in self._attrs:
                return self.StyleWrapper(self._attrs['style'], self)
        @style.setter
        def style(self, styles):
            self['style'] = styles

        @property
        def class_list(self):
            if 'class' in self._attrs:
                return self.context.manage_class(self._attrs['class'])
            else:
                return []

        def invalidate_cache(self):
            if self._tree_cache is not None:
                self._tree_cache = None
                for p in tuple(self._parents):
                    p.invalidate_cache()
                    self._parents.remove(p)
        def __getitem__(self, item):
            if isinstance(item, str):
                item = item.replace("_", "-")
                return self._attrs[item]
            else:
                return self._elems[item]
        def __setitem__(self, item, value):
            if isinstance(item, str):
                item = item.replace("_", "-")
                old_value = self._attrs.get(item, None)
                self._attrs[item] = self.context.sanitize_value(value)
                self._attr_view = None
            else:
                old_value = self._elems[item]
                self._elems[item] = value
                self._elem_view = None
            self.invalidate_cache()
            self.on_update('attribute', value, old_value, subkey=item)
        def insert(self, where, child):
            if where is None:
                where = len(self._elems)
            self._elems.insert(where, child)
            self._elem_view = None
            self.invalidate_cache()
            self.on_update('element', child, None, subkey=where)
        def append(self, child):
            self.insert(None, child)
        def __delitem__(self, item):
            if isinstance(item, str):
                item = item.replace("_", "-")
                old_value = self._attrs.get(item, None)
                try:
                    del self._attrs[item]
                except KeyError:
                    pass
                else:
                    self._attr_view = None
            else:
                old_value = self._elems[item]
                del self._elems[item]
                self._elem_view = None
            self.invalidate_cache()
            self.on_update('attribute' if isinstance(item, str) else 'element', None, old_value, subkey=item)

        atomic_types = (int, bool, float)
        @classmethod
        def construct_etree_element(cls, elem, root, parent=None, attr_converter=None):
            if isinstance(elem, cls.atomic_types):
                elem = str(elem)
            if hasattr(elem, 'to_tree'):
                elem.to_tree(root=root, parent=parent, attr_converter=attr_converter)
            elif hasattr(elem, 'modify'):
                elem.modify().to_tree(root=root, parent=parent, attr_converter=attr_converter)
            elif isinstance(elem, ElementTree.Element):
                root.append(elem)
            elif isinstance(elem, (str, int, float, CSS)):
                elem = str(elem)
                kids = list(root)
                if len(kids) > 0:
                    if kids[-1].tail is None:
                        kids[-1].tail = elem
                    else:
                        kids[-1].tail += "\n" + elem
                else:
                    root.text = elem
            elif hasattr(elem, 'to_widget'):
                raise ValueError(
                    "can't convert {} to pure HTML. It looks like a Jupyter widget so look for the appropriate `JHTML` subclass.".format(
                        elem))
            else:
                raise ValueError("don't know what to do with {}".format(elem))

        attr_converter = None
        @classmethod
        def construct_etree_attrs(cls, attrs, attr_converter=None):
            _copied = False
            if 'style' in attrs:
                styles = attrs['style']
                if hasattr(styles, 'items'):
                    styles = CSS(**styles)
                if hasattr(styles, 'tostring'):
                    if not _copied:
                        attrs = attrs.copy()
                        _copied = True
                    attrs['style'] = styles.tostring()
            if 'class' in attrs:
                if not isinstance(attrs['class'], str):
                    if not _copied:
                        attrs = attrs.copy()
                        _copied = True
                    try:
                        iter(attrs['class'])
                    except TypeError:
                        attrs['class'] = str(attrs['class'])
                    else:
                        attrs['class'] = " ".join(str(c) for c in attrs['class'])
                    if len(attrs['class']) == 0:
                        del attrs['class']
            if attr_converter is None:
                attr_converter = cls.attr_converter
            if attr_converter is not None:
                attrs = attr_converter(attrs)
            return attrs
        @property
        def tree(self):
            return self.to_tree()
        def to_tree(self, root=None, parent=None, attr_converter=None):
            if parent is not None:
                self._parents.add(parent)
            if self._tree_cache is None:
                if root is None:
                    root = ElementTree.Element('root')
                attrs = self.construct_etree_attrs(self.attrs, attr_converter=attr_converter)
                my_el = ElementTree.SubElement(root, self.tag, attrs)
                if all(isinstance(e, str) for e in self.elems):
                    my_el.text = "\n".join(self.elems)
                else:
                    for elem in self.elems:
                        self.construct_etree_element(elem, my_el, parent=self, attr_converter=attr_converter)
                self._tree_cache = my_el
            elif root is not None:
                if self._tree_cache not in root:
                    root.append(self._tree_cache)
            return self._tree_cache
        def to_json(self, root=None, parent=None, attr_converter=None):
            tree = self.to_tree(root=root, parent=parent, attr_converter=attr_converter)
            return self.context.xml_to_json(tree)
        @classmethod
        def _prettyify(cls, current, *, indent, riffle, parent=None, index=-1, depth=0):
            # lightly adapted from https://stackoverflow.com/a/65808327/5720002
            for i, node in enumerate(current):
                cls._prettyify(node, indent=indent, riffle=riffle, parent=current, index=i, depth=depth + 1)
            if current.text is not None and len(current.text.strip()) > 0:
                current.text = (
                        riffle + textwrap.indent(current.text, prefix=indent * (depth+1))
                        + riffle + (indent * depth)
                )
            if parent is not None:
                if index == 0:
                    txt = parent.text
                    if txt is None:
                        txt = ""
                    parent.text = txt + riffle + (indent * depth)
                else:
                    txt = parent[index - 1].tail
                    if txt is not None:
                        txt = riffle + (indent * (depth)) + txt
                    else:
                        txt = ""
                    parent[index - 1].tail = txt + riffle + (indent * depth)
                if index == len(parent) - 1:
                    txt = current.tail
                    if txt is not None:
                        txt = riffle + (indent * (depth)) + txt
                    else:
                        txt = ""
                    current.tail = txt + riffle + (indent * (depth - 1))

        default_indent = "  "
        default_newline = "\n"
        def tostring(self, attr_converter=None, indent=None, method='html', riffle=True, prettify=False,
                     write_string=None,
                     **base_etree_opts):
            tree = self.to_tree(attr_converter=attr_converter)
            if prettify:
                if indent is not False:
                    if indent is None or indent is True:
                        indent = self.default_indent
                else:
                    indent = ""
                if riffle is not False:
                    if riffle is None or riffle is True:
                        riffle = self.default_newline
                else:
                    riffle = ""
                tree = copy.deepcopy(tree)
                self._prettyify(tree, indent=indent, riffle=riffle)
                if write_string is None:
                    write_string = ElementTree.tostring
                base_str = write_string(tree, **base_etree_opts)
            else:
                if indent is not None and indent is not False:
                    if indent is True:
                        indent = self.default_indent
                    tree = copy.deepcopy(tree)
                    ElementTree.indent(tree, space=indent)

                if riffle is not None and indent is not False:
                    if riffle is True:
                        riffle = self.default_newline
                    strs = [
                        s.decode() for s in ElementTree.tostringlist(
                            tree,
                            method=method,
                            **base_etree_opts
                        )
                    ]
                    base_str = riffle.join(strs)
                    if write_string is not None:
                        base_str = write_string(base_str)
                else:
                    if write_string is None:
                        write_string = ElementTree.tostring
                    base_str = write_string(tree)

            if hasattr(base_str, 'decode'):
                base_str = base_str.decode()
            return base_str

        def sanitize_key(self, key):
            key = key.replace("-", "_")
            for safe, danger in self.context.keyword_replacements.items():
                key = key.replace(danger, safe)
            return key
        def format(self, padding="", prefix="", linewidth=100):
            template_header = "{name}("
            template_footer = ")"
            template_pieces = []
            args_joiner = ", "
            full_joiner = ""
            elem_padding = ""
            def use_lines():
                nonlocal full_joiner, args_joiner, elem_padding, template_footer
                full_joiner = "\n"
                args_joiner = ",\n"
                elem_padding = padding + "  "
                template_footer = "{padding}  )"

            name = type(self).__name__
            tag = repr(self.tag) if len(template_pieces) > 1 else repr(self.tag)

            inner_comps = [
                (x.format(padding=padding+"  ", prefix=prefix, linewidth=linewidth) if isinstance(x, HTML.XMLElement) else repr(x))
                for x in self.elems if not (isinstance(x, str) and x.strip() == "")
            ]

            if not isinstance(self, HTML.TagElement):
                template_pieces.append("{tag}")
            if len(self.attrs) > 0:
                attr_pieces = ["{}={!r}".format(self.sanitize_key(k), v) for k,v in self.attrs.items()]
                if len(inner_comps) > 0:
                    template_pieces.append("{inner}")
                    template_pieces.append("{attrs}")
                else:
                    template_pieces.append("{attrs}")
            else:
                attr_pieces = []
                template_pieces.append("{inner}")
                # if "\n" not in inner:
                #     inner = inner.strip()
                #     full_joiner = ""
                #     template_footer = ")"

            template = full_joiner.join([
                template_header,
                args_joiner.join(template_pieces),
                template_footer
            ])
            out = template.format(
                padding=padding,
                tag=padding + "  " + tag,
                name=prefix+name,
                inner=args_joiner.join(elem_padding+x for x in inner_comps),
                attrs=args_joiner.join(elem_padding+x for x in attr_pieces),
            )
            if len(out) > linewidth + len(prefix):
                use_lines()
                template = full_joiner.join([
                    template_header,
                    args_joiner.join(template_pieces),
                    template_footer
                ])
                out = template.format(
                    padding=padding,
                    tag=padding + "  " + tag,
                    name=prefix + name,
                    inner=args_joiner.join(elem_padding + x for x in inner_comps),
                    attrs=args_joiner.join(elem_padding + x for x in attr_pieces),
                )
            return out
        def dump(self, prefix="", linewidth=80):
            print(self.format(prefix=prefix, linewidth=linewidth))
        def write(self, file, **opts):
            def write_str(tree, **base_opts):
                if isinstance(tree, str):
                    if hasattr(file, 'write'):
                        file.write(tree)
                    else:
                        with open(file, 'w+') as f:
                            f.write(tree)
                else:
                    tree.write(file, **base_opts)
            return self.tostring(write_string=write_str, **opts)
        MAX_REPR_LENGTH = 1000
        def __repr__(self):
            base_repr = "{}({}, {})".format(type(self).__name__, self.elems, self.attrs)
            if len(base_repr) > self.MAX_REPR_LENGTH + 3:
                split_len = self.MAX_REPR_LENGTH // 2
                base_repr = base_repr[:split_len] + "..." + base_repr[-split_len:]
            return base_repr
        def _repr_html_(self):
            return self.tostring()
        def _ipython_display_(self):
            self.display()
        def get_display_element(self):
            return HTML.Div(self, cls='jhtml')
        def get_mime_bundle(self):
            # from .WidgetTools import JupyterAPIs
            # display = JupyterAPIs.get_display_api()
            # from IPython.display import HTML as dispHTML
            wrapper = self.get_display_element()
            data = {
                'text/html': wrapper.tostring()
            }
            return data

        def _cross_plat_open(self, file, delay=5):
            import os, sys, subprocess, time
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', file])
            elif sys.platform.startswith('win'):  # Windows
                os.startfile(file, 'open')
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.run(['xdg-open', file])
            else:
                raise NotImplementedError(f"unsure how to open file on {sys.platform}")
            time.sleep(delay)

        def display_in_browser(self):
            import tempfile as tf

            if self.tag.lower() != 'html':
                if self.tag.lower() != 'body':
                    wrapper = HTML.Body(self.get_display_element())
                else:
                    wrapper = self
                wrapper = HTML.Html(wrapper)
            else:
                wrapper = self

            with tf.NamedTemporaryFile(suffix='.html', prefix=type(self).__name__+"-", mode='w+',
                                       # delete=False
                                       ) as tmp_html:
                tmp_html.write(wrapper.tostring())
                tmp_html.seek(0)
                tmp_html.flush()
                self._cross_plat_open(tmp_html.name)

        def display_ipython(self):
            from .WidgetTools import JupyterAPIs

            display = JupyterAPIs.get_display_api()
            wrapper = self.get_display_element()
            return display.display(display.HTML(wrapper.tostring()))

        def display(self):
            from .WidgetTools import JupyterAPIs

            use_ipython = JupyterAPIs.in_jupyter_environment()
            if use_ipython:
                self.display_ipython()
            else:
                self.display_in_browser()
        @mixedmethod
        def _ipython_pinfo_(self):
            from ...Docs import jdoc
            return jdoc(self)

        def make_class_list(self):
            self._attrs['class'] = self._attrs['class'].split()
        def add_class(self, *cls, copy=True):
            return self.context.ClassAdder(self, cls, copy=copy).modify()
        def remove_class(self, *cls, copy=True):
            return self.context.ClassRemover(self, cls, copy=copy).modify()
        def add_styles(self, copy=True, **sty):
            return self.context.StyleAdder(self, copy=copy, **sty).modify()
        def remove_styles(self, copy=True, **sty):
            return self.context.StyleRemover(self, copy=copy, **sty).modify()
        # def remove_styles(self, copy=True, **sty):
        #     return HTML.StyleAdder(self, copy=copy, **sty).modify()

        def _find_child_node(self, etree):
            from collections import deque
            # BFS to try to find the element that matches
            remaining = deque()
            remaining.append(self)
            while remaining:
                elem = remaining.popleft()
                if isinstance(elem, self.context.ElementModifier):
                    elem = elem.modify()
                if isinstance(elem, HTML.XMLElement):
                    if etree == elem.tree:
                        return elem
                    else:
                        for e in elem.elems:
                            remaining.append(e)

        def find(self, path, find_element=True):
            base = self.tree.find(path)
            if find_element and base is not None:
                new = self._find_child_node(base)
                if new is not None:
                    base = new
            return base
        def findall(self, path, find_element=True):
            bases = self.tree.findall(path)
            if find_element:
                new = []
                for b in bases:
                    newb = self._find_child_node(b)
                    if newb is not None:
                        new.append(newb)
                    else:
                        new.append(b)
                bases = new
            return bases
        def iterfind(self, path, find_element=True):
            bases = self.tree.iterfind(path)
            for b in bases:
                if find_element:
                    newb = self._find_child_node(b)
                    if newb is not None:
                        yield newb
                    else:
                        yield b
                else:
                    yield b
        def _build_single_selector(self, root='.//', node_type='*', parents=None, **attrs):
            return "{root}{node_type}{atts}{parents}".format(
                root=root,
                node_type=node_type,
                atts='[' +
                     ' and '.join(
                         "@{k}='{v}'".format(k='class' if k == 'cls' else k, v=v)
                         for k,v in attrs.items()
                     ) + ']' if len(attrs) > 0 else '',
                parents="" if parents is None else ('.' + '.' * parents)
            )

        def _build_xpath_selector(self,  root='.//', node_type='*', parents=None, **attrs):
            attrs.update({
                'root':root,
                'node_type':node_type,
                'parents':parents
            })
            direct_prod_attrs = [
                [v]
                    if v is None else
                [str(vv) for vv in v]
                    if not isinstance(v, (str, int, float, bool)) else
                [str(v)]
                for v in attrs.values()
            ]
            selectors = [
                self._build_single_selector(
                    **dict(zip(attrs.keys(), p))
                )
                for p in itertools.product(*direct_prod_attrs)
            ]
            return " | ".join(selectors)

        def find_by_id(self, id, mode='first', parent=None, find_element=True):
            fn = {
                'first':self.find,
                'all':self.findall,
                'iter':self.iterfind
            }[mode]
            sel = ".//*[@id='{id}']{parents}".format(id=id, parents="" if parent is None else ('.'+'.'*parent))
            return fn(sel, find_element=find_element)
        def find_by_attributes(self,
                               *,
                               root='.//', node_type='*', parents=None,
                               mode='first',
                               find_element=True,
                               **attrs
        ):
            fn = {
                'first': self.find,
                'all': self.findall,
                'iter': self.iterfind
            }[mode]
            sel = self._build_xpath_selector(root=root, node_type=node_type, parents=parents, **attrs)
            return fn(sel, find_element=find_element)
        def build_selector(self, *dicts, **attrs):
            if len(dicts) == 0:
                return self._build_xpath_selector(**attrs)
            elif len(attrs) == 0:
                cur = self._build_xpath_selector(**dicts[0])
                for d in dicts[1:]:
                    if 'root' in d:
                        raise ValueError("root is inherited from previous selector")
                    d = dict(d, root=cur+'/')
                    cur = self._build_xpath_selector(**d)
                return cur
            else:
                raise ValueError("unsure what to do when given both dicts and kwargs?")


        def copy(self):
            import copy
            base = copy.copy(self)
            base.attrs = base.attrs.copy()
            base._tree_cache = None
            base._parents = weakref.WeakSet()
            return base

    base_element = XMLElement

    class Comment(XMLElement):
        def __init__(self, *elems, **attrs):
            super().__init__(ElementTree.Comment, *elems, **attrs)

    class TagElement(XMLElement):
        tag = None
        def __init__(self, *elems, **attrs):
            super().__init__(self.tag, *elems, **attrs)
        def __call__(self, *elems, **kwargs):
            return type(self)(
                self._elems + list(elems),
                activator=self.activator,
                on_update=self.on_update,
                **dict(self.attrs, **kwargs)
            )
    class Nav(TagElement): tag='nav'
    class Anchor(TagElement): tag='a'
    class Text(TagElement): tag='p'
    class Div(TagElement): tag='div'
    class Heading(TagElement): tag='h1'
    class SubHeading(TagElement): tag='h2'
    class SubsubHeading(TagElement): tag='h3'
    class SubsubsubHeading(TagElement): tag='h4'
    class SubHeading5(TagElement): tag='h5'
    class SubHeading6(TagElement): tag='h6'
    class Small(TagElement): tag='small'
    class Bold(TagElement): tag='b'
    class Italic(TagElement): tag='i'
    class Image(TagElement): tag='img'
    class ListItem(TagElement): tag='li'
    class BaseList(TagElement):
        def __init__(self, *elems, item_attributes=None, **attrs):
            if item_attributes is None:
                item_attributes = {}
            # elems = [HTML.ListItem(x, **item_attributes) if not isinstance(x, HTML.ListItem) else x for x in elems]
            super().__init__(*elems, **attrs)
    class List(BaseList): tag='ul'
    class NumberedList(BaseList): tag='ol'
    class Pre(TagElement): tag='pre'
    class Style(TagElement): tag='style'
    class Script(TagElement): tag='script'
    class Span(TagElement): tag='span'
    class Button(TagElement): tag='button'
    class TableRow(TagElement): tag='tr'
    class TableHeading(TagElement): tag='th'
    class TableHeader(TagElement): tag='thead'
    class TableFooter(TagElement): tag='tfoot'
    class TableBody(TagElement): tag='tbody'
    class TableItem(TagElement): tag='td'
    class Table(TagElement):
        tag = 'table'
        def __init__(self, *rows, headers=None, **attrs):
            if len(rows) == 1 and isinstance(rows[0], (list, tuple)):
                rows = rows[0]
            rows = [
                HTML.TableRow(
                    [HTML.TableItem(y) if not isinstance(y, HTML.TableItem) else y for y in x]
                ) if not isinstance(x, HTML.TableRow) else x for x in rows
            ]
            if headers is not None:
                rows = [
                    HTML.TableRow([HTML.TableHeading(x) if not isinstance(x, HTML.TableHeading) else x for x in headers])
                ] + rows
            super().__init__(rows, **attrs)

    class Canvas(TagElement): tag='canvas'

    A = Anchor
    class Abbr(TagElement): tag= "abbr"
    class Address(TagElement): tag= "address"
    class Area(TagElement): tag= "area"
    class Article(TagElement): tag= "article"
    class Aside(TagElement): tag= "aside"
    class Audio(TagElement): tag= "audio"
    class B(TagElement): tag= "b"
    class Base(TagElement): tag= "base"
    class Bdi(TagElement): tag= "bdi"
    class Bdo(TagElement): tag= "bdo"
    class Blockquote(TagElement): tag= "blockquote"
    class Body(TagElement): tag= "body"
    class Br(TagElement): tag= "br"
    class Caption(TagElement): tag= "caption"
    class Cite(TagElement): tag= "cite"
    class Code(TagElement): tag= "code"
    class Col(TagElement): tag= "col"
    class Colgroup(TagElement): tag= "colgroup"
    class Data(TagElement): tag= "data"
    class Datalist(TagElement): tag= "datalist"
    class Dd(TagElement): tag= "dd"
    class Del(TagElement): tag= "del"
    class Details(TagElement): tag= "details"
    class Dfn(TagElement): tag= "dfn"
    class Dialog(TagElement): tag= "dialog"
    class Dl(TagElement): tag= "dl"
    class Dt(TagElement): tag= "dt"
    class Em(TagElement): tag= "em"
    class Embed(TagElement): tag= "embed"
    class Fieldset(TagElement): tag= "fieldset"
    class Figcaption(TagElement): tag= "figcaption"
    class Figure(TagElement): tag= "figure"
    class Footer(TagElement): tag= "footer"
    class Form(TagElement): tag= "form"
    class Head(TagElement): tag= "head"
    class Header(TagElement): tag= "header"
    class Hr(TagElement): tag= "hr"
    class Html(TagElement): tag = "Html"
    i = Italic
    class Iframe(TagElement): tag= "iframe"
    Img = Image
    class Input(TagElement): tag= "input"
    class Ins(TagElement): tag= "ins"
    class Kbd(TagElement): tag= "kbd"
    class Label(TagElement): tag= "label"
    class Legend(TagElement): tag= "legend"
    Li = ListItem
    class Link(TagElement): tag= "link"
    class Main(TagElement): tag= "main"
    class Map(TagElement): tag= "map"
    class Mark(TagElement): tag= "mark"
    class Meta(TagElement): tag= "meta"
    class Meter(TagElement): tag= "meter"
    class Noscript(TagElement): tag= "noscript"
    class Object(TagElement): tag= "object"
    Ol = NumberedList
    P = Text
    class Optgroup(TagElement): tag= "optgroup"
    class Option(TagElement): tag= "option"
    class Output(TagElement): tag= "output"
    class Param(TagElement): tag= "param"
    class Picture(TagElement): tag= "picture"
    class Progress(TagElement): tag= "progress"
    class Q(TagElement): tag= "q"
    class Rp(TagElement): tag= "rp"
    class Rt(TagElement): tag= "rt"
    class Ruby(TagElement): tag= "ruby"
    class S(TagElement): tag= "s"
    class Samp(TagElement): tag= "samp"
    class Section(TagElement): tag= "section"
    class Select(TagElement): tag= "select"
    class Source(TagElement): tag= "source"
    class Strong(TagElement): tag= "strong"
    class Sub(TagElement): tag= "sub"
    class Summary(TagElement): tag= "summary"
    class Sup(TagElement): tag= "sup"
    class Svg(TagElement): tag= "svg"
    Tbody = TableBody
    Td = TableItem
    class Template(TagElement): tag= "template"
    class Textarea(TagElement): tag= "textarea"
    Tfoot = TableFooter
    Th = TableHeading
    Thead = TableHeader
    class Time(TagElement): tag= "time"
    class Title(TagElement): tag= "title"
    Tr = TableRow
    class Track(TagElement): tag= "track"
    class U(TagElement): tag= "u"
    Ul = List
    class Var(TagElement): tag= "var"
    class Video(TagElement): tag= "video"
    class Wbr(TagElement): tag= "wbr"

    # @classmethod
    # def extract_body(cls, etree, strip=True):
    #     text = etree.text
    #     if text is not None:
    #         if isinstance(text, str):
    #             text = [text]
    #     else:
    #         text = []
    #     tail = etree.tail
    #     if tail is not None:
    #         if isinstance(tail, str):
    #             tail = [tail]
    #     else:
    #         tail = []
    #     tag = etree.tag
    #
    #     elems = (
    #             [t.strip() if strip else t for t in text]
    #             + children
    #             + [t.strip() if strip else t for t in tail]
    #     )
    #     if strip:
    #         elems = [e for e in elems if not isinstance(e, str) or len(e) > 0]

class ContentXML(XMLBase):

    class Element(HTML.XMLElement):
        ignored_styles = CSS.known_properties
        def get_display_element(self):
            return HTML.Pre(self.tostring()).get_display_element()
        def tostring(self, method='xml', prettify=True, **opts):
            return super().tostring(method=method, prettify=prettify, **opts)

    base_element = Element
    class TagElement(Element):
        tag = None

        def __init__(self, *elems, **attrs):
            super().__init__(self.tag, *elems, **attrs)

        def __call__(self, *elems, **kwargs):
            return type(self)(
                self._elems + list(elems),
                activator=self.activator,
                on_update=self.on_update,
                **dict(self.attrs, **kwargs)
            )

    class DeclarativeElement(TagElement):
        def __init__(self, *elems, **attrs):
            self.tag = type(self).__name__
            super().__init__(*elems, **attrs)

    class Comment(HTML.Comment): ...

    class PrefixedElement(Element):
        prefix = None
        def __init__(self, base_tag, *elems, **attrs):
            self.base_tag = base_tag
            super().__init__(self.prefix + base_tag, *elems, **attrs)
        def __call__(self, *elems, **kwargs):
            return type(self)(
                self.base_tag,
                self._elems + list(elems),
                activator=self.activator,
                on_update=self.on_update,
                **dict(self.attrs, **kwargs)
            )


