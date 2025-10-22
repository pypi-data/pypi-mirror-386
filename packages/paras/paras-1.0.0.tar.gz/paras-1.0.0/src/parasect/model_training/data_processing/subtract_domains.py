from sys import argv

from parasect.core.parsing import parse_list
from parasect.core.writers import write_list


if __name__ == "__main__":
    domains_1 = set(parse_list(argv[1]))
    domains_2 = set(parse_list(argv[2]))
    domains = domains_1 - domains_2
    write_list(list(domains), argv[3])