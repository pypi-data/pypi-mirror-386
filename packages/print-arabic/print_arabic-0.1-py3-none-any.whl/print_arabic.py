"""
print_arabic - A simple library to print Arabic text with proper bidirectional support

Example:
    import print_arabic
    print_arabic("مرحبا بالعالم")
"""

from bidi.algorithm import get_display
import arabic_reshaper
import sys

__version__ = "0.1"


def print_arabic(text):
    """
    Print Arabic text with proper bidirectional support.

    This function reshapes Arabic text and applies bidirectional algorithm
    to display Arabic text correctly in terminals and consoles.

    Args:
        text (str): The Arabic text to print

    Example:
        >>> import print_arabic
        >>> print_arabic.print_arabic("مرحبا بك")
    """
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    print(bidi_text)


# Make the module itself callable
class _PrintArabicModule(sys.modules[__name__].__class__):
    def __call__(self, text):
        """Allow module to be called directly"""
        print_arabic(text)


sys.modules[__name__].__class__ = _PrintArabicModule


__all__ = ['print_arabic']
