import requests
from queue import Queue
from threading import Thread
from bs4 import BeautifulSoup
from tqdm import tqdm
import os

class Downloader:
    downloadUrl = "https://lexaloffle.com/bbs/?pid={cartId}"

    def __init__(self, threadCount, workRange):
        """
        :param threadCount: Amount of threads to use, sane amounts are between 1 and 50
        :param workRange: Range of id's to check for. for example: (0, 105000)
        """
        self.threadCount = threadCount
        self.workRange = workRange
        self.queue = Queue()
        self.progress = tqdm(desc="Carts checked", total=self.workRange[-1])

    # Wrapping requests in this allows for better error and retry control
    def request(self, url, method=requests.get, attempts=15, timeout=7, *args, **kwargs):
        for attempt in range(attempts):
            try:
                r = method(url=url, timeout=timeout, *args, **kwargs)
                if r is not None and r.ok:
                    return r
                elif r.status_code == 403:
                    return None
            except requests.RequestException:
                pass

    def download(self, cartId):
        # Visit the threadId
        r = self.request(self.downloadUrl.format(cartId=cartId))
        if r is None or not r.ok:
            return

        # Scrape the image file link
        soup = BeautifulSoup(r.text, "html.parser")
        cartFile = soup.find("a", {"title": "Open Cartridge File"})
        if cartFile is None:
            return
        link = f"https://lexaloffle.com{cartFile['href']}"

        # Try getting the image file
        r = self.request(link)
        if r is None or not r.ok:
            return
        self.save(content=r.content, filename=os.path.basename(link))

    @staticmethod
    def save(content, filename):
        with open(f"carts/{filename}", "wb") as file:
            file.write(content)

    # Main function for fetching an id and downloading it
    def loop(self):
        while not self.queue.empty():
            self.download(cartId=self.queue.get())
            self.progress.update(1)
            self.queue.task_done()

    # Creates the threads that end up working
    def startThreads(self):
        threads = [Thread(target=self.loop) for x in range(self.threadCount)]
        [t.start() for t in threads]
        [t.join() for t in threads]

    # Entrypoint for the class
    def run(self):
        os.makedirs("carts", exist_ok=True)

        assert type(self.threadCount) == int, "self.threadcount is not an integer."
        assert 1 <= self.threadCount <= 100, "self.threadcount is not between 1 and 100. pls don't bombard them with spam"
        assert all([type(self.workRange) == tuple,
                    len(self.workRange) == 2,
                    all(map(lambda x: type(x) == int, self.workRange))
                    ]), "self.workRange has to be a tuple of 2 integers"

        [self.queue.put(x) for x in range(*self.workRange)]
        self.startThreads()
