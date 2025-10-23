""" unit tests. """
import datetime


# noinspection PyProtectedMember
from ae.sys_core_sh import SihotXmlParser, ResResponse, SihotXmlBuilder, _SihotTcpClient


class TestSihotTcpClient:
    def test_init_defaults(self):
        stc = _SihotTcpClient(server_ip='server_ip', server_port=369)
        assert stc.server_ip == 'server_ip'
        assert stc.server_port == 369
        assert stc.timeout == 3.6
        assert stc.encoding == 'utf-8'
        assert stc.debug_level == 0

    def test_init_params(self):
        stc = _SihotTcpClient(server_ip='server_ip', server_port=369, timeout=0.369, encoding='encoding',
                              debug_level=3)
        assert stc.server_ip == 'server_ip'
        assert stc.server_port == 369
        assert stc.timeout == 0.369
        assert stc.encoding == 'encoding'
        assert stc.debug_level == 3


class TestSihotXmlParser:
    XML_EXAMPLE = '''<?xml version="1.0" encoding="iso-8859-1"?>
    <SIHOT-Document>
        <SIHOT-Version>
            <Version>9.0.0.0000</Version>
            <EXE>D:\\sihot\\sinetres.exe</EXE>
        </SIHOT-Version>
        <OC>A-SIMPLE_TEST_OC</OC>
        <ID>1</ID>
        <TN>123</TN>
        <RC>0</RC>
    </SIHOT-Document>'''

    def test_attributes(self, cons_app):
        xml_parser = SihotXmlParser(cons_app)
        xml_parser.parse_xml(self.XML_EXAMPLE)
        assert xml_parser.oc == 'A-SIMPLE_TEST_OC'
        assert xml_parser.tn == '123'
        assert xml_parser.id == '1'
        assert xml_parser.rc == '0'
        assert xml_parser.msg == ''
        assert xml_parser.ver == ''
        assert xml_parser.error_level == '0'
        assert xml_parser.error_text == ''


class TestResResponse:
    SXML_RESPONSE_EXAMPLE = '''<?xml version="1.0" encoding="iso-8859-1"?>
    <SIHOT-Document>
        <SIHOT-Version>
            <Version>9.0.0.0000</Version>
            <EXE>D:\\SIHOT\\SINETRES.EXE</EXE>
        </SIHOT-Version>
        <OC>FAKE_UNKNOWN_OC_MSG</OC>
        <TN>135</TN>
        <ID>99</ID>
        <RC>1</RC>
        <MSG>Unknown operation code!</MSG>
        <MATCHCODE>E987654</MATCHCODE>
    </SIHOT-Document>'''

    def test_attributes(self, cons_app):
        xml_parser = ResResponse(cons_app)
        xml_parser.parse_xml(self.SXML_RESPONSE_EXAMPLE)
        assert xml_parser.oc == 'FAKE_UNKNOWN_OC_MSG'
        assert xml_parser.tn == '135'
        assert xml_parser.id == '99'
        assert xml_parser.rc == '1'
        assert xml_parser.msg == 'Unknown operation code!'
        assert xml_parser.ver == ''
        assert xml_parser.error_level == '0'
        assert xml_parser.error_text == ''
        assert xml_parser.matchcode == 'E987654'


class TestSihotXmlBuilder:
    def test_create_xml(self, cons_app):
        xml_builder = SihotXmlBuilder(cons_app)
        xml_builder.beg_xml('TEST_OC')
        xml_builder.add_tag('EMPTY')
        xml_builder.add_tag('DEEP', xml_builder.new_tag('DEEPER', 'value'))
        test_date = xml_builder.convert_value_to_xml_string(datetime.datetime.now())
        xml_builder.add_tag('DATE', test_date)
        xml_builder.end_xml()
        cons_app.dpo('----  New XML created: ', xml_builder.xml)
        assert xml_builder.xml.startswith('<?xml version="1.0"')
        assert xml_builder.xml.endswith(
            '?>\n<SIHOT-Document>\n'
            '<OC>TEST_OC</OC><TN>2</TN><EMPTY></EMPTY><DEEP><DEEPER>value</DEEPER></DEEP>'
            '<DATE>' + test_date + '</DATE>\n</SIHOT-Document>')

    def test_create_xml_kernel(self, cons_app):
        xml_builder = SihotXmlBuilder(cons_app, use_kernel=True)
        xml_builder.beg_xml('TEST_OC')
        xml_builder.add_tag('EMPTY')
        xml_builder.add_tag('DEEP', xml_builder.new_tag('DEEPER', 'value'))
        test_date = xml_builder.convert_value_to_xml_string(datetime.datetime.now())
        xml_builder.add_tag('DATE', test_date)
        xml_builder.end_xml()
        cons_app.dpo('----  New XML created: ', xml_builder.xml)
        assert xml_builder.xml.startswith('<?xml version="1.0"')
        assert xml_builder.xml.endswith(
            '?>\n<SIHOT-Document>\n<SIHOT-XML-REQUEST>'
            '\n<REQUEST-TYPE>TEST_OC</REQUEST-TYPE><EMPTY></EMPTY><DEEP><DEEPER>value</DEEPER></DEEP>'
            '<DATE>' + test_date + '</DATE>\n</SIHOT-XML-REQUEST>\n</SIHOT-Document>')
