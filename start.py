import app


if __name__ == "__main__":
    downloader = app.Downloader(workRange=(0, 105000),  # Set this to like 100 above highest ID you can find
                                threadCount=50  # 10 is safe, 50 is wild, but they didn't block my ip so uhh
                                )
    downloader.run()