
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import re


# Number of reducers
NUM_REDUCERS = 2

# Folder paths
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
INPUT_FOLDER = PROJECT_FOLDER / "datasets" / "text-files"
OUTPUT_FOLDER = Path(__file__).resolve().parent / "output"


# Step 1: Read words from a file
def mapper(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read().lower()

    words = re.findall(r"[a-z0-9]+", text)

    result = []

    for word in words:
        result.append((word, 1))

    return result


# Step 2: Combine repeated words in one mapper's result
def combiner(pairs):
    counts = defaultdict(int)

    for word, number in pairs:
        counts[word] += number

    return counts


# Step 3: Choose a reducer for each word
def partition(word):
    return sum(ord(letter) for letter in word) % NUM_REDUCERS


# Step 4: Reduce words by adding their counts
def reducer(word_counts):
    result = {}

    for word in sorted(word_counts):
        result[word] = word_counts[word]

    return result


def main():
    files = sorted(INPUT_FOLDER.glob("book_*.txt"))

    if not files:
        print("No input files found!")
        return

    # Run mappers in parallel
    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        mapped_results = list(executor.map(mapper, files))

    # Create two empty reducers
    partitions = [defaultdict(int) for _ in range(NUM_REDUCERS)]

    # Combine and partition
    for pairs in mapped_results:
        combined_words = combiner(pairs)

        for word, count in combined_words.items():
            reducer_number = partition(word)
            partitions[reducer_number][word] += count

    # Create the output folder
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # Shuffle, sort and reduce
    for number in range(NUM_REDUCERS):
        word_counts = partitions[number]
        final_result = reducer(word_counts)

        output_file = OUTPUT_FOLDER / f"reducer_{number}.txt"

        with open(output_file, "w", encoding="utf-8") as file:
            for word, count in final_result.items():
                file.write(f"{word} {count}\n")

        print(f"Reducer {number} finished.")

    print("MapReduce finished successfully!")


if __name__ == "__main__":
    main()
