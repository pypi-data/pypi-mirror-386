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

from typing import TYPE_CHECKING, ClassVar, List, Optional, Tuple, Type
from pathlib import Path
from dataclasses import dataclass


from ..exceptions import PmtMacrosInvalidPmtFileError
from ..tools_and_constants import ScriptData, SiblingFile
from ..paths_utils import read_file
from .base3_generic_extractors import (
    GenericExtractor,
    SingleFileExtractor,
    SingleFileExtractorWithRems,
)

if TYPE_CHECKING:
    from pyodide_mkdocs_theme.pyodide_macros import PyodideMacrosPlugin

CWD = Path.cwd()






#--------------------------------------------------------------------------------------






@dataclass(eq=False)
class SqlExtractor(SingleFileExtractorWithRems, terminal=True):

    ARG_NAME:         ClassVar[str] = "sql_name"
    EXTENSION:        ClassVar[str] = ".sql"
    LEADING_HEADER:   ClassVar[str] =r"--[\t -]*"
    TRAILING_HEADER:  ClassVar[str] =r"[\t -]*--"
    INCLUSION_HEADER: ClassVar[str] = "--"






#--------------------------------------------------------------------------------------






@dataclass(eq=False)
class PythonExtractor(GenericExtractor, terminal=True):

    ARG_NAME:         ClassVar[str] = "py_name"
    EXTENSION:        ClassVar[str] = ".py"
    LEADING_HEADER:   ClassVar[str] =r"#[\t ]*-+[\t ]*"
    TRAILING_HEADER:  ClassVar[str] =r"[\t ]*-+[\t ]*#"
    INCLUSION_HEADER: ClassVar[str] = "##"

    @classmethod
    def get_file_extractor_for(
        cls, env:'PyodideMacrosPlugin', rel_path:str, *, runner_file:Optional[Path]=None, with_top_constraint=False
    ) -> Tuple[Path, 'GenericExtractor'] :

        # Use of .snippets.py files as macro arguments are not allowed.
        is_snippets = rel_path and rel_path.split('/')[-1] == env.py_snippets_stem
        if with_top_constraint and is_snippets:
            raise PmtMacrosInvalidPmtFileError(
                f"`{ env.py_snippets_stem }.py` files cannot be used as macro argument: they can "
                f"only be used for code snippets inclusion.\n{ env.log() }"
            )
        return super().get_file_extractor_for(env, rel_path, runner_file=runner_file, with_top_constraint=False)

    @classmethod
    def get_extractor_class(cls, env:'PyodideMacrosPlugin', runner_file:Optional[Path]) -> Type['PythonExtractor']:
        is_snippets = runner_file and runner_file.stem == env.py_snippets_stem
        if is_snippets:
            return PythonSnippetsExtractor
        return PythonFilesExtractor





@dataclass(eq=False)
class PythonSnippetsExtractor(SingleFileExtractor, PythonExtractor):


    def extract_files_content(self):
        script_content = read_file(self.exo_file) if self.exo_file else ""
        self.extract_monolithic_pmt_file(script_content)


    def validate_section(self, section:str, *, required=False):
        if section not in self.contents:
            self._raise_invalid_section(section)


    def check_potential_invalid_pmt_headers(
        self,
        script_content: str,
        headers: List[Tuple[str,str]],
        headers_and_matches: List[Tuple[str,str]],
    ):
        pass




@dataclass(eq=False)
class PythonFilesExtractor(SingleFileExtractorWithRems, PythonExtractor):

    def iter_on_files(self):
        return (
            self.exo_file,
            self.rem_rel_path,
            self.vis_rem_rel_path,
            self.corr_rel_path,
            self.test_rel_path,
        )

    def extract_non_pmt_file(self, script_content:str):
        """
        "Old fashion way" extractions, with:
            - user code + public tests (+ possibly HDR) in the base script file (optional)
            - secret tests in "{script}_test.py" (optional)
            - Correction in "{script}_corr.py" (optional, but secret tests have to exist)
            - Remarks in "{script}_REM.md" (optional, but secret tests have to exist)

        (Bypass the super call)
        """
        log_exo = self.exo_file and Path(self.exo_file).relative_to(CWD)

        self.env.outdated_PM_files.append(
            (log_exo, self.env.file_location())
        )

        if script_content.startswith('#MAX'):
            # SOFT DEPRECATED (kept in case the user set the logger to `warn` instead of `error`)
            # If something about MAX in the file, it has precedence:
            self.env.warn_unmaintained(
                partial_msg = "Setting IDE MAX value through the file is deprecated. Move this "
                             f"to the IDE macro argument.\nFile: { log_exo }"
            )
            script = script_content
            first_line, script = script.split("\n", 1) if "\n" in script else (script,'')
            script_content = script.strip()
            self.file_max_attempts = first_line.split("=")[1].strip()

        sections_with_strip = (
            (ScriptData.env,      True),
            (ScriptData.code,     True),
            (ScriptData.tests,    True),
            (ScriptData.secrets,  True),
            (ScriptData.corr,     True),
            (ScriptData.REM,      False),
            (ScriptData.VIS_REM,  False),
        )
        contents = (
            *self.env.get_hdr_and_public_contents_from(script_content, apply_strip=False),
            *map(self.get_file_content_or_empty_string, SiblingFile.VALUES)
        )

        for (section, stripped), content in zip(sections_with_strip, contents):
            if stripped:
                content = self.strip_section(content)
            self.contents[section] = content
