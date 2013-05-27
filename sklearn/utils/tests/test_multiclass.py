import numpy as np

from sklearn.externals.six.moves import xrange
from sklearn.externals.six import iteritems

from sklearn.utils.testing import assert_array_equal
from sklearn.utils.testing import assert_equal
from sklearn.utils.testing import assert_true
from sklearn.utils.testing import assert_false
from sklearn.utils.testing import assert_raises

from sklearn.utils.multiclass import unique_labels
from sklearn.utils.multiclass import is_label_indicator_matrix
from sklearn.utils.multiclass import is_multilabel
from sklearn.utils.multiclass import is_sequence_of_sequences
from sklearn.utils.multiclass import type_of_target

EXAMPLES = {
    'multilabel-indicator': [
        np.random.randint(2, size=(10, 10)),
        np.array([[0, 1], [1, 0]]),
        np.array([[0, 0], [0, 0]]),
        np.array([[-1, 1], [1, -1]]),
        np.array([[-3, 3], [3, -3]]),
    ],
    'multilabel-sequences': [
        [[0, 1]],
        [[0], [1]],
        [[1, 2, 3]],
        [[1], [2], [0, 1]],
        [[1], [2]],
        [[]],
        [()],
        np.array([[], [1, 2]], dtype='object'),
    ],
    'multiclass': [
        [1, 0, 2, 2, 1, 4, 2, 4, 4, 4],
        np.array([1, 0, 2]),
        np.array([[1], [0], [2]]),
        [0, 1, 2],
        ['a', 'b', 'c'],
    ],
    'multiclass-multioutput': [
        np.array([[1, 0, 2, 2], [1, 4, 2, 4]]),
        np.array([['a', 'b'], ['c', 'd']]),
        np.array([[1, 0, 2]]),
    ],
    'binary': [
        [0, 1],
        [1, 1],
        [],
        [0],
        np.array([0, 1, 1, 1, 0, 0, 0, 1, 1, 1]),
        np.array([[0], [1]]),
        [1, -1],
        [3, 5],
        ['a'],
        ['a', 'b'],
        ['abc', 'def'],
    ],
    'continuous': [
        [1e-5],
        [0, .5],
        np.array([[0], [.5]]),
    ],
    'continuous-multioutput': [
        np.array([[0, .5], [.5, 0]]),
        np.array([[0, .5]]),
    ],
    'unknown': [
        # Not currently multiclass-multioutput, nor indicator
        np.array([[0, 1]]),
        # empty second dimension
        np.array([[], []]),
        # 3d
        np.array([[[0, 1], [2, 3]], [[4, 5], [6, 7]]]),
        # not currently supported sequence of sequences
        np.array([np.array([]), np.array([1, 2, 3])], dtype=object),
        [np.array([]), np.array([1, 2, 3])],
    ]
}

def test_unique_labels():
    # Empty iterable
    assert_raises(ValueError, unique_labels)

    # Multiclass problem
    assert_array_equal(unique_labels(xrange(10)), np.arange(10))
    assert_array_equal(unique_labels(np.arange(10)), np.arange(10))
    assert_array_equal(unique_labels([4, 0, 2]), np.array([0, 2, 4]))

    # Multilabels
    assert_array_equal(unique_labels([(0, 1, 2), (0,), tuple(), (2, 1)]),
                       np.arange(3))
    assert_array_equal(unique_labels([[0, 1, 2], [0], list(), [2, 1]]),
                       np.arange(3))
    assert_array_equal(unique_labels(np.array([[0, 0, 1],
                                               [1, 0, 1],
                                               [0, 0, 0]])),
                       np.arange(3))

    # Several arrays passed
    assert_array_equal(unique_labels([4, 0, 2], xrange(5)),
                       np.arange(5))
    assert_array_equal(unique_labels((0, 1, 2), (0,), (2, 1)),
                       np.arange(3))


def test_is_multilabel():
    for group, group_examples in iteritems(EXAMPLES):
        if group.startswith('multilabel'):
            assert_, exp = assert_true, 'True'
        else:
            assert_, exp = assert_false, 'False'
        for example in group_examples:
            assert_(is_multilabel(example),
                    msg='is_multilabel(%r) should be %s' % (example, exp))


def test_is_label_indicator_matrix():
    for group, group_examples in iteritems(EXAMPLES):
        if group == 'multilabel-indicator':
            assert_, exp = assert_true, 'True'
        else:
            assert_, exp = assert_false, 'False'
        for example in group_examples:
            assert_(is_label_indicator_matrix(example),
                    msg='is_label_indicator_matrix(%r) should be %s'
                    % (example, exp))


def test_is_sequence_of_sequences():
    for group, group_examples in iteritems(EXAMPLES):
        if group == 'multilabel-sequences':
            assert_, exp = assert_true, 'True'
        else:
            assert_, exp = assert_false, 'False'
        for example in group_examples:
            assert_(is_sequence_of_sequences(example),
                    msg='is_sequence_of_sequences(%r) should be %s'
                    % (example, exp))


def test_type_of_target():
    for group, group_examples in iteritems(EXAMPLES):
        for example in group_examples:
            assert_equal(type_of_target(example), group,
                         msg='type_of_target(%r) should be %r, got %r'
                         % (example, group, type_of_target(example)))
