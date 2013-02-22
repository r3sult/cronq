import time

class Injector(object):

    def __init__(self, storage):
        self.storage = storage
        storage.bootstrap()

    def run(self):
        while True:
            self.storage.inject()
            time.sleep(1)

def main():
    from cronq.backends.mysql import Storage
    from cronq.queue_connection import Publisher
    injector = Injector(Storage(Publisher()))
    injector.run()


if __name__ == '__main__':
    main()
