class A(object):
    def __init__(self):
        pass

    def c(self, text):
        for c in text:
            yield c


if __name__ == '__main__':
    a = A()
    gen = a.c("SHIT")

    print(next(gen))
    print(next(gen))
    print(next(gen))
    print(next(gen))
