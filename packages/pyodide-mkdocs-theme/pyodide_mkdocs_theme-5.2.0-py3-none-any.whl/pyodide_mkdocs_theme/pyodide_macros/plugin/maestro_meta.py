"""
pyodide-mkdocs-theme
Copyleft GNU GPLv3 🄯 2024 Frédéric Zinelli

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.
If not, see <https://www.gnu.org/licenses/>.
"""
# pylint: disable=multiple-statements



import inspect
from contextlib import contextmanager
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set, Tuple, Type
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path

import yaml

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page



from ..exceptions import PmtMacrosContractError, PmtMacrosError, PmtMetadataError
from ..pyodide_logger import logger
from ..tools_and_constants import DeprecationLevel, ScriptData
from .tools.maestro_tools import CopyableConfig
from .config import PyodideMacrosConfig, PLUGIN_CONFIG_SRC, SubConfigSrc
from .maestro_files import MaestroFiles








class MaestroMeta(MaestroFiles):
    """ Handles the .meta.pmt.yml values and the meta sections in Pages. """

    __pmt_meta_wrapped__: str = "__pmt_meta_wrapped__"
    """
    Property added to the mkdocs events decorated with MaestroMeta.meta_config_swap. This property
    allows to enforce proper contracts on the config values, whatever the plugin inheritance chain.
    """

    _meta_tree: Optional['MetaTree'] = None
    """
    Tree holding all the meta configs, merging the data appropriately at any depth.
    """



    def on_config(self, config:MkDocsConfig):

        self.check_config_swap_decorations()

        super().on_config(config)

        # Gather all the meta files AFTER the super call, so that the config is up to date:
        self._meta_tree = MetaTree.create_meta_config_tree(self)



    def invalid_config_or_args(
        self,
        bads: List[Tuple[bool,str]],
        msg: str,
        error_class:Type[PmtMacrosError],
    ):
        all_deprecated = all(is_dep for is_dep,_ in bads)
        if all_deprecated and self.deprecation_level == DeprecationLevel.warn:
            logger.warning(msg)
        else:
            raise error_class(msg)


    #-------------------------------------------------------------------------



    @classmethod
    def meta_config_swap(cls, method_or_env):
        """
        Static decorator for mkdocs events that are using a Page argument.

        For the decorated event, the global mkdocs config content will be swapped with a version
        of it merged with the content of the .meta.pmt.yml files, and any metadata section in the
        page itself.
        """
        is_env    = isinstance(method_or_env, MaestroMeta)
        env       = method_or_env if is_env else None
        decorator = _meta_swap_decorator(env, cls.__pmt_meta_wrapped__)
        return decorator if is_env else decorator(method_or_env)



    @contextmanager
    def local_meta_config(self, page:Optional[Page]):
        """
        Context manager putting in place (by mutation) the global config plugin updated with
        the meta data "up to the given page".
        """
        # pylint: disable=E0203, W0201
        self.setup_ctx(page)
        if not page:
            yield
        else:
            before = self._meta_tree.swap_config_for_page(page)
            try:
                yield
            finally:
                self._meta_tree.rotate(before)



    def check_config_swap_decorations(self):
        """
        Check the top event calls in the hierarchy are wrapped with the MaestroMeta decorator.
        At the time of writing this class, the hierarchy leads to these qualified names (PMT 5.0):

            PyodideMacrosPlugin
            MaestroContracts
            MaestroTemplates
            MaestroMacros
            MaestroMacroManager
            MaestroIndent
            MaestroMeta
            MaestroFiles
            MaestroPyLibs
            MaestroGeneratedPages
            BaseMaestro
            BasePlugin[PyodideMacroConfig]
            MacrosPlugin                        <<< Meta configs have to also be seen here!
            ---------------------------------------------------------------
            # Any method visible/defined only here or deeper doesn't need to be decorated:
            BasePlugin
            Generic
            object
        """
        mro_depth = { cls.__qualname__: i for i,cls in enumerate(self.__class__.mro()) }
        no_wrapper_needed = mro_depth['BasePlugin']
        for hook in '''
            on_pre_page
            on_page_read_source
            on_page_markdown
            on_page_content
            on_page_context
            on_post_page
        '''.split():

            method = getattr(self, hook, None)
            if not method:
                continue

            cls_qualname = method.__qualname__[:-len(method.__name__)-1]
            need_wrapper = mro_depth[cls_qualname] < no_wrapper_needed
            is_decorated = hasattr(method, self.__pmt_meta_wrapped__)

            if need_wrapper and not is_decorated:
                raise PmtMacrosContractError(
                    f'The { method.__qualname__ } event method should be decorated with the '
                    f'pyodide_mkdocs_theme.pyodide_macros.{ self.meta_config_swap.__qualname__ } '
                     'class method decorator (use it as outer decorator).'
                )









def _meta_swap_decorator(env:Optional[MaestroMeta], wrap_property_flag:str):
    def decorator(method:Callable):

        def build_page_getter_at_runtime(args:tuple, kwargs:dict) -> Callable :
            """
            If introspection didn't work try to build the page_getter from the runtime values.
            (Note: nowadays, useless in PMT itself. Kept just in case...)
            """
            i_arg = next( (i    for i,v in enumerate(args)   if isinstance(v,Page)), None)
            name  = next( (name for name,v in kwargs.items() if isinstance(v,Page)), None)

            # pylint: disable=unnecessary-lambda-assignment
            if i_arg is not None and name:
                raise PmtMetadataError(
                    "Found several arguments that could be a Page argument in the "
                    f"{ method.__name__ } method."
                )
            if i_arg is not None:
                return getter_builder(i_arg)
            elif name is not None:
                return getter_builder(name_arg=name)
            else:
                raise PmtMetadataError(
                    "Couldn't find an argument whose the value is a mkdocs Page instance on "
                    f"the { method.__name__ } method."
                )


        def getter_builder(i_arg:int=None, name_arg:str=None):
            if page_getter:
                raise PmtMetadataError(
                    "Found several arguments that could be a Page argument in the "
                    f"{ method.__name__ } method."
                )
            if name_arg:
                return lambda _, kwargs: kwargs[name_arg]
            else:
                return lambda args, kw: kw['page'] if 'page' in kw else args[i_arg]
                # Needs the extra check for kw because mkdocs may pass positional args as
                # _NAMED_ args anyway...


        page_getter: Callable = None

        # First, try introspection on the method arguments (through annotations)
        params = inspect.signature(method).parameters
        for i_arg,param in enumerate(params.values()):
            if param.annotation in (Page, Optional[Page]):
                if param.kind == param.KEYWORD_ONLY:
                    page_getter = getter_builder(name_arg=param.name)
                else:
                    page_getter = getter_builder(i_arg)

        @wraps(method)
        def wrapper(*a, **kw):
            nonlocal page_getter

            if not page_getter:
                # If introspection didn't work:
                page_getter = build_page_getter_at_runtime(a,kw)

            page: Page = page_getter(a, kw)
            env_meta: MaestroMeta = env or a[0]
            with env_meta.local_meta_config(page):
                out = method(*a,**kw)
            return out

        setattr(wrapper, wrap_property_flag, True)

        return wrapper
    return decorator










@dataclass
class MetaTree:
    """
    Configuration metadata tree, handling mkdocs.yml config and .pmt.meta.yml files.

    - One MetaTree instance per directory.
    - The self.config objects are shared across différent MetaTree instances when it doesn't change.

    Using a global cache (page.file.src_uri based) because the config swap will occur in various hooks
    for the same pages, so this avoids to recompute the config several times (on_page_markdown,
    on_page_content, on_page_context, ...)
    """

    env: MaestroMeta

    segment: str
    """ Directory name or file name. """

    config: CopyableConfig

    children: Dict[str,'MetaTree'] = field(default_factory=dict)


    _CACHE: ClassVar[Dict[str,CopyableConfig]] = {}


    @classmethod
    def create_meta_config_tree(cls, env:MaestroMeta):
        logger.info("Build meta configs tree.")

        # Make sure the class level cache is emptied on each consecutive build (simpler):
        cls._CACHE.clear()

        # Remove anything that is invalid for a PyodideMacrosConfig instance => allow to get rid of
        # the macro related parts and various things that shouldn't be there...
        cfg:CopyableConfig = PyodideMacrosConfig()
        cfg = cfg.copy_with(env.config)

        meta_tree = cls(env, '_docs_', cfg)      # Root element

        # Explore the docs_dir and build all intermediate configs:
        for meta_path in env.docs_dir_path.rglob(env._pmt_meta_filename):
            content  = meta_path.read_text(encoding=env.meta_yaml_encoding)
            meta_rel = meta_path.relative_to(env.docs_dir_path)
            meta_dct = yaml.load(content, Loader=yaml.Loader)
            meta_tree.insert_meta_file(meta_dct, meta_rel)

        return meta_tree


    def insert_meta_file(self, yml_dct:dict, meta_path:Path):
        """
        Insert the merged config for a given meta file in the MetaTree hierarchy.
        The content of the file is validated against the PyodidePluginSrc structure (first level
        is validated or not depending on `build.meta_yaml_allow_extras` value).
        """
        self._validate_meta_data(
            yml_dct, str(meta_path), self.env, validate_top_lvl=not self.env.meta_yaml_allow_extras
        )

        tree = self
        for segment in meta_path.parent.parts:
            if segment not in tree.children:
                tree.children[segment] = MetaTree(tree.env, segment, tree.config)
            tree = tree.children[segment]

        tree.config = tree.config.copy_with(yml_dct, consume_dict=True)

        if yml_dct:
            raise PmtMetadataError(
                f"Invalid key/value pairs in { self.env.docs_dir_cwd_rel / meta_path }:"
                + "".join( f'\n    {k} : {v!r}' for k,v in yml_dct.items())
            )



    def _validate_meta_data(
        self,
        meta_dct: Dict[str,Any],
        file: str,
        env: MaestroMeta,
        validate_top_lvl:bool=False,
    ):
        bads = [
            *self._validate_meta_python_libs(meta_dct, env.base_py_libs)
        ]
        if validate_top_lvl:
            bads.extend( PLUGIN_CONFIG_SRC.yield_invalid_yaml_paths_or_values(meta_dct) )
        else:
            for key in meta_dct:
                if PLUGIN_CONFIG_SRC.has(key):
                    sub:SubConfigSrc = getattr(PLUGIN_CONFIG_SRC, key)
                    bads.extend( sub.yield_invalid_yaml_paths_or_values(meta_dct[key]) )

        if bads:
            source_kind = "meta file" if file.endswith(env._pmt_meta_filename) else "headers of the file"
            msg = (
                f"Invalid PyodideMacrosPlugin configuration in the { source_kind } {file}:\n  "
                + '\n'.join(msg for _,msg in bads)
                + "\nIf you are trying to add variables or content at the top level of a "
                + "`.meta.pmt.yml` file, set the `build.meta_yaml_allow_extras` to true."
            )
            env.invalid_config_or_args(bads, msg, PmtMetadataError)



    def _validate_meta_python_libs(
        self,
        meta_dct: Dict[str,Any],
        base_py_libs: Set[str],
    ):
        """
        Validate that all the python_libs names are found in the mkdocs.yml initial configuration.
        If @meta_dct is None, check the content of self.python_libs instead (allow to validate
        headers).
        """
        if 'build' not in meta_dct: return
        dct = meta_dct['build']
        if 'python_libs' not in dct: return
        lst = dct['python_libs']

        bad_libs = [lib for lib in lst if lib not in base_py_libs]
        if bad_libs:
            yield False, "Invalid build.python_libs:\n  " + ' '.join(bad_libs)



    def get_config_for_page_with_metadata(self, page:Page):
        """
        Extract the appropriated config for the given Page directory, then merge it with
        any metadata section coming from the Page itself.

        NOTE: Only the metadata matching some of the plugin's config options will be merged.
              Other values/items will be ignored (they are still usable in macros call using
              the original way the macros plugin handles them). For more information, see:
              https://mkdocs-macros-plugin.readthedocs.io/en/latest/post_production/#html-templates
        """
        src = Path(page.file.src_uri)       # Relative to docs_dir!

        if src not in self._CACHE:
            self._validate_meta_data(page.meta, page.file.src_uri, self.env)

            # Find the deepest parent config (yaml contents):
            tree = self
            segments = src.parent.parts     # Note:  Path('index.md').parent.parts == () => ok!
            for segment in segments:
                if segment not in tree.children:
                    break
                tree = tree.children[segment]

            # then merge with the markdown headers if any:
            config = tree.config if not page.meta else tree.config.copy_with(page.meta)
            self._CACHE[src] = config

        return self._CACHE[src]


    def swap_config_for_page(self, page:Page):
        """
        Extract the live config for the given page, merging with the md headers if any, then rotate all
        the values/data related to the local config and return a tuple of the original values to restore
        after the logic needing the config swap has been applied.
        """
        current = (
            self.env.config,
            self.env.allowed_pmt_sections_in_order,
            self.env.allowed_pmt_sections,
            self.env.pmt_sections_pattern,
        )

        # Swap the config, so that the new values (below) are computed with it:
        self.env.config   = self.get_config_for_page_with_metadata(page)

        sections_in_order = [*ScriptData.VALUES, *self.env.extra_pyodide_sections]
        sections_as_set   = {*ScriptData.VALUES, *self.env.extra_pyodide_sections}
        sections_pattern  = ScriptData.build_pattern_from([*sections_as_set, ScriptData.ignore])

        self.rotate((
            self.env.config, sections_in_order, sections_as_set, sections_pattern,
        ))
        return current


    def rotate(self, data:Tuple[Any,...]):
        (
            self.env.config,
            self.env.allowed_pmt_sections_in_order,
            self.env.allowed_pmt_sections,
            self.env.pmt_sections_pattern
        ) = data
