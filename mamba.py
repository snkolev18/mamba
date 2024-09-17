from file_download_utilities import file_download_tqdm as file_download

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url",
                        help="URL address path to the file",
                        required=True,
                        type=str)
    parser.add_argument("-o", "--destination-path",
                        required=True,
                        type=str)
    # parser.add_argument("-c", "--client",
    #                     help="Don't use, under development. Defaults to requests package internally")
    parser.add_argument("-t", "--threads",
                        type=int)
    parser.add_argument("-cz", "--chunk-size",
                        help="Chunk size in bytes. Specifies the size of the download and disk write chunk",
                        type=int)
    parser.add_argument("-f", "--force-download",
                        default=False, type=bool)

    args = parser.parse_args()

    file_download(url=args.url, dest_path=args.destination_path, threads=args.threads, chunk_size=args.chunk_size, force_download=args.force_download)
