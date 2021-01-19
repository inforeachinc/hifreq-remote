import re


def exception_check(expected_exception_class, expected_exception_text_pattern):
    def wrapper1(func):
        def wrapper2(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                exception_class = e.__class__.__module__ + '.' + e.__class__.__name__
                if exception_class != expected_exception_class:
                    raise Exception('Expected exception ' + expected_exception_class + ' but ' + exception_class + " was raised instead.")
                exception_text = str(e)
                if not re.search(expected_exception_text_pattern, exception_text):
                    raise Exception('Expected exception to match pattern ' + expected_exception_text_pattern + ' but the text was ' + exception_text)

            else:
                raise Exception('Expected exception ' + expected_exception_class + ' was not raised')

        return wrapper2

    return wrapper1


def decimal_equal(first, second):
    return round(abs(second - first), 6) == 0


def error_check(expected_error_message_pattern, actual_error):
    if not re.search(expected_error_message_pattern, actual_error):
        raise Exception(
            'Expected error to match pattern ' + expected_error_message_pattern + ' but the text was ' + actual_error)

