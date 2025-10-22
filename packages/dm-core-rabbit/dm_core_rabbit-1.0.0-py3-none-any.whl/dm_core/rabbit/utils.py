import re


class CaseConvert(object):

    @staticmethod
    def to_snake(string):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def to_camel(string):
        words = string.split('_')
        return ''.join(word.capitalize() for word in words)