import sys
import traceback

import parseFilenameandUpload
import documentuploadtodb


def main():
    try:
        print("Running document upload process...")
        parseFilenameandUpload.main()
    except Exception as e:
        print("An error occurred during document upload:")
        traceback.print_exc()
        sys.exit(1)
    try:
        print("Uploading documents to database...")
        documentuploadtodb.main()
    except Exception as e:
        print("An error occurred during database upload:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
