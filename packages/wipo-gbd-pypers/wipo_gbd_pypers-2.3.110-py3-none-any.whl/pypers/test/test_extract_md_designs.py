import unittest
from pypers.steps.fetch.extract.md.designs import Designs
from pypers.utils.utils import dict_update
from pypers.test import mock_db, mockde_db, mock_logger
from mock import patch, MagicMock
import os
import shutil
import json


class MockPage:

    @patch("pypers.core.interfaces.db.get_db_logger", MagicMock(side_effect=mock_logger))
    def __init__(self, vals):
        self.content = []
        for i in vals:
            self.content.append(
                {
                    'markId': str(i),
                    'media': ['img%s.jpg' % k for k in range(0, 10)],
                    'images': [{'location': 'img%s.jpg' % k}
                               for k in range(0, 10)]
                }
            )
        if len(vals) == 100:
            self.content[0]['images'] = [{'location': 'foo.jpg'}]
        self.content = json.dumps(self.content)

    @patch("pypers.core.interfaces.db.get_db_logger", MagicMock(side_effect=mock_logger))
    def __exit__(self, *args, **kwargs):
        pass

    @patch("pypers.core.interfaces.db.get_db_logger", MagicMock(side_effect=mock_logger))
    def __enter__(self, *args, **kwargs):
        pass


def mock_page(media, *args, **kwargs):
    vals = media.split('markId=')[1].split(',')
    return MockPage(vals)


def mock_zipextract(source, dest):
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Designs xmlns="http://md.oami.europa.eu/schemas/design">
  <Design>
    <DesignIdentifier>MD0-0001</DesignIdentifier>
  </Design>
  <Design>
    <DesignIdentifier>MD0-0010</DesignIdentifier>
  </Design>
</Designs>'''
    ext = 'xml'
    if 'img' in dest:
        ext = 'img'
    for i in range(0, 10):
        xml_dest = os.path.join(dest, 'TMD0-000%s.%s' % (i, ext))
        with open(xml_dest, 'w') as f:
            f.write(xml_content)


mock_get_value_counter = 0


def mock_get_nodevalue(*args, **kwargs):
    global mock_get_value_counter
    res = '12%s' % mock_get_value_counter
    mock_get_value_counter += 1
    return res


class TestMerge(unittest.TestCase):

    path_test = os.path.join(os.path.dirname(__file__), 'foo')
    cfg = {
        'step_class': ' pypers.steps.fetch.extract.md.designs.Designs',
        'sys_path': None,
        'name': 'Designs',
        'meta': {
            'job': {},
            'pipeline': {
                'input': {
                    'from_web': {
                        'credentials': {
                            'user': 'toto',
                            'password': 'password'
                        }
                    }

                },
                'run_id': 1,
                'log_dir': path_test
            },
            'step': {},
        },
        'output_dir': path_test
    }

    extended_cfg = {
        'input_archive': {'toto': [os.path.join(path_test, 'toto.zip'),
                                   os.path.join(path_test, 'IMG.zip')
                                   ]},
    }

    @patch("pypers.core.interfaces.db.get_db_logger", MagicMock(side_effect=mock_logger))
    def setUp(self):
        try:
            shutil.rmtree(self.path_test)
        except Exception as e:
            pass
        os.makedirs(self.path_test)
        for _, v in self.extended_cfg['input_archive'].items():
            for fin in v:
                with open(fin, 'w') as f:
                    f.write('toto')

        """
        img_alreday = os.path.join(self.path_test, '01', '20')
        os.makedirs(img_alreday)
        img_alreday = os.path.join(img_alreday, '120.foooo.high.png')
        with open(img_alreday, 'w') as f:
            f.write('toto')
        """
        self.cfg = dict_update(self.cfg, self.extended_cfg)

    @patch("pypers.core.interfaces.db.get_db_logger", MagicMock(side_effect=mock_logger))
    def tearDown(self):
        try:
            shutil.rmtree(self.path_test)
            pass
        except Exception as e:
            pass

    @patch('pypers.utils.utils.zipextract',
           MagicMock(side_effect=mock_zipextract))
    @patch('pypers.utils.xmldom.get_nodevalue',
           MagicMock(side_effect=mock_get_nodevalue))
    @patch("requests.sessions.Session.get",
           MagicMock(side_effect=mock_page))
    @patch("pypers.core.interfaces.db.get_db", MagicMock(side_effect=mock_db))
    @patch("pypers.core.interfaces.db.get_db_logger", MagicMock(side_effect=mock_logger))
    def test_process(self):
        mockde_db.update(self.cfg)
        step = Designs.load_step("test", "test", "step")
        step.process()


if __name__ == "__main__":
    unittest.main()
