cpdef list whitespace_tokenizer(str text):
    """
    Tokenizes text into words. Words are separated by white characters.
    
    :param text: Text to tokenize.
    :return: List of tuples. Each tuple contains word and its character start and end offset.
    """

    cdef int start=0
    cdef int end=0

    cdef list result=[]

    while end<len(text):
        if text[end].isspace():
            if start!=end:
                result.append((text[start:end],start,end))
            end+=1
            start=end
        else:
            end+=1

    if start!=end:
        result.append((text[start:end],start,end))

    return result

cdef class WhitespaceTokenizer:
    """
    Tokenizer that uses whitespace to tokenize text.
    It returns token ids instead of words.
    """

    cdef dict vocabulary

    def __init__(self, vocabulary=None):
        """
        Initializes the tokenizer.

        :param vocabulary: Vocabulary to use. If None, an empty vocabulary is used.
        """
        self.vocabulary = {} if vocabulary is None else vocabulary

    def __call__(self, text):
        """
        Tokenizes text into words.

        :param text: Text to tokenize.
        :return: List of tuples. Each tuple contains word and its character start and end offset.
        """
        return self.tokenize(text)

    cdef tokenize(self, str text):
        """
        Tokenizes text into words.

        :param text: Text to tokenize.
        :return: List of tuples. Each tuple contains word and its character start and end offset.
        """
        cdef list res = []
        tokens = whitespace_tokenizer(text)

        for i in range(len(tokens)):
            token = tokens[i][0]
            if token not in self.vocabulary:
                self.vocabulary[token] = len(self.vocabulary)
            res.append((self.vocabulary[token], tokens[i][1], tokens[i][2]))

        return res