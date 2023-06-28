"""
Autor: Rui Chaves (ruichaves99@gmail.com)
Descrição: Ficheiro que guarda a matriz Z e que permite a atualização da mesma e geração de chaves a pedido.
"""

import numpy as np
from datetime import datetime, timedelta
import threading


class Keys:
    def __init__(self, M, K, V):
        if type(M) is str:
            M = np.array([int(c) for c in M])
        self.M = M
        self.K = K
        self.V = V
        self.Z = self.generate_matrix_Z()
        self.update_count = 0
        self.matrix_updating = False        

        #NOTE: ensure that update_matrix_Z() and generate_key() do not run simultaneously and interfere with each other
        self.matrix_updating_lock = threading.Lock()

    # Funcao que da rotate a uma linha da matriz n vezes
    def rotate(self, seq, n):
        return np.roll(seq, n)

    # Funcao que transpoe uma linha da matriz
    def transpose(self, seq):
        return seq.T

    # Funcao que gera um numero aleatorio entre min_val e max_val com um valor de seed
    def random(self, seed, min_val, max_val):
        np.random.seed(seed)
        return np.random.randint(min_val, max_val + 1)

    # Funcao que implementa o XOR entre n arrays
    def xor(self, *args):
        result = args[0] #type: ignore
        for arg in args[1:]:
            result = np.bitwise_xor(result, arg)
        return result

    # Funcao que gera a matriz Z, recorre a funcao rotate e random
    def generate_matrix_Z(self):
        M1 = self.M[:self.K]
        M2 = self.M[self.K:]

        ZA = np.array([self.rotate(M1, i) for i in range(self.K)])
        ZB = np.array([self.rotate(M2, j) for j in range(self.K)]).T

        ZC = np.array([[self.random(ZA[i, j], 0, 255) for j in range(self.K)] for i in range(self.K)])
        ZD = np.array([[self.random(ZB[i, j], 0, 255) for j in range(self.K)] for i in range(self.K)])

        Z = self.xor(ZA, ZB, ZC, ZD)
        return Z

    # Funcao que gera uma chave com base na matriz Z
    def generate_key(self, firstChar=33, numChars=94):
        with self.matrix_updating_lock:
            i = self.random(self.update_count + self.Z[0, 0], 0, self.K - 1)
            j = self.random(self.Z[i, 0], 0, self.K - 1)

            C = self.xor(self.Z[i], self.transpose(self.Z[:, j]))
            C = ''.join(chr(byte % numChars + firstChar) for byte in C if byte!=0) # Convert to ascii string within limits given (ensure printable characters and not nulls)

            return C, datetime.now() + timedelta(seconds=self.V)


    # Funcao que atualiza a matriz Z e retorna o tempo de atualizacao
    def update_matrix_Z(self):
        with self.matrix_updating_lock:
            self.matrix_updating = True
            for i in range(self.K):
                self.Z[i] = self.rotate(self.Z[i], self.random(self.Z[i, 0], 0, self.K - 1))

            for j in range(self.K):
                self.Z[:, j] = self.rotate(self.Z[:, j], self.random(self.Z[0, j], 0, self.K - 1))

            self.update_count += 1
            self.matrix_updating = False
            return datetime.now()
