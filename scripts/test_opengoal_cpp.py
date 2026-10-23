"""Original regression inputs: no recovered game source or IR."""
import copy
import unittest

from opengoal_cpp import emit
from prepare_opengoal_path import selected_form
from probe_opengoal_browser import OutputParser


def program(instructions):
    return {'functions': [{'name': 'eco-entry', 'instructions': [
        {'text': text, 'assembly_family': False} for text in instructions]}]}


class PortableBoundaryTests(unittest.TestCase):
    def test_duplicate_function_identity_rejected(self):
        doc = program(['null'])
        doc['functions'].append(copy.deepcopy(doc['functions'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate function'):
            emit(doc, 'eco-entry')

    def test_host_service_cannot_be_shadowed(self):
        doc = program(['null'])
        doc['functions'].append({'name': 'eco-suspend', 'instructions': []})
        with self.assertRaisesRegex(ValueError, 'host service'):
            emit(doc, 'eco-entry')

    def test_unknown_opcode_does_not_emit_success(self):
        with self.assertRaisesRegex(ValueError, 'unsupported IR'):
            emit(program(['native-stack-copy']), 'eco-entry')

    def test_assembly_needs_semantics_even_if_text_looks_supported(self):
        doc = program(['null'])
        doc['functions'][0]['instructions'][0]['assembly_family'] = True
        with self.assertRaisesRegex(ValueError, 'semantic lowering'):
            emit(doc, 'eco-entry')

    def test_unresolved_call_graph_does_not_become_stub(self):
        with self.assertRaisesRegex(ValueError, 'missing function: missing'):
            emit(program(["mov igpr-1, 'missing"]), 'eco-entry')

    def test_branch_cannot_escape_frame(self):
        for text in ['goto label-2', 'j(igpr-0 < igpr-1) label-2']:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'branch outside'):
                emit(program([text]), 'eco-entry')

    def test_out_of_bounds_register_rejected(self):
        with self.assertRaisesRegex(ValueError, 'register limit'):
            emit(program(['mov-ic igpr-256, 7']), 'eco-entry')

    def test_only_reachable_functions_lowered(self):
        doc = program(['mov-ic igpr-2, 205', 'ret igpr-0 igpr-2'])
        other = copy.deepcopy(doc['functions'][0])
        other['name'] = 'unreachable'
        other['instructions'][0]['text'] = 'unsupported-native-op'
        doc['functions'].append(other)
        self.assertIn('f.r[2] = uint64_t(205)', emit(doc, 'eco-entry'))

    def test_extraction_retains_strings_and_comments(self):
        source = '(defun original () "escaped \\\" )" ; )\n  (call))\n(next)'
        self.assertEqual(selected_form(source, '(defun original '), source[:source.index('\n(next)')])
        with self.assertRaises(ValueError):
            selected_form('(defun original ()', '(defun original ')

    def test_browser_assertions_ignore_script_literals(self):
        parser = OutputParser()
        parser.feed('<pre id="output">not complete</pre><script>"RESULT 205 yields=3 ticks=3"</script>')
        self.assertEqual(parser.output, 'not complete')


if __name__ == '__main__':
    unittest.main()
