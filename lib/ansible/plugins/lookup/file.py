# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: file
    author: Daniel Hokka Zakrisson <daniel@hozac.com>
    version_added: "0.9"
    short_description: read file contents
    description:
        - This lookup returns the contents from a file on the Ansible controller's file system.
    options:
        _terms:
            description: path(s) of files to read
            required: True
        rstrip:
            description: whether or not to remove whitespace from the end of the file
            type: bool
            required: False
            default: True
        lstrip:
            description: whether or not to remove whitespace from the beginning of the file
            type: bool
            required: False
            default: False
        rstrip_non_printable:
            description: >
                whether or not to remove non-printable characters from the end of the file
            type: bool
            required: False
            default: False
        lstrip_non_printable:
            description: >
                whether or not to remove non-printable characters from the beginning of
                the file
            type: bool
            required: False
            default: False
        encoding:
            description: Encoding to read the file with
            type: str
            required: False
            default: utf-8
    notes:
        - >
            if read in variable context, the file can be interpreted as YAML if the content is
            valid to the parser.
        - this lookup does not understand 'globbing', use the fileglob lookup instead.
"""

EXAMPLES = """
- debug: msg="the value of foo.txt is {{lookup('file', '/etc/foo.txt') }}"

- name: display multiple file contents
  debug: var=item
  with_file:
    - "/path/to/foo.txt"
    - "bar.txt"  # will be looked in files/ dir relative to play or in role
    - "/path/to/biz.txt"
"""

RETURN = """
  _raw:
    description:
      - content of file(s)
"""

import string

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []

        for term in terms:
            display.debug("File lookup term: %s" % term)

            # Find the file in the expected search path
            lookupfile = self.find_file_in_search_path(variables, 'files', term)
            display.vvvv(u"File lookup using %s as file" % lookupfile)
            try:
                if lookupfile:
                    b_contents, show_data = self._loader._get_file_contents(lookupfile)
                    contents = to_text(
                        b_contents, encoding=kwargs.get('encoding', 'utf-8'),
                        errors='surrogate_or_strict'
                    )
                    lstrip_npa = kwargs.get('lstrip_non_printable', False)
                    rstrip_npa = kwargs.get('rstrip_non_printable', False)
                    lstrip = kwargs.get('lstrip', False)
                    rstrip = kwargs.get('rstrip', False)
                    lindex = 0
                    rindex = 0
                    if lstrip or lstrip_npa:
                        for lindex, char in enumerate(contents):
                            if lstrip and char in string.whitespace:
                                continue
                            elif lstrip_npa and char not in string.printable:
                                continue
                            else:
                                break
                    if rstrip or rstrip_npa:
                        for rindex, char in enumerate(reversed(contents)):
                            if rstrip and char in string.whitespace:
                                continue
                            elif rstrip_npa and char not in string.printable:
                                continue
                            else:
                                break
                    contents = contents[lindex:(len(contents)-rindex)]
                    ret.append(contents)
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("could not locate file in lookup: %s" % term)

        return ret