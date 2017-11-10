
class MusicRecommender:
    def __init__(self, sparse_songmatrix, trackid_vector):
        self.sparse_songmatrix = sparse_songmatrix
        self.trackid_vector = trackid_vector

    def recommend_song(self, sparse_word_frequency_vector):
        print("Start recommending")

        scores = self.sparse_songmatrix * sparse_word_frequency_vector

        GET_TOP_N = 200
        row = scores.toarray().ravel()

        top_ten_indicies = reversed(row.argsort()[-GET_TOP_N:])
        top_ten_values = reversed(row[row.argsort()[-GET_TOP_N:]])

        row_and_scores = list()
        for row, value in zip(top_ten_indicies, top_ten_values):
            row_and_scores.append((value, row))


        to_return = list()
        for score, row in row_and_scores[:GET_TOP_N]:
            to_return.append((self.trackid_vector[row], score))

        return to_return