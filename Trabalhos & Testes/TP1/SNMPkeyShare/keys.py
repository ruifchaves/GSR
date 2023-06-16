import numpy as np



update_count = 0

class Keys:
    def __init__(self, M, K, T):
        if type(M) is str:
            M = np.array([int(c) for c in M])
            #print("M:", M)
        self.M = M
        self.K = K
        self.T = T
        self.Z = self.generate_matrix_Z()
        self.update_count = 0

    def rotate(self, seq, n):
        return np.roll(seq, n)

    def transpose(self, seq):
        return seq.T

    def random(self, seed, min_val, max_val):
        np.random.seed(seed)
        return np.random.randint(min_val, max_val + 1)

    def xor(self, *args):
        result = args[0]

        for arg in args[1:]:
            result = np.bitwise_xor(result, arg)
        return result


    def generate_matrix_Z(self):
        M1 = self.M[:self.K]
        M2 = self.M[self.K:]

        ZA = np.array([self.rotate(M1, i) for i in range(self.K)])
        ZB = np.array([self.rotate(M2, j) for j in range(self.K)]).T

        ZC = np.array([[self.random(ZA[i, j], 0, 255) for j in range(self.K)] for i in range(self.K)])
        ZD = np.array([[self.random(ZB[i, j], 0, 255) for j in range(self.K)] for i in range(self.K)])

        Z = self.xor(ZA, ZB, ZC, ZD)
        return Z

    def update_matrix_Z(self):
        for i in range(self.K):
            self.Z[i] = self.rotate(self.Z[i], self.random(self.Z[i, 0], 0, self.K - 1))

        for j in range(self.K):
            self.Z[:, j] = self.rotate(self.Z[:, j], self.random(self.Z[0, j], 0, self.K - 1))

        self.update_count += 1

    def generate_key(self):
        i = self.random(self.update_count + self.Z[0, 0], 0, self.K - 1)
        j = self.random(self.Z[i, 0], 0, self.K - 1)

        C = self.xor(self.Z[i], self.transpose(self.Z[:, j]))
        return C



# Example usage
#   M = np.random.randint(0, 256, size=(2 * 8,), dtype=np.uint8)
#   K = 8
#   T = 1000

#   key_gen = KeyGenerator(M, K, T)

# Update the matrix Z
#   key_gen.update_matrix_Z()

# Generate a key
#   key = key_gen.generate_key()
#   print("Generated key:", key)

