import pytest

from handlers.image_processing_handlers import parser


def test1_parser():
    assert parser('109 30х40 баннер') == {'sizes': ['30х40'],
                                          'number': '109',
                                          'material': 'Баннер',
                                          'no_material': False,
                                          'cropper': False,
                                          'urgent': False
                                          }


def test2_parser():
    assert parser('109asdf 20:80 банер %') == {'sizes': ['20х80'],
                                               'number': '109asdf',
                                               'material': 'Баннер',
                                               'no_material': False,
                                               'cropper': True,
                                               'urgent': False
                                               }


def test3_parser():
    assert parser('1нпа  холст % 20X80 ! 60*100') == {'sizes': ['20х80', '60х100'],
                                                      'number': '1нпа',
                                                      'material': 'Холст',
                                                      'no_material': False,
                                                      'cropper': True,
                                                      'urgent': True
                                                      }


def test4_parser():
    assert parser('30х40 109 баннер') == {'sizes': ['30х40'],
                                          'number': '109',
                                          'material': 'Баннер',
                                          'no_material': False,
                                          'cropper': False,
                                          'urgent': False
                                          }


def test5_parser():
    assert parser('#4148 матовый 40:60 2.30/40') == {'sizes': ['40х60', '30х40'],
                                                     'number': '4148',
                                                     'material': 'Матовый холст',
                                                     'no_material': False,
                                                     'cropper': False,
                                                     'urgent': False
                                                     }


def test6_parser():
    assert parser('#3495 банер 20/30 3шт 🚨сегодня отправить 🚨') == {'sizes': ['20х30'],
                                                                    'number': '3495',
                                                                    'material': 'Баннер',
                                                                    'no_material': False,
                                                                    'cropper': False,
                                                                    'urgent': True
                                                                    }


def test7_parser():
    assert parser('30х40 №109 баннер') == {'sizes': ['30х40'],
                                           'number': '109',
                                           'material': 'Баннер',
                                           'no_material': False,
                                           'cropper': False,
                                           'urgent': False
                                           }


def test8_parser():
    assert parser('#4148 глянцевый 30/40') == {'sizes': ['30х40'],
                                               'number': '4148',
                                               'material': 'Холст',
                                               'no_material': False,
                                               'cropper': False,
                                               'urgent': False
                                               }


def test9_parser():
    assert parser('n41wed глянец 30:90') == {'sizes': ['30х90'],
                                             'number': '41wed',
                                             'material': 'Холст',
                                             'no_material': False,
                                             'cropper': False,
                                             'urgent': False
                                             }


def test10_parser():
    assert parser('№45аапр глянец 1.50:70 2.40/60 3. 45/35 горизонт 4-5. 20/30 вертикально') == {
        'sizes': ['50х70', '40х60', '45х35', '20х30'],
        'number': '45аапр',
        'material': 'Холст',
        'no_material': False,
        'cropper': False,
        'urgent': False
    }


def test11_parser():
    assert parser('n41wed 30:90') == {'sizes': ['30х90'],
                                      'number': '41wed',
                                      'material': 'Холст',
                                      'no_material': True,
                                      'cropper': False,
                                      'urgent': False
                                      }


def test12_parser():
    assert parser('#7107 гдянец 50/70 2.40:60') == {'sizes': ['50х70', '40х60'],
                                                    'number': '7107',
                                                    'material': 'Холст',
                                                    'no_material': True,
                                                    'cropper': False,
                                                    'urgent': False
                                                    }


if __name__ == '__main__':
    pytest.main()
