def init(word1: str, word2: str) -> list:
    # create cache (2D array) and initialize with all 0s
    cache = [[0 for _ in range(len(word2)+1)] for _ in range(len(word1)+1)]
    # base cases filled up
    for i in range(len(word1)):
        cache[i][len(word2)] = len(word1) - i

    for j in range(len(word2)):
        cache[len(word1)][j] = len(word2) - j

    return cache

def editDistance(word1: str, word2: str) -> list:
    cache = init(word1=word1, word2=word2) # correct

    def helper_r(i, j):
        # base case
        if(i == len(word1) or j == len(word2)):
            return cache[i][j]

        if(cache[i][j] == 0):
            if(word1[i] != word2[j]):
                cache[i][j] = min(
                    helper_r(i+1, j),
                    helper_r(i, j+1),
                    helper_r(i+1, j+1)
                ) + 1
            else:
                cache[i][j] = helper_r(i+1, j+1)
        
        return cache[i][j]

    def helper_i():
        for i in range( len(word1) - 1, -1, -1 ):
            for j in range( len(word2) -1, -1, -1 ):
                if(word1[i] == word2[j]):
                    cache[i][j] = cache[i+1][j+1]
                else:
                    cache[i][j] = min(
                    cache[i+1][j],
                    cache[i][j+1],
                    cache[i+1][j+1]
                ) + 1

    helper_i()
    # helper_r(0, 0)
    return cache[0][0]