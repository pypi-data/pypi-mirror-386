
from sys import argv

from parasect.core.parsing import parse_fasta_file, parse_list

if __name__ == "__main__":

    domains = parse_list(argv[1])
    fasta = parse_fasta_file(argv[2])
    with open(argv[3], 'w') as out:
        for domain in domains:
            out.write(f">{domain}\n{fasta[domain]}\n")