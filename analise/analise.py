class Analise(object):
    def __init__(self, analise_type, geo, fi, fm, fr):
        self.analise_type = analise_type
        self.geo = geo
        self.fi = fi
        self.fm = fm
        self.fr = fr


    def calcFracGlobal(fm, fi):  # ================= Método TESTADO =======================
        F = fm + fi
        Fm = fm / F
        Fi = fi / F



        return Fm, Fi

    def tensorA(self, fk, Ck, Cj, C): # <------- FALTA TESTAR =======================
        Ak = 1 / fk * ((Ck - Cj) ** -1) * (C - Cj)
        return Ak

    def tensorB(self, fk, Ck, Cj, C): # <------- FALTA TESTAR =======================
        D = C ** -1
        Dk = Ck ** -1
        Dj = Cj ** -1
        Bk = 1 / fk * ((Dk - Dj) ** -1) * (D - Dj)
        return Bk

    def corrigeFrac(fi, fj):  # <------- FALTA TESTAR =======================
        ft = fi + fj
        fic = fi / ft
        fjc = fj / ft

        return fic, fjc

    @staticmethod
    def corrigeFracs(fi, fj, fk):  # <------- FALTA TESTAR =======================
        ft = fi + fj + fk
        fic = fi / ft
        fjc = fj / ft
        fkc = fk/ft

        return fic, fjc, fkc


