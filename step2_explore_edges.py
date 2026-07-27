# step2_explore_edges.py

print("Searching franchises_unfiltered.txt for crossover relationships...")

with open('franchises_unfiltered.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Pull out only the lines that contain a capital ' X ' with spaces around it
crossover_pages = [line.strip() for line in lines if " X " in line]

print(f"\n-> Success! Found {len(crossover_pages)} crossover relationship pages.")
print("Here are 10 random examples from the wiki data:")
print("-" * 50)

# Print the first 10 to inspect them
for page in crossover_pages[:10]:
    print(page)